from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import barber_services

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.barber import Barber


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    duration_minutes: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    barbers: Mapped[list["Barber"]] = relationship(
        secondary=barber_services, back_populates="services"
    )

    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")