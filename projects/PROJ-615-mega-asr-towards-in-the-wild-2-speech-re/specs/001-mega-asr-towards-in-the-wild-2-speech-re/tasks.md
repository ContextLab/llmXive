# Tasks: Mega-ASR Reproduction & Validation

**Input**: Design documents from `/specs/615-mega-asr-reproduction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with CPU-only dependencies (`torch`, `librosa`, `jiwer`, `pandas`, `scipy`) in `requirements.txt`
- [X] T003 [P] Configure linting and formatting tools (ruff, black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/mega_asr/data_loader.py` with streaming/batching logic: implement a generator yielding batches of 100 samples; if memory usage exceeds the available system capacity, reduce batch size to 50 and retry.
- [X] T005 [P] Implement `src/mega_asr/inference.py` wrapper that enforces CPU-only model loading (no CUDA/bitsandbytes)
- [X] T006 [P] Implement `src/mega_asr/evaluation.py` wrapper for WER calculation using `jiwer`
- [X] T007 Create `data/examples.jsonl` sample dataset with valid audio paths and ground truth text for smoke testing
- [X] T008 Configure environment variables for artifact paths and benchmark selection in `.env.example`
- [X] T022 [P] Implement data sampling logic in `src/mega_asr/data_loader.py` to select N records (500, 1000) using random sampling for benchmark subsets

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Inference Pipeline on Sample Data (Priority: P1) 🎯 MVP

**Goal**: Verify the codebase executes without runtime errors on CPU-only hardware using sample data.

**Independent Test**: Run `scripts/run_inference.py` with `data/examples.jsonl`; verify `results/sample_predictions.jsonl` is generated with non-empty text fields.

### Implementation for User Story 1

- [X] T011 [US1] Implement `scripts/run_inference.py` entry point with `--input` and `--output` arguments
- [X] T012 [US1] Integrate `src/mega_asr/inference.py` to load Mega-ASR checkpoint on CPU without requiring CUDA or GPU acceleration
- [X] T013 [US1] Add error handling for missing audio files and unsupported codecs in `src/mega_asr/inference.py`: log a structured warning containing the file path and error type to `results/error_report.json`, skip the specific record, and continue processing the rest of the batch.
- [X] T014 [US1] Ensure output JSONL contains `transcription` field for every valid audio entry

### Tests for User Story 1 (Mandatory)

> **NOTE**: These tests must run AFTER T011/T012 generate the output file.

- [X] T009 [US1] Contract test for inference output schema in `tests/contract/test_inference_schema.py`
- [X] T010 [US1] Integration smoke test for CPU execution in `tests/integration/test_smoke_sample.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute and Report Word Error Rate (WER) (Priority: P2)

**Goal**: Validate the metric engine by comparing predictions against ground truth labels.

**Independent Test**: Run `scripts/evaluate_predictions.py` against sample predictions; verify stdout contains a WER float value.

### Implementation for User Story 2

- [X] T017 [US2] Implement `scripts/evaluate_predictions.py` with `--predictions` and `--ground_truth` arguments
- [X] T018 [US2] Integrate `src/mega_asr/evaluation.py` to calculate WER using Levenshtein distance
- [X] T019 [US2] Add validation to ensure prediction and ground truth lengths match (or handle misalignment gracefully)
- [X] T020 [US2] Format and print summary report including WER value to stdout

### Tests for User Story 2 (Mandatory)

- [X] T015 [P] [US2] Unit test for WER calculation alignment with `jiwer` in `tests/unit/test_wer_calculation.py`
- [X] T016 [US2] Contract test for evaluation report schema in `tests/contract/test_evaluation_schema.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Paper Benchmark Results (Priority: P3)

**Goal**: Validate paper claims on a statistically representative sample of the VOiCES/NOIZEUS benchmarks.

**Independent Test**: Execute pipeline on a sampled benchmark subset; verify WER is reported with a "Sampled" label.

### Implementation for User Story 3

- [X] T023 [US3] Update `scripts/run_inference.py` and `scripts/evaluate_predictions.py` to accept benchmark configuration (e.g., `--benchmark voices-r4-b-f`)
- [X] T024 [US3] Add logic to label results as "Sampled" in the final report to maintain scientific rigor, referencing N values from T022
- [X] T025 [US3] Ensure batch processing prevents OOM errors on the 7GB RAM runner (implement memory check: if peak RAM > 6.5GB, reduce batch size to 50 and retry; verify peak RAM < 6.5GB)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Metric Stability Analysis (Priority: P3)

**Goal**: Address reviewer concern regarding "allometric scaling" by measuring metric stability (WER variance) across sample sizes (N=100, 500, 1000) rather than deriving a scaling exponent.

**Independent Test**: Generate a report showing WER variance across sample sizes and compare against paper's claims.

### Implementation for Metric Stability Analysis

- [X] T027 [US3] Implement `scripts/analyze_stability.py` to run inference/evaluation iteratively on increasing sample sizes (N=100, 500, 1000) using logic from T022
- [X] T028 [US3] Generate `results/stability_analysis.json` containing keys: `sample_size`, `wer`, `compute_time`, `timestamp`, `benchmark_name`, `is_sampled`
- [X] T029 [US3] Write `research.md` section interpreting the Metric Stability (WER variance) relative to sample size, acknowledging scaling laws are out of scope
- [X] T039 [P] Document the Sampling Strategy (random vs. stratified, N values) in `docs/sampling_strategy.md` as required by SC-005

**Checkpoint**: Research validation complete; stability concerns addressed with empirical data.

---

## Phase 7: CI Enforcement & Validation (Priority: P1)

**Goal**: Ensure the project adheres to the 6-hour CI limit and data integrity requirements.

- [X] T036 [P] Implement CI timeout configuration (GitHub Actions `timeout-minutes`) and a watchdog script to enforce the time limit

The research question, the method, and the references remain unchanged as required.
- [X] T037 [P] Implement latency instrumentation in `scripts/run_inference.py` to measure inference time per sample and validate against the total time limit (SC-001)
- [X] T038 [P] Implement explicit input/output record counting and integrity validation in `scripts/evaluate_predictions.py` to ensure all valid input records produce output (SC-004)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/` and `README.md`
- [X] T032 Code cleanup and refactoring of wrapper scripts
- [X] T033 Performance optimization for audio loading and batch processing
- [X] T034 [P] Additional unit tests for edge cases (corrupted checkpoints, empty files) in `tests/unit/`
- [X] T035 Run `quickstart.md` validation to ensure full pipeline reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Metric Stability Analysis (Phase 6)**: Depends on US3 completion and T022 (Sampling Logic)
- **CI Enforcement (Phase 7)**: Can run in parallel with final integration
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output format
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 logic
- **Metric Stability Analysis (Phase 6)**: Depends on US3 to provide benchmark data and T022 for sampling logic

### Within Each User Story

- Core implementation before integration
- Implementation before tests (Tests must run after implementation generates data)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All unit tests marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

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
5. Add Metric Stability Analysis → Analyze stability data → Final Report
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI (limited vCPU and RAM). No GPU, no 8-bit quantization, no full dataset loading.
- **Ordering**: Tests (T009, T010, T016) must run AFTER their respective implementation tasks (T011, T012, T017, T018). T009/T010 are NOT parallel with T011/T012. T016 is NOT parallel with T017/T018.
- **Memory Fallback**: T004 and T025 explicitly define the fallback logic (batch size 100 -> 50) if RAM > 6.5GB.
- **CI Limit**: T036/T037 enforce the 6-hour limit.
- **Data Integrity**: T038 enforces record counting.