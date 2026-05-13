# Feature Specification: llmXive website — UI bug-fixes and polish

**Feature Branch**: `008-website-ui-fixes`
**Spec dir**: `specs/007-website-ui-fixes/`
**Created**: 2026-05-12
**Status**: Draft
**Tracking issue**: #115 ("UI issues and bugs")
**Type**: website bug-fix + polish, plus one new lightweight maintenance agent + an hourly intake cron (for #115 item 8)

## Overview

The public llmXive site (https://context-lab.com/llmXive — a static GitHub Pages app built from `web/`, synced to `docs/`, with data from `web/data/projects.json`) has accumulated a batch of minor-to-moderate UI bugs and missing affordances, tracked in issue #115. This spec collects them into one coordinated fix. It spans three categories:

- **Static-site fixes** (header wordmark, tab indicator, pipeline-diagram modals, agent-registry modal, "How to contribute" section, client-side Markdown rendering in modals).
- **Data-correctness fixes** (Contributors list showing prompt names instead of models, mismatched contribution counts, project modals always defaulting to a PDF).
- **An auth fix** (GitHub sign-out may not actually clear state / can't switch accounts — flagged CRITICAL/SECURITY in #115) and a **docs fix** (the repo README is stale).
- **A human-submission intake path** (a feedback control on any artifact + a paper-submission control; each creates a tagged GitHub issue; a new lightweight maintenance agent run by an hourly cron triages and closes those issues).

Per Constitution Principle I (Single Source of Truth), the website is a *view* over canonical state (`state/`, `agents/registry.yaml`, `projects/`, `papers/`, run-logs). Fixes pull from those sources rather than hand-maintaining duplicate data in the site.

**Scope boundary**: Item 8 of #115 ("any artifact accepts human feedback → triggers AI review + triage") has a front-end half (a feedback control on any artifact / a paper-submission control accepting a link or PDF) and a backend half (the worker that processes those submissions). **Both are in scope here** (the clarification on the recording mechanism — tagged GitHub issues consumed by a new lightweight hourly *maintenance agent* — made the backend small enough to fit). What is genuinely deferred is anything *beyond* the maintenance agent's "turn a submission into a triaged project / route to the right pipeline step" job.

## Clarifications

### Session 2026-05-12

- Q: On mobile (where the tab row may wrap/scroll) how should the active-tab indicator behave? → A: **Same sliding underline as desktop, made correct** — keep the single underline element and recompute its position from the active tab's *actual rendered geometry* on every layout change (click, resize, orientation, font-load); the current bug is stale/wrong geometry, so fixing the math fixes mobile too. (Supersedes the spec's earlier "or an equivalent unambiguous marking" alternative — FR-002.)
- Q: Where should artifact Markdown (idea bodies, specs, plans, agent prompts) be rendered to HTML for the modals? → A: **Client-side, lightweight vendored library** — bundle a small (~10KB) Markdown renderer into `web/js/`, fetch the raw `.md` from the repo (raw.githubusercontent / GitHub API), render on modal-open. No `web_data.py` change for this; the site stays a pure static client; one new vendored JS file. (FR-004, FR-009.)
- Q: How should account-switching after GitHub sign-out be enabled (GitHub won't re-prompt while an active grant exists)? → A: **Revoke the OAuth grant on sign-out** — on sign-out, call GitHub's API (via the Cloudflare OAuth proxy, which holds the client secret) to delete the app's authorization grant, so the next sign-in necessarily re-prompts and a different account can be chosen. **Constraint**: the Cloudflare-Worker proxy MUST continue to support the existing flow; if (and only if) grant-revocation can't be done within the current Cloudflare setup, fall back to forcing GitHub's account-chooser on sign-in (an extra redirect). Sign-out's local-state clear (FR-010) happens regardless, before the revoke call, so a failed revoke still signs the user out locally. (FR-011.)
- Q: How should site-submitted feedback / papers be recorded, and who processes them? → A: **All contributions become specially-tagged GitHub issues** (e.g. label `human-submission` with a sub-type `feedback` / `new-paper`; an uploaded PDF is attached to the issue or staged so the issue references it). A **new lightweight maintenance agent**, run by an **hourly GitHub Action cron**, walks the open tagged issues: for each, it makes LLM calls as needed to decide what the submission is, turns it into a project (or routes it to the appropriate pipeline step, or acknowledges-and-closes if not actionable), moves any attached files to their proper locations, and closes the issue once handled. This **supersedes** the earlier "/speckit-specify" answer (structured file under `feedback/`): the canonical record is the tagged issue; the maintenance agent — not a `feedback/` directory — is the consumer. The maintenance agent IS in scope here (FR-020/FR-021); only work *beyond* its bounded triage job is deferred. (FR-012..FR-015, FR-020, FR-021.)
- Q: What should the user see in the modal after a successful submission (new PDF, new comment, feedback, …)? → A: **A confirmation message that a new GitHub issue has been created, with a clickable link to it, and that the contribution will be processed within the next hour** (matching the hourly intake cron). (FR-013b, SC-011.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — A visitor reads a clean, correctly-rendered dashboard (Priority: P1)

A first-time visitor lands on the site. The header shows the project name as one word in its box. They click between tabs (on desktop and on mobile); the active-tab indicator stays correctly aligned under the active tab, including after resizing the window. They open the Contributors tab and see a ranked list of the **models** that have contributed (Qwen3.5-122B, Gemma-3-27B, …) and human collaborators — not agent/prompt names. The contribution counts shown match the actual number of artifacts those contributors produced.

**Why this priority**: This is the site's front door — the bugs here (split wordmark, broken tab indicator, wrong contributor names, wrong counts) are the most visible and the most damaging to credibility, and they're all low-risk fixes.

**Independent Test**: Load the site on desktop and a mobile-width viewport; verify the wordmark renders as one word; click each tab and resize the window, checking the indicator tracks the active tab in every state; open Contributors and verify (i) every listed AI contributor is a model name, not a prompt/agent name, and (ii) at least one contributor's displayed count matches an independently-derived count of that contributor's artifacts.

**Acceptance Scenarios**:

1. **Given** the site loaded at any viewport width, **When** the header renders, **Then** the project wordmark appears as a single unbroken token inside its box (no visible split into "llm" + "Xive").
2. **Given** the site on a desktop viewport, **When** the user clicks a tab, **Then** the active-tab indicator is positioned under exactly that tab; **And** when the window is resized, the indicator re-aligns to the (still-)active tab; **And** the same alignment behavior holds at mobile widths (the indicator is visible and correctly placed, or — if the mobile layout doesn't use an underline indicator — the active tab is unambiguously marked some other way).
3. **Given** the Contributors tab, **When** it renders, **Then** every AI-attributed row names a model (from the model attribution recorded in run-logs / project state), not a prompt name (e.g. "brainstorm", "flesh_out"); **And** human contributors are unchanged.
4. **Given** the Contributors tab, **When** a contributor's contribution count is displayed, **Then** it equals the count of distinct artifacts that contributor produced as recorded in canonical state (no double-counting, no phantom counts).

---

### User Story 2 — A visitor inspects a project's actual current artifact (Priority: P1)

A visitor opens a project from any tab. If the project has a published PDF, the modal shows the PDF. If it doesn't yet (e.g. an in-progress research project, or one only at the brainstormed/spec/plan stage), the modal shows *that project's current artifact* — the brainstormed idea, the research spec, the plan, the in-progress write-up, etc. — rendered appropriately (Markdown rendered as Markdown, LaTeX source shown as source, etc.), using the modal space effectively rather than showing an empty or broken PDF embed.

**Why this priority**: Most projects don't have a PDF yet; the current always-default-to-PDF behavior means most project modals are useless. Fixing this makes the dashboard genuinely browsable.

**Independent Test**: Open a project that has a PDF → the PDF renders. Open a project at the brainstormed stage → the idea Markdown renders. Open an in-progress research project → its current artifact renders. In no case is a broken/empty PDF embed shown.

**Acceptance Scenarios**:

1. **Given** a project with a published PDF, **When** the user opens its modal, **Then** the PDF is displayed.
2. **Given** a project without a PDF, **When** the user opens its modal, **Then** the project's current-stage artifact is displayed, rendered in a form appropriate to its type, occupying the space the PDF embed would have used.
3. **Given** a project whose current artifact is Markdown, **When** the modal opens, **Then** the Markdown is rendered (headings, links, lists), not shown as raw text.
4. **Given** a project with neither a PDF nor a renderable artifact yet, **When** the modal opens, **Then** the user sees a clear "no artifact yet — here's where it'll appear" placeholder plus the project's metadata and links — never a broken embed.

---

### User Story 3 — GitHub sign-out actually signs the user out (Priority: P1, CRITICAL/SECURITY)

A signed-in visitor clicks "sign out". Their session is fully cleared — the stored GitHub token and user are removed, the UI reflects the signed-out state, and they can immediately sign in again as a *different* GitHub user without stale state interfering.

**Why this priority**: #115 flags this CRITICAL/SECURITY: if sign-out doesn't actually clear the token, a shared-device user's GitHub credentials persist, and the inability to re-sign-in as a different user is a concrete symptom that something is broken. This must be triaged first.

**Independent Test**: Sign in as user A; click sign out; verify the stored token + user are gone (no `llmxive_gh_token` / user in browser storage) and the UI shows signed-out; then start the OAuth flow again and sign in as user B; verify the UI shows user B (not user A, not an error, not a no-op).

**Acceptance Scenarios**:

1. **Given** a signed-in session, **When** the user clicks sign out, **Then** all client-side auth state (token, user record, any in-flight OAuth state) is removed and the UI shows the signed-out state — unconditionally, before/independent of the grant-revocation step.
2. **Given** sign-out, **When** it runs, **Then** the app's GitHub OAuth authorization grant is revoked via the Cloudflare OAuth proxy; **And** if revocation fails, the user is still signed out locally and a non-blocking warning is shown.
3. **Given** the user has just signed out, **When** they initiate the GitHub OAuth flow again, **Then** GitHub re-prompts (because the grant was revoked — or, in the documented fallback, because the account-chooser is forced) and the user can sign in as a *different* account; the UI then shows the newly-signed-in account.
4. **Given** sign-out, **When** the page is reloaded, **Then** the user is still signed out (no resurrection of the prior session from storage).

---

### User Story 4 — A visitor explores the pipeline and the agent registry in-place (Priority: P2)

On the About page, a visitor clicks a circle in the pipeline diagram. A modal opens describing what that step does (its inputs and outputs), linking to a few recent example artifacts produced by that step, and listing the agents that step uses — each agent name clickable to view that agent's prompt. Separately, the visitor clicks "agent registry"; a modal opens rendering the list of agents (with a link to view `agents/registry.yaml` on GitHub); clicking an agent shows that agent's prompt and tools rendered in the modal, with a link to view the prompt source on GitHub.

**Why this priority**: These are net-new affordances (not bug fixes) that make the system legible to outside readers; valuable but not blocking the front-door cleanup.

**Independent Test**: On About, click each pipeline-diagram circle → a modal opens with a step description (inputs/outputs), ≥1 example-artifact link, and the step's agent list with each agent linking to a viewable prompt. Click "agent registry" → a modal lists all agents with a GitHub link to the registry; click an agent → its prompt + tools render in the modal with a GitHub link to the source.

**Acceptance Scenarios**:

1. **Given** the About page, **When** the user clicks a pipeline-diagram circle, **Then** a modal opens with (a) a description of that step including its inputs and outputs, (b) links to recent example artifacts from that step, (c) the list of agents that step uses, each linking to a viewable rendering of that agent's prompt.
2. **Given** the "agent registry" entry point, **When** the user clicks it, **Then** a modal opens rendering the agent list, with a link to `agents/registry.yaml` on GitHub.
3. **Given** the agent-registry modal, **When** the user clicks an agent, **Then** that agent's prompt and tools are rendered in the modal, with a link to view the prompt source on GitHub.

---

### User Story 5 — A visitor gives feedback on any artifact, or submits a paper, and an hourly cron triages it (Priority: P2)

A visitor viewing any artifact (not just a brainstormed idea — an in-progress research project, a spec, a plan, a paper, anything) finds a control to submit human feedback on it. They can also submit a new paper for consideration/review by providing a link or uploading a PDF. The submission becomes a specially-tagged GitHub issue; the visitor gets a confirmation linking to that issue. Within the hour, a maintenance-agent cron picks up the issue, decides what it is, acts on it (routes the feedback to the right pipeline step / project, or creates a project, or — for a paper — creates/links the relevant project/review entry and files the attachment, or acknowledges if not actionable), comments on the issue saying what it did, and closes it.

**Why this priority**: Broadens human participation. The front-end (P2 within this spec) plus a small backend maintenance agent + its cron — both in scope, but they don't block the front-door cleanup (US1–US3).

**Independent Test**: On any artifact (idea / spec / plan / in-progress research / paper) there is a "give feedback" control; submitting it creates a `human-submission`+`feedback` GitHub issue with full context and shows a confirmation with the issue link. There is a "submit a paper" control accepting a URL or a PDF upload; submitting it creates a `human-submission`+`new-paper` issue with the link/PDF. Running the maintenance-agent cron over the open tagged issues: each is acted on, gets an explanatory comment, and is closed (or, if unprocessable, stays open with an explanatory comment and the run still succeeds).

**Acceptance Scenarios**:

1. **Given** any artifact view (idea, spec, plan, in-progress research, paper, review), **When** the user opens it, **Then** a "submit feedback" affordance is present.
2. **Given** the feedback affordance, **When** the user submits feedback, **Then** a GitHub issue tagged `human-submission` + `feedback` is created (via the user's GitHub credentials) carrying the target artifact/project id, its current stage, the submitter, and the content; **And** the user sees a confirmation linking to the created issue; **And** a failed creation surfaces an error and preserves the user's input.
3. **Given** the site, **When** the user chooses "submit a paper", **Then** they can supply either a URL or a PDF upload, and a GitHub issue tagged `human-submission` + `new-paper` is created with the URL inline or the PDF attached/referenced.
4. **Given** an open `human-submission` issue, **When** the maintenance-agent cron runs, **Then** the agent triages it (routes / creates a project / files a paper / acknowledges), moves any attached files to canonical locations, posts a comment describing what it did, and closes the issue.
5. **Given** a `human-submission` issue the agent cannot process, **When** the cron runs, **Then** the issue is left open with an explanatory comment and the run completes without failing (other submissions still get processed).

---

### User Story 6 — A visitor reads an accurate "How to contribute" section and an up-to-date README (Priority: P2)

On the About page there is a "How to contribute" section explaining the four ways to participate: add ideas, help with development, provide feedback, review existing content — each with a concrete pointer (where to click on the site / which repo area). The repo's top-level README is current: it reflects the actual pipeline, agent count, the website, and the spec-driven workflow as they are today.

**Why this priority**: Documentation/onboarding; low-risk, high-value-for-newcomers.

**Independent Test**: On About, a "How to contribute" section lists the four contribution modes with actionable pointers. The README, read end-to-end, contains no statements contradicted by the current repo state (no stale agent counts, no removed features described as present, no missing major features like the website).

**Acceptance Scenarios**:

1. **Given** the About page, **When** it renders, **Then** a "How to contribute" section is present listing: add ideas, help with development, provide feedback, review existing content — each with a usable pointer.
2. **Given** the repo README, **When** read, **Then** every factual claim about the current system (pipeline stages, agent registry, the public site, the spec workflow) matches the repo's current state.

---

### Edge Cases

- **A model attribution is missing/ambiguous in run-logs** for some old artifact → the Contributors list falls back to a clearly-labelled "unattributed" bucket rather than silently showing a prompt name or dropping the contribution.
- **A project has an artifact type the site doesn't yet know how to render** → the modal shows a download/view-on-GitHub link for that artifact plus the metadata, never a broken embed.
- **The OAuth proxy is down / grant-revocation fails** when the user signs out → sign-out's local-state clear still succeeds (it's independent of the proxy); a non-blocking warning is shown; the documented fallback (force the account-chooser on the next sign-in) still gives account-switching.
- **The Cloudflare-Worker proxy can't implement grant-revocation** within its current setup → the spec's documented fallback applies (force GitHub's account-chooser on sign-in); FR-011 is satisfied by either path.
- **The user opens a pipeline-diagram circle for a step that has no example artifacts yet** → the modal shows the step description + agent list and a "no examples yet" note for the examples section.
- **A submission's GitHub-issue creation fails** (network / auth / rate-limit) → the user sees an error and the form preserves their input for retry; nothing is silently dropped.
- **The maintenance agent can't decide what a submission is, or an LLM call fails** → it leaves the issue open with an explanatory comment; the cron run still completes and processes the other submissions.
- **Two cron runs overlap (or a submission is partly processed)** → the workflow is idempotent — an already-handled-and-closed issue is skipped; a partly-processed one is re-attempted from a safe point or left open with a note.
- **Mobile**: every modal introduced or modified here is usable at mobile widths (scrollable, dismissible, not clipped).
- **Items 1, 2, 6 (sign-out)** must not regress when the underlying `web/data/projects.json` is regenerated by the pipeline crons (these are static-markup / auth-logic fixes, independent of the data payload).

## Requirements *(mandatory)*

### Functional Requirements

**Static-site fixes**
- **FR-001**: The header wordmark MUST render the project name as a single unbroken token within its box at all viewport widths (fixes #115 item 1).
- **FR-002**: The active-tab indicator MUST be a single sliding-underline element whose position is computed from the active tab's actual rendered geometry, recomputed on every layout-changing event (tab click, window resize, orientation change, web-font load); it MUST be correctly aligned under the active tab on desktop AND at mobile widths (fixes #115 item 2).
- **FR-003**: Clicking a circle in the About-page pipeline diagram MUST open a modal containing: (a) a description of that step including its inputs and outputs; (b) links to recent example artifacts produced by that step; (c) the list of agents that step uses, each linking to a viewable rendering of that agent's prompt (fixes #115 item 7).
- **FR-004**: An "agent registry" entry point MUST open a modal that renders the agent list (with a link to `agents/registry.yaml` on GitHub); clicking an agent in that modal MUST render that agent's prompt (Markdown rendered client-side via the vendored renderer — see FR-009b) and tools, with a link to the prompt source on GitHub (fixes #115 item 9).
- **FR-005**: The About page MUST include a "How to contribute" section listing the four contribution modes (add ideas, help with development, provide feedback, review existing content), each with an actionable pointer (fixes #115 item 10).
- **FR-006**: The pipeline-diagram-step content (FR-003) and agent-registry content (FR-004) MUST be derived from canonical sources (`agents/registry.yaml`, the pipeline-stage definitions, run-logs / `web/data/projects.json` for example artifacts) — not hand-maintained duplicates in the site (Constitution Principle I).

**Data-correctness fixes**
- **FR-007**: The Contributors list MUST attribute AI contributions to the **model** that produced them (as recorded in run-log / project-state model attribution), not to a prompt/agent name; contributions whose model is unknown MUST be shown in a clearly-labelled "unattributed" bucket, not under a prompt name (fixes #115 item 3).
- **FR-008**: Each contributor's displayed contribution count MUST equal the count of distinct artifacts that contributor produced as recorded in canonical state — no double-counting, no phantom entries (fixes #115 item 4). The `web_data` builder is the place this is fixed (the site reads it).
- **FR-009**: A project modal MUST display the project's PDF if one exists; otherwise it MUST display the project's current-stage artifact rendered in a form appropriate to its type (Markdown rendered as HTML, LaTeX shown as source, JSON/YAML shown formatted, etc.), using the space the PDF embed would have used; if no renderable artifact exists yet, it MUST show a clear placeholder plus metadata and a view-on-GitHub link — never a broken/empty embed (fixes #115 item 5).
- **FR-009b**: Markdown rendering anywhere on the site (project-modal Markdown artifacts per FR-009, agent prompts per FR-004, pipeline-step descriptions per FR-003 if Markdown) MUST be done client-side by a single small vendored Markdown→HTML library bundled into `web/js/`; the raw `.md` is fetched from the repo at modal-open time (no `web_data.py` change required for rendering; no heavyweight build-time dependency).

**Auth fix (CRITICAL/SECURITY)**
- **FR-010**: Clicking "sign out" MUST remove all client-side authentication state (the stored GitHub token, the stored user record, any in-flight OAuth `state`) and update the UI to the signed-out state; this local-state clear MUST happen unconditionally (before, and independent of, the grant-revocation in FR-011); after sign-out, a page reload MUST keep the user signed out (fixes #115 item 6).
- **FR-011**: On sign-out, the system MUST revoke the GitHub OAuth authorization grant for the app (via the existing Cloudflare-Worker OAuth proxy, which holds the client secret — a call to GitHub's grant-revocation API), so that a subsequent sign-in necessarily re-prompts at GitHub and the user can choose a *different* account. The Cloudflare-Worker proxy MUST continue to support the existing OAuth flow; **if grant-revocation cannot be implemented within the current Cloudflare setup, the fallback is** to force GitHub's account-chooser on sign-in instead (one extra redirect). A failed revocation MUST NOT block sign-out (the user is still signed out locally per FR-010) but SHOULD surface a non-blocking warning (fixes #115 item 6).

**Human-submission front-end + intake (item 8)**
- **FR-012**: Every artifact view on the site (idea, research spec, plan, in-progress research, paper, review — not only brainstormed ideas) MUST present a "submit feedback" affordance (fixes #115 item 8).
- **FR-013**: Submitting feedback MUST create a GitHub issue tagged with a canonical label (e.g. `human-submission`) and a sub-type (`feedback`), via the signed-in user's GitHub credentials, carrying enough context (target artifact/project id, the artifact's current stage, who submitted, the feedback content) for the maintenance agent (FR-020) to triage it.
- **FR-013b**: On a successful submission (FR-013, FR-014, and any other artifact-submission path — a new PDF, a comment, feedback), the modal MUST display a message stating that a new GitHub issue has been created — including a clickable link to that issue — and that the contribution will be processed within the next hour (matching the FR-021 cron cadence). On a failed creation the modal MUST surface an error and preserve the user's input for retry.
- **FR-014**: The site MUST provide a "submit a paper for consideration/review" affordance accepting either a URL or a PDF upload; the submission MUST create a GitHub issue tagged `human-submission` + `new-paper`, with the URL recorded inline or the uploaded PDF attached to (or staged and referenced by) the issue, carrying enough context for the maintenance agent to triage it; the FR-013b confirmation message applies.
- **FR-015**: The canonical record of a human submission is the tagged GitHub issue. The site MUST NOT need to commit any repo files for a submission — the maintenance agent (FR-020) is responsible for moving any attached files into their proper locations and creating/updating projects.

**Maintenance agent + intake cron (item 8 backend)**
- **FR-020**: There MUST be a new lightweight **maintenance agent** that, given an open `human-submission`-tagged GitHub issue, decides what the submission is (using LLM calls as needed), and: for a `feedback` submission — routes it to the appropriate pipeline step / project (or, if it concerns no existing artifact and warrants a new line of work, creates a project; or, if not actionable, posts an acknowledgement); for a `new-paper` submission — creates (or links) the relevant project/review entry and moves any attached PDF/URL into the canonical location; in all cases it posts a brief comment on the issue describing what it did and closes the issue. The agent MUST be added to `agents/registry.yaml` with its prompt under `agents/prompts/`.
- **FR-021**: A GitHub Action cron MUST run hourly, enumerate the open `human-submission`-tagged issues, and invoke the maintenance agent on each; the workflow MUST be idempotent (an issue the agent has already handled and closed is skipped) and MUST not fail the run if a single submission can't be processed (it leaves that issue open with an explanatory comment and continues).

**Docs fix**
- **FR-016**: The repo's top-level README MUST be updated so every factual claim about the current system (pipeline stages, agent registry/count, the public website, the spec-driven workflow) matches the repo's current state (fixes #115 item 11, and the #115 comment).

**Cross-cutting**
- **FR-017**: All new/modified modals MUST be usable at mobile widths (scrollable, dismissible, not clipped).
- **FR-018**: After all fixes, the site MUST be re-synced from `web/` to `docs/` (the GitHub Pages source) so the deployed site reflects the changes; the deploy MUST not break the existing build/sync workflow.
- **FR-019**: None of these fixes may regress when `web/data/projects.json` is regenerated by the pipeline crons (the static-markup, auth, and modal-rendering fixes are independent of the data payload's churn).

### Key Entities *(include if feature involves data)*

- **Contributor (display row)**: name, kind (human | model | unattributed), contribution count, areas. AI rows are keyed by **model identifier**, derived from run-log/project-state model attribution — not by prompt name. Built in `web_data`.
- **Project modal artifact**: the artifact a project modal should display — resolved as: published PDF if present, else the current-stage artifact (idea Markdown / research spec / plan / in-progress write-up / LaTeX source / …), else a "no artifact yet" placeholder. Each carries a type tag the renderer switches on.
- **Pipeline-step descriptor**: for the About-page diagram — { step name, description, inputs, outputs, agents-used (each with a prompt-file pointer), recent-example-artifact links }. Derived from the pipeline-stage definitions + `agents/registry.yaml` + recent artifacts.
- **Agent (registry view)**: { name, purpose, prompt path (→ GitHub link + rendered content), tools, default backend/model }. Derived from `agents/registry.yaml` + the prompt `.md` files.
- **Human submission**: a GitHub issue tagged `human-submission` + a sub-type label (`feedback` | `new-paper`), created via the signed-in user's GitHub credentials. Body carries: target artifact/project id (for `feedback`), target artifact stage, submitter (GitHub user), the content; for `new-paper`, a URL inline or an attached/referenced PDF. The maintenance agent reads, acts on, comments on, and closes it. (The tagged issue — not any repo file — is the canonical record.)
- **Maintenance agent**: a new lightweight agent in `agents/registry.yaml` (prompt under `agents/prompts/`) that triages one `human-submission` issue: routes feedback to the right pipeline step / project, or creates a project, or — for a paper — creates/links a project/review entry and files the attachment, or acknowledges if not actionable; then comments + closes. Uses LLM calls as needed (default backend/model per the registry pattern).
- **Intake cron**: an hourly GitHub Action that enumerates open `human-submission` issues and invokes the maintenance agent on each; idempotent; tolerant of per-submission failures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On every viewport from mobile (~360px) to wide desktop, the header wordmark is one unbroken token (0 occurrences of a visible "llm" / "Xive" split).
- **SC-002**: For each of {desktop, mobile} × {click each tab, resize after clicking}, the active-tab indicator is correctly aligned to the active tab (or the active tab is unambiguously marked) — 0 misalignment cases.
- **SC-003**: 100% of AI-attributed Contributors rows name a model (or sit in the "unattributed" bucket); 0 rows name a prompt/agent.
- **SC-004**: For every contributor, displayed count == independently-derived artifact count from canonical state — 0 mismatches.
- **SC-005**: For every project, opening its modal shows either its PDF (if it has one) or its current-stage artifact rendered appropriately or a clear placeholder — 0 broken/empty PDF embeds across all projects.
- **SC-006**: Sign-out clears all client auth state (verified: no `llmxive_gh_token` / user / OAuth-state in browser storage post-sign-out) and survives reload — passes in 100% of test runs; the OAuth grant is revoked (or, in the fallback, the account-chooser is forced).
- **SC-007**: After sign-out, the OAuth flow can be completed to sign in as a different GitHub user — passes in 100% of test runs.
- **SC-008**: Every pipeline-diagram circle opens a modal with a step description (incl. inputs/outputs), ≥1 example-artifact link (or a "no examples yet" note for steps with none), and the step's agent list with every agent linking to a viewable prompt — true for 100% of circles.
- **SC-009**: The agent-registry modal lists 100% of agents in `agents/registry.yaml` (including the new maintenance agent); clicking any agent renders its prompt + tools with a GitHub source link — true for 100% of agents.
- **SC-010**: The About page has a "How to contribute" section covering all four contribution modes with actionable pointers.
- **SC-011**: 100% of artifact views on the site present a "submit feedback" affordance; a "submit a paper" affordance exists accepting URL or PDF; a submitted feedback/paper creates a `human-submission`-tagged GitHub issue with full context; **and the modal then shows a message stating that a new issue was created (with a clickable link to it) and that the contribution will be processed within the next hour** — verified for ≥1 submission of each type.
- **SC-012**: Running the maintenance-agent cron over the open `human-submission` issues: every processable issue is acted on, commented on, and closed; unprocessable ones stay open with a comment and the run still succeeds — 100%.
- **SC-013**: The README contains 0 factual claims contradicted by the current repo state (verified by review against the live repo).
- **SC-014**: All new/modified modals are usable at mobile widths — 0 clipped/undismissable cases.
- **SC-015**: After the fixes, `docs/` matches `web/` (the deploy sync ran) and the GitHub Pages build succeeds.
- **SC-016**: The pipeline-cron regeneration of `web/data/projects.json` does not reintroduce any of these bugs — verified by re-running the relevant checks after a cron tick (or a simulated regeneration).

## Assumptions

- The site is a static GitHub Pages app: markup in `web/index.html`, styles in `web/css/*.css`, behavior in `web/js/*.js` (vanilla JS), data in `web/data/projects.json` (built by `src/llmxive/web_data.py`), and `web/` is synced to `docs/` for deployment. Fixes touch these files; the data-correctness fixes (FR-007, FR-008) are made in `web_data.py` so the site just renders correct data.
- GitHub auth uses an OAuth flow with the token in browser `localStorage` (`llmxive_gh_token`) and exchange via the existing Cloudflare-Worker OAuth proxy (`simple-oauth-proxy`), which holds the client secret. FR-010 is a client-side fix to `web/js/auth.js` (clear all auth state). FR-011's grant-revocation needs the proxy to expose a "revoke grant" endpoint (the proxy calls GitHub's grant-revocation API with the client secret); the proxy MUST keep working for the existing flow. If grant-revocation can't be added to the current Cloudflare setup, the fallback (force the account-chooser on sign-in) is purely client-side. Either path is a small adjunct, not a separate spec.
- "Recent example artifacts" for a pipeline step (FR-003) are sourced from the existing project/run-log data already in `web/data/projects.json` (or a small extension of it) — no new crawl.
- The maintenance agent (FR-020) follows the existing agent pattern (`agents/registry.yaml` entry + `agents/prompts/<name>.md` + the backend router for LLM calls). It is *not* a pipeline-stage agent (it doesn't own a project stage); it's invoked by the intake cron (FR-021), similar in spirit to the librarian being tool-style. Its scope is bounded to "triage one `human-submission` issue and act on it" — no broader pipeline changes.
- The intake cron (FR-021) is a new GitHub Action workflow (hourly schedule), alongside the existing pipeline crons; it uses the repo's GitHub token to list/comment/close issues and to commit any file moves the maintenance agent decides on.
- Markdown rendering on the site (FR-009b) uses a single small vendored client-side library (~10KB), bundled into `web/js/`; the raw `.md` is fetched from the repo at modal-open. No `web_data.py` change for rendering; no heavyweight build-time dependency.
- The four pipeline-diagram steps / lanes already exist on the About page; FR-003 makes the existing circles interactive, it doesn't redesign the diagram.

## Out of Scope

- Anything the maintenance agent does *beyond* "triage one `human-submission` issue → route / create a project / file a paper / acknowledge → comment → close" — e.g. running the downstream pipeline steps itself, a richer feedback-conversation UI, multi-round human↔agent dialogue on a submission. (The maintenance agent itself IS in scope; its job is bounded.)
- Any redesign of the dashboard layout, tab set, or visual theme beyond the specific fixes listed.
- Hosting/CDN/DNS changes for context-lab.com (beyond the Cloudflare-Worker proxy's "revoke grant" endpoint addition, which is in scope as an FR-011 adjunct).
- Changes to the data pipeline itself beyond the `web_data.py` contributor-attribution / count fixes (FR-007, FR-008).
- Authentication providers other than GitHub.
