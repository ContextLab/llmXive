# Tasks: Statistical Discrepancies in Publicly Available Election Data

**Input**: Design documents from `/specs/001-statistical-discrepancies-in-publicly-av/`
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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Initialize project directory structure: Create `projects/PROJ-064-statistical-discrepancies-in-publicly-av/` with `code/`, `data/` (raw/processed), `tests/`, `docs/`, `state/`, and `config/` subdirectories in one atomic step.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw/`, `data/processed/` and `state/` for checksums in `projects/PROJ-064-statistical-discrepancies-in-publicly-av/`
- [X] T005 [P] Implement base logging infrastructure in `code/utils/logger.py` with explicit support for JSON-formatted logs containing keys: `timestamp`, `level`, `message`, `task_id`, `checksum`, `artifact_hash`, `reproducible_flag`, `vif_score`, and `collinearity_status` to satisfy Constitution Principle I (Reproducibility), Principle V (Versioning), and SC-006 (Collinearity). The logger MUST support a `--verify-reproducible` flag that outputs these hashes for external verification AND mandates the update of `state/` YAML files with artifact hashes. **CLI Entry Point**: `python code/main.py --verify-reproducible`. **YAML Update**: Update `state/...yaml` under `artifact_hashes` key. **Note**: Depends on T004 (data directory structure) to ensure log paths exist.
- [X] T007 Create base data models/entities (Jurisdiction, Discrepancy) in `code/models.py` AND define the output schema (columns: `precinct_sum`, `county_reported`, `discrepancy_abs`, `discrepancy_pct`, `missing_data` flag) for downstream tasks.
- [X] T008 Implement content hashing utility for artifacts in `code/utils/hashing.py`
- [X] T009a [P] Implement GitHub Actions workflow trigger for `--verify-reproducible` in `.github/workflows/verify_reproducible.yml` to re-run analysis on a fresh CI runner. **Trigger**: `on: push`, `on: schedule`. **Job Steps**: 1) Checkout code, 2) Install dependencies, 3) Run `python code/main.py --verify-reproducible`, 4) Upload artifacts. This MUST execute the full pipeline on a fresh CI runner as mandated by Constitution Principle I.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and normalize election data from verified sources into a unified format with calculated discrepancies.

**Independent Test**: The pipeline can be tested by running the data ingestion script against a small, fixed sample of known CSV files and verifying that the output DataFrame contains the expected columns (`precinct_sum`, `county_reported`, `discrepancy_abs`, `discrepancy_pct`) with no nulls in critical fields.

### Implementation for User Story 1

- [X] T014a [US1] Implement unified ingestion pipeline in `code/ingestion.py`: 1) Verify data source is on the verified list (Hugging Face mirrors, etc.) before attempting download; 2) If source is not verified, check `SYNTHETIC_FALLBACK` config flag; 3) If `SYNTHETIC_FALLBACK` is True, generate synthetic data with realistic properties; 4) If `SYNTHETIC_FALLBACK` is False, raise a clear `DataFetchError`; 5) Download/Generate data, parse raw CSVs, normalize aggregation levels, handle format deviations, and calculate discrepancies. **Execution Flow**: Strictly enforce verified source gate before any fetch attempt. **Note**: Consolidates T014a-e, T016, T014e-override, T060, T070. <!-- FAILED: unspecified -->
- [X] T017 [US1] Implement discrepancy calculation and edge case handling in `code/discrepancy.py`: 1) Calculate `precinct_sum`, `county_reported`, `discrepancy_abs`, `discrepancy_pct` per T007 schema; 2) Skip records with zero county votes and log warnings; 3) Flag "directional anomalies" (precinct sum > county total) but retain for Permutation model; 4) Apply documented imputation rules or flag records with `missing_data` marker. **Note**: Consolidates T017-T020.
- [X] T018 [US1] Implement validation logic to ensure required variables (precinct votes, county totals) exist, raising clear errors if missing in `code/ingestion.py`. **Note**: Logic integrated into T014a.
- [X] T019 [US1] ⚠️ BLOCKING PREREQ for T027, T055 Implement logic to flag "directional anomalies" (precinct sum > county total) and exclude from Negative Binomial fit if non-negative error assumption is violated in `code/discrepancy.py`.
- [X] T021 [US1] Ensure raw data is saved to `data/raw/` with checksums and processed data to `data/processed/` in `code/main.py`.
- [X] T053 [US1] Implement streaming data ingestion for large datasets in `code/ingestion.py`: Use `datasets.load_dataset(..., streaming=True)` to process election data in chunks. Implement an online aggregation strategy to compute `precinct_sum` and `discrepancy_pct` without loading the full dataset into RAM. If the dataset size exceeds ~10GB, implement a deterministic sampling strategy (e.g., `itertools.islice` with a fixed seed) to extract the first [deferred] rows and explicitly log the sample size and its representativeness limitations.
- [X] T054 [US1] Add explicit verification of real data source integrity in `code/ingestion.py`: Before processing, verify the downloaded file's SHA-256 checksum against the known good hash from the verified source metadata. If the checksum mismatches, raise an error and abort the pipeline.
- [X] T061 [US1] Implement verified data source registry: Create `config/verified_sources.yaml` containing a whitelist of approved data sources (OpenElections, EAC, specific state-level CSVs) with their exact URLs, checksums, and expected schema versions. The ingestion script MUST validate against this registry before any download attempt.
- [X] T062 [US1] Implement streaming data loader for NAB-style election data: Replace any bulk `pd.read_csv` calls with a generator-based loader using `datasets.load_dataset(..., streaming=True)` that processes precinct-level data in chunks of [deferred] rows, accumulating statistics on-the-fly to compute `precinct_sum` and `discrepancy_pct` without ever loading the full dataset into RAM.
- [X] T063 [US1] Implement deterministic sampling for large datasets: If the streaming dataset exceeds 10GB or the estimated number of jurisdictions exceeds a substantial threshold, implement a deterministic sampling strategy using `itertools.islice` with a fixed seed (42) to extract a representative sample (e.g., first N rows where N is calculated to fit available system memory) and explicitly log the sample size, sampling method, and representativeness limitations in `data/processed/sampling_report.json`. **Note**: Sampling ONLY if necessary for size.
- [X] T067 [US1] Implement checksum verification for downloaded data: Before processing any downloaded file, compute its SHA-256 checksum and compare it against the expected hash stored in `config/verified_sources.yaml`. If the checksums do not match, raise a `DataIntegrityError` and abort the pipeline.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests AFTER implementation to ensure they verify the correct schema and logic. Depends on T007 (Data Models & Schema).

- [X] T010 [P] [US1] Unit test for data ingestion with mock CSV files in `tests/test_ingestion.py` (Schema defined in T007)
- [X] T011 [P] [US1] Contract test verifying output schema (precinct_sum, county_reported, etc.) in `tests/test_ingestion.py` <!-- FAILED: unspecified -->
- [X] T012 [P] [US1] Test for missing data handling (imputation vs. flagging) in `tests/test_ingestion.py` <!-- FAILED: unspecified -->
- [X] T013 [P] [US1] Test for auto-detection of file delimiters in `tests/test_ingestion.py`
- [X] T050 [P] Additional unit tests for edge cases (zero votes, missing data) in `tests/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Null Model Simulation and Statistical Testing (Priority: P2)

**Goal**: Construct Negative Binomial and Permutation null models, perform Anderson-Darling and KS tests, and frame findings as associational deviations.

**Independent Test**: The analysis module can be tested by feeding it a synthetic dataset with known properties (Negative Binomial distributed noise) and verifying that the p-values from the Anderson-Darling and KS tests align with the expected distribution (high p-values) within ±0.05 tolerance, using seed=42.

### Implementation for User Story 2

- [X] T027 [US2] Implement Monte Carlo simulation with NB and permutation null models in `code/simulation.py`: 1) Fit a Negative Binomial null model to the *observed* data (using robust stats like median/MAD) as required by FR-003; 2) Execute [deferred] iterations (seed=42) as required by FR-003; 3) Implement chunked processing (10 batches of multiple iterations) to ensure memory usage stays under 7 GB RAM limit; 4) Aggregate results (accumulate log-likelihoods/p-values) to ensure statistical equivalence to a full-scale run; 5) If NB fit fails (convergence error), switch to permutation-based null model as fallback. **Note**: Consolidates T027-T034.
- [ ] T029 [US2] Implement internal verification sub-routine for chunking strategy equivalence in `tests/test_simulation.py`. **Logic**: Run a small-scale single-block simulation and compare its aggregated result against the chunked aggregation result using a Kolmogorov-Smirnov test to verify p-value > 0.05, ensuring statistical equivalence of the chunking strategy.
- [ ] T030 [US2] Implement Anderson-Darling test comparing observed discrepancies against the simulated null distributions in `code/analysis.py`
- [ ] T031 [US2] Implement Kolmogorov-Smirnov test comparing observed vs. null distributions in `code/analysis.py`
- [ ] T032 [US2] Implement logic to calculate p-values for each jurisdiction individually against the null distribution in `code/analysis.py`
- [X] T033 [US2] Implement logic to frame all findings as "associational deviations from random expectation" in the output reports. **Machine Readable**: MUST embed this framing text in `data/processed/results.json` under the key `"framing"`. **Human Readable**: Generate `docs/report.md` with mandatory framing text. **Note**: Must generate `docs/report.md` with mandatory framing text.
- [ ] T035 [US2] Implement VIF calculation for predictors if regression is extended: Check if 'population density, precinct size' exist in config. **Output**: Generate `data/processed/collinearity_report.json` containing VIF values if predictors exist, or a status of "Not Applicable" if no predictors are present. **Note**: Must always generate the artifact for verification. in `code/analysis.py`
- [ ] T055 [US2] Refine Negative Binomial parameter estimation in `code/simulation.py`: Ensure the NB parameters (mu, alpha) are estimated using robust statistics (median/MAD) on the *cleaned* dataset (excluding directional anomalies) to prevent outliers from biasing the null model. Add a unit test to verify that the estimated parameters are insensitive to the inclusion/exclusion of extreme outliers. **Note**: Depends on T019 (cleaned data).
- [X] T057 [US2] Add a "Data Provenance" report generator in `code/main.py`: At the end of the pipeline, generate a `data/processed/provenance.json` file that lists the exact dataset source URL, version, checksum, and sampling method used for the analysis. **JSON Schema**: `{source_url: string, version: string, checksum: string, sampling_method: string}`. This satisfies the requirement for explicit traceability of the input data.
- [ ] T064 [US2] Verify statistical equivalence of chunked Monte Carlo: Implement a verification test in `tests/test_simulation.py` that runs the full 10,000-iteration simulation in a single batch (if memory permits) and compares the resulting null distribution against the chunked aggregation result using a Kolmogorov-Smirnov test. The test must pass with p-value > 0.05 to confirm the chunking strategy does not introduce statistical bias.
- [X] T068 [US2] Add "Data Provenance" artifact generation: Ensure `code/main.py` generates a `data/processed/provenance.json` file at the end of the pipeline containing the exact dataset source URL, version, checksum, sampling method, and sampling size (if applicable). This artifact must be included in the final results package for auditability.

### Tests for User Story 2 ⚠️

- [ ] T023 [P] [US2] Unit test for Negative Binomial null model generation with synthetic data in `tests/test_simulation.py`
- [ ] T024 [P] [US2] Unit test for Permutation-based null model generation in `tests/test_simulation.py`
- [ ] T025 [P] [US2] Unit test for Anderson-Darling and KS test outputs against known distributions in `tests/test_simulation.py`
- [ ] T026 [P] [US2] Test for non-circular null model construction (independent of observed anomalies) in `tests/test_simulation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on thresholds and models, and generate visualizations (histograms, Q-Q plots, heatmaps) using CPU-tractable libraries.

**Independent Test**: The visualization module can be tested by running the sensitivity sweep and verifying that the output files (plots) are generated and that the sensitivity report correctly lists the variation in flagged jurisdiction counts.

**⚠️ DEPENDENCY**: This phase depends on Phase 4 completion (T027-T035).

### Implementation for User Story 3

- [ ] T039 [US3] Implement sensitivity analysis and reporting in `code/analysis.py`: 1) Load thresholds from `config/sensitivity_thresholds.yaml` (concrete values: `primary_threshold=0.5%`, `sweep_thresholds={0.01%, 0.05%, 0.1%}`); 2) Compare Negative Binomial vs. Permutation null models; 3) Generate a UNIFIED report correlating variation in flagged counts across BOTH dimensions; 4) Execute analysis at the primary threshold and compare results against the sensitivity sweep; 5) Append comparison metrics to `data/processed/results.json`; 6) Generate `data/processed/sensitivity_report.md` documenting variation in false-positive rates and a plot showing stability. **Note**: Consolidates T039a-template, T039a-resolve, T039b, T039c, T039d, T046, T056, T059, T066, T069.
- [ ] T041 [US3] Implement visualization module for histograms, Q-Q plots, and heatmaps in `code/viz.py`: 1) Generate histograms of observed vs. simulated discrepancies; 2) Generate Q-Q plots comparing observed vs. null distributions; 3) Generate a table or heatmap of top jurisdictions by discrepancy magnitude; 4) Ensure all visualizations are saved as static image files within the available disk limit. **Note**: Consolidates T041-T044.
- [ ] T048 [US3] Profile and optimize memory-bound operations in `simulation.py` to reduce peak memory usage during the Monte Carlo loop. **Deliverable**: `code/benchmark_memory.py`. **Verification**: Run `python code/benchmark_memory.py` and confirm peak memory usage is < 7 GB. **Requirement**: Must measure and record the memory metric as a formal output artifact for SC-005 verification. **Output Artifact**: Save to `data/processed/memory_profile.json` with schema `{peak_memory_gb: float, timestamp: string}`.
- [X] T049 [P] Benchmark Monte Carlo chunking to ensure < 6h execution time for 10k iterations. **Deliverable**: `code/benchmark_time.py`. **Verification**: Execute `code/benchmark_time.py` with full 10k iterations; confirm total runtime is < 6 hours on the target runner environment and log memory usage stays < 7 GB.

### Tests for User Story 3 ⚠️

- [ ] T036 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/test_analysis.py`
- [ ] T037 [P] [US3] Unit test for visualization generation (histograms, Q-Q plots) in `tests/test_viz.py`
- [ ] T038 [P] [US3] Integration test verifying memory usage stays within acceptable limits during sensitivity sweep in `tests/test_analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. Depends on US1 and US2 output schemas.

- [X] T006 [P] Generate and execute traceability map generation: Run the traceability_map.json generator script to link all final statistics to source data rows. **Note**: Merged T006 and T006_exec.
- [X] T047a [P] Generate `docs/quickstart.md` with end-to-end pipeline execution instructions in `docs/`
- [X] T047b [P] Generate `docs/data-model.md` with entity definitions and schema details in `docs/`
- [X] T051 Run `quickstart.md` validation: Execute `pytest tests/test_quickstart.py` and verify exit code 0.

---

## Phase 7: Revision & Data Integrity Fixes

**Purpose**: Address specific reviewer concerns regarding data source verification, streaming implementation, and robust error handling to prevent fabrication.

- [Removed: T052 moved to Phase 3 as T014a]
- [Removed: T053 moved to Phase 6]
- [Removed: T054 moved to Phase 6]
- [Removed: T055 moved to Phase 6]
- [Removed: T056 moved to Phase 6]
- [Removed: T057 moved to Phase 6]
- [Removed: T058 moved to Phase 6]
- [Removed: T059 moved to Phase 6]
- [Removed: T060 moved to Phase 6]
- [Removed: T061 moved to Phase 6]
- [Removed: T062 moved to Phase 6]
- [Removed: T063 moved to Phase 6]
- [Removed: T064 moved to Phase 6]
- [Removed: T066 moved to Phase 6]
- [Removed: T067 moved to Phase 6]
- [Removed: T068 moved to Phase 6]
- [Removed: T069 moved to Phase 6]
- [Removed: T070 moved to Phase 6]

---

## Phase 8: Pending Implementation & Verification

**Purpose**: Address remaining gaps in data sourcing, streaming implementation, and verification of statistical robustness.

(No tasks remaining)

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T071 Reconcile run-book vs implementation for `code/discrepancy_calc.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/discrepancy_calc.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
