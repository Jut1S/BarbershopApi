from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Barber, Booking, BookingStatus, Service, User
from app.routers.deps import get_current_user
from app.schemas.booking import BookingCreate, BookingRead

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.starts_at.tzinfo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "starts_at must include timezone")

    if data.starts_at.tzinfo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "starts_at must include timezone")

    if data.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot book in the past")

    barber = db.get(Barber, data.barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    if not barber.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Barber is not active")

    service = db.get(Service, data.service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")

    if service not in barber.services:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This barber does not provide this service"
        )

    booking = Booking(
        user_id=user.id,
        barber_id=barber.id,
        service_id=service.id,
        starts_at=data.starts_at,
        ends_at=data.starts_at + timedelta(minutes=service.duration_minutes),
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This time slot is already taken")
    db.refresh(booking)
    return booking


@router.get("/my", response_model=list[BookingRead])
def my_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Booking).where(Booking.user_id == user.id).order_by(Booking.starts_at)
    return db.scalars(stmt).all()


@router.post("/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(
    booking_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, booking_id)
    if booking is None or booking.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    booking.status = BookingStatus.cancelled
    db.commit()
    db.refresh(booking)
    return booking