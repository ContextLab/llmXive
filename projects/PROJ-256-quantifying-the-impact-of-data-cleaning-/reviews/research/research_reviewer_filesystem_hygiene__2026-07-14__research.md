---
action_items:
- id: f606745a4273
  severity: writing
  text: Delete all files in code/ matching the pattern t0*.py (e.g., t013_record_baseline_metrics.py,
    t022_save_cleaned_datasets.py, etc.) after verifying their logic has been integrated
    into the canonical modules (analysis.py, cleaning.py, reporting.py, main.py).
- id: 21482a473c63
  severity: writing
  text: Move code/run_lint.py and code/run_quickstart_validation.py to a new directory
    code/scripts/ (or scripts/ at root) to separate maintenance tools from source
    code.
- id: 3ed16d0ac646
  severity: writing
  text: 'Audit code/cleanup_utils.py and code/profiler.py: merge any unique logic
    into code/utils.py or code/main.py, then delete the standalone files.'
- id: dec52585c134
  severity: writing
  text: Update .gitignore to exclude temporary task scripts (e.g., t*.py, scratch*.py)
    to prevent recurrence.
artifact_hash: 21385be9ff6aabb87c4cf55fcdf382d57dcae8502dde76fbe91c17f85b06fa72
artifact_path: projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-14T16:03:40.929593Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

The repository exhibits significant **structural fragmentation** and **clutter** that violates the project's own stated conventions in `plan.md`. The plan explicitly defines a clean layout where `code/` contains modules (`analysis.py`, `cleaning.py`, etc.) and `tests/` contains tests, with no mention of loose scripts at the root or in `code/`.

**Specific Hygiene Defects:**

1.  **Stray Task Scripts in `code/`**: The `code/` directory is cluttered with numerous one-off scripts named `t013_record_baseline_metrics.py`, `t022_save_cleaned_datasets.py`, `t023_reanalyze_cleaned_variants.py`, `t027_run_comparison.py`, `t030_dataset_size_sensitivity.py`, `t032_permutation_null_fpr.py`, `t033_outlier_threshold_sweep.py`, `t034_generate_forest_plot.py`, `t035_generate_ci_heatmap.py`, `t036_pvalue_shift_reporting.py`, `t037_ci_width_reporting.py`, `t038_effect_size_reporting.py`, `t039_log_excluded_datasets.py`, `t040_create_comparison_report.py`, `t041_generate_final_report.py`, `t044_runtime_profiling.py`, `t045_conditional_bootstrap_reduction.py`, and `t048_verify_checksums_and_state.py`.
    *   **Issue**: These files are not part of the modular architecture described in `plan.md` (which lists `main.py`, `analysis.py`, `cleaning.py`, etc.). They appear to be temporary execution wrappers or "scratch" scripts left in the repository root of the `code/` directory. They compete for attention with the actual source modules and make the directory difficult to navigate.
    *   **Fix**: Delete these `t0XX_*.py` files. If they contain unique logic not yet integrated into the main modules (`analysis.py`, `reporting.py`, etc.), that logic must be refactored into the appropriate module, and the script deleted. If they are merely execution entry points, they should be consolidated into `code/main.py` or moved to a `code/scripts/` directory if the project adopts that convention (which it currently does not).

2.  **Misplaced Utility Scripts**: Files `run_lint.py`, `run_quickstart_validation.py`, and `t013_record_baseline_metrics.py` (and others listed above) are located directly in `code/`.
    *   **Issue**: `run_lint.py` and `run_quickstart_validation.py` are maintenance/CI scripts, not core research logic. They clutter the source directory.
    *   **Fix**: Move `run_lint.py` and `run_quickstart_validation.py` to a `scripts/` directory (e.g., `code/scripts/` or `scripts/`) or delete them if they are redundant with standard tooling (e.g., `pytest`, `ruff` CLI).

3.  **Redundant/Stray Files**: `cleanup_utils.py` (9366 bytes) and `profiler.py` (8312 bytes) exist alongside `utils.py` and `main.py`.
    *   **Issue**: `cleanup_utils.py` suggests a duplication of utility functions or a temporary file that wasn't merged into `utils.py`. `profiler.py` is a maintenance tool that should not sit in the main code directory.
    *   **Fix**: Audit `cleanup_utils.py` and `profiler.py`. Merge necessary logic into `utils.py` or `main.py` and delete the standalone files.

4.  **Missing `.gitignore` for Scratch Artifacts**: The presence of these `t0XX_*.py` files suggests a lack of discipline in what is committed. While not a "secret," this pattern of committing temporary execution scripts is a hygiene failure.
    *   **Fix**: Ensure `.gitignore` is updated to ignore any future temporary scripts (e.g., `t*.py`, `scratch*.py`, `debug*.py`) if the project intends to keep them locally but not in version control.

The repository is currently a mix of a structured module system and a "dumping ground" for task-specific scripts. This violates the "Single Source of Truth" and "Versioning Discipline" principles by making it unclear which files are the canonical implementation and which are temporary.

## Required Changes

- Delete all files in `code/` matching the pattern `t0*.py` (e.g., `t013_record_baseline_metrics.py`, `t022_save_cleaned_datasets.py`, etc.) after verifying their logic has been integrated into the canonical modules (`analysis.py`, `cleaning.py`, `reporting.py`, `main.py`).
- Move `code/run_lint.py` and `code/run_quickstart_validation.py` to a new directory `code/scripts/` (or `scripts/` at root) to separate maintenance tools from source code.
- Audit `code/cleanup_utils.py` and `code/profiler.py`: merge any unique logic into `code/utils.py` or `code/main.py`, then delete the standalone files.
- Update `.gitignore` to exclude temporary task scripts (e.g., `t*.py`, `scratch*.py`) to prevent recurrence.
