# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Plan Phase 7 declares significance only if p < 0.05 AND ΔMAE ≥ 0.1 log-TOF (MID), while spec FR-008/SC-001 and contracts/performance_summary.schema.yaml define significance as p < 0.05 AND ΔR² ≥ 0.02. The plan introduces a third, different criterion (ΔMAE) that no contract or spec defines, and the plan's own FR-008 row claims '✅' while describing the spec rule. Pick one rule and make plan, spec, and performance_summary.schema.yaml agree.
- Two overlapping dataset schemas disagree: dataset.schema.yaml uses `entry_id` and `is_excluded` (hash of composition+facet only), while aligned_dataset.schema.yaml and data-model.md use `catalyst_id` and `excluded_from_training` (hash includes synthesis_condition). No plan element designates which is the SSoT; Phase 11 tests only aligned_dataset.schema.yaml, leaving dataset.schema.yaml an orphan contract with no exercising plan element (violates plan↔contract coverage and Principle I/IV).
