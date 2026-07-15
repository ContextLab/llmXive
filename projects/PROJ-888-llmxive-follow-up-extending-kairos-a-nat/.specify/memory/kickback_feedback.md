# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T028 (stats.py) prioritizes 'Bayesian Hierarchical Model (BHM)' as the primary method, but FR-005 and Constitution Principle VII explicitly mandate 'paired t-test or Wilcoxon signed-rank test' as the primary validation. The task order implies BHM is the default, creating a semantic dependency violation where the required frequentist test is demoted to secondary or omitted, breaking the spec's statistical contract.
- Task T027 (metrics.py) implements error growth for '100, 500, and 1000 steps', but FR-004 and SC-001 explicitly require horizons of '100, 250, and 500 steps'. The task order omits the 250-step horizon (a required data artifact) and adds an unrequested 1000-step horizon, violating the data-flow dependency for the specific success criteria defined in the spec.
- Task T018 (download weights) is a hard dependency for T019 (kairos_adapter) and T020 (training_loop). However, T018 has no fallback strategy for the 'Assumption about model weights' (spec.md). If T018 fails, the entire US2/US3 pipeline blocks. The task order treats this as a standard setup task rather than a critical path risk with a required contingency (e.g., synthetic baseline or graceful skip), violating the 'Reproducibility' principle which requires the pipeline to run on a fresh environment.
- Task T029 (sensitivity analysis) specifies a sweep across 'low, medium, and high' levels. SC-005 requires a sweep in '4-bit increments' (4, 8, 12, 16). The task description is ambiguous and may result in a data artifact that does not satisfy the specific granularity required by the success criterion, creating a potential gap in the analysis output.
