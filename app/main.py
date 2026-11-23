from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers import barbers, services, auth, bookings

app = FastAPI(title="Barbershop API")

app.include_router(auth.router)
app.include_router(barbers.router)
app.include_router(services.router)
app.include_router(bookings.router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}