from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.associations import barber_services

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.service import Service

class Barber(Base):
    __tablename__ = "barbers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="barber")

    services: Mapped[list["Service"]] = relationship(
        secondary=barber_services, back_populates="barbers"
    )