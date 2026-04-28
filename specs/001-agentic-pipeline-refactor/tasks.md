---
description: "Task list for the Spec-Kit-per-project agentic pipeline refactor"
---

# Tasks: Agentic Pipeline Refactor (Spec-Kit-per-Project)

**Input**: Design documents from `/Users/jmanning/llmXive/specs/001-agentic-pipeline-refactor/`
**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓), quickstart.md (✓)

**Tests**: Real-call tests are MANDATORY per Constitution Principle III. Mock-only unit tests are NOT generated; only real-call (live LLM, live citation fetch, live code sandbox) tests are scheduled.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently. Setup and Foundational phases gate all stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different files, no shared deps with incomplete tasks → can run in parallel
- **[Story]**: User-story label (US1–US9) for tasks inside a story phase
- All paths are repo-relative

## Path Conventions

- Python package: `src/llmxive/`
- Agent definitions, prompts, templates: `agents/`
- Per-project Spec Kit scaffolds: `projects/<PROJ-ID>/`
- Pipeline state: `state/`
- Tests: `tests/{unit,integration,real_call,contract}/`
- Workflows: `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bootstrap the new package, dependencies, lint/typecheck, and the canonical directory skeleton.

- [X] T001 Create `pyproject.toml` at repo root declaring the `llmxive` package with `langchain≥0.3`, `langgraph≥0.2`, `langchain-dartmouth≥0.3.1`, `langchain-huggingface≥0.1`, `huggingface_hub`, `pydantic≥2`, `jsonschema`, `tenacity`, `pyyaml`, `httpx`, `gitpython`, `arxiv`, `crossref-commons`, `matplotlib`, `pytest≥8`, `pytest-asyncio`, `ruff`, `mypy`
- [X] T002 Create the canonical directory skeleton at the repo root: `src/llmxive/{backends,speckit,agents,pipeline,state,tools}/`, `agents/{prompts,templates,tools}/`, `state/{projects,run-log,locks,citations}/`, `tests/{unit,integration,real_call,contract}/`, `.github/workflows/`
- [X] T003 [P] Configure `ruff.toml` with project-wide lint rules and `mypy.ini` with strict typing for `src/llmxive/**`
- [X] T004 [P] Add `.github/workflows/llmxive-pipeline.yml` skeleton with cron `0 */3 * * *` and a `workflow_dispatch` trigger declaring two optional inputs — `project_id` (string; if set, restricts the run to that project) and `stage` (enum of every Spec Kit slash command + idea-generation phases; if set, runs only that stage on the specified or scheduler-selected project) — to satisfy FR-002; the steps remain stubbed until US1 (FIX C1)
- [X] T005 [P] Add `.github/workflows/llmxive-real-call-tests.yml` skeleton that runs on PRs touching `src/llmxive/**`, `agents/**`, `.github/workflows/**`; the steps remain stubbed until US8 (extended in T036 and T114)
- [X] T006 Add `.gitignore` entries for `.env*`, `.venv/`, `__pycache__/`, `*.egg-info/`, `state/run-log/*/in-progress/*` so secrets and ephemeral artifacts never enter `git log`
- [X] T007 [P] Migrate the legacy directories — write `scripts/migrate_legacy_layout.py` that moves every `technical_design_documents/<id>/`, `implementation_plans/<id>/`, `papers/<id>/` and the existing `projects/<PROJ-ID>/` content into the canonical Spec-Kit-per-project layout under `projects/<PROJ-ID>/`, then deletes the legacy trees (FR-023, FR-025); the script is invoked once in T009
- [X] T008 [P] Author the system-wide research-project constitution template at `agents/templates/research_project_constitution.md` (initial v1.0.0). Required sections: Core Principles (≥ 5, project-specific scientific and methodological norms), Reproducibility Requirements, Data Hygiene, Verified Accuracy gate (citations, figures, claims), Versioning, Governance/amendment procedure. Substitution tokens (FIX U3): `{{project_id}}`, `{{title}}`, `{{field}}`, `{{date}}`, `{{principal_agent_name}}` (FIX A3)
- [ ] T009 Run `python scripts/migrate_legacy_layout.py --apply` and commit the resulting per-project tree; delete legacy `technical_design_documents/`, `implementation_plans/`, `papers/` directories in the same commit (FR-023). Migration edge cases (FIX U1): a legacy project with a partial paper but no research design lands at `human_input_needed` with `human_escalation_reason="legacy migration: missing research scaffold"`; a legacy project with no recognizable artifacts lands at `human_input_needed` with `human_escalation_reason="legacy migration: empty project"`. Pre-migration line count for `code/llmxive-automation/**` is captured to `state/migration_metrics.yaml` for SC-007 verification (FIX C3)
- [X] T010 [P] Author the system-wide paper-project constitution template at `agents/templates/paper_project_constitution.md` (initial v1.0.0). Required sections: Core Principles (writing-quality, figure-quality, citation-verification, statistical-interpretation, reproducibility, jargon-discipline), Required Sections (Abstract / Intro / Methods / Results / Discussion / References), Style & Voice norms, Reference-Verification gate, LaTeX Build gate, Governance/amendment procedure. Substitution tokens (FIX U3): `{{project_id}}`, `{{title}}`, `{{field}}`, `{{date}}` (FIX A3)

**Checkpoint**: Repo skeleton, deps, and migration are in place. Tests still empty.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the components every user story depends on: Pydantic types, contract-validation tooling, the LLM backend chain, the headless Spec Kit runner, the agent base class, the state stores, the lifecycle/advancement evaluator (skeleton only — extended per story), the per-project lock, the preflight, the run-log writer, and the agent-registry loader.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T011 Implement Pydantic models matching every schema in `contracts/` at `src/llmxive/types.py` (Project, ReviewRecord, RunLogEntry, AgentRegistryEntry, BackendEntry, Citation, Lock, Task; cross-field invariants per the schemas)
- [X] T012 Add a contract-validation utility at `src/llmxive/contract_validate.py` that loads each schema in `contracts/` (YAML or JSON) and validates a candidate object via `jsonschema`
- [X] T013 [P] Implement `src/llmxive/preflight.py`: validates `DARTMOUTH_CHAT_API_KEY`, `DARTMOUTH_API_KEY`, `HF_TOKEN`, `git`, `pdflatex`, `uvx`/`uv`, every prompt template referenced by `agents/registry.yaml` exists, the agent registry parses against the contract, and the Dartmouth + HF endpoints respond to a HEAD/list call (FR-032, Constitution Principle V)
- [X] T014 [P] Implement `src/llmxive/state/runlog.py` — append-only JSON Lines writer at `state/run-log/<YYYY-MM>/<run-id>.jsonl`; emits one line per agent invocation; validates each line against `contracts/run-log-entry.schema.json` before write. SCHEMA-VALIDATION FAILURES MUST raise (no silent skips, no partial writes); the failed entry is written verbatim to `state/run-log/<YYYY-MM>/.invalid/<entry_id>.json` for postmortem; this guarantees SC-003 100% compliance (FIX C7)
- [X] T015 [P] Implement `src/llmxive/state/project.py` — read/write `state/projects/<PROJ-ID>.yaml`, validates against `contracts/project-state.schema.yaml`, computes content hashes for every artifact under the project's canonical paths
- [X] T016 [P] Implement `src/llmxive/state/reviews.py` — reads/writes review records under `projects/<PROJ-ID>/reviews/{research,paper}/<author>__<YYYY-MM-DD>__<type>.md`, validates frontmatter against `contracts/review-record.schema.yaml`, refuses self-review (`reviewer_name == artifact.produced_by_agent`)
- [X] T017 [P] Implement `src/llmxive/state/citations.py` — reads/writes `state/citations/<PROJ-ID>.yaml`, validates against `contracts/citation.schema.yaml`, exposes a token-overlap matcher with default threshold 0.7
- [X] T018 [P] Implement `src/llmxive/pipeline/lock.py` — file-based per-project advisory lock at `state/locks/<PROJ-ID>.lock`; acquire / release / detect-stale-by-`expires_at` (FR-005)
- [X] T019 Implement `src/llmxive/config.py` — parses `web/about.html` once at import time and exposes `RESEARCH_ACCEPT_THRESHOLD`, `PAPER_ACCEPT_THRESHOLD`, `TASKER_MAX_REVISION_ROUNDS` (default 5), `LEAF_TASK_BUDGET_SECONDS` (default 300), `SANDBOX_BUDGET_SECONDS` (default 240), `CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7 — surfaced here so it is tunable without code changes; FIX K2), `STAGE_ADVANCEMENT_RATE_WINDOW_DAYS` (default 7, used by SC-001 metric — FIX C6); preflight rejects parse failure (FR-038)
- [X] T020 Implement the LLM backend chain: `src/llmxive/backends/{base,dartmouth,huggingface,local,router}.py`. Dartmouth uses `ChatDartmouth` from `langchain-dartmouth`, exposes `list()` for runtime model resolution (FR-022); HF uses `ChatHuggingFace`; local uses `transformers` for ≤ 7B models. Router falls back per agent registry config (FR-019). Schema invariant `is_paid: const false` enforced at registry-load (FR-020)
- [X] T021 Implement the headless Spec Kit runner at `src/llmxive/speckit/runner.py`: invokes `create-new-feature.sh`, `setup-plan.sh`, `check-prerequisites.sh` (and the per-project equivalents under `projects/<PROJ-ID>/.specify/scripts/bash/`) with `--json` and parses output. Exposes `init_speckit_in(directory)` that copies the upstream Spec Kit scaffold into a new project directory. Before invocation, runner verifies the per-project `.specify/scripts/bash/` exists, is executable, and matches the upstream pinned version's checksum; if missing or stale, runner re-syncs from a local Spec Kit cache populated at preflight time, then re-checks (FIX U2). Used by Project-Initializer + Paper-Initializer
- [X] T022 [P] Implement `src/llmxive/speckit/slash_command.py` — base class wrapping (a) the mechanical script invocation + (b) the upstream slash-command prompt template (referenced by path under `.specify/templates/` or `.claude/skills/speckit-*/`, never copied per Principle I) + (c) the LLM call + (d) writing artifacts at canonical Spec Kit paths + (e) appending a run-log entry
- [X] T023 [P] Implement `src/llmxive/agents/base.py` — `Agent` base class as a LangGraph node; declares input/output artifact types, default backend, fallback chain, prompt path, prompt version, wall-clock budget; emits a structured run-log entry on every invocation
- [X] T024 [P] Implement `src/llmxive/agents/runner.py` — invokes one agent given a project ID and a task, acquires the per-project lock via T018, calls `Agent.run()`, writes outputs and run-log, releases lock
- [X] T025 [P] Author the agent-registry loader at `src/llmxive/agents/registry.py` — reads `agents/registry.yaml`, validates against `contracts/agent-registry.schema.yaml`, exposes `get(name)` and `list()`
- [X] T026 Initialize `agents/registry.yaml` (v0.1.0) with backends section only (`dartmouth`, `huggingface`, `local`, all `is_paid: false`); agent entries are added per user story
- [X] T027 [P] Implement `src/llmxive/agents/lifecycle.py` — defines the 30+ stage enum exactly matching `contracts/project-state.schema.yaml`, exposes a `LifecycleGraph` LangGraph `StateGraph` skeleton; transitions are added incrementally per user story
- [X] T028 Implement `src/llmxive/agents/advancement.py` — non-LLM rule-based Advancement-Evaluator that reads project state + review records and decides each stage transition. Wired up generically; per-stage rules are added as user stories add their stages. Self-review prohibited at the rule level (FR-007 self-review edge case)
- [X] T029 [P] Implement `src/llmxive/pipeline/scheduler.py` — selects the next project to act on per FR-001 priority order (`in_progress` > `analyzed` > `clarified` > `specified` > `flesh_out_complete` > `brainstormed` > `paper_in_progress` > `paper_analyzed` > `paper_clarified` > `paper_specified` > `paper_drafting_init` > `research_complete`); within a tier, oldest `updated_at` wins
- [X] T030 [P] Implement `src/llmxive/pipeline/resume.py` — reads the most recent run-log and project state, returns the next stage to run for each project (FR-035)
- [X] T031 Implement `src/llmxive/cli.py` — `python -m llmxive` entry points: `preflight`, `run --max-tasks N`, `agents run --agent X --project Y [--dry-run]`, `backends list-models --backend dartmouth`. Wires all of the above
- [X] T032 [P] Real-call test `tests/real_call/test_dartmouth_chat.py` — gated by `LLMXIVE_REAL_TESTS=1`, issues a real `ChatDartmouth.invoke()` and asserts response shape (Constitution III; FR-029)
- [X] T033 [P] Real-call test `tests/real_call/test_hf_fallback.py` — same shape, against `ChatHuggingFace`
- [X] T034 [P] Real-call test `tests/real_call/test_speckit_scripts_headless.py` — exercises `create-new-feature.sh --json`, `setup-plan.sh --json`, `check-prerequisites.sh --json` against a temp directory and asserts the JSON shape upstream Spec Kit returns
- [X] T035 [P] Contract test `tests/contract/test_schemas.py` — loads every schema in `contracts/` and validates a known-good fixture object against each
- [X] T036 Wire `.github/workflows/llmxive-real-call-tests.yml` (extends T005's skeleton) to run `pytest tests/real_call/` and `pytest tests/contract/` with `LLMXIVE_REAL_TESTS=1` and the repository secrets exposed (FIX D1)

**Checkpoint**: Foundation ready. Backends, Spec Kit runner, types, state, lock, lifecycle skeleton, scheduler, CLI, and real-call CI all green. User-story phases can begin.

---

## Phase 3: User Story 1 — Spec-Kit-per-project pipeline drives every slash command (Priority: P1) 🎯 MVP

**Goal**: A fleshed-out idea is promoted to a per-project Spec Kit scaffold; specialist agents drive `/speckit.constitution`, `/specify`, `/clarify`, `/plan`, `/tasks`, `/analyze`, `/implement` end-to-end on that project.

**Independent Test**: Pick one fleshed-out idea fixture; trigger every Spec-Kit-driving agent in sequence on a clean fork; confirm every artifact lands at canonical Spec Kit paths and `analyze` reports clean before `implement` starts.

### Tests for User Story 1 (REAL-CALL only) ⚠️

- [X] T037 [P] [US1] Real-call test `tests/real_call/test_full_pipeline_e2e.py` — feeds `tests/real_call/fixtures/PROJ-TEST-001/` (a minimal idea) through Brainstorm → Flesh-Out → Project-Initializer → Specifier → Clarifier → Planner → Tasker → Implementer; asserts every canonical artifact exists at the canonical Spec Kit paths and the project reaches `research_complete` (FR-030)

### Implementation for User Story 1

#### Idea-generation phase (Brainstorm + Flesh-Out + Idea-Selector)

- [X] T038 [P] [US1] Author Brainstorm Agent prompt at `agents/prompts/brainstorm.md` (single-paragraph idea seeds from a field prompt)
- [X] T039 [P] [US1] Author Flesh-Out Agent prompt at `agents/prompts/flesh_out.md` (calls Lit-Search tool; produces structured idea with research question + related work + expected results + methodology; performs duplicate-detection via semantic similarity against existing project ideas)
- [X] T040 [P] [US1] Author Idea-Selector Agent prompt at `agents/prompts/idea_selector.md` (rule-based selection criteria + lightweight LLM ranking)
- [X] T041 [P] [US1] Implement Lit-Search tool at `agents/tools/lit_search.py` — queries Semantic Scholar, arXiv, OpenAlex; returns structured paper records; used as a LangChain tool by Flesh-Out and (later) by Paper-Specifier and the Writing Agent
- [X] T042 [US1] Add `brainstorm`, `flesh_out`, `idea_selector` entries to `agents/registry.yaml` (default backend `dartmouth`, fallback `huggingface`, prompt paths from T038–T040, budget 300 s each, `paid_opt_in: false`)

#### Per-project Spec Kit drivers

- [X] T043 [P] [US1] Author the Project-Initializer Agent prompt at `agents/prompts/project_initializer.md` (invokes upstream `specify init` mechanics inside `projects/<PROJ-ID>/`, derives the project's `.specify/memory/constitution.md` from the research-project constitution template at `agents/templates/research_project_constitution.md` with project-specific token substitution per FR-012)
- [X] T044 [US1] Implement Project-Initializer Agent at `src/llmxive/agents/project_initializer.py` — uses `src/llmxive/speckit/runner.py::init_speckit_in("projects/<PROJ-ID>/")`, applies the constitution template by substituting `{{project_id}}`, `{{title}}`, `{{field}}`, `{{date}}`, and `{{principal_agent_name}}` from project state (FIX U3); transitions project to `project_initialized`
- [X] T045 [P] [US1] Author Specifier Agent prompt at `agents/prompts/specifier.md` (drives `/speckit.specify` for the project's Spec Kit scaffold; invokes `projects/<PROJ-ID>/.specify/scripts/bash/create-new-feature.sh --json`)
- [X] T046 [US1] Implement Specifier Agent at `src/llmxive/speckit/specify_cmd.py` — extends `SlashCommandAgent` from T022; reads the fleshed-out idea, writes `projects/<PROJ-ID>/specs/001-<short-name>/spec.md`, transitions project to `specified`
- [X] T047 [P] [US1] Author Clarifier Agent prompt at `agents/prompts/clarifier.md` (drives `/speckit.clarify`; resolves `[NEEDS CLARIFICATION]` markers via primary-source verification — uses Reference-Validator if a marker concerns an external claim — escalates to `human_input_needed` after the configured number of unresolved attempts)
- [X] T048 [US1] Implement Clarifier Agent at `src/llmxive/speckit/clarify_cmd.py`; transitions project to `clarified` on success or `human_input_needed` on cap-hit
- [X] T049 [P] [US1] Author Planner Agent prompt at `agents/prompts/planner.md` (drives `/speckit.plan`; invokes `setup-plan.sh --json`, produces `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`)
- [X] T050 [US1] Implement Planner Agent at `src/llmxive/speckit/plan_cmd.py`; transitions project to `planned`
- [X] T051 [P] [US1] Author Tasker Agent prompt at `agents/prompts/tasker.md` (drives `/speckit.tasks` followed immediately by `/speckit.analyze`; for each issue analyze surfaces, edits the upstream artifact and re-runs analyze; cap iterations at `TASKER_MAX_REVISION_ROUNDS` from T019; on cap-hit transitions project to `human_input_needed`)
- [X] T052 [US1] Implement Tasker Agent at `src/llmxive/speckit/tasks_cmd.py` AND `src/llmxive/speckit/analyze_cmd.py`; the Tasker orchestrates both per FR-015. Transitions project to `analyzed` on clean analyze report
- [X] T053 [P] [US1] Author Implementer Agent prompt at `agents/prompts/implementer.md` (drives `/speckit.implement`; completes as many tasks from `tasks.md` as fit within the leaf wall-clock budget; persists progress per-task; the very next scheduled run resumes from the next incomplete task)
- [X] T054 [US1] Implement Implementer Agent at `src/llmxive/speckit/implement_cmd.py`; transitions project to `in_progress` on first task; transitions to `research_complete` when the last `tasks.md` checkbox is checked
- [X] T055 [US1] Add `project_initializer`, `specifier`, `clarifier`, `planner`, `tasker`, `implementer` entries to `agents/registry.yaml` with their prompt paths, budgets, and backend chains

#### Lifecycle wiring

- [X] T056 [US1] Extend `src/llmxive/agents/lifecycle.py` LangGraph with the US1 transitions (`brainstormed`→`flesh_out_in_progress`→`flesh_out_complete`→`project_initialized`→`specified`→`clarify_in_progress`→`clarified`→`planned`→`tasked`→`analyze_in_progress`→`analyzed`→`in_progress`→`research_complete`); each transition's allowed source/target enforced
- [X] T057 [US1] Extend `src/llmxive/agents/advancement.py` with the US1 advancement rules (e.g., `analyzed` → `in_progress` requires `analyze` clean; `in_progress` → `research_complete` requires every task in `tasks.md` checked off)
- [X] T058 [US1] Wire all US1 agents into `src/llmxive/pipeline/graph.py` LangGraph orchestration so a single scheduled run advances any one project by one stage when conditions allow
- [X] T059 [US1] Wire `.github/workflows/llmxive-pipeline.yml` to call `python -m llmxive run --max-tasks 5` with the cron and dispatch triggers; the `Status-Reporter Agent` step (added in US9) is stubbed for now

**Checkpoint**: User Story 1 fully functional — a fleshed-out idea fixture advances brainstormed → research_complete across one or more scheduled runs, with every Spec Kit slash command driven by a dedicated agent.

---

## Phase 4: User Story 2 — Implementer agents preferentially resume incomplete work (Priority: P1)

**Goal**: When multiple projects are eligible, an Implementer Agent picks `in_progress` projects before `analyzed` projects; multiple Implementer Agents in successive scheduled runs collaborate on the same project without re-running completed tasks.

**Independent Test**: Pre-stage two projects — one with three of five tasks complete, one freshly `analyzed`. Run the scheduler. Confirm the `in_progress` project is picked first and the next-incomplete task is the one worked.

### Implementation for User Story 2

- [X] T060 [US2] Extend `src/llmxive/pipeline/scheduler.py` (started in T029) with the full FR-001 priority order — `in_progress > analyzed > clarified > specified > flesh_out_complete > brainstormed > paper_in_progress > paper_analyzed > paper_clarified > paper_specified > paper_drafting_init > research_complete` — and the within-tier oldest-`updated_at` rule (FR-006). Add **integration** test `tests/integration/test_scheduler_priority.py` using fixture `state/projects/` files (no LLM call; pure priority verification — distinct from real-call tests, since this is fixture-driven; FIX A1, FIX I3)
- [X] T061 [US2] Extend `src/llmxive/speckit/implement_cmd.py` (T054) to read `tasks.md` plus prior run-log entries to find the first incomplete task; never re-run a task already marked complete; record per-task completion in the run-log so successive scheduled runs continue forward
- [X] T062 [US2] Real-call test `tests/real_call/test_resume_progression.py` — runs the pipeline twice on the same fixture project and asserts each run completes a different next-incomplete task

**Checkpoint**: Multiple Implementer-Agent runs collaborate on one project; in_progress projects always pre-empt fresh analyzed projects.

---

## Phase 5: User Story 3 — Research-quality reviewers vote on implemented projects (Priority: P1)

**Goal**: Once a project hits `research_complete`, Research-Reviewer Agents read the implementation, write review records with one of {`accept`, `minor_revision`, `full_revision`, `reject`}, and accumulate votes. The Advancement-Evaluator routes to the corresponding next stage.

**Independent Test**: Stage a `research_complete` fixture project. Run several Research-Reviewer Agents. Confirm review records appear under `projects/<PROJ-ID>/reviews/research/`, point totals are computed correctly, and the most-weighted recommendation determines the next stage.

### Implementation for User Story 3

- [X] T063 [P] [US3] Author Research-Reviewer Agent prompt at `agents/prompts/research_reviewer.md` (reads the project's implementation — code, data, results — and emits a structured review with verdict in {accept, minor_revision, full_revision, reject})
- [X] T064 [US3] Implement Research-Reviewer Agent at `src/llmxive/agents/research_reviewer.py`; writes review records under `projects/<PROJ-ID>/reviews/research/<agent-name>__<YYYY-MM-DD>__research.md` with frontmatter validated against `contracts/review-record.schema.yaml`
- [X] T065 [US3] Add `research_reviewer` entry to `agents/registry.yaml`
- [X] T066 [US3] Extend `src/llmxive/agents/advancement.py` (T028, T057) with the research-review rules per `research.md` R5: group by verdict, sum weighted votes, advance to `research_accepted` only when accept-votes ≥ `RESEARCH_ACCEPT_THRESHOLD` (T019), else route to the corresponding revision stage. Self-review is rejected: skip review records where `reviewer_name == produced_by_agent`
- [X] T067 [US3] Extend `src/llmxive/agents/lifecycle.py` (T056) with `research_complete`→`research_review`→{`research_accepted` | `research_minor_revision` | `research_full_revision` | `research_rejected`} transitions
- [X] T068 [US3] Implement revision routing: `research_minor_revision` re-invokes the Tasker Agent with a synthesized revision-task brief from reviewer feedback; `research_full_revision` resets project to `clarified` with reviewer prompt attached to the spec; `research_rejected` snapshots the project under `projects/<PROJ-ID>/.rejected/<timestamp>/` and resets to `brainstormed` (no scaffolding deletion — preserve git history)
- [X] T069 [US3] Real-call test `tests/real_call/test_research_review_flow.py` — feeds three deliberately-different fixture implementations (good / minor-flaws / fundamental-flaws) through the reviewer pool and asserts each gets routed to the expected next stage

**Checkpoint**: Research-quality voting works end-to-end with all four route paths verified.

---

## Phase 6: User Story 4 — Paper drafting is its own Spec Kit pipeline (Priority: P1)

**Goal**: For a `research_accepted` project, a paper Spec Kit pipeline runs at `projects/<PROJ-ID>/paper/.specify/`, with paper-focused agents driving `/speckit.specify`, `/clarify`, `/plan`, `/tasks`, `/analyze`, `/implement` for the paper artifact, plus specialist sub-agents for writing, figures, statistics, lit-search, reference verification, proofreading, and LaTeX build/fix.

**Independent Test**: Take a `research_accepted` fixture project; run the paper pipeline end-to-end; confirm `projects/<PROJ-ID>/paper/specs/001-paper/{spec,plan,tasks}.md` exist, `analyze` is clean, the LaTeX compiles to PDF, every cited reference is verified, and the proofreader's flag list is empty.

### Implementation for User Story 4 (paper Spec Kit drivers)

- [ ] T070 [P] [US4] Author Paper-Initializer Agent prompt at `agents/prompts/paper_initializer.md` (scaffolds `projects/<PROJ-ID>/paper/.specify/` from upstream Spec Kit; derives `paper/.specify/memory/constitution.md` from `agents/templates/paper_project_constitution.md` per FR-013)
- [ ] T071 [US4] Implement Paper-Initializer Agent at `src/llmxive/agents/paper_initializer.py`; transitions project to `paper_drafting_init`
- [ ] T072 [P] [US4] Author Paper-Specifier prompt at `agents/prompts/paper_specifier.md` (drives `/speckit.specify` for the paper artifact: defines sections, required figures, claim list, target venue style)
- [ ] T073 [US4] Implement Paper-Specifier Agent at `src/llmxive/speckit/paper_specify_cmd.py`; transitions to `paper_specified`
- [ ] T074 [P] [US4] Author Paper-Clarifier prompt at `agents/prompts/paper_clarifier.md`
- [ ] T075 [US4] Implement Paper-Clarifier Agent at `src/llmxive/speckit/paper_clarify_cmd.py`; transitions to `paper_clarified`
- [ ] T076 [P] [US4] Author Paper-Planner prompt at `agents/prompts/paper_planner.md`
- [ ] T077 [US4] Implement Paper-Planner Agent at `src/llmxive/speckit/paper_plan_cmd.py`; transitions to `paper_planned`
- [ ] T078 [P] [US4] Author Paper-Tasker prompt at `agents/prompts/paper_tasker.md` (same analyze-resolve loop discipline as the research-stage Tasker, FR-016)
- [ ] T079 [US4] Implement Paper-Tasker Agent at `src/llmxive/speckit/paper_tasks_cmd.py` (reuses the Tasker's analyze-resolve infrastructure from T052); transitions to `paper_tasked` then `paper_analyzed`

### Implementation for User Story 4 (paper sub-agents)

- [ ] T080 [P] [US4] Author Writing-Agent prompt at `agents/prompts/paper_writing.md` (composes prose for one section/subsection at a time; reuses `lit_search` tool from T041)
- [ ] T081 [US4] Implement Writing-Agent at `src/llmxive/agents/paper_writing.py`
- [ ] T082 [P] [US4] Author Figure-Generation-Agent prompt at `agents/prompts/paper_figure_generation.md` (generates Python plotting code that runs in the code sandbox; output PDF/PNG into `projects/<PROJ-ID>/paper/figures/`)
- [ ] T083 [US4] Implement Figure-Generation-Agent at `src/llmxive/agents/paper_figure_generation.py` using the code sandbox (T088)
- [ ] T084 [P] [US4] Author Statistics-Agent prompt at `agents/prompts/paper_statistics.md` (performs and writes interpretations of inferential analyses on real data outputs; runs analysis code in sandbox)
- [ ] T085 [US4] Implement Statistics-Agent at `src/llmxive/agents/paper_statistics.py`
- [ ] T086 [P] [US4] Author Proofreader-Agent prompt at `agents/prompts/proofreader.md` (flags repeated sections, internal inconsistencies, jargon overuse, logical issues; emits a structured flags report)
- [ ] T087 [US4] Implement Proofreader-Agent at `src/llmxive/agents/proofreader.py`
- [ ] T088 [P] [US4] Implement code-execution sandbox at `agents/tools/code_sandbox.py` (subprocess.Popen with wall-clock timeout `SANDBOX_BUDGET_SECONDS` from T019; captures stdout/stderr; SIGKILL on timeout; per-project virtualenv populated from the project's pinned requirements; used by Figure-Generation, Statistics, and any code-running task)
- [ ] T089 [P] [US4] Implement LaTeX-Build Agent prompt at `agents/prompts/latex_build.md` (compiles LaTeX → PDF via `pdflatex`; captures errors; produces `projects/<PROJ-ID>/paper/pdf/<paper>.pdf` on success)
- [ ] T090 [US4] Implement LaTeX-Build Agent at `src/llmxive/agents/latex_build.py` and the LaTeX-Fix prompt at `agents/prompts/latex_fix.md` + agent at `src/llmxive/agents/latex_fix.py` (repairs compile errors and re-invokes Build; project escalates to `human_input_needed` after configurable repeated-failure cap)
- [ ] T091 [P] [US4] Author Paper-Implementer dispatcher prompt at `agents/prompts/paper_implementer.md` (drives `/speckit.implement` for the paper Spec Kit; the Paper-Tasker emits each task with a `kind:` field whose value is one of the paper-task taxonomy: `prose`, `figure`, `statistics`, `lit-search`, `reference-verification`, `proofread`, `latex-build`, `latex-fix`. The dispatcher routes each task to the matching sub-agent: prose→Writing-Agent, figure→Figure-Generation-Agent, statistics→Statistics-Agent, lit-search→Lit-Search tool wrapper, reference-verification→Reference-Validator, proofread→Proofreader-Agent, latex-build→LaTeX-Build, latex-fix→LaTeX-Fix; FIX U4)
- [ ] T092 [US4] Implement Paper-Implementer dispatcher at `src/llmxive/speckit/paper_implement_cmd.py`; transitions to `paper_in_progress`; transitions to `paper_complete` when ALL of the following are simultaneously true: every task in the paper's `tasks.md` is checked AND the LaTeX builds (T090) AND the Proofreader flag list is empty (T087) AND every paper-stage citation has `verification_status=verified` (T107). This conjunction satisfies SC-011 (FIX C8); satisfies FR-026 (citation verification gate)
- [ ] T093 [US4] Add all US4 agents (`paper_initializer`, `paper_specifier`, `paper_clarifier`, `paper_planner`, `paper_tasker`, `paper_implementer`, `paper_writing`, `paper_figure_generation`, `paper_statistics`, `proofreader`, `latex_build`, `latex_fix`) to `agents/registry.yaml`
- [ ] T094 [US4] Extend `src/llmxive/agents/lifecycle.py` (T056, T067) with paper-stage transitions: `research_accepted`→`paper_drafting_init`→`paper_specified`→`paper_clarified`→`paper_planned`→`paper_tasked`→`paper_analyzed`→`paper_in_progress`→`paper_complete`
- [ ] T095 [US4] Real-call test `tests/real_call/test_paper_pipeline_e2e.py` — fixture `research_accepted` project advances through every paper-stage agent; asserts compiled PDF exists, every figure was generated from real data, every citation is verified

**Checkpoint**: Paper Spec Kit pipeline produces a compiled PDF + figures + verified bibliography end-to-end on a fixture.

---

## Phase 7: User Story 5 — Paper reviewers vote on the final draft (Priority: P1)

**Goal**: Once a project hits `paper_complete`, Paper-Reviewer Agents vote with one of {`accept`, `minor_revision`, `major_revision_writing`, `major_revision_science`, `fundamental_flaws`}. The Advancement-Evaluator routes accordingly.

**Independent Test**: Stage a `paper_complete` fixture; run several Paper-Reviewer Agents; assert each recommendation type routes the project to the correct next stage.

### Implementation for User Story 5

- [ ] T096 [P] [US5] Author Paper-Reviewer Agent prompt at `agents/prompts/paper_reviewer.md` (reads compiled PDF + LaTeX source; emits structured review)
- [ ] T097 [US5] Implement Paper-Reviewer Agent at `src/llmxive/agents/paper_reviewer.py`; writes review records under `projects/<PROJ-ID>/paper/reviews/<agent-name>__<YYYY-MM-DD>__paper.md`
- [ ] T098 [US5] Add `paper_reviewer` entry to `agents/registry.yaml`
- [ ] T099 [US5] Extend `src/llmxive/agents/advancement.py` (extends T028, T057, T066; FIX D2) with paper-review rules: group by verdict, sum weighted votes, advance to `paper_accepted` when accept-votes ≥ `PAPER_ACCEPT_THRESHOLD` (T019), else route per most-weighted recommendation (`paper_minor_revision` → re-invoke Paper-Tasker; `paper_major_revision_writing` → reset to `paper_clarified`; `paper_major_revision_science` → reset to `clarified` (research pipeline) with reviewer feedback attached; `paper_fundamental_flaws` → snapshot under `.rejected/` and reset to `brainstormed`)
- [ ] T100 [US5] Extend `src/llmxive/agents/lifecycle.py` with `paper_complete`→`paper_review`→{five outcomes} transitions and the final `paper_accepted`→`posted` transition
- [ ] T101 [US5] Real-call test `tests/real_call/test_paper_review_flow.py` — five fixture papers (one per recommendation type) advance to the expected next stage

**Checkpoint**: All five paper-review routing paths verified.

---

## Phase 8: User Story 6 — Free-backend operation with cost-aware fallbacks (Priority: P1)

**Goal**: A clean fork with only `DARTMOUTH_CHAT_API_KEY` and `HF_TOKEN` configured runs the entire pipeline end-to-end; cost estimate is $0.00.

**Independent Test**: Provision a fork with only the free secrets; run a full scheduled workflow; confirm every agent succeeds and the run summary reports zero paid-API calls.

### Implementation for User Story 6

- [ ] T102 [US6] Add a Dartmouth-quota-error detector to `src/llmxive/backends/dartmouth.py` (T020) that classifies HTTP 429 / quota-exceeded responses; the router falls back to HF Inference (FR-019)
- [ ] T103 [US6] Add a `cost_estimate_usd` calculator that reports `0.0` for every free-backend invocation; the run-log writer (T014) refuses to write any entry with `cost_estimate_usd > 0` unless the agent's `paid_opt_in: true` (registry contract enforces `paid_opt_in: const false` in v1, so any non-zero is a contract violation; FR-020)
- [ ] T104 [US6] Real-call test `tests/real_call/test_free_backend_only.py` — runs a small fixture pipeline with `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` explicitly unset; asserts every agent succeeds and `cost_estimate_usd == 0.0` in every run-log entry
- [ ] T105 [US6] Real-call test `tests/real_call/test_dartmouth_outage_falls_back.py` — primary path: induce a real Dartmouth 429 by exhausting an isolated test-account daily quota in a dedicated nightly fixture run, then assert the next call routes to HF Inference. Secondary (fast inner-loop) path, gated by env var `LLMXIVE_DARTMOUTH_HEALTHY_OK_TO_MOCK=1`, uses an httpx-level mock that returns 429 — this path runs ONLY in CI when the primary real-429 fixture is unavailable, NEVER in production verification. The real path is the source of truth (Constitution Principle III); the mock path is the secondary fast-feedback layer using identical call syntax (FIX A2, FIX K1)

**Checkpoint**: SC-002 is verifiable in CI; the free-only invariant is enforceable at the contract layer.

---

## Phase 9: User Story 7 — Verified-accuracy guardrails block fabricated references (Priority: P2)

**Goal**: The Reference-Validator Agent runs at three points (research-stage citations, paper-stage citations, and as a final gate before `research_accepted` and `paper_accept`). Citations require both reachability AND title-token-overlap ≥ 0.7. Artifacts with unverified citations are blocked from advancing.

**Independent Test**: Inject a fabricated citation into a fixture paper; confirm the Reference-Validator flags it, the project cannot reach `paper_accepted`, and the failing citation is listed on the project's GitHub issue.

### Implementation for User Story 7

- [ ] T106 [P] [US7] Author Reference-Validator Agent prompt at `agents/prompts/reference_validator.md`
- [ ] T107 [US7] Implement Reference-Validator Agent at `src/llmxive/agents/reference_validator.py` — uses `agents/tools/citation_fetcher.py` (T108) to resolve the citation, computes token-overlap against the cited title/authors with the threshold from T017 (default 0.7), writes outcomes to `state/citations/<PROJ-ID>.yaml` (T017)
- [ ] T108 [P] [US7] Implement citation-fetcher at `agents/tools/citation_fetcher.py` — handles `url` via `httpx`, `arxiv` via `arxiv` package, `doi` via `crossref-commons`, `dataset` via Zenodo/HF datasets API; returns `{fetched_title, fetched_authors, status}`; distinguishes `unreachable` (transient 5xx/timeout) from `mismatch` (200 but title-overlap < threshold)
- [ ] T109 [US7] Add `reference_validator` entry to `agents/registry.yaml`
- [ ] T110 [US7] Wire Reference-Validator into the lifecycle at THREE points (FR-026 says citations must be verified before an artifact earns its **first** review point, so the gate is in three places): (a) automatically at every artifact write that introduces or modifies citations (Specifier, Planner, Implementer, Paper-Specifier, Paper-Implementer); (b) inside the Advancement-Evaluator BEFORE awarding any review point — a review record's score is set to 0.0 if the reviewed artifact has any citation in `unreachable` or `mismatch` status; and (c) as a blocking final gate on the `research_review`→`research_accepted` and `paper_review`→`paper_accepted` transitions per FR-028 (FIX C2, FIX I2)
- [ ] T111 [US7] Real-call test `tests/real_call/test_reference_validator_blocks_fabrication.py` — a fixture paper with one verified arXiv citation + one fabricated citation; assert the fabricated citation is `mismatch`, the project cannot advance, and the GitHub issue comment lists the failing citation
- [ ] T112 [US7] Real-call test `tests/real_call/test_reference_validator_distinguishes_unreachable.py` — a citation against a temporarily-unreachable host; assert outcome is `unreachable`, retry on next scheduled run, and project blocks only after K consecutive `unreachable` runs

**Checkpoint**: SC-004 is verifiable in CI: citations in advanced artifacts have verification rate 100%.

---

## Phase 10: User Story 8 — Real-execution test gate on every PR (Priority: P2)

**Goal**: Every PR that modifies agent code, prompts, Spec Kit templates, or workflow files passes the real-execution CI gate including the full e2e fixture.

**Independent Test**: Open a PR that breaks one agent's prompt template; CI fails fast with a clear message identifying the broken prompt.

### Implementation for User Story 8

- [ ] T113 [P] [US8] Add a `path-filters.yml` to `.github/` driving `dorny/paths-filter@v3` so the real-call workflow only runs when relevant paths change
- [ ] T114 [US8] Extend `.github/workflows/llmxive-real-call-tests.yml` (extends T005 skeleton, then T036 wiring; FIX D1) with: prompt-existence check (every prompt referenced by `agents/registry.yaml` exists and parses), Spec Kit script executability check, backend reachability check, then runs `pytest tests/real_call/` (FR-031)
- [ ] T115 [P] [US8] Add a deliberate-failure smoke test `tests/real_call/test_broken_prompt_fails_fast.py` (gated by env flag `LLMXIVE_DELIBERATE_BREAK=1`, runs locally only) — used to manually verify the CI gate's failure mode
- [ ] T116 [US8] Document the real-call gate in `quickstart.md` step 9 (already drafted) and surface the gate's pass/fail status in PR descriptions via a CI status check name `llmxive-real-call`

**Checkpoint**: SC-009 verifiable: every relevant PR passes the real-execution gate before merge.

---

## Phase 11: User Story 9 — Fast failure signals & resume from any stage (Priority: P3)

**Goal**: Failures surface within seconds via fail-fast preconditions; the next scheduled run resumes from the failed slash command on the affected project.

**Independent Test**: Force a precondition failure (revoke `DARTMOUTH_CHAT_API_KEY`); confirm the run terminates within a small fraction of the timeout with a precondition-specific message; restore the key; confirm the next scheduled run resumes from the failed stage.

### Implementation for User Story 9

- [ ] T117 [P] [US9] Author Status-Reporter Agent prompt at `agents/prompts/status_reporter.md` (produces the workflow run summary listing agents invoked, projects touched, transitions made, citations verified, paid-API calls (expected: 0), total wall time; posts exactly one issue comment per state transition; regenerates `web/data/projects.json` per the `contracts/web-data.schema.yaml` schema)
- [ ] T118 [US9] Implement Status-Reporter Agent at `src/llmxive/agents/status_reporter.py`; runs as the final step of every scheduled workflow
- [ ] T119 [P] [US9] Author Repository-Hygiene Agent prompt at `agents/prompts/repository_hygiene.md` (verifies `.gitignore` blocks `.env*`, no leftover screenshots/scratch dirs at repo root, doc parity between code constants and the about page)
- [ ] T120 [US9] Implement Repository-Hygiene Agent at `src/llmxive/agents/repository_hygiene.py`; runs as a periodic cron job (separate workflow `.github/workflows/llmxive-hygiene.yml`)
- [ ] T121 [P] [US9] Author Task-Atomizer prompt at `agents/prompts/task_atomizer.md` (when a parent task's wall-clock estimate exceeds the agent's leaf budget, decomposes hierarchically; sub-tasks may themselves be re-atomized)
- [ ] T122 [US9] Implement Task-Atomizer at `src/llmxive/agents/atomizer.py` — emits sub-task records under `projects/<PROJ-ID>/code/.tasks/` (research stage) or `projects/<PROJ-ID>/paper/source/.tasks/` (paper stage); each sub-task gets its own run-log entry with `parent_entry_id` set to the atomization parent
- [ ] T123 [P] [US9] Author Task-Joiner prompt at `agents/prompts/task_joiner.md`
- [ ] T124 [US9] Implement Task-Joiner at `src/llmxive/agents/joiner.py` — auto-spawned by the scheduler when the run-log shows every sibling sub-task has `outcome=success`; merges sub-task outputs per the parent's `expected_outputs` declaration; the Joiner emits one run-log entry referencing every sibling's `task_id`. Hierarchical: a level-N Joiner's output becomes input to the level-(N-1) Joiner
- [ ] T125 [US9] Add `status_reporter`, `repository_hygiene`, `task_atomizer`, `task_joiner` entries to `agents/registry.yaml`
- [ ] T126 [US9] Wire `src/llmxive/pipeline/resume.py` (T030) to read the most recent run-log per project and route the next scheduled run to the failed slash command (FR-035); add resume-handling to every Spec-Kit-driving agent's `run()` so they pick up where the previous run left off
- [ ] T127 [US9] Real-call test `tests/real_call/test_failfast_missing_secret.py` — runs the workflow with `DARTMOUTH_CHAT_API_KEY` unset; asserts exit within a small fraction of the timeout with a precondition-specific message
- [ ] T128 [US9] Real-call test `tests/real_call/test_resume_after_midpipeline_failure.py` — interrupts a fixture pipeline at the Tasker stage; confirms the next scheduled run resumes from the Tasker, not from `brainstormed`
- [ ] T129 [US9] Real-call test `tests/real_call/test_atomizer_joiner_hierarchy.py` — a parent task with estimate > leaf budget atomizes; sub-tasks themselves over-budget re-atomize; the Joiner fires only after the last sibling completes

**Checkpoint**: SC-005 verifiable: misconfigured runs terminate within seconds; mid-pipeline failures resume cleanly.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Updates that don't fit cleanly inside a single user story but are required for the refactor to ship.

- [ ] T130 Update `web/about.html` to publish the 30+ stage lifecycle, the new thresholds (`research_accept_threshold`, `paper_accept_threshold`), and the per-stage point requirements; this is the authoritative source consumed by `src/llmxive/config.py` (T019, FR-038)
- [ ] T131 [P] Update `web/index.html` and `web/projects.html` to render data from `web/data/projects.json` per the new schema; verify zero broken links to artifact files after migration (FR-037, SC-010)
- [ ] T132 [P] Document the system in `README.md` at repo root: link to the constitution, the about page, the agent registry, and the quickstart; remove every reference to the legacy `code/llmxive-automation/` tree
- [ ] T133 [P] **Verify** (do not re-edit) that the repository-level `CLAUDE.md` SPECKIT block points to `specs/001-agentic-pipeline-refactor/plan.md`; this was set during the plan phase and a re-edit here would be redundant per Principle I (FIX K3). If verification fails, surface the discrepancy to a human rather than silently overwriting.
- [ ] T134 Run `python -m llmxive preflight` against the fully-built system; assert `OK — ready to run` is printed and the exit code is 0
- [ ] T135 Run `pytest tests/contract/` to confirm every schema validates against fixture objects
- [ ] T136 Run the full `tests/real_call/` suite locally with real secrets to confirm end-to-end success ahead of CI
- [ ] T137 [P] Add `tests/real_call/fixtures/PROJ-TEST-001/` — a minimal end-to-end fixture project (raw idea seed; expected canonical artifacts at every stage) used by T037, T062, T069, T095, T101, T128
- [ ] T138 [P] Performance check: confirm the preflight phase completes in under 60 s on a clean Actions runner (FR-032 measurable target)
- [ ] T139 Run `scripts/migrate_legacy_layout.py` one last time on the merge candidate to confirm idempotence (re-running on already-migrated content is a no-op); commit any residual moves
- [ ] T140 Final cleanup pass — delete stale debug artifacts at the repo root (`pipeline_log.txt`, `=`, `.specify/feature.json` if no longer needed beyond v1, leftover `.claude/` if untracked); run the Repository-Hygiene Agent once before opening the PR
- [ ] T141 [P] Add a 7-day rolling stage-advancement-rate metric to the Status-Reporter Agent (T118): for each scheduled run, compute the count of distinct `current_stage` transitions across all projects in the trailing `STAGE_ADVANCEMENT_RATE_WINDOW_DAYS` window from T019 and surface it in `web/data/projects.json` and the workflow run summary; satisfies SC-001 measurability (FIX C6)
- [ ] T142 [P] Add an SC-007 line-count assertion to the Repository-Hygiene Agent (T120): on each run, recompute the post-migration line count for the new `src/llmxive/**` + `agents/**` trees, compare to the pre-migration baseline captured in `state/migration_metrics.yaml` (T009), and surface the delta in the run summary; assert `post < pre` and emit a CRITICAL run-log entry on regression (FIX C3)
- [ ] T143 [P] Add an SC-008 onboarding-validation step to the Polish phase: a smoke-doc test `tests/integration/test_readme_onboarding.py` that asserts the top-level `README.md` exposes (i) a link to `agents/registry.yaml`, (ii) a link to `agents/prompts/`, and (iii) a one-paragraph "how to find the agent for stage X" recipe — the three items required for a new contributor to identify any agent's prompt within 5 minutes (FIX C4)
- [ ] T144 [P] Add an SC-012 convergence-rate metric to the Status-Reporter Agent (T118): track each project's `revision_round` field (already on `state/projects/<PROJ-ID>.yaml` per the schema) and emit a rolling 30-day distribution in the run summary, asserting that ≥ 95 % of projects converge within 3 rounds; emit a HIGH run-log entry when the rate drops below 90 % (FIX C5)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T001–T010 can mostly parallelize after T002.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Stories (Phases 3–11)**: All depend on Foundational. After Foundational, P1 stories (US1–US6) can in principle start in parallel, BUT in practice US1 must complete first because it establishes the Spec-Kit-driver pattern that US2, US3, US4, US5 extend.
  - **US1 → US2 → US3** (research half: implement → resume → review)
  - **US1 → US4 → US5** (paper half: depends on US1 establishing the per-project Spec Kit driver; paper pipeline reuses the runner and the Tasker analyze-loop)
  - **US6** (free-backend) can run partly in parallel with US1 once the backend chain (T020) is in place
  - **US7** (citations) integrates into US1 (research-stage) and US4 (paper-stage); start it any time after T017
  - **US8** (CI gate) integrates with whatever exists; can start after Foundational and grow as new tests appear
  - **US9** (resume + atomizer/joiner + status-reporter) integrates throughout; the Status-Reporter is needed by US1's workflow wiring (T059), but a stub can ship in US1 and the full agent in US9
- **Polish (Phase 12)**: Depends on all desired user stories.

### User Story Dependencies (concrete)

- **US1 (P1)**: Depends only on Foundational.
- **US2 (P1)**: Depends on US1 (extends the Implementer).
- **US3 (P1)**: Depends on US1 (reviews the artifacts US1 produces).
- **US4 (P1)**: Depends on US1 (reuses the Spec Kit driver pattern); also depends on US3 (paper pipeline starts only when research is `research_accepted`).
- **US5 (P1)**: Depends on US4.
- **US6 (P1)**: Depends only on Foundational.
- **US7 (P2)**: Depends on Foundational (the citation store + token-overlap matcher are foundational); the Reference-Validator agent itself integrates into US1 and US4.
- **US8 (P2)**: Depends on Foundational; grows with each story.
- **US9 (P3)**: Depends on Foundational; the Status-Reporter integrates everywhere.

### Within Each User Story

- Prompts are authored before the agents that consume them.
- Tools and shared utilities (e.g., `lit_search`, `code_sandbox`, `citation_fetcher`) are implemented before the agents that depend on them.
- Lifecycle and Advancement-Evaluator extensions come last in each story, since they tie everything together.
- Real-call tests run last per story to confirm the end-to-end behavior.

### Parallel Opportunities

- All Setup tasks marked [P] (T003, T004, T005, T007, T008, T010) can run in parallel after T002 creates the directory skeleton.
- All Foundational tasks marked [P] (T013, T014, T015, T016, T017, T018, T022, T023, T024, T025, T027, T029, T030, T032, T033, T034, T035) can run in parallel — they're independent files.
- Within each user story, all prompt-authoring tasks marked [P] can run in parallel (T038–T040, T043, T045, T047, T049, T051, T053, T063, T070, T072, T074, T076, T078, T080, T082, T084, T086, T088, T089, T091, T096, T106, T108, T117, T119, T121, T123).
- The three independent free-backend tests (T104, T105, plus US7/US8/US9 backend tests) are parallel-safe.

---

## Parallel Example: User Story 1

```bash
# All US1 prompts can be drafted in parallel:
Task: "Author agents/prompts/brainstorm.md"
Task: "Author agents/prompts/flesh_out.md"
Task: "Author agents/prompts/idea_selector.md"
Task: "Author agents/prompts/project_initializer.md"
Task: "Author agents/prompts/specifier.md"
Task: "Author agents/prompts/clarifier.md"
Task: "Author agents/prompts/planner.md"
Task: "Author agents/prompts/tasker.md"
Task: "Author agents/prompts/implementer.md"

# Then the Spec-Kit-driver implementations (which all extend SlashCommandAgent) can be parallelized too:
Task: "Implement src/llmxive/speckit/specify_cmd.py"
Task: "Implement src/llmxive/speckit/clarify_cmd.py"
Task: "Implement src/llmxive/speckit/plan_cmd.py"
Task: "Implement src/llmxive/speckit/tasks_cmd.py"
Task: "Implement src/llmxive/speckit/implement_cmd.py"

# Lifecycle and Advancement-Evaluator extensions are sequential (they edit the same files):
Task: "Extend src/llmxive/agents/lifecycle.py with US1 transitions"
Task: "Extend src/llmxive/agents/advancement.py with US1 rules"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1
4. **STOP and VALIDATE**: A fleshed-out idea fixture advances brainstormed → research_complete on a single fork.

### Incremental Delivery

1. Setup + Foundational → infra ready.
2. Add US1 → research half MVP (idea → research_complete).
3. Add US2 → multi-run resumability of research.
4. Add US3 → research-quality voting routes projects forward.
5. Add US6 (free backends) — can ship in parallel with US3 since they don't share files.
6. Add US7 (citation guardrails) — integrates retroactively into US1 and US4 once shipped.
7. Add US4 → paper drafting MVP (research_accepted → paper_complete).
8. Add US5 → paper-quality voting routes papers to `posted` or revision paths.
9. Add US8 → CI gate locks all of the above against regression.
10. Add US9 → fail-fast and resumability + atomizer/joiner + status reporter.
11. Polish (Phase 12) → about page, README, web data, final hygiene.

### Parallel Team Strategy

With multiple developers (or multiple Implementer Agents on this very repo using the new pipeline once it's bootstrapped):

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Developer A: US1 (the critical path).
   - Developer B: US6 (free-backend tests + fallback hardening).
   - Developer C: US7 (citation infrastructure; partial integration into US1's Specifier & Implementer once they exist).
3. After US1 is green:
   - Developer A: US2 then US3.
   - Developer B: US4 (paper Spec Kit drivers + sub-agents).
   - Developer C: US8 + US9 (CI gate + observability + atomizer/joiner).
4. Final integration on US5 + Polish before merging the refactor PR.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- [Story] label maps task to specific user story for traceability.
- Each user story is independently completable and testable per the Independent Test description in spec.md.
- Real-call tests are the primary verification path (Constitution Principle III); mocks are not added unless they share calling syntax with a real-path test that demonstrated correctness first.
- Commit after each task or logical group (the constitution requires frequent commits during debugging; this carries over to feature work).
- Stop at any checkpoint to validate a story independently.
- Avoid: vague tasks, same-file conflicts marked [P], cross-story dependencies that break the independent-test promise.
