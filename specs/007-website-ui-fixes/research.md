# Phase 0 Research — spec 007 (website UI bug-fixes + polish, #115)

All `/speckit-clarify` questions were resolved in the spec's `## Clarifications` section; this file consolidates the *implementation* decisions those clarifications imply, plus the few remaining technical choices.

---

## D1 — Tab-indicator geometry (FR-002)

**Decision**: Keep the single `.tab-underline` element. On every layout-affecting event — a tab click, `window` `resize`, `orientationchange`, and `document.fonts.ready` (web-font load shifts text widths) — recompute `underline.style.left` and `underline.style.width` from `activeTab.getBoundingClientRect()` minus `tabsContainer.getBoundingClientRect()` (NOT `offsetLeft`/`offsetWidth`, which drift when the container has been horizontally scrolled). Debounce the `resize` handler (rAF). The underline element lives inside the scrolling tab row so it scrolls with the tabs; its `left` is relative to that row's content box.

**Rationale**: The current code (`app.js` ~L204-212, L230) uses `tab.offsetLeft`/`tab.offsetWidth` and only re-runs on `resize`; on mobile the tab row can wrap or horizontally scroll, so `offsetLeft` (relative to the offset parent, not the visual position) is wrong, and there's no recompute on orientation change or font load. Fixing the geometry math + the event set is the minimal correct fix and works at every breakpoint — exactly the clarification's "same sliding underline, made correct".

**Alternatives considered**: per-tab CSS bottom-border (can't mis-align, but loses the slide and changes the look); underline-desktop / highlight-mobile (two code paths). Rejected per the clarification.

---

## D2 — Markdown rendering library (FR-009b, FR-004, FR-009)

**Decision**: Vendor **one small, MIT/ISC-licensed Markdown→HTML library** (~1–10 KB minified) under `web/js/vendor/markdown.min.js`, with a `web/js/vendor/README.md` recording name, version, license, and source URL. Candidate: **`snarkdown`** (~1 KB, MIT) for the common case (headings, bold/italic, links, lists, code spans/blocks) — adequate for idea bodies, specs, plans, agent prompts. If a richer feature set (tables, GFM) proves necessary for some artifacts, swap to a `marked`-min build (~30 KB). The raw `.md` is fetched at modal-open from `https://raw.githubusercontent.com/ContextLab/llmXive/main/<path>` (no auth needed for a public repo); the rendered HTML is sanitized (the lib's escaping + we strip any `<script>`/`on*=`) before injection. No `web_data.py` change for rendering; no build step.

**Rationale**: The clarification chose client-side rendering with a small vendored lib explicitly. Vendoring (not a CDN `<script>`) keeps the site self-contained and avoids a third-party runtime dependency (Constitution IV / repo-cleanliness). `snarkdown` is the smallest credible option; `marked` is the fallback if features are missing. Fetching raw `.md` from `raw.githubusercontent.com` is the standard zero-auth way to read a public-repo file from a browser; it's cache-friendly.

**Alternatives considered**: pre-render in `web_data.py` (bloats `projects.json`, cron must re-render every tick — rejected by the clarification); a heavyweight client renderer like `markdown-it` (~100 KB — overkill); rendering server-side in a Worker (unnecessary moving part). All rejected.

**Security note**: Markdown from the repo is author-controlled (agents/maintainers), low risk, but the renderer's output is still sanitized before `innerHTML` injection (defense in depth — Constitution).

---

## D3 — OAuth sign-out: grant revocation vs. account-chooser (FR-010, FR-011)

**Decision**: Two-part fix in `web/js/auth.js`, plus a small Cloudflare-Worker adjunct:
1. **FR-010 (unconditional, client-only)**: `signOut()` removes `KEY_TOKEN` + `KEY_USER` from `localStorage` **and** `KEY_STATE` from `sessionStorage` (the current code forgets the latter), then re-renders. This always runs, first.
2. **FR-011 (grant revocation, via the proxy)**: After the local clear, `signOut()` POSTs `{ token }` to a new `<PROXY>/revoke` route on the Cloudflare Worker. The Worker — which holds the OAuth `client_id` + `client_secret` — calls `DELETE https://api.github.com/applications/{client_id}/grant` with `Authorization: Basic base64(client_id:client_secret)` and body `{ "access_token": token }` (GitHub's "Delete an app authorization" endpoint). This revokes *all* tokens for the user↔app pair, so the next `startLogin()` necessarily re-prompts at GitHub and the user can pick a different account. A failed `/revoke` (Worker down, GitHub error) logs a non-blocking `console.warn` + shows a small "couldn't fully revoke — you may need to sign out of github.com" notice; the user is still signed out locally.
3. **Fallback (if the Cloudflare Worker can't add `/revoke`)**: `startLogin()` forces GitHub's account chooser by first navigating to `https://github.com/logout` (which clears the github.com session) with a `return_to` back to the `authorize` URL — or, simpler, by appending the OAuth `prompt`-equivalent that GitHub honors. Either way the user re-authenticates and can choose an account. This is purely client-side; no Worker change.

**Cloudflare feasibility**: A Cloudflare Worker can absolutely make an outbound `fetch` to `api.github.com` with a `Basic` auth header — that's exactly what the existing `/` code-exchange route already does (it exchanges `code` for a token using the client secret). Adding a `/revoke` route is the same shape (one more `fetch`, a `DELETE`). So the primary path is expected to work; the fallback is the safety net the clarification asked for ("if the current setup with cloudflare still works"). The Worker change is documented in `contracts/oauth-proxy.md` and applied in that (external) repo.

**Rationale**: Grant revocation is the semantically-correct "sign out" (it ends the user↔app relationship, so a fresh sign-in is a real fresh sign-in) and directly fixes #115's "can't sign in as a new user". It needs a tiny proxy addition (the proxy already has the secret). The fallback handles the case the user flagged. The `KEY_STATE` cleanup is a free correctness fix in the same function.

**Alternatives considered**: client-side-only token clear with no revocation (doesn't fix account-switching — rejected, #115 flags it CRITICAL); revoking just *this* token via `DELETE /applications/{client_id}/token` instead of the whole grant (still leaves the grant, so GitHub still won't re-prompt — insufficient). Forcing the account-chooser *as the primary* (works, but an extra redirect every sign-in even when not switching — kept as the fallback only).

---

## D4 — Human submissions → tagged GitHub issues; PDF staging (FR-012..015)

**Decision**: New helpers in `web/js/auth.js` (mirroring the existing `submitIdea` / `submitReview`):
- `submitFeedback({ target_id, target_kind, target_stage, content })` → `POST /repos/{owner}/{repo}/issues` with a structured body (a blockquote summary, the target reference, the submitter login, the content, a footer) and `labels: ["human-submission", "feedback"]`. Returns the created issue (`html_url`, `number`).
- `submitPaper({ url } | { pdfFile })` → for a URL: `POST .../issues` with `labels: ["human-submission", "new-paper"]` and the URL in the body. For an uploaded PDF: GitHub's REST API has **no issue-attachment endpoint** (attachments are a web-UI-only feature), so we **stage** the PDF: `PUT /repos/{owner}/{repo}/contents/submissions/inbox/<ISO-timestamp>-<slug>.pdf` (base64) with `branch: main`, then `POST .../issues` referencing `submissions/inbox/<…>.pdf` in the body + `labels: ["human-submission", "new-paper"]`. Enforce a client-side size cap (≤ 10 MB) before the upload; over the cap, require a URL instead.
- On success, the modal shows the FR-013b message: *"✓ Submitted — created [issue #N](html_url). The submission intake agent will process this within the next hour."*
- On failure, the modal shows an error and keeps the form populated for retry.

The `submitFeedback` control is added to **every artifact modal** in `app.js` (idea, spec, plan, in-progress research, paper, review — not just brainstormed ideas, fixing the current `submitIdea`-only limitation). The "submit a paper" entry point is a top-level control (e.g. next to "submit idea").

**Rationale**: The clarification chose tagged GitHub issues as the canonical record. Reusing `ghFetch` + the `submitIdea`/`submitReview` pattern keeps it consistent (Constitution I — no parallel HTTP layer). PDF staging via the Contents API is the only browser-doable way (no attachment API); a size cap keeps git history sane; `submissions/inbox/` is a clearly-transient location the maintenance agent empties (moves the PDF to the project's canonical home and deletes the inbox copy).

**Alternatives considered**: committing a structured `feedback/<…>.yaml` file (the earlier /speckit-specify answer — superseded); a separate submissions service (unnecessary — issues + the Contents API suffice); base64-embedding the PDF in the issue body (issue bodies have a size limit and it's ugly — rejected).

---

## D5 — `web_data.py` contributor fix: root-cause first (FR-007, FR-008)

**Decision**: Before changing anything, determine which of these is the live bug (the spec notes `web_data.py` *already* keys AI contributors by `_normalize_model_name(model_name)`):
- (a) **Stale `web/data/projects.json`** — the deployed JSON predates the model-keying fix → just regenerate (+ ensure the cron regenerates it).
- (b) **A code path still emitting `agent_name`** — e.g. the `_agent_contributors` review-walk at ~L434 reads `agent_name` for some entry type → change it to read/normalize `model_name` (and bucket unknowns as `"unattributed"` per the spec's edge case).
- (c) **Double-counting / phantom counts** — `contribution_count` incremented per run-log entry rather than per distinct artifact, or the same artifact counted in two passes → dedup by `(contributor, artifact_path)` and reconcile against the actual artifact set.
- The site-JS regex (`/qwen|gemma|claude|tinyllama|gpt|mistral|llama/i.test(item.submitter)` in `app.js` ~L71) that *guesses* whether a `submitter` is a model — replace with an authoritative `kind` from the data (`web_data.py` already emits `kind: "llm" | "human" | "unattributed"`); the JS just renders the kind it's told.

Then: fix the identified cause in `web_data.py`, add a regression test (`tests/phase2/test_web_data_contributors.py`) asserting (i) no contributor row's `name` is a known prompt/agent name (`brainstorm`, `flesh_out`, `librarian`, …) and (ii) for ≥1 contributor, `contribution_count == ` an independently-counted artifact total from the fixture, regenerate `web/data/projects.json`, and commit.

**Rationale**: "Fix in place" (Constitution I) — `web_data.py` is the canonical builder; the site is a pure view, so the fix belongs in the builder, and the JS just stops second-guessing. Root-causing first avoids "fixing" something that's actually just stale data.

**Alternatives considered**: hand-correcting the contributor list in the JSON (violates "the site is a view" + would be re-broken on the next cron tick — rejected); a hard-coded model-name map in the JS (duplicates data — rejected).

---

## D6 — The `submission_intake` maintenance agent (FR-020)

**Decision**: A new agent following the repo's existing pattern:
- **Registry entry** in `agents/registry.yaml`: `name: submission_intake`, `purpose:` (≤ 200 chars: "Triage human-submission GitHub issues from the website — route feedback to the right pipeline step / create a project / file a submitted paper / acknowledge — then comment and close."), `prompt_path: agents/prompts/submission_intake.md`, `default_backend: dartmouth` (fallback huggingface, then local), `default_model: gemma.gemma3.27b` (a *fast* model — triage is a quick classification, not a deep task — matching the registry's "faster/less-complex → Gemma" routing), `wall_clock_budget_seconds: 300`. It is **tool-style** (like the librarian — it doesn't own a project stage; it's invoked by the cron, not the orchestrator's stage-routing).
- **Module** `src/llmxive/agents/submission_intake.py`: an `Agent` subclass + a `process_submission_issue(issue, *, repo_root, gh) -> IntakeResult` function: parse the issue's labels + body → for `feedback` — one LLM call decides {which existing artifact/project this concerns AND which pipeline step it implies AND whether it's actionable}; act accordingly (post a comment on the project's tracking issue / nudge the project's state / create a brainstormed project via the existing brainstorm path / or just acknowledge); for `new-paper` — create-or-link a project (and a `paper/` scaffold or a review entry as appropriate), move the staged PDF from `submissions/inbox/` to the project's canonical home (or record the URL), delete the inbox copy; in **all** cases, post a brief comment on the `human-submission` issue describing what was done, and close it. On an LLM failure or an unparseable issue → leave the issue open with an explanatory comment, return a `failed` result (the cron tolerates it).
- **Prompt** `agents/prompts/submission_intake.md`: instructs the model, given an issue's sub-type + body + (for feedback) a list of candidate artifacts/projects, to return a small structured verdict (which target, which action, rationale) — YAML or a tight JSON, parsed defensively.

**Rationale**: Reuses every existing convention (registry / prompts / backend router / `Agent` base) — Constitution I. Tool-style + cron-invoked mirrors the librarian, which the codebase already supports. A fast model for triage is the cost-effective choice (Constitution IV). The "leave open + comment on failure" behavior is fail-fast-but-isolated (Constitution V) and is exactly what FR-021 requires.

**Alternatives considered**: making it a pipeline-stage agent (it doesn't fit — submissions aren't projects-with-a-stage until *after* triage); doing the triage purely with rules/no LLM (a free-text feedback comment genuinely needs an LLM to route — rules can't); a heavyweight model (overkill for classification).

---

## D7 — The intake cron workflow (FR-021)

**Decision**: New `.github/workflows/submission-intake.yml`:
- `on: schedule: - cron: "0 * * * *"` (hourly) + `workflow_dispatch` (for the one-time manual exercise required by Constitution III before relying on the schedule) + `[skip ci]`-style guard so it doesn't trigger other workflows.
- `permissions: { contents: write, issues: write }` (commit file moves, comment/close issues).
- Steps: `actions/checkout@v5`; `actions/setup-python@v6`; `pip install -e .`; run a small entry point (a new CLI subcommand `python -m llmxive submissions process` or a tiny `scripts/process_submissions.py`) that: lists open issues with label `human-submission` via the GitHub API; for each, calls `submission_intake.process_submission_issue(...)`; if it returns `ok`, the agent already commented + closed; if `failed`, the agent already left an explanatory comment and the issue stays open; the run **does not fail** on per-submission errors (it logs them and exits 0) — only a setup-precondition failure (no token, missing label, import error) exits non-zero. Idempotent: an already-closed issue isn't returned by the "open issues" query, so re-runs naturally skip handled submissions; a partly-processed one is re-attempted from a safe point (the agent checks "does the target project already exist / is the PDF already moved" before acting).
- Uses `${{ secrets.GITHUB_TOKEN }}` (free, scoped to the repo) for the issue/Contents API; the agent's LLM calls use the existing `DARTMOUTH_CHAT_API_KEY` secret (already configured for the other pipeline crons).

**Rationale**: Mirrors the existing pipeline-cron workflows (`pipeline-brainstorm.yml` etc. — hourly schedule, `pip install -e .`, a Python entry point). Free (GitHub Actions minutes). The "don't fail the run on a single bad submission" + idempotency are FR-021's explicit requirements.

**Alternatives considered**: an `on: issues` event trigger (fires immediately on issue creation — but the spec/clarification asked for "every hour" + a cron is simpler to make idempotent and to reason about; we can add the event trigger later as an optimization); a separate scheduler service (unnecessary — GitHub Actions cron is the free, in-repo option).

---

## D8 — Pipeline-step & agent-registry modal content sourcing (FR-003, FR-004, FR-006)

**Decision**: `src/llmxive/web_data.py` emits two new top-level blocks into `web/data/projects.json`:
- `agents`: a list, one per `agents/registry.yaml` entry — `{ name, purpose, prompt_path, prompt_github_url, registry_github_url, tools, default_backend, default_model }`. The site's agent-registry modal renders this list; clicking an agent fetches the `prompt_path` `.md` from `raw.githubusercontent.com`, renders it with the vendored Markdown lib, and shows `tools` + the GitHub link.
- `pipeline_steps`: a list, one per pipeline stage (research lane + paper lane) — `{ key, name, lane, description, inputs, outputs, agents: [<agent name>...], example_artifacts: [{ project_id, title, github_url }...] }`. `description`/`inputs`/`outputs` come from the pipeline-stage definitions (the `Stage` enum + its docstrings / the existing `STAGE_TO_AGENT` map + a short per-stage blurb that already exists in the About-page markup — consolidate that prose into `web_data.py` so it's defined once); `agents` from `STAGE_TO_AGENT` (+ the librarian/tool-style agents a stage uses); `example_artifacts` = the most-recent N projects currently at (or past) that stage, from the existing per-project data. The site's pipeline-diagram circles get `data-step="<key>"`; clicking one opens a modal rendering that step's block.

**Rationale**: Constitution I — the site must not hand-maintain step descriptions / agent lists; they're derived in the one canonical builder from the one canonical registry + stage definitions. The About-page markup currently has short per-stage `<p>` blurbs *inline in HTML* — that's a (small) duplication; moving them into `web_data.py`'s `pipeline_steps` and having the HTML render from the data removes it. `raw.githubusercontent.com` for the prompt `.md` files keeps the JSON small (it ships paths, not prompt bodies).

**Alternatives considered**: shipping full prompt bodies in `projects.json` (bloats it — rejected); a separate `agents.json` / `pipeline.json` file (more files, same data — folding into the existing `projects.json` is simpler); keeping the step descriptions in HTML (duplication — rejected).

---

## D9 — Project-modal artifact resolution (FR-009)

**Decision**: `web_data.py` ensures each per-project entry in `projects.json` has a `current_artifact: { type: "pdf" | "markdown" | "latex" | "json" | "yaml" | "none", repo_path: <path or null>, github_url: <url or null> }` (the published-PDF case keeps the existing `pdf_url`; the `type` field tells the JS which to do). In `app.js`, the project-modal open path becomes: if the project has a published PDF → embed it (current behavior, but only when it actually exists); else if `current_artifact.type` is `markdown` → fetch the raw `.md`, render with the vendored lib, inject sanitized; else if `latex`/`json`/`yaml` → fetch + show as `<pre>`-formatted source with a "view on GitHub" link; else (`none`) → show a placeholder ("No artifact yet — this project is at stage X; the next artifact will appear here") + the project's metadata + a "browse the project on GitHub" link. Never `<embed src="…nonexistent.pdf">`.

**Rationale**: Directly implements FR-009 + the "never a broken embed" edge case. The artifact-type resolution is data-driven (the builder knows the project's stage and therefore its current artifact), so the JS is a simple `switch`. Reuses the vendored Markdown lib (D2).

**Alternatives considered**: having the JS probe for `<project>.pdf` and fall back on a 404 (works but flickers + a wasted request — better to be told by the data); a server-side render of every artifact (rejected — see D2).

---

## Summary of decisions

| # | Decision |
|-|-|
| D1 | Tab indicator: one sliding underline, recomputed from `getBoundingClientRect` on click/resize/orientation/font-load |
| D2 | Markdown: vendored small lib (`snarkdown` ~1 KB, MIT; `marked`-min fallback) under `web/js/vendor/`; fetch raw `.md`; sanitize before inject |
| D3 | Sign-out: unconditional local clear (incl. `sessionStorage` state) + `POST <PROXY>/revoke` → Worker `DELETE /applications/{client_id}/grant`; fallback = force account-chooser on sign-in; failed revoke is non-blocking |
| D4 | Submissions: `submitFeedback` / `submitPaper` in `auth.js` → `human-submission`+sub-type GitHub issues; PDFs staged via the Contents API to `submissions/inbox/` (≤10 MB cap); feedback control on every artifact modal; FR-013b confirmation message |
| D5 | Contributor fix: root-cause in `web_data.py` (stale data vs. `agent_name` path vs. double-count), fix in the builder, drop the JS model-guessing regex, regression test, regenerate |
| D6 | `submission_intake` agent: registry entry + `agents/prompts/submission_intake.md` + `src/llmxive/agents/submission_intake.py`; tool-style; fast model (Gemma 3 27B); fail-open-but-isolated |
| D7 | Intake cron: `.github/workflows/submission-intake.yml`, hourly + `workflow_dispatch`; lists open `human-submission` issues; idempotent; per-submission-failure-tolerant; uses `GITHUB_TOKEN` + the existing LLM secret |
| D8 | `web_data.py` emits `agents` + `pipeline_steps` blocks (derived from `registry.yaml` + stage definitions + recent artifacts); site modals render from them; prompt `.md` fetched from `raw.githubusercontent.com` |
| D9 | Project-modal artifact: data-driven `current_artifact.{type,repo_path,github_url}`; JS resolves PDF → rendered Markdown → formatted source → placeholder; never a broken embed |

No unresolved `NEEDS CLARIFICATION` remain.
