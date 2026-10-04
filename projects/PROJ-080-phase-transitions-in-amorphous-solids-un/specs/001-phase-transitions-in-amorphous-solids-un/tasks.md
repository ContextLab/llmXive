---
description: "Task list template for feature implementation"
---

# Tasks: Phase Transitions in Amorphous Solids Under Shear Stress

**Input**: Design documents from `/specs/001-phase-transitions-in-amorphous-solids/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a-dirs [P] Create project structure per implementation plan: Create directories `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `specs/contracts`, `state` in `projects/PROJ-phase-transitions-in-amorphous-solids/`.
- [ ] T001a-schemas [P] Create schema files `specs/contracts/trajectory.schema.yaml` and `specs/contracts/output.schema.yaml` with the following EXACT content:
  ```yaml
  # trajectory.schema.yaml
  type: object
  required: [particles, box_dimensions, stress_tensor, timesteps]
  properties:
    particles:
      type: array
      minItems: 1
      items:
        type: object
        required: [x, y, z]
        properties:
          x: {type: number}
          y: {type: number}
          z: {type: number}
    box_dimensions:
      type: object
      required: [Lx, Ly, Lz]
      properties:
        Lx: {type: number}
        Ly: {type: number}
        Lz: {type: number}
    stress_tensor:
      type: array
      items:
        type: array
        items: {type: number}
    timesteps: {type: integer, minimum: 1}
    metadata:
      type: object
      properties:
        checksum: {type: string, pattern: "^[a-f0-9]{64}$"}
        source: {type: string}
  ```
  ```yaml
  # output.schema.yaml
  type: object
  required: [d2_min, yield_flags, metadata]
  properties:
    d2_min:
      type: array
      items:
        type: object
        required: [particle_id, value]
        properties:
          particle_id: {type: integer}
          value: {type: number}
    yield_flags:
      type: object
      required: [timestep, stress_value]
      properties:
        timestep: {type: integer}
        stress_value: {type: number}
    metadata:
      type: object
      required: [checksum, source]
      properties:
        checksum: {type: string}
        source: {type: string}
  ```
- [ ] T001b [P] Initialize Python 3.11 project with pytest, ruff, black, and mypy dependencies in `pyproject.toml`.
- [ ] T001c [P] Configure linting and formatting tools: Setup `ruff.toml` for linting, `pyproject.toml` [tool.black] for formatting, and `mypy.ini` for type checking.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Implement `code/utils.py` with global `SEED = 42` and specific streaming helpers: `def stream_hdf5(path, chunk_size)` and `def stream_parquet(path, chunk_size)`. These functions must yield data chunks to ensure memory usage stays within acceptable limits for large files, satisfying FR-006.
- [ ] T004 Configure logging infrastructure to capture warnings for indeterminate trajectories (US1) using Python's `logging` module with file handlers.
- [ ] T005 [P] Setup environment configuration for dataset source verification (HuggingFace `materials-science/amorphous-silicon-shear-trajectories`) including verified URL and checksum validation logic. **Instruction**: Do not hardcode checksums. The task must include a script to fetch the dataset, compute the SHA-256 hash, and store it in `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml` for future validation.
- [ ] T006 [P] Implement `code/data_generator.py`: Synthetic MD trajectory generation. **Constraint**: Must generate particle coordinates, box dimensions, stress tensors, and assign "brittle" or "ductile" labels based on physical simulation parameters (strain rate, temperature). **Output**: `data/raw/synthetic_trajectory_*.h5` and `data/raw/metadata.json`. **Dependency**: T002.
- [ ] T007 [P] Implement `code/data_loader.py`: HuggingFace Streaming Implementation. **Constraint**: Must use `datasets.load_dataset(..., streaming=True)` for real data. **Dependency**: T002, T006 (Must verify T006 output exists before attempting fallback).

---

## Phase 3: Data Ingestion & Verification

**Goal**: Ensure the pipeline has a verified, accessible real data source, falling back to synthetic data ONLY if real data is missing, and computing checksums for state tracking.

- [ ] T008 [P] [US1] **DATA SOURCE VERIFICATION & FALLBACK**: Implement `code/data_loader.py` to attempt fetching the `materials-science/amorphous-silicon-shear-trajectories` dataset from HuggingFace using `datasets.load_dataset("materials-science/amorphous-silicon-shear-trajectories", split="train", streaming=True)`. **Constraint**: **PRIMARY PATH**: If the fetch fails (network error, missing repo, or invalid ID), the code MUST catch the specific library exceptions (`datasets.exceptions.DatasetNotFoundError`, `ConnectionError`) and **immediately fallback to loading the Synthetic Data Generator output** from `data/raw/` (generated by T006). **Critical**: If fallback occurs, the script MUST log "SYNTHETIC FALLBACK ACTIVE" and set a flag in the output metadata. **Dependency**: T006, T007.
- [ ] T009 [P] [US1] **DATA STREAMING IMPLEMENTATION**: Implement streaming logic in `code/data_loader.py` to process trajectories in chunks. **Constraint**: Must explicitly state the streaming strategy: Use `datasets.load_dataset(..., streaming=True)` with a fixed chunk size of 1000 timesteps or 100MB, whichever is smaller, to ensure memory usage < 1GB per chunk. **Dependency**: T008.
- [ ] T010 [P] [US1] **CHECKSUM COMPUTATION**: Implement a checksum computation step in `code/data_loader.py` that calculates the SHA hash of the downloaded/generated file and **writes the result to `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml`** under the `artifact_hashes` key. **Constraint**: This task must run after T008 and before T011. **Dependency**: T008.
- [ ] T011 [US1] **CHECKSUM VALIDATION**: Implement a checksum verification step in `code/data_loader.py` that compares the downloaded/generated file hash against the known value stored in `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml` using the SHA-256 algorithm. **Constraint**: If the hash file is missing, the script MUST run T010 to generate it for the current data source. If T010 fails or the hash mismatch occurs, raise a `FatalError` and halt execution. **Dependency**: T008, T009, T010.
- [ ] T011b [P] [Data Hygiene] **SYNTHETIC DATA VALIDATION**: Implement a checksum validation step for synthetic data files in `data/raw/` to ensure data integrity before loading. This task should verify the SHA-256 hash of each synthetic trajectory file against a pre-calculated checksum stored in `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml`. If the checksums do not match, raise an exception and halt execution. This is a critical data hygiene step to prevent the use of corrupted synthetic data. **Dependency**: T006, T010.

---

## Phase 4: User Story 1 - Precursor Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw MD trajectory data, compute $D^2_{min}$ and local shear strain, and identify the yielding timestep.

**Independent Test**: Process a single small trajectory (≤ 10,000 steps) and verify the output CSV contains per-particle $D^2_{min}$ and a flagged yielding index.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T012 [P] [US1] Unit test for Falk-Langer $D^2_{min}$ calculation in `tests/unit/test_preprocess.py`
- [ ] T013 [P] [US1] Integration test for stress-drop detection logic in `tests/unit/test_preprocess.py`
- [ ] T014 [US1] Integration test for "indeterminate" flagging when stress drop is ambiguous in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 1

- [ ] T015a [US1] Implement `code/preprocess.py`: Create streaming loader function for HDF5/Parquet files. **MUST enforce FR-006**: Check particle count; if > 100k, raise an explicit `ValueError` with message "ValueError: Particle count exceeds limit 100000" and exit with code 1. No synthetic fallbacks. **Function Signature**: `def load_and_validate_trajectory(path: str) -> TrajectoryData`. **Dependency**: T002, T008.
- [ ] T015b [US1] Implement `code/preprocess.py`: Implement neighbor list builder for particle proximity calculation. **Function Signature**: `def build_neighbor_list(coordinates: np.ndarray, cutoff: float) -> NeighborList`. **Dependency**: T015a.
- [ ] T015c [US1] Implement `code/preprocess.py`: Implement Falk-Langer $D^2_{min}$ calculation loop for every particle (FR-001). **Function Signature**: `def compute_d2_min(current_coords: np.ndarray, prev_coords: np.ndarray, neighbor_list: NeighborList) -> np.ndarray`. **Dependency**: T015b.
- [ ] T016a [US1] Implement `code/preprocess.py`: Implement stress-strain curve extraction from trajectory data. **Function Signature**: `def extract_stress_curve(stress_tensor: np.ndarray) -> np.ndarray`. **Dependency**: T015a.
- [ ] T016b [US1] Implement stress-drop detection algorithm to flag yielding onset (FR-002). **Logic**: Detect the first drop > 5% relative to the local maximum stress occurring over the preceding 50 timesteps. **Function Signature**: `def detect_yielding(stress_curve: np.ndarray) -> int`. **Dependency**: T016a.
- [ ] T016c-verify [US1] **STRICT ENFORCEMENT**: Implement logic to verify the 50-timestep window and local maximum calculation. **Constraint**: If multiple drops occur, ignore subsequent ones. This task replaces the removed T037 to strictly adhere to FR-002's single-yield requirement. **Algorithm**: Explicitly verify `local_max` is computed over `t-50:t` and `stress[t] < local_max * 0.95`. **Dependency**: T016b.
- [ ] T017 [US1] Implement `code/preprocess.py`: Flag datasets as "indeterminate" if no sharp stress peak is found and log warnings
- [ ] T018 [P] [US1] Implement robust error handling in `code/preprocess.py` for corrupted or incomplete trajectory files (missing frames, NaN values)
- [ ] T019 [P] [US1] Add numerical stability checks in `code/preprocess.py` to detect and handle NaN/Infinity values in $D^2_{min}$ calculations (e.g., due to neighbor list issues)
- [ ] T020 [P] [US1] Add unit tests for edge cases: corrupted files, missing frames, NaN values in `tests/unit/test_preprocess.py`
- [ ] T021 [US1] Write output artifacts: `data/processed/precursor_metrics.csv` (per-particle $D^2_{min}$) and `data/processed/yield_flags.json` (yielding timestep). **Dependency**: T015a, T015b, T015c, T016a, T016b, T016c-verify, T017, T018, T019, T008, T009, T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compare $D^2_{min}$ distributions between brittle and ductile trajectories to identify structural precursors.

**Independent Test**: Run analysis on two labeled datasets (brittle, ductile) and verify output includes KS-test statistic and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test for shear-band aggregation logic in `tests/unit/test_analysis.py`
- [ ] T023 [P] [US2] Unit test for **Kolmogorov-Smirnov Test** implementation in `tests/unit/test_analysis.py`. **Note**: Spec FR-003 mandates KS-test. The test must verify the KS-test logic. **Dependency**: T025.
- [ ] T024 [P] [US2] Integration test for "Power Limitation" warning when sample size < 30 in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 2

- [ ] T025 [US2] **SHEAR BAND AGGREGATION**: Aggregate $D^2_{min}$ values to shear bands using k-means clustering (k=3, seed=42) and write `data/processed/shear_band_stats.csv` with columns `shear_band_id`, `mean_D2_min`, `particle_count`. **Constraint**: This artifact is required for the KS-Test in US2. **Algorithm**: Use `sklearn.cluster.KMeans(n_clusters=3, random_state=42)`. **Dependency**: T021.
- [ ] T026 [US2] **MANDATORY**: Perform a **Kolmogorov-Smirnov (KS) Test** to compare brittle vs. ductile distributions of shear-band mean $D^2_{min}$ values. **Rationale**: Spec FR-003 explicitly mandates a KS-test. **Constraint**: The implementation MUST log an "Amendment Note" to the execution log stating: "KS-Test applied per Spec FR-003. If Permutation Test is required, a formal spec amendment must be approved first." **Algorithm**: Perform the KS-test with random seed 42. The output must frame the result as an "associational finding" as per Spec. **Output**: `data/processed/ks_test_results.json` containing the observed statistic, p-value, and metadata. **Dependency**: T025.
- [ ] T026-amend [P] [US2] **SPEC AMENDMENT TASK**: If the team decides to switch from KS-Test to Permutation Test, this task must be executed to formally amend `spec.md` FR-003 and `plan.md` before implementation. **Output**: Updated `spec.md` and `plan.md` with the amendment. **Dependency**: T026.
- [ ] T027 [US2] Check sample size (N ≥ 30). If < 30, halt and report "Power Limitation" warning (US2 Acceptance). **Context**: N refers to the number of shear bands (aggregated units). **Dependency**: T025.
- [ ] T028a [US2] **MANDATORY ENFORCEMENT**: Implement conditional logic to detect if **more than one hypothesis test** is performed. **Logic**: Count the total number of distinct (strain_rate, temperature) combinations analyzed in the current run. **Source**: Metadata is extracted from `data/raw/metadata.json` (T006) or HuggingFace dataset metadata. **Keys**: `strain_rate`, `temperature`. **Fallback**: If keys missing, assume multiple_tests=True and count=N (conservative) and apply Bonferroni correction. **Output**: A boolean flag `multiple_tests` and the count of tests. **Dependency**: T006, T008, T026.
- [ ] T028 [US2] **MANDATORY ENFORCEMENT**: **Enforce** Bonferroni correction (FR-005) to the KS-Test p-values **ONLY IF** `multiple_tests` is true (from T028a). **Logic**: The system MUST apply the correction only when the count > 1. **Output**: `data/processed/corrected_p_values.json`. **Dependency**: T028a, T026.
- [ ] T029 [US2] Generate output artifacts: `data/processed/ks_test_results.json` (statistic, p-value), `data/processed/histograms.png` (overlay of distributions), and `data/processed/significance_report.json` (final p-value vs alpha=0.05 pass/fail). **Dependency**: T028. **Note**: This task MUST explicitly compare the corrected p-value against the alpha=0.05 threshold and write a pass/fail determination to the report, satisfying SC-002.
- [ ] T029b [P] [US2] **THRESHOLD EXTRACTION**: Extract the derived threshold value from the analysis results (e.g., from `ks_test_results.json` or `significance_report.json`) and save it to `data/processed/derived_threshold.json`. **Constraint**: This artifact is required for T032a-split. **Dependency**: T029.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Predictive Threshold Validation (Priority: P3)

**Goal**: Validate a specific $D^2_{min}$ threshold for predicting time-to-failure and perform sensitivity analysis.

**Independent Test**: Apply derived threshold to held-out validation set and verify FPR/FNR and F-score are reported correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_predict.py`
- [ ] T031 [P] [US3] Integration test for confusion matrix generation in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T032a-deriv [US3] **LABEL DERIVATION**: Implement logic to derive "brittle" or "ductile" labels from global mechanical response metrics (e.g., total strain at failure) if they are missing in `metadata.json`. **Constraint**: If labels are present in metadata, use them. If missing, compute them based on the threshold defined in the spec: Use 'total strain at failure' from metadata. If missing, compute from stress curve as the strain at the point where stress drops below [deferred] of peak. **Output**: Updated `metadata.json` or in-memory label array. **Dependency**: T006, T008.
- [ ] T032a-deriv-verify [US3] **LABEL VALIDATION**: Implement logic to VERIFY that derived labels match the 'brittle'/'ductile' definitions in the Spec (e.g., total strain at catastrophic failure) before use in US2/US3. **Constraint**: If labels do not match expected definitions, raise a `ValueError` and halt. **Output**: Validation report. **Dependency**: T032a-deriv.
- [ ] T032a-split [US3] **MANDATORY**: Derive the base threshold value from US1/US2 outputs **AND** perform a hold-out split on the dataset to create a validation set. **Algorithm**: Select the D_min value that maximizes F-score on the **training set ONLY**. **Constraint**: Once derived, the threshold value MUST be **frozen** and stored before any access to the validation set to prevent data leakage. **Split Method**: Use `sklearn.model_selection.train_test_split` with `test_size=0.2`, `random_state=42`, and `stratify=y` (where y is the brittle/ductile label). **Source**: Labels are derived from `data/raw/metadata.json` (T006/T008) or via T032a-deriv. **Input**: `data/processed/derived_threshold.json` (from T029b). **Output**: `data/processed/validation_set_indices.json` and the derived `threshold_value`. **Dependency**: T021, T029, T029b, T032a-deriv, T032a-deriv-verify, T008.
- [ ] T032a-eval [US3] **MANDATORY**: Execute the prediction model on the held-out validation set and record the F-score. **Algorithm**: Apply the frozen threshold (from T032a-split) to the validation set. Calculate F-score, FPR, FNR. **Output**: `data/processed/validation_metrics.json`. **Dependency**: T032a-split.
- [ ] T032b [US3] Define 'time-to-failure' as an independent ground truth (total strain at catastrophic failure)
- [ ] T033 [US3] Sweep $D^2_{min}$ threshold over the specific range. **Logic**: The research question remains: How can we establish a dynamic threshold for anomaly detection? The method involves calculating a lower bound as the threshold minus 0.05 and an upper bound as the threshold plus 0.05. The sweep range is defined as a small interval around the threshold, encompassing values slightly below, at, and slightly above the threshold. **Constraint**: The `threshold` in this range MUST be the **derived threshold value output by T032a-split**. **Output**: Generate intermediate data structure and `data/processed/sensitivity_table.csv` containing the sweep results. **Dependency**: T032a-split.
- [ ] T034 [US3] Calculate False Positive Rate (FPR), False Negative Rate (FNR), **True Positives (TP), True Negatives (TN), and F-score (F1)** for each threshold step. **MANDATORY**: Generate `data/processed/sensitivity_table.csv` containing the full sweep results (threshold, FPR, FNR, F1) to satisfy FR-004's requirement for a comparative table. **Dependency**: T032a-split, T033.
- [ ] T035 [US3] Generate output artifacts: `data/processed/prediction_results.json` (confusion matrix, F-score, FPR, FNR), `data/processed/sensitivity_table.csv`. **Dependency**: T034.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Performance & Validation (Cross-Cutting)

**Purpose**: Ensure the pipeline meets runtime and memory constraints on the target CI environment.

- [ ] T036a [P] [SC-004] Implement `code/metrics.py`: Runtime instrumentation wrapper to measure execution time
- [ ] T037a [P] [SC-005] Implement `code/metrics.py`: Peak memory tracking logic
- [ ] T038 [SC-004, SC-005] Execute full pipeline on GitHub Actions runner to verify runtime and memory constraints. **Requirement**: Must run only after T021, T029, T035 are complete. **Requirement**: Must invoke instrumentation logic from T036a/T037a to capture metrics. **Requirement**: Must verify runtime is ≤ **6 hours** as per SC-004. **Requirement**: Must verify memory is ≤ **7GB** as per SC-005. **Measurement Tool**: Use `resource` module for runtime and `memory_profiler` library for memory. **Behavior**: If runtime > 6 hours or memory > 7GB, the script MUST generate `data/processed/performance_report.json` with `status: "WARN"`, `reason: "Runtime/Memory exceeded limit"`, and the measured duration/usage, and log a warning. It should NOT exit with code 1 unless the limit is exceeded by >20%. **Dependency**: T021, T029, T035, T036a, T037a.
- [ ] T039 [P] Generate `data/processed/performance_report.json` with all measured outcomes

**Dependencies**: T038 depends on T036a and T037a being implemented AND T021, T029, T035 being complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Ingestion (Phase 3)**: **Must be completed before Phase 4 (US1) and Phase 5 (US2)**. T021 depends on T008-T011.
- **User Stories (Phase 4+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Statistical Robustness (Phase 5)**: Can run in parallel with Phase 4, but depends on T021 completion.
- **Predictive Validation (Phase 6)**: Depends on T032a-split and T032a-eval completion.
- **Real Data Integration (Phase 2/3)**: Must run after Phase 2 (Foundational) and before Phase 3 (Data Ingestion) implementation to ensure streaming logic is in place.
- **Robustness & Edge Cases**: Can run in parallel with Phase 4-6, but must be completed before final integration testing (T038).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories, but requires Phase 3 (Data Ingestion) to be complete for data availability.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 output** (`precursor_metrics.csv` from T021 and `shear_band_stats.csv` from T025). T025, T026 require T021 completion.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US1 and US2 outputs**. T032a-split requires T029b completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Phase 7 tasks marked [P] can run in parallel with their respective dependencies met.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, cross-story dependencies that break independence
- **Data Integrity**: Ensure `code/preprocess.py` fails loudly if real data fetch fails; fallback to synthetic data ONLY if real data is missing (T008).
- **Memory Safety**: All data loading must use streaming/chunking to stay under available RAM constraints (T007, T009).
- **Execution Order**: T036a/T037a must be completed before T038; T038 must be completed before T039. T021 must be completed before T025/T026.
- **Constraint Preservation**: Spec FR-003 mandates KS-Test. T026 implements KS-Test. T026-amend handles potential future amendments.
- **Critical Dependencies**: T021 requires T016b and T008 to be complete. T034 requires T032a-split to be complete.
- **New Phase 0**: Addresses the requirement to "STREAM the real data" and handle large datasets without memory overflow or synthetic fallbacks, ensuring compliance with the "Real data + real results only" rule.
- **New Phase 2**: Addresses edge cases related to corrupted data, missing frames, and numerical instability, ensuring the pipeline fails loudly and predictably as required by the "fail loud" policy.
- **Correction**: T006 and T007 are now in Phase 2 (Foundational) to ensure data generation and streaming logic are ready before ingestion.
- **Correction**: T008 (Data Source Verification) now prioritizes Synthetic Data Generator output as per Plan's 'Critical Scope Adjustment'.
- **Correction**: T010 writes to `state/projects/PROJ-080-phase-transitions-in-amorphous-solids-un.yaml` instead of the schema file, resolving the contradiction of a static schema holding dynamic data.
- **Correction**: T025 now uses fixed k=3 for determinism.
- **Correction**: T026 implements KS-Test per Spec FR-003, with a mandatory log note for the Spec deviation if Permutation Test is considered later.
- **Correction**: T032a-split now requires `stratify=y` to ensure class balance.
- **Correction**: T011 now explicitly computes hash if missing, preventing validation against an empty value.
- **New Phase 3**: Addresses the requirement to "STREAM the real data" and handle large datasets without memory overflow or synthetic fallbacks, ensuring compliance with the "Real data + real results only" rule.
- **Correction**: T025 is the single source of truth for shear-band aggregation. T021b removed.
- **Correction**: T032a-deriv added to handle label derivation if missing.
- **Correction**: T028a now includes explicit key names and fallback logic.
- **Correction**: T029 no longer outputs `sensitivity_table.csv`.
- **Correction**: T032a-split now requires `stratify=y` to ensure class balance.
- **Correction**: T032a-deriv-verify added to validate derived labels.
- **Correction**: T001a is split into T001a-dirs and T001a-schemas.
- **Correction**: T032a-eval explicitly defines the validation set and the evaluation metrics.
- **New Task**: T029b added to extract and save the derived threshold value.
- **Correction**: T038 updated to report warnings instead of hard failing, aligning with Spec measurement intent.
- **Correction**: T011b (formerly T040) moved to Phase 3 with explicit dependencies.
- **Correction**: T007 [P] tag removed to ensure T006 completion before fallback logic runs.