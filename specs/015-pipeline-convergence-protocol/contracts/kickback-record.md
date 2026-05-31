# Contract — Kickback Record & Adaptive Routing (`src/llmxive/convergence/kickback.py`)

Adaptive, severity-driven kickback that replaces BOTH existing revision-routing schemes (graph transient stages + advancement.py spec-012). Implements spec FR-014, FR-034.

## API

```python
def route_kickback(
    spec: ReviewSpec,
    unresolved: list[Concern],
    *,
    project: Project,
) -> KickbackRecord:
    """Pick the worst unresolved severity, map it to a prior stage via spec.kickback_routing,
    and emit a fully-provenanced KickbackRecord."""
```

## Routing rule
1. `worst = max(c.severity for c in unresolved)` (Severity order: trivial < code < writing < requirement < methodology < science < fatal).
2. `to_stage = spec.kickback_routing[worst]` (per the ReviewSpec registry table). Code-level severities on the research/paper-implement units are resolved **in-loop** (re-dispatch the reviser), not kicked back.
3. Emit `KickbackRecord{from_stage, to_stage, worst_severity, unresolved_concerns, artifact_links (all artifacts + every review), reason (plain-language non-convergence explanation), created_at}`.
4. The record is persisted with the project and carried forward so the next worker has full provenance (FR-014). `advancement.py` reads the `ConvergenceResult`, applies `route_kickback` on non-convergence, and writes `current_stage = to_stage` (it no longer scores points).

## Collapse of the two legacy schemes (discrepancy #6 / #51)
- DELETE the hardcoded transient-stage routing block in `graph._decide_next_stage` (`paper_minor_revision→paper_tasked`, etc.).
- DELETE `advancement.py` point scoring (`_award_review_points`, threshold comparisons, `_winning_recommendation` majority vote).
- The single SSoT routing path is `ConvergenceResult` → (`next_stage` if converged) | (`route_kickback().to_stage` if not).
- Existing revision `Stage` values (e.g. `RESEARCH_MINOR_REVISION`, `PAPER_MAJOR_REVISION_*`) are reused as kickback targets where they map cleanly; the convergence-based path supersedes the spec-012 `PAPER_REVISION_IN_PROGRESS`/`READY_FOR_IMPLEMENTATION` dual scheme.

## Invariants
- A kickback ALWAYS carries every unresolved concern + links to every artifact/review involved + a human-readable reason (no opaque kickbacks).
- There is no global kickback cap (FR-017); each kickback is recorded with a `ProgressRecord` so non-improving cycles are inspectable.
