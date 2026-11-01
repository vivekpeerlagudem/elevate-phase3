"""Phase 3 evidence ledger builder + verifier.

Only five PDF documents were provided (no source code). Every row therefore cites one or more
documents with a verbatim quote. This script locates the PDF page of every quote in the
pdftotext export and FAILS if any quote is not found, so every page reference is mechanically
checked. Outputs: evidence-ledger.csv and ../08-evidence-ledger.md (table body).

Grades (user's scheme, applied honestly to documentation-only evidence):
  IMPLEMENTED / PARTIALLY IMPLEMENTED: cannot be used. They require reading source code, which was not provided.
  DOCUMENTED ONLY  - described in a supplied document; not verified in code by me.
  PLANNED          - explicitly future work / recommendation in a document.
  NOT FOUND        - not used (requires a codebase search I cannot perform).
  UNKNOWN          - documents conflict, or no document establishes it.
The column doc_label records the document's OWN confidence label (e.g. CONFIRMED/VERIFIED from source),
so a reader can see how strongly the source document asserts it.
Run: python3 -I build_ledger.py
"""
import csv, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
TXT = os.path.join(os.path.dirname(HERE), 'uploads-text')
DOCS = {
    'HB': ('Elevate_Deep_Reverse_Engineering_Handbook', 'Deep Reverse-Engineering Handbook (Python AI service, 21 Oct 2026)'),
    'BR': ('elevate_beginner_technical_review', 'Beginner Technical Review (Python AI service, commit 864b477, 23 Oct 2026)'),
    'TS': ('Elevate_transformation_strategy', 'Transformation Strategy (Python AI service + research, 23 Oct 2026)'),
    'BE': ('ELEVATE_BACKEND_TECHNICAL_DOCUMENTATION', 'Elevate 2.0 API Technical Documentation (ASP.NET Core, 30 Oct 2026)'),
    'FE': ('ELEVATE_FRONTEND_TECHNICAL_DOCUMENTATION', 'Elevate 2.0 Frontend Technical Documentation (React, 30 Oct 2026)'),
}
DO, PL, UNK = 'DOCUMENTED ONLY', 'PLANNED', 'UNKNOWN'

def norm(s):
    s = unicodedata.normalize('NFKC', s).replace('’', "'").replace('—', '-').replace('–', '-').replace('−', '-')
    return re.sub(r'\s+', ' ', s).strip().lower()

PAGES = {k: [norm(p) for p in open(os.path.join(TXT, v[0] + '.txt'), encoding='utf-8', errors='replace').read().split('\f')] for k, v in DOCS.items()}

# id, area, finding, grade, doc_label, [(doc, quote), ...], notes
R = [
# ---------------- Source inventory / system shape
('P3-001', 'Inventory', 'Three separate Elevate codebases are described: a Python "Elevate AI Service", an ASP.NET Core 8 "Elevate 2.0 API", and a React/TypeScript "Elevate 2.0" frontend. None of their source code was supplied.', DO, 'doc-stated scope',
 [('HB', 'paie-kensium_elevate-ai-service'), ('BE', 'ASP.NET Core 8.0 Web API / PostgreSQL'), ('FE', 'React 18.3.1 + TypeScript 5.5 + Vite 5.4')], 'Inventory of /root/.claude/uploads: five PDFs only, no archive or code files.'),
('P3-002', 'Inventory', 'The frontend document names its source tree kensium-solutions-kensium_elevate-2.0-225096fcc9b3; the beginner review names the AI-service baseline commit 864b477.', DO, 'doc-stated scope',
 [('FE', 'kensium-solutions-kensium_elevate-2.0-225096fcc9b3'), ('BR', 'master @ 864b477')], 'Identifiers usable to request the exact source snapshots.'),
# ---------------- Architecture
('P3-010', 'Architecture', 'The AI service is a FastAPI + Celery backend that captures Teams and external meetings, generates LLM insights, and syncs Jira/JSM and Tempo.', DO, 'CONFIRMED (HB) / VERIFIED stack (TS)',
 [('HB', 'is a FastAPI + Celery backend service that:'), ('TS', 'Elevate AI is a FastAPI + Celery backend')], ''),
('P3-011', 'Architecture', 'The AI service is layered: routes -> handlers -> repositories/services; Celery tasks are thin wrappers over worker/utils.', DO, 'CONFIRMED (HB)',
 [('HB', 'The application follows a strict layered architecture')], ''),
('P3-012', 'Architecture', 'Router/endpoint count conflicts across documents: 26 routers (handbook), 64 endpoints across 25 routers (beginner review); the strategy says it verified 26.', UNK, 'conflict',
 [('HB', '26 routers under /api/v1'), ('BR', '64 endpoints'), ('TS', 'handbook says 26')], 'Exact count cannot be settled without the code.'),
('P3-013', 'Architecture', 'Runtime: Docker Compose with app, celery-worker, celery-beat, redis and otel-agent; PostgreSQL is external (commented out of compose).', DO, 'CONFIRMED (HB)',
 [('HB', 'is expected to be an external managed database'), ('BR', 'PostgreSQL is not in docker-compose')], ''),
('P3-014', 'Background jobs', 'Celery uses Redis as broker, PostgreSQL as result backend, late acks, prefetch 1, soft 300 s / hard 360 s limits.', DO, 'CONFIRMED (HB) / VERIFIED (TS)',
 [('HB', 'Ack: Late (task_acks_late=True)'), ('TS', 'acks_late=True')], ''),
('P3-015', 'Background jobs', 'Queue count conflicts: ~80 (handbook) vs 74 Queue definitions (strategy, beginner review).', UNK, 'conflict',
 [('HB', '~80 dedicated queues'), ('TS', '74 Queue(...) definitions'), ('BR', '74 queues, lines 4-79')], 'Two later documents agree on 74.'),
('P3-016', 'Background jobs', 'Celery Beat runs 14 periodic jobs, from 2-minute (AI insight scheduler) to daily syncs.', DO, 'CONFIRMED (HB)',
 [('HB', '14 periodic jobs')], ''),
('P3-017', 'Background jobs', 'A routing-key mismatch means 14 short-named tasks fall through to the default queue when dispatched ad hoc.', DO, 'CONFIRMED (BR)',
 [('BR', 'Celery routing-key mismatch for 14 short-named tasks')], 'Impact depends on whether the default queue is consumed in production (UNKNOWN).'),
('P3-018', 'Background jobs', 'Celery chord callbacks may not fire if a header task fails.', DO, 'INFERRED (HB)',
 [('HB', 'if a header task in a chord fails')], ''),
('P3-019', 'Architecture', 'The .NET Elevate 2.0 API has no service or repository layer; controllers access DbContext directly; it runs no background jobs.', DO, 'doc static analysis',
 [('BE', 'There is no service/repository layer'), ('BE', 'There are no background jobs, message queues')], ''),
('P3-020', 'Architecture', 'The .NET API does not call external services; it reads data that other pipelines write.', DO, 'doc static analysis',
 [('BE', 'This API does not call external services directly')], 'Consistent with the AI service being the writer, but the shared-database link is not documented (see P3-041).'),
# ---------------- Security / auth
('P3-030', 'Security', 'The AI service has no API authentication or authorization dependency on any route.', DO, 'CONFIRMED (HB, BR) / VERIFIED (TS)',
 [('HB', 'No API authentication middleware identified'), ('BR', 'None of the 64 FastAPI routes check who is calling'), ('TS', 'Zero auth dependencies exist on any of')], 'Whether an upstream proxy enforces auth is UNKNOWN in all documents.'),
('P3-031', 'Security', 'The .NET API enforces no authentication; zero endpoints require it.', DO, 'doc static analysis',
 [('BE', 'Zero endpoints require authentication.'), ('BE', 'No Implemented Authentication')], ''),
('P3-032', 'Security', 'The .NET login compares the submitted "PasswordHash" to the stored value by plain string equality and returns the full user entity.', DO, 'doc static analysis',
 [('BE', 'compares PasswordHash as plain string match (no hashing)'), ('BE', 'Login returns full entity including')], ''),
('P3-033', 'Security', 'The frontend sends no Authorization header and treats a localStorage-persisted isAuthenticated flag as its only session authority.', DO, 'doc static analysis',
 [('FE', 'Does not attach any Authorization header'), ('FE', 'the frontend treats isAuthenticated in Zustand as the sole authority')], ''),
('P3-034', 'Security', 'Microsoft 365 (MSAL) sign-in is coded in the frontend but disabled.', DO, 'doc static analysis',
 [('FE', 'single sign-on is implemented in the codebase but is currently disabled')], ''),
('P3-035', 'Security', 'RBAC data (roles, modules, permissions, assignments matched by department + job title) is stored but not enforced server-side.', DO, 'doc static analysis',
 [('BE', 'RBAC enforcement Data-only'), ('BE', 'RoleAssignment does not directly reference a User ID')], ''),
('P3-036', 'Security', 'Recall AI webhook signature verification exists only as commented-out code (TODO).', DO, 'CONFIRMED (HB, BR) / VERIFIED (TS)',
 [('HB', 'Webhook signature verification is coded as a TODO comment'), ('BR', 'Recall AI webhook signature verification is commented out')], ''),
('P3-037', 'Security', 'Jira webhooks have no signature check; MS Graph clientState is not validated.', DO, 'CONFIRMED (BR)',
 [('BR', 'Jira webhook has no signature check'), ('BR', 'MS Graph `clientState` is not validated')], ''),
('P3-038', 'Security', 'Transcript text is injected verbatim into prompts (autoescape off), a prompt-injection surface.', DO, 'CONFIRMED (BR)',
 [('BR', 'Prompt injection surface')], ''),
('P3-039', 'Security', 'Configuration hygiene issues: hardcoded CORS origins incl. an internal IP (AI service); AllowAll CORS, Swagger in production and hardcoded fallback DB credentials (.NET API).', DO, 'CONFIRMED (HB) / doc static analysis (BE)',
 [('HB', 'CORS allows internal IP'), ('BE', 'AllowAll'), ('BE', 'Swagger UI enabled in all environments'), ('BE', 'Hardcoded fallback credentials')], ''),
# ---------------- Database
('P3-040', 'Database', 'AI service: PostgreSQL via SQLModel/SQLAlchemy with Alembic (~70 migrations).', DO, 'CONFIRMED (HB)',
 [('HB', 'Alembic with ~70 version files')], ''),
('P3-041', 'Database', 'Two different meeting schemas are described: the AI service writes meetings/transcripts/meeting_insights; the .NET API reads ai_pm_ms_meeting and ai_pm_llm_meeting_insights in a separate "Meetings" database. No document links them.', UNK, 'conflict',
 [('HB', 'meeting_insights (summary, minutes, key_notes)'), ('BE', 'Table: ai_pm_ms_meeting'), ('BE', 'ai_pm_llm_meeting_insights')], 'Searched all three AI-service documents for "ai_pm": no hits. Could be legacy vs current, views, or separate pipelines.'),
('P3-042', 'Database', 'AI-service hierarchy: projects -> meetings (meetings.parent_id, SET NULL) -> transcripts (CASCADE) -> seven insight/child tables (CASCADE).', DO, 'CONFIRMED from model FKs (HB)',
 [('HB', 'meetings.parent_id'), ('HB', 'transcripts.parent_id'), ('HB', 'CASCADE deletes 7 child tables')], 'Meetings attach to a project, not directly to a customer.'),
('P3-043', 'Database', 'Customer -> JSM ticket -> comments/sentiments relationships are only inferred in the handbook.', DO, 'INFERRED (HB)',
 [('HB', 'jsm_tickets.customer_id')], ''),
('P3-044', 'Database', 'The AI-service model count conflicts: 38+ (handbook), 45 (beginner review), 44 import lines (strategy).', UNK, 'conflict',
 [('HB', '38+ ORM'), ('BR', 'All 45 models use SQLModel'), ('TS', '44 import lines')], ''),
('P3-045', 'Database', 'No ORM Relationship() declarations and no onupdate on updated_at columns in the AI service.', DO, 'CONFIRMED (BR)',
 [('BR', 'No ORM `Relationship()` declarations'), ('BR', 'No `onupdate=` on any `updated_at` column')], ''),
('P3-046', 'Database', 'ai_insights uses a polymorphic reference_id with no foreign key; meeting_insights upserts on a composite unique key (parent_id, insight_type).', DO, 'CONFIRMED (BR)',
 [('BR', 'note the polymorphic `reference_id` with'), ('BR', 'composite unique constraint')], 'Summary/minutes/key notes are overwritten on regeneration: no version history documented.'),
('P3-047', 'Database', '.NET API: customers and projects come from Jira issues; Project.parent_id logically links to a Customer with no FK; no migrations folder.', DO, 'doc static analysis',
 [('BE', 'Logically links to'), ('BE', 'No migrations found'), ('BE', 'Missing FK annotations')], ''),
('P3-048', 'Database', 'Project team roles (project manager, lead, architect, tech lead, QA) are stored as name/email strings on the project; no project-membership table is documented in any document.', DO, 'doc static analysis',
 [('BE', 'project_manager, project_lead,')], 'Python model list mentions UserHierarchy but no project-membership entity.'),
('P3-049', 'Database', 'The data model is single-tenant-shaped; billing_* and sensitive_fields tables exist with unknown producers.', DO, 'INFERRED (TS)',
 [('TS', 'The data model is single-tenant-shaped'), ('TS', 'billing_* and sensitive_fields tables exist')], ''),
# ---------------- Integrations
('P3-050', 'Integrations: Microsoft', 'Microsoft Graph: app-only and delegated OAuth tokens; per-user transcript and calendar subscriptions plus a tenant-wide Meet Now subscription; renewal every 6 hours.', DO, 'CONFIRMED (HB)',
 [('HB', 'Application (client credentials):'), ('HB', 'Per-user transcript subscription:'), ('HB', 'Every 6 hours')], ''),
('P3-051', 'Integrations: Microsoft', 'Transcript webhooks are de-duplicated in Redis (SET NX, 5-minute TTL) and processed asynchronously; validationToken handshake only.', DO, 'CONFIRMED (HB, BR)',
 [('HB', 'Redis SET NX with 5-min TTL for dedup key'), ('HB', 'Validated via `validationToken` handshake')], 'Dedup fails open on Redis loss (HB 14.4).'),
('P3-052', 'Integrations: Recall AI', 'External (non-tenant) meetings are captured by Recall AI bots; webhooks are de-duplicated by webhook-id.', DO, 'CONFIRMED (HB)',
 [('HB', 'deploys Recall AI recording bots'), ('HB', 'Deduplication via')], ''),
('P3-053', 'Integrations: Jira/JSM', 'Jira/JSM: Basic auth; daily syncs of accounts, customers, projects, licenses; JSM tickets via webhook with a 10-second debounce plus incremental sync.', DO, 'CONFIRMED (HB)',
 [('HB', 'Basic auth (username + password from config)'), ('HB', 'debounced sync (10s')], 'Write-back to Jira is not documented anywhere.'),
('P3-054', 'Integrations: Tempo', 'Tempo worklogs: incremental sync every 15 minutes and deletion reconciliation every 20 minutes.', DO, 'CONFIRMED (HB)',
 [('HB', 'Incremental worklog sync (every 15 min)')], ''),
('P3-055', 'Integrations: AWS', 'Recordings go to S3 (multipart upload, presigned playback URLs), with a SharePoint-to-S3 migration path.', DO, 'CONFIRMED (HB)',
 [('HB', 'Multipart upload of meeting recordings')], ''),
# ---------------- AI pipeline
('P3-060', 'AI', 'LLM calls go through LiteLLM; the provider is set at runtime by an environment variable and is unknown.', DO, 'CONFIRMED (HB)',
 [('HB', 'determined at runtime by the model')], 'Production LLM_MODEL is UNKNOWN in all documents.'),
('P3-061', 'AI', 'Each transcript runs through seven insight tasks: summary, minutes, key notes, action items, commitments, sentiment, upsell opportunities; each uses a Jinja2 system+user prompt.', DO, 'CONFIRMED (HB, BR)',
 [('HB', 'Dispatches all 7 tasks'), ('HB', 'System role prompt')], ''),
('P3-062', 'AI', 'Sync vs async LLM call conflicts: handbook says acompletion(); two later documents say synchronous completion() and call the handbook wrong.', DO, 'CONFIRMED (BR) / VERIFIED (TS)',
 [('HB', 'uses `await litellm.acompletion()`'), ('BR', 'is synchronous inside an `async def`'), ('TS', 'correction to the handbook')], 'Majority of documents: synchronous.'),
('P3-063', 'AI', 'LLM run tracking conflicts: handbook and strategy say every call records an llm_runs row with tokens; the beginner review says the seven insight workers create no llm_runs row and tokens are only logged.', UNK, 'conflict',
 [('HB', 'tokens_used, model'), ('TS', 'creates an llm_runs row (status pending)'), ('BR', 'Token usage is logged but never stored in the database')], 'The beginner review cites specific line numbers; cost attribution per meeting is at best unverified.'),
('P3-064', 'AI', 'The seven insight tasks have no Celery retry; a transient LLM error loses that insight until the daily coverage sweep.', DO, 'CONFIRMED (BR)',
 [('BR', 'have no Celery retry')], ''),
('P3-065', 'AI', 'No structured-output schema enforcement, no evaluation suite, no RAG/embeddings, no tool-calling or agents: direct completion calls only.', DO, 'NOT FOUND (HB) / VERIFIED (TS)',
 [('TS', 'No structured-output schema enforcement at the LLM boundary'), ('TS', 'No RAG, no embeddings, no vector search'), ('HB', 'Direct LLM completion calls only.')], ''),
('P3-066', 'AI', 'Cross-entity insights (customer sentiment trend, project alerts) are regenerated by a dirty-flag scheduler every 2 minutes, with a reaper and a daily coverage sweep.', DO, 'CONFIRMED (BR)',
 [('BR', 'claims up to 50 pending jobs with a 180-second debounce')], ''),
('P3-067', 'AI', 'AI outputs are written straight to their tables (upsert or insert); no human review or approval step before persistence is described in any document.', DO, 'CONFIRMED write path (BR)',
 [('BR', 'replace its content')], 'Searched all five documents for approval/review/confirm: none for AI output.'),
('P3-068', 'AI', 'Action items are stored in meeting_action_items "with owners"; no document describes assignment to Elevate users, status, due-date tracking, comments, completion or Jira creation.', UNK, 'gap',
 [('HB', 'Structured action items with')], 'Searched all documents for owner/due/status/complete/lifecycle on action items: none found.'),
('P3-069', 'AI', 'Project alerts are LLM-generated aggregates; no document describes dismissal, resolution or an alert lifecycle.', UNK, 'gap',
 [('HB', 'LLM generates risk alerts')], 'An alerts table exists in the model list; its lifecycle is undocumented.'),
('P3-070', 'AI', 'The −100/+100 sentiment scale appears only in the strategy document, sourced to a user guide that was not supplied.', UNK, 'single secondary source',
 [('TS', 'bounded -100/+100')], ''),
('P3-071', 'AI', 'After insights, an email is sent via MS Graph and transcript sales-stage detection runs.', DO, 'CONFIRMED (HB)',
 [('HB', 'process_meeting_completed_notification')], ''),
# ---------------- Workflows / frontend
('P3-080', 'Workflows', 'Recording control (stop/start per occurrence or series) with Do-Not-Record domain enforcement and on-demand Recall bots.', DO, 'CONFIRMED (HB)',
 [('HB', 'Do Not Record domain enforcement'), ('HB', 'Trigger ad-hoc Recall AI bot for a meeting in')], 'Most-tested feature per HB/BR.'),
('P3-081', 'Workflows', 'Teams capability documented in code is pre-meeting chat notices; an "interactive Teams bot" is asserted only in the strategy document.', UNK, 'single secondary source',
 [('HB', 'Pre-meeting chat notices in Teams'), ('TS', 'interactive Teams bot')], 'No route, task, model or bot-framework dependency for a conversational bot appears in HB/BR.'),
('P3-082', 'Workflows', 'The documented frontend reads only /api/Meeting for meetings; no call to meeting-insight endpoints or the AI service appears in its endpoint inventory.', DO, 'doc static analysis',
 [('FE', 'Reads /api/Meeting')], 'Where users actually view insights is UNKNOWN.'),
('P3-083', 'Workflows', '"Needs Attention" for projects and customers is computed by client-side predicates in the frontend; the AI service separately has NeedsAttention models. Their relationship is undocumented.', UNK, 'conflict/gap',
 [('FE', 'Client-side predicate filter over same /api/Project data'), ('HB', 'NeedsAttentionComment')], ''),
('P3-084', 'Workflows', 'The dashboard is a static placeholder with hard-coded zeros.', DO, 'doc static analysis',
 [('FE', 'static placeholder (hard-coded 0 values)')], 'No management dashboard is implemented in the documented frontend.'),
('P3-085', 'Workflows', 'Frontend/backend contract mismatch: the frontend sends PUT /api/Project/{id} and PUT /api/Customer/{id}; the documented .NET API lists Project and Customer as read-only.', UNK, 'conflict',
 [('FE', 'PUT /api/Project/{id} projectApi.updateProject ProjectEdit'), ('BE', 'Summary: 32 endpoints total')], 'Either the API differs from its documentation or these edit screens fail.'),
# ---------------- Quality
('P3-090', 'Quality', 'Testing: AI service has ~180 unit-test files with all DB calls mocked; the .NET API and the frontend have no tests.', DO, 'CONFIRMED (HB) / doc static analysis',
 [('HB', 'No database fixtures'), ('BE', 'No test project exists in the solution'), ('FE', 'No tests of any kind')], ''),
('P3-091', 'Quality', 'No CI pipeline in the AI-service repository.', DO, 'VERIFIED (TS)',
 [('TS', 'no CI workflow files')], ''),
('P3-092', 'Planned', 'The strategy recommends a "pragmatic evolution": confirm auth, sign webhooks, add CI, structured outputs, evals and RLS. These are recommendations, not committed work.', PL, 'recommendation (TS)',
 [('TS', 'Pragmatic evolution (recommended now)')], ''),
]


def main():
    out, fails = [], []
    for rid, area, finding, grade, label, srcs, notes in R:
        cites = []
        for d, q in srcs:
            pages = [str(i) for i, p in enumerate(PAGES[d], 1) if norm(q) in p]
            if not pages:
                fails.append(f'{rid}: quote not found in {d}: {q!r}')
            cites.append(f'{d} p.{",".join(pages) or "?"} "{q}"')
        out.append([rid, area, finding, grade, label, ' || '.join(cites), notes])
    with open(os.path.join(HERE, 'evidence-ledger.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['id', 'area', 'finding', 'grade', 'source_document_label', 'citations', 'notes']); w.writerows(out)
    md = ['| ID | Area | Finding | Grade | Document label | Citations (doc, PDF page, quote) | Notes |', '|---|---|---|---|---|---|---|']
    for r in out:
        md.append('| ' + ' | '.join(c.replace('|', '\\|').replace(' \\|\\| ', '<br>') for c in r) + ' |')
    open(os.path.join(HERE, 'ledger-table.md'), 'w').write('\n'.join(md) + '\n')
    counts = {}
    for r in out: counts[r[3]] = counts.get(r[3], 0) + 1
    print(len(out), 'rows', counts)
    for f in fails: print('FAIL', f)
    sys.exit(1 if fails else 0)

main()
