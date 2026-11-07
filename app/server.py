import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.flow import get_model, llm_enabled, run_ticket
from app.models import FeedbackRequest, TicketRequest

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Customer Support Flow")

# In-memory store. Tickets are lost when the server restarts.
TICKETS: dict[str, dict] = {}


@app.get("/api/health")
def health():
    enabled = llm_enabled()
    return {
        "status": "ok",
        "llm_enabled": enabled,
        "model": get_model() if enabled else "keyword engine",
    }


@app.post("/api/tickets")
def create_ticket(payload: TicketRequest):
    result = run_ticket(payload.customer_name.strip(), payload.issue_description.strip())
    TICKETS[result["ticket_id"]] = result
    return result


@app.get("/api/tickets")
def list_tickets():
    return list(TICKETS.values())[::-1]


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = TICKETS.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/api/tickets/{ticket_id}/feedback")
def submit_feedback(ticket_id: str, payload: FeedbackRequest):
    ticket = TICKETS.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket["satisfaction_score"] = payload.score
    return ticket


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
