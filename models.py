from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel


class DutyType(StrEnum):
    COFFEE = "coffee"
    FRIDGE = "fridge"


class OfficeMember(BaseModel):
    id: int
    username: str
    full_name: str | None = None
    coffee_drinker: bool = True
    active: bool = True


class DutyAssignment(BaseModel):
    id: int
    member_id: int
    duty_type: DutyType
    assigned_at: datetime
    cycle_id: int


class CycleInfo(BaseModel):
    cycle_id: int
    duty_type: DutyType
    assigned_member_ids: set[int]


class AssignmentResult(BaseModel):
    success: bool
    message: str
