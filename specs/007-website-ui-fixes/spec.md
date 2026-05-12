# Feature Specification: llmXive website — UI bug-fixes and polish

**Feature Branch**: `008-website-ui-fixes`
**Spec dir**: `specs/007-website-ui-fixes/`
**Created**: 2026-05-12
**Status**: Draft
**Tracking issue**: #115 ("UI issues and bugs")
**Type**: website bug-fix + polish (no new agent)

## Overview

The public llmXive site (https://context-lab.com/llmXive — a static GitHub Pages app built from `web/`, synced to `docs/`, with data from `web/data/projects.json`) has accumulated a batch of minor-to-moderate UI bugs and missing affordances, tracked in issue #115. This spec collects them into one coordinated fix. It spans three categories:

- **Static-site fixes** (header wordmark, tab indicator, pipeline-diagram modals, agent-registry modal, "How to contribute" section).
- **Data-correctness fixes** (Contributors list showing prompt names instead of models, mismatched contribution counts, project modals always defaulting to a PDF).
- **An auth fix** (GitHub sign-out may not actually clear state — flagged CRITICAL/SECURITY in #115) and a **docs fix** (the repo README is stale).

Per Constitution Principle I (Single Source of Truth), the website is a *view* over canonical state (`state/`, `agents/registry.yaml`, `projects/`, `papers/`, run-logs). Fixes pull from those sources rather than hand-maintaining duplicate data in the site.

**Scope boundary**: Item 8 of #115 ("any artifact accepts human feedback → triggers AI review + triage") has two halves — (a) the *front-end* affordance (a feedback control on any artifact / a paper-submission control accepting a link or PDF, which records the submission as a structured file in the repo) and (b) the *backend AI-review-and-triage worker* that processes those submissions. Half (a) is in scope here; half (b) is a separate follow-up spec.

## Clarifications

### Session 2026-05-12

- Q: How should site-submitted feedback / paper submissions (FR-013, FR-014) be recorded so a future triage worker can consume them? → A: As a **structured tracked file in the repo** — committed under a `feedback/` directory via the signed-in user's GitHub credentials (not a GitHub issue/comment). Keeps the issue tracker uncluttered and gives the future triage worker a clean machine-readable input. (Exact path layout / file format is a `/speckit-plan` detail.)

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

1. **Given** a signed-in session, **When** the user clicks sign out, **Then** all client-side auth state (token, user record, any in-flight OAuth state) is removed and the UI shows the signed-out state.
2. **Given** the user has just signed out, **When** they initiate the GitHub OAuth flow again, **Then** the flow completes (the GitHub authorization step is reached — not silently skipped using a cached grant in a way that prevents account switching) and the UI shows the newly-signed-in account.
3. **Given** sign-out, **When** the page is reloaded, **Then** the user is still signed out (no resurrection of the prior session from storage).

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

### User Story 5 — A visitor gives feedback on any artifact, or submits a paper (Priority: P2)

A visitor viewing any artifact (not just a brainstormed idea — an in-progress research project, a spec, a plan, a paper, anything) finds a control to submit human feedback on it. They can also submit a new paper for consideration/review by providing a link or uploading a PDF. The submission is recorded so the system can act on it; the visitor gets confirmation. *(The downstream AI-review-and-triage of the submission is a separate follow-up spec — see Scope boundary above.)*

**Why this priority**: Broadens human participation; depends on (5a) only — the front-end + the recording mechanism — within this spec.

**Independent Test**: On any artifact (idea / spec / plan / in-progress research / paper) there is a "give feedback" control; submitting it records the feedback to the repo (e.g. as an issue comment or a tracked file) and shows a confirmation. There is a "submit a paper" control that accepts a URL or a PDF upload and records the submission. No artifact type is missing the feedback control.

**Acceptance Scenarios**:

1. **Given** any artifact view (idea, spec, plan, in-progress research, paper, review), **When** the user opens it, **Then** a "submit feedback" affordance is present.
2. **Given** the feedback affordance, **When** the user submits feedback, **Then** the feedback is recorded against that artifact in the canonical repo (issue/comment/file — decided at /speckit-plan) and the user receives a confirmation.
3. **Given** the site, **When** the user chooses "submit a paper", **Then** they can supply either a URL or a PDF upload, and the submission is recorded for consideration.
4. **Given** a recorded feedback or paper submission, **Then** it carries enough context (which artifact / project, who submitted, the content) for a downstream triage step to act on it.

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
- **The OAuth proxy is down** when the user tries to sign in after signing out → a clear error is shown; sign-out itself still succeeds (it's a pure local-state clear, independent of the proxy).
- **The user opens a pipeline-diagram circle for a step that has no example artifacts yet** → the modal shows the step description + agent list and a "no examples yet" note for the examples section.
- **A feedback submission fails to record** (network / auth) → the user sees an error and the form preserves their input for retry; nothing is silently dropped.
- **Mobile**: every modal introduced or modified here is usable at mobile widths (scrollable, dismissible, not clipped).
- **Items 1, 2, 6 (sign-out)** must not regress when the underlying `web/data/projects.json` is regenerated by the pipeline crons (these are static-markup / auth-logic fixes, independent of the data payload).

## Requirements *(mandatory)*

### Functional Requirements

**Static-site fixes**
- **FR-001**: The header wordmark MUST render the project name as a single unbroken token within its box at all viewport widths (fixes #115 item 1).
- **FR-002**: The active-tab indicator MUST be positioned under the active tab; MUST re-align to the active tab on window resize; and MUST behave correctly at mobile widths (either a correctly-placed indicator or an equivalent unambiguous active-tab marking) (fixes #115 item 2).
- **FR-003**: Clicking a circle in the About-page pipeline diagram MUST open a modal containing: (a) a description of that step including its inputs and outputs; (b) links to recent example artifacts produced by that step; (c) the list of agents that step uses, each linking to a viewable rendering of that agent's prompt (fixes #115 item 7).
- **FR-004**: An "agent registry" entry point MUST open a modal that renders the agent list (with a link to `agents/registry.yaml` on GitHub); clicking an agent in that modal MUST render that agent's prompt and tools, with a link to the prompt source on GitHub (fixes #115 item 9).
- **FR-005**: The About page MUST include a "How to contribute" section listing the four contribution modes (add ideas, help with development, provide feedback, review existing content), each with an actionable pointer (fixes #115 item 10).
- **FR-006**: The pipeline-diagram-step content (FR-003) and agent-registry content (FR-004) MUST be derived from canonical sources (`agents/registry.yaml`, the pipeline-stage definitions, run-logs / `web/data/projects.json` for example artifacts) — not hand-maintained duplicates in the site (Constitution Principle I).

**Data-correctness fixes**
- **FR-007**: The Contributors list MUST attribute AI contributions to the **model** that produced them (as recorded in run-log / project-state model attribution), not to a prompt/agent name; contributions whose model is unknown MUST be shown in a clearly-labelled "unattributed" bucket, not under a prompt name (fixes #115 item 3).
- **FR-008**: Each contributor's displayed contribution count MUST equal the count of distinct artifacts that contributor produced as recorded in canonical state — no double-counting, no phantom entries (fixes #115 item 4). The `web_data` builder is the place this is fixed (the site reads it).
- **FR-009**: A project modal MUST display the project's PDF if one exists; otherwise it MUST display the project's current-stage artifact rendered in a form appropriate to its type (Markdown rendered as Markdown, LaTeX shown as source, etc.), using the space the PDF embed would have used; if no renderable artifact exists yet, it MUST show a clear placeholder plus metadata and a view-on-GitHub link — never a broken/empty embed (fixes #115 item 5).

**Auth fix (CRITICAL/SECURITY)**
- **FR-010**: Clicking "sign out" MUST remove all client-side authentication state (the stored GitHub token, the stored user record, any in-flight OAuth `state`) and update the UI to the signed-out state; after sign-out, a page reload MUST keep the user signed out (fixes #115 item 6).
- **FR-011**: After signing out, initiating the GitHub OAuth flow again MUST allow signing in as a *different* GitHub user (the flow reaches GitHub's authorization step rather than silently completing from a cached grant in a way that prevents account switching) (fixes #115 item 6).

**Feedback / submission front-end (item 8a)**
- **FR-012**: Every artifact view on the site (idea, research spec, plan, in-progress research, paper, review — not only brainstormed ideas) MUST present a "submit feedback" affordance (fixes #115 item 8, front-end half).
- **FR-013**: Submitting feedback MUST record it as a structured file committed to the canonical repo (a `feedback/` directory — e.g. `feedback/<project-or-artifact-id>/<ISO-timestamp>.yaml`, layout decided at `/speckit-plan`) via the signed-in user's GitHub credentials, carrying enough context (which artifact/project, who submitted, the content, the artifact's current stage) for a downstream triage step to process it; the site MUST show the user a confirmation on success; a failed commit MUST surface an error and preserve the user's input for retry.
- **FR-014**: The site MUST provide a "submit a paper for consideration/review" affordance accepting either a URL or a PDF upload; the submission MUST be recorded as a structured file in the same `feedback/` (or a parallel `submissions/`) directory — with the URL recorded inline, or the uploaded PDF committed alongside the descriptor — carrying enough context for downstream triage.
- **FR-015**: This spec implements the front-end + recording half of #115 item 8 only. The backend AI-review-and-triage worker that processes recorded feedback/paper submissions and routes them to the appropriate pipeline step is explicitly out of scope and tracked as a follow-up spec (see Assumptions).

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
- **Feedback submission**: { target artifact/project id, target artifact stage, submitter (GitHub user), content, timestamp, kind: artifact-feedback | new-paper (URL or uploaded-PDF path) }. Recorded as a structured file (YAML/JSON) committed under `feedback/` in the canonical repo via the signed-in user's GitHub credentials (exact path layout decided at /speckit-plan); for an uploaded PDF, the PDF is committed alongside the descriptor. This is the input the future AI-review-and-triage worker (separate spec) consumes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On every viewport from mobile (~360px) to wide desktop, the header wordmark is one unbroken token (0 occurrences of a visible "llm" / "Xive" split).
- **SC-002**: For each of {desktop, mobile} × {click each tab, resize after clicking}, the active-tab indicator is correctly aligned to the active tab (or the active tab is unambiguously marked) — 0 misalignment cases.
- **SC-003**: 100% of AI-attributed Contributors rows name a model (or sit in the "unattributed" bucket); 0 rows name a prompt/agent.
- **SC-004**: For every contributor, displayed count == independently-derived artifact count from canonical state — 0 mismatches.
- **SC-005**: For every project, opening its modal shows either its PDF (if it has one) or its current-stage artifact rendered appropriately or a clear placeholder — 0 broken/empty PDF embeds across all projects.
- **SC-006**: Sign-out clears all client auth state (verified: no `llmxive_gh_token` / user / OAuth-state in browser storage post-sign-out) and survives reload — passes in 100% of test runs.
- **SC-007**: After sign-out, the OAuth flow can be completed to sign in as a different GitHub user — passes in 100% of test runs.
- **SC-008**: Every pipeline-diagram circle opens a modal with a step description (incl. inputs/outputs), ≥1 example-artifact link (or a "no examples yet" note for steps with none), and the step's agent list with every agent linking to a viewable prompt — true for 100% of circles.
- **SC-009**: The agent-registry modal lists 100% of agents in `agents/registry.yaml`; clicking any agent renders its prompt + tools with a GitHub source link — true for 100% of agents.
- **SC-010**: The About page has a "How to contribute" section covering all four contribution modes with actionable pointers.
- **SC-011**: 100% of artifact views on the site present a "submit feedback" affordance; a "submit a paper" affordance exists accepting URL or PDF; a submitted feedback/paper is recorded to the repo with full context and the user sees a confirmation — verified for ≥1 artifact of each type.
- **SC-012**: The README contains 0 factual claims contradicted by the current repo state (verified by review against the live repo).
- **SC-013**: All new/modified modals are usable at mobile widths — 0 clipped/undismissable cases.
- **SC-014**: After the fixes, `docs/` matches `web/` (the deploy sync ran) and the GitHub Pages build succeeds.
- **SC-015**: The pipeline-cron regeneration of `web/data/projects.json` does not reintroduce any of these bugs — verified by re-running the relevant checks after a cron tick (or a simulated regeneration).

## Assumptions

- The site is a static GitHub Pages app: markup in `web/index.html`, styles in `web/css/*.css`, behavior in `web/js/*.js` (vanilla JS), data in `web/data/projects.json` (built by `src/llmxive/web_data.py`), and `web/` is synced to `docs/` for deployment. Fixes touch these files; the data-correctness fixes (FR-007, FR-008) are made in `web_data.py` so the site just renders correct data.
- GitHub auth uses an OAuth flow with the token in browser `localStorage` (`llmxive_gh_token`) and exchange via the existing OAuth-proxy worker (`simple-oauth-proxy`). FR-010/FR-011 are client-side fixes to `web/js/auth.js`; the `state` handling and the GitHub re-prompt are the likely root causes. If a proxy-side change turns out to be required, it's a small adjunct to this spec, not a separate one.
- "Recent example artifacts" for a pipeline step (FR-003) are sourced from the existing project/run-log data already in `web/data/projects.json` (or a small extension of it) — no new crawl.
- **The backend AI-review-and-triage worker for item 8 (the half that reads the recorded `feedback/` submissions and routes them into the pipeline) is OUT OF SCOPE for this spec.** It will be a separate spec (a new pipeline agent / step). This spec records submissions as structured files under `feedback/` that the future worker consumes (resolved at `/speckit-specify`: recording mechanism = tracked file in the repo, committed via the signed-in user's GitHub credentials — *not* a GitHub issue/comment).
- Markdown rendering in modals (FR-009, FR-004) uses a lightweight client-side renderer (or pre-rendered HTML in `web_data`) — decided at `/speckit-plan`; no heavyweight dependency.
- The four pipeline-diagram steps / lanes already exist on the About page; FR-003 makes the existing circles interactive, it doesn't redesign the diagram.
- The `feedback/` directory layout (per-project subdirs vs. flat, file format, how uploaded PDFs are stored) is a `/speckit-plan` detail; the spec only fixes that it's a structured tracked file with enough context for the triage worker.

## Out of Scope

- The backend AI-review-and-triage worker for #115 item 8 (separate follow-up spec — a new pipeline agent/step that consumes the recorded feedback/paper submissions).
- Any redesign of the dashboard layout, tab set, or visual theme beyond the specific fixes listed.
- Hosting/CDN/DNS changes for context-lab.com.
- Changes to the data pipeline itself beyond the `web_data.py` contributor-attribution / count fixes (FR-007, FR-008).
- Authentication providers other than GitHub.
