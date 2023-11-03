from pydantic import BaseModel
from pydantic.fields import Field
from typing import Optional


class FeedbackIn(BaseModel):
    player_name: str = Field(..., example="Player1")
    vote: int = Field(..., ge=-1, le=1, description="Vote is -1, 0 or 1")
    prediction: str = Field(..., example="Real_Player")
    confidence: Optional[float] = Field(0, ge=0, le=1, description="double from 0 to 1")
    subject_id: int = Field(..., example=1)
    feedback_text: Optional[str] = Field(None, example="Test feedback")
    proposed_label: Optional[str] = Field(None, example="Real_Player")


class FeedbackOut(BaseModel):
    message: str = Field(..., example="Feedback submitted successfully")