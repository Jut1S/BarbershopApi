from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.deps import get_current_admin

from app.schemas.barber import BarberCreate, BarberRead, BarberUpdate
from datetime import date, datetime, time, timedelta, timezone
from app.models import Barber, Booking, BookingStatus, Service
from app.schemas.service import ServiceRead

router = APIRouter(prefix="/barbers", tags=["barbers"])


@router.get("", response_model=list[BarberRead])
def list_barbers(db: Session = Depends(get_db)):
    return db.scalars(select(Barber).order_by(Barber.id)).all()


@router.get("/{barber_id}", response_model=BarberRead)
def get_barber(barber_id: int, db: Session = Depends(get_db)):
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    return barber


@router.post("", response_model=BarberRead, status_code=201,
             dependencies=[Depends(get_current_admin)])
def create_barber(data: BarberCreate, db: Session = Depends(get_db)):
    barber = Barber(**data.model_dump())
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber


@router.patch("/{barber_id}", response_model=BarberRead,
              dependencies=[Depends(get_current_admin)])
def update_barber(barber_id: int, data: BarberUpdate, db: Session = Depends(get_db)):
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(barber, field, value)
    db.commit()
    db.refresh(barber)
    return barber


@router.delete("/{barber_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(get_current_admin)])
def deactivate_barber(barber_id: int, db: Session = Depends(get_db)):
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    barber.is_active = False
    db.commit()

WORK_START = time(9, 0)
WORK_END = time(18, 0)
SLOT_STEP = timedelta(minutes=30)
SHOP_TZ = timezone(timedelta(hours=5))  # часовой пояс барбершопа


@router.get("/{barber_id}/slots", response_model=list[datetime])
def get_free_slots(
    barber_id: int,
    date: date,
    service_id: int,
    db: Session = Depends(get_db),
):
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    if service not in barber.services:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This barber does not provide this service"
        )

    duration = timedelta(minutes=service.duration_minutes)
    day_start = datetime.combine(date, WORK_START, tzinfo=SHOP_TZ)
    day_end = datetime.combine(date, WORK_END, tzinfo=SHOP_TZ)

    bookings = db.scalars(
        select(Booking).where(
            Booking.barber_id == barber_id,
            Booking.status == BookingStatus.confirmed,
            Booking.starts_at < day_end,
            Booking.ends_at > day_start,
        )
    ).all()

    now = datetime.now(timezone.utc)
    slots = []
    current = day_start
    while current + duration <= day_end:
        slot_end = current + duration
        is_free = current > now and all(
            not (current < b.ends_at and slot_end > b.starts_at) for b in bookings
        )
        if is_free:
            slots.append(current)
        current += SLOT_STEP
    return slots

@router.get("/{barber_id}/services", response_model=list[ServiceRead])
def list_barber_services(barber_id: int, db: Session = Depends(get_db)):
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    return barber.services


@router.put("/{barber_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(get_current_admin)])
def add_service_to_barber(barber_id: int, service_id: int, db: Session = Depends(get_db)):
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    if service not in barber.services:
        barber.services.append(service)
        db.commit()


@router.delete("/{barber_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(get_current_admin)])
def remove_service_from_barber(barber_id: int, service_id: int, db: Session = Depends(get_db)):
    barber = db.get(Barber, barber_id)
    if barber is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Barber not found")
    service = db.get(Service, service_id)
    if service is not None and service in barber.services:
        barber.services.remove(service)
        db.commit()