# Feature Specification: Agentic Pipeline Refactor (Spec-Kit-per-Project)

**Feature Branch**: `001-agentic-pipeline-refactor`
**Created**: 2026-04-28 · **Last revised**: 2026-04-28
**Status**: Draft (revised — Spec-Kit-per-project model)
**Input**: User description: "Refactor llmXive so the entire scientific-discovery
pipeline is structured around GitHub Spec Kit. Each research project is its
own Spec Kit project. Specialist agents drive every Spec Kit slash command
(`/speckit.constitution`, `/specify`, `/clarify`, `/plan`, `/tasks`,
`/analyze`, `/implement`) under the supervision of higher-level reviewer
and lifecycle agents. After research is implemented, an analogous Spec Kit
pipeline is run for the *paper* artifact. All agents run in scheduled
GitHub Actions cron jobs on free LLM backends (Dartmouth Chat via
`langchain-dartmouth`, Hugging Face fallback)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Each project is a Spec-Kit project; agents drive every slash command (Priority: P1)

A repository maintainer enables the system. Brainstorm and Flesh-Out
agents create new project ideas. The system promotes the strongest ones
into per-project Spec Kit subdirectories under `projects/<PROJ-ID>/`,
each with its own `.specify/` scaffold. From that point on, specialist
agents drive every Spec Kit slash command in sequence — `specify`,
`clarify`, `plan`, `tasks`, `analyze`, `implement` — until the project's
research artifacts are complete. After research review, a second Spec
Kit pipeline runs for the paper itself (in
`projects/<PROJ-ID>/paper/.specify/`), driven by analogous paper-focused
agents.

**Why this priority**: This is the core architectural change. Spec Kit
becomes the methodology, not just a project-management overlay; agents
are conversational drivers of slash commands rather than ad-hoc Python
functions.

**Independent Test**: Pick one fleshed-out idea from the queue. Run the
full per-project pipeline (`speckit.constitution` → `specify` →
`clarify` → `plan` → `tasks` → `analyze` → `implement`) end-to-end via
scheduled runs. Confirm that every slash-command output exists at the
canonical Spec Kit path (`projects/<PROJ-ID>/.specify/memory/constitution.md`,
`projects/<PROJ-ID>/specs/001-<short-name>/{spec,plan,tasks}.md`, etc.),
that all checklists pass, and that `analyze` produces no unresolved
issues at the time `implement` begins.

**Acceptance Scenarios**:

1. **Given** a fleshed-out idea selected for promotion, **When** the
   Project-Initializer Agent runs, **Then** a fresh Spec Kit scaffold is
   created at `projects/<PROJ-ID>/` (its own `.specify/` directory,
   `specs/` directory, and project-level `constitution.md` derived from
   the user-supplied research-project constitution template).
2. **Given** a Spec-Kit-initialized project with no spec yet, **When** the
   Specifier Agent runs, **Then** it executes the `/speckit.specify`
   workflow (mechanical script `create-new-feature.sh` + LLM-driven
   spec drafting) and writes `projects/<PROJ-ID>/specs/001-<short-name>/spec.md`.
3. **Given** a project whose spec has open `[NEEDS CLARIFICATION]`
   markers, **When** the Clarifier Agent runs, **Then** it executes
   `/speckit.clarify` and either resolves every marker by interrogating
   primary sources (Constitution Principle II) or escalates the project
   to a `human_input_needed` status.
4. **Given** a clarified spec, **When** the Planner Agent runs, **Then**
   it executes `/speckit.plan`, producing `plan.md`, `research.md`,
   `data-model.md`, `quickstart.md`, and `contracts/` exactly as Spec
   Kit dictates.
5. **Given** a complete plan, **When** the Tasker Agent runs, **Then** it
   executes `/speckit.tasks` to produce `tasks.md`, then immediately
   runs `/speckit.analyze`, then resolves EVERY issue analyze raises by
   editing the upstream artifact, and re-runs `/speckit.analyze` until
   it returns a clean report. The Tasker's run-log records every issue
   and its resolution.
6. **Given** an analyzed task list, **When** an Implementer Agent runs,
   **Then** it executes `/speckit.implement`, completing as many tasks
   as fit within its leaf wall-clock budget. The agent persists progress
   so subsequent scheduled runs resume from the next incomplete task.

---

### User Story 2 — Implementer agents preferentially resume incomplete work (Priority: P1)

The pool of Implementer Agents preferentially picks up projects whose
`tasks.md` is partially complete (in-progress projects), and only
selects fresh analyzed-but-not-yet-started projects when no in-progress
work is available. Each Implementer Agent records which task IDs it
completed in the run-log, so different agents in different scheduled
runs can collaborate on the same project without stepping on each
other.

**Why this priority**: Reliability — ensures projects make end-to-end
progress rather than starting many in parallel and finishing none.

**Independent Test**: Manually mark several tasks as complete in one
project and several others as analyzed-but-untouched. Run the
scheduler. Verify the Implementer Agent picks the partially-complete
project first, completes one or more of its remaining tasks, and the
new run-log entries reference the same `PROJ-ID`.

**Acceptance Scenarios**:

1. **Given** N projects in `in_progress` and M projects in `analyzed`,
   **When** the scheduler picks the next project, **Then** an
   `in_progress` project is selected with priority over an `analyzed`
   project.
2. **Given** two scheduled runs in succession, **When** the second run
   starts, **Then** the Implementer Agent reads `tasks.md` plus the
   prior run-log and resumes from the first incomplete task, never
   re-running a successfully completed task.
3. **Given** an Implementer Agent finishing the last task in `tasks.md`,
   **When** it commits its final outputs, **Then** the project's
   stage advances to `research_complete` (ready for research review).

---

### User Story 3 — Research-quality reviewers vote on the implemented project (Priority: P1)

Once a project's research implementation is complete, Research-Reviewer
Agents read the implemented artifacts (code, data, results) and submit
a vote with a recommendation: `accept`, `minor_revision`,
`full_revision`, or `reject`. Votes accumulate using the existing point
system (LLM = 0.5, human = 1.0). Once an accept threshold is reached the
project advances to paper drafting; below threshold, the recommendation
with the most weighted votes determines the next action.

**Why this priority**: Quality gate — research must pass review before
paper drafting begins, mirroring traditional peer review.

**Independent Test**: Stage a project with deliberately weak code (e.g.,
unhandled error case left in). Run multiple Research-Reviewer Agents.
Confirm their vote distribution skews toward `minor_revision` or
`full_revision`, that the corresponding revision pipeline is triggered,
and that no project advances to paper drafting without the accept
threshold.

**Acceptance Scenarios**:

1. **Given** a `research_complete` project, **When** a Research-Reviewer
   Agent runs, **Then** it reads the implemented artifacts (not just
   the spec/plan/tasks) and writes a review record under
   `projects/<PROJ-ID>/reviews/research/` with one of four
   recommendations.
2. **Given** the project's research-review point total reaches the
   accept threshold (per `web/about.html`), **When** the
   Advancement-Evaluator Agent runs, **Then** the project advances to
   `paper_drafting` and the paper Spec Kit pipeline is initialized.
3. **Given** the project's most-weighted recommendation is
   `full_revision`, **When** the Advancement-Evaluator Agent runs, **Then**
   the project is reset to the `idea_clarified` stage with the reviewer's
   prompt feedback attached, and the Specifier Agent re-runs from there.
4. **Given** the most-weighted recommendation is `minor_revision`, **When**
   the Advancement-Evaluator Agent runs, **Then** the Tasker Agent is
   re-invoked to generate a revision task list addressing the reviewers'
   feedback, and Implementer Agents pick it up in the next scheduled run.
5. **Given** the most-weighted recommendation is `reject`, **When** the
   Advancement-Evaluator Agent runs, **Then** the project is bumped back
   to the brainstorming phase and a `rejected/` snapshot is recorded.

---

### User Story 4 — Paper drafting is its own Spec Kit pipeline with paper-focused agents (Priority: P1)

For an `accept`ed research project, paper drafting runs through an
analogous Spec Kit pipeline at
`projects/<PROJ-ID>/paper/.specify/`, with each command driven by a
paper-focused agent: writing, figure generation, statistical
interpretation, literature search, reference & claim verification, and
proofreading. The output is a LaTeX source tree, supporting code, and a
compiled PDF with figures.

**Why this priority**: Paper drafting has its own quality concerns
(prose, figures, citations, logical flow) that warrant the same
disciplined methodology as research.

**Independent Test**: Take a research-accepted fixture project. Run the
paper pipeline end-to-end. Confirm that
`projects/<PROJ-ID>/paper/specs/001-paper/{spec,plan,tasks}.md` exist,
that the paper's `analyze` step finds and fixes issues before
`implement`, that the implemented paper compiles to PDF without LaTeX
errors, that every cited reference is verified by the
Reference-Validator Agent, and that the proofreader's review log is
empty of `repeated section`, `inconsistency`, and `over-jargon` flags.

**Acceptance Scenarios**:

1. **Given** a research-accepted project, **When** the Paper-Initializer
   Agent runs, **Then** it scaffolds a Spec Kit project at
   `projects/<PROJ-ID>/paper/` with a paper-specific constitution.
2. **Given** an unwritten paper spec, **When** the Paper-Specifier Agent
   runs, **Then** it executes `/speckit.specify` for the paper artifact,
   describing structure (Abstract, Intro, Methods, Results, Discussion,
   Bibliography), required figures, and analysis interpretations.
3. **Given** a paper with a `tasks.md`, **When** Paper-Implementer Agents
   run, **Then** specialist sub-agents handle their respective task
   categories: Writing-Agent for prose, Figure-Generation-Agent for
   plots, Statistics-Agent for inferential analysis, Lit-Search-Agent
   for related work, Reference-Verifier-Agent (reuses the
   Reference-Validator Agent) for citation accuracy, and
   Proofreader-Agent for logic, repetition, inconsistency, and
   jargon-overuse checks.
4. **Given** a complete paper draft, **When** the LaTeX-Build Agent runs,
   **Then** it compiles the LaTeX to PDF, captures errors, and the
   LaTeX-Fix Agent repairs any compilation failures before the project
   advances.

---

### User Story 5 — Paper reviewers vote on the final draft (Priority: P1)

Once paper drafting is complete (compiled PDF + verified citations +
clean proofreader pass), Paper-Reviewer Agents read the full paper and
submit a vote with one of four recommendations: `accept`,
`minor_revision`, `major_revision_writing`, `major_revision_science`,
or `fundamental_flaws`. Votes accumulate. Once the accept threshold is
reached, the project advances to `posted`. Otherwise, the
most-weighted recommendation routes the project to a specific revision
path.

**Why this priority**: Final quality gate — distinguishes writing
problems (fix in the paper Spec Kit pipeline) from science problems
(bump back to research) from showstoppers (bump back to brainstorming).

**Independent Test**: Stage a fixture paper with a deliberately weak
results section. Run multiple Paper-Reviewer Agents. Confirm the votes
correctly route the project to `major_revision_science` (back to the
research Spec Kit pipeline), not to `major_revision_writing` or
`accept`.

**Acceptance Scenarios**:

1. **Given** a complete paper draft, **When** a Paper-Reviewer Agent
   runs, **Then** it reads the PDF and the LaTeX source and writes a
   review record under `projects/<PROJ-ID>/paper/reviews/` with one of
   five recommendations.
2. **Given** the paper-review point total reaches the accept threshold,
   **When** the Advancement-Evaluator Agent runs, **Then** the project
   advances to `posted` and a Status-Reporter Agent posts the canonical
   completion announcement.
3. **Given** the most-weighted recommendation is
   `major_revision_writing`, **When** the Advancement-Evaluator Agent
   runs, **Then** the project is reset to the `paper_clarify` stage of
   the paper Spec Kit pipeline (preserving the research artifacts).
4. **Given** the most-weighted recommendation is
   `major_revision_science`, **When** the Advancement-Evaluator Agent
   runs, **Then** the project is reset to the research Spec Kit
   pipeline's `clarify` stage with reviewer feedback attached.
5. **Given** the most-weighted recommendation is `fundamental_flaws`,
   **When** the Advancement-Evaluator Agent runs, **Then** the project
   is bumped back to brainstorming and a `rejected/` snapshot is taken.
6. **Given** the most-weighted recommendation is `minor_revision`,
   **When** the Advancement-Evaluator Agent runs, **Then** the
   Paper-Tasker Agent is re-invoked to generate a revision task list
   targeting the reviewers' feedback.

---

### User Story 6 — The system runs end-to-end on free LLM backends with cost-aware fallbacks (Priority: P1)

(Carried forward unchanged from the prior revision.) The default
execution path uses only free or zero-cost services: GitHub Actions free
minutes, Dartmouth Chat (`langchain-dartmouth`) for the bulk of LLM
calls, Hugging Face Inference (free tier) as fallback, and free local
inference for the smallest agents. Paid services MUST NOT be required
and MUST be opt-in.

**Independent Test**: Same as before — provision a fresh fork with only
`DARTMOUTH_CHAT_API_KEY` and a Hugging Face token. Run the full
scheduled workflow. Every agent succeeds; cost estimate is $0.00.

---

### User Story 7 — Verified-accuracy guardrails block fabricated references and unverified claims at every stage (Priority: P2)

The Reference-Validator Agent runs at three points: when a research-stage
artifact (design, plan, code, data analysis) cites an external source,
when a paper-stage artifact does so, and as a final gate before
`research_accept` and before `paper_accept`. Each external citation
MUST be fetched against its primary source and pass title/author match
before contributing review points.

**Independent Test**: Inject a fabricated citation into a fixture paper.
Confirm the Reference-Validator Agent flags it, the project cannot
reach `paper_accept`, and the failing citation is listed on the
project's GitHub issue.

---

### User Story 8 — Real-execution test gate verifies pipeline functionality before scheduled runs hit production (Priority: P2)

(Carried forward.) Every PR that modifies agent code, prompts, Spec Kit
templates, or workflow configuration MUST pass a CI check that runs at
least one real LLM call against a free backend, executes one
end-to-end pipeline run on a fixture project that goes from
`brainstorm` through `research_complete`, and verifies the run-log
format. Mock-only tests do not satisfy this gate.

---

### User Story 9 — Operators get clear, fast failure signals and can resume from any stage (Priority: P3)

(Carried forward.) Failures surface within seconds via fail-fast
preconditions. The next scheduled run resumes from the failed Spec Kit
slash command on the failing project, never restarting the pipeline
from `brainstorm`.

---

### Edge Cases

- A project's `/speckit.analyze` keeps surfacing the same issue across
  multiple revision rounds: the Tasker Agent MUST cap revision-round
  iterations (default 5) and escalate the project to `human_input_needed`
  once the cap is reached.
- An Implementer Agent crashes mid-task: the per-task entry in the
  run-log records `outcome=failed`, the per-project lock is released
  (or auto-released by `expires_at`), and the next scheduled run picks
  up from the failed task.
- Two Implementer Agents in the same scheduled run try to claim the
  same project: the per-project lock prevents this; the second agent
  picks the next project in priority order.
- A research-review or paper-review vote is submitted on stale artifacts
  (the artifact's hash changed after the review was started): the vote
  is invalidated and the reviewer is asked to re-vote. (Same anti-tamper
  pattern as before.)
- A Brainstorm Agent generates a duplicate idea (semantic match against
  existing ideas): the duplicate is rejected at flesh-out time before a
  new project ID is allocated.
- The paper-LaTeX build fails repeatedly even after the LaTeX-Fix Agent
  runs N times: project escalates to `human_input_needed`.
- The Reference-Validator flags a citation as `unreachable` (transient
  network issue, not a fabrication): the validator retries on the next
  scheduled run; the project is NOT bumped back to revision unless the
  status remains `unreachable` for K consecutive runs.
- A reviewer agent reviews an artifact authored by itself (or by a
  prompt-derived sibling): self-review detection (same agent name on
  author and reviewer) refuses to award points.

## Requirements *(mandatory)*

### Functional Requirements

#### Pipeline orchestration & scheduling

- **FR-001**: System MUST run scheduled GitHub Actions cron jobs (default
  every 3 hours) that select projects to act on according to the
  scheduler priority order: `in_progress` > `analyzed` > `clarified` >
  `specified` > `flesh_out_complete` > `brainstormed` > `paper_in_progress`
  > `paper_analyzed` > `paper_clarified` > `paper_specified` >
  `paper_drafting_init` > `research_complete`.
- **FR-002**: System MUST support manual `workflow_dispatch` triggering
  of the entire pipeline or any single per-project Spec Kit slash
  command.
- **FR-003**: System MUST advance projects through the canonical
  lifecycle: `brainstormed` → `flesh_out_complete` → `specified` →
  `clarified` → `planned` → `tasked` → `analyzed` → `in_progress` →
  `research_complete` → `research_review` → (`research_accepted` |
  `minor_revision` | `full_revision` | `rejected`) → `paper_drafting_init`
  → `paper_specified` → `paper_clarified` → `paper_planned` →
  `paper_tasked` → `paper_analyzed` → `paper_in_progress` →
  `paper_complete` → `paper_review` → (`accepted` |
  `minor_revision_paper` | `major_revision_writing` |
  `major_revision_science` | `fundamental_flaws`) → `posted`.
- **FR-004**: System MUST persist pipeline state (per-project current
  stage, run-log entries, citation-verification status, lock state) in
  files committed to the repository so any contributor can audit
  history via `git log`.
- **FR-005**: System MUST acquire and release a per-project advisory
  lock before any mutating agent run, and MUST refuse to run if the
  lock is already held.
- **FR-006**: The Implementer Agent's project-selection rule MUST
  preferentially pick up projects with `in_progress` status (partially
  implemented) before considering `analyzed` projects (fresh,
  unimplemented but ready). Selection within a status tier is by oldest
  `updated_at`.

#### Agent registry & responsibilities

- **FR-007**: System MUST define a single canonical agent registry
  enumerating every specialist agent with its purpose, declared inputs,
  declared outputs, default LLM backend, fallback backends, and prompt
  template path.
- **FR-008**: The agent registry MUST include, at minimum, the following
  specialist agents:

  **Idea-generation phase**:
  - **Brainstorm Agent** — generates short, raw idea seeds from a field
    prompt. Output: a one-paragraph idea note.
  - **Flesh-Out Agent** — expands a raw idea into a fully-defined
    research concept by pulling related literature, articulating the
    research question, identifying expected results, and noting
    methodology. Calls the Lit-Search Agent as a tool. Output: a
    fleshed-out idea document. Performs duplicate-detection against
    existing project ideas.
  - **Idea-Selector Agent** — non-LLM rule + lightweight ranking;
    selects which fleshed-out ideas to promote to per-project Spec Kit
    initialization based on score thresholds and capacity.

  **Per-project Spec Kit pipeline (one agent per slash command)**:
  - **Project-Initializer Agent** — runs the equivalent of
    `specify init` inside `projects/<PROJ-ID>/`: creates `.specify/`,
    copies templates, drafts the project's research-level
    `constitution.md` from the system-wide research-project constitution
    template (Constitution Principle I — one template, every project
    references it).
  - **Specifier Agent** — drives `/speckit.specify`: invokes the
    mechanical script `create-new-feature.sh`, then runs the LLM
    workflow to draft `spec.md` from the fleshed-out idea.
  - **Clarifier Agent** — drives `/speckit.clarify`: identifies any
    `[NEEDS CLARIFICATION]` markers in the spec, fetches primary sources
    where possible (Constitution Principle II), and updates the spec.
    Escalates to `human_input_needed` if a marker cannot be resolved
    after a configurable number of attempts.
  - **Planner Agent** — drives `/speckit.plan`: invokes `setup-plan.sh`
    and produces `plan.md`, `research.md`, `data-model.md`,
    `quickstart.md`, and `contracts/`.
  - **Tasker Agent** — drives `/speckit.tasks` followed by
    `/speckit.analyze`. Resolves EVERY analyze-issue by editing the
    upstream artifact and re-running analyze. Records each issue and
    its resolution in the run-log. Caps revision-round iterations
    (default 5) and escalates to `human_input_needed` on cap-hit.
  - **Implementer Agent** — drives `/speckit.implement`: completes as
    many tasks from `tasks.md` as fit within its leaf wall-clock budget,
    persists progress, and re-queues the project for the next scheduled
    run if tasks remain.

  **Research-quality review phase**:
  - **Research-Reviewer Agent (LLM)** — reads the implemented research
    artifacts (code, data, analyses) and produces a review record with
    a recommendation in {`accept`, `minor_revision`, `full_revision`,
    `reject`} plus weighted feedback.

  **Paper drafting phase (analogous Spec Kit pipeline)**:
  - **Paper-Initializer Agent** — scaffolds Spec Kit at
    `projects/<PROJ-ID>/paper/` with a paper-level constitution.
  - **Paper-Specifier Agent** — drives `/speckit.specify` for the paper
    artifact (sections, required figures, claim list).
  - **Paper-Clarifier Agent** — drives `/speckit.clarify` on the paper
    spec.
  - **Paper-Planner Agent** — drives `/speckit.plan` for the paper.
  - **Paper-Tasker Agent** — drives `/speckit.tasks` + `/speckit.analyze`
    for the paper, resolving every issue analyze raises.
  - **Paper-Implementer Agents** — drive `/speckit.implement` for the
    paper. Specialized sub-agents handle their task categories:
    - **Writing-Agent** — composes prose for one section/subsection at
      a time.
    - **Figure-Generation-Agent** — generates plots from real data
      using a code-execution sandbox; outputs PDF/PNG figures.
    - **Statistics-Agent** — performs and writes interpretations of
      inferential analyses on real outputs.
    - **Lit-Search-Agent** — finds and verifies related literature; can
      be called by Flesh-Out, Paper-Specifier, and Writing-Agent.
    - **Reference-Verifier-Agent** — alias for the
      Reference-Validator Agent; runs against every citation in the
      paper.
    - **Proofreader-Agent** — flags repeated sections, internal
      inconsistencies, jargon overuse, logical issues.
    - **LaTeX-Build Agent** — compiles LaTeX → PDF; captures errors.
    - **LaTeX-Fix Agent** — repairs LaTeX compilation errors.

  **Final paper review phase**:
  - **Paper-Reviewer Agent (LLM)** — reads the compiled PDF + LaTeX
    source; produces a review record with a recommendation in
    {`accept`, `minor_revision`, `major_revision_writing`,
    `major_revision_science`, `fundamental_flaws`}.

  **Cross-cutting**:
  - **Reference-Validator Agent** — fetches and verifies every cited
    URL, arXiv ID, DOI, or dataset reference (Constitution Principle II).
  - **Advancement-Evaluator Agent** — non-LLM, rule-based. Reads review
    records and project state, decides every stage transition.
  - **Repository-Hygiene Agent** — enforces operational standards
    (gitignore checks, leftover-file cleanup, doc parity checks).
  - **Status-Reporter Agent** — produces the run summary; posts issue
    comments for state changes and failures; regenerates `web/data/projects.json`.
  - **Task-Atomizer Agent** — when a parent task's wall-clock estimate
    exceeds its agent's leaf budget, decomposes it hierarchically into
    sub-tasks each fitting the budget. Recursive: a sub-task whose
    estimate is still over-budget is re-atomized.
  - **Task-Joiner Agent** — automatically spawned when the last sibling
    sub-task in an atomized set completes. Merges sub-task outputs into
    the parent task's artifact format. For hierarchical
    decompositions, a Joiner at level N produces input for the level-(N-1)
    Joiner.
- **FR-009**: Each agent MUST be invocable in isolation (CLI flag or
  stage selector) for testing and manual recovery, without requiring
  the preceding stages to run.
- **FR-010**: Each agent MUST emit a structured run-log entry
  conforming to a single canonical schema, written to a path the rest
  of the system reads.

#### Spec Kit integration

- **FR-011**: Each project MUST have its own Spec Kit scaffold at
  `projects/<PROJ-ID>/.specify/` (research) and, post-research-review,
  `projects/<PROJ-ID>/paper/.specify/` (paper). The repository's
  top-level `.specify/` directory remains the meta-system for the
  llmXive refactor itself; the per-project scaffolds are independent
  Spec Kit projects.
- **FR-012**: The system-wide **research-project constitution
  template** lives at one canonical location
  (`agents/templates/research_project_constitution.md`). Every per-project
  research constitution is derived from this template at
  Project-Initializer time, with project-specific values substituted.
- **FR-013**: The system-wide **paper-project constitution template**
  lives at `agents/templates/paper_project_constitution.md`. Every
  per-project paper constitution is derived from this template at
  Paper-Initializer time.
- **FR-014**: Specialist agents that drive Spec Kit slash commands MUST
  invoke the slash command's *mechanical script* (e.g.,
  `create-new-feature.sh`, `setup-plan.sh`, `check-prerequisites.sh`)
  exactly once per invocation, then drive the LLM workflow following
  the slash command's authored prompt template. Slash commands are
  agent-driven, not subprocess-callable as a single command (verified:
  Spec Kit's slash commands assume an agent-driven chat session; only
  the bash scripts are headless).
- **FR-015**: The Tasker Agent MUST run `/speckit.analyze` after every
  `/speckit.tasks` invocation and MUST resolve every issue analyze
  surfaces by editing the upstream artifact, then re-running analyze.
  This loop continues until analyze returns clean OR the configured
  cap is hit (default 5 rounds), at which point the project is
  escalated to `human_input_needed`.
- **FR-016**: The same `/speckit.analyze`-then-resolve discipline MUST
  apply at the paper stage (Paper-Tasker Agent).

#### LLM backend abstraction

- **FR-017**: System MUST support at least three free LLM backend
  families, configurable per agent: (a) Dartmouth Chat (authenticated
  via the `DARTMOUTH_CHAT_API_KEY` repository secret, accessed via
  `langchain-dartmouth`), (b) Hugging Face Inference (free tier,
  authenticated via Hugging Face token), and (c) local inference on the
  Actions runner for small enough models.
- **FR-018**: Each agent's backend selection MUST be configured in the
  agent registry, NOT hardcoded in agent code, so backends can be
  swapped by editing one file.
- **FR-019**: System MUST automatically fall back to the next configured
  free backend on transient errors (rate limit, quota, connectivity)
  before failing the run.
- **FR-020**: System MUST NOT require any paid-API key to function.
  Paid backends, if added later, MUST be opt-in and clearly flagged in
  the agent registry; the contract schema asserts paid-opt-in is
  `false` by default.
- **FR-021**: Every LLM call MUST validate its preconditions (key
  present, endpoint reachable, model available) before issuing the
  request, and MUST fail-fast with a precondition-specific error
  message if any check fails.
- **FR-022**: Dartmouth model identifiers MUST be resolved at runtime
  via `ChatDartmouth.list()` and `CloudModelListing.list()`, never
  hardcoded.

#### Single source of truth & repository structure

- **FR-023**: The refactor MUST consolidate all duplicated logic in the
  current `code/llmxive-automation/` tree into exactly one canonical
  implementation; the legacy duplicates MUST be deleted.
- **FR-024**: System MUST store every prompt template in exactly one
  canonical location (`agents/prompts/`), referenced by every agent
  that uses it; copy-pasted prompt strings inside agent code are
  prohibited.
- **FR-025**: Every research project's artifacts MUST live under a
  single canonical layout (`projects/<PROJ-ID>/.specify/...`,
  `projects/<PROJ-ID>/specs/...`, `projects/<PROJ-ID>/code/...`,
  `projects/<PROJ-ID>/data/...`, `projects/<PROJ-ID>/reviews/research/...`).
  Every paper-stage artifact MUST live under
  `projects/<PROJ-ID>/paper/.specify/...`,
  `projects/<PROJ-ID>/paper/specs/...`,
  `projects/<PROJ-ID>/paper/figures/...`, and
  `projects/<PROJ-ID>/paper/reviews/...`. Prior parallel layouts under
  `technical_design_documents/`, `implementation_plans/`, `papers/`
  MUST be migrated into the canonical layout or deleted.

#### Verified accuracy

- **FR-026**: Every external citation in any user-facing artifact
  (research design, plan, code annotations, paper) MUST be verified
  against the primary source by the Reference-Validator Agent before
  the artifact can earn its first review point.
- **FR-027**: The validator MUST record, per citation, the verification
  outcome (verified / unreachable / mismatch), the source URL fetched,
  the fetched title or authors, and the timestamp.
- **FR-028**: Any artifact with an unverified or mismatched citation
  MUST be blocked from advancing past `research_review` (research stage)
  or `paper_review` (paper stage) until the citation is corrected or
  removed.

#### Real-execution testing

- **FR-029**: The CI pipeline MUST run at least one real LLM call
  against a free backend on every PR that modifies agent code, prompts,
  Spec Kit templates, or workflow files.
- **FR-030**: The CI pipeline MUST run an end-to-end fixture
  (brainstorm → research_complete) on every PR that modifies the
  pipeline orchestrator or any agent that drives a Spec Kit slash
  command.
- **FR-031**: The CI pipeline MUST verify, on every PR, that every
  prompt template referenced by the agent registry exists and parses,
  every Spec Kit script referenced by the agent registry is executable,
  and every backend configuration resolves to a valid endpoint.

#### Failure behavior & observability

- **FR-032**: Every workflow run MUST validate critical preconditions
  (required secrets present, required tools on PATH including `git`,
  `pdflatex`, `uv`/`pipx`/`uvx`, required input files exist and parse,
  output directories writable, network reachability for required
  backends) within a fail-fast preamble.
- **FR-033**: System MUST post a status comment on the relevant GitHub
  issue when a project's stage advances, when a project is blocked, and
  when an agent run fails — exactly one comment per state transition.
- **FR-034**: System MUST emit a per-run summary listing: agents
  invoked, projects touched, state transitions made, citations
  verified, paid-API calls (expected: zero), and total wall time.
- **FR-035**: When a run fails mid-pipeline, the next scheduled run
  MUST resume from the failed Spec Kit slash command on the affected
  project, not restart from `brainstormed`.

#### Long-running task handling

- **FR-036**: Every individual agent task is capped at a configured
  short-task wall-clock budget that fits the GitHub Actions free
  runner. For tasks whose estimated runtime exceeds the budget, the
  Task-Atomizer Agent MUST decompose the task into sub-tasks, each
  fitting the budget. The Task-Joiner Agent MUST automatically merge
  sub-task outputs when the last sibling completes. Both support
  arbitrary hierarchy depth.

#### Web interface continuity

- **FR-037**: The existing public web interface (`web/index.html`,
  `web/about.html`, `web/projects.html`) MUST continue to load project
  state from canonical repository data. The about page MUST be updated
  to reflect the Spec-Kit-per-project model and document every
  lifecycle stage.
- **FR-038**: The about page remains the single source of truth for
  stage thresholds (point counts to advance from one stage to the next);
  code reads from a parser that extracts these values.

### Key Entities *(include if feature involves data)*

- **Project**: A research effort identified by `PROJ-###-descriptive-name`.
  Has a current stage (≥ 25 enumerated values per FR-003), accumulated
  review points (research-stage points + paper-stage points kept
  separately), and a canonical artifact directory tree.
- **Stage**: One of the 25+ enumerated lifecycle states.
- **Artifact**: A file produced by an agent. Each has a content hash
  for tamper detection and lives under the project's canonical layout.
- **Review Record**: A signed record per reviewer per artifact with a
  recommendation (research-stage values OR paper-stage values), score,
  and feedback. Anti-tamper via artifact hash. Self-review prohibited.
- **Agent**: A specialist defined in the agent registry with declared
  inputs, outputs, prompt template, default backend, and fallback chain.
- **Backend**: An LLM service (Dartmouth Chat, Hugging Face, local
  inference) with endpoint, authentication, model id, quota policy,
  and `is_paid: false` invariant for v1.
- **Run-Log Entry**: A structured record per agent invocation with
  inputs, outputs, backend, model, prompt version, timestamps, outcome,
  cost (zero by default).
- **Citation**: An external reference attached to an artifact, with
  verification status produced by the Reference-Validator Agent.
- **Lock**: A per-project advisory lock preventing concurrent mutating
  agent runs.
- **Task**: A unit of work assigned to an agent, with parent task ID,
  wall-clock estimate, declared inputs and outputs.
- **Atomization Tree**: A directed tree of Tasks rooted at a top-level
  task, with leaves that fit the wall-clock budget.
- **Spec Kit Project**: A self-contained Spec Kit scaffold at either
  `projects/<PROJ-ID>/` (research) or `projects/<PROJ-ID>/paper/`
  (paper). Each contains its own `.specify/` directory and `specs/`
  feature directories.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A clean fork of the repository, configured only with the
  free `DARTMOUTH_CHAT_API_KEY` secret and a Hugging Face token,
  advances at least one project by exactly one lifecycle stage per
  scheduled run on average over a 7-day window without any human
  intervention.
- **SC-002**: The total paid-API spend across all scheduled runs over
  any rolling 30-day window is $0.00 by default; any non-zero spend
  MUST be attributable to an explicit opt-in configuration change
  recorded in `git log`.
- **SC-003**: Every agent invocation produces a run-log entry
  conforming to the canonical schema; run-log compliance over any
  30-day window is 100%.
- **SC-004**: For every paper that reaches `accepted` or `posted`,
  every cited external reference has a successful verification record;
  the rate of fabricated or unverified citations is 0%.
- **SC-005**: When a scheduled run fails its precondition checks, the
  run terminates within a small fraction of the configured workflow
  timeout, so wasted compute on misconfigured runs is negligible.
- **SC-006**: Replacing any single agent's prompt requires editing
  exactly one file (the prompt template); auditors verify by counting
  the number of files modified in PRs that change only a prompt — the
  count is 1 plus optionally a version-bump entry.
- **SC-007**: The legacy duplicated implementations in the current
  `code/llmxive-automation/` tree are deleted; the new code base's
  total line count is measurably smaller than the legacy code base
  while preserving or improving feature coverage as measured by the
  real-execution test suite.
- **SC-008**: A new contributor can identify, within 5 minutes of
  opening the repository, which agent owns a given lifecycle stage and
  where its prompt lives, by reading the agent registry and one
  referenced prompt file.
- **SC-009**: Every PR that modifies agent code, prompts, Spec Kit
  templates, or workflows passes a real-execution CI gate that includes
  at least one real LLM call against a free backend and one real
  fixture-pipeline run; the gate's pass rate on green-build PRs is 100%.
- **SC-010**: The published web interface continues to display
  accurate project state, with zero broken links to artifact files
  after the refactor migration completes; the about page accurately
  documents every one of the 25+ lifecycle stages.
- **SC-011**: For every research-accepted project, an analogous paper
  Spec Kit pipeline runs to completion (LaTeX compiles to PDF) without
  human intervention, with the Reference-Verifier and Proofreader
  agents producing clean reports.
- **SC-012**: The Tasker Agent's `analyze`-then-resolve loop converges
  (clean analyze report) within 3 rounds on 95%+ of projects; only the
  remaining ≤ 5% escalate to `human_input_needed`.

## Assumptions

- The about-page point thresholds remain the single source of truth
  for stage advancement. The exact thresholds for new stages
  introduced by this refactor (research review accept threshold, paper
  review accept threshold) MUST be added to the about page in this PR.
- The Spec Kit `.specify/` scaffold can be initialized non-interactively
  by running its bash scripts (verified: `create-new-feature.sh`,
  `setup-plan.sh`, etc., are headless and accept `--json` output).
- The Spec Kit slash commands' authored prompts (under
  `.claude/skills/speckit-*/SKILL.md` or equivalent) are accessible to
  our agents as prompt templates. If Spec Kit ships them only via
  `.claude/skills/`, the agent registry MUST point at those paths
  rather than copying the content (Constitution Principle I — single
  source of truth).
- Per-project Spec Kit scaffolds in subdirectories of one parent repo
  are supported (each `.specify/` is independent of the parent
  `.specify/`). This MUST be verified during early implementation; if
  conflicts arise, sub-projects will move to detached worktrees or
  submodules.
- The system-wide research-project constitution and paper-project
  constitution will be drafted in this same PR (initial v1.0.0
  versions), then evolved separately. Both live under
  `agents/templates/`.
- GitHub Actions free-tier minutes remain sufficient for the cron
  schedule under the Spec-Kit-per-project model; if quota becomes
  binding, scaling decisions are out of scope for v1.
- Dartmouth's free LLM access remains available for the duration of v1.
- The Reference-Validator Agent's title-token-overlap threshold (0.7)
  is a starting point and may be tuned based on false-positive/negative
  rates observed in early runs.
- Migration of existing projects (under
  `technical_design_documents/`, `implementation_plans/`, `papers/`,
  `projects/`) to the new Spec-Kit-per-project layout is part of this
  refactor; nothing is silently dropped.
- Human review submissions (worth 1.0 point each) continue via the
  existing GitHub-issue-based flow; the refactor does not change the
  human-review submission UX.
