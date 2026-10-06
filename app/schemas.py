from datetime import datetime
from pydantic import BaseModel, field_validator

VALID_STATUSES = [
    "submitted",
    "researching",
    "building",
    "testing",
    "complete",
    "failed",
]

VALID_DISCIPLINES = [
    "Infrastructure",
    "Enchantment",
    "Alchemy",
    "Artifice",
    "Cartography",
    "Other",
]


class CommissionCreate(BaseModel):
    patron: str
    discipline: str
    title: str
    description: str

    @field_validator("discipline")
    @classmethod
    def discipline_must_be_valid(cls, v: str) -> str:
        if v not in VALID_DISCIPLINES:
            raise ValueError(
                f"discipline must be one of {VALID_DISCIPLINES}"
            )
        return v


class CommissionStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(
                f"status must be one of {VALID_STATUSES}"
            )
        return v


class NoteCreate(BaseModel):
    body: str


class JobOut(BaseModel):
    id: int
    commission_id: int
    status: str
    artifact_id: str | None
    report: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class NoteOut(BaseModel):
    id: int
    commission_id: int
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommissionOut(BaseModel):
    id: int
    patron: str
    discipline: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    notes: list[NoteOut] = []
    jobs: list[JobOut] = []

    model_config = {"from_attributes": True}
