# Tasks: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Input**: Design documents from `/specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/`
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

## Phase 0: Research (Preparatory)

- [X] T004b Perform a priori power analysis for the planned random seeds.
 **Output**: `docs/power_analysis_report.md` documenting required effect size, assumed variance, and justification for N=5.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/` directory structure (code, data, artifacts, tests)
- [X] T001b Create `.gitignore` and `README.md` placeholders
- [X] T001c Initialize `requirements.txt` with pinned dependencies (including `torch`, `transformers`, `datasets`, `scipy`, `bitsandbytes`, `pandas`, `numpy`, `pyyaml`)
- [X] T001d Create `__init__.py` files for `code/`, `code/models/`, `code/training/`, `code/evaluation/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement dataset download and verification script (`code/data/download.py`) for the three permitted datasets:
 - bAbI Task 3 via `datasets.load_dataset("babi", "task3_10k")`
 - LAMBADA via `datasets.load_dataset("lambada")`
 - Story Cloze Test via `datasets.load_dataset("story_cloze")`
 - Each download must compute and store a SHA‑256 checksum in `data/raw/checksums.json`.
- [X] T005 [P] Implement memory monitoring utility (`code/training/memory_monitor.py`) to track RSS and trigger batch‑size reduction to 4 and, if RSS still > 6 GB, cap the training dataset to [deferred] of its original size. Must log the decision and final hyperparameters (FR‑).
- [X] T006 Implement model loading utilities (`code/models/loading.py`) that provide functions to load:
 - `gpt2-medium` (with 4‑bit quantization) when RAM permits,
 - `DistilGPT2` as a fallback when the memory budget is exceeded.
- [X] T007 [P] Implement 2‑D grid memory slot data structures (`code/models/memory_slot.py`) and EpisodicChunk schema (`code/models/episodic_chunk.py`).
- [ ] T007b Implement coordinate assignment logic for episodic chunks (FR‑001).
- [X] T008 [P] Configure experiment logging and artifact storage (`code/utils/logger.py`) to write JSON/CSV to `artifacts/results/`.
- [X] T008b Create YAML schema for training run metadata: `artifacts/schemas/training_run.yaml`.
- [X] T008c Draft quickstart guide: `docs/quickstart.md`.
- [X] T008d Draft contracts document: `docs/contracts.md`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Spatial Memory Implementation and Baseline Comparison (Priority: P1) 🎯 MVP

**Goal**: Implement the spatial‑memory transformer variant and baseline, train on bAbI Task 3, and measure exact‑match recall across multiple seeds.

**Independent Test**: Can be fully tested by fine‑tuning both models on bAbI task and measuring exact‑match recall accuracy across 5 random seeds.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for recall metric calculation in `tests/unit/test_metrics.py`
- [X] T011 [P] [US1] Integration test for training loop memory constraints in `tests/integration/test_training_memory.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement gpt2‑medium baseline wrapper (`code/models/base.py`) **and** DistilGPT2 fallback (`code/models/base_fallback.py`). The wrapper must expose the same interface; selection logic lives in `code/models/loading.py`. Addresses FR‑001, FR‑002, and the spec’s requirement for a gpt2‑medium baseline (with documented fallback).
- [X] T013 [P] [US1] Implement cosine similarity calculation for soft‑addressed retrieval (FR‑002) in `code/models/spatial.py`.
- [X] T014 [US1] Implement training loop (`code/training/loop.py`) with adaptive batch size (8 → 4) and, if RSS > 6 GB at batch size 4, cap the dataset to [deferred] of its size. Include detailed logging of memory usage and batch‑size decisions.
- [ ] T015 [US1] Implement evaluation script (`code/evaluation/metrics.py`) to compute exact‑match recall per seed and store results in `artifacts/results/recall_accuracy.json`.
- [ ] T016 [US1] Implement main execution entry point (`code/main.py`) to orchestrate download → model loading → train (across seeds ‑4) → evaluate. Must generate `artifacts/results/run_summary.json` with keys: `seeds`, `accuracies`, `effective_batch_size`, `runtime_seconds`.
- [ ] T017a [US1] Log hyperparameters and memory usage per run (including final batch size and any dataset capping) in `artifacts/results/hyperparams_log.json`. Must run after T014.
- [ ] T017b [US1] Record final effective hyperparameters and any deviations (e.g., batch‑size reduction, dataset capping) in `artifacts/results/hyperparams_log.json`, explicitly noting the 6 GB RAM threshold (FR‑003).
- [ ] T017c [US1] Verify total runtime ≤ 5 hours; write `artifacts/results/runtime_report.json` with `runtime_seconds` and a boolean `within_limit`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis Framework with Multiple Comparison Correction (Priority: P2)

**Goal**: Perform paired statistical testing across seeds with multiple‑comparison correction and effect‑size calculation.

**Independent Test**: Can be fully tested by running paired t‑tests on recall accuracy across seeds and verifying p‑values and confidence intervals are computed correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for t‑test and Cohen's d calculation in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement statistical analysis module (`code/evaluation/stats.py`) with paired two‑tailed t‑tests, Shapiro‑Wilk normality check, and fallback to Wilcoxon signed‑rank test.
- [ ] T020 [US2] Implement multiple‑comparison correction (Bonferroni or Holm‑Bonferroni) for the three dataset comparisons (bAbI, LAMBADA, Story Cloze) (FR‑006).
- [~] T021 [US2] Implement effect‑size calculation (Cohen's d) with 95 % confidence intervals (FR‑007).
- [ ] T022 [US2] Generate statistical summary report `artifacts/results/statistical_summary.json` containing p‑values, corrected p‑values, effect sizes, and confidence intervals for each dataset.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Structural Metric Quantification for Spatial Organization (Priority: P2)

**Goal**: Measure and report structural correlates (interference distance, slot occupancy, coordinate variance) to validate spatial organization efficacy.

**Independent Test**: Can be fully tested by computing the interference distance metric and verifying a measurable difference between spatial and non‑spatial variants.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for interference distance calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [~] T024 [P] [US3] Implement interference distance metric in `code/evaluation/metrics.py`. The metric must be computed **separately** for the spatial variant and the non‑spatial baseline, and the results stored in `artifacts/results/interference_distance.json` with fields `spatial`, `baseline`, and `delta`.
- [X] T025 [P] [US3] Implement slot occupancy distribution logger in `code/evaluation/metrics.py` that records the distribution **per epoch** for each run; output to `artifacts/results/slot_occupancy_epoch_{epoch}.csv`.
- [X] T026 [P] [US3] Implement coordinate variance logger in `code/evaluation/metrics.py` that records variance **per epoch**; output to `artifacts/results/coordinate_variance_epoch_{epoch}.csv`.
- [~] T027 [US3] Extend `code/main.py` to run interference‑injection experiments after standard evaluation, log results to `artifacts/results/interference_metrics.json`, and ensure the file includes both variant results and statistical significance.
- [~] T028 [US3] Add documentation to `research.md` under a new “Structural Metrics” heading, describing the interference‑distance methodology, slot‑occupancy logging, and coordinate‑variance tracking.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T029 [P] Documentation updates: Add formal mapping between spatial “rooms” and transformer components (addressing John von Neumann concern on formal mapping).
- [X] T030 Refactor `code/models/spatial.py` to reduce memory footprint (addressing Eric Kandel concern on structural stability).
- [X] T031 Optimize `code/training/loop.py` to reduce training time (addressing John von Neumann concern on overhead).
- [~] T032 [P] Additional unit tests for edge cases (dataset mismatch, OOM recovery) in `tests/unit/`.
- [~] T033 [P] Run quickstart validation: execute `./scripts/validate_quickstart.sh` which runs a minimal end‑to‑end pipeline and checks that `artifacts/results/run_summary.json` is produced within the 5‑hour limit.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 results for statistical comparison
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 results for interference injection

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
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

1. Complete Setup + Foundational together
2. Add User Story 1 (T012‑T017c) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (T019‑T022) → Test independently → Deploy/Demo
4. Add User Story 3 (T024‑T028) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (T012, T013, T014, T015, T016, T017a‑c)
 - Developer B: User Story 2 (T019, T020, T021, T022)
 - Developer C: User Story 3 (T024, T025, T026, T027, T028)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **Reviewer Concerns Addressed**:
 - Ada Lovelace: T028 clarifies spatial coordinates as “variables” vs “operations”.
 - Dan Rockmore: T020 ensures standardized recall tests and multiple‑comparison correction.
 - David Krakauer: T013/T028 addresses binding problem via soft‑addressed retrieval and auxiliary position‑encoder regularization.
 - Eric Kandel: T014/T025/T027 address consolidation via consistent training, slot‑occupancy logging, and stability under interference metrics.
 - John von Neumann: T013/T017a/T029 formalizes addressing scheme, quantifies overhead, and maps spatial “rooms” to transformer components.
 - Rosalind Franklin: T024 defines the quantitative “interference distance” metric to distinguish spatial organization from arbitrary embeddings.