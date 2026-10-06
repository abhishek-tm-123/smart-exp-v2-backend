# SmartExp Jarvis CLI

## Start the backend

From the project folder, apply database migrations once:

```powershell
.\venv\Scripts\alembic.exe upgrade head
```

Start the API in one PowerShell window:

```powershell
.\venv\Scripts\uvicorn.exe app.main:app --reload
```

The API should be available at `http://127.0.0.1:8000`.

## Start Jarvis CLI

Open a second PowerShell window in the same project folder:

```powershell
.\venv\Scripts\python.exe -m app.cli
```

If your API uses another address, supply it explicitly:

```powershell
.\venv\Scripts\python.exe -m app.cli --api-url http://127.0.0.1:8000
```

## Use it

Create an account with `/signup`, then use `/login`. Password input is hidden.

Once signed in, type natural language requests directly:

```text
I spent 120 on groceries today.
How much did I spend this month?
Set a Food budget of 5000 from 2026-10-01 to 2026-10-31.
What is my budget status?
```

Commands:

- `/help` — show commands
- `/signup` — create an account
- `/login` — sign in
- `/logout` — remove the in-memory login token
- `/me` — show the signed-in account
- `/transactions` — list transactions
- `/summary YYYY-MM-DD YYYY-MM-DD` — show a spending summary
- `/budgets` — show budgets active today
- `/quit` — exit the CLI

The login token stays only in memory for the active CLI session.

Jarvis requests can take up to two minutes because the assistant may make a Gemini tool-selection call, query the finance database, and make a second Gemini call to produce its response. The CLI displays `Jarvis is thinking...` while it waits.
