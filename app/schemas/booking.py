from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    barber_id: int
    service_id: int
    starts_at: datetime


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    barber_id: int
    service_id: int
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus