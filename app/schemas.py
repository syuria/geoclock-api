"""Request validation with Pydantic. Bad input returns 400 with details."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class SiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: float = Field(default=150, gt=0, le=5000)


class EmployeeIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    hourly_rate: Decimal = Field(gt=0, max_digits=8, decimal_places=2)


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ClockInIn(Location):
    employee_id: int
    site_id: int


class ClockOutIn(Location):
    employee_id: int


class PeriodQuery(BaseModel):
    start: date
    end: date
