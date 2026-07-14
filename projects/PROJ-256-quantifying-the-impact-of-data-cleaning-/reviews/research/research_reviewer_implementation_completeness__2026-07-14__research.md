---
action_items:
- id: 213f140c57a7
  severity: writing
  text: Consolidate all logic from t022_save_cleaned_datasets.py, t023_reanalyze_cleaned_variants.py,
    t027_run_comparison.py, t030_dataset_size_sensitivity.py, t032_permutation_null_fpr.py,
    t033_outlier_threshold_sweep.py, t034_generate_forest_plot.py, t035_generate_ci_heatmap.py,
    t036_pvalue_shift_reporting.py, t037_ci_width_reporting.py, t038_effect_size_reporting.py,
    t039_log_excluded_datasets.py, t040_create_comparison_report.py, t041_generate_final_report.py,
    t044_runtime_profiling.py, t045_conditi
- id: c9e83ec045e6
  severity: writing
  text: Ensure code/main.py imports and calls these functions directly to form a single,
    runnable pipeline.
- id: 0792c2741b39
  severity: writing
  text: Delete the standalone t0*.py scripts once their logic is migrated.
- id: 2a82b2198747
  severity: writing
  text: Verify code/cleaning.py contains the full implementation of T017-T021 (IQR,
    imputation, recoding) and not just imports from cleanup_utils.py.
artifact_hash: 21385be9ff6aabb87c4cf55fcdf382d57dcae8502dde76fbe91c17f85b06fa72
artifact_path: projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-14T16:02:16.129366Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_completeness
score: 0.0
verdict: minor_revision
---

The project passes the execution gate, but a rigorous trace of `tasks.md` against the provided code listing reveals critical gaps where tasks marked `[x]` have no corresponding implementation logic in the main modules, relying instead on fragmented, standalone scripts that do not constitute a complete, integrated pipeline.

**1. Missing Core Implementation in `code/cleaning.py` (Tasks T017-T021)**
`tasks.md` marks T017 (IQR outlier removal), T018-T020 (imputation strategies), and T021 (categorical recoding) as complete. However, the provided `code/cleaning.py` (6071 bytes) is not shown in full, but the file listing reveals a suspicious proliferation of standalone scripts (`t022_save_cleaned_datasets.py`, `t023_reanalyze_cleaned_variants.py`) and a file named `cleanup_utils.py` (9366 bytes).
*   **Defect**: The plan specifies a unified `code/cleaning.py` module. The presence of `cleanup_utils.py` and separate `t02*` scripts suggests the logic for T017-T021 is either missing from `cleaning.py` or duplicated/fragmented.
*   **Evidence**: `tasks.md` T022 requires writing cleaned datasets to `data/processed/`. The file `t022_save_cleaned_datasets.py` exists, but `code/cleaning.py` (the designated location per plan) is not confirmed to contain the `apply_iqr_outlier_removal` or `apply_knn_imputation` functions. If `cleaning.py` only contains stubs or imports from `cleanup_utils.py` without the actual logic, the task is incomplete.
*   **Action**: Verify `code/cleaning.py` contains the full implementation of T017-T021. If logic is in `cleanup_utils.py`, move it to `cleaning.py` or update `tasks.md` to reflect the new file structure. Ensure no logic is left in standalone `t02*.py` scripts that are not imported by the main pipeline.

**2. Missing Core Implementation in `code/analysis.py` (Tasks T012, T023, T030)**
`tasks.md` T012 (baseline analysis) and T023 (re-run tests on cleaned data) are marked done.
*   **Defect**: The file `t023_reanalyze_cleaned_variants.py` (5135 bytes) exists as a standalone script. The plan requires `code/analysis.py` to handle statistical tests.
*   **Evidence**: If `code/analysis.py` does not contain the `run_t_test` and `run_linear_regression` functions that are called by the main pipeline, and instead relies on `t023_reanalyze_cleaned_variants.py` as a separate entry point, the pipeline is not "wired up" as a single callable module. The existence of `t023_*.py` suggests the implementation was split into ad-hoc scripts rather than integrated into `analysis.py`.
*   **Action**: Consolidate the logic from `t023_reanalyze_cleaned_variants.py` into `code/analysis.py`. Ensure `code/main.py` (987 bytes) imports and calls these functions directly, rather than executing separate scripts.

**3. Missing Core Implementation in `code/reporting.py` (Tasks T027-T041)**
`tasks.md` T027 (metrics comparison), T031 (bootstrap), T032 (permutation), T033 (threshold sweep), and T034-T038 (visualizations/reporting) are marked done.
*   **Defect**: The file listing shows a massive fragmentation of these tasks into individual scripts: `t027_run_comparison.py`, `t030_dataset_size_sensitivity.py`, `t032_permutation_null_fpr.py`, `t033_outlier_threshold_sweep.py`, `t034_generate_forest_plot.py`, `t035_generate_ci_heatmap.py`, `t036_pvalue_shift_reporting.py`, `t037_ci_width_reporting.py`, `t038_effect_size_reporting.py`.
*   **Evidence**: `tasks.md` T027-T041 explicitly require implementation in `code/reporting.py`. The presence of 12 separate `t03*.py` scripts indicates that `code/reporting.py` (6858 bytes) likely contains only stubs or imports, while the actual logic resides in these fragmented scripts. This violates the "wired up" requirement; the pipeline is a collection of scripts, not a cohesive module.
*   **Action**: Refactor the logic from `t027_*.py` through `t038_*.py` into `code/reporting.py`. The `code/main.py` script must orchestrate these functions. The standalone `t03*.py` scripts should be deleted or converted to unit tests.

**4. Truncation/Fragmentation Risk**
The sheer number of `t0*.py` scripts (T013, T022, T023, T027, T030, T032, T033, T034, T035, T036, T037, T038, T039, T040, T041, T044, T045, T048) suggests the implementer hit the 32K token limit and split the code into many small files rather than completing the modules specified in the plan. This is a completeness defect: the *plan* specified `code/analysis.py` and `code/reporting.py`, but the *code* is scattered.

**Required Changes**
- Consolidate all logic from `t022_save_cleaned_datasets.py`, `t023_reanalyze_cleaned_variants.py`, `t027_run_comparison.py`, `t030_dataset_size_sensitivity.py`, `t032_permutation_null_fpr.py`, `t033_outlier_threshold_sweep.py`, `t034_generate_forest_plot.py`, `t035_generate_ci_heatmap.py`, `t036_pvalue_shift_reporting.py`, `t037_ci_width_reporting.py`, `t038_effect_size_reporting.py`, `t039_log_excluded_datasets.py`, `t040_create_comparison_report.py`, `t041_generate_final_report.py`, `t044_runtime_profiling.py`, `t045_conditional_bootstrap_reduction.py`, and `t048_verify_checksums_and_state.py` into their designated modules: `code/cleaning.py`, `code/analysis.py`, and `code/reporting.py`.
- Ensure `code/main.py` imports and calls these functions directly to form a single, runnable pipeline.
- Delete the standalone `t0*.py` scripts once their logic is migrated.
- Verify `code/cleaning.py` contains the full implementation of T017-T021 (IQR, imputation, recoding) and not just imports from `cleanup_utils.py`.
