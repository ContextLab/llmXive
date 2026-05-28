# Contract — Review-Intake Triage (`src/llmxive/convergence/triage.py`)

Stage-aware triage that turns human/personality reviews into **advisory inputs** (never gates). Implements spec FR-021…023.

## API

```python
def triage(
    review_text: str,
    *,
    stage_context: str,          # the project's current stage (lenses derived from its ReviewSpec)
    source: Literal["human", "personality"],
    author: str,                 # github handle, or persona name (keeps the "(simulated)" suffix)
    model: str = "qwen.qwen3.5-122b",
) -> TriageRecord: ...
```

## Behavior
1. **Quality filter** (FR-021a): deterministic (non-empty, parseable) + an LLM judgment that the review is evidence-based, specific, and relevant to the project. Fail → `quality_pass=False`, `mapped_lenses=[]`, ignored.
2. **Safety/on-topic filter** (FR-022): family-friendly + safe + on-topic (reuses the `safety_ethics` reviewer's criteria as the rubric). Fail → `safe_on_topic=False`, excluded from the publication log.
3. **Aspect-mapping** (FR-021b): map the review to the current stage's lens(es) (from `reviewspec_for(stage_context)`). Matched lens reviewers receive `review_text` as an extra advisory input in their R1/R3 prompt. Unmapped but quality+safe+on-topic → routed to the step's generic reviewer, else recorded-but-not-actioned.
4. **Preservation** (FR-022): `preserved = quality_pass ∧ safe_on_topic`. Preserved reviews are copied to the project's review log and included in the publication review log; non-preserved are excluded (with `excluded_reason`).
5. Large reviews are routed through `summarize` before being handed to a reviewer.

## Producers
- The personality cron (`agents/personality.py:tick`) keeps writing review `.md` files; they now flow through `triage` (advisory), not point-scoring (FR-023). The `(simulated)` suffix is preserved.
- Human GitHub issue comments flow through the **same** `triage` (one SSoT path).

## Non-goals
Triage NEVER directly advances or blocks a stage and NEVER awards points. It only informs the LLM panel that holds the unanimous gate.
