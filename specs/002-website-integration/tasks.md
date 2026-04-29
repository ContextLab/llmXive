# Tasks: Website Integration with Agentic Pipeline

**Feature**: 002-website-integration
**Spec**: spec.md  •  **Plan**: plan.md

## Phase A — Static-site shell + accurate data (US1+US5+US6)

- [ ] T001 Add `web_data.py` with pure functions to project + run-log + reviews + citations → JSON dict in src/llmxive/web_data.py
- [ ] T002 [P] Expand `status_reporter` agent to write the new schema in src/llmxive/agents/status_reporter.py
- [ ] T003 [P] Port styles from web/notes/design/styles.css to web/css/site.css (verbatim)
- [ ] T004 [P] Port app.js skeleton from web/notes/design/app.js to web/js/app.js (will be rewired in T008)
- [ ] T005 Create web/js/data.js (fetch projects.json, expose model)
- [ ] T006 Rewrite web/index.html (port design + expand to FR-005 tab set, add login button, OAuth meta tag, embed pdf modal)
- [ ] T007 Rewrite web/about.html (preserve data-threshold spans, narrate 34-stage pipeline, two review gates, Spec-Kit-per-project)
- [ ] T008 Wire web/js/app.js to real data: tab counts, kanban columns, hero stats, fallback empty state
- [ ] T009 [P] Run status_reporter once to bootstrap web/data/projects.json with the existing in-repo project state
- [ ] T010 Test: tests/integration/test_web_data_aggregates.py
- [ ] T011 Test: tests/integration/test_web_about_pipeline_narrative.py (verifies new pipeline stages mentioned, no "Five-stage pipeline" stale phrase)

## Phase B — Artifact-log dialog (US2)

- [ ] T020 Add `artifact_links` + `citation_summary` + `last_run_log` blocks to status_reporter output (plumbing)
- [ ] T021 Create web/js/dialog.js (renders the modal + artifact list + embedded PDF)
- [ ] T022 Wire card-click → open dialog (papers, in-progress, paper pipeline)
- [ ] T023 Add Esc-to-close + click-backdrop-to-close + focus-trap
- [ ] T024 [P] Test: tests/integration/test_web_data_artifact_links.py
- [ ] T025 PDF render fallback: if embed fails, show "Download PDF" button

## Phase C — Local credentials (US4)

- [ ] T030 Create src/llmxive/credentials.py (load/save/clear/mask + 0600 enforcement)
- [ ] T031 Wire src/llmxive/preflight.py to use credentials.load_dartmouth_key()
- [ ] T032 Add `python -m llmxive auth {set|show|rotate|clear}` subcommand in src/llmxive/cli.py
- [ ] T033 Test: tests/integration/test_credentials_store.py (env precedence, prompt fallback, perm check)

## Phase D — GitHub OAuth + Submit/Review (US3)

- [ ] T040 Create infra/oauth-proxy/wrangler.toml + src/index.ts + README
- [ ] T041 Document deploy: `wrangler secret put CLIENT_SECRET; wrangler deploy`
- [ ] T042 Create web/js/auth.js (login + token store + sign-out)
- [ ] T043 Add Sign-in button + avatar slot to web/index.html
- [ ] T044 Wire Submit-Idea modal: needs auth, collects {title, description, field, keywords}, POSTs to GitHub Issues API with labels [idea, brainstormed]
- [ ] T045 Wire Review modal: needs auth, collects {target_artifact, verdict, score, body}, PUTs file under projects/<PROJ-ID>/reviews/research/ via Contents API
- [ ] T046 [P] Test (Playwright): tests/e2e/test_site_auth.py (mocks Worker boundary)

## Phase E — End-to-end + Playwright (US7)

- [ ] T050 Add `python -m llmxive brainstorm <N>` subcommand
- [ ] T051 Add `python -m llmxive run --advance --max-cycles K` driver loop
- [ ] T052 Run brainstorm 5; commit the resulting state
- [ ] T053 Run advance until ≥2 projects reach POSTED
- [ ] T054 Regenerate web/data/projects.json with the new state
- [ ] T055 [P] Playwright: tests/e2e/test_site.py (tabs, dialog, counters)
- [ ] T056 Visual verification (screenshot) and adjust styles if needed
- [ ] T057 Final commit + push (no PR yet, per user)

## Polish

- [ ] T070 Remove `web/notes/design/` (design integrated)
- [ ] T071 Remove legacy `web/projects.html`, `web/AUTHENTICATION.md`, `web/database/`, `web/notes/`, `web/REPOSITORY_ROLES.md`, `web/COMPREHENSIVE_TEST_REPORT.md`, `web/server.log` if no longer relevant
- [ ] T072 Update README.md website-section pointers
- [ ] T073 Add a docs note about rotating the leaked Dartmouth key
