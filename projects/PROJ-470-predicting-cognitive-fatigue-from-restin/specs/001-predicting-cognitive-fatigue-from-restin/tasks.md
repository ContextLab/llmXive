---
description: "Task list for Predicting Cognitive Fatigue from Resting-State EEG Complexity"
---

# Tasks: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Input**: Design documents from `/specs/001-cognitive-fatigue-eeg-complexity/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: Tests are OPTIONAL – include them only if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format
`- [ ] T### [P?] [Story] Description (file path)`

- **[P]** – can run in parallel (different files, no dependencies)
- **[S]** – sequential (requires locking or unique filenames)
- **[Story]** – which user story this task belongs to (`US1`, `US2`, `US3`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project directory structure: `projects/PROJ-470-predicting-cognitive-fatigue-from-restin/`, `data/raw/`, `data/processed/`, `code/`, `tests/unit/`, `tests/integration/`, `docs/` (verification in `tests/unit/test_setup.py`).
- [X] T002 [P] Create code skeleton files: `code/config.yaml`, `code/download.py`, `code/preprocess.py`, `code/features.py`, `code/analysis.py`, `code/report.py`, `code/models/__init__.py` (verification in `tests/unit/test_skeleton.py`).
- [X] T003 [P] Create docs skeleton files: `docs/README.md`, `docs/quickstart.md` (verification in `tests/unit/test_docs_skeleton.py`).
- [X] T004 [P] Initialize Python virtual environment and create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `pyyaml`, `pytest`, `nolds`, `statsmodels`, `psutil`, `pyentropy` (verification via `pip list`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can be implemented.

- [X] T005 [P] Create `code/config.yaml` with pipeline parameters:
 ```yaml
 filter_low: 1.0
 filter_high: 40.0
 artifact_threshold_uV: to be determined empirically during the implementation phase
 random_seed: 42
 notch_frequency: to be determined empirically during the implementation phase
 ```
 (verification parses file and checks keys/values).
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` that writes exclusion events to `data/processed/exclusion_log.csv` (verification in `tests/unit/test_logging.py`).
- [X] T007 [P] Implement a minimal `code/report.py` stub that can ingest CSVs from `data/analysis/` and render them as markdown tables (verification in `tests/unit/test_report_stub.py`).
- [X] T008 [P] Generate `docs/quickstart.md` with step‑by‑step instructions for the full pipeline (verification checks file exists and contains required commands).
- [X] T009 [P] **Data Retrieval, Validation, and Extraction** – implement `code/download.py` to fetch the public EEG dataset from **PhysioNet** (e.g., ` or another verified dataset that contains both resting‑state EEG and paired pre/post fatigue ratings).
 1. Download the full dataset.
 2. Validate presence of `eeg_data` and `fatigue_rating` variables.
 3. Count participants; if **N < 30**, raise an exception with message `"Sample size N < 30"` and exit code 1.
 4. If required variables are missing, raise an exception with message `"Missing required variables: [...]"` and exit code 1.
 5. Output `data/raw/download_manifest.json` (listing all participant files).
 6. Output `data/processed/fatigue_scores.csv` (`participant_id`, `timepoint`, `fatigue_score`).
 7. Output `data/processed/validation_report.json` (`n_participants`, `variables_found`, `status`).
 (verification: HEAD request before download; existence checks; proper error handling).
- [X] T026 [P] Implement monitoring infrastructure in `code/utils/monitor.py` using `psutil` and `time` to capture `peak_rss_gb` and `total_runtime_hours`. Write results to `data/analysis/resource_usage.json` (verification checks file and keys).

**Checkpoint**: Foundational phase complete – user‑story work may now begin.

---

## Phase 3: User Story 1 – Data Retrieval & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data and preprocess to remove artifacts and line noise.
**Independent Test**: Run preprocessing on a synthetic 120 s EEG segment containing 50 Hz line noise; verify > 20 dB attenuation at 50 Hz.

- [ ] T012 [US1] [S] Implement `code/preprocess.py` to apply a band‑pass filter (1–40 Hz) **and** a notch filter at the `notch_frequency` from `config.yaml`. The script reads `data/raw/download_manifest.json`, processes each segment, and writes cleaned files to `data/processed/cleaned_eeg/`.
 **Verification** (`tests/unit/test_preprocess.py`): generate synthetic signal with 50 Hz sinusoid, run the function, assert existence of `data/processed/cleaned_eeg_verification.fif`, compute PSDs and confirm ≥ 20 dB attenuation at 50 Hz.
- [ ] T013 [US1] [S] Add epoch‑rejection to `code/preprocess.py`: any epoch exceeding ±100 µV is excluded and logged via the logging utility from T006.
 **Verification**: after processing, `data/processed/exclusion_log.csv` contains entries (or header only if none).
- [ ] T014 [US1] [S] Add segment‑length validation: discard any resting‑state segment shorter than 120 s and log the rejection reason.
 **Verification**: same `exclusion_log.csv` check as T013.
- [ ] T015a [US1] [P] Implement a pure function `process_segment(raw_data, config)` in `code/preprocess.py` that performs band‑pass, notch, re‑reference, and artifact rejection **without any file I/O** and returns the processed NumPy array plus metadata.
 **Verification**: unit test confirms function returns expected types and does not create files.
- [ ] T015b [US1] [S] Orchestrate full‑dataset preprocessing: read `download_manifest.json`, launch a `multiprocessing.Pool` that calls `process_segment` (T015a) for each segment, and write each output to `data/processed/cleaned_eeg/{participant_id}_{segment_id}.fif`.
 **Verification**: all expected `.fif` files exist for every participant (N ≥ 30) and `exclusion_log.csv` records any rejections.

**Checkpoint**: User Story 1 fully functional and independently testable.

---

## Phase 4: User Story 2 – Complexity Feature Extraction (Priority: P2)

**Goal**: Compute Lempel‑Ziv Complexity (LZC) and Permutation Entropy (PE) for each cleaned resting‑state segment.
**Independent Test**: Run feature extraction on a synthetic signal with known LZC/PE values and verify the outputs fall within expected mathematical bounds.

- [ ] T016 [US2] [S] Implement `code/features.py` to calculate **both** LZC (using `nolds.lz_complexity` with median quantization) and PE (using `pyentropy.permutation_entropy` with embedding dimension = 3, delay = 1) **per channel** for every file in `data/processed/cleaned_eeg/`. Write results to `data/analysis/complexity_metrics.csv` with columns: `participant_id`, `channel`, `segment_id`, `lzc_value`, `pe_value`. This task is the **sole producer** of that CSV.
 **Verification**: file exists and contains the required columns.
- [ ] T017 [US2] [P] Feature‑value sanity check: create `tests/unit/test_features.py` that loads `complexity_metrics.csv` and asserts all LZC values are ≤ 1.0 and all PE values are ≤ 2.585 (the theoretical maximum for dimension = 3). Log a warning if the spec does not specify bounds, but the test must still enforce these mathematical limits.

**Checkpoint**: User Story 2 complete and independently testable.

---

## Phase 5: User Story 3 – Correlation Analysis & Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply multiple‑comparison correction, perform sensitivity analysis, and generate the final report.

- [ ] T018 [US3] [S] Implement validation in `code/analysis.py` that checks for the existence of:
 * `data/processed/cleaned_eeg/` (any `.fif` files)
 * `data/analysis/complexity_metrics.csv`
 * `data/processed/fatigue_scores.csv`

 If any are missing, print a clear error listing available files and exit with code 1. (Depends on T009, T015b.)
- [ ] T019 [US3] [S] Implement **Delta Calculation** in `code/analysis.py`: compute *post‑minus‑pre* deltas for both complexity (averaged across channels) and fatigue scores, ensuring strict pairing by `participant_id`. Write `data/analysis/delta_scores.csv` (`participant_id`, `delta_complexity_lzc`, `delta_complexity_pe`, `delta_fatigue`). Abort with an informative error if any participant lacks a complete pre/post pair.
- [ ] T020a [US3] [S] Implement **Raw Correlation**: calculate Pearson and Spearman correlations between each delta metric (LZC, PE) and `delta_fatigue`. Save results (coefficients, raw p‑values) to `data/analysis/raw_correlation_results.csv`.
 **Verification**: file exists with columns `metric`, `pearson_r`, `pearson_p`, `spearman_r`, `spearman_p`.
- [ ] T020b [US3] [S] Apply **Benjamini‑Hochberg (BH) correction** to the raw p‑values from T020a using `statsmodels.stats.multitest.multipletests`. Output corrected p‑values to `data/analysis/bh_corrected_pvalues.csv`.
 **Verification**: file exists and contains a `bh_corrected_p` column.
- [ ] T024 [US3] [S] Compute **Collinearity Diagnostics (VIF)** for the predictor set (`delta_fatigue`, `pre_complexity_lzc`, `pre_complexity_pe`, plus any available covariates such as `age`, `time_of_day`, `medication_status`). Write all VIF values to `data/analysis/vif_diagnostics.log` and the list of predictors with VIF < 5 to `data/analysis/vif_valid_predictors.json`. Do **not** abort the pipeline if VIF ≥ 5; only log a warning.
 **Verification**: both files exist; the log contains numeric VIFs; the JSON lists the valid predictors (may be empty).
- [ ] T021 [US3] [S] Implement **ANCOVA Model** (`Post_Complexity ~ delta_fatigue + Pre_Complexity + covariates`) using only predictors listed in `vif_valid_predictors.json`. Write results to `data/analysis/ancova_results.csv`. If `vif_valid_predictors.json` is empty, log a warning `"No valid predictors for ANCOVA (VIF ≥ 5). Skipping ANCOVA."` and skip this step without failing.
 **Verification**: file exists when model runs; otherwise a warning is logged and pipeline continues.
- [ ] T023 [US3] [S] Perform **Sensitivity Analysis** at thresholds p ≤ 0.05 and p ≤ 0.01 for **both** raw and BH‑corrected p‑values. Produce two tables:
 * `data/analysis/sensitivity_table_raw.csv`
 * `data/analysis/sensitivity_table_corrected.csv`

 Each table contains columns `threshold`, `significant_electrodes_count`.
 **Verification**: both tables exist and contain rows for the two thresholds.
- [ ] T025 [US3] [S] Generate the **Final Report** (`docs/final_report.md`) that assembles:
 * Correlation results (raw and BH‑corrected)
 * ANCOVA results (if produced)
 * Sensitivity analysis tables
 * VIF diagnostics summary
 * Interpretation of the relationship between complexity and fatigue, explicitly discussing the reviewer’s point about “adaptive simplification vs. degenerative noise”.
 The report must cite the source CSV/LOG files and include the tables rendered as markdown.
 **Verification**: file exists and contains the required sections with correct citations.
- [ ] T027 [US3] [S] Verify total pipeline **memory usage ≤ 7 GB** using the monitoring output (`data/analysis/resource_usage.json`). Fail the pipeline if `peak_rss_gb` > 7.0.
 **Verification**: assert the JSON key exists and respects the limit.
- [ ] T028 [US3] [S] Verify total pipeline **runtime ≤ 6 hours** using `resource_usage.json`. Fail if `total_runtime_hours` > 6.0.
 **Verification**: assert the JSON key exists and respects the limit.
- [ ] T031 [US3] [P] Add an **Interpretation Section** to the report that distinguishes between “adaptive simplification” (where reduced complexity reflects efficient neural economy) and “degenerative noise” (where reduced complexity reflects loss of informational richness). Reference the reviewer’s suggestion and include a brief literature note (e.g., Krakauer 2023) to contextualize both possibilities.
 **Verification**: `docs/final_report.md` contains a heading `## Interpretation of Complexity Changes` and a paragraph that mentions both concepts and cites a placeholder reference `[Krakauer 2023]`.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Final quality‑of‑life improvements that affect the whole project.

- [ ] T032 [P] Update `README.md` to include a concise overview of the pipeline, command‑line usage, and links to the final report.
- [ ] T033 [P] Add comprehensive type hints and docstrings to all public functions (`process_segment`, feature extraction, analysis helpers) to satisfy static‑analysis checks.
- [ ] T034 [P] Run `pytest --cov` across `tests/` and ensure coverage ≥ 85 %; add any missing tests.
- [ ] T035 [P] Format all code with `black` and lint with `ruff`; ensure CI passes linting stage.
- [ ] T036 [P] Archive the exact versions of all external datasets (e.g., store the SHA‑256 of each downloaded file in `data/raw/download_manifest.json`) to guarantee reproducibility.

---

### Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phases 3‑5)** → **Polish (Phase 6)**
- All tasks in a given phase must be completed before moving to the next phase.
- Within a user story, tasks marked `[P]` may be executed in parallel; tasks marked `[S]` must respect the listed order.

---
