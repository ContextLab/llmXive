# Implementation Plan: llmXive website — UI bug-fixes and polish (#115)

**Branch**: `008-website-ui-fixes` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)
**Input**: [specs/007-website-ui-fixes/spec.md](./spec.md) · **Tracking issue**: #115

## Summary

Fix the batch of UI bugs + missing affordances tracked in #115, across the existing static GitHub Pages site (`web/` → synced to `docs/`; markup `web/index.html`, vanilla JS `web/js/*.js`, styles `web/css/*.css`, data `web/data/projects.json` built by `src/llmxive/web_data.py`) plus a small Python/CLI + GitHub-Actions addition for the new human-submission intake path.

Approach, by area:
- **Static-site fixes** (FR-001..006, FR-009b, FR-017): edit `web/index.html` + `web/css/*` + `web/js/app.js`; add one small vendored Markdown→HTML lib under `web/js/vendor/`. The wordmark is a CSS `white-space: nowrap` / box fix; the tab indicator is a JS geometry fix in `app.js` (recompute from `getBoundingClientRect()` of the active tab relative to its container on click + `resize` + `orientationchange` + `document.fonts.ready`); the pipeline-diagram circles get `data-step="…"` + a click handler opening a modal whose content is built from a new `pipeline_steps` block in `web/data/projects.json` (emitted by `web_data.py` from the pipeline-stage definitions + `agents/registry.yaml` + recent artifacts); the agent-registry modal is built from an `agents` block in `web/data/projects.json` (emitted by `web_data.py` from `agents/registry.yaml`); the "How to contribute" section is static markup in `index.html`.
- **Data-correctness fixes** (FR-007, FR-008): in `src/llmxive/web_data.py` — `_agent_contributors` / the run-log walk already key by `_normalize_model_name(model_name)`, so investigate whether the live bug is (a) a code path still emitting `agent_name`, (b) double-counting, or (c) just stale `web/data/projects.json`; fix the builder + regenerate. The site JS reads the corrected data; the only JS change is dropping any fallback that would display a prompt name (`app.js` currently has a `/qwen|gemma|claude|…/i` regex test on `item.submitter` — make the "model vs prompt" classification authoritative from the data, not regex-guessed).
- **Project-modal artifact rendering** (FR-009): in `app.js`, change the modal-open path from "always embed `<project>.pdf`" to "resolve the artifact: published PDF → embed it; else fetch + render the current-stage artifact (Markdown via the vendored renderer; LaTeX/JSON/YAML as formatted source); else show a placeholder + metadata + view-on-GitHub link". The "current-stage artifact path" per project comes from `web/data/projects.json` (extend the per-project entry in `web_data.py` with `current_artifact: {type, repo_path}` if not already present).
- **Auth fix** (FR-010, FR-011): in `web/js/auth.js` — `signOut()` also removes `KEY_STATE` from `sessionStorage` and (FR-011) calls a new `POST <PROXY>/revoke` endpoint with the token so the Cloudflare Worker revokes the app's GitHub OAuth authorization grant (the Worker holds the client secret; it calls `DELETE /applications/{client_id}/grant`). If the Worker can't add that endpoint, the fallback is `startLogin()` forcing GitHub's account-chooser (route through `https://github.com/logout?return_to=…/login/oauth/authorize?...` or add `prompt=login`-equivalent). The local-state clear happens first, unconditionally; a failed revoke logs a non-blocking warning. The Cloudflare-Worker change (the `/revoke` route) is a small adjunct documented in `contracts/oauth-proxy.md`.
- **Human-submission intake** (FR-012..015): in `web/js/auth.js` — add `submitFeedback({target, stage, content})` and `submitPaper({url|pdfFile})` (mirroring the existing `submitIdea` / `submitReview`), each creating a GitHub issue labelled `human-submission` + a sub-type label, via `ghFetch("/repos/.../issues", …)`; for a PDF, upload it as an issue attachment isn't supported by the REST API, so stage it: commit the PDF to a `submissions/inbox/<timestamp>.pdf` path via the Contents API and reference it in the issue body (the maintenance agent moves it to its canonical home). In `web/js/app.js` / `web/js/dialog.js` — add the "submit feedback" control to every artifact modal and a "submit a paper" entry point; on success show the FR-013b message (issue link + "processed within the next hour").
- **Maintenance agent + intake cron** (FR-020, FR-021): a new agent `submission_intake` in `agents/registry.yaml` + prompt `agents/prompts/submission_intake.md`; a new module (e.g. `src/llmxive/agents/submission_intake.py`) with the agent class + a `process_submission_issue(issue)` entry point that uses the backend router for LLM triage and the GitHub API to comment/close + the file moves; a new CLI subcommand or a small runner invoked by a new GitHub Action workflow `.github/workflows/submission-intake.yml` (hourly `schedule:`) that lists open `human-submission` issues and processes each, idempotent + per-submission-failure-tolerant.
- **Docs** (FR-016): rewrite the repo-root `README.md` to match the current system (the two Spec-Kit pipelines, the agent registry incl. the new agent, the public site, the spec-driven workflow). Also re-sync `web/` → `docs/` is handled automatically by the existing `Deploy Pages` workflow on push to `main` (FR-018) — no manual step, but verify it runs green.

## Technical Context

**Language/Version**: JavaScript (browser, vanilla ES2020, no build step) for the site; Python 3.11 for `web_data.py` + the new `submission_intake` agent + CLI; YAML for `agents/registry.yaml`; GitHub Actions workflow YAML.
**Primary Dependencies**: existing — Font Awesome (CDN, already used), the GitHub REST API (via `ghFetch`), the Cloudflare-Worker OAuth proxy; new — one small vendored Markdown→HTML library (~10 KB, MIT/ISC-licensed, e.g. `snarkdown` or `marked`-min) committed under `web/js/vendor/`; the existing `llmxive.backends.router` for the maintenance agent's LLM calls.
**Storage**: the repo itself (GitHub) — issues for submissions, files committed via the Contents API; `web/data/projects.json` (built artifact); no database.
**Testing**: `pytest tests/phase2/` for `web_data.py` changes + the `submission_intake` agent (real GitHub-API + real-LLM tests gated on creds, mocks as secondary per Constitution III); for the site JS, visual verification via screenshots at desktop + mobile widths + manual click-through of each modal (Constitution III: "UI / web interface behavior MUST be visually verified").
**Target Platform**: GitHub Pages (static site) + GitHub Actions runners (Python + the new hourly cron) + a Cloudflare Worker (the OAuth proxy).
**Project Type**: web app (static front-end) + a small Python/CLI + Actions backend addition.
**Performance Goals**: site stays a no-build static client; the Markdown renderer adds < ~15 KB to page weight; the intake cron processes a typical hour's submissions (expected: 0–handful) well within an Action's time budget.
**Constraints**: free-first (Constitution IV) — GitHub Pages + GitHub Actions free minutes + the existing free Cloudflare Worker; no paid services. No build pipeline for the site (it must remain directly deployable). Don't regress when the pipeline crons regenerate `web/data/projects.json` (FR-019).
**Scale/Scope**: ~6.7k lines of existing `web/` code touched in a handful of files; one new ~10 KB vendored JS file; one new ~150–250-line Python agent module + a ~30-line registry entry + a ~50-line prompt + a ~40-line workflow; a `web_data.py` extension (a couple of new emitted blocks + the contributor fix); a README rewrite.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Single Source of Truth** — PASS. The site is a *view* over canonical state: the pipeline-step modal content, the agent-registry modal content, and the contributor list are all *derived* (in `web_data.py`) from `agents/registry.yaml` / the pipeline-stage definitions / run-logs — no hand-maintained duplicates in the site (FR-006). The Markdown renderer is one vendored copy used everywhere Markdown is shown (FR-009b). The new submission helpers reuse the existing `ghFetch` plumbing in `auth.js` (no parallel HTTP layer); the new `submission_intake` agent uses the existing `agents/registry.yaml` + `agents/prompts/` + backend-router patterns. The README is the one canonical project doc.
- **II. Verified Accuracy** — PASS. The README rewrite (FR-016) must verify every claim against the current repo (Constitution II is exactly this). The pipeline-step / agent-registry modal content links to the actual GitHub sources so a reader can verify. No new external-fact claims are introduced beyond what's already in the repo.
- **III. Robustness & Reliability (Real-World Testing)** — PASS. `web_data.py` changes get real-fixture tests in `tests/phase2/`; the `submission_intake` agent gets a real-GitHub-API test (create a test issue, run the agent, assert it commented/closed/filed) + a real-LLM triage smoke (gated on `DARTMOUTH_CHAT_API_KEY` + `LLMXIVE_REAL_TESTS=1`), with mocks only as a secondary fast layer. The site JS fixes are *visually* verified (screenshots at desktop + mobile, click-through of every new/modified modal, sign-out→re-sign-in-as-different-user) — the constitution's UI clause. The hourly workflow is exercised once manually (`workflow_dispatch`) before relying on the schedule.
- **IV. Cost Effectiveness (Free-First)** — PASS. Everything stays on GitHub Pages + GitHub Actions free minutes + the existing free Cloudflare Worker. The Markdown renderer is open-source and vendored (no CDN dependency / paid service). The maintenance agent's LLM calls use the existing free Dartmouth/HF backends via the router. No paid service introduced.
- **V. Fail Fast** — PASS. The intake workflow validates its preconditions (GitHub token present, the `human-submission` label exists, the agent module imports) before processing; a per-submission failure is isolated (the issue stays open with an explanatory comment) and doesn't fail the run; the agent fails fast on a malformed issue body. The site's submission helpers validate input (non-empty content, a valid URL or a PDF under a sane size) before the GitHub call, and surface a clear error on failure (preserving the user's input).
- **Additional constraints** — repo-cleanliness: no transient artifacts left in the repo root; the vendored Markdown lib goes under `web/js/vendor/` (a deliberate, documented location), not loose; `package.json` isn't used by the static site, so no manifest update for the vendored JS, but the lib's license is recorded in a `web/js/vendor/README.md`. Documentation parity: the README rewrite + the `agents/registry.yaml` entry land in the same PR as the agent.

**Result: PASS — no violations; no Complexity-Tracking entries needed.**

## Project Structure

### Documentation (this feature)

```text
specs/007-website-ui-fixes/
├── spec.md              # (done)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── projects-json-delta.md       # new blocks in web/data/projects.json (pipeline_steps, agents, per-project current_artifact) + the contributor fix
│   ├── auth-js-delta.md             # web/js/auth.js: signOut() changes + submitFeedback/submitPaper
│   ├── oauth-proxy.md               # the Cloudflare Worker's new /revoke route (FR-011) + the fallback
│   ├── submission-intake-agent.md   # agents/registry.yaml entry + agents/prompts/submission_intake.md + the agent module's contract
│   ├── submission-intake-workflow.md# .github/workflows/submission-intake.yml (hourly cron)
│   └── site-ui-fixes.md             # the per-FR behavior contracts for the static-site fixes (wordmark, tab indicator, modals, how-to-contribute) + the visual-verification checklist
├── checklists/
│   └── requirements.md  # (done)
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source code (repository root)

```text
web/
├── index.html                       # MODIFIED — wordmark box markup; data-step on pipeline circles; agent-registry entry point; "How to contribute" section; feedback/paper-submission controls; (re-synced to docs/ by the Deploy Pages workflow)
├── css/
│   ├── site.css                     # MODIFIED — .tab-underline geometry-driven; wordmark white-space
│   ├── components.css / layout.css  # MODIFIED — new modal styles (pipeline-step, agent-registry, submit-feedback, submit-paper) at desktop + mobile
│   └── (others unchanged)
├── js/
│   ├── app.js                       # MODIFIED — tab-indicator recompute on click/resize/orientation/font-load; pipeline-step modal; agent-registry modal; project-modal artifact resolution; "How to contribute" wiring; submit-feedback/paper UI + the FR-013b confirmation message
│   ├── auth.js                      # MODIFIED — signOut() also clears sessionStorage state + calls PROXY /revoke; new submitFeedback/submitPaper; (fallback) startLogin forces account-chooser
│   ├── dialog.js                    # MODIFIED — feedback/paper submission dialogs
│   ├── data.js                      # MODIFIED (maybe) — surface the new projects.json blocks (pipeline_steps, agents, per-project current_artifact)
│   └── vendor/
│       ├── markdown.min.js          # NEW — vendored small Markdown→HTML lib (MIT/ISC)
│       └── README.md                # NEW — name, version, license, source URL of the vendored lib
└── data/projects.json               # REGENERATED by web_data.py (with the new blocks + the contributor fix)

src/llmxive/
├── web_data.py                      # MODIFIED — emit `pipeline_steps`, `agents`; per-project `current_artifact`; fix contributor model-vs-prompt + counts (FR-007, FR-008)
└── agents/
    └── submission_intake.py         # NEW — the maintenance agent (class + process_submission_issue(...))

agents/
├── registry.yaml                    # MODIFIED — new `submission_intake` agent entry
└── prompts/
    └── submission_intake.md         # NEW — the triage prompt

.github/workflows/
└── submission-intake.yml            # NEW — hourly cron; lists open `human-submission` issues; invokes submission_intake on each

tests/phase2/
├── test_web_data_contributors.py    # NEW/EXTENDED — model-not-prompt attribution + correct counts (FR-007, FR-008) against real fixtures
├── test_web_data_blocks.py          # NEW — the new projects.json blocks are well-formed + derived from registry/stages (FR-006)
└── test_submission_intake.py        # NEW — real-GitHub-API issue→triage→comment/close/file + real-LLM triage smoke (gated); parser/edge-case tests

README.md                            # MODIFIED — rewritten to match the current system (FR-016)

# (Cloudflare Worker — the simple-oauth-proxy — gets a new /revoke route; that repo/Worker is external; the change is documented in contracts/oauth-proxy.md and applied there.)
```

**Structure Decision**: this is a web-app feature with a small Python/CLI + GitHub-Actions backend addition; it follows the repo's existing layout (the static site under `web/`, Python under `src/llmxive/`, agents under `agents/`, workflows under `.github/workflows/`, tests under `tests/phase2/`). No new top-level structure. The one external touch is the Cloudflare-Worker OAuth proxy's new `/revoke` route — out of this repo's tree but in scope, documented in `contracts/oauth-proxy.md`.

## Complexity Tracking

*No Constitution violations — section intentionally empty.*
