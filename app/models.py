from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    approved = "approved"
    declined = "declined"
    error = "error"


class PaymentEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))

    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    merchant_id: str
    terminal_id: str
    processor: str

    amount: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    status: PaymentStatus
    response_code: str
    latency_ms: int = Field(ge=0)