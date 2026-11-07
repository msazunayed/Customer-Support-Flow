# Customer support flow built with CrewAI Flows.
# Order: receive_ticket -> categorize_ticket -> route_by_category -> handler -> resolve_ticket
# Uses an LLM on Groq when GROQ_API_KEY is set, otherwise a keyword classifier.
import os
import random
import string

from dotenv import load_dotenv
from crewai.flow.flow import Flow, listen, or_, router, start

from app.models import CATEGORIES, SupportTicketState

load_dotenv()

DEFAULT_MODEL = "groq/openai/gpt-oss-120b"


def llm_enabled() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def get_model() -> str:
    return os.getenv("SUPPORT_MODEL", DEFAULT_MODEL)


CATEGORY_KEYWORDS = {
    "Billing": ["bill", "invoice", "charge", "payment", "refund", "subscription", "price", "paid"],
    "Account Access": ["login", "log in", "password", "locked", "access", "sign in", "account", "otp", "2fa"],
    "Technical Issue": ["error", "crash", "bug", "broken", "not working", "slow", "fail", "loading", "timeout"],
    "Feature Request": ["feature", "would be nice", "please add", "wish", "suggest", "request", "support for"],
}


def keyword_category(text: str) -> str:
    lowered = text.lower()
    scores = {cat: sum(1 for word in words if word in lowered) for cat, words in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def llm_category(text: str):
    # Ask the LLM for a category; returns None if no key is set or the call fails.
    if not llm_enabled():
        return None
    try:
        from crewai import LLM

        llm = LLM(model=get_model())
        prompt = f"""
        Categorize the following customer support issue into one of these categories:
        - Billing
        - Account Access
        - Technical Issue
        - Feature Request
        - Other

        Issue: {text}

        Return only the category name.
        """
        answer = str(llm.call(prompt)).strip().lower()
        for cat in CATEGORIES:
            if cat.lower() == answer:
                return cat
        for cat in CATEGORIES:
            if cat.lower() in answer:
                return cat
        return None
    except Exception as exc:
        print(f"[llm_category] LLM call failed, using keyword fallback: {exc}")
        return None


class CustomerSupportFlow(Flow[SupportTicketState]):

    @start()
    def receive_ticket(self):
        # In a real app the ticket would come from an API or helpdesk webhook.
        if not self.state.ticket_id:
            self.state.ticket_id = "TKT-" + "".join(random.choices(string.digits, k=5))
        self.state.history.append(f"Ticket {self.state.ticket_id} received")
        return "Ticket received"

    @listen(receive_ticket)
    def categorize_ticket(self, _):
        category = llm_category(self.state.issue_description) or keyword_category(self.state.issue_description)
        self.state.category = category
        self.state.history.append(f"Categorized as {category}")
        return category

    @router(categorize_ticket)
    def route_by_category(self, category):
        route = category.lower().replace(" ", "_")
        self.state.history.append(f"Routed to the {category} queue")
        return route

    @listen("billing")
    def handle_billing_issue(self):
        self.state.priority = "high"
        self.state.history.append("Billing team reviewing the charge")
        return "Billing issue handled"

    @listen("account_access")
    def handle_access_issue(self):
        self.state.priority = "high"
        self.state.history.append("Access team verifying the account")
        return "Access issue handled"

    @listen("technical_issue")
    def handle_technical_issue(self):
        self.state.history.append("Engineering triaging the bug report")
        return "Technical issue handled"

    @listen("feature_request")
    def handle_feature_request(self):
        self.state.priority = "low"
        self.state.history.append("Logged for the product backlog")
        return "Feature request logged"

    @listen("other")
    def handle_other(self):
        self.state.priority = "low"
        self.state.history.append("General support agent assigned")
        return "General issue handled"

    @listen(or_("billing", "account_access", "technical_issue", "feature_request", "other"))
    def resolve_ticket(self, resolution_info):
        self.state.resolution = f"Issue resolved: {resolution_info}"
        self.state.history.append("Ticket resolved")
        return self.state.resolution


def run_ticket(customer_name: str, issue_description: str) -> dict:
    # Run the full flow for one ticket and return its final state as a dict.
    flow = CustomerSupportFlow()
    flow.state.customer_name = customer_name
    flow.state.issue_description = issue_description
    flow.kickoff()
    return flow.state.model_dump()


if __name__ == "__main__":
    # Command line demo: python -m app.flow
    result = run_ticket(
        "Shakil Ahmed",
        "I'm locked out of my account and the password reset email never arrives",
    )
    for key, value in result.items():
        print(f"{key}: {value}")
