from typing import Any
from pydantic import BaseModel, Field

class ReasonRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    candidates: list[dict[str, Any]] = Field(min_length=1, max_length=50)
    current_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")

class ReasonOutput(BaseModel):
    answer_text: str = Field(min_length=1, max_length=1200)
    chosen_ids: list[str] = Field(default_factory=list, max_length=50)
    excluded_ids: list[str] = Field(default_factory=list)
    exclusion_reason: dict[str, str] = Field(default_factory=dict)
