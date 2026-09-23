# Tasks: The Impact of Predictive Coding Errors on Subjective Time Perception

**Input**: Design documents from `/specs/001-predictive-coding-time-perception/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Data Discovery & Validation (Priority: P0 - Critical Blocker)

**Goal**: Attempt to download and validate datasets from the documented list. If no valid dataset is found after filtering, log the exclusion and halt. Do NOT block on an empty pre‑approved list; instead, execute the download/filter flow.

- [X] T004a [P] **Initialize Dataset IDs**. Create `data/README.md` with a 'Verified datasets' YAML block containing the list of verified OpenML/HF dataset identifiers. **Format**: YAML list of objects: `- id: <ID>, source: <OpenML|HF>, url: <URL>`. (FR‑001, Constitution III)

- [X] T012a [P] [US1] **Read Dataset IDs**. Implement `code/read_ids.py` to read dataset IDs from `data/README.md`. **Logic**: 1. Parse the 'Verified datasets' YAML block in `data/README.md` (keys: `id`, `source`, `url`). 2. Output a Python list of dictionaries for downstream tasks. (FR‑001, Constitution III)

- [X] T012b [US1] **Data Download & Checksum Verification**. Implement `code/download.py` to:
 1. Fetch each dataset using IDs from T012a via OpenML/HuggingFace.
 2. Compute SHA‑256 checksums; verify against source‑provided checksums (retrieved from dataset metadata API) and store in `data/raw/checksums.json`. On mismatch, **FAIL**.
 3. **FAIL LOUDLY**: If a fetch fails (network error, missing ID, invalid schema), raise `DataFetchError` and halt execution immediately. Do NOT fall back to synthetic data.
 4. Write raw files to `data/raw/` with accompanying `checksums.json`.
 5. **Verification**: Ensure `DataFetchError` is raised on missing ID or network failure. (FR‑001, Constitution III)

- [X] T012c [US1] **Filter & Log Exclusions**. Implement `code/filter.py` to:
 1. Read raw files from `data/raw/`.
 2. Filter for required columns (`duration_estimate`, `stimulus_sequence`, `participant_id`, `sequence_length`, `stimulus_modality`).
 3. Datasets missing any required column are excluded.
 4. Write `data/processed/exclusion_log.json` documenting excluded datasets and reasons. (FR‑002, SC‑001)

- [X] T012d [US1] **Blocker Logic & README Update**. Implement `code/update_readme.py` to:
 1. Read `data/processed/exclusion_log.json`.
 2. If **0 valid datasets** remain, write a **critical blocker** entry to `data/README.md`, create `data/blocked_status.json` with schema `{timestamp, reason, exit_code: 1}`, and **HALT** further execution.
 3. If valid datasets exist, update `data/README.md` with dataset statuses and reasons. (FR‑002, SC‑001)

- [X] T004b [P] **Validate non‑empty dataset IDs**. Implement `code/validate_ids.py` to ensure `data/README.md` contains at least one valid dataset entry in the 'Verified datasets' block. If empty, write a critical blocker to `data/README.md` and `data/blocked_status.json`. (Gate 0 reinforcement)

## Phase 1: Setup (Shared Infrastructure)

- [X] T001a [P] Create project directories: `data/raw`, `data/processed`, `code`, `figures`, `analysis`, `contracts`, `tests`
- [X] T001b [P] Create `__init__.py` files in `code/` and `tests/` directories
- [X] T002a [P] Create `pyproject.toml` with project metadata and a compatible Python version.
- [X] T002b [P] Create `code/requirements.txt` with pinned dependencies.
- [X] T002c [P] Setup virtualenv and install dependencies from `code/requirements.txt`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Setup `data/README.md` schema for dataset metadata and exclusion logs (fields: dataset_id, status, reason, checksum)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes streaming logic for large datasets.

- [X] T005 [P] Create `contracts/dataset.schema.yaml` defining required columns (duration_estimate, stimulus_sequence, participant_id, sequence_length, stimulus_modality)
- [X] T006 [P] Create `contracts/output.schema.yaml` defining analysis results structure
- [X] T007 [P] Setup environment configuration management for random seeds in `code/config.py`
- [X] T008 [P] Implement chunked data loading utility in `code/utils.py` to handle datasets >500 MB within GB RAM limits. Uses `pandas.read_csv()` with `chunksize` and `pd.concat()` for aggregation. (FR‑009, Assumption 9)
- [X] T028b [P] Define convergence threshold, bootstrap configuration, and Laplace smoothing α (`config.LAPLACE_ALPHA = 1.0`) in `code/config.py`. Set `BOOTSTRAP_N_JOBS=2` (hard cap). (FR‑009, Assumption 10)

### Streaming & Markov Implementation (Atomic Sub-tasks for T041)
- [X] T041a [P] **Streaming Loader Refactor**. Implement streaming logic in `code/preprocess.py` using `datasets.load_dataset(..., streaming=True)` for HF and chunked iteration for OpenML. **Constraint**: Must enforce `config.MAX_TRIALS = 5000` hard cap during iteration by selecting the **first 5000 trials** via `itertools.islice` to guarantee SC-004 compliance. (FR‑003, Assumption 1, SC‑004)
- [X] T041b [P] **Online Aggregation Logic**. Implement online aggregation in `code/preprocess.py` to build the first-order Markov transition matrix incrementally without loading full dataset into RAM. (FR‑003, Assumption 1)
- [X] T041c [P] **Write Incremental Counts**. Implement logic to write `data/processed/markov_counts.json` during streaming aggregation. (FR‑003)
- [ ] T041d [P] **Write Final Markov State**. Implement logic to finalize and write `data/processed/markov_state.json` containing `transition_matrix`, `alphabet`, `order=1`. **Output**: This file is the artifact validated by T017b. (FR‑003, SC‑001)

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download valid time‑perception datasets, filter for sequential stimuli, and compute surprisal metrics.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Dep: T005)
- [X] T011 [US1] Integration test for data download and validation in `tests/integration/test_download_validation.py`

### Implementation for User Story 1

- [X] T015 [US1] **Chunked Loading & Runtime Capping**. Implement `code/preprocess.py` to:
 1. Load raw data via `utils.load_chunked()` or T041a's streaming utility.
 2. **Unconditionally** cap processing at `config.MAX_TRIALS = 5000` (via T041a logic) to ensure SC-004 compliance.
 3. Log any truncation. (FR‑003, Assumption 1, SC‑004)

- [X] T016a [US1] **Build Transition Matrix**. In `code/preprocess.py`:
 1. Use the online aggregation logic from T041b to build the first-order transition count matrix in memory.
 2. Apply Laplace smoothing using `config.LAPLACE_ALPHA`.
 3. **Do NOT write to disk here**; T041d handles the final write. (FR‑003, Assumption 1)

- [X] T016b [US1] **Compute Surprisal**. In `code/preprocess.py`:
 1. Compute surprisal (‑log₂ probability) for each trial using the matrix from T016a.
 2. Append surprisal to each trial. (FR‑003, Assumption 1)

- [X] T016c [US1] **Write Standardized CSV**. In `code/preprocess.py`:
 1. Write the final `data/processed/standardized.csv` with columns: `duration_estimate`, `stimulus_sequence`, `participant_id`, `surprisal`, `sequence_length`, `stimulus_modality`, plus any other covariates.
 2. **Verification**: Assert that `sequence_length` and `stimulus_modality` are present. (FR‑003, SC‑001)

- [X] T017 [US1] **Standardized CSV Verification**. Implement `code/verify_standardized.py` to assert that `standardized.csv`:
 1. Contains ALL columns defined in `contracts/dataset.schema.yaml`: `duration_estimate`, `stimulus_sequence`, `participant_id`, `surprisal`, `sequence_length`, `stimulus_modality`.
 2. Has ≥100 valid rows.
 3. **Note**: This task ensures the artifact is valid for the full duration of Phase 3 and before Phase 4 begins.
 4. Logs success/failure to `analysis/verification_log.json`. (SC‑001)

- [ ] T017b [US1] **Markov State Validation**. Verify `markov_state.json` (produced by T041d) exists, `order == 1`, and write a confirmation entry to `analysis/verification_log.json`. (Constitution VI, SC‑001)

- [X] T042 [US1] **Sample Size Declaration**. Add logic to `code/preprocess.py` to explicitly log the sampling strategy (e.g., "Streaming full dataset" or "First N=5000 trials") to `data/README.md` (section: "Sampling Strategy") and `analysis/verification_log.json` under key `sampling_strategy`. (Rule: "State the exact streaming/sampling rule")

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Fit linear mixed‑effects models, calculate effect sizes, and perform sensitivity analysis.

### Tests for User Story 2 (OPTIONAL)

- [X] T019 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py` (Dep: T006)
- [X] T020 [P] [US2] Unit test for MDE calculation logic in `tests/unit/test_mde_calc.py`

### Implementation for User Story 2

- [X] T043 [US2] **Covariate Verification (Authoritative Check)**. Implement `code/check_covariates.py` to:
 1. Verify that `sequence_length` and `stimulus_modality` columns exist in `data/processed/standardized.csv`.
 2. If missing, log a warning, set flag `covariates_missing=true`, and **HALT** further analysis (T021a).
 3. Write `covariates_missing` status to `analysis/results.json`.
 4. **Dependency**: This is the authoritative check for covariates; T021a relies on this output. (FR‑004, Edge Cases)

- [X] T026 [US2] **LMM Residual Diagnostics**. Implement in `code/analysis.py`:
 1. Fit a preliminary LMM (without surprisal) to check assumptions.
 2. Perform Shapiro‑Wilk on **residuals** (not outcome) and check homoscedasticity.
 3. Store `residual_normality_pval` and `homoscedasticity_status` in `analysis/results.json`.
 4. **Dependency**: Must run before T021a to inform model validity. (Edge Cases, FR‑004)

- [X] T021a [US2] **Fit LMM**. Implement `code/analysis.py` to:
 1. Load `data/processed/standardized.csv`.
 2. **Check `covariates_missing` from T043**: If true, **HALT** execution and report error in `analysis/results.json`. Do NOT refit a simplified model.
 3. **Check `residual_normality_pval` from T026**: If non-normal, log warning but proceed (LMM robustness).
 4. Fit LMM: `Duration ~ Surprisal + Sequence_Length + Modality + (1 | Participant_ID)`.
 5. Write intermediate results (`coef`, `pval`, `convergence_status`) to `analysis/results.json`. (FR‑004, SC‑002)

- [X] T021b [US2] **Handle Convergence Failure**. (Sub-task of T021a logic) If full model fails to converge, refit with random-intercept-only model. Log simplification in `analysis/results.json`. (SC‑002)

- [X] T021c [US2] **Write Results**. (Sub-task of T021a logic) Ensure all results are written to `analysis/results.json`. (SC‑002)

- [X] T021d [US2] **Model Convergence Reporting**. After T021a, compute the proportion of datasets where the full model converged without fallback and write `analysis/convergence_report.json`. (SC‑002)

- [ ] T023a [US2] **Test Count & Correction Decision**. In `code/analysis.py`:
 1. Count the number of hypothesis tests performed.
 2. Set flag `needs_correction` = (test_count > 1).
 3. Write `needs_correction` to `analysis/results.json`. (FR‑005, SC‑003)

- [ ] T023b [US2] **Multiple‑Comparison Correction**. In `code/analysis.py`:
 1. **Conditionally** apply Benjamini-Hochberg correction ONLY if `needs_correction` is true (from T023a).
 2. If `needs_correction` is false, skip correction and log `correction_applied=false`.
 3. Write `adjusted_pvalues` and `correction_applied` to `analysis/results.json`. (FR‑005, SC‑003)

- [X] T023c [US2] **FWER Verification**. Verify that after correction (if applied) the family‑wise error rate ≤ 0.05; write `fwer_control_status` (boolean) to `analysis/results.json`. (SC‑003)

- [X] T024 [US2] **Effect Size with Confidence Intervals**. Compute Cohen’s d and its 95 % CI using `pingouin.compute_effsize`; store under `effect_sizes` with keys `d` and `ci` in `analysis/results.json`. (FR‑006)

- [X] T025 [US2] **Minimum Detectable Effect (MDE) & Limitation Reporting**. Using `pingouin.power_ttest` (or appropriate LMM power function), calculate MDE for power = `config.POWER_TARGET` given observed variance and sample size. Write `mde` and a boolean `mde_limitation` (true if observed effect < MDE) to `analysis/results.json`. (FR‑007, SC‑005)

- [X] T025d [US2] **MDE Limitation Reporting**. If `mde_limitation` is true (from T025), explicitly write a human-readable `limitation_statement` to `analysis/results.json` explaining that the observed effect is smaller than the MDE and the result is underpowered. (FR‑007, SC‑005)

- [X] T025b [US2] **MDE Reporting for All Datasets**. Ensure the MDE calculation (T025) runs for every dataset analyzed, regardless of outcome, and logs to `analysis/mde_report.json`. (SC‑005)

- [ ] T025c [US2] **Cutoff Sensitivity Analysis (Conditional)**. Implement `code/analysis.py` to:
 1. Check if the researcher introduced any *new* binary cutoffs (e.g., high vs. low surprisal) in the pipeline by scanning `data/processed/standardized.csv` for columns that are binary (0/1) and not present in the original schema.
 2. **If no new binary columns are found**, this task is a no-op; log `cutoff_sensitivity_skipped=true`.
 3. **If cutoffs exist**, perform a sensitivity sweep and log results.
 4. Write `cutoff_sensitivity_status` to `analysis/results.json`. (Assumption 7)

- [X] T027 [US2] **Primary Result Presence Verification**. Verify that `analysis/results.json` always contains keys `coef_surprisal` and `pval_surprisal` from the LMM (or simplified model). Log any deviation to `analysis/verification_log.json`. (Constraint Preservation)

- [X] T028 [US2] **Bootstrap Resampling**. Using `joblib.Parallel(n_jobs=2)` (fallback to a single core if only one core is available), perform bootstrap resampling to obtain robust CIs for fixed effects; append results to `analysis/results.json` and log runtime to `analysis/runtime.log`. (FR‑009)

## Phase 5: User Story 3 - Visualization and Reproducible Reporting (Priority: P3)

**Goal**: Generate forest plots, residual diagnostics, and ensure reproducible environment.

### Tests for User Story 3 (OPTIONAL)

- [X] T029 [P] [US3] Integration test for Dockerfile build and full analysis run in `tests/integration/test_reproducibility.py`

### Implementation for User Story 3

- [X] T030 [US3] **Forest Plot Generation**. Implement `code/visualize.py` to create forest plots of condition effects using `matplotlib/seaborn`; save to `figures/forest_plot.png` (≥300 DPI). (FR‑008)

- [X] T031 [US3] **Residual Diagnostic Plots**. Extend `code/visualize.py` to produce residual QQ‑plots and residual vs. fitted plots; save to `figures/residuals_*.png`. (FR‑008)

- [X] T032 [US3] **High‑Resolution Plot Saving**. Ensure all plots are saved at ≥300 DPI in `figures/`. (FR‑008)

- [X] T033a [US3] **Dockerfile Creation**. Write `Dockerfile` with `FROM python:slim`, copy source, install pinned `requirements.txt`. (US‑3)

- [X] T033b [US3] **Pipeline Runner Script**. Create `code/run_pipeline.py` that sequentially executes download, preprocess, analysis, and visualize. Set `CMD ["python", "code/run_pipeline.py"]`. (US‑3)

- [X] T033c [US3] **Docker Compatibility Check**. Verify Dockerfile builds on a CPU‑only GitHub Actions runner with ≤7 GB RAM. (US‑3)

- [X] T034a [US3] **Measure Runtime/Memory**. Implement `code/validate_runtime.py` to use `time` and `tracemalloc` to measure total runtime and peak memory. (SC‑004)

- [X] T034b [US3] **Validate Constraints**. Assert runtime < 6 h and memory ≤ 7 GB; if violated, log violation. (SC‑004)

- [X] T034c [US3] **Generate Report**. Write `analysis/runtime_report.json` with metrics and constraint status. (SC‑004)

- [X] T034d [US3] **Environment Constraint Enforcement**. Implement `scripts/verify_env.sh` to check `os.cpu_count()` ≥ 2 and available RAM; if constraints not met, force `config.USE_CHUNKED_LOADER=True` and abort if not active. (SC‑004, Assumption 10)

- [X] T034e [US3] **Simulated‑Environment Execution**. Run the full pipeline within the constrained environment, capture runtime and memory, and write a summary to `analysis/simulated_runtime.json`. (SC‑006)

- [X] T034f [US3] **Reproducibility Checklist**. Generate `reproducibility-checklist.md` guiding reviewers to reproduce results within 6 h on a fresh CPU‑only runner. (SC‑006)

- [X] T034g [US3] **6‑Hour Constraint Reporting**. Consolidate runtime metrics from T034a, T034b, T034e into `analysis/constraint_report.json` indicating compliance or violation. (SC‑004, SC‑006)

- [X] T033d [US3] **Dockerfile Optimization**. Update `Dockerfile` (T033a) to ensure the environment is CPU-optimized (no CUDA libraries installed) and that the entrypoint enforces a configurable timeout via `ENTRYPOINT ["timeout", "a_sufficient_duration", "python", "code/run_pipeline.py"]`. (SC‑004, SC‑006)

## Phase 6: Data Gap Resolution (Manual Intervention) (Priority: P0 - Post-Blocker)

**Goal**: Address the critical data gap identified in Plan.md. If Phase 0 halts due to no valid datasets, this phase provides the mechanism for **manual** intervention to add a verified source.

- [X] T050 [P] [US1] **Manual Dataset Injection Protocol (Instruction)**. **Human Action**: The researcher MUST manually edit `data/README.md` to add a new dataset entry to the 'Verified datasets' YAML block.
 1. **Action**: Open `data/README.md`.
 2. **Format**: Add `- id: <NEW_ID>, source: <OpenML|HF>, url: <URL>` to the YAML list.
 3. **Constraint**: Do NOT use any script to inject data. The system must not automate this step. (Rule: "Manual intervention required", FR-001)

- [X] T051 [US1] **Validate Manual Update**. Implement `code/validate_manual_update.py` to:
 1. Check if `data/blocked_status.json` exists.
 2. If it exists, re-parse `data/README.md` (T012a logic) to verify the new dataset entry is present and valid.
 3. If valid, remove `data/blocked_status.json` and log "Blocker cleared by manual update".
 4. If invalid, raise `ValueError` and log the rejection reason.
 5. **Constraint**: This script ONLY validates; it does NOT inject data. (Rule: "If a verified real data source is injected, USE it", FR-001)

- [X] T052 [US1] **Re-run Trigger**. Implement `scripts/trigger_recheck.py` to:
 1. Check if `data/blocked_status.json` exists.
 2. If it exists and T051 has cleared it (or if `data/dataset_ids.txt` has been manually updated), automatically re-run `code/download.py` (T012b) and subsequent pipeline steps.
 3. If not modified, exit with code 0 and log "No changes detected, manual intervention required." (Gate 0 logic)

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0** runs first. If a critical blocker is written, subsequent phases are halted.
- **Setup (Phase 1)** can run in parallel with Phase 0.
- **Foundational (Phase 2)** depends on successful completion of Phase 0.
- **User Stories** (Phases 3‑5) depend on Phase 2.
- **Polish (Phase N)** depends on all user‑story phases.

### Parallel Opportunities

- All `[P]` tasks without dependencies may run concurrently.
- Tasks that read artifacts produced by a predecessor must not be marked `[P]`.
