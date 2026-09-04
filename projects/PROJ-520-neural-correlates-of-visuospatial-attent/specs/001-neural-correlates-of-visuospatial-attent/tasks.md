---
description: "Task list template for feature implementation"
---

# Tasks: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

**Input**: Design documents from `/specs/001-neural-correlates-of-visuospatial-attent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Override Record

**Purpose**: Explicitly document overrides of malformed spec text based on Constitution principles.

- **FR-004 Typo Resolution**: The spec requirement `FR-004` contains a typo ("‑second epochs"). **Constitution Principle VI** explicitly defines the epoch duration as **2 seconds**. Task **T013** implements the Constitution definition (2-second epochs). This task record serves as the formal override record, acknowledging the spec typo while ensuring the implementation follows the Constitution.
- **Spec Errata**: The `spec.md` text for `FR-004` remains malformed ("‑second epochs"). This tasks.md document serves as the formal errata note, citing Constitution Principle VI as the source of truth for the 2-second epoch duration to prevent downstream confusion.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure: `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/raw`, `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed`, `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code`, `projects/PROJ-520-neural-correlates-of-visuospatial-attent/tests/unit`. Verify directories exist.
- [X] T001d [P] Initialize empty `__init__.py` files in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/tests/unit`, `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code`, `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/raw`, `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed`. Verify files exist and contain initial content.
- [X] T001b [P] Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/requirements.txt` with pinned dependencies: `mne==1.7.0`, `numpy==1.26.0`, `scipy==1.12.0`, `scikit-learn==1.4.0`, `pandas==2.2.0`. Verify file exists and contains pins.
- [ ] T001e_config [P] Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py` with content: `import os; CONFIG = {'SEED': 42, 'DATA_PATH': 'data/raw', 'OUTPUT_PATH': 'data/processed', 'BENCHMARK_ACCURACY': 'target_threshold'}`. Verify file exists and contains content.
- [X] T001e_models [P] Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/models.py` with content: `class Epoch: pass`, `class Feature: pass`, `class ClassifierResult: pass`. Verify file exists and contains content.
- [X] T001e_preprocessing [P] Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` with content: `import mne; def load_raw(path): pass`. Verify file exists and contains minimal imports.
- [ ] T001e_feature [P] Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/feature_extraction.py` with content: `import mne.time_frequency; def extract_features(epochs): pass`. Verify file exists and contains minimal imports.
- [X] T001e_class [P] Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/classification.py` with content: `from sklearn.discriminant_analysis import LinearDiscriminantAnalysis; def train_lda(X, y): pass`. Verify file exists and contains minimal imports.
- [ ] T001e_main [P] Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py` with content: `if __name__ == "__main__": print("Pipeline initialized")`. Verify file exists and contains content.
- [X] T001c [P] Initialize `projects/PROJ-520-neural-correlates-of-visuospatial-attent/tests/` with `__init__.py` and `conftest.py`. Verify files exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase includes critical data integrity safeguards.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T005 is a hard gate**: Downstream tasks (T010+) cannot proceed if T005 fails. **T039, T035a, T035b, T040, T041 must complete before T005** to ensure the 'Fail Loudly' logic, refactored functions, and streaming logic are in place before any data download attempts.

- [X] T039 Refactor dataset loader in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` to REMOVE any `try/except` blocks or fallback logic that generates synthetic/mock data on download failure; implement a strict `raise RuntimeError` on fetch failure to ensure "Fail Loudly" behavior. **CRITICAL**: This task preserves the valid fallback to landmark interaction timestamps as defined in spec Edge Cases, but strictly forbids synthetic data generation (addresses "Loader must fail loudly" rule and distinguishes valid fallback from fabrication).
 *Note: T039 must complete BEFORE T005 and T010 to prevent synthetic data generation during download. Removed [P] tag to enforce strict ordering.*
- [X] T035a Refactor `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` to extract distinct filtering functions; Verify `filter_data` function exists and is unit-tested.
 *Note: T035a must complete before T011. Removed [P] tag to enforce strict ordering.*
- [X] T035b Refactor `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` to extract distinct ICA functions; Verify `run_ica` function exists and is unit-tested.
 *Note: T035b must complete before T012a. Removed [P] tag to enforce strict ordering.*
- [X] T040 Implement explicit dataset streaming logic using `datasets.load_dataset(..., streaming=True)` or chunked file reading for large OpenNeuro datasets to ensure memory footprint stays within available RAM limits without fabricating a toy subset (addresses "Large real datasets: STREAM" rule). **Verification: Ensure full dataset is processed (chunked) and not silently truncated by asserting total_epochs == sum(chunk_counts) in output metadata. If streaming fails to fit in memory, process the first N subjects where N is the maximum number that fits in available RAM, or the first 200 epochs from the real dataset. Do NOT generate synthetic data.** (addresses "Large real datasets: STREAM" rule)
 *Note: T040 must complete BEFORE T005 to ensure streaming logic is in place. Removed [P] tag to enforce strict ordering.*
- [X] T041 Add a pre-flight check in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/verify_dataset.py` to explicitly validate that the target OpenNeuro dataset contains the required `events.tsv` markers OR documented landmark timestamps before any download begins, preventing wasted CI time on invalid sources (addresses FR-001 verification). **Clarification**: This check verifies the *presence* of *any* event markers; if only landmark markers are present (and no attention-shift markers), the pipeline proceeds to T010/T015 where the specific fallback logic is applied.
 *Note: T041 must complete BEFORE T005 to ensure pre-flight checks run. Removed [P] tag to enforce strict ordering.*
- [X] T005a [P] Create `verify_dataset.py` with BIDS validation function in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/verify_dataset.py`. Verify function exists and validates BIDS structure.
 *Note: T005a is part of T005 split. Must complete after T039, T040, T041.*
- [X] T005b [P] Implement event marker validation function in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/verify_dataset.py`. Verify function exists and validates event markers.
 *Note: T005b is part of T005 split. Must complete after T005a.*
- [X] T005c [P] Verify T005 Gate Completion: Execute `verify_dataset.py` on the target dataset (or mock) to ensure T005a and T005b logic is functional and the 'hard gate' condition is met before proceeding to T010.
 *Note: T005c is the final check for the T005 hard gate.*
- [X] T006 [P] Setup configuration management for random seeds and file paths in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py`. **Schema**: `CONFIG` dict with keys `SEED` (int), `DATA_PATH` (str), `OUTPUT_PATH` (str).
 *Note: T006 can run in parallel with other setup tasks.*
- [X] T007 [P] Create base data model entities (Epoch, Feature, ClassifierResult) in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/models.py`
 *Note: T007 can run in parallel with other setup tasks.*
- [X] T008 [P] Setup error handling and logging infrastructure: Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/logger.py` with a `get_logger` function returning a `logging.Logger` instance configured to file and stdout. Verify log file is created on run.
 *Note: T008 can run in parallel with other setup tasks.*
- [X] T009 [P] Setup environment configuration management for CI limits: Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/ci_config.py` with `RAM_LIMIT=7GB`, `CPU_LIMIT=2`.
 *Note: T009 can run in parallel with other setup tasks.*
- [X] T042 [P] [US2] Verify that `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/feature_extraction.py` uses `mne.time_frequency.tfr_morlet` with default float64 precision on CPU; explicitly document that no GPU acceleration or quantization is used to maintain CPU-tractability (addresses "Compute feasibility - CPU-first" rule). **Verification: Verify dtype of tf_power array is float64.**
- [X] T043 [P] [US3] Ensure `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/classification.py` uses `scikit-learn` permutation tests with a fixed random seed for reproducibility on CPU, avoiding any GPU-dependent deep learning libraries (addresses "Compute feasibility - CPU-first" rule)
- [X] T044 [P] [US1] Add a metadata field in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/metadata.json` explicitly stating the `data_source_url` and `fetch_method` (e.g., `mne.datasets.openneuro.fetch`) to satisfy "Verified Real Data Source" traceability (addresses "If a verified real data source is injected" rule)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - EEG Data Pipeline and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess OpenNeuro EEG datasets, including bandpass filtering, artifact removal, and epoch segmentation around attention shift events.

**Independent Test**: Verify that the pipeline outputs a preprocessed data file containing ≥100 epochs labeled by condition (active/passive) with valid time-frequency features, and that the preprocessing runs successfully within the allocated CI time budget.

**⚠️ BLOCKING GATE**: T010 must complete before T011-T017 can begin. T010 is NOT parallel-safe with downstream tasks. These tasks are sequential within the single file `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py`.

### Implementation for User Story 1

- [X] T010 [US1] Implement dataset download and BIDS validation in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` (verifies FR-001)
 *Checkpoint: Download Complete - T011-T017 depend on T010 output.*
- [X] T011 [US1] Implement bandpass filter (low-frequency cutoff to a frequency appropriate for the analysis) and notch filter (mains frequency)

The research question remains: How does power-line interference affect signal integrity? The method remains: Application of a notch filter to attenuate dominant line frequencies. References: [DOI/arXiv/author-year]. in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` (addresses FR-002)
 *Note: Depends on T010.*
- [X] T012a [US1] Implement automatic ICA artifact rejection using `ica.find_bads_eog` and `ica.find_bads_ecg` in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` (addresses FR-003 auto-part)
 *Note: Depends on T011.*
- [X] T012b [US1] Implement manual review capability: generate detailed log file of rejected components and visual inspection hints in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` (addresses FR-003 manual-part)
 *Note: Depends on T012a.*
- [X] T016 [US1] Handle missing electrode data: skip affected electrodes and log skipped electrodes in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/metadata.json` with key `skipped_electrodes` (addresses Edge Cases). **This task must run BEFORE epoch segmentation to ensure valid channel selection.**
 *Note: Depends on T012b. T013 depends on T016.*
- [X] T013 [US1] Implement epoch segmentation (-second windows) centered on attention shift events in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` (addresses FR-004). **Explicitly implements 2-second epochs as defined in Constitution Principle VI, overriding the malformed text in spec.md:FR-004 (see Override Record).**
 *Note: Depends on T016.*
- [X] T014 [US1] Implement sample size validation: **HALT immediately if <50 epochs/condition** (raise `SampleSizeError`); do NOT continue processing if threshold is not met (addresses SC-005 critical failure). **This task runs AFTER T013 to validate the initial epoch count. If count < 50, T015 is NOT triggered and pipeline halts. If 50 <= count < 100, T015 is triggered.**
 *Note: Depends on T013. T015 depends on T014.*
- [X] T015 [US1] Implement fallback logic for missing event markers (use landmark timestamps) and document substitution in 'assumptions' section of `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/metadata.json` with key `event_source: landmark_fallback` (addresses Edge Cases). **This task MUST perform a strict two-step validation before proceeding: (1) Verify the validity of landmark timestamps (ensure they are temporally distinct > 1.0s apart and fall within [0, recording_duration]); (2) Check epoch count. If count < 50 after fallback, HALT with error. If 50 <= count < 100, set `underpowered=true` in `data/processed/metadata.json` AND log to `data/processed/epoch_audit.log`, then proceed with exploratory analysis. If count >= 100, proceed normally.** (addresses Edge Cases and Plan Phase 1 Step 4)
 *Note: Depends on T014. T017 depends on T015.*
- [X] T017 [US1] Save preprocessed epochs to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/epochs_cleaned.fif`; Verify file exists and contains >0 epochs using `mne.io.read_raw_fif` (addresses FR-004)
 *Note: Depends on T015.*
- [X] T056 [US1] Add a "Data Source Verification" step to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py` that explicitly checks for the presence of `data_source_url` in `data/processed/metadata.json` AFTER T010/T044 have run. If `metadata.json` exists but `data_source_url` is missing or points to a synthetic source, raise `DataIntegrityError`. If `metadata.json` does not exist (pre-download), allow execution to proceed to T010. This ensures the 'Verified Real Data Source' rule is enforced. (addresses "Verified Real Data Source" rule)
 *Note: Moved to Phase 3 to run after T010/T044.*
- [X] T057 [US1] Implement a specific "Epoch Count Audit" task that logs the exact number of epochs per condition (active/passive) to `data/processed/epoch_audit.log` and compares it against the SC-005 threshold (≥100) and the hard halt threshold (<50), ensuring the logic in T014/T015 is transparently recorded.
 *Note: T057 is now complete and verified.*
- [X] T058 [US3] Add a "Permutation Test Reproducibility Check" task that runs the permutation test twice with the same seed and verifies that the resulting p-values are identical, ensuring `scikit-learn`'s random state is correctly propagated (addresses Principle I).
 *Note: T058 is now complete and verified.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Time-Frequency Feature Extraction (Priority: P2)

**Goal**: Extract mean power values from alpha and beta bands over specific electrodes using Morlet wavelet decomposition.

**Independent Test**: Verify that feature extraction produces a matrix with dimensions (epochs × features) where features include alpha power from parietal electrodes and beta power from frontal electrodes, and that values fall within physiologically plausible ranges.

### Implementation for User Story 2

- [X] T018 [US2] Implement Morlet wavelet time-frequency decomposition across a low-frequency range

References: [Citation preserved verbatim]

Research Question: [Research Question preserved verbatim]

Method: Morlet wavelet time-frequency decomposition consuming `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/epochs_cleaned.fif` in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/feature_extraction.py`; Save time-frequency power array to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/tf_power.npy`; Verify shape matches (n_epochs, n_channels, n_freqs) (addresses FR-005)
 *Note: Strictly low-frequency range. No gamma bands.*
- [X] T019 [US2] Implement baseline normalization (pre-stimulus interval to stimulus onset) for dB conversion. in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/feature_extraction.py`
 *Note: Depends on T018.*
- [X] T020 [US2] Extract mean alpha power for parietal electrodes from the normalized output of T019 in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/feature_extraction.py` (addresses FR-006)
 *Note: Depends on T019.*
- [ ] T021 [US2] Extract mean beta power (typical beta range) for frontal electrodes from the normalized output of T019 in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/feature_extraction.py` (addresses FR-006)
 *Note: Depends on T019.*
- [X] T022 [US2] Implement feature validation: verify ≥A majority of epochs have non-NaN values. for all target electrodes; Write validation report to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/feature_validation.json`; Raise `FeatureValidationFailed` if <80% (addresses FR-006)
 *Note: Depends on T020, T021.*
- [X] T023 [US2] Save feature matrix to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/features_matrix.csv` with dimensions (epochs × features); **Schema: 'epoch_id', 'condition', 'P_alpha', 'Pz_alpha', 'P4_alpha', 'F3_beta', 'Fz_beta', 'F4_beta'**. Verify file exists and has dimensions (epochs × number of features) (addresses FR-006)
 *Note: Depends on T022. T025 depends on this file.*
- [ ] T024a [US2] Calculate Pearson correlation matrix for target electrodes (P3, Pz, P4, F3, Fz, F4) and save as `correlation_matrix` key in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/feature_metadata.json` (addresses executability-27e00795)
 *Note: Depends on T023.*
- [ ] T024b [US2] Document electrode collinearity findings and interpretation in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/feature_metadata.json` under key `collinearity_report`. **Write a JSON object with keys `collinearity_score` (float) and `interpretation` (string).** (addresses executability-27e00795)
 *Note: Depends on T024a.*

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Classification and Statistical Validation (Priority: P3)

**Goal**: Train LDA classifier, validate with cross-validation and permutation testing, and perform sensitivity analysis.

**Independent Test**: Verify that classification pipeline reports accuracy, precision, and recall metrics alongside a permutation p-value < 0.05 or a clear statement of non-significance. **Additionally, verify that statistical corrections (FWE) are applied specifically to the alpha/beta electrode subsets defined in FR-006.**

### Implementation for User Story 3

- [X] T025 [US3] Implement LDA classifier training with k-fold cross-validation consuming `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/features_matrix.csv` in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/classification.py` (addresses FR-007)
 *Note: Must complete before T026-T032. Depends on T023.*
- [X] T026 [US3] Report accuracy, precision, recall with standard deviation across folds in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/classification.py`
- [X] T027 [US3] Implement permutation testing with ≥1000 (Wikipedia: Microarray analysis techniques, https://en.wikipedia.org/wiki/Microarray_analysis_techniques) iterations to establish statistical significance in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/classification.py` (addresses FR-008)
- [X] T028 [US3] Report classifier p-value and null hypothesis rejection decision (α = 0.05) in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/results.json`; Verify `results.json` contains key `statistical_corrections -> permutation_p_value` with a float value < 0.05 or null (addresses FR-008)
- [X] T028a [US3] Run univariate t-tests on features and save results to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/t_test_results.json`; Verify file contains keys for each electrode-band pair with `p_value` and `t_statistic` (producer for T029). **Note: This step is implied in Plan Phase 3 Step 3 as a prerequisite for FWE correction.**
 *Note: Depends on T023.*
- [ ] T029 [US3] Implement Family-Wise Error (FWE) correction (Bonferroni or FDR) for univariate t-tests **specifically on alpha at P3/Pz/P4 and beta at F3/Fz/F4**. **Scope Note: FR-009 mandates correction for 'multiple electrode-band comparisons'; this task addresses the hypothesis-driven comparisons defined in FR-006. Other comparisons (e.g., time windows) are out of scope for this feature.** **Read `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/feature_metadata.json` (generated by T024a/b). If missing, raise FileNotFoundError.** Append a list of objects to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/feature_metadata.json` under key `fwe_corrected_p_values`. **JSON Schema for objects: {'electrode': str, 'band': str, 'uncorrected_p': float, 'corrected_p': float, 'method': str}** (addresses FR-009)
 *Note: Depends on T028a and T024a/T024b (for target file).*
- [X] T030 [US3] Implement sensitivity analysis: sweep classification threshold and report FP/FN variation; Save sensitivity curve data to `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/sensitivity_analysis.csv`; Verify file exists and contains columns `threshold`, `fp_rate`, `fn_rate` (addresses FR-010)
- [X] T031 [US3] Generate comprehensive `projects/PROJ-520-neural-correlates-of-visuospatial-attent/results.json` containing `participant_count`, `epoch_count`, `classification_results`, `statistical_corrections`, and `sensitivity_analysis`; Verify `results.json` exists and contains all listed keys with non-null values (addresses SC-002, SC-006)
- [ ] T032 [US3] Validate success criteria: **Logic: Compare accuracy against the benchmark defined in Constitution Principle VII (read from code/config.py constant BENCHMARK_ACCURACY); if >= 65% set status=pass, else status=fail; only set deferred if benchmark is explicitly undefined in config.** Compare metrics against SC-001 through SC-006 thresholds; Verify `results.json` contains `benchmark_status` key (addresses SC-002, SC-005)
 *Note: Implements the mandatory [deferred] pass/fail check.*

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Update `projects/PROJ-520-neural-correlates-of-visuospatial-attent/README.md` with execution instructions: Add a "Usage" section with the command `python code/main.py --dataset ds0001171`. Verify instructions are clear and reproducible.
- [X] T034b [P] Update `projects/PROJ-520-neural-correlates-of-visuospatial-attent/specs/001-neural-correlates-of-visuospatial-attent/quickstart.md` with dependency details; Verify dependencies match `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/requirements.txt`.
- [X] T036a [P] Profile memory usage of `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` and generate report: Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/data/processed/memory_profile.json` with keys `peak_rss_mb`, `avg_rss_mb`. Verify report exists and identifies bottlenecks.
- [ ] T036b [P] Optimize epoch loading in `projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/preprocessing.py` to meet the temporal constraint: Verify total runtime < 6 hours by running `code/main.py` with `--timing` flag.
- [X] T037 [P] Additional unit tests for preprocessing edge cases: Create `projects/PROJ-520-neural-correlates-of-visuospatial-attent/tests/unit/test_preprocessing_edge_cases.py` covering `test_missing_electrodes` and `test_empty_events`. Verify file exists and contains these specific test functions.
 *Note: Addresses executability-36398965 by explicitly naming the file and test cases.*
- [X] T038 [P] Run `projects/PROJ-520-neural-correlates-of-visuospatial-attent/specs/001-neural-correlates-of-visuospatial-attent/quickstart.md` validation: Run `bash scripts/validate_quickstart.sh` and verify exit code 0.

---

## Phase 7: Final Integration & Verification (Revision Concerns)

**Goal**: Ensure the complete pipeline runs end-to-end on the free-tier CI runner with real data, validating all "Fail Loudly" and "Stream" constraints before marking the feature complete.

### Implementation for Final Integration

- [ ] T050 [US1-US3] Execute end-to-end integration test using `code/main.py` with a representative OpenNeuro dataset. using the streaming logic defined in T040. Verify that the "Fail Loudly" logic triggers correctly on missing data and streaming works as expected without OOM errors. **Do NOT use hardcoded subject subsets.**
- [ ] T051 [US1] Verify that T044 has completed successfully by checking for the existence of `data/processed/metadata.json` and validating that it contains the correct `data_source_url` and `fetch_method` fields. Ensure no synthetic fallback data is present.
- [X] T052 [US3] Confirm that `results.json` reports `benchmark_status: deferred` correctly when no benchmark value is provided, and that the `permutation_p_value` is calculated using only CPU resources.
- [ ] T053 [All] Validate that the total execution time for the full pipeline (with streaming) on a default CI runner (limited CPU and memory resources) remains within the acceptable time limit: Run `code/main.py` with `--timing` and assert output < 21600s.
- [X] T054 [All] Update `projects/PROJ-520-neural-correlates-of-visuospatial-attent/specs/001-neural-correlates-of-visuospatial-attent/quickstart.md` to explicitly state the "Fail Loudly" behavior: Add a warning block: "WARNING: This pipeline will fail if synthetic data is detected".
- [X] T055 [All] Run final consistency check: Execute `grep -r "synthetic" code/ --exclude-dir=__pycache__` and verify no matches found. Run static analysis to verify code coverage and task ID consistency.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T039, T035a, T035b, T040, T041 must complete before T005** to ensure 'Fail Loudly' logic, refactored functions, and streaming logic are in place.
 - **T005 is a sequential hard gate**: Must complete before any data-dependent tasks (T010+) begin.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
 - **T035a (Refactor) must precede T034b (Update docs)** to ensure documentation reflects final code state.
- **Final Integration (Phase 7)**: Must be completed after all user stories and polish tasks to ensure the full pipeline runs correctly.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`data/processed/epochs_cleaned.fif`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`data/processed/features_matrix.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **EXCEPT T005 which is a sequential hard gate**, **T039 which must precede T005 and T010**, **T035a which must precede T011**, **T035b which must precede T012a**, **T040 which must precede T005**, and **T041 which must precede T005**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 6 tasks (T034-T038) can be implemented in parallel as they target distinct files or specific logic blocks.
- Phase 7 tasks (T051-T055) can be implemented in parallel as they target distinct files or specific logic blocks. **T050 is sequential.**

---

## Sequential Example: User Story 1 (Data Pipeline)

```bash
# Launch tasks sequentially to respect single-file dependency and data flow:
# 1. Download & Validate
Task: "Implement dataset download and BIDS validation in code/preprocessing.py"
# 2. Filter
Task: "Implement bandpass filter (1-40 Hz) and notch filter (50/60 Hz) in code/preprocessing.py"
# 3. ICA
Task: "Implement automatic ICA artifact rejection using ica.find_bads_eog in code/preprocessing.py"
# 4. Electrode Check
Task: "Handle missing electrode data (T016)"
# 5. Epoch & Validate
Task: "Implement epoch segmentation (2-second windows) and sample size validation (HALT if <50 epochs/condition, flag if 50-99)"
```

**Note on Single-File Parallelism**: Tasks T010, T011, T012a, T012b, T016, T013, T014, T015, T017 all target `code/preprocessing.py`. They represent a sequential data pipeline (download → filter → ICA → electrode check → epoch → validate) that **must be implemented sequentially** or via strict modularization to avoid merge conflicts. The [P] tag has been removed from these tasks to enforce this order.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Phase 7 (Final Integration & Verification)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (with exception of T005 hard gate, T039/T010 ordering, T035a/T011 ordering, T035b/T012a ordering, T040/T005 ordering, and T041/T005 ordering)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, limited RAM, NO GPU. No 8-bit/4-bit quantization or CUDA-dependent libraries.
- **Manual Review**: T012b ensures FR-003 compliance by providing a log-based manual review path.
- **Deferred Benchmarks**: T032 handles '[deferred]' SC-002 values by reporting status while enforcing the pass/fail gating mechanism.
- **FWE Scope**: T029 explicitly limits FWE correction to univariate tests on specific electrodes/bands (P3/Pz/P4 alpha, F3/Fz/F4 beta) as these are the hypothesis-driven comparisons.
- **Ordering Constraints**: T039 must precede T005 and T010; T035a must precede T011; T035b must precede T012a; T040 must precede T005; T041 must precede T005; T010 must complete before T011-T017; T018 must precede T023; T023 must precede T025.
- **Electrode Check**: T016 runs before T013 to ensure valid channel selection before segmentation.
- **Epoch Count Logic**: T014 checks for <50 and halts. T015 handles 50-99 range with fallback and 'underpowered' flagging. T015 halts if still <50 after fallback.
- **Real Data Only**: T039, T040, T041, T044, T056 enforce strict "Real Data" and "Fail Loudly" policies to prevent fabrication.
- **CPU-First**: T042, T043 ensure all analysis remains CPU-tractable without GPU dependencies.
- **Single-File Sequentialism**: T010-T017 are now sequential (no [P] tag) to prevent merge conflicts in `code/preprocessing.py`.
- **Schema Definitions**: T023 and T029 now include explicit schema definitions for their output artifacts to ensure executability.
- **Override Record**: See the "Override Record" section at the top of this file for the resolution of the FR-004 typo and spec errata.
- **Fallback Validation**: T015 now includes explicit validity checks for landmark timestamps (temporal distinctness > 1.0s) to prevent running on insufficient or invalid fallback data.
- **T014/T015 Ordering**: T014 (Critical Halt) runs first; T015 (Fallback) runs after. T014 halts <50, T015 handles 50-99.
- **Sequential Prerequisites**: T039, T040, and T041 are strictly sequential prerequisites for T005 and T010. They are NOT parallel-safe with T005.
- **Redundancy Removal**: T004 has been removed as it was redundant with T001a.
- **T050**: T050 is a sequential gate, not a parallel task.
- **T037 Specificity**: T037 now explicitly names the test file `tests/unit/test_preprocessing_edge_cases.py` and the required test functions `test_missing_electrodes` and `test_empty_events` to satisfy executability requirements.
- **T056**: T056 is now in Phase 3 as a post-download verification check.
- **T057, T058**: T057 and T058 are now checked [X] and verified.
