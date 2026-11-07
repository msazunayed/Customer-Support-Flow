# Support Flow Studio

A customer support pipeline built with CrewAI Flows, served by FastAPI, with a
browser UI written in plain HTML, CSS and JavaScript.

Each ticket moves through five steps:

1. `receive_ticket` (start): creates the ticket ID and records intake.
2. `categorize_ticket`: classifies the issue with an LLM on Groq, or with keywords when no API key is set.
3. `route_by_category` (router): sends the ticket to a category branch.
4. A category handler: sets priority and logs the team action.
5. `resolve_ticket`: closes the ticket with a resolution note.

## Project structure

```
customer-support-flow/
├── app/
│   ├── __init__.py
│   ├── models.py      # Pydantic state and request models
│   ├── flow.py        # CrewAI Flow definition and run_ticket()
│   └── server.py      # FastAPI app: JSON API and static files
├── static/
│   ├── index.html     # Page layout
│   ├── styles.css     # Dark glass UI and animations
│   └── app.js         # Frontend logic
├── .env.example       # Environment variable template
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10 or newer (CrewAI requires it)
- pip
- A Groq API key (optional)

## Setup

Open a terminal in the project folder.

**1. Create a virtual environment**

macOS and Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**2. Install the dependencies**

```bash
pip install -r requirements.txt
```

CrewAI pulls in several packages, so the first install can take a few minutes.

**3. Configure the environment (optional)**

Copy the template and add your Groq key if you want LLM categorization:

macOS and Linux:
```bash
cp .env.example .env
```

Windows:
```powershell
copy .env.example .env
```

Then edit `.env`:

```
GROQ_API_KEY=your-groq-key-here
SUPPORT_MODEL=groq/openai/gpt-oss-120b
```

The model name uses the `groq/` prefix, which tells LiteLLM to send the request to Groq. The rest is Groq's model ID.

If you skip this step, the app uses a built-in keyword classifier. Everything
still works, including the UI.

## Run the web app

```bash
uvicorn app.server:app --reload
```

Open http://127.0.0.1:8000 in your browser.

The header badge shows which categorization engine is active.

## Run the flow from the command line

```bash
python -m app.flow
```

This processes one sample ticket and prints the final state.

## API endpoints

| Method | Path                                | Purpose                          |
|--------|-------------------------------------|----------------------------------|
| GET    | `/api/health`                       | Engine status                    |
| POST   | `/api/tickets`                      | Run the flow for a new ticket    |
| GET    | `/api/tickets`                      | List processed tickets           |
| GET    | `/api/tickets/{ticket_id}`          | Get one ticket                   |
| POST   | `/api/tickets/{ticket_id}/feedback` | Save a 1 to 5 satisfaction score |

Interactive API docs are available at http://127.0.0.1:8000/docs.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'app'`**: run the commands from the project root, the folder that contains `app/`.
- **Port 8000 is already in use**: run `uvicorn app.server:app --reload --port 8001` and open port 8001.
- **Badge says "Server unreachable"**: check that uvicorn is still running in the terminal.
- **LLM errors**: the app falls back to keyword categorization automatically and prints the error in the terminal. Check `GROQ_API_KEY` and `SUPPORT_MODEL` in `.env`, and restart uvicorn after editing it.
- **Tickets disappear after a restart**: storage is in memory by design. Add a database if you need persistence.

## output

https://github.com/user-attachments/assets/007f149d-da1d-46cc-ad02-3ecb911677a2

