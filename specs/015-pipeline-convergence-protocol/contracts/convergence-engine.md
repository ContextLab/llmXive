# Contract — Convergence Engine (`src/llmxive/convergence/engine.py`)

Generic SSoT engine implementing identify→revise→re-review (spec FR-009…018). Generalizes the 8/12-panel + `rereview_block` machinery; the bespoke tasker Mode-A/B loop is refactored INTO it.

## API

```python
def run_convergence(
    spec: ReviewSpec,
    project: Project,
    *,
    max_rounds: int = 3,
    per_round_budget_s: float | None = None,   # FR-013 per-round wall-clock budget
    advisory_inputs: list[TriageRecord] | None = None,
) -> ConvergenceResult: ...
```

`Reviewer` and `Reviser` are Protocols (callables):

```python
class Reviewer(Protocol):
    name: str            # lens, e.g. "plan.methodology"
    def identify(self, artifacts: dict[str, str], *, constitution: str | None,
                 advisory: list[str]) -> list[Concern]: ...                 # R1
    def rereview(self, artifacts: dict[str, str], own_concerns: list[Concern],
                 responses: list[ConcernResponse], *, constitution: str | None,
                 advisory: list[str]) -> list[Verdict]: ...                  # R3

class Reviser(Protocol):
    def revise(self, artifacts: dict[str, str], concerns: list[Concern]
               ) -> tuple[dict[str, str], list[ConcernResponse]]: ...        # R2
```

## Round loop (FR-010…013)
1. **R1 (identify)** — every reviewer raises `Concern`s. Overflowing artifact inputs are routed through `summarize` with `spec.overflow_goal`; the constitution is included from `specified` onward (`spec.constitution_input`).
2. If zero critical concerns → `converged=True`, `next_stage` set, return.
3. **R2 (revise)** — `spec.reviser.revise(...)` addresses **every** concern, runs a self-consistency pass, emits `ConcernResponse` per concern (+ a change-log).
4. **R3 (re-review)** — each reviewer judges only its **own** concerns against the responses. An R1-accepter re-reviews only if R2 changed an artifact relevant to its lens; dissenters always re-review (FR-012). Stale verdicts (artifact changed since judged) and self-review (reviewer==producer) are detected and never count as a pass (FR-018, fixes `_produced_by` stub).
5. **Converge test** — all reviewers `pass` → `converged=True`, advance. Else iterate `[R2→R3]`.
6. **Cap** — after `max_rounds` rounds without unanimous pass → `converged=False`, emit `KickbackRecord` (see `kickback-record.md`), set `kickback`.

## Honesty + persistence (FR-015, FR-016)
- `ConvergenceResult.converged` ALWAYS reflects the real R3 outcome — never `True`/`passed` when concerns remain (fixes the spec-014 masked non-convergence).
- The full concern/response/verdict trail is persisted (replaces `tasker_rounds.yaml`) and an inspection record + a run-log entry are written **per round** (FR-050/051).

## No global cap (FR-017)
The engine enforces only the per-step `max_rounds` cap. It does not track or enforce a global kickback budget; `ProgressRecord`s let callers observe (but not abort) non-improving cycles. Genuine reviewer/reviser/backend failures raise → routed to `human_input_needed`/`*_blocked` (fail-fast), distinct from convergence exhaustion.

## Adapters
Existing agents wrap into `Reviewer`/`Reviser`: `ResearchReviewerAgent` (8 lenses) and `PaperReviewerAgent` (12 lenses) → reviewers; speckit revisers (`specifier`+`clarifier`, `planner`, `tasker` Mode-B, `implementer`, paper twins) → revisers. New early-step panels are prompt-driven reviewers under `agents/prompts/panels/`.
