# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 11 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- SC-004 requires bootstrap confidence‑interval half‑width ≤ 0.02, but tasks T007 and T008 verify against a relaxed ≤ 0.05 target, so the success criterion is not met.
- Phase 3 of the plan specifies a *dual* null‑simulation strategy (stratified label shuffling **and** residual permutation). Tasks T005/T006 only implement label shuffling, omitting the residual‑permutation component, leaving the plan element unimplemented.
- Task T001 is marked `[P]` (parallel‑safe) but it creates/updates shared code files (checkpointing utilities, main entry point, and contract schemas). Running this task in parallel could cause race conditions on file writes, violating the parallel‑safety guarantee.
- The `transformed_data.schema.yaml` enumerates the method value as `rank_based`, but T004 describes the transformation function as `apply_rank_inverse_normal` and logs method name `rank_inverse_normal`. This schema‑validation inconsistency will cause task verification to fail.
- Plan.md (Phase 3) specifies a dual null‑simulation strategy (stratified label shuffling **and** residual permutation), but T006 only implements label shuffling. The task therefore does not satisfy the plan’s requirement and will miss the residual‑permutation component.
- SC‑004 (and FR‑009) require bootstrap confidence‑interval half‑width ≤ 0.02, yet T007’s verification checks `ci_half_width ≤ 0.05`. This relaxes the success criterion and creates a mismatch between the specification and the task’s acceptance condition.
- Similarly, T008 validates CI half‑width against ≤ 0.05, contradicting SC‑004’s ≤ 0.02 target. The task’s verification must be aligned with the success criteria defined in the specification.
- Verification for T007 validates CI half‑width ≤ 0.05 for empirical power, but SC‑003 mandates a CI half‑width of ±0.02. This relaxes the success criterion and weakens the specification.
- Verification for T007 validates CI half‑width ≤ 0.05 for empirical power, but SC‑004 (bootstrap CI precision) requires ≤ 0.02. The task’s acceptance condition therefore weakens the required precision.
- Verification for T008 validates CI half‑width ≤ 0.05 for aggregated results, but SC‑004 explicitly requires a bootstrap CI half‑width of ≤ 0.02. This constitutes a weakening of the success criterion.
- The `transformed_data.schema.yaml` enumerates the method value "rank_based", while tasks (T004) refer to the transformation "rank_inverse_normal". This schema‑contract mismatch violates FR‑003, as transformed files would not validate against the declared contract.
