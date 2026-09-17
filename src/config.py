from common.config import BaseAppSettings


class Settings(BaseAppSettings):
    service_name: str = "customer-support-agent"

settings = Settings()
