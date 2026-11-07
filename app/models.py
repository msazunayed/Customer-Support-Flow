from typing import List

from pydantic import BaseModel, Field

CATEGORIES = ["Billing", "Account Access", "Technical Issue", "Feature Request", "Other"]


class SupportTicketState(BaseModel):
    # Structured state shared by every step of the support flow.
    ticket_id: str = ""
    customer_name: str = ""
    issue_description: str = ""
    category: str = ""
    priority: str = "medium"
    resolution: str = ""
    satisfaction_score: int = 0
    history: List[str] = Field(default_factory=list)


class TicketRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=80)
    issue_description: str = Field(..., min_length=5, max_length=2000)


class FeedbackRequest(BaseModel):
    score: int = Field(..., ge=1, le=5)
