# 02. Backend and frontend deep dive (as documented)

All findings are **DOCUMENTED ONLY** or **UNKNOWN**: no code was supplied. File paths and line numbers are the source documents' claims, repeated so that a code reviewer can check them. I have not verified them.

## A. Elevate AI Service (Python)

### A.1 Stack (handbook CONFIRMED; strategy VERIFIED against `pyproject.toml`)
- **Application:** Python 3.13, FastAPI 0.123 and Uvicorn.
- **Data:** SQLModel 0.0.27 on SQLAlchemy 2.0, psycopg 3 and Alembic.
- **Background work:** Celery 5.6 on Redis 7.
- **Integrations:** LiteLLM (<2.0), httpx and boto3.
- **Templates and telemetry:** Jinja2, plus OpenTelemetry exporting to SigNoz.
- Evidence: [P3-010, P3-014].

### A.2 API surface
The routers fall into these groups:

| Group | Purpose |
|---|---|
| Microsoft Graph | Calendar, meetings, users, subscriptions, OAuth, three webhook receivers, chat notices |
| LLM | Meeting insights, cross-entity AI insights, upsell lifecycle, transcript stage insights |
| Jira | Accounts, customers, projects, licenses, JSM tickets, JSM webhook |
| Recording | Recording control, on-demand recording, AWS recordings, transcript purge |
| Other | Recall AI webhook, Tempo worklogs |

- Router and endpoint counts conflict between documents: 26 routers (handbook) versus 64 endpoints across 25 routers (beginner review) [P3-012].
- **The pattern:** most POST endpoints queue a Celery task and return 202. The only DELETE is the transcript purge, which cascades to seven tables [P3-042].

### A.3 Documented strengths (to keep in mind for Phase 4)
- **Strict one-way layering**, with no circular imports reported [P3-011].
- **One queue per task:**
  - late acks and reject-on-worker-lost for crash safety [P3-014]
  - trace IDs carried from HTTP into Celery
  - OpenTelemetry tracing
- **Redis de-duplication:**
  - on every webhook source, using webhook IDs and resource paths [P3-051, P3-052]
  - a per-join-URL lock for on-demand recording
- **Recording control** is the most-tested feature; its stop/start state machine covers scopes and platforms [P3-080].

### A.4 Documented defects
| Defect | Source label | Ledger |
|---|---|---|
| No API authentication on any route | CONFIRMED/VERIFIED | P3-030 |
| Recall signature verification commented out; Jira unsigned; Graph `clientState` unchecked | CONFIRMED | P3-036, P3-037 |
| 14 tasks fall through to the `default` queue when dispatched ad hoc | CONFIRMED (beginner review) | P3-017 |
| No retry on the seven insight tasks | CONFIRMED (beginner review) | P3-064 |
| LLM run and token tracking possibly not recorded for insights | CONFLICT | P3-063 |
| `db_session()` docstring says it commits; it doesn't | CONFIRMED (beginner review p.15) | — |
| No `onupdate` on `updated_at`; no ORM relationships | CONFIRMED | P3-045 |
| Prompt-injection surface (`autoescape=False`) | CONFIRMED | P3-038 |
| Hardcoded CORS origins, including an internal IP | CONFIRMED | P3-039 |
| ~180 tests, all with a mocked DB; no CI | CONFIRMED/VERIFIED | P3-090, P3-091 |

## B. Elevate 2.0 API (.NET)

### B.1 Shape
- **Project:** a single ASP.NET Core 8 project, with 9 controllers and 9 entities.
- **Two DbContexts:**
  - `ApplicationDbContext` → database "elevate": customers, projects, users, roles, modules, role_permissions, role_assignments.
  - `MeetingsDbContext` → database "Meetings": `ai_pm_ms_meeting`, `ai_pm_llm_meeting_insights`.
- **Missing pieces:** no service layer, no migrations, no tests, no background work [P3-019, P3-047, P3-090].

### B.2 Endpoints
The API has 32 endpoints, and none requires authentication [P3-031]:

| Controller | Operations |
|---|---|
| Customer, Project, Meeting, MeetingInsight, Module, RoleAssignment | Read-only |
| Role, RolePermission | Full CRUD, including bulk |
| User | Read, two logins, and an update of four billing fields |

- **Quirks:**
  - Meeting returns only the latest 50 meetings, with no pagination.
  - MeetingInsight requires a meeting ID.
  - `PUT` and `PATCH` bulk do the same thing.
  - Soft-delete is applied inconsistently.

### B.3 Critical issues
- **Login:**
  - Plain-text string compare.
  - The full user row is returned.
  - No token is issued [P3-032].
- **Configuration:**
  - CORS allows all origins.
  - Swagger is on in production.
  - The configuration has hardcoded fallback DB credentials [P3-039].
- **RBAC:** stored but never enforced. Roles map to users by matching department and job title, not by user ID [P3-035].

## C. Elevate 2.0 frontend (React)

### C.1 Shape
- **App:** a single-page app with 16 page components, 2 of which are orphaned.
- **State and data:**
  - Zustand stores the authentication state in localStorage.
  - A single `ApiClient` built on fetch handles all calls.
- **Tooling gaps:** no React Query, no form or validation library, no tests, no CI configuration [P3-033, P3-090].

### C.2 Screens and what they really do
| Screen | Behaviour (documented) | Ledger |
|---|---|---|
| Login | Email and password posted to `/api/User/login-with-password`; Microsoft 365 button commented out | P3-033, P3-034 |
| Dashboard | **Static placeholder with hard-coded 0s** | P3-084 |
| Employees | List, filters, CSV export; edit of 4 billing fields | — |
| Projects / Customers | List and edit; the edit screens send a full-object `PUT` | P3-085 |
| Needs Attention (projects / customers) | **Client-side predicates** over the same lists | P3-083 |
| Roles / Role permissions | Editable permission matrix by department and job title (deletes each row, then bulk-creates) | P3-035 |
| Meetings | Lists `/api/Meeting` only; **no insight screen in the endpoint inventory** | P3-082 |

### C.3 The contract mismatch
**The frontend sends `PUT /api/Project/{id}` and `PUT /api/Customer/{id}`, but the .NET API documentation lists no such endpoints** [P3-085].
- **Possible explanations:**
  - the API is out of step with its documentation
  - those saves fail at runtime
  - another, undocumented service receives them
- **Status: UNKNOWN.** Only the code or a running system can settle it.

## D. Cross-component conclusions (INFERRED from the documents)
1. **The documented user interface shows almost none of the AI service's output.**
   - No screen calls insight endpoints, apart from a meetings list (where insights may be reached through the .NET API's MeetingInsight endpoint, but no screen calling it is documented).
   - Action items, commitments, sentiment, alerts and upsell signals have no documented screen [P3-082].
   - Some other user interface may exist; this is UNKNOWN.
2. **"Needs Attention" exists twice:**
   - as frontend rules
   - as Python models (`NeedsAttention`, `NeedsAttentionComment`)
   - Nothing documented connects the two [P3-083].
3. **No layer authenticates.** Each component's documentation points elsewhere for security.
