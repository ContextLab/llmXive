---
description: "Task list for spec 007 — llmXive website UI bug-fixes + polish (#115)"
---

# Tasks: llmXive website — UI bug-fixes and polish (#115)

**Input**: design docs in `/specs/007-website-ui-fixes/` — [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)
**Branch**: `008-website-ui-fixes` · **Tracking issue**: #115

**Tests**: included where the constitution mandates them — real-call tests for `web_data.py` changes + the `submission_intake` agent (Constitution III), and a visual-verification checklist for the static-site fixes (Constitution III's UI clause). The site JS itself isn't unit-tested (vanilla, no harness) — it's verified visually.

**Organization**: by user story (US1–US6 from spec.md), priority order P1 → P2. Each US phase is an independently testable increment.

**Conventions**: `[P]` = parallelizable (different files, no incomplete deps). `[USn]` = which user story (US-phase tasks only; Setup / Foundational / Polish carry no story label).

---

## Phase 1 — Setup

- [ ] T001 Preflight (per quickstart §0): `git switch 008-website-ui-fixes`; confirm `python -c "import llmxive.web_data; print('ok')"`; confirm the site serves locally (`python -m http.server -d web 8000` → open it); confirm a GitHub token is available for the API tests and `DARTMOUTH_CHAT_API_KEY` + `LLMXIVE_REAL_TESTS=1` for the gated LLM tests. Record what's available; nothing blocks if the gated creds are absent (those tests skip).
- [ ] T002 Vendor the Markdown→HTML library: download `snarkdown` (~1 KB, MIT) to `web/js/vendor/markdown.min.js` (fallback: a `marked`-min build if richer features prove needed during US2/US4); create `web/js/vendor/README.md` recording the lib name, version, license, and source URL. (Constitution — repo cleanliness: vendored libs live under `web/js/vendor/`, not loose; license recorded.)
- [ ] T003 Add a tiny sanitizing Markdown wrapper — `web/js/markdown.js` (NEW): `renderMarkdown(rawMd) -> safeHtml` (run `rawMd` through the vendored lib, then strip `<script>` tags, `on*=` attributes, and `javascript:` URLs from the output) and `fetchAndRenderMarkdown(rawUrl) -> Promise<safeHtml>` (fetch the `.md` from a `raw.githubusercontent.com` URL, then `renderMarkdown`). Reference it from `web/index.html`. (Used by US2's project modals and US4's agent-prompt + pipeline-step modals — built once here.)

**Checkpoint**: vendored Markdown lib + wrapper in place; the site still loads.

---

## Phase 2 — Foundational (blocking prerequisites for US1, US2, US4)

These extend the canonical builder so the site has corrected data + the new blocks to render. Per Constitution I the site is a view; these tasks are where the data is made right.

- [ ] T004 `src/llmxive/web_data.py` (MODIFIED) — **root-cause the contributor bug first** (research D5): regenerate `web/data/projects.json` and inspect `contributors[]`; determine which is the live bug — stale JSON / a code path emitting `agent_name` (likely the review-walk) / double-counting; fix the *builder* accordingly: every contributor row's `name` is a normalized model id, a GitHub username, or the literal `"unattributed"` (never a prompt/agent name); every row has an explicit `kind ∈ {"llm","human","unattributed"}`; `contribution_count` == count of distinct artifacts that contributor produced (dedup by `(contributor, artifact_path)`; no phantom entries). Per `contracts/projects-json-delta.md` "Fixed: contributors[]". (FR-007, FR-008; E4.)
- [ ] T005 `src/llmxive/web_data.py` (MODIFIED) — emit a new top-level `agents[]` block (one entry per `agents/registry.yaml` entry): `{name, purpose, prompt_path, prompt_github_url, prompt_raw_url, registry_github_url, tools, default_backend, default_model, inputs, outputs}` (E1). Per `contracts/projects-json-delta.md` `agents[]`.
- [ ] T006 `src/llmxive/web_data.py` (MODIFIED) — emit a new top-level `pipeline_steps[]` block (one entry per pipeline stage, both lanes): `{key, name, lane, order, description, inputs, outputs, agents, example_artifacts:[{project_id,title,github_url}]}` (E2). `description`/`inputs`/`outputs` consolidated from the `Stage` enum + its docstrings + the per-stage blurbs **moved out of `web/index.html`** (so the prose is defined once — Constitution I); `agents` from `STAGE_TO_AGENT` (+ tool-style agents a stage calls, e.g. `librarian`); `example_artifacts` = the most-recent ≈3–5 projects at/past that stage. Per `contracts/projects-json-delta.md` `pipeline_steps[]`.
- [ ] T007 `src/llmxive/web_data.py` (MODIFIED) — add `current_artifact: {type, repo_path, github_url, raw_url}` to each per-project entry (`type ∈ {"pdf","markdown","latex","json","yaml","none"}`; `"pdf"` iff a published PDF exists and then the existing `pdf_url` is used; otherwise the current-stage artifact's path/format; `"none"` ⇒ all three URLs `null`) (E3). Per `contracts/projects-json-delta.md` per-project `current_artifact`.
- [ ] T008 [P] `tests/phase2/test_web_data_contributors.py` (NEW) — real-fixture regression test (Constitution III): build the payload from real project state; assert (i) no `contributors[]` row's `name` is a known prompt/agent name (`brainstorm`, `flesh_out`, `librarian`, `specifier`, `clarifier`, `planner`, `tasker`, `implementer`, `reviewer`, `paper_*`, `figure_generation`, `statistician`, `proofreader`, `latex_*`, `citation_validator`, `submission_intake`, …); (ii) every row has `kind ∈ {"llm","human","unattributed"}`; (iii) for ≥1 contributor, `contribution_count` == an independently-counted artifact total from the fixture. (FR-007, FR-008.)
- [ ] T009 [P] `tests/phase2/test_web_data_blocks.py` (NEW) — real-fixture test: build the payload; assert `agents[]` count == number of `agents/registry.yaml` entries AND every `prompt_path` exists on disk AND `prompt_github_url`/`prompt_raw_url` are correctly-formed; assert every `Stage` appears in `pipeline_steps[]`, every `pipeline_steps[].agents` name ⊆ `agents[].name`, every `example_artifacts` `project_id` ⊆ `projects[].id`; assert every project's `current_artifact` has a valid shape and `type=="pdf"` iff a published PDF is present. (FR-006; E1, E2, E3.)
- [ ] T010 Run `python -m pytest tests/phase2/test_web_data_contributors.py tests/phase2/test_web_data_blocks.py -q` → both pass; then regenerate `web/data/projects.json` (`python -c "from pathlib import Path; from llmxive.web_data import write_payload; write_payload(Path('.'))"`); `ruff check src/llmxive/web_data.py`; `git add` the modified `web_data.py` + the new tests + the regenerated `web/data/projects.json` + the `web/index.html` per-stage-blurb removal; commit (`spec-007: web_data — agents/pipeline_steps blocks + current_artifact + contributor fix (#115)`).

**Checkpoint**: `web/data/projects.json` has the new `agents` + `pipeline_steps` blocks, per-project `current_artifact`, and a corrected `contributors` list; tests green; cron-regeneration is safe (the builder is the source).

---

## Phase 3 — US1: A visitor reads a clean, correctly-rendered dashboard (Priority: P1)

**Goal**: header wordmark one word; tab indicator correct on desktop+mobile incl. resize/rotate; Contributors show models not prompts with correct counts.
**Independent test**: load the site at ~1280px and ~375px → wordmark is one unbroken token; click each tab + resize + rotate → indicator tracks the active tab in every state; open Contributors → every AI row is a model name (or "unattributed"), and ≥1 row's count matches an independent artifact count.

- [ ] T011 [P] [US1] `web/index.html` + `web/css/site.css` (MODIFIED) — the header wordmark: `white-space: nowrap` on the wordmark span and size its box to fit it (no flex/inline-block boundary that lets it wrap). (FR-001; SC-001.)
- [ ] T012 [US1] `web/js/app.js` + `web/css/site.css` (MODIFIED) — replace the `offsetLeft`/`offsetWidth`-based tab-underline positioning with `positionUnderline()` computing `underline.style.left`/`width` from `activeTab.getBoundingClientRect()` minus the tab-row container's `getBoundingClientRect()`; call it on tab click, on `window` `resize` (rAF-debounced), on `orientationchange`, and once `document.fonts.ready` resolves; remove any hard-coded `.tab-underline` left/width in CSS. Per `contracts/site-ui-fixes.md` FR-002 + research D1. (FR-002; SC-002.)
- [ ] T013 [US1] `web/js/data.js` + `web/js/app.js` (MODIFIED) — render the Contributors list from the corrected data: drop the `/qwen|gemma|claude|tinyllama|gpt|mistral|llama/i.test(item.submitter)` regex in `app.js`; use the authoritative `kind` from `contributors[]` (and from per-project `submitter`/`authors` rows where the same model-vs-human distinction is shown); a `"unattributed"` row renders as a labelled bucket. (FR-007 — the site-side half; SC-003, SC-004.)
- [ ] T014 [US1] Visual verification (Constitution III): serve `web/` locally; at ~1280px and ~375px walk the wordmark + tab-indicator + Contributors items of `contracts/site-ui-fixes.md`'s checklist; screenshot each (desktop + mobile); fix anything off (in `web/`, not by hand-editing the data). Commit (`spec-007: US1 — wordmark + tab indicator + model-not-prompt contributors (#115)`).

**Checkpoint**: the dashboard front door is clean and correct — independently shippable.

---

## Phase 4 — US3: GitHub sign-out actually signs the user out (Priority: P1, CRITICAL/SECURITY)

**Goal**: sign-out clears all client auth state (incl. the `sessionStorage` OAuth-state key) and survives reload; after sign-out the OAuth flow re-prompts so a *different* GitHub user can sign in.
**Independent test**: sign in as A → sign out → no `llmxive_gh_token`/`llmxive_gh_user` in `localStorage`, no `llmxive_gh_oauth_state` in `sessionStorage`, UI signed-out; reload → still signed-out; start OAuth → GitHub re-prompts → sign in as B → UI shows B.

> Triaged first among the P1s per #115's CRITICAL/SECURITY flag — but it touches `web/js/auth.js` which US5 also touches, so do US3 then US5 sequentially on `auth.js`.

- [ ] T015 [US3] `web/js/auth.js` (MODIFIED) — `signOut()`: capture the token first, then `localStorage.removeItem(KEY_TOKEN)` + `localStorage.removeItem(KEY_USER)` + `sessionStorage.removeItem(KEY_STATE)` + `renderSlot()` (the unconditional local clear — FR-010); then best-effort `await fetch(PROXY + "/revoke", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({token})})` — on non-2xx → `console.warn(...)` + a small non-blocking notice ("you may need to sign out of github.com to switch accounts"); never throw from `signOut()`. Per `contracts/auth-js-delta.md` `signOut()`. (FR-010, FR-011.)
- [ ] T016 [US3] **Cloudflare Worker** (`simple-oauth-proxy`, external repo) — add the `POST /revoke` route per `contracts/oauth-proxy.md`: receive `{token}` → `DELETE https://api.github.com/applications/{CLIENT_ID}/grant` with `Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)`, `Accept: application/vnd.github+json`, body `{access_token: token}`; treat `204` and `404` as success; same CORS as the existing route (+ an `OPTIONS` preflight handler); deploy. **If the route can't be added to the current Worker setup** → instead take the fallback in `web/js/auth.js` (`startLogin()` navigates to `https://github.com/logout?return_to=<encoded authorize URL>` first, forcing GitHub's account-chooser) — purely client-side, no Worker change. Document which path was taken in the commit message. (FR-011.)
- [ ] T017 [US3] Verify (Constitution III, UI clause): sign in as user A → sign out → inspect browser storage (clean) + UI (signed-out) → reload (still signed-out) → start OAuth → GitHub re-prompts → sign in as user B → UI shows B. Screenshot the re-sign-in-as-different-user. (If the `/revoke` path was taken, also confirm via the Worker logs that the revoke fired; if the fallback, confirm the account-chooser appeared.) Commit (`spec-007: US3 — sign-out clears all state + revokes the OAuth grant [or: forces account-chooser] (#115)`).

**Checkpoint**: the CRITICAL/SECURITY sign-out bug is fixed — independently shippable.

---

## Phase 5 — US2: A visitor inspects a project's actual current artifact (Priority: P1)

**Goal**: project modal shows the PDF if it exists, else the current-stage artifact rendered appropriately (Markdown rendered, LaTeX/JSON/YAML formatted), else a clear placeholder — never a broken/empty embed.
**Independent test**: open a project with a PDF → PDF; one at brainstormed → idea Markdown rendered; an in-progress research project → its current artifact; one with `current_artifact.type=="none"` → placeholder + metadata + GitHub link. No broken embeds anywhere.

> Depends on Phase 2 (T007 — per-project `current_artifact`) and Phase 1 (T002/T003 — the Markdown renderer).

- [ ] T018 [US2] `web/js/app.js` (MODIFIED) — change the project-modal open path from "always `<embed src=…<project>.pdf>`" to resolve `current_artifact` (E3): published PDF (`type=="pdf"` / the existing `pdf_url`) → embed it; `type=="markdown"` → `await fetchAndRenderMarkdown(current_artifact.raw_url)` → inject the sanitized HTML into the artifact pane; `type ∈ {"latex","json","yaml"}` → fetch `raw_url` → show as `<pre>` formatted source + a "view on GitHub" link (`github_url`); `type=="none"` → a placeholder ("No artifact yet — this project is at stage X; the next artifact will appear here") + the project's metadata + a "browse the project on GitHub" link. Never an `<embed>` pointing at a nonexistent PDF. Per `contracts/site-ui-fixes.md` FR-009 + research D9. (FR-009, FR-009b.)
- [ ] T019 [US2] `web/css/components.css` / `web/css/projects.css` (MODIFIED) — styles for the non-PDF artifact panes (the rendered-Markdown body; the `<pre>` source view; the "no artifact yet" placeholder) at desktop + mobile widths. (FR-017.)
- [ ] T020 [US2] Visual verification (Constitution III): serve `web/` locally; open a project with a PDF (PDF shows), one at the brainstormed stage (idea Markdown renders, not raw), an in-progress research project (its current artifact renders), and (if any) one with `type=="none"` (placeholder, no broken embed); at ~375px too; screenshot. Commit (`spec-007: US2 — project modal renders the current-stage artifact, never a broken embed (#115)`).

**Checkpoint**: project modals are useful for projects without a PDF — independently shippable.

---

## Phase 6 — US4: A visitor explores the pipeline and the agent registry in-place (Priority: P2)

**Goal**: clicking a pipeline-diagram circle opens a modal with the step's description/inputs/outputs + example-artifact links + the step's agents (each → its prompt); an "agent registry" entry point opens a modal listing all agents, each clickable to view its prompt + tools.
**Independent test**: on About, click each circle → a modal with description (rendered), inputs, outputs, the agent list (each → a viewable prompt), example-artifact links (or "no examples yet"); click "agent registry" → all agents listed + a GitHub link to the registry; click an agent → its prompt (rendered) + tools + a GitHub source link.

> Depends on Phase 2 (T005/T006 — the `agents` + `pipeline_steps` blocks) and Phase 1 (T002/T003 — the Markdown renderer).

- [ ] T021 [US4] `web/index.html` (MODIFIED) — give each `.stage` circle in `.pipeline.two-lane` a `data-step="<key>"` (the `pipeline_steps[].key`); remove the per-stage `<p>` blurbs from the HTML (the text now comes from the data — done in T006); add an "Agent registry" modal entry point (e.g. make the existing footer "Agent registry" button a modal trigger, `data-open-modal="agents"`, plus an About-page button). (FR-003, FR-004.)
- [ ] T022 [US4] `web/js/app.js` (MODIFIED) — the **pipeline-step modal**: a click handler on `.stage[data-step]` opens a modal rendering that `pipeline_steps` entry — `name` (heading), `description` (via `renderMarkdown`), `inputs`/`outputs` (labelled lists), `agents` (a list — each agent name opens the agent modal / its prompt), `example_artifacts` (links, or "no examples yet"); dismissible (backdrop/Escape/close); mobile-usable. Per `contracts/site-ui-fixes.md` FR-003 + research D8. (FR-003, FR-006.)
- [ ] T023 [US4] `web/js/app.js` (MODIFIED) — the **agent-registry modal**: opening `data-open-modal="agents"` renders the `agents[]` block as a list of `name` + `purpose` + a link to `agents/registry.yaml` on GitHub (`registry_github_url`); clicking an agent → `await fetchAndRenderMarkdown(agents[i].prompt_raw_url)` injected as the prompt body + `tools` (+ `default_backend`/`default_model`) + a "view prompt on GitHub" link (`prompt_github_url`); dismissible; mobile-usable. Per `contracts/site-ui-fixes.md` FR-004 + research D8. (FR-004, FR-006.)
- [ ] T024 [US4] `web/css/components.css` / `web/css/layout.css` (MODIFIED) — styles for the pipeline-step and agent-registry modals (and the nested agent-prompt view) at desktop + mobile. (FR-017.)
- [ ] T025 [US4] Visual verification (Constitution III): serve `web/` locally; click every pipeline-diagram circle (each → a complete modal); open the agent-registry modal (all agents listed, incl. `submission_intake` once Phase 8 lands — until then, all *current* agents); click ≥3 agents (prompt renders, tools shown, GitHub links work); at ~375px too; screenshot. Commit (`spec-007: US4 — pipeline-step + agent-registry modals (#115)`).

**Checkpoint**: the system is legible to outside readers via in-place modals — independently shippable.

---

## Phase 7 — US5 (front-end): A visitor gives feedback on any artifact, or submits a paper (Priority: P2)

**Goal**: a "submit feedback" control on every artifact modal; a "submit a paper" control (URL or PDF); each creates a `human-submission`-tagged GitHub issue; the modal shows "issue created (link); processed within the hour".
**Independent test**: on any artifact (idea/spec/plan/in-progress/paper/review) there's a feedback control; submitting → a `human-submission`+`feedback` issue with full context + the confirmation message; "submit a paper" accepts a URL or a PDF (PDF staged under `submissions/inbox/`) → a `human-submission`+`new-paper` issue. No artifact type is missing the feedback control.

> Touches `web/js/auth.js` (after US3's changes there) + `web/js/app.js`/`dialog.js`.

- [ ] T026 [US5] `web/js/auth.js` (MODIFIED) — add `submitFeedback({target_id, target_kind, target_stage, content})` → `POST /repos/{OWNER}/{REPO}/issues` with `labels:["human-submission","feedback"]` and a structured body (blockquote summary; `target_*`; `submitter = user()?.login || "anonymous"`; the `content`; a footer) → returns the created issue; validates `content` non-empty before the call, throws on failure. Per `contracts/auth-js-delta.md` `submitFeedback`. (FR-012, FR-013.)
- [ ] T027 [US5] `web/js/auth.js` (MODIFIED) — add `submitPaper({url} | {pdfFile})`: `{url}` → `POST .../issues` with `labels:["human-submission","new-paper"]` + the URL in the body; `{pdfFile}` (a `File`) → client-side size check (≤ 10 MB; over → throw "PDF too large; submit a URL instead") → `PUT /repos/.../contents/submissions/inbox/<ISO-timestamp>-<slug>.pdf` (base64, `branch:main`) → then `POST .../issues` with `labels:["human-submission","new-paper"]` + the body referencing `submissions/inbox/<…>.pdf` → returns the issue. Add `submitFeedback`/`submitPaper` to the `LlmxiveAuth` exports. Per `contracts/auth-js-delta.md` `submitPaper` + research D4. (FR-014, FR-015; E6.)
- [ ] T028 [US5] `web/js/app.js` + `web/js/dialog.js` + `web/index.html` (MODIFIED) — add a "submit feedback" control to **every** artifact modal (idea, research spec, plan, in-progress research, paper, review — not just brainstormed ideas; the dialog collects free-text feedback and submits via `submitFeedback` with the modal's `target_*`); add a top-level "submit a paper" entry point (a dialog with a URL field or a PDF file-picker, submitting via `submitPaper`). (FR-012, FR-014.)
- [ ] T029 [US5] `web/js/app.js` / `web/js/dialog.js` (MODIFIED) — the FR-013b confirmation: on a successful submission (`submitFeedback`, `submitPaper`, **and** the existing `submitIdea`/`submitReview`) show in the modal a message that a new GitHub issue was created **with a clickable link** (`html_url`) **and** that the contribution will be processed within the next hour; on failure → inline error + the form's input preserved for retry. (FR-013b; SC-011.)
- [ ] T030 [US5] [P] `tests/phase2/test_submission_helpers.py` (NEW) — real-GitHub-API test (gated on a token): call the equivalent of `submitFeedback` (a small Python harness POSTing the same issue payload, OR — if a JS test runner isn't set up — assert the payload shape `web/js/auth.js` would send by extracting it) — create a test `human-submission`+`feedback` issue on the repo, assert its labels + body context, then close + delete it; same for `new-paper`+URL; for `new-paper`+PDF, stage a tiny test PDF via the Contents API, assert a `submissions/inbox/<…>.pdf` appeared, then clean it up. (FR-012..015.) *(If a browser-JS test harness is genuinely out of scope, this task validates the issue/file payloads via a Python equivalent of the helpers — the maintenance-agent tests in Phase 8 then exercise the consumer side end-to-end against real issues.)*
- [ ] T031 [US5] Visual verification (Constitution III): serve `web/` locally; on each artifact type there's a feedback control; submit one (a test issue is created — clean it up after) → the confirmation message (issue link + "within the hour") shows; the "submit a paper" control accepts a URL and a (small) PDF; at ~375px too; screenshot. Commit (`spec-007: US5 front-end — submitFeedback/submitPaper + per-artifact feedback UI + confirmation message (#115)`).

**Checkpoint**: humans can submit feedback/papers from the site (recorded as tagged issues) — the backend that processes them is Phase 8.

---

## Phase 8 — US5 (backend): the `submission_intake` maintenance agent + hourly cron (Priority: P2)

**Goal**: an hourly GitHub Action invokes a new lightweight maintenance agent over open `human-submission` issues; the agent triages each (route feedback / create a project / file a paper / acknowledge), comments, and closes it; per-submission failures are isolated; idempotent.
**Independent test**: create test `human-submission` issues of each sub-type → `gh workflow run submission-intake.yml` → each is acted on, gets a comment, and is closed (or, if unprocessable, stays open with a comment and the run still succeeds); running again is a no-op for the handled ones.

> Depends on Phase 7 (the issues to consume) — but the agent module + tests can be written in parallel with the front-end and just need a test issue to run against.

- [ ] T032 [US5] `agents/registry.yaml` (MODIFIED) + `agents/prompts/submission_intake.md` (NEW) — add the `submission_intake` entry (E7): `purpose` ≤ 200 chars ("Triage human-submission GitHub issues from the website — route feedback to the right pipeline step / create a project / file a submitted paper / acknowledge — then comment and close."), `inputs:[issue]`, `outputs:[project]`, `prompt_path: agents/prompts/submission_intake.md`, `default_backend: dartmouth`, `fallback_backends:[huggingface,local]`, `default_model: gemma.gemma3.27b`, `wall_clock_budget_seconds: 300`; verify it passes the `agent-registry` schema. Write the prompt: given an issue's sub-type + body + (for feedback) candidate targets + the valid pipeline steps, return a tight structured triage verdict (`target` / `action ∈ {route-to-<step>, create-project, acknowledge}` / one-sentence rationale), with an instruction to be conservative (prefer `acknowledge`/`route-to-<step>`-as-a-comment over aggressive state changes; prefer an existing project over a new one unless it's clearly a brand-new idea). Per `contracts/submission-intake-agent.md`. (FR-020.)
- [ ] T033 [US5] `src/llmxive/agents/submission_intake.py` (NEW) — `SubmissionIntakeAgent(Agent)` + `IntakeResult` dataclass (`status ∈ {"ok","failed","skipped"}`, `action`, `target`, `error`, `comment_url` — E8) + `process_submission_issue(issue, *, repo_root, gh, registry_entry=None) -> IntakeResult` per `contracts/submission-intake-agent.md`: parse labels (must be `human-submission` + one of `feedback`/`new-paper`, else `failed` + a comment, no close); for `feedback` — gather target context, one LLM call (render the prompt) → parse the verdict defensively → act (`route-to-<step>` → comment on the project's tracking issue + conservatively nudge state; `create-project` → reuse the brainstorm/idea-lifecycle project-creation path — **don't duplicate**; `acknowledge` → a comment); for `new-paper` — create-or-link the project (reuse the paper-init/project-creation paths), move a staged `submissions/inbox/<…>.pdf` to the project's canonical home via the Contents API (read → `PUT` → `DELETE` the inbox copy) or record the URL, clean up orphan inbox files; in all `ok` cases — comment on the `human-submission` issue describing what was done + **close it**; on any LLM/parse/unexpected failure — comment "couldn't process automatically: <reason>" + return `failed` (don't close); `skipped` if the work is already done (target project exists / PDF already moved / issue closed) — idempotency. Reuse an existing GitHub-API helper if one exists, else a thin `gh` wrapper. (FR-020; E8.)
- [ ] T034 [US5] The cron entry point — add a `submissions process` subcommand to `src/llmxive/cli.py` (or a `scripts/process_submissions.py`): precondition checks first (Constitution V — a GitHub token present; the `human-submission` label exists on the repo, creating it + `feedback`/`new-paper` if missing; `from llmxive.agents.submission_intake import process_submission_issue` imports) → on any precondition fail, exit non-zero with a clear message → else list open issues with label `human-submission` (paginated) → call `process_submission_issue` on each → log `ok`/`skipped`/`failed` per issue → exit 0 (a per-submission failure never fails the run; only a precondition failure does). Per `contracts/submission-intake-workflow.md`. (FR-021.)
- [ ] T035 [US5] `.github/workflows/submission-intake.yml` (NEW) — per `contracts/submission-intake-workflow.md`: `on: schedule: - cron: "0 * * * *"` + `workflow_dispatch`; `permissions: {contents: write, issues: write}`; `concurrency: {group: submission-intake, cancel-in-progress: false}`; steps — `actions/checkout@v5` (fetch-depth 0) → `actions/setup-python@v6` (3.11) → `pip install -e .` → run the entry point (`python -m llmxive submissions process`) with `env: {GITHUB_TOKEN: ${{secrets.GITHUB_TOKEN}}, DARTMOUTH_CHAT_API_KEY: ${{secrets.DARTMOUTH_CHAT_API_KEY}}}` → a final "push file moves if any" step committing `submission-intake: process submissions [skip ci]`. (FR-021; E9.)
- [ ] T036 [US5] [P] `tests/phase2/test_submission_intake.py` (NEW) — per `contracts/submission-intake-agent.md` test obligations: parser/edge (malformed labels → `failed`, no close, a comment; unparseable LLM verdict → `failed`, no close); real-GitHub-API (gated on a token) — create a test `human-submission`+`feedback` issue → `process_submission_issue` → assert a comment posted + the issue closed (clean up); same for `new-paper`+URL; for `new-paper`+staged-PDF — stage a tiny test PDF, create the issue, run the agent, assert the PDF moved to the canonical path + the inbox copy gone + the issue closed; real-LLM triage smoke (gated on `DARTMOUTH_CHAT_API_KEY` + `LLMXIVE_REAL_TESTS=1`) — a "missing edge case in the spec for PROJ-X" feedback → verdict targets PROJ-X with `route-to-<spec/clarify-step>`; a "you should look into Z" (new topic) → `create-project`; an off-topic one → `acknowledge`; idempotency — run twice over the same handled issue → 2nd is `skipped`, nothing duplicated. (FR-020, FR-021.)
- [ ] T037 [US5] Run `python -m pytest tests/phase2/test_submission_intake.py tests/phase2/test_submission_helpers.py -q` (offline tests pass; gated ones skip cleanly or pass with creds); `ruff check src/llmxive/agents/submission_intake.py src/llmxive/cli.py tests/phase2/`; then **exercise the workflow once manually** (Constitution III): create a test `human-submission`+`feedback` issue on the repo → `gh workflow run submission-intake.yml` → confirm it processed (comment + close), then a `new-paper`+URL one, then a `new-paper`+staged-PDF one (assert the PDF moved); confirm a precondition failure (e.g. unset token in a local invocation) exits non-zero. Commit (`spec-007: US5 backend — submission_intake agent + hourly intake cron (#115)`).

**Checkpoint**: submissions submitted via the site get triaged within the hour — US5 complete.

---

## Phase 9 — US6: "How to contribute" section + README refresh (Priority: P2)

**Goal**: an About-page "How to contribute" section listing the four modes with actionable pointers; the repo README rewritten to match the current system.
**Independent test**: About has a "How to contribute" section covering add ideas / help with development / provide feedback / review existing content, each with a usable pointer; the README, read end-to-end, contains no factual claim contradicted by the current repo.

- [ ] T038 [P] [US6] `web/index.html` (MODIFIED) — add a "How to contribute" section under `#about` listing: **add ideas** (→ the "submit idea" control), **help with development** (→ the GitHub repo / open issues), **provide feedback** (→ the "submit feedback" control on any artifact), **review existing content** (→ the review controls / the Reviews data) — each with a concrete pointer (link or "click here on the site" cue). Plain static markup; styled to match the About page. (FR-005; SC-010.)
- [ ] T039 [P] [US6] `README.md` (MODIFIED) — rewrite the repo-root README to match the current system: the two Spec-Kit pipelines (research + paper) and their stages; the agent registry (count + a pointer to `agents/registry.yaml`, including `submission_intake`); the public website (`context-lab.com/llmXive`) and how to use it (submit ideas/feedback/papers; review; browse); the `/speckit-*` spec-driven workflow; how to contribute. **Verify every factual claim against the current repo** (Constitution II — web-fetch/inspect, don't write from memory). (FR-016; SC-013.)
- [ ] T040 [US6] Visual verification (the About section) + a read-through of the README against the repo; fix any inaccuracy. Commit (`spec-007: US6 — How-to-contribute section + README refresh (#115)`).

**Checkpoint**: onboarding docs are accurate — US6 complete.

---

## Phase 10 — Polish & cross-cutting

- [ ] T041 Full regression: `python -m pytest tests/phase2/ -q --ignore=tests/phase2/test_librarian_cross_domain.py` → all pass (a transient arXiv HTTP 429 in `test_librarian_search.py` under suite load is a known flake — re-run it in isolation to confirm; not a regression). Capture the count. (SC — no-regression.)
- [ ] T042 Lint: `ruff check src/llmxive/web_data.py src/llmxive/agents/submission_intake.py src/llmxive/cli.py tests/phase2/` → clean (auto-fix import-order / unicode-comment issues per the existing pattern; do NOT reformat unrelated pre-existing nits in `cli.py` beyond what your change touches — keep the PR scoped).
- [ ] T043 Re-verify FR-019: re-run `web_data.py` (`python -c "from pathlib import Path; from llmxive.web_data import write_payload; write_payload(Path('.'))"`); confirm `web/data/projects.json` still has the `agents` + `pipeline_steps` blocks, per-project `current_artifact`, and the corrected `contributors` list (a pipeline-cron tick doesn't reintroduce any of these bugs). (SC-016.)
- [ ] T044 Mobile pass: re-check at ~375px that every modal touched/added (pipeline-step, agent-registry, project-artifact, submit-feedback, submit-paper) is scrollable, dismissible, not clipped. (FR-017; SC-014.)
- [ ] T045 [P] Diagnostic: write `notes/2026-05-13-spec-007-website-fixes-diagnostic.md` (or append to an appropriate notes file) recording — the screenshots from the visual-verification steps (desktop + mobile); the contributor-bug root cause + fix; the sign-out fix path taken (revoke vs. fallback); the SC-001..SC-016 verdicts; the manual `submission-intake` workflow-dispatch result. (Constitution III — UI behavior visually verified, recorded.)
- [ ] T046 [P] Tick all completed checkboxes in this `specs/007-website-ui-fixes/tasks.md`. Commit the doc + tasks updates (`spec-007: diagnostic + tasks tick (#115)`).
- [ ] T047 Push `008-website-ui-fixes`; open a PR against `main` (`gh pr create --base main --head 008-website-ui-fixes --title "Spec 007: llmXive website UI bug-fixes + polish (#115)" --body-file <(…)` — body summarizing: the static-site fixes (wordmark, tab indicator, pipeline+agent modals, how-to-contribute, artifact rendering, Markdown rendering); the data-correctness fixes in `web_data.py` (model-not-prompt contributors, correct counts, the new blocks); the auth fix (sign-out clears all state + revokes the OAuth grant / forces account-chooser); the submission front-end + the `submission_intake` agent + the hourly intake cron; the README refresh; the test plan; the SC-001..016 verdicts; the screenshots). Wait for the `real-call` CI to pass. After merge: confirm the `Deploy Pages` workflow runs green (re-syncs `web/`→`docs/`) and the `Submission Intake` cron's first run (or a `workflow_dispatch`) processes cleanly. Post the PR link on issue #115; for each #115 checkbox now satisfied, note which FR/PR addressed it.

---

## Dependencies & ordering

- **Phase 1 (Setup: T001–T003)** → everything (the Markdown renderer is used by US2 + US4).
- **Phase 2 (Foundational: T004–T010)** → US1 (corrected contributors), US2 (`current_artifact`), US4 (`agents`/`pipeline_steps` blocks). T004–T007 are sequential edits to `web_data.py`; T008/T009 [P] (different test files); T010 gates after them.
- **US1 (Phase 3: T011–T014)** — T011 [P] (`index.html`/`site.css` wordmark) ∥ T012 (`app.js`/`site.css` tab indicator) — both touch `site.css` so do T011 then T012 to avoid a conflict; T013 (contributors render) needs Phase 2; T014 gates.
- **US3 (Phase 4: T015–T017)** — touches `web/js/auth.js`; do **before** US5's `auth.js` changes. T016 is the Worker (external) or the client fallback.
- **US2 (Phase 5: T018–T020)** — needs Phase 1 + T007.
- **US4 (Phase 6: T021–T025)** — needs Phase 1 + T005/T006. T021 (`index.html`) before T022/T023 (`app.js`).
- **US5 front-end (Phase 7: T026–T031)** — touches `web/js/auth.js` **after** US3; T026/T027 (`auth.js`) before T028/T029 (`app.js`/`dialog.js`); T030 [P] (test file).
- **US5 backend (Phase 8: T032–T037)** — can be written in parallel with Phases 3–7 (different files: `agents/`, `src/llmxive/agents/`, `.github/workflows/`, `tests/phase2/`); the manual workflow exercise (T037) needs ≥1 `human-submission` issue (create a test one). T032→T033→T034→T035 sequential-ish; T036 [P].
- **US6 (Phase 9: T038–T040)** — T038 [P] (`index.html`) ∥ T039 [P] (`README.md`); T040 gates.
- **Polish (Phase 10: T041–T047)** — after all US phases. T045/T046 [P].
- **Suggested critical path**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T010 → T012 (tab indicator) → T018 (artifact modal) → T022/T023 (modals) → T015–T017 (sign-out) → T026–T029 (submission FE) → T032–T037 (intake backend) → T038/T039 → T041–T047. (US1/US6's static bits and the Phase-8 module can run in parallel branches of the same person's work.)

## Parallel-execution examples

- Phase 2: `T008` ∥ `T009` (different new test files).
- Across phases: `T011` (US1 wordmark) ∥ `T021` (US4 `data-step` markup) ∥ `T038` (US6 about section) ∥ `T039` (README) — all different files.
- Phase 8 (the intake backend) can proceed entirely in parallel with the Phase 3–7 site work — different file trees.

## Implementation strategy (MVP first)

- **MVP = US1 + US3** (the two P1 front-door / security fixes, both low-risk, both independently shippable). Land Phases 1–4 (skipping US2 if you want the absolute minimum, though US2 is also P1 and small).
- **Then** US2 (P1, the artifact-modal fix), then the P2 stories US4 → US5 → US6 in that order; each is an independent increment.
- The `submission_intake` agent + cron (Phase 8) is the largest single chunk; it can be developed and tested in isolation (against a test issue) and merged once US5's front-end (Phase 7) is in.
- The Cloudflare-Worker `/revoke` route (T016) is the one external dependency; if it can't be done, the client-side account-chooser fallback satisfies FR-011 with no Worker change.
