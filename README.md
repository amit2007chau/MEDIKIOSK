# MEDIKIOSK — From patient voice to verified clinical timeline

MediKiosk is a local, end-to-end hackathon prototype for hospital pre-consultation intake. It turns patient-reported information and previous documents into an evidence-linked, clinician-reviewable timeline. It is not an autonomous medical device: it does not diagnose, prescribe, or replace a doctor.

## What is included

- A touch-first multilingual patient kiosk (English/Hindi), with text, touch and optional browser speech recognition.
- An adaptive complaint engine for fever, cough, chest pain, breathlessness, headache, abdominal pain, vomiting, diarrhoea and general complaints.
- FastAPI backend with JWT access/refresh tokens, Argon2 password hashing, role-based authorization and audit records.
- Synthetic demo patients, real database-backed encounters, consent, immutable raw answers, document uploads, mock OCR, clinical extraction, timeline construction, potential-red-flag rules and clinician summaries.
- Separate doctor review and triage dashboards which call protected backend APIs; the staff dashboard has authenticated WebSocket updates plus a refresh fallback.
- Evidence links to uploaded records, doctor edit/verify flow, FHIR-compatible export, and working mock HIS/ABDM delivery.
- Docker Compose for PostgreSQL, Redis, MinIO, FastAPI and three independently deployed React applications. Local development automatically uses SQLite and filesystem storage when services are unavailable.

## Architecture

```text
Patient kiosk (3000) ──┐
Doctor review (3001) ──┼── FastAPI API + WebSocket (8000) ── PostgreSQL
Triage dashboard (3002)┘              │                     ├─ Redis
                                      ├─ mock OCR / ASR / TTS / LLM
                                      ├─ local mirror + MinIO documents
                                      └─ mock HIS / ABDM + FHIR bundle
```

The backend is a modular monolith. Provider interfaces in `backend/app/services/providers.py` allow a real OCR, ASR, TTS, LLM, HIS or ABDM implementation to replace a deterministic mock without changing workflows. Background document extraction intentionally does not block the kiosk. A local copy of an upload remains available if MinIO is unreachable in development.

## Project structure

```text
apps/
  patient-kiosk/       # tablet/touch workflow
  doctor-dashboard/    # clinician review, evidence and verification
  staff-dashboard/     # realtime triage queue
backend/
  app/api/v1/          # auth, kiosk, clinical, operations, admin routes
  app/models/          # SQLAlchemy data model
  app/services/        # questions, OCR/extraction, flags, summaries, storage
  migrations/          # Alembic initial migration
  tests/               # API integration and RBAC tests
shared/ui/             # shared visual-language documentation
docker-compose.yml
```

## Data model

`users`, `patients`, `encounters`, `kiosk_sessions`, and `consents` cover ownership and intake state. `answers` retains original patient language and structured values. `medical_documents`, `clinical_entities`, and `timeline_events` preserve traceable evidence. `red_flags` holds deterministic potential alerts; `clinical_summaries` holds draft and verified clinician records; `audit_logs` records privileged actions.

## Run locally

Prerequisites: Docker Desktop (recommended), or Python 3.10+ and Node 20+.

### Full stack (recommended)

```bash
copy .env.example .env
docker compose up --build
```

Compose applies the initial Alembic migration and seeds the synthetic demo data when the backend starts. Browse:

- Patient kiosk: <http://localhost:3000>
- Doctor dashboard: <http://localhost:3001>
- Triage dashboard: <http://localhost:3002>
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health/detailed>
- MinIO console: <http://localhost:9003>

### Host development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

In three other terminals, run `npm install` and `npm run dev` in each folder under `apps/`. The supplied `.env` uses SQLite (`backend/data/medikiosk.db`) and works without Docker services.

## Demo accounts

All accounts use `DemoPass123!` and all patient names/documents are explicitly synthetic.

| Role | Email | Workspace |
| --- | --- | --- |
| Admin | `admin@medikiosk.local` | Doctor dashboard/API admin routes |
| Doctor | `doctor@medikiosk.local` | Doctor dashboard |
| Triage staff | `staff@medikiosk.local` | Staff dashboard |

## Demo journey

1. In the kiosk select हिन्दी, choose a demo patient, consent, then choose **Chest pain** and **Severe** breathing difficulty.
2. Finish the adaptive questions. Add a PDF/JPG/PNG to exercise the mock OCR path; document status changes to `PROCESSED` in the background.
3. Submit intake. A deterministic `HIGH` potential urgent-symptom prompt is created and sent via WebSocket to triage.
4. Sign into triage, acknowledge/escalate/resolve the prompt.
5. In clinical review, open the encounter. Inspect patient-reported history, timeline, document source, extracted evidence and the non-diagnostic summary. Edit and verify it.
6. Click **Send verified record to mock HIS**; `GET /api/v1/encounters/{id}/fhir` returns the FHIR-compatible Bundle and the mock ABDM endpoint is also available.

## API overview

`POST /api/v1/auth/login`, `/refresh`, `/me` authenticate users. Public-demo kiosk endpoints are session-bound: `GET /kiosk/demo-patients`, `POST /kiosk/identify`, consent, current-question, answer, document upload, and complete. Clinical roles can read `/patients`, `/encounters`, documents, summaries and FHIR. Doctors/admins alone edit or verify summaries and sync integrations. Triage/admins alone update red-flag status. Admins alone manage users and view audit logs. Swagger describes schemas and examples.

Protected document and patient routes verify the caller's role; session-bound kiosk requests verify the expiring session belongs to the associated patient/encounter. The browser's protected route handling is a usability feature, never the authority—the backend enforces every role decision.

## Migrations, seeding, and tests

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
python -m app.seed
python -m pytest -q
```

From the repository root, use `make test` to run backend tests and each Vite production build. `make dev` delegates to Compose.

## Configuration and safety

Copy `.env.example` for container settings. `DATABASE_URL`, `REDIS_URL`, `MINIO_*`, `JWT_*`, `CORS_ORIGINS`, `MAX_UPLOAD_BYTES`, and provider mode variables are documented there. Replace the development JWT secret and remove demo credentials before any non-demo deployment.

Uploads accept only PDF/JPEG/PNG under 10 MB, store generated UUID-based paths, and reject unsupported types. Application logs avoid document contents, passwords and tokens. This prototype does not include production-grade antivirus scanning, key management, consent law localisation, clinical validation, real ABDM credentials, or a real OCR/ASR/LLM service; its mocks are intentional so the complete flow works offline.

## Troubleshooting

- **Port in use:** edit the host side of the `ports` mapping in Compose.
- **Backend cannot connect:** wait for PostgreSQL startup, then check `docker compose logs backend`; host-mode defaults to SQLite.
- **CORS/API request failure:** verify `VITE_API_URL` and `CORS_ORIGINS` point to the selected frontend origins.
- **No speech button result:** browser speech recognition is optional; touch/text is always available.
- **No live triage event:** the dashboard reconnects every three seconds and polls every 15 seconds; ensure the API is reachable and the staff token is valid.
- **MinIO unavailable:** the local mirror is intentional for development; documents remain accessible to clinical reviewers.
