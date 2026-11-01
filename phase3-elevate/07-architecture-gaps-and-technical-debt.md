# 07. Architecture gaps and technical debt

Section A lists problems that the documents report from their own code reading. I have not verified them. Section B lists problems I infer from the documents taken together. Section C lists my recommendations. Nothing here proposes a stack, and nothing designs Phase 4.

## A. Problems reported by the documents (code-level claims, not re-verified)
| # | Problem | Component | Document label | Ledger |
|---|---|---|---|---|
| A1 | No authentication enforced on any API (Python or .NET); frontend session is a localStorage flag | All three | CONFIRMED / VERIFIED / static analysis | P3-030, P3-031, P3-033 |
| A2 | Plain-text password compare; login returns the full user row; hardcoded fallback DB credentials | .NET API | static analysis | P3-032, P3-039 |
| A3 | RBAC stored but never enforced; mapped by department and job title, not user | .NET API | static analysis | P3-035 |
| A4 | Unsigned or unchecked webhooks: Recall (TODO), Jira, Graph `clientState` | AI service | CONFIRMED | P3-036, P3-037 |
| A5 | Prompt-injection surface | AI service | CONFIRMED | P3-038 |
| A6 | No retry on LLM insight tasks; no structured-output validation; no evaluation suite | AI service | CONFIRMED / VERIFIED | P3-064, P3-065 |
| A7 | Routing-key mismatch for 14 tasks; chord callbacks can be skipped; de-duplication fails open | AI service | CONFIRMED / INFERRED | P3-017, P3-018, P3-051 |
| A8 | No ORM relationships; no `onupdate`; polymorphic reference with no FK; logical FKs in .NET | Both backends | CONFIRMED | P3-045, P3-046, P3-047 |
| A9 | No CI; tests mocked or absent | All three | VERIFIED / static analysis | P3-090, P3-091 |
| A10 | CORS: internal IP hardcoded (Python); AllowAll (.NET); Swagger on in production | Both backends | CONFIRMED | P3-039 |
| A11 | Frontend/backend contract mismatch on Project and Customer `PUT` | Frontend vs .NET | conflict | P3-085 |

## B. Architectural weaknesses (INFERRED from the documents together)
1. **Split-brain data ownership.**
   - Customers, projects and meetings exist in the AI-service database and in the .NET "elevate" and "Meetings" databases, under different table names [P3-041].
   - There is no documented ownership rule or sync, which is a likely source of data inconsistency.
2. **Two backends with no contract between them.**
   - The documented UI talks only to the .NET API.
   - The AI service's rich output has no documented path to users [P3-082].
3. **Weak entity relationships.** Logical links with no FKs and a polymorphic `reference_id` mean the database cannot guarantee integrity [P3-046, P3-047].
4. **AI output is not a managed business record.**
   - It is written without review [P3-067] and overwritten on regeneration [P3-046].
   - It is deleted with its transcript [P3-042], so it carries no lifecycle [P3-068, P3-069].
5. **Duplicate functionality:**
   - "Needs Attention" exists in the frontend rules and in Python models [P3-083].
   - Customer and project data is held in two places [P3-041].
   - RBAC tables appear in both backends' model lists [P3-035].
6. **Missing lifecycle management** for action items, commitments, risks, alerts and health (see `06`).
7. **No membership model.** Project people are strings on the project [P3-048]. That rules out "my projects" scoping, permissions by project, and owner resolution for action items.
8. **Single-tenant shape** [P3-049]. This is acceptable internally, but a constraint if the product is ever offered beyond Kensium.
9. **Scalability notes (from the documents):**
   - Seven full-transcript LLM calls per meeting.
   - DB-backed Celery results.
   - The .NET API has no pagination (a fixed 50 meetings) and returns full tables.

## C. Reuse, redesign, retire (recommendations; Phase 4 will decide)
| Item | Recommendation | Why |
|---|---|---|
| Graph capture (subscriptions, de-duplication, delegated/app tokens, Meet Now) | **Reuse the logic** | Most mature, tested area per the documents [P3-050, P3-051] |
| Recording control and Do-Not-Record policy | **Reuse** | Best-tested feature; consent is a compliance need [P3-080] |
| Recall integration | **Reuse, after adding signature verification** | [P3-036, P3-052] |
| Jira/JSM and Tempo sync | **Reuse the sync logic; redesign auth** (Basic auth) and add write-back | [P3-053, P3-054] |
| Prompt templates and insight taxonomy (7 types + ticket sentiment + stage + cross-entity) | **Reuse as a starting taxonomy; redesign the output contract** (structured, validated, versioned) | [P3-061, P3-065] |
| Dirty-flag cross-entity scheduler | **Reuse the pattern** | Sound job model with reaper and sweep [P3-066] |
| Insight storage as transcript-owned rows with overwrite and cascade | **Redesign** | No lifecycle, no history [P3-042, P3-046] |
| .NET Elevate 2.0 API as built | **Retire or replace** | No auth, plain-text passwords, no service layer, duplicate data model [P3-031, P3-032, P3-041] |
| Frontend auth and session model | **Retire** | localStorage flag only [P3-033] |
| Client-side "Needs Attention" rules | **Retire into a server-side rule** | Duplicated, invisible to other consumers [P3-083] |

**All of section C is conditional.** It rests on documentation only and must be confirmed against the source code before Phase 4 commits to any of it.
