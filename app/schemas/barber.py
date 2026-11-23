from pydantic import BaseModel, ConfigDict


class BarberCreate(BaseModel):
    name: str
    description: str | None = None


class BarberUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class BarberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool