# Final Code Review Checklist

**Project**: PROJ-026-the-influence-of-visual-complexity-on-im
**Task**: T058 - Final Code Review
**Date**: 2026-06-29

This checklist must be verified before merging the feature branch into the main pipeline. All items must be checked off.

## 1. Task Completion Verification
- [ ] All tasks in `tasks.md` are marked as `[X]` (completed).
- [ ] No tasks remain in a "pending" or "failed" state in the project state file (`state/projects/PROJ-026-the-influence-of-visual-complexity-on-im.yaml`).
- [ ] The `state/projects/PROJ-026-the-influence-of-visual-complexity-on-im.yaml` file has been updated with the current timestamp in `updated_at`.

## 2. Critical Specification Amendments
- [ ] **Amendment-001 Verification**: Confirm `specs/001-the-influence-of-visual-complexity-on-im/amendment-001.md` exists.
- [ ] **Ratified Status**: Verify the file contains the exact line `Status: Ratified`.
- [ ] **Implementation Alignment**: Ensure `code/analysis/permutation.py` implements the Permutation Test (n=1000) as required by the amendment, and does NOT implement Repeated-Measures ANOVA.

## 3. Data Integrity & Synthetic Data Policy
- [ ] **No Synthetic Fallbacks**: Grepping the codebase (specifically `code/data/load.py` and `code/main.py`) confirms there are NO `try/except` blocks that fall back to `generate_synthetic_*` or `mock_*` functions when real data is missing.
- [ ] **Fail-Loud Implementation**: Verify that `code/data/load.py` raises a `RuntimeError` immediately if real data files are missing and the `--null-effect` flag is NOT set.
- [ ] **Real Data Source**: Confirm that any data loading logic points to a verified, real data source (e.g., specific HuggingFace dataset ID or local file path in `data/raw/`) and does not use hardcoded fake rows.

## 4. Output Schema & Artifact Validation
- [ ] **Permutation Results**: `data/results/permutation_results.json` exists and contains keys: `p_value`, `effect_size`, `observed_cohen_d`, `perm_standardized_mean_diff`.
- [ ] **Sensitivity Results**: `data/results/sensitivity_results.json` exists and contains keys: `threshold_sweep`, `loio_results`.
- [ ] **PCA Variance**: `data/results/pca_variance.json` exists and contains `status` (either "ok" or "warning") and cumulative variance metrics.
- [ ] **Visualization**: `data/results/d_score_comparison.png` exists, is non-empty, and matches the expected publication quality (Seaborn boxplot, viridis palette, 95% CI).
- [ ] **Counterbalance Mapping**: `data/processed/counterbalance_assignment.csv` exists and reflects a seeded random shuffle (seed=42) derived from the complexity categories in `data/processed/complexity_scores.csv`.

## 5. Audit Trails & Logging
- [ ] **Counterbalance Log**: `logs/counterbalance_strategy.log` exists and contains the random seed (42) and the split ratio.
- [ ] **Join Report**: `logs/join_report.log` exists and explicitly logs the number of rows successfully joined during the aggregation step.
- [ ] **Exclusion Report**: `logs/exclusion_report.log` exists and lists participants excluded due to insufficient trials (<10).
- [ ] **Permutation Log**: `logs/permutation_run.log` exists and logs the exact seed (42) and iteration count (1000).
- [ ] **Validation Log**: `logs/validation.log` exists and lists valid/invalid images from the stimulus validation step.

## 6. Code Quality & CI
- [ ] **Static Analysis**: `ruff check --fix` and `mypy --strict` passed with exit code 0 for all modules (`code/data/`, `code/stimuli/`, `code/analysis/`, `code/viz/`).
- [ ] **Reproducibility**: The pipeline `python code/main.py --null-effect` produces identical output hashes on consecutive runs (verified by T055).
- [ ] **CI Workflow**: `.github/workflows/analysis.yml` exists and successfully runs the pipeline with the `--null-effect` flag.

## Sign-off
- [ ] **Reviewer Name**: ____________________
- [ ] **Date**: ____________________
- [ ] **Final Decision**: [ ] APPROVED FOR MERGE [ ] REJECTED (See comments below)

*Comments:*
_________________________________________________________
_________________________________________________________