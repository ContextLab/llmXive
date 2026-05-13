# Phase 1 Data Model — spec 007 (website UI bug-fixes + polish, #115)

This feature mostly *changes how existing data is rendered* and adds a couple of *new derived blocks* + a couple of *new persisted records*. There's no database. Entities below are grouped by where they live: new blocks in the build artifact (`web/data/projects.json`), new persisted records (GitHub issues / staged files / a registry entry / a workflow), and a few changed shapes.

---

## E1 — `agents` block (in `web/data/projects.json`; derived, regenerated each build)

A new top-level array, one entry per `agents/registry.yaml` agent.

| Field | Type | Notes |
|-|-|-|
| `name` | str | The agent's registry name (e.g. `librarian`, `submission_intake`). |
| `purpose` | str | From the registry. |
| `prompt_path` | str | Repo-relative path of the agent's prompt `.md` (e.g. `agents/prompts/librarian.md`). |
| `prompt_github_url` | str | `https://github.com/ContextLab/llmXive/blob/main/<prompt_path>` (the "view on GitHub" link). |
| `prompt_raw_url` | str | `https://raw.githubusercontent.com/ContextLab/llmXive/main/<prompt_path>` (the site fetches this to render the prompt). |
| `registry_github_url` | str | `https://github.com/ContextLab/llmXive/blob/main/agents/registry.yaml` (constant; included for the "view the registry" link). |
| `tools` | list[str] | From the registry (may be empty). |
| `default_backend` | str | From the registry. |
| `default_model` | str | From the registry. |
| `inputs` / `outputs` | list[str] | From the registry (the agent's I/O kinds). |

**Source**: `agents/registry.yaml` (the canonical agent list). **Built by**: `src/llmxive/web_data.py` (`build_payload` gains an `agents` key). **Consumed by**: the agent-registry modal in `web/js/app.js` (lists `name`+`purpose`; on click, fetches `prompt_raw_url`, renders with the vendored Markdown lib, shows `tools` + `prompt_github_url`). **Validation**: every `agents/registry.yaml` entry MUST appear exactly once; `prompt_path` MUST point to an existing file.

---

## E2 — `pipeline_steps` block (in `web/data/projects.json`; derived, regenerated each build)

A new top-level array, one entry per pipeline stage (both lanes — research and paper).

| Field | Type | Notes |
|-|-|-|
| `key` | str | Stable id used as `data-step` on the diagram circle (e.g. `flesh_out`, `paper_draft`). |
| `name` | str | Display name (e.g. "Flesh-out"). |
| `lane` | str | `"research"` \| `"paper"`. |
| `order` | int | Position within the lane. |
| `description` | str | What the step does (Markdown-ish; rendered with the vendored lib). Consolidated here from the prose currently inline in the About-page HTML + the `Stage` enum docstrings. |
| `inputs` | list[str] | The artifact(s)/state the step consumes. |
| `outputs` | list[str] | The artifact(s)/state it produces. |
| `agents` | list[str] | Names of the agents this step uses (from `STAGE_TO_AGENT` + any tool-style agents it calls, e.g. `librarian`); each links to its `agents` entry (E1). |
| `example_artifacts` | list[{project_id, title, github_url}] | The most-recent N (≈3–5) projects currently at — or that have passed through — this stage, with a link to the relevant artifact in that project. May be empty (→ the modal shows "no examples yet"). |

**Source**: the pipeline-stage definitions (`Stage` enum + `STAGE_TO_AGENT` + the per-stage blurbs) + `agents/registry.yaml` + the existing per-project data already in `projects.json`. **Built by**: `web_data.py`. **Consumed by**: the pipeline-diagram modal in `app.js` (the diagram circles carry `data-step="<key>"`; clicking opens a modal rendering `description` (Markdown), `inputs`, `outputs`, the `agents` list (each → the agent modal / its prompt), and `example_artifacts` links). **Validation**: every pipeline stage MUST appear; `agents` names MUST exist in E1; `example_artifacts` `project_id`s MUST exist in the projects list.

---

## E3 — Per-project `current_artifact` (in `web/data/projects.json`; derived; changed/added per-project field)

A field on each existing per-project entry telling the modal what to display when there's no published PDF.

| Field | Type | Notes |
|-|-|-|
| `type` | str | `"pdf"` \| `"markdown"` \| `"latex"` \| `"json"` \| `"yaml"` \| `"none"`. `"pdf"` only when the project has a published paper PDF. |
| `repo_path` | str \| null | Repo-relative path of the artifact (the idea `.md`, the spec, the plan, the LaTeX, …); `null` when `type == "none"`. |
| `github_url` | str \| null | `https://github.com/.../blob/main/<repo_path>` (the "view on GitHub" link); `null` when `type == "none"`. |
| `raw_url` | str \| null | `https://raw.githubusercontent.com/.../main/<repo_path>` (the site fetches this for `markdown`/`latex`/`json`/`yaml`); `null` for `pdf` (the existing `pdf_url` is used) and `none`. |

**Source**: the project's stage + its files (the builder knows, from the project state, which artifact is "current"). **Built by**: `web_data.py` (extends `_project_to_entry`). **Consumed by**: the project modal in `app.js` (resolution: published PDF → embed; `markdown` → fetch+render; `latex`/`json`/`yaml` → fetch+`<pre>`; `none` → placeholder). **Validation**: when `type != "none"`, `repo_path` MUST exist; `type == "pdf"` iff there's a published PDF.

---

## E4 — Contributor row (in `web/data/projects.json`; **changed** shape/semantics)

Existing entity; this feature fixes its attribution + counts (FR-007, FR-008). Already largely correct in `web_data.py` (keyed by `_normalize_model_name`); the fix is to (a) ensure no code path emits a prompt/agent name, (b) add an `"unattributed"` kind for unknown-model contributions, (c) make `contribution_count` a count of *distinct artifacts* (no double-counting), and (d) have the site JS render the `kind` it's told rather than regex-guessing.

| Field | Type | Notes |
|-|-|-|
| `name` | str | A **model identifier** (e.g. `qwen.qwen3.5-122b`, normalized) for AI contributors, or a GitHub username for humans, or the literal `"unattributed"` bucket. **Never** a prompt/agent name. |
| `kind` | str | `"llm"` \| `"human"` \| `"unattributed"`. The site renders this directly (no regex inference). |
| `contribution_count` | int | Count of *distinct artifacts* this contributor produced, as recorded in canonical state. No double-counting; no phantom entries. |
| `areas` | list[str] | The kinds of work (spec, plan, code, data, paper, review, idea, …) — unchanged. |

**Source**: run-logs (`model_name` per successful agent invocation), project front-matter (`submitter`/`model_name`), review front-matter (`reviewer_name`/`model_name`), human reviewer rows. **Built by**: `web_data.py` (`_agent_contributors` + `_submitter_contributors` + the human-review merge). **Consumed by**: the Contributors tab in `app.js`. **Validation (regression test)**: no row's `name` is a known prompt/agent name; for ≥1 row, `contribution_count` equals an independently-derived artifact count from the fixture.

---

## E5 — Human submission (a GitHub issue; **new** persisted record)

The canonical record of a website-submitted contribution. Created by `web/js/auth.js` (`submitFeedback` / `submitPaper`) via the GitHub Issues API; consumed and closed by the `submission_intake` agent.

| Aspect | Value |
|-|-|
| Labels | `human-submission` + exactly one sub-type: `feedback` \| `new-paper`. |
| Title | A short human-readable summary (e.g. `Feedback on PROJ-123: …` or `Paper submission: <title-or-host>`). |
| Body (structured) | A blockquote summary; then — for `feedback`: `target_id` (project/artifact id), `target_kind`, `target_stage`, `submitter` (GitHub login), the feedback `content`; for `new-paper`: the `url` inline OR a reference to the staged PDF at `submissions/inbox/<…>.pdf`, plus the `submitter`; then a footer pointing back to the site + noting "the submission intake agent will process this within the hour". |
| Lifecycle | Created `open` by the site → picked up by the hourly `submission-intake` cron → the `submission_intake` agent triages it, acts (routes / creates a project / files the paper / acknowledges), posts a comment describing what it did, and **closes** it. On a triage/LLM failure: stays `open` with an explanatory comment; re-attempted next cron tick. |
| Identity | The issue number (GitHub-assigned). The site shows `html_url` to the user as the confirmation link. |

**Validation**: MUST carry enough context for the agent to act (a `feedback` issue MUST name a target; a `new-paper` issue MUST have a URL or a staged-PDF reference). The site MUST NOT need to commit any repo file for a `feedback` submission (only `new-paper`-with-PDF stages a file).

---

## E6 — Staged PDF (a committed file under `submissions/inbox/`; **new**, transient)

A PDF uploaded via the "submit a paper" control, staged into the repo because the GitHub REST API has no issue-attachment endpoint.

| Aspect | Value |
|-|-|
| Path | `submissions/inbox/<ISO-timestamp>-<slug>.pdf` (slug from the submitter-provided title or filename). |
| Created by | `web/js/auth.js` `submitPaper` — `PUT /repos/.../contents/<path>` (base64), `branch: main`, then the file is referenced in the `new-paper` issue body. |
| Size cap | ≤ 10 MB (enforced client-side before upload; over the cap → require a URL instead). |
| Lifecycle | Created on submission → the `submission_intake` agent moves it to the relevant project's canonical home (e.g. `projects/PROJ-###-…/paper/submitted/<…>.pdf` or wherever the triage decides) and **deletes** the `submissions/inbox/` copy when it closes the issue. `submissions/inbox/` is meant to be empty between cron ticks. |

**Validation**: a `submissions/inbox/<…>.pdf` SHOULD always be referenced by an open `human-submission`+`new-paper` issue; an orphaned inbox file (no referencing issue) is cleaned up by the agent's next run.

---

## E7 — `submission_intake` agent registry entry (in `agents/registry.yaml`; **new**)

| Field | Value |
|-|-|
| `name` | `submission_intake` |
| `purpose` | ≤ 200 chars — "Triage human-submission GitHub issues from the website: route feedback to the right pipeline step / create a project / file a submitted paper / acknowledge — then comment and close the issue." |
| `inputs` / `outputs` | the issue → project/comment (tool-style; doesn't own a stage) |
| `prompt_path` | `agents/prompts/submission_intake.md` |
| `default_backend` | `dartmouth` (fallback `huggingface`, then `local`) |
| `default_model` | `gemma.gemma3.27b` (fast — triage is a quick classification) |
| `wall_clock_budget_seconds` | `300` |

**Validation**: must pass the existing `agent-registry` schema (the `purpose` ≤ 200 chars, etc.); the `prompt_path` file must exist.

---

## E8 — `IntakeResult` (in-memory; returned by `submission_intake.process_submission_issue(...)`)

| Field | Type | Notes |
|-|-|-|
| `status` | str | `"ok"` (acted + commented + closed the issue) \| `"failed"` (left the issue open with an explanatory comment) \| `"skipped"` (already handled — e.g. the target project already exists; idempotency). |
| `action` | str \| null | What was done: `routed-to-step` / `created-project` / `filed-paper` / `acknowledged` (when `ok`); `null` otherwise. |
| `target` | str \| null | The project/artifact id acted on / created, if any. |
| `error` | str \| null | The exception message / reason, when `failed`. |
| `comment_url` | str \| null | The URL of the comment the agent posted on the issue. |

**Lifecycle**: computed once per issue per cron tick; logged; not persisted (the persisted record is the issue's comment + closed state + any committed file moves).

---

## E9 — `submission-intake` workflow (`.github/workflows/submission-intake.yml`; **new**)

| Aspect | Value |
|-|-|
| Triggers | `schedule: - cron: "0 * * * *"` (hourly) + `workflow_dispatch`. |
| Permissions | `contents: write`, `issues: write`. |
| Steps | checkout (`@v5`) → setup-python (`@v6`) → `pip install -e .` → run the entry point (`python -m llmxive submissions process` or `scripts/process_submissions.py`) which lists open `human-submission` issues and calls `submission_intake.process_submission_issue` on each. |
| Failure semantics | A per-submission failure → the issue stays open with a comment; the run still exits 0. Only a setup-precondition failure (no token / missing label / import error) exits non-zero. |
| Idempotency | Closed issues aren't in the "open issues" query → handled submissions are skipped on re-runs; partly-processed ones are re-attempted from a safe point. |
| Secrets | `${{ secrets.GITHUB_TOKEN }}` (issue/Contents API) + `${{ secrets.DARTMOUTH_CHAT_API_KEY }}` (the agent's LLM calls — already configured for the other pipeline crons). |

---

## Changed-existing-entity summary

- **`web/data/projects.json`** — gains top-level `agents` (E1) and `pipeline_steps` (E2) arrays; each per-project entry gains `current_artifact` (E3); the `contributors` rows get fixed attribution + counts + an explicit `kind` (E4). Everything else unchanged.
- **`web/js/auth.js`** — `signOut()` also clears the `sessionStorage` OAuth-state key and calls the proxy `/revoke`; gains `submitFeedback` / `submitPaper`; (fallback) `startLogin` forces the account-chooser. The existing `submitIdea` / `submitReview` / `ghFetch` are unchanged (reused).
- **`web/js/app.js`** — the tab-indicator geometry; the pipeline-step + agent-registry modals; the project-modal artifact resolution; the per-artifact feedback control + the FR-013b confirmation; drops the model-name-guessing regex (renders `kind` from the data).
- **`web/index.html` / `web/css/*`** — wordmark box (`white-space: nowrap`); `data-step` on the pipeline circles; the agent-registry entry point; the "How to contribute" section; the submission controls; new modal styles (desktop + mobile); the `.tab-underline` CSS no longer needs hard-coded offsets.
- **`agents/registry.yaml`** — gains the `submission_intake` entry (E7).
- **`README.md`** — rewritten to match the current system.
- **`src/llmxive/web_data.py`** — emits E1/E2/E3; fixes E4.
- **`docs/`** — re-synced from `web/` by the existing `Deploy Pages` workflow on push to `main` (no manual change).
