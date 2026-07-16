# Tasks: Quantifying the Impact of Data Resolution on Gravitational Wave Signal Detection

**Input**: Design documents from `/specs/001-quantifying-the-impact-of-data-resolutio/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- **[Depends: T###]**: Explicit dependency on another task ID to enforce data flow order

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p src tests data/raw data/processed data/profiling contracts state`.
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (pycbc, scipy, numpy, pandas, gwosc, pytest, memory-profiler, scikit-learn)
- [ ] T003 [P] Configure linting and formatting: Create `ruff.toml` (rules E, F, I) and `pyproject.toml` (black config) at repository root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create JSON schemas in `contracts/`: `contracts/injection.schema.yaml` (fields: resolution, snr, re_weighted_snr, timestamp, noise_segment_id) and `contracts/detection_metric.schema.yaml` (fields: p_value, method, detection_probability, resolution, n_injections).
- [X] T005 [P] Implement `src/config.py` with global seeds, paths, and resolution targets (, 2048, 1024, 512, 256 Hz)
- [ ] T006a [P] Implement `src/data_hygiene.py` to generate SHA256 checksums for all files in `data/` and write them to `state/checksums.json` in the format `{file_path: hash}`.
- [ ] T006b [P] Implement `data-hygiene.sh` shell script that calls `src/data_hygiene.py` and writes the final checksum record to `state/checksums.json` (Constitution Principle III).
- [ ] T007 [P] Create `src/schema_validator.py` with a function `validate_json(data, schema_path)` that raises `ValueError` on mismatch, and add a CLI entry point to validate a specific file against a schema.
- [ ] T008 [P] Implement `src/profiler.py` (FR-006) with memory monitoring (hard limit substantial capacity). **Critical**: If peak memory usage exceeds 6GB during any batch, abort the current batch, exit with code 1, and write a detailed log to `data/profiling/memory_error.log`.
- [X] T009 Setup `pytest` configuration and `tests/contract/test_schemas.py` to verify schema enforcement

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Down-sample Simulated BBH Waveforms (Priority: P1) 🎯 MVP

**Goal**: Generate diverse non-spinning BBH waveforms at a high sampling frequency and down-sample them to multiple resolution levels. using anti-aliasing FIR filters with amplitude correction.

**Independent Test**: Generate a single waveform, down-sample to a target sampling rate, verify via FFT that aliasing artifacts are suppressed to negligible levels relative to the signal peak. and that the Nyquist limit is respected.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test `test_downsample_anti_aliasing` in `tests/unit/test_downsample.py` (verify FFT spectral content)
- [ ] T011 [P] [US1] Unit test `test_waveform_generation_range` in `tests/unit/test_waveform_gen.py` (verify mass/distance ranges)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/waveform_gen.py` (FR-001) to generate non-spinning BBH waveforms (low to high mass, 100–500 Mpc) at 4096 Hz using `pycbc.waveform`
- [ ] T013 [US1] [Depends: T012] Implement `src/downsample.py` (FR-002) to apply FIR low-pass filters (cutoff = fs/2). **Critical**: Calculate the theoretical frequency response H(f) of the filter, then pre-scale the waveform amplitude by $1/|H(f_{peak})|$ before decimation to isolate resolution loss from filter attenuation (Plan: Filter Confound Control).
- [ ] T014 [US1] [Depends: T012, T013] Implement `src/downsample.py` pipeline logic to produce A small set of distinct files per waveform: **Copy** the native output of T012 as the 4096 Hz file (no re-processing) and **generate** 4 down-sampled files (2048, 1024, 512, 256 Hz) with metadata tagging.
- [ ] T015 [US1] Add validation in `src/downsample.py` to ensure no frequency components exceed the measured RMS noise floor of the specific segment by more than 10 dB (SC-004). **Critical**: Calculate RMS noise floor of the target segment and assert that aliased components > Nyquist are < 10 dB above this floor, raising an error if violated.
- [ ] T016 [US1] Integrate `src/schema_validator.py` to validate down-sampled waveform metadata before saving to `data/processed/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Inject Signals and Compute Matched-Filter SNR (Priority: P2)

**Goal**: Inject down-sampled waveforms into real GWOSC noise segments and compute matched-filter SNR and re-weighted SNR ($\hat{\rho}$) using resolution-matched template banks and PSDs.

**Independent Test**: Inject a high-SNR signal at 4096 Hz and 256 Hz; verify recovered SNR matches injected value within 1% at 4096 Hz and is lower but valid at 256 Hz.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `test_psd_re_estimation` in `tests/unit/test_matched_filter.py` (verify PSD is rate-specific)
- [ ] T019 [P] [US2] Integration test `test_injection_recovery` in `tests/integration/test_pipeline.py` (verify SNR recovery)

### Implementation for User Story 2

- [ ] T020 [US2] [Depends: T014] Implement `src/injection.py` (FR-003) to fetch real GWOSC noise segments, inject waveforms at random time offsets (with a minimum separation interval), and **explicitly generate injection realization metadata** (random seeds, time offsets, specific noise segment IDs) for reproducibility and statistical analysis.
- [ ] T021a [US2] [Depends: T020] Implement `src/injection.py::run_pilot(N=20)` to execute a pilot injection run and return the empirical standard deviation ($\sigma_{emp}$).
- [ ] T021b [US2] [Depends: T021a] Implement `src/injection.py::calculate_final_n(sigma, target_power=0.8)` to calculate the required sample size N based on $\sigma_{emp}$, **capped at 200**, to achieve power ≥ 0.8.
- [ ] T022 [US2] [Depends: T020] Implement `src/matched_filter.py` (FR-004, FR-008) to compute matched-filter SNR. **Critical**: Must use **resolution-matched template banks** (generate/load banks specific to each sampling rate: high, medium, and low frequencies) to ensure scientific soundness.
- [ ] T023 [US2] Implement `src/matched_filter.py` logic to calculate re-weighted SNR $\hat{\rho} = \rho / \sqrt{ + (\chi^/df)^2}$ with 16 frequency bins
- [ ] T024 [US2] Implement `src/matched_filter.py` to re-estimate PSD for each specific sampling rate (critical for correct SNR)
- [ ] T025 [US2] Integrate `src/profiler.py` to record CPU/Memory usage per injection run
- [ ] T026 [US2] Validate output rows against `detection_metric.schema.yaml` before writing to `data/processed/injections.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Detection Probability and Compute Resource Metrics (Priority: P3)

**Goal**: Calculate detection probability (re-weighted SNR > 8) per resolution, profile resources, and perform statistical tests (Welch's t-test, Mann-Whitney U) to confirm SNR degradation.

**Independent Test**: Run analysis on a small subset; verify detection probability matches manual count and resource metrics are non-zero and proportional to data size.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test `test_statistical_tests` in `tests/unit/test_analysis.py` (verify p-value calculation and Bonferroni correction)
- [ ] T029 [P] [US3] Unit test `test_detection_threshold` in `tests/unit/test_analysis.py` (verify [deferred]/50%/10% curve calculation)

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `src/analysis.py` (FR-005) to calculate detection probability (fraction of $\hat{\rho} > 8$) per resolution level
- [ ] T031a [US3] [Depends: T026] Implement `src/analysis.py` to perform **Jonckheere-Terpstra test** as the **primary verification method** for monotonic SNR degradation (SC-001, FR-007).
- [ ] T031b [US3] [Depends: T031a] Implement `src/analysis.py` to perform **Welch's t-tests with Bonferroni correction** for adjacent pairs (secondary check) AND implement the **Mann-Whitney U fallback test** (conditional on Shapiro-Wilk normality test failure).
- [ ] T032 [US3] Implement `src/analysis.py` to compute detection probability curves and identify "knee" points: **Implement logistic regression for curve fitting; if data points < 3, fallback to linear interpolation between 10%, 50%, 90% thresholds** as per SC-002.
- [ ] T033 [US3] Implement `src/analysis.py` to aggregate resource metrics (CPU time, memory) and compute efficiency trade-off guidelines (FR-006, SC-003)
- [ ] T034 [US3] Implement stratified analysis logic (SNR bins: 8-12, 12-20, >20) for all statistical tests
- [ ] T035 [US3] Validate final aggregated metrics against schema and write to `data/processed/analysis_results.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `specs/001-quantifying-the-impact-of-data-resolutio/quickstart.md`
- [ ] T037 Code cleanup and refactoring (remove unused imports, optimize loops for h limit)
- [ ] T038 Performance optimization: ensure data streaming to respect system memory constraints
- [ ] T039 [P] Add unit test `tests/unit/test_injection.py::test_glitch_handling` for edge case handling of transient glitches
- [ ] T040 [P] Add unit test `tests/unit/test_downsample.py::test_phase_distortion_check` for edge case handling of filter phase distortion
- [ ] T041 Run `quickstart.md` validation and verify all acceptance criteria pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **CRITICAL DATA FLOW**: While tasks are grouped by Phase, the data flow enforces strict ordering:
 - US1 (Phase 3) MUST complete before US2 (Phase 4) can begin (Waveforms -> Injection). **T020 explicitly depends on T014**.
 - US2 (Phase 4) MUST complete before US3 (Phase 5) can begin (Injections -> Analysis). **T031a explicitly depends on T026**.
 - The "Parallel Team Strategy" below is only valid if the team respects these data dependencies (i.e., Developer C cannot start until Developer B finishes).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 outputs (down-sampled waveforms) - **Cannot start until T014 is complete**
- **User Story 3 (P3)**: Depends on US2 outputs (injection results) - **Cannot start until T026 is complete**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Core implementation before integration
- Story complete before moving to next priority
- **Explicit Task Ordering**:
 - US1: T012 -> T013 -> T014
 - US2: T020 -> T021a -> T021b -> T022 -> T023 -> T024 -> T025 -> T026
 - US3: T030 -> T031a -> T031b -> T032 -> T033 -> T034 -> T035

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- **Note**: Different user stories CANNOT be worked on in parallel by different team members unless the team explicitly manages the data hand-off (e.g., Developer B finishes US1 before Developer C starts US2).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test test_downsample_anti_aliasing in tests/unit/test_downsample.py"
Task: "Unit test test_waveform_generation_range in tests/unit/test_waveform_gen.py"

# Launch all models for User Story 1 together (after T012/T013 logic is ready):
Task: "Implement src/waveform_gen.py (FR-001)..."
Task: "Implement src/downsample.py (FR-002)..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify anti-aliasing and file generation)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Requires US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (Requires US2 data)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy (Data-Flow Aware)

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Waveforms)
 - Developer B: User Story 2 (Injection/SNR) - **Waits for Developer A (T014)**
 - Developer C: User Story 3 (Analysis/Stats) - **Waits for Developer B (T026)**
3. Stories complete and integrate sequentially based on data flow, not just phase grouping.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Feasibility**: All tasks designed for CPU-only (limited vCPU, GB RAM). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: All tasks use real GWOSC data; no synthetic/fake data generation for input.
- **Statistical Rigor**: Power analysis (configurable pilot -> full) and Bonferroni correction implemented as per plan.
- **Ordering**: Explicit dependencies [Depends: T###] added to enforce correct data flow (Producer before Consumer).