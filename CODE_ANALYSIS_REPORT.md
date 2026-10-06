# SmartExp v2 Backend — Code Analysis Report

**Review date:** October 3, 2026  
**Scope:** Current repository source, migrations, configuration example, and tests. No code was changed as part of this review. Tests were not run.

## Executive summary

This repository is a small FastAPI backend prototype with a functioning authentication path: signup hashes passwords, login issues JWT access tokens, and `/auth/me` validates a bearer token. SQLAlchemy async database access and Alembic migrations are in place, and there are auth integration tests.

The core transaction and budget domain is now implemented, while the AI, RAG, and voice capabilities described in `SmartExp-AI-Architecture.md` are still absent. Before deployment, prioritize restricting CORS, handling bcrypt's 72-byte password limit, and making test database setup isolated and repeatable.

## Findings

### High — Password validation permits inputs bcrypt cannot process

`SignupRequest` accepts passwords up to 128 characters (`app/schemas/auth.py:6-9`), but bcrypt operates on at most 72 input bytes. `hash_password` sends the unbounded UTF-8 bytes directly to bcrypt (`app/core/security.py:9-13`). Depending on the installed bcrypt version, longer inputs can raise an exception during signup or be truncated, causing failures or different passwords to authenticate equivalently. The schema's character limit also does not enforce a byte limit for Unicode.

**Recommendation:** Define and enforce an explicit policy compatible with the chosen password hasher, preferably use a modern password-hashing library with an appropriate scheme, and test boundary cases.

### High — CORS policy is overly broad for credentialed requests

The app allows every origin, method, and header while enabling credentials (`app/main.py:15-22`). This permits arbitrary sites to make browser requests to the API; the wildcard-origin/credentials combination can also behave inconsistently across browsers and clients.

**Recommendation:** Read allowed frontend origins from deployment configuration and allow only the required methods and headers.

### Medium — Authenticated legacy users cannot sign in after migration

The migration adds `hashed_password` and backfills existing records with the literal `UNUSABLE_PASSWORD_RESET_REQUIRED` (`alembic/versions/913a6d41c3be_add_hashed_password_to_users.py:21-29`). Password verification rejects this non-bcrypt placeholder (`app/core/security.py:16-25`), and there is no password-reset flow in the API. Existing user rows therefore remain inaccessible through login after upgrade unless reset credentials are provisioned separately.

**Recommendation:** Document and implement a reset/provisioning flow for existing users before applying this migration to a database with real accounts.

### Medium — Auth integration tests use the configured application database

The test fixture builds its engine from the normal `settings.DATABASE_URL` (`tests/conftest.py:6-19`) and signup tests insert records without cleanup (`tests/test_auth.py:9-43`). This requires a separately managed test database to be configured manually and can leave persistent data behind or accidentally write to a non-test database.

**Recommendation:** Require an explicit test database URL, create/drop or roll back test data deterministically, and fail fast when the configured database is not intended for tests.

### Medium — Duplicate signup has a check-then-insert race

Signup checks for an existing email and then inserts (`app/api/routes/auth.py:23-36`). The unique database index is useful, but concurrent requests can both pass the check; one then receives an unhandled integrity error rather than the documented `409 Conflict`.

**Recommendation:** Catch the unique-constraint violation, roll back the session, and translate it to the same conflict response.

### Low — SQL statement logging is enabled unconditionally

The shared async engine uses `echo=True` (`app/db/session.py:4-7`). This can produce noisy logs and expose SQL parameters or sensitive operational details in production logs.

**Recommendation:** Make SQL echo a development-only setting and default it off in production.

### Low — Dead code and duplicate return statements remain

`/db-test` contains a second unreachable return (`app/main.py:33-38`), and the expense placeholder has an unreachable legacy return (`app/api/routes/expenses.py:9-16`). These do not change runtime behavior, but add confusion during maintenance.

## Current implementation overview

- **API:** FastAPI app, root health response, database connectivity probe, auth router, transaction CRUD/summary routes, and budget routes (`app/main.py`).
- **Authentication:** Email normalization, bcrypt hashing, JWT access tokens with expiration/type claims, and database-backed bearer-user lookup (`app/services/auth.py`, `app/core/security.py`, `app/api/deps.py`).
- **Persistence:** Async SQLAlchemy engine/session and a `User` model; Alembic migrations include the user table and password hash (`app/db`, `app/models/user.py`, `alembic/versions`).
- **Tests:** Auth coverage includes signup, duplicate email, login, invalid credentials, and `/auth/me` token cases (`tests/test_auth.py`). Tests depend on a live configured PostgreSQL database.
- **Implemented:** User-owned transactions, income/expense CRUD, date/category filtering, spending summaries, and period-based budget status.
- **Not implemented:** Goals, AI orchestration/tools, RAG/vector storage, conversation history, and voice pipelines.

## Suggested order of work

1. Set a safe, configurable CORS allowlist and disable SQL echo outside development.
2. Resolve the password length/byte behavior and add a recovery path for users backfilled by the migration.
3. Isolate tests behind a dedicated test database and make data cleanup deterministic.
4. Map the core transaction domain and implement authenticated expense CRUD.
5. Add the AI/RAG/voice architecture only after the core financial data and authorization boundaries are established.

## Verification limits

This is a source review only. The test suite was not run, and database connectivity, migration execution, and runtime behavior were not independently verified. The existing `.env` file was not inspected; it is untracked in this checkout and should remain outside version control.
