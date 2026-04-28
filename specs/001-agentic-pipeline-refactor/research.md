# Research: Agentic Pipeline Refactor (Spec-Kit-per-Project)

**Date**: 2026-04-28 (revised)
**Status**: Phase 0 complete — every Technical Context unknown resolved.

This document records every framework/library/protocol decision, with
explicit Decision/Rationale/Alternatives blocks. Every external claim
was verified by reading primary sources during spec drafting (Constitution
Principle II).

## R1. Agent framework

**Decision**: LangChain 0.3.x + LangGraph 0.2.x.

**Rationale**:
- `langchain-dartmouth ≥ 0.3.1` ships `ChatDartmouth(ChatOpenAI)` —
  inherits from `langchain_openai.chat_models.ChatOpenAI`, so
  `bind_tools()`, structured output, streaming, and every other
  ChatOpenAI affordance work without extra glue. Verified by reading
  [`src/langchain_dartmouth/llms.py`](https://github.com/dartmouth-libraries/langchain-dartmouth/blob/main/src/langchain_dartmouth/llms.py)
  (lines 18 and 430).
- LangGraph provides a typed `StateGraph` with checkpointers — a
  natural fit for a 25-stage lifecycle that must resume from any
  failed stage (FR-035).
- One framework, one source of truth (Principle I).

**Alternatives considered**:
- HF Python tiny-agents: rejected because the constructor's `provider`
  parameter is restricted to a fixed enum and does not accept a custom
  OpenAI-compatible base_url. Targeting Dartmouth Chat would require
  forking the upstream Agent class.
- Project-native minimal orchestrator: rejected because rolling our
  own state graph and tool dispatcher duplicates LangGraph.

## R2. Spec Kit integration model

**Decision**: Each research project is an **independent Spec Kit
project** under `projects/<PROJ-ID>/`, with its own `.specify/`
scaffold, distinct from the repository-level meta `.specify/`. Specialist
agents drive each Spec Kit slash command by combining (a) the
mechanical bash script (headless, accepts `--json`) and (b) the
slash command's authored prompt template (fetched from upstream
`.claude/skills/speckit-*/SKILL.md`).

**Rationale**:
- Spec Kit's README explicitly states the slash commands are
  "agent-driven, not CLI-driven"; there is no `specify run plan`
  binary. The bash scripts (`create-new-feature.sh`,
  `setup-plan.sh`, `check-prerequisites.sh`) ARE headless and accept
  `--json`. Therefore, the path to driving Spec Kit programmatically
  is: agent invokes script + agent runs LLM with the slash-command
  prompt template + agent commits the resulting artifacts.
- Per-project independence keeps each project's spec/plan/tasks at
  the canonical Spec Kit location, so any Spec-Kit-aware tool
  (including a future `specify analyze` upgrade) works on each project
  without modification.
- Principle I is preserved because the *implementation* of "drive a
  slash command" is a single class hierarchy
  (`src/llmxive/speckit/slash_command.py`); only the *content* (each
  project's spec/plan/tasks) is per-project, which is unavoidable.

**Verified facts** (from [github/spec-kit README](https://github.com/github/spec-kit)):
- Slash commands: `/speckit.constitution`, `/speckit.specify`,
  `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`,
  `/speckit.analyze`, `/speckit.implement`, `/speckit.checklist`,
  `/speckit.taskstoissues`.
- Install: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@<tag>`.
- Per-project layout: `.specify/{memory,scripts,specs,templates}/`.

**Alternatives considered**:
- **Single repo-wide Spec Kit project**: rejected because every
  research project's spec/plan/tasks would collide in one
  `.specify/specs/` directory; we'd lose Spec Kit's cross-artifact
  consistency (each `analyze` would consider unrelated projects).
- **Detached git worktrees per project**: rejected for v1 — adds
  worktree management cost; revisit if subdirectory `.specify/`
  scaffolds turn out to interfere.
- **Submodules per project**: rejected — adds cloning ceremony,
  fragments `git log` audit trail (Principle I).

## R3. Mechanical-script vs slash-command-prompt division

**Decision**: For each Spec-Kit-driving agent
(`Specifier`, `Clarifier`, `Planner`, `Tasker`, `Implementer`, and
their paper-stage analogs), the agent's runtime does:

1. Invoke the relevant bash script (e.g., `create-new-feature.sh
   --json --short-name <name> "<description>"`) and parse the JSON
   output.
2. Load the slash-command's authored prompt template from upstream
   Spec Kit (`.claude/skills/speckit-<command>/SKILL.md`) — referenced
   by path, never copied (Principle I).
3. Construct the agent's input by templating: the project's current
   state + the slash-command prompt + any relevant existing
   artifacts.
4. Call the LLM via the configured backend chain.
5. Parse the LLM's output and write artifacts to the project's
   canonical Spec Kit paths.
6. Append a structured run-log entry.

**Rationale**:
- Keeps Spec Kit upstream as a dependency, not a fork (Principle I —
  no parallel implementations).
- The mechanical script is the source of truth for branching, file
  numbering, and state mutation; we never reimplement it.
- The slash-command prompt is the source of truth for *what* the
  agent should produce; we drive it through our backend chain instead
  of through a chat session.

**Alternatives considered**:
- **Reimplement slash-command logic in Python**: rejected — duplicates
  upstream maintenance burden; violates Principle I.
- **Run an embedded Claude Code session per slash command**: rejected
  — bloats the runner image, requires API access we don't need (we
  call LLMs directly via LangChain).

## R4. Lifecycle stage machine

**Decision**: Implement the 25+ lifecycle states (FR-003) as a single
LangGraph `StateGraph` with the Advancement-Evaluator Agent as the
sole writer of `current_stage`. Stage transitions are pure functions
of (current_stage, project_state, review_records), making them
deterministic and testable.

**Rationale**:
- Principle I — exactly one writer of stage transitions.
- Principle V — fail fast at the transition: an invalid combination
  (e.g., advancing a project to `paper_drafting_init` without research
  acceptance) raises a precondition error, never silently passes.
- LangGraph's checkpointer makes each transition a recoverable
  checkpoint, supporting FR-035 resume-from-failure.

**Alternatives considered**:
- A simpler explicit state-transition table in YAML: workable for v1
  but loses LangGraph's checkpoint/resume semantics; rejected since
  resume is a hard requirement.

## R5. Reviewer voting & vote weighting

**Decision**: Each Research-Reviewer or Paper-Reviewer Agent emits one
review record with a single recommendation. Vote weights follow the
existing point system (LLM 0.5, human 1.0). Aggregation:

- Group review records by recommendation type.
- Sum weighted votes per recommendation.
- The recommendation with the highest weighted total is the
  "winning" recommendation.
- For research: `accept` requires reaching the about-page accept
  threshold (sum of accept votes ≥ research-accept-threshold) before
  the project advances; otherwise the winning recommendation routes
  the project to the corresponding revision path.
- For paper: same pattern with paper-accept-threshold.

**Rationale**:
- Threshold gating ensures multiple reviewers agree before
  advancement (defense against a single rogue accept).
- Per-recommendation routing for non-accept cases handles the case
  where the reviewer pool agrees on a recommendation type but no
  single recommendation reaches the accept threshold.
- Self-review prohibition (FR Edge Case) is enforced at write time:
  the Advancement-Evaluator skips review records where
  `reviewer_name == artifact.produced_by_agent`.

**Alternatives considered**:
- Plurality (winner-takes-all) without an accept threshold:
  rejected — single LLM accept could prematurely advance a project.
- Borda or Condorcet voting: rejected as overkill for a 4-or-5-way
  vote; the threshold-plus-plurality scheme is simpler and well-
  understood.

## R6. Idea-generation & flesh-out

**Decision**: A Brainstorm Agent produces lightweight, single-paragraph
idea notes. A Flesh-Out Agent expands them into structured idea
documents with: research question, brief related-work summary
(produced via the Lit-Search-Agent tool), expected results, and
required methodology. The Idea-Selector Agent (rule-based + lightweight
LLM ranking) decides which fleshed-out ideas to promote to per-project
Spec Kit initialization.

**Rationale**:
- Two-stage idea generation prevents low-effort raw ideas from
  consuming Spec Kit setup cost; only fleshed-out ideas (with
  context, motivation, and references) become projects.
- Flesh-Out's reliance on Lit-Search ensures every promoted idea is
  grounded in actual related work (Principle II); duplicate detection
  at flesh-out time uses semantic similarity against existing project
  ideas.

**Alternatives considered**:
- One-stage brainstorm-to-spec: rejected because Spec Kit
  initialization is cheap but spec-clarify-plan-tasks-analyze is
  expensive; we don't want to spend that cost on shallow ideas.

## R7. LLM backend strategy

(Carried forward from prior revision.)

**Decision**: Dartmouth Chat (default) → HF Inference (free fallback)
→ local Transformers/llama.cpp on the runner (last-resort fallback for
the smallest agents). All free; paid backends opt-in only and
schema-blocked by default.

## R8. Dartmouth model identifier resolution

**Decision**: Resolve at runtime via `ChatDartmouth.list()` and
`CloudModelListing.list()`; never hardcode model name strings.

**Rationale** (carried forward): the `langchain-dartmouth` README
states "For a list of available models, check the respective
`list()` method of each class"; the user's named targets
(`gpt-oss-120b`, `gemma-3-27b`, a Qwen variant) could not be
verified verbatim, and per Principle II we MUST NOT hardcode unverified
strings.

## R9. Tool calling vs MCP

**Decision**: Native LangChain `bind_tools()` with Pydantic-typed tool
schemas. No MCP servers in v1.

(Rationale carried forward.)

## R10. Pipeline scheduling and orchestration runtime

**Decision**: GitHub Actions cron at `0 */3 * * *` (every 3 hours)
invoking `python -m llmxive run`. State machine in LangGraph with a
file-backed checkpointer reading/writing
`state/projects/<PROJ-ID>.yaml`. Per-project advisory lock
(`state/locks/<PROJ-ID>.lock`) is held for the duration of any
mutating run.

## R11. Long-running tasks: Atomizer / Joiner

**Decision**: Cap every agent task at a configurable wall-clock budget
(default 5 minutes per leaf task). Tasks whose estimate exceeds the
budget are passed through the Task-Atomizer Agent, which decomposes
recursively. The Task-Joiner Agent auto-spawns when the last sibling
sub-task completes.

## R12. Code-execution sandbox & figure generation

**Decision**: `subprocess.run` inside the GitHub Actions runner with a
strict per-execution wall-clock timeout (default 4 minutes).
Per-project `code/` working directory; per-run virtualenv populated
from the project's pinned `requirements.txt`. Figure-generation runs
in the same sandbox using `matplotlib`/`seaborn`/`plotly`; figure
outputs go to `projects/<PROJ-ID>/paper/figures/`.

**Rationale**: The runner is a fresh ephemeral VM per scheduled run;
no Docker-in-Docker needed (Principle IV).

## R13. State persistence: files vs database

**Decision**: All pipeline state is files committed to the repo —
YAML for human-readable state, JSON Lines for append-only run-logs,
zero-byte sentinel files for advisory locks.

(Rationale carried forward — auditability + zero infra cost.)

## R14. Stage thresholds — single source of truth

**Decision**: Stage thresholds live in `web/about.html`. At preflight,
a parser extracts numbers and writes them to `src/llmxive/config.py`'s
constants. New thresholds for the Spec-Kit-per-project model
(research-review accept threshold, paper-review accept threshold)
MUST be added to the about page in this PR (FR-038).

## R15. Reference-Validator behavior

**Decision**: For each citation, fetch the primary source (HTTP for
URLs, arXiv API for arXiv IDs, DOI resolver for DOIs, dataset registry
for dataset IDs). Verify both *reachability* and *match* (cited title
or first author appears in fetched metadata). Token-overlap ≥ 0.7 to
mark `verified`. Distinguish `unreachable` from `mismatch` for retry
behavior.

## R16. Real-call CI test design

**Decision**: A separate `tests/real_call/` directory, gated by
`LLMXIVE_REAL_TESTS=1`. CI runs the full e2e fixture pipeline on every
PR that touches `src/llmxive/`, `agents/`, or `.github/workflows/`.

## R17. Migration of existing artifacts

**Decision**: A one-shot `scripts/migrate_legacy_layout.py` moves every
existing `technical_design_documents/<id>/`,
`implementation_plans/<id>/`, and `papers/<id>/` into the canonical
`projects/<PROJ-ID>/` Spec-Kit-per-project layout. Generated
`state/projects/<PROJ-ID>.yaml` files reflect each migrated project's
current stage on the new lifecycle (e.g., a project with a finished
design doc but no plan starts at `clarified`). Legacy directories are
deleted in the same PR (Principle I).

## R18. Web interface continuity

**Decision**: The web pages continue to read project data from JSON
files generated by the Status-Reporter Agent. The about page is
updated in this PR to:

- Document the 25+ lifecycle stages and the Spec-Kit-per-project model.
- Set thresholds for research-review accept and paper-review accept.
- Provide a single source of truth for code to parse.

(Rationale carried forward — generated JSON layer between agent state
and the static site preserves Principle I across the web/internal
boundary.)
