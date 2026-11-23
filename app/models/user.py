import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.booking import Booking


class UserRole(str, enum.Enum):
    client = "client"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.client, server_default=UserRole.client.value
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")