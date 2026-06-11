# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

llmXive is an automated platform for scientific discovery: a registry of
specialist LLM agents — with occasional human guidance — advances ideas from a
one-paragraph brainstorm to a peer-reviewed paper, committing every artifact,
review, and decision to git. Two pipelines (research and paper) drive each
project through a ~34-state lifecycle scaffolded with GitHub Spec Kit.

Governance lives in the constitution
([.specify/memory/constitution.md](.specify/memory/constitution.md)) — six
principles: Single Source of Truth, Verified Accuracy, Real-World Testing,
Cost Effectiveness (Free-First), Fail Fast, and Convergent Review.

## Repository Architecture

- **`src/llmxive/`**: the Python package — agents, backends (Dartmouth Chat +
  local transformers), pipeline/state machinery, claims verification layer
  (specs 016–020), librarian, convergence engine, audits. Installable via
  `pip install -e ".[dev]"` (Python ≥ 3.11).
- **`agents/registry.yaml`**: the SINGLE source of truth for agent → prompt /
  model / backend / budget assignments (~50 agents). Prompts live in
  `agents/prompts/`. All registry models must be free
  (`paid_opt_in: false`; enforced by `tests/unit/test_config_consistency.py`).
- **`projects/`**: one directory per research project
  (`PROJ-###-descriptive-name`) holding `idea/`, specs, code, data, paper,
  and reviews for that project.
- **`state/`**: canonical machine state — run logs, claims registry,
  librarian + judge caches, convergence cache, revisions.
- **`specs/`**: Spec Kit feature specs for llmXive itself (the platform);
  the highest-numbered spec is the most recent work.
- **`web/`** is the dashboard source; **`docs/`** is its deployed copy,
  regenerated wholesale from `web/` by the Pages workflow — never hand-edit
  `docs/`. `web/data/projects.json` is built by `src/llmxive/web_data.py`
  from canonical state.
- **`papers/`**, **`notes/`**, **`infra/`**, **`scripts/`**: papers + audit
  artifacts, dated engineering notes, deployment helpers, maintenance scripts.

## Key Workflows

### Project status management
- Each reviewable stage runs an identify → revise → re-review convergence
  cycle with its LLM panel; advancement requires **unanimous panel
  acceptance** within the 3-round per-step cap, else adaptive kickback to the
  prior stage (spec 015 / Constitution VI). There is NO accumulated point
  system; do not re-introduce one. Human and simulated-personality reviews
  are advisory inputs routed through stage-aware triage.
- Review records are written under `projects/<id>/reviews/` (research) and
  `projects/<id>/paper/reviews/` (paper) as
  `<reviewer_name>__<YYYY-MM-DD>__<stage>.md` with YAML frontmatter validated
  against the review-record contract.

### Claims and verified accuracy
- Every factual claim in generated artifacts is detected, registered,
  resolved against a real source, and cached (`src/llmxive/claims/`,
  `state/claims/`; specs 016–020). Empirical results must trace to
  harness-signed receipts (`src/llmxive/results/`) — never hallucinated.
- All references must be validated against the live source (download/fetch,
  not memory) before commit.

### Testing
- `pytest tests/unit tests/contract tests/integration` — offline suites.
- `LLMXIVE_REAL_TESTS=1 pytest tests/real_call` — real-call suites
  (Constitution III: no mocks as the primary path). Heavy modules carry the
  `slow` marker; the per-PR CI gate runs `-m "not slow"`, nightly runs all.
- Real LLM calls need `DARTMOUTH_CHAT_API_KEY`; without Dartmouth access,
  the `local` transformers backend exercises the identical router path
  (e.g. `LLMXIVE_JUDGE_TEST_BACKEND=local`).
- Prompt changes (`agents/prompts/**`) are gated by the promptfoo eval in
  `eval/promptfoo/` (`.github/workflows/prompt-eval.yml`), whose assertions
  reuse the production parsers.

## Working with the Repository

- Single Source of Truth: before adding any function/config/prompt, search
  for an existing equivalent; modify in place, delete dead code, or refactor
  to a shared helper (Constitution I).
- When code changes, update the corresponding docs (README, docstrings,
  website text) in the same commit; when dependencies change, update
  `pyproject.toml`.
- Run the full verification suite before pushing; if tests fail repeatedly,
  fix the code — do not weaken the tests.
- Use GitHub issues for all project tracking and communication.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
[specs/023-pipeline-e2e-completion/plan.md](specs/023-pipeline-e2e-completion/plan.md).
<!-- SPECKIT END -->
