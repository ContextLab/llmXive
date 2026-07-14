---
action_items:
- id: 5b297d95d1dc
  severity: writing
  text: 'Consolidate Scripts: Merge the t0XX_*.py scripts into the cohesive modules
    defined in plan.md (code/data_loader.py, code/cleaning.py, code/analysis.py, code/reporting.py).
    The t0XX scripts should be removed or converted into a single code/main.py that
    calls functions from these modules.'
- id: f6c40ed5e9d9
  severity: writing
  text: 'Centralize Configuration: Ensure code/config.py is the *only* source for
    paths and parameters. All modules must import from it, eliminating hardcoded strings
    like "data/raw/" or "output/figures/" scattered across the t0XX files.'
- id: 9a73808b738b
  severity: writing
  text: 'Add Test Suite: Create a tests/ directory with unit tests for the core logic
    (e.g., tests/test_cleaning.py to verify outlier removal, tests/test_analysis.py
    to verify p-value calculation). At minimum, add a smoke test that runs the full
    pipeline from a clean state.'
- id: 8a57df67fb07
  severity: writing
  text: 'Remove Redundancy: Audit cleanup_utils.py, utils.py, and profiler.py to merge
    duplicate functions and ensure a single, clear API for utility operations.'
artifact_hash: 21385be9ff6aabb87c4cf55fcdf382d57dcae8502dde76fbe91c17f85b06fa72
artifact_path: projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-14T16:02:37.810462Z'
reviewer_kind: llm
reviewer_name: research_reviewer_code_quality_research
score: 0.0
verdict: minor_revision
---

The codebase exhibits a **structural fragmentation** that severely impedes reproducibility and trust. The implementation strategy has resulted in a "script-per-task" anti-pattern where the core pipeline logic is scattered across dozens of small, single-purpose scripts (e.g., `t013_record_baseline_metrics.py`, `t022_save_cleaned_datasets.py`, `t036_pvalue_shift_reporting.py`) rather than being organized into cohesive, reusable modules.

**1. Fragmented Pipeline & Lack of Orchestration**
The `code/` directory contains over 20 files prefixed with `t0XX_` (e.g., `t013_...`, `t032_...`, `t048_...`). These appear to be direct translations of `tasks.md` into executable scripts rather than modular code.
- **Problem**: There is no single entry point that orchestrates the full research pipeline. A researcher cannot simply run `python code/main.py` to reproduce the study; they must manually execute a sequence of 20+ scripts in a specific order.
- **Evidence**: `main.py` (987 bytes) exists but is likely too small to contain the full logic. The presence of `t013_record_baseline_metrics.py` (995 bytes) and `t027_run_comparison.py` (1902 bytes) suggests logic is duplicated or split arbitrarily.
- **Impact**: This makes the code impossible to extend or debug. If a researcher wants to change the outlier threshold, they must locate and edit multiple `t0XX` scripts rather than a single configuration or function.

**2. Hardcoded Paths and Lack of Configuration**
The fragmentation likely leads to hardcoded paths in each script.
- **Problem**: Without a central `config.py` being imported by all these scripts, each `t0XX` script likely defines its own input/output paths (e.g., `data/raw/...`, `data/processed/...`).
- **Evidence**: The existence of `code/config.py` (2084 bytes) is noted, but the sheer number of independent scripts suggests it is not consistently used. If `t034_generate_forest_plot.py` hardcodes `output/figures/` while `t013` hardcodes `data/processed/`, the pipeline breaks on a clean checkout if directory structures differ slightly.

**3. Missing Tests for Core Logic**
The `tests/` directory is listed in the plan but **absent** from the provided `code summary`.
- **Problem**: There is zero evidence of a test suite (`tests/`, `test_*.py`) in the file listing.
- **Impact**: The project relies entirely on the "execution gate" passing once. There is no regression testing for the statistical logic (e.g., verifying that `apply_iqr_outlier_removal` actually removes the correct rows). A future change to `cleaning.py` could silently break the analysis without any automated warning.

**4. Dead/Redundant Code**
- **Problem**: The presence of `cleanup_utils.py` (9366 bytes) alongside `utils.py` (2123 bytes) and `profiler.py` (8312 bytes) suggests overlapping responsibilities.
- **Evidence**: `cleanup_utils.py` is significantly larger than `utils.py`, yet the naming implies similar utility functions. This duplication makes it unclear which file contains the "source of truth" for helpers like `pin_random_seed` or `compute_file_checksum`.

**Required Changes**
To make this codebase readable, reproducible, and extendable:
- **Consolidate Scripts**: Merge the `t0XX_*.py` scripts into the cohesive modules defined in `plan.md` (`code/data_loader.py`, `code/cleaning.py`, `code/analysis.py`, `code/reporting.py`). The `t0XX` scripts should be removed or converted into a single `code/main.py` that calls functions from these modules.
- **Centralize Configuration**: Ensure `code/config.py` is the *only* source for paths and parameters. All modules must import from it, eliminating hardcoded strings like `"data/raw/"` or `"output/figures/"` scattered across the `t0XX` files.
- **Add Test Suite**: Create a `tests/` directory with unit tests for the core logic (e.g., `tests/test_cleaning.py` to verify outlier removal, `tests/test_analysis.py` to verify p-value calculation). At minimum, add a smoke test that runs the full pipeline from a clean state.
- **Remove Redundancy**: Audit `cleanup_utils.py`, `utils.py`, and `profiler.py` to merge duplicate functions and ensure a single, clear API for utility operations.
