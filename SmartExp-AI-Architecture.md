# SmartExp AI Backend – Architecture & Strategy

**Version:** 2.0 (AI-Powered)  
**Last Updated:** September 2026  
**Status:** Starting from scratch (new backend repository)

---

## 1. Project Vision

Build a **Jarvis-style personal finance assistant** that:

- Understands natural language (typed or spoken)
- Takes real actions (add expense, set budget, check spending, etc.)
- Remembers user context (past expenses, budgets, goals)
- Replies in a natural, conversational way
- Works reliably with voice input

**Core Principle (2026 Reality):**  
Use modern Gen AI APIs (Claude / GPT / Gemini) + RAG + Tool Calling.  
**Do not** train a model from scratch unless you later have massive scale, proprietary data, and a dedicated ML team.

---

## 2. Why We Are Moving Away From a Custom Classification Model

| Factor                        | Old Approach (Classification Model) | New Approach (LLM + RAG + Tools) | Winner      |
|-------------------------------|-------------------------------------|----------------------------------|-------------|
| Time to good product          | Already built                       | 2–6 weeks for strong version     | New         |
| Natural conversation quality  | Limited                             | Excellent                        | New         |
| Handling messy language       | Weak                                | Outstanding                      | New         |
| Taking actions                | Manual mapping                      | Native Tool Calling              | New         |
| Multi-turn & context          | Hard                                | Natural                          | New         |
| Maintenance                   | You retrain for every new intent    | Provider improves models         | New         |
| Cost                          | Very low after training             | Pay-per-use                      | Old (short-term) |
| Privacy & Control             | Full control                        | Data goes to provider            | Depends     |

**Conclusion:**  
A pure intent classification model is good for simple structured commands but too limited for a true Jarvis experience. We keep the spirit of the old system (actions on expenses/budgets) but replace the brain with a modern LLM agent.

---

## 3. Repository Strategy Decision

**Decision:** Create a **new backend repository** and start from scratch.

### Reasons
- Old backend is tightly coupled to the classification model
- We want a clean architecture designed for LLM agents, tools, and RAG from day one
- Avoid carrying technical debt
- Old version can continue running independently if needed

### Naming Suggestion
- `smartexp-ai-backend` or `smartexp-backend-v2`

### Frontend
- Keep the existing React.js frontend for now
- Update API endpoints later when the new backend is ready

### Database
- Prefer reusing the same PostgreSQL database (or clean migration)
- Add `pgvector` extension for RAG

---

## 4. Recommended High-Level Architecture

```
User (Voice / Text)
        ↓
[React Frontend]
        ↓
Speech-to-Text (Deepgram / Whisper / Gemini)
        ↓
[FastAPI Backend - New Repo]
    ├── Conversation Manager (Redis)
    ├── RAG Retriever (PostgreSQL + pgvector)
    ├── LLM Orchestrator (Claude 4 / GPT-4.1 / Gemini 2.5)
    └── Tool Executor
        ↓
Actions → Database (add expense, update budget, etc.)
        ↓
Natural Language Response
        ↓
Text-to-Speech (ElevenLabs / OpenAI TTS)
        ↓
User hears reply
```

---

## 5. Tech Stack (Recommended)

### Backend
- **Framework:** FastAPI
- **LLM Orchestration:** Official SDKs or LangChain / LlamaIndex
- **Primary LLM:** Claude 4 Sonnet or GPT-4.1
- **Fallback / Cheap model:** Gemini 2.5 Flash or Claude Haiku
- **Embeddings:** OpenAI `text-embedding-3-small` or Voyage
- **Database:** PostgreSQL + pgvector
- **Cache / Short-term Memory:** Redis
- **Auth:** Keep existing auth system or migrate JWT / session

### Voice
- **Speech-to-Text:** Deepgram Nova-2 (recommended) or OpenAI Whisper / Gemini
- **Text-to-Speech:** ElevenLabs or OpenAI TTS

### Frontend (existing)
- React.js (update API base URL and add voice recording UI later)

---

## 6. Core Tools the AI Agent Must Have

These are the functions the LLM can call:

- `add_expense` – amount, category, merchant, date, notes
- `add_income`
- `get_spending_summary` – by period / category
- `get_budget_status`
- `set_budget`
- `get_goals_progress`
- `create_goal`
- `search_transactions`
- `generate_report`
- `categorize_transaction` (optional)

The LLM is instructed to **always call tools** instead of inventing numbers.

---

## 7. Database Design (Key Tables)

- `users`
- `transactions` (with embedding vector column)
- `budgets`
- `goals`
- `conversation_sessions` / short-term history (or keep in Redis)
- Vector search via `pgvector` on transaction notes + categories

**RAG Strategy:**
- Embed every new transaction
- On every user message → retrieve top relevant past transactions + current budgets + goals
- Combine with recent conversation history

---

## 8. How a Typical Conversation Works

**User says:**  
“Add 850 rupees for dinner at Pizza Hut yesterday”

1. Speech → Text
2. Backend retrieves relevant context (RAG)
3. LLM understands intent → calls `add_expense` tool
4. Tool saves to database
5. LLM generates natural reply: “Done. I’ve added ₹850 under Food for Pizza Hut on yesterday.”
6. Reply is converted to speech and played

**User says:**  
“How much did I overspend on food this month?”

1. LLM calls `get_spending_summary` + `get_budget_status`
2. Calculates difference
3. Replies naturally with the number and context

---

## 9. Folder Structure (New Backend)

```
smartexp-ai-backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py
│   │       ├── voice.py
│   │       └── ...
│   ├── agents/
│   │   └── finance_agent.py
│   ├── tools/
│   │   ├── expense.py
│   │   ├── budget.py
│   │   ├── goals.py
│   │   └── reports.py
│   ├── rag/
│   │   └── retriever.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── llm.py
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── vector.py
│   └── prompts/
│       └── system.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 10. When (and Only When) Fine-tuning or Training Your Own Model Makes Sense

Only consider later if:
- You have tens of thousands of conversations per day
- API costs become too high
- You need strict data privacy (financial data never leaves your servers)
- You have collected high-quality conversation data

Even then → prefer fine-tuning an open-source model (Llama 3.1/4, Mistral, etc.) rather than training from scratch.

---

## 11. Cost Expectations (Realistic)

| Component              | Approximate Cost (moderate usage) |
|------------------------|-----------------------------------|
| Primary LLM            | $0.15 – 0.40 per conversation     |
| STT + TTS              | $0.01 – 0.04 per turn             |
| Embeddings             | Very low                          |
| **Per active user/month** | $3 – 12 (typical)              |

Start with Claude 4 Sonnet for best quality. Add cheaper models for simple queries later.

---

## 12. Next Steps (Implementation Order)

1. Create new repository and basic FastAPI project
2. Set up PostgreSQL + pgvector + Redis
3. Define database models (copy useful parts from old backend)
4. Implement core tools (`add_expense`, `get_spending_summary`, etc.)
5. Build the LLM agent with tool calling
6. Add RAG retrieval
7. Create `/chat` endpoint
8. Add voice endpoints (STT + TTS)
9. Connect existing React frontend
10. Test real conversations and improve system prompt

---

## 13. Key Principles Going Forward

- Prefer calling tools over guessing any financial number
- Keep replies natural, concise, and helpful
- Always confirm actions clearly
- Design for voice from the beginning
- Keep the old classification model archived (do not bring it into this repo)

---

**This document should be placed in the root of the new backend repository** as `ARCHITECTURE.md` or `docs/STRATEGY.md`.

You can update it as the project evolves.