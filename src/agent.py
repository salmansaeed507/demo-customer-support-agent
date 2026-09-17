"""Simulated ShopPilot agent tools — mirrors frontend simulateAgentTurn."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import KnowledgeDoc, Order, Product, Ticket

KB_EXCERPTS: dict[str, list[str]] = {
    "shipping-policy.pdf": [
        "Standard shipping arrives in 3–5 business days. Express options ship within 1–2 business days after fulfillment.",
        "We currently ship to the contiguous United States. Tracking numbers are emailed when the carrier scans the package.",
    ],
    "returns-and-refunds.md": [
        "Unused items may be returned within 30 days of delivery with the original receipt or order confirmation.",
        "Refunds are issued to the original payment method and typically post within 5–7 business days after we receive the return.",
    ],
    "product-faq.docx": [
        "Most electronics include a 1-year limited manufacturer warranty covering defects in materials and workmanship.",
        "For sizing and fit questions, check the product page Size Guide before opening a return.",
    ],
    "warranty-guide.pdf": [
        "Warranty claims require proof of purchase and a description of the defect. Cosmetic wear is not covered.",
        "Approved warranty replacements ship free; refurbished units may be issued when new stock is unavailable.",
    ],
}


@dataclass
class AgentTurnResult:
    text: str
    trace: list[dict]
    citations: list[dict] | None = None
    ticket: Ticket | None = None


def _excerpts_for_doc(name: str) -> list[str]:
    for key, excerpts in KB_EXCERPTS.items():
        if key.lower() == name.lower():
            return excerpts
    return [
        f"Relevant section from {name} matching the customer query.",
        f"Additional context retrieved from {name} for grounding the reply.",
    ]


def _build_citations(docs: list[dict]) -> list[dict]:
    citations = []
    for i, doc in enumerate(docs):
        excerpts = _excerpts_for_doc(doc["name"])
        citations.append(
            {
                "filename": doc["name"],
                "excerpt": excerpts[i % len(excerpts)],
                "rank": i + 1,
                "score": doc["score"],
            }
        )
    return citations


def _score_doc(name: str, query: str) -> float:
    n = name.lower()
    q = query.lower()
    score = 0.55
    if "return" in q or "refund" in q:
        if "return" in n or "refund" in n:
            score = 0.91
        elif "shipping" in n:
            score = 0.62
        elif "warranty" in n:
            score = 0.58
    elif "ship" in q or "deliver" in q:
        if "shipping" in n:
            score = 0.89
        elif "return" in n:
            score = 0.61
    elif "warrant" in q:
        if "warrant" in n:
            score = 0.9
        elif "faq" in n or "product" in n:
            score = 0.7
    elif "faq" in q or "product" in q:
        if "faq" in n or "product" in n:
            score = 0.86
    return round(score * 100) / 100


def _next_ticket_id(db: Session) -> str:
    tickets = db.scalars(select(Ticket.id)).all()
    nums = []
    for ticket_id in tickets:
        digits = "".join(ch for ch in ticket_id if ch.isdigit())
        if digits:
            nums.append(int(digits))
    next_num = (max(nums) + 1) if nums else 1001
    return f"TCK-{next_num}"


def run_agent_turn(db: Session, text: str, thread_id: str, user_id: int) -> AgentTurnResult:
    trimmed = text.strip()
    lower = trimmed.lower()
    plan_input = trimmed[:80] + ("…" if len(trimmed) > 80 else "")
    trace: list[dict] = [
        {
            "tool": "plan",
            "input": plan_input,
            "output": "Classify intent and choose tools",
            "status": "ok",
        }
    ]

    if "create ticket" in lower:
        summary = re.sub(r"create ticket[:\s]*", "", trimmed, flags=re.I).strip() or trimmed
        ticket = Ticket(
            id=_next_ticket_id(db),
            user_id=user_id,
            customer="Admin chat user",
            summary=summary,
            conversation_id=thread_id,
            priority="medium",
            status="open",
            created=datetime.now(timezone.utc),
        )
        db.add(ticket)
        db.flush()
        trace = [
            {
                "tool": "plan",
                "input": trimmed[:80],
                "output": "Intent: create_ticket",
                "status": "ok",
            },
            {
                "tool": "create_ticket",
                "input": f'summary="{summary[:60]}" · priority=medium',
                "output": f"ticket_id={ticket.id} · status=open",
                "status": "ok",
            },
            {
                "tool": "compose_reply",
                "output": "Confirm ticket created via ticketing API",
                "status": "ok",
            },
        ]
        return AgentTurnResult(
            text=f'Created ticket {ticket.id}: “{ticket.summary}”. Priority medium, status open.',
            trace=trace,
            ticket=ticket,
        )

    order_match = re.search(r"#?\b(\d{4,})\b", lower)
    if order_match:
        order_id = order_match.group(1)
        order = db.scalar(
            select(Order).where(
                Order.user_id == user_id,
                (Order.id == order_id) | (Order.id == f"{user_id}-{order_id}"),
            )
        )
        if order is not None:
            items_label = ", ".join(
                f"{item.name} ×{item.quantity}" for item in order.items
            )
            trace.append(
                {
                    "tool": "get_order",
                    "input": f"order_id={order.id}",
                    "output": (
                        f"status={order.status} · customer={order.customer} · "
                        f"total={order.total:.2f} · items={items_label} · "
                        f"ship_to={order.shipping_address} · tracking={order.tracking_number}"
                    ),
                    "status": "ok",
                }
            )
            trace.append(
                {
                    "tool": "compose_reply",
                    "output": "Answer from order API result (not model memory)",
                    "status": "ok",
                }
            )
            status_label = order.status.replace("_", " ")
            carrier_bit = (
                f" ({order.carrier})"
                if order.carrier and order.carrier != "—"
                else ""
            )
            tracking_bit = (
                f" · tracking {order.tracking_number}"
                if order.tracking_number and order.tracking_number != "Pending"
                else ""
            )
            return AgentTurnResult(
                text=(
                    f"Order #{order.id} for {order.customer} is {status_label}. "
                    f"Items: {items_label}. Total ${order.total:.2f}. "
                    f"Shipping to {order.shipping_address} via {order.shipping_method}"
                    f"{carrier_bit}{tracking_bit}."
                ),
                trace=trace,
            )
        trace.append(
            {
                "tool": "get_order",
                "input": f"order_id={order_id}",
                "output": "No order found",
                "status": "miss",
            }
        )
        trace.append(
            {
                "tool": "compose_reply",
                "output": "Report miss; suggest checking the order id",
                "status": "ok",
            }
        )
        return AgentTurnResult(
            text=(
                f"I couldn't find order #{order_id} in the order API. "
                "Double-check the id or create a ticket if you need a human to dig in."
            ),
            trace=trace,
        )

    wants_kb = any(
        token in lower
        for token in ("return", "refund", "ship", "deliver", "warrant", "policy", "faq")
    )
    if wants_kb:
        if "refund" in lower:
            query = "refund timeline"
        elif "return" in lower:
            query = "return window"
        elif "warrant" in lower:
            query = "warranty coverage"
        elif "ship" in lower or "deliver" in lower:
            query = "shipping times"
        else:
            query = trimmed[:48]

        indexed = db.scalars(
            select(KnowledgeDoc).where(
                KnowledgeDoc.user_id == user_id,
                (KnowledgeDoc.embedding_status == "ready") | (KnowledgeDoc.indexed.is_(True)),
            )
        ).all()
        ranked = sorted(
            (
                {"name": d.name, "score": _score_doc(d.name, lower)}
                for d in indexed
            ),
            key=lambda d: d["score"],
            reverse=True,
        )[:2]
        ranked = [d for d in ranked if d["score"] >= 0.58]
        citations = _build_citations(ranked) if ranked else None

        trace.append(
            {
                "tool": "retrieve_knowledge",
                "input": f'query="{query}"',
                "output": (
                    f"{len(citations)} chunk(s): "
                    + ", ".join(f"{c['filename']}#{c['rank']}" for c in citations)
                    if citations
                    else "0 chunks (KB empty or unindexed)"
                ),
                "status": "ok" if citations else "miss",
            }
        )
        trace.append(
            {
                "tool": "compose_reply",
                "output": (
                    "Ground answer in retrieved chunks + cite sources"
                    if citations
                    else "Fallback policy copy (no retrieval hits)"
                ),
                "status": "ok",
            }
        )

        if citations:
            top = citations[0]
            fname = top["filename"].lower()
            if "return" in fname or "return" in lower or "refund" in lower:
                reply = (
                    f"Based on {top['filename']}: unused items can be returned within 30 days "
                    "with the original receipt. Refunds post in 5–7 business days after we receive the item."
                )
            elif "shipping" in fname or "ship" in lower:
                reply = (
                    f"Based on {top['filename']}: standard shipping is 3–5 business days; "
                    "express is typically 1–2 business days after fulfillment. "
                    "You’ll get a tracking email when the carrier scans the package."
                )
            elif "warrant" in fname:
                reply = (
                    f"Based on {top['filename']}: most electronics include a 1-year limited "
                    "warranty for defects. Claims need proof of purchase; cosmetic wear isn’t covered."
                )
            else:
                reply = f"I found relevant guidance in {top['filename']}. {top['excerpt']}"
            return AgentTurnResult(text=reply, trace=trace, citations=citations)

        return AgentTurnResult(
            text=(
                "I couldn't retrieve indexed knowledge for that yet. "
                "Index a policy doc in RAG / Knowledge, then ask again."
            ),
            trace=trace,
        )

    ticket_id_match = re.search(r"\b(tck[- ]?\d+)\b", lower, flags=re.I)
    if ticket_id_match or ("ticket" in lower and "create" not in lower):
        tickets = list(db.scalars(select(Ticket).where(Ticket.user_id == user_id)).all())
        if ticket_id_match:
            raw = ticket_id_match.group(1).upper().replace(" ", "-")
            tid = raw.replace("TCK", "TCK-", 1).replace("TCK--", "TCK-") if raw.startswith("TCK") else raw
            normalized = tid if "TCK-" in tid else f"TCK-{tid}"
            ticket = next(
                (t for t in tickets if t.id.lower() == normalized.lower()),
                None,
            )
            if ticket is None:
                needle = ticket_id_match.group(1).replace(" ", "").lower()
                ticket = next((t for t in tickets if needle in t.id.lower().replace("-", "")), None)
            if ticket is not None:
                trace.append(
                    {
                        "tool": "get_ticket",
                        "input": f"ticket_id={ticket.id}",
                        "output": (
                            f"status={ticket.status} · priority={ticket.priority} · "
                            f"customer={ticket.customer}"
                        ),
                        "status": "ok",
                    }
                )
                trace.append(
                    {
                        "tool": "compose_reply",
                        "output": "Summarize ticket from ticketing API",
                        "status": "ok",
                    }
                )
                return AgentTurnResult(
                    text=(
                        f"Ticket {ticket.id} ({ticket.status}, {ticket.priority}): "
                        f"{ticket.summary} — opened for {ticket.customer} ({ticket.created.isoformat()})."
                    ),
                    trace=trace,
                )
            trace.append(
                {
                    "tool": "get_ticket",
                    "input": f"ticket_id={normalized}",
                    "output": "Ticket not found",
                    "status": "miss",
                }
            )
        else:
            open_tickets = [t for t in tickets if t.status == "open"]
            example = tickets[0].id if tickets else "TCK-1042"
            trace.append(
                {
                    "tool": "list_tickets",
                    "input": 'status="open"',
                    "output": f"{len(open_tickets)} open ticket(s)",
                    "status": "ok",
                }
            )
            trace.append(
                {
                    "tool": "compose_reply",
                    "output": "Summarize open-ticket count from API",
                    "status": "ok",
                }
            )
            return AgentTurnResult(
                text=(
                    f"There are currently {len(open_tickets)} open ticket(s). "
                    f"Ask for a ticket id (e.g. {example}) for details, or say "
                    "“create ticket …” to open one."
                ),
                trace=trace,
            )
        trace.append(
            {
                "tool": "compose_reply",
                "output": "Explain miss and next steps",
                "status": "ok",
            }
        )
        return AgentTurnResult(
            text=(
                "I couldn't find that ticket. Try a full id like TCK-1042, or say "
                "“create ticket …” to open a new one."
            ),
            trace=trace,
        )

    products = list(db.scalars(select(Product).where(Product.user_id == user_id)).all())
    product = next(
        (
            p
            for p in products
            if (
                lower.find(p.name.lower()) >= 0
                or lower.find(p.name.lower()[:8]) >= 0
                or any(
                    len(tok) >= 4 and tok in lower
                    for tok in p.name.lower().split()
                )
            )
        ),
        None,
    )
    if product is not None:
        trace.append(
            {
                "tool": "get_product",
                "input": f"product_id={product.id}",
                "output": f"name={product.name} · price={product.price} · stock={product.stock}",
                "status": "ok",
            }
        )
        trace.append(
            {
                "tool": "compose_reply",
                "output": "Answer from catalog API",
                "status": "ok",
            }
        )
        return AgentTurnResult(
            text=(
                f"{product.name} — ${product.price}, {product.category}, "
                f"stock {product.stock}. {product.description}"
            ),
            trace=trace,
        )

    if "product" in lower or "stock" in lower or "catalog" in lower:
        hits = products[:3]
        trace.append(
            {
                "tool": "search_catalog",
                "input": f'query="{trimmed[:40]}"',
                "output": (
                    f"{len(hits)} product(s): "
                    + (", ".join(p.name for p in hits) if hits else "none")
                ),
                "status": "ok" if hits else "miss",
            }
        )
        trace.append(
            {
                "tool": "compose_reply",
                "output": "List catalog hits from product API",
                "status": "ok",
            }
        )
        if hits:
            names = "; ".join(f"{p.name} (${p.price})" for p in hits)
            return AgentTurnResult(
                text=(
                    f"I can look up catalog items. Examples: {names}. "
                    "Ask about a specific product name for details."
                ),
                trace=trace,
            )
        return AgentTurnResult(
            text=(
                "The catalog looks empty right now — add a product in the Products panel, "
                "then ask again."
            ),
            trace=trace,
        )

    trace.append(
        {
            "tool": "retrieve_knowledge",
            "input": f'query="{trimmed[:48]}"',
            "output": "0 high-confidence chunks",
            "status": "miss",
        }
    )
    trace.append(
        {
            "tool": "compose_reply",
            "output": "Escalate: insufficient tool evidence",
            "status": "ok",
        }
    )
    return AgentTurnResult(
        text=(
            "I don't have enough information to answer confidently. Try asking about an "
            "order number, a product, returns, shipping, a ticket id, or say “create ticket” "
            "to open a support ticket."
        ),
        trace=trace,
    )
