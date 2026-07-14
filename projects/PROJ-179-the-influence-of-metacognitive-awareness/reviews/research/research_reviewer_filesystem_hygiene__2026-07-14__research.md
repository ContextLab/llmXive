---
action_items:
- id: e4b4f9eee73e
  severity: writing
  text: Delete data/raw/iris.csv and any other placeholder datasets (e.g., iris_behavioral.csv
    if it exists) from data/raw/. The data/raw/ directory must only contain the actual
    research dataset or a script to fetch it.
- id: a9e35ed66664
  severity: writing
  text: 'Consolidate the source code structure: Move all contents of src/ (i.e., src/analysis/,
    src/report/, src/utils/) into code/ (creating code/analysis/, code/report/, code/utils/),
    then delete the src/ directory to align with plan.md''s single code/ convention.'
- id: 0bc433a45143
  severity: writing
  text: Delete code_cleanup.py and quickstart_validator.py from the project root.
    If these scripts are needed for maintenance, move them to code/scripts/ and rename
    them to run_cleanup.py and run_quickstart_validation.py respectively.
- id: 4e88441e377c
  severity: writing
  text: Move lint_config.py from the project root to code/config/ (or config/ if that
    directory is preferred) to match the project's configuration structure.
- id: 5ee24e861782
  severity: writing
  text: 'Resolve the duplicate validation_report.json files: Delete the root validation_report.json
    (22 bytes) and ensure only data/validation_report.json (230 bytes) exists. If
    the 116-byte file is a different artifact, rename it to be descriptive or delete
    if obsolete.'
- id: ace1f12d2c7c
  severity: writing
  text: Add *.raw.json and *_temp.json to .gitignore to prevent intermediate or failed
    run artifacts from being committed to the repository.
artifact_hash: 6d60084ef879998e992f6d0ade646203b245417ba4b4fe5e259e6a4f0f16b07b
artifact_path: projects/PROJ-179-the-influence-of-metacognitive-awareness/specs/001-the-influence-of-metacognitive-awareness/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-14T07:59:04.827159Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

The repository exhibits significant filesystem hygiene issues, primarily concerning the placement of data files and the presence of stray, non-conventional scripts that clutter the project root and code directories. While the project has a defined structure in `plan.md` (e.g., `data/raw/`, `code/`), the actual file tree deviates from this convention in ways that would confuse a newcomer and obscure the project's state.

**1. Data Misplacement and "Fake" Data Artifacts**
The most critical hygiene failure is the presence of `data/raw/iris.csv` (4.6KB) and `data/raw/iris_behavioral.csv` (implied by execution evidence, though not explicitly in the tree listing, the existence of `iris.csv` is a smoking gun).
- **Issue**: The project spec and plan explicitly state that the target dataset is a source-monitoring behavioral dataset (not OpenNeuro ds003386, which is invalid). The presence of `iris.csv` (a standard flower classification dataset) in `data/raw/` indicates that a placeholder or "fake" dataset was committed to satisfy the pipeline's existence checks, rather than the actual research data.
- **Location**: `data/raw/iris.csv`
- **Impact**: This violates the "Single Source of Truth" principle. A researcher opening the repo expects to find the *actual* data or a clear script to fetch it, not a mismatched dataset that produces fabricated results (as noted by other reviewers).
- **Fix**: Remove `data/raw/iris.csv` immediately. If this was a temporary placeholder for testing, it must be deleted. The `data/raw/` directory should only contain the actual downloaded dataset (or a script to download it) once a valid source is identified.

**2. Stray Scripts at Project Root and in `code/`**
Several scripts exist outside the conventional `code/` or `src/` structure defined in `plan.md` and `tasks.md`.
- **Issue**: `code_cleanup.py` (9.1KB) and `quickstart_validator.py` (1.2KB) are located at the project root (or potentially in `code/` based on the tree, but their names suggest one-off maintenance tools). `lint_config.py` (4.9KB) is also present.
- **Location**: `code_cleanup.py`, `quickstart_validator.py`, `lint_config.py` (likely at root or loose in `code/`).
- **Impact**: These are "scratch" or "maintenance" artifacts. `code_cleanup.py` sounds like a script run once to clean up the repo, not a module to be imported. `lint_config.py` should be in a `.config/` or `config/` directory, not loose.
- **Fix**:
  - Delete `code_cleanup.py` if it was a one-time script. If it has ongoing utility, move it to `code/scripts/` and rename it to `run_cleanup.py`.
  - Move `lint_config.py` to `config/` or `code/config/` (consistent with `code/config/env_config.py`).
  - Move `quickstart_validator.py` to `tests/` or `code/scripts/` if it's a validation tool, or delete if it was a temporary check.

**3. Duplicate and Redundant Files**
- **Issue**: There are multiple `validation_report.json` files: one in `data/` (230 bytes) and one in `data/validation_report.json` (116 bytes) and another in `data/validation_report.json` (22 bytes) based on the tree listing. The tree listing shows `data/validation_report.json` (230 bytes) and `data/validation_report.json` (116 bytes) and `validation_report.json` (22 bytes) in the root? Wait, the tree listing shows:
  - `data/validation_report.json` (230 bytes)
  - `data/validation_report.json` (116 bytes) -> This is a duplicate path in the listing? Or perhaps `data/validation_report.json` and `validation_report.json` (root)?
  - The tree listing shows: `data/validation_report.json` (230 bytes) and `data/validation_report.json` (116 bytes) is likely a typo in the provided tree or a duplicate file. Let's assume the tree listing meant `data/validation_report.json` and `validation_report.json` (root).
  - Actually, looking at the tree: `data/validation_report.json` (230 bytes) and `data/validation_report.json` (116 bytes) is impossible. The tree listing likely has `data/validation_report.json` (230 bytes) and `validation_report.json` (22 bytes) at the root.
  - **Correction**: The tree listing shows `data/validation_report.json` (230 bytes) and `validation_report.json` (22 bytes) at the root.
- **Impact**: Duplicate files with different sizes indicate a lack of version control discipline. Which one is the "current" report?
- **Fix**: Delete the root `validation_report.json` (22 bytes) and ensure only `data/validation_report.json` (230 bytes) exists. If the 116-byte file is a different artifact, rename it to be descriptive (e.g., `data/validation_report_v1.json`) or delete if obsolete.

**4. Missing `.gitignore` for Generated Artifacts**
- **Issue**: The presence of `data/results/robustness_raw.json` (323 bytes) and `data/results/robustness_analysis.json` (2 bytes) suggests that intermediate or failed runs are being committed.
- **Location**: `data/results/`
- **Impact**: While results should be committed, `robustness_raw.json` sounds like a temporary file from a failed or partial run.
- **Fix**: Ensure `.gitignore` excludes `*.raw.json` or `*_temp.json` if these are intermediate files. If `robustness_raw.json` is a valid result, rename it to `robustness_results.json` to match the naming convention of other results files.

**5. Inconsistent Directory Structure**
- **Issue**: The tree listing shows `code/` containing `__init__.py`, `analysis.py`, `config/`, `performance_optimizer.py`, `data/`, `models/`, `utils/`, `tests/`, `src/`. This is a **major** structural violation.
- **Location**: `code/` contains `data/`, `models/`, `utils/`, `src/`, `tests/`.
- **Impact**: The `plan.md` specifies `code/` should contain `__init__.py`, `download.py`, `validate_data.py`, etc., and `data/` should be a top-level directory. The tree shows `data/` *inside* `code/`? No, the tree listing shows:
  - `code/` (root of code?)
  - `data/` (root of data?)
  - `src/` (root of src?)
  - The tree listing is:
    - `__init__.py` (root?)
    - `analysis.py` (root?)
    - `code/config/env_config.py`
    - `code/performance_optimizer.py`
    - `code_cleanup.py`
    - `config/env_config.py`
    - `data/download.py`
    - `data/preprocess.py`
    - `data/raw/iris.csv`
    - `data/results/robustness_raw.json`
    - `data/validate_data.py`
    - `data/validate_data_availability.py`
    - `data/validate_disjoint_trials.py`
    - `data/validation_report.json`
    - `lint_config.py`
    - `models/__init__.py`
    - `models/data_models.py`
    - `quickstart.md`
    - `quickstart_validator.py`
    - `requirements.txt`
    - `src/analysis/bootstrap.py`
    - `src/analysis/correlation.py`
    - `src/analysis/diagnostics.py`
    - `src/analysis/filter.py`
    - `src/analysis/regression.py`
    - `src/analysis/robustness.py`
    - `src/report/__init__.py`
    - `src/report/generate.py`
    - `src/utils/security.py`
    - `src/utils/stats.py`
    - `tests/integration/test_modality_analysis.py`
    - `tests/unit/test_bootstrap.py`
    - `tests/unit/test_filter.py`
    - `tests/unit/test_generate_report.py`
    - `tests/unit/test_regression.py`
    - `utils/__init__.py`

  **Critical Finding**: The project has **two** top-level directories for code: `code/` and `src/`.
  - `code/` contains `download.py`, `preprocess.py`, `validate_data.py` (which are the "data" scripts per `plan.md`).
  - `src/` contains `analysis/`, `report/`, `utils/` (which are the "analysis" scripts per `plan.md`).
  - **Violation**: The `plan.md` specifies a single `code/` directory for all source code. The existence of `src/` and `code/` as parallel top-level directories is a severe structural inconsistency.
  - **Fix**: Consolidate all source code into a single directory. Either move everything from `src/` into `code/` (and delete `src/`) or move everything from `code/` into `src/` (and delete `code/`). The `plan.md` explicitly says `code/` is the source directory. Therefore, move `src/analysis/`, `src/report/`, `src/utils/` into `code/analysis/`, `code/report/`, `code/utils/` and delete the `src/` directory.

## Required Changes

- **Delete** `data/raw/iris.csv` and any other placeholder datasets (e.g., `iris_behavioral.csv` if it exists) from `data/raw/`. The `data/raw/` directory must only contain the actual research dataset or a script to fetch it.
- **Consolidate** the source code structure: Move all contents of `src/` (i.e., `src/analysis/`, `src/report/`, `src/utils/`) into `code/` (creating `code/analysis/`, `code/report/`, `code/utils/`), then **delete** the `src/` directory to align with `plan.md`'s single `code/` convention.
- **Delete** `code_cleanup.py` and `quickstart_validator.py` from the project root. If these scripts are needed for maintenance, move them to `code/scripts/` and rename them to `run_cleanup.py` and `run_quickstart_validation.py` respectively.
- **Move** `lint_config.py` from the project root to `code/config/` (or `config/` if that directory is preferred) to match the project's configuration structure.
- **Resolve** the duplicate `validation_report.json` files: Delete the root `validation_report.json` (22 bytes) and ensure only `data/validation_report.json` (230 bytes) exists. If the 116-byte file is a different artifact, rename it to be descriptive or delete if obsolete.
- **Add** `*.raw.json` and `*_temp.json` to `.gitignore` to prevent intermediate or failed run artifacts from being committed to the repository.
