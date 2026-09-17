from fastapi import APIRouter, Depends

from ..dependencies import require_user_id
from .agent import router as agent_router
from .chat import router as chat_router
from .knowledge import router as knowledge_router
from .orders import router as orders_router
from .products import router as products_router
from .tickets import router as tickets_router

router = APIRouter(dependencies=[Depends(require_user_id)])
router.include_router(products_router)
router.include_router(tickets_router)
router.include_router(orders_router)
router.include_router(knowledge_router)
router.include_router(chat_router)
router.include_router(agent_router)
