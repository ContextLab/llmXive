# Feature Specification: Website Integration with Agentic Pipeline

**Feature Branch**: `002-website-integration`
**Created**: 2026-04-29
**Status**: Draft
**Input**: Adapt the new design at web/notes/design/ to the live llmXive site so it accurately reflects the agentic pipeline (spec 001) — real counters, per-stage artifact visibility, true About narrative, paper-card artifact dialogs, GitHub login, secure local API key storage.

## User Scenarios & Testing

### User Story 1 — A visitor sees the live, accurate state of llmXive in seconds (Priority: P1)

A first-time visitor lands on https://context-lab.com/llmXive/. The hero counters show real numbers (no hard-coded values). Tabs show real artifacts produced by the agentic pipeline.

**Why this priority**: Without an accurate landing page, every other piece of polish is window-dressing. This is the minimum viable product.

**Independent Test**: Load the page in a fresh browser. Verify all 4 hero counters match what is on disk in `state/projects/*.yaml` and `state/run-log/*.jsonl`. Verify each tab populates from `web/data/projects.json`.

**Acceptance Scenarios**:
1. **Given** the pipeline has run at least once and produced `web/data/projects.json`, **When** a visitor loads `index.html`, **Then** hero counters show `total_contributions`, `active_projects`, `papers_posted`, `total_contributors` from the JSON file (no hard-coded literals).
2. **Given** the JSON file is missing or malformed, **When** the page loads, **Then** counters show `—` and a non-blocking banner reads "Pipeline state not yet generated."
3. **Given** the JSON contains 17 projects across many stages, **When** a visitor switches tabs, **Then** each tab shows projects whose `current_stage` falls into that tab's stage-set (Papers ↔ POSTED, In Progress ↔ IN_PROGRESS+RESEARCH_COMPLETE+RESEARCH_REVIEW, etc.).

### User Story 2 — A visitor inspects every artifact a project produced (Priority: P1)

Clicking any paper card opens a modal showing: the compiled PDF in an embedded viewer, plus a chronological log of every artifact related to the project (spec.md, plan.md, tasks.md, code paths, data paths, figures, review records, citation status, run-log entries). Clicking any list item opens that artifact directly.

**Why this priority**: This is the user's headline ask and the strongest signal that the new pipeline produces genuine work.

**Independent Test**: Click a paper card. Confirm an embedded `<embed>` PDF renders. Confirm the artifact list contains every file under `projects/<PROJ-ID>/` plus relevant `state/` entries for that project. Click each item; confirm it opens the raw file (GitHub blob URL or local path) in a new tab.

**Acceptance Scenarios**:
1. **Given** project PROJ-007 has reached POSTED, **When** a user clicks its card, **Then** the modal shows `paper/pdf/PROJ-007-*.pdf` rendered inline AND a list with the spec, plan, tasks, code/, data/, figures/, reviews/, citations, and last 10 run-log entries.
2. **Given** the user clicks a list item like `tasks.md`, **When** the click fires, **Then** the file opens at `https://github.com/ContextLab/llmXive/blob/<ref>/projects/PROJ-007-.../specs/001-.../tasks.md`.
3. **Given** an in-progress project has no PDF yet, **When** a user clicks its card, **Then** the dialog shows "No PDF compiled yet" and still lists all available artifacts.

### User Story 3 — A signed-in contributor submits an idea or review on the live site (Priority: P2)

A visitor clicks "Sign in with GitHub", authenticates via the OAuth web flow (proxied through a Cloudflare Worker), and gains the ability to (a) submit an idea (creates a GitHub issue tagged for brainstorming), (b) submit a human review (creates a review markdown file via Contents API).

**Why this priority**: This unlocks the human-in-the-loop functionality required by Constitution Principle II. It can ship after US1+US2 since unauthenticated visitors get a fully usable read-only site.

**Independent Test**: Click "Sign in with GitHub", complete the redirect dance, verify avatar + login appear in topbar. Click "Submit Idea", fill the form, submit; verify a GitHub issue exists with label `idea` and the brainstorm template body. Click an artifact, click "Add review", submit; verify a new file under `projects/<PROJ-ID>/reviews/research/` exists on `main`.

**Acceptance Scenarios**:
1. **Given** the OAuth Worker is reachable and the user has a GitHub account, **When** the user clicks "Sign in with GitHub", **Then** within 5 seconds the topbar shows their avatar + login.
2. **Given** the user is signed in and submits a valid idea, **When** they click Submit, **Then** a GitHub issue is created with title, body, and labels `idea, brainstormed`.
3. **Given** the user is signed in and submits a review with verdict=accept, **When** they click Submit, **Then** a file `human__YYYY-MM-DD__M.md` is committed to `projects/<PROJ-ID>/reviews/research/` with score 1.0.
4. **Given** a signed-out user clicks "Submit Idea", **When** the click fires, **Then** the modal first prompts them to sign in.

### User Story 4 — A maintainer runs the pipeline locally without re-pasting the API key each time (Priority: P2)

A maintainer types `python -m llmxive run` once. The first time, the CLI asks for the Dartmouth Chat key and stores it encrypted at-rest under `~/.config/llmxive/credentials.toml` (or equivalent OS keychain). On every subsequent run, the key is loaded silently.

**Why this priority**: Required for Maintainer-mode reproducibility (Constitution Principle V — fail fast on missing secrets). Must ship before US7.

**Independent Test**: Delete `~/.config/llmxive/credentials.toml`. Run `python -m llmxive preflight`. Confirm prompt for the key. Re-run preflight; confirm no prompt and exit 0 in <5s.

**Acceptance Scenarios**:
1. **Given** no credentials file exists and `DARTMOUTH_CHAT_API_KEY` is not in the environment, **When** the user runs `python -m llmxive run`, **Then** the CLI prompts: "Enter Dartmouth Chat API key (sk-…):". Input is read with no echo.
2. **Given** the user enters a valid-looking key, **When** they press enter, **Then** the key is written to `~/.config/llmxive/credentials.toml` with file mode 0600 and the run continues.
3. **Given** the credentials file exists with mode 0600, **When** any subsequent `python -m llmxive *` command runs, **Then** the key is loaded and no prompt appears.
4. **Given** the credentials file exists with mode > 0600 (group-readable), **When** any command runs, **Then** preflight refuses to start with "credentials file has unsafe permissions; chmod 600 it" and exit 1.

### User Story 5 — A visitor reads the About page and the narrative is true (Priority: P2)

The About section names the actual 34-state pipeline, the two review gates with their actual point thresholds (machine-readable, tied to `data-threshold` spans the test suite already validates), and explains the Spec-Kit-per-project model.

**Why this priority**: Trust. A misleading About page actively undermines the credibility of the project.

**Independent Test**: Open the About tab. Verify every claim either (a) names a Stage value from `src/llmxive/types.py` or (b) references a `data-threshold` span value, and (c) describes Spec Kit's role in both research and paper pipelines.

**Acceptance Scenarios**:
1. **Given** the page is loaded, **When** a user opens About, **Then** the pipeline diagram shows the canonical lifecycle (research lane + paper lane) with stage names matching the Stage enum.
2. **Given** the about page has `data-threshold` spans, **When** the existing test `test_about_thresholds.py` runs, **Then** it still passes.
3. **Given** "Five-stage pipeline" is the old narrative, **When** the new About loads, **Then** the heading reads instead about Spec-Kit-per-project + 34-stage lifecycle and the 5-node diagram is replaced by the two-lane research+paper diagram.

### User Story 6 — Aggregates and counters are real (Priority: P3)

Every count on the page (hero stats, tab counts, kanban column counts, contributors KPIs) is computed from real artifacts in the repo, not from sample data.

**Why this priority**: Necessary for honesty (Constitution Principle II — verified accuracy) but cosmetic if all of US1–US5 work.

**Independent Test**: Add a new project to `state/projects/`. Re-run `status_reporter`. Verify every counter on the page increments accordingly.

**Acceptance Scenarios**:
1. **Given** N projects exist on disk, **When** `status_reporter` regenerates `web/data/projects.json`, **Then** `aggregates.active_projects` equals the count of projects whose `current_stage` is not in `{POSTED, RESEARCH_REJECTED, PAPER_FUNDAMENTAL_FLAWS, BLOCKED}`.
2. **Given** the run-log contains M `outcome=success` entries with non-self-review agents, **When** the JSON regenerates, **Then** `aggregates.total_contributions == M`.
3. **Given** a paper review record exists, **When** the page reloads, **Then** the contributors list includes the human reviewer with `kind=human` and `n=1`.

### User Story 7 — End-to-end pipeline run produces real papers visible on the site (Priority: P3)

A maintainer runs the local pipeline to populate the brainstormed-ideas backlog with at least 5 ideas, takes 2 of them through the full pipeline (specify → clarify → plan → tasks → analyze → implement → review → paper Spec Kit → posted), and these new artifacts appear on the live site.

**Why this priority**: This is the final acceptance test for the entire feature. Everything else must work first.

**Independent Test**: Start with an empty `projects/` and `state/projects/` (or after a clean migration). Run `python -m llmxive brainstorm 5` then `python -m llmxive run --advance --max-cycles 50`. Verify ≥2 projects reach `POSTED`, that `web/data/projects.json` contains them, and that the rendered site shows them with full artifact dialogs.

## Edge Cases

- **No projects yet**: Hero counters show 0/0/0/0; tabs show empty-state messages; About still works.
- **OAuth Worker offline**: Sign-in button shows "GitHub login temporarily unavailable" and remains clickable so the user knows the issue is transient.
- **PDF in artifact dialog fails to load**: Modal shows "Could not load PDF" with a direct link to GitHub raw.
- **User on Safari with PDF rendering disabled**: Fall back to a download link.
- **Two visitors submit the same idea simultaneously**: Both issues are created (no de-duplication; surfacing as a duplicate is the brainstorm/lit-search agent's job, not the website's).
- **Local pipeline run on Windows**: Credentials path uses `%APPDATA%\llmxive\credentials.toml` on Windows, `~/.config/llmxive/credentials.toml` on POSIX.
- **Credentials file exists but key is invalid**: First API call fails; preflight catches this and prints "Stored Dartmouth key rejected by server; rotate it with `python -m llmxive auth rotate`."

## Functional Requirements

### Hero + Layout
- **FR-001**: The site MUST adopt the visual design from `web/notes/design/` (typography, colors, layout, motion) without modification to look-and-feel.
- **FR-002**: All four hero counters MUST be sourced from `web/data/projects.json::aggregates`, never hard-coded.
- **FR-003**: The page MUST render visibly within 1.5 seconds on a cold cache for a 200-project repo (US1 latency budget).
- **FR-004**: The site MUST work fully read-only without authentication.

### Tabs and Artifact Visibility
- **FR-005**: There MUST be tabs covering every stage in the new pipeline. The tab set is: `Published` (POSTED), `In Progress` (IN_PROGRESS through RESEARCH_REVIEW), `Paper Pipeline` (PAPER_DRAFTING_INIT through PAPER_REVIEW), `Plans` (PLANNED, TASKED, ANALYZED), `Designs` (SPECIFIED, CLARIFIED), `Backlog` (BRAINSTORMED, FLESH_OUT_*), `Contributors`, `About`.
- **FR-006**: The Backlog tab MUST display a kanban with columns for every Stage value from BRAINSTORMED through PAPER_REVIEW (collapsing terminal accept/reject branches into their parent column), so every artifact a project has produced is visible somewhere on the site.
- **FR-007**: Tab badge counts MUST equal the number of projects in that tab's stage-set.

### Paper-card Dialog (US2)
- **FR-008**: Clicking a card on `Published`, `Paper Pipeline`, or `In Progress` MUST open a modal containing: project title + current_stage badge, an embedded PDF (if any), and a chronological artifact list.
- **FR-009**: The artifact list MUST include, in order: `idea/*.md`, `specs/001-*/spec.md`, `specs/001-*/plan.md`, `specs/001-*/tasks.md`, `code/**`, `data/**`, `paper/specs/001-paper/*.md`, `paper/figures/**`, `paper/source/main.tex`, `paper/pdf/*.pdf`, `reviews/research/**`, `paper/reviews/**`, citations summary, last 10 run-log entries.
- **FR-010**: Each artifact list item MUST be clickable and open the canonical view of that artifact (GitHub blob URL when on the live site; relative file:// when on a local file server).
- **FR-011**: When an artifact does not exist for a project (e.g., paper not yet drafted), the row MUST be omitted (not greyed out) so the list doubles as a stage-progress indicator.

### Authentication (US3)
- **FR-012**: The site MUST support GitHub OAuth login via a Cloudflare Worker proxy that holds the OAuth `client_secret`. The Worker source MUST live in this repo at `infra/oauth-proxy/`.
- **FR-013**: The Worker MUST verify the `state` parameter (CSRF protection) on every callback.
- **FR-014**: After login the user's avatar + login + a "Sign out" affordance MUST be visible in the topbar; the user object MUST be cached in `localStorage` for the session.
- **FR-015**: The Worker URL MUST be configurable via a `<meta name="llmxive-oauth-proxy" content="…">` tag so different deployments (production, staging, fork) can use different Workers without rebuilding the JS.
- **FR-016**: Submission of a new idea (Submit Idea modal) MUST create a GitHub issue with title, body, and labels `idea` plus `brainstormed`. The body MUST include the structured frontmatter the Brainstorm-Agent expects.
- **FR-017**: Submission of a review MUST create a markdown file under the project's `reviews/research/` or `paper/reviews/` directory via the GitHub Contents API, with frontmatter compatible with `ReviewRecord`.
- **FR-018**: Token MUST be requested with scope `public_repo` (sufficient for issues + PR contents on a public repo).

### Local API key storage (US4)
- **FR-019**: The CLI MUST read `DARTMOUTH_CHAT_API_KEY` from, in order: (1) environment variable, (2) `~/.config/llmxive/credentials.toml` on POSIX or `%APPDATA%\llmxive\credentials.toml` on Windows, (3) interactive prompt.
- **FR-020**: When prompting interactively, the CLI MUST use `getpass`-style hidden input and offer to persist the key.
- **FR-021**: When persisting, the file MUST be written with permissions 0600 (POSIX) or have its NTFS ACL restricted to current user (Windows).
- **FR-022**: A new subcommand `python -m llmxive auth {set|show|rotate|clear}` MUST be available for managing the stored key. `show` MUST mask all but the last 4 characters.
- **FR-023**: Preflight MUST refuse to start if the credentials file has world- or group-readable bits set (POSIX), printing a clear remediation hint.

### About page truth (US5)
- **FR-024**: The About tab MUST narrate the actual 34-state lifecycle, the Spec-Kit-per-project model, the 0.5/1.0 review weights, the two separate review gates (research_review and paper_review), and the seven research-Spec-Kit + seven paper-Spec-Kit slash commands.
- **FR-025**: The About page MUST contain machine-readable `data-threshold` spans for both review gates and any other point thresholds (matching the existing test contract).
- **FR-026**: The About page MUST link to the Constitution, the spec, and the agent registry from this repo.

### Aggregates (US6)
- **FR-027**: `web/data/projects.json::aggregates` MUST contain `total_contributions`, `active_projects`, `papers_posted`, `total_contributors`, `human_contributors`, `ai_contributors`, `total_collaborations`, generated by `status_reporter` from `state/run-log/`, `state/projects/`, and `projects/*/reviews/`.
- **FR-028**: The Status-Reporter Agent MUST regenerate `web/data/projects.json` after every successful pipeline cycle.
- **FR-029**: Each project entry in the JSON MUST include `id`, `title`, `field`, `current_stage`, `phase_group`, `points_research_total`, `points_paper_total`, `created_at`, `updated_at`, `keywords`, `speckit_research_dir`, `speckit_paper_dir`, `artifact_links` (a dict from artifact-kind to relative path).

### End-to-end (US7)
- **FR-030**: `python -m llmxive brainstorm <N>` MUST add at least N new ideas to the brainstorm queue (each producing a `BRAINSTORMED` Project record).
- **FR-031**: A repeated `python -m llmxive run --advance --max-cycles K` MUST drive at least one project from BRAINSTORMED to POSTED if K is large enough (≥40 cycles).
- **FR-032**: The end-to-end run MUST be reproducible from a clean working directory using only the credentials file from FR-019.

## Key Entities

- **WebProjectEntry** — projection of `Project` plus aggregated stats and artifact paths used by the website. Lives in `web/data/projects.json`.
- **WebAggregates** — counters block in the same JSON, replacing all hard-coded literals.
- **OAuthProxy** — Cloudflare Worker mapping `/authenticate?code=…&state=…` to a token exchange. Source committed; secrets configured via `wrangler secret`.
- **CredentialsFile** — `credentials.toml` with `dartmouth_chat_api_key` and timestamp.
- **ArtifactDialogModel** — client-side model assembling artifact rows by introspecting a project's `artifact_links` plus a small set of derived rows (citations, run-log).

## Success Criteria

- **SC-001**: With the new site deployed, a first-time visitor can identify the project's current focus (latest POSTED paper or oldest stuck stage) within 30 seconds. (Tested via 5-user readability walkthrough.)
- **SC-002**: 100% of hero counters and tab counts are sourced from disk; no values are hard-coded outside `web/data/projects.json`. (Tested by grep.)
- **SC-003**: 100% of projects whose `current_stage` is non-terminal appear in exactly one tab. (Tested by enumerating Stage values.)
- **SC-004**: Paper-card dialog shows ≥80% of artifact kinds (spec, plan, tasks, code, data, paper PDF, reviews, citations, run-log) for any POSTED project. (Tested via Playwright.)
- **SC-005**: GitHub OAuth round-trip completes in <5 seconds at the 95th percentile. (Tested via Worker timing logs.)
- **SC-006**: Locally, `python -m llmxive run` succeeds on second invocation without any user interaction. (Tested via `tests/integration/test_credentials_persist.py`.)
- **SC-007**: The pipeline produces ≥2 POSTED projects in a single end-to-end local run with N=5 brainstormed ideas. (Tested via `tests/local_e2e/test_run_to_posted.py`.)
- **SC-008**: All Playwright assertions in `tests/e2e/test_site.py` pass against the rendered site. (Tested directly.)
- **SC-009**: The web/about.html `data-threshold` test (`tests/integration/test_about_thresholds.py`) still passes after the redesign.

## Assumptions

- Cloudflare Workers free tier is sufficient (it is, by Stage 3 research finding 1).
- `pdf.js` or browser-native `<embed>` is sufficient for in-modal PDF rendering on Chrome, Firefox, Safari.
- The OAuth `client_id` is public and may be checked into the repo.
- `client_secret` is set via `wrangler secret put` and never committed.
- The maintainer's local clock is in UTC; the website renders ISO timestamps without timezone math.
- GitHub Pages already serves `web/` from the deployed branch.
