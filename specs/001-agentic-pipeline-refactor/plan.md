# Implementation Plan: Agentic Pipeline Refactor (Spec-Kit-per-Project)

**Branch**: `001-agentic-pipeline-refactor` | **Date**: 2026-04-28 (revised) | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-agentic-pipeline-refactor/spec.md`

## Summary

Replace the monolithic `code/llmxive-automation/` orchestrator with a
LangGraph-based pipeline of specialist agents that each drive one
GitHub **Spec Kit** slash command (`/speckit.constitution`, `specify`,
`clarify`, `plan`, `tasks`, `analyze`, `implement`) inside an
**independent Spec Kit project per research effort**. Each project's
research lifecycle is a Spec Kit pipeline at
`projects/<PROJ-ID>/.specify/`; after research-quality review accepts the
implementation, an analogous paper Spec Kit pipeline runs at
`projects/<PROJ-ID>/paper/.specify/`. Specialist sub-agents handle
paper-specific tasks (writing, figure generation, statistics, literature
search, reference verification, proofreading, LaTeX build/fix). Two
review stages — research-quality and paper-quality — each route projects
to an `accept`, `minor_revision`, `major_revision_*`, or `reject`
recommendation per weighted vote. Backends default to Dartmouth Chat via
`langchain-dartmouth` with Hugging Face fallback; runs are scheduled by
GitHub Actions cron jobs; state is persisted as files under `state/` for
audit via `git log`.

## Technical Context

**Language/Version**: Python 3.11 (matches GitHub Actions hosted runners' default; aligns with `langchain-dartmouth` 0.3.x and `langchain` 0.3.x)
**Primary Dependencies**:
  - LLM/agent framework: `langchain ≥ 0.3`, `langgraph ≥ 0.2`, `langchain-dartmouth ≥ 0.3.1`, `langchain-huggingface ≥ 0.1`, `huggingface_hub`
  - Spec Kit: `specify-cli` (installed via `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@<pinned-tag>`); the per-project bash scripts (`create-new-feature.sh`, `setup-plan.sh`, `check-prerequisites.sh`) are the headless interface our agents call
  - Data validation: `pydantic ≥ 2`, `jsonschema`
  - Operational: `tenacity` (retry/backoff), `pyyaml` (agent registry & state files), `httpx` (citation validator), `gitpython` (commit-from-Actions), `arxiv` (arXiv API), `crossref-commons` (DOI metadata)
  - Paper-stage: `matplotlib`, `seaborn`, `numpy`, `scipy`, `pandas` (figure-generation and statistics agents); `pylatex` or direct `subprocess` to `pdflatex`
  - Testing/lint: `pytest ≥ 8`, `pytest-asyncio`, `ruff`, `mypy`
**Storage**: Files committed to the repository — no database. State files: `state/projects/<PROJ-ID>.yaml`, `state/run-log/<YYYY-MM>/<run-id>.jsonl`, `state/locks/<PROJ-ID>.lock`, `state/citations/<PROJ-ID>.yaml`. Project artifacts under `projects/<PROJ-ID>/` (research Spec Kit) and `projects/<PROJ-ID>/paper/` (paper Spec Kit), each with their own `.specify/` and `specs/` subdirectories
**Testing**: `pytest` for unit and integration; a dedicated `tests/real_call/` suite that exercises real Dartmouth Chat and HF Inference endpoints (Constitution Principle III); a `tests/fixtures/` tree with one minimal end-to-end project that runs from `brainstormed` through `research_complete` on every PR
**Target Platform**: Ubuntu 22.04/24.04 GitHub Actions hosted runners (free tier); web interface served from `web/` via GitHub Pages
**Project Type**: Single Python project + per-project Spec Kit scaffolds + static web interface + GitHub Actions workflow definitions
**Performance Goals**: Cron firing → first agent invocation in under 60 s (fail-fast preconditions). Average advancement of one project per scheduled run (SC-001). Per-task wall-clock budget configurable; default 5 minutes per leaf task. Tasker `analyze`-then-resolve loop converges within 3 rounds for 95 %+ of projects (SC-012)
**Constraints**: $0 paid-API spend (Constitution Principle IV; SC-002); fits within GitHub Actions free-tier minutes; every external citation verified against primary source before earning a review point (Constitution Principle II); single source of truth for prompts, agents, project layouts, and constitutions (Constitution Principle I); no fork of upstream Spec Kit
**Scale/Scope**: ~30 specialist agents in the registry (idea-generation, per-project Spec Kit drivers, sub-agents for paper implementation, reviewers, cross-cutting); ~50 prompt templates; ~10–50 active projects; cron every 3 hours

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) defines five principles. Each gate below MUST pass before proceeding.

### Principle I — Single Source of Truth (NON-NEGOTIABLE)

- ✅ **PASS**: One canonical agent registry (`agents/registry.yaml`)
  declares every agent. One canonical prompts directory
  (`agents/prompts/`) holds every prompt template. Two canonical
  constitution templates (`agents/templates/research_project_constitution.md`
  and `agents/templates/paper_project_constitution.md`) are the only
  source for per-project constitutions. Spec Kit slash-command prompts
  are referenced from upstream Spec Kit's `.claude/skills/speckit-*/`
  paths — never copied. The legacy `code/llmxive-automation/` tree is
  deleted (FR-023). Per-project artifacts live exactly once under
  `projects/<PROJ-ID>/`.

### Principle II — Verified Accuracy (NON-NEGOTIABLE)

- ✅ **PASS**: The Reference-Validator Agent runs at three points
  (research-stage citations, paper-stage citations, and as a final
  blocking gate before `research_accepted` and `paper_accept`).
  Citations require both reachability AND title-token-overlap ≥ 0.7
  with the primary source (defends against 200-OK-but-mismatched
  fakes). Dartmouth model identifiers resolved at runtime via
  `ChatDartmouth.list()` (FR-022).

### Principle III — Robustness & Reliability (Real-World Testing)

- ✅ **PASS**: `tests/real_call/` issues real LLM calls against free
  Dartmouth Chat and HF Inference endpoints (FR-029). The end-to-end
  fixture pipeline (`brainstormed → research_complete`) runs on every
  PR that touches the orchestrator or any Spec-Kit-driving agent
  (FR-030).

### Principle IV — Cost Effectiveness (Free-First)

- ✅ **PASS**: Default backend = Dartmouth Chat (free for Dartmouth
  community members). Fallback = Hugging Face Inference (free tier).
  Local inference on the Actions runner for the smallest agents.
  `agents/registry.yaml` schema asserts `is_paid: const false` for
  every backend and `paid_opt_in: const false` for every agent —
  schema-level enforcement of the principle (FR-020).

### Principle V — Fail Fast

- ✅ **PASS**: A unified fail-fast preamble (target completion under
  60 s) verifies every required secret, every required tool on PATH
  (`git`, `pdflatex`, `uv`/`uvx`/`pipx`), every required input file's
  existence and parseability, and network reachability for required
  backends (FR-032). Per-task wall-clock budgets are enforced before
  the task starts; the Task-Atomizer pre-decomposes over-budget tasks.

### Operational standards (from constitution's Additional Constraints section)

- ✅ Repository hygiene: legacy debug artifacts at the repo root
  (`pipeline_log.txt`, `=`, scratch directories) are removed in this
  PR; the Repository-Hygiene Agent enforces ongoing cleanliness.
- ✅ Secrets: only `DARTMOUTH_CHAT_API_KEY`, `DARTMOUTH_API_KEY`,
  `HF_TOKEN`, and `GITHUB_TOKEN` are referenced; `.gitignore` blocks
  `.env*`.
- ✅ Documentation parity: `web/about.html` is updated in this PR to
  reflect the Spec-Kit-per-project lifecycle (FR-037, FR-038); code
  reads thresholds from a single parser.
- ✅ Dependency tracking: one `requirements.txt` (or `pyproject.toml`)
  is updated in this PR.
- ✅ Project structure: per-project canonical layout enforced
  (FR-025).
- ✅ Identifiers: `PROJ-###-descriptive-name` used everywhere.

**Gate verdict (Phase 0 entry): PASS — proceed to Phase 0.**

### Post-design re-check (after Phase 1 artifacts complete)

After generating [`research.md`](research.md), [`data-model.md`](data-model.md),
[`contracts/`](contracts/), and [`quickstart.md`](quickstart.md), every
gate is re-verified:

- **Principle I (SSoT)**: Every Spec Kit slash command's mechanical
  script is invoked from exactly one wrapper module
  (`src/llmxive/speckit/runner.py`). Slash-command prompt templates
  are referenced from upstream paths only. Agent registry is one file.
  Constitution templates are two files. Still **PASS**.
- **Principle II**: Reference-Validator contract requires both
  reachability and token-overlap ≥ 0.7. Cross-field invariants
  enforced in pydantic. Still **PASS**.
- **Principle III**: `tests/real_call/test_full_pipeline_e2e.py` is
  first-class; `tests/fixtures/PROJ-TEST-001/` exists as a minimal
  brainstorm-to-research-complete project. Still **PASS**.
- **Principle IV**: Schema constants asserting `is_paid: const false`
  and `paid_opt_in: const false`. Cost field enforced ≥ 0 with v1
  invariant `== 0`. Still **PASS**.
- **Principle V**: Preflight is a first-class entry point; agent
  budgets bounded by schema (`maximum: 1800`). Still **PASS**.

**Post-design gate verdict: PASS — ready for `/speckit.tasks`.**

## Project Structure

### Documentation (this feature)

```text
specs/001-agentic-pipeline-refactor/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agent-registry.schema.yaml
│   ├── run-log-entry.schema.json
│   ├── review-record.schema.yaml
│   ├── project-state.schema.yaml
│   ├── citation.schema.yaml
│   └── web-data.schema.yaml
├── checklists/
│   └── requirements.md
└── tasks.md   (output of /speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
agents/                                  # Single canonical agent system
├── registry.yaml                        # Every agent declared here (FR-007)
├── templates/                           # System-wide constitution templates (FR-012, FR-013)
│   ├── research_project_constitution.md
│   └── paper_project_constitution.md
├── prompts/                             # Single canonical prompt library (FR-024)
│   ├── brainstorm.md
│   ├── flesh_out.md
│   ├── idea_selector.md
│   ├── project_initializer.md
│   ├── specifier.md                     # drives /speckit.specify
│   ├── clarifier.md                     # drives /speckit.clarify
│   ├── planner.md                       # drives /speckit.plan
│   ├── tasker.md                        # drives /speckit.tasks + /speckit.analyze
│   ├── implementer.md                   # drives /speckit.implement
│   ├── research_reviewer.md
│   ├── paper_initializer.md
│   ├── paper_specifier.md
│   ├── paper_clarifier.md
│   ├── paper_planner.md
│   ├── paper_tasker.md
│   ├── paper_writing.md
│   ├── paper_figure_generation.md
│   ├── paper_statistics.md
│   ├── lit_search.md
│   ├── reference_validator.md
│   ├── proofreader.md
│   ├── latex_fix.md
│   ├── paper_reviewer.md
│   ├── status_reporter.md
│   ├── repository_hygiene.md
│   ├── task_atomizer.md
│   └── task_joiner.md
└── tools/                               # In-process tool implementations
    ├── github_io.py
    ├── citation_fetcher.py              # arXiv / DOI / URL fetcher with token-overlap check
    ├── code_sandbox.py                  # subprocess sandbox with timeout
    ├── latex_build.py
    └── lit_search.py                    # Semantic Scholar / arXiv / OpenAlex queries

src/llmxive/                             # Core Python package (single source of truth)
├── __init__.py
├── config.py                            # constants parsed from web/about.html
├── backends/
│   ├── base.py
│   ├── dartmouth.py                     # ChatDartmouth wrapper + list() integration
│   ├── huggingface.py
│   ├── local.py
│   └── router.py
├── speckit/                             # Headless interface to upstream Spec Kit
│   ├── __init__.py
│   ├── runner.py                        # invokes mechanical scripts (create-new-feature.sh, setup-plan.sh, check-prerequisites.sh) and parses --json output
│   ├── slash_command.py                 # base class wrapping (mechanical script + LLM-driven slash-command prompt)
│   ├── constitution_cmd.py              # /speckit.constitution
│   ├── specify_cmd.py
│   ├── clarify_cmd.py
│   ├── plan_cmd.py
│   ├── tasks_cmd.py
│   ├── analyze_cmd.py
│   └── implement_cmd.py
├── agents/
│   ├── base.py                          # Agent base class (LangGraph node)
│   ├── runner.py                        # invokes one agent, writes run-log
│   ├── lifecycle.py                     # 25+ stage state machine
│   ├── advancement.py                   # rule-based, non-LLM stage transitions
│   ├── atomizer.py
│   └── joiner.py
├── pipeline/
│   ├── __init__.py
│   ├── graph.py                         # LangGraph state graph
│   ├── scheduler.py                     # picks next project per FR-001 priority
│   ├── lock.py                          # per-project advisory lock
│   └── resume.py                        # resume from failed slash command
├── state/
│   ├── project.py
│   ├── runlog.py
│   ├── reviews.py
│   └── citations.py
├── tools/
│   ├── github.py                        # gh CLI wrapper
│   ├── git_commit.py
│   ├── citations.py                     # title-overlap matcher
│   └── sandbox.py
├── preflight.py                         # FR-032 fail-fast preamble
├── cli.py                               # python -m llmxive entry point
└── types.py                             # pydantic schemas matching contracts/

state/                                   # Committed pipeline state (auditable via git log)
├── projects/<PROJ-ID>.yaml
├── run-log/<YYYY-MM>/<run-id>.jsonl
├── locks/<PROJ-ID>.lock
└── citations/<PROJ-ID>.yaml

projects/<PROJ-ID>/                       # Research Spec Kit (per FR-011, FR-025)
├── .specify/                            # research-stage Spec Kit scaffold
│   ├── memory/constitution.md           # derived from agents/templates/research_project_constitution.md
│   ├── scripts/, templates/             # standard Spec Kit content
├── specs/001-<short-name>/              # Spec Kit feature directory
│   ├── spec.md
│   ├── plan.md
│   ├── tasks.md
│   ├── research.md, data-model.md, quickstart.md
│   └── contracts/
├── code/, data/                         # research artifacts produced by /speckit.implement
├── reviews/research/                    # research-quality reviews
└── paper/                               # paper Spec Kit (created post-research-accept)
    ├── .specify/
    │   └── memory/constitution.md       # derived from agents/templates/paper_project_constitution.md
    ├── specs/001-paper/
    │   ├── spec.md, plan.md, tasks.md, etc.
    ├── figures/
    ├── source/                          # LaTeX sources
    ├── pdf/                             # compiled PDFs
    └── reviews/                         # paper-quality reviews

tests/
├── unit/
├── integration/
├── real_call/                           # Constitution III: real Dartmouth + HF + e2e fixture
│   ├── test_dartmouth_chat.py
│   ├── test_hf_fallback.py
│   ├── test_speckit_scripts_headless.py
│   ├── test_full_pipeline_e2e.py
│   └── fixtures/PROJ-TEST-001/
├── contract/
└── conftest.py

.github/workflows/
├── llmxive-pipeline.yml                 # cron every 3 hours; runs `python -m llmxive run`
├── llmxive-real-call-tests.yml          # PR check: runs tests/real_call/
└── llmxive-pages.yml                    # publishes web/ to GitHub Pages

web/
├── index.html
├── about.html                           # FR-037: updated to document the 25+ lifecycle stages
└── projects.html
```

**Structure Decision**: Single Python project at `src/llmxive/` with the
agent registry, prompt library, and constitution templates at `agents/`.
Each research project is its own Spec Kit scaffold under
`projects/<PROJ-ID>/`; each paper is its own Spec Kit scaffold under
`projects/<PROJ-ID>/paper/`. Pipeline state lives as plain files under
`state/` for `git log` auditability. The legacy `code/llmxive-automation/`
tree is deleted (FR-023). Upstream Spec Kit is consumed via its bash
scripts (headless) plus its slash-command prompts (referenced, not
copied).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No Constitution violations to justify — all five gates pass. The
Spec-Kit-per-project model adds nesting (each project carries its own
`.specify/`), but each scaffold is independent of the parent — they
share neither memory nor templates with the meta-system, and the
duplication is *content-level* (each project legitimately has its own
spec/plan/tasks), not *implementation-level*, so Principle I is
preserved.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-|-|-|
| (none) | (none) | (none) |
