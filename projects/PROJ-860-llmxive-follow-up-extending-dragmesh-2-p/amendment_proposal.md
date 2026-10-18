# Amendment Proposal – Addition of Paired‑t‑Test Analysis
**Version:** 1.0
**Date:** 2026-10-18
**Authors:** llmXive‑follow‑up team

## Background
The original specification for *Virtual Tactile Zero‑Shot Adaptation* (see
`specs/001-llmxive-follow-up-extending-dragmesh-2-p/spec.md`) includes a statistical
evaluation based on a Generalized Linear Mixed Model (GLMM). While the GLMM
satisfies the requirement for mixed‑effects inference (FR‑005), the
Constitution of the project (Principle VII) also mandates a **direct
paired‑comparison** between the adaptive and static policies to demonstrate
that the adaptive reward scaling yields a measurable improvement on a per‑object
basis.

## Proposed Amendment
- **Add a paired‑t‑test** on the per‑object success rates of the adaptive policy
 versus the static baseline.
- The test will be performed after aggregation of trial results (see
 `code/analysis.py` → `prepare_paired_data`).
- The paired‑t‑test result (t‑statistic, p‑value, mean difference) will be
 recorded in `data/results/t_test_summary.json` and incorporated into the
 final experiment summary (`data/logs/experiment_summary.json`).
- The analysis script `code/analysis/statistical_test.py` will be extended to
 invoke `perform_paired_ttest` from `code/analysis.py` and to include the
 t‑test outcome in the generated report.

## Rationale
- **Constitution Principle VII** requires that any statistical claim be
 supported by at least one direct hypothesis test. A paired‑t‑test provides a
 clear, interpretable metric of improvement that complements the GLMM’s
 fixed‑effect inference.
- The paired design respects the experimental protocol (identical objects,
 identical initial conditions) and thus isolates the effect of the adaptive
 reward scheduler.
- The test’s significance threshold will be `p < 0.05`, matching the GLMM
 requirement and ensuring consistency across statistical evaluations.

## Impact on Existing Artifacts
- **`code/analysis/statistical_test.py`** – will import and call the new
 `perform_paired_ttest` function, then write the JSON summary.
- **`data/results/t_test_summary.json`** – new artifact containing the
 paired‑t‑test results.
- **`data/logs/experiment_summary.json`** – will now include the field
 `t_test_p` (p‑value from the paired‑t‑test) alongside `p_value` (GLMM) and
 other metrics.

## Versioning & Traceability
- This amendment is versioned as **1.0**. Future revisions (e.g., changing
 the significance threshold or adding additional post‑hoc tests) will increment
 the minor version (e.g., 1.1, 1.2) and be recorded in this document.
- All changes introduced by this amendment will be logged in the project’s
 reproducibility audit (`code/audit_reproducibility.py`) to maintain a
 verifiable change history.

## Acceptance Criteria
1. The paired‑t‑test script runs without error on the aggregated results
 (`data/results/sweep.csv`).
2. `data/results/t_test_summary.json` is created and contains the keys
 `t_statistic`, `p_value`, and `mean_difference`.
3. The experiment summary (`data/logs/experiment_summary.json`) includes the
 new `t_test_p` field.
4. The amendment document is present at the repository root as
 `amendment_proposal.md` and is versioned as shown above.