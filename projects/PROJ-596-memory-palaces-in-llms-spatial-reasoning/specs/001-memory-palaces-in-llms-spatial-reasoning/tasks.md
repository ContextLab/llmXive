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
 **Output**: `docs/power_analysis_report.md` documenting required effect size, assumed variance, and justification for N=5. **Parameters**: Paired t-test, alpha=0.05, assumed effect size (Cohen's d) = 0.5.
- [X] T043 [P] Define the "Jacquard-loom analogy" and "Traversal Sequence" concept in `research.md`. **Requirement**: Must explicitly define the analogy to distinguish between "Memory Palace" (variables) and "Traversal Algorithm" (operations). Must define the "Synaptic Plasticity" mechanism and "Recall Stability under Decay" metric parameters (noise distribution, scaling factor) for future research. **Output**: Updated `research.md` with these definitions. **Note**: This task is for future research planning only; the implementation is deferred. **Note**: This task also defines the "Jacquard-loom analogy" required by T039 (now removed) and the "Traversal Sequence" required by T042 (now removed).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/` directory structure (code, data, artifacts, tests). **Constraint**: Must enforce single-core execution environment (set `OMP_NUM_THREADS=1` and `torch.set_num_threads(1)`) to strictly adhere to Spec Assumptions and SC-007/SC-008.
- [X] T001b Create `.gitignore` and `README.md` placeholders
- [X] T001c Initialize `requirements.txt` with pinned dependencies (including `torch`, `transformers`, `datasets`, `scipy`, `bitsandbytes`, `pandas`, `numpy`, `pyyaml`)
- [X] T001d Create `__init__.py` files for `code/`, `code/models/`, `code/training/`, `code/evaluation/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement dataset download and verification script (`code/data/download.py`) for the three permitted datasets:
 - bAbI Task 3 via `datasets.load_dataset("babi", "task3_10k")`
 - LAMBADA via `datasets.load_dataset("lambada")`
 - Story Cloze Test via `datasets.load_dataset("story_cloze")`
 - Each download must compute and store a SHA‑256 checksum in `data/raw/checksums.json`.
- [X] T005 [P] Implement memory monitoring utility (`code/training/memory_monitor.py`) to track RSS and trigger batch‑size reduction to a lower value and, if RSS > 6 GB at batch size 4, cap the training dataset to **[deferred] of the original** (or the maximum contiguous subset that fits within 6 GB RAM, whichever is smaller) (FR‑010). **Note**: The spec's placeholder is resolved here as [deferred] hard-cap. Must log the decision and final hyperparameters (FR‑003).
- [X] T006 [P] Implement model loading utilities (`code/models/loading.py`) that provide functions to load:
 - `gpt2-medium` (with 4‑bit quantization) when RAM permits (theoretical target),
 - `DistilGPT2` as the primary fallback when the memory budget is exceeded (feasible baseline).
 - **Behavior**: `load_gpt2_medium()` MUST raise an OOM exception if memory is insufficient; it MUST NOT handle fallback internally. The fallback logic resides in the orchestrator (T012).
- [X] T007 [P] Implement 2‑D grid memory slot data structures (`code/models/memory_slot.py`) and EpisodicChunk schema (`code/models/episodic_chunk.py`).
- [X] T007b Implement coordinate assignment logic for episodic chunks (FR‑001). This task must define the algorithm for mapping episodic chunks to (x, y) coordinates in the 2-D grid. **Algorithm**: Sequential row-major mapping. **Overflow Handling**: FIFO eviction (oldest slot overwritten) if capacity (8x8=64) is exceeded. **Prerequisite**: Must be completed before T013 and T014.
- [X] T013 [P] Implement cosine similarity calculation for soft‑addressed retrieval (FR‑002) in `code/models/spatial.py`. **Note**: Moved to Foundational as it is a core utility for the spatial model.
- [X] T008 [P] Configure experiment logging and artifact storage (`code/utils/logger.py`) to write JSON/CSV to `artifacts/results/`.
- [X] T008b Create YAML schema for training run metadata: `artifacts/schemas/training_run.yaml`.
- [X] T008c Draft quickstart guide: `docs/quickstart.md`.
- [X] T008d Draft contracts document: `docs/contracts.md`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Spatial Memory Implementation and Baseline Comparison (Priority: P1) 🎯 MVP

**Goal**: Implement the spatial‑memory transformer variant and baseline, train on bAbI Task 3, and measure exact‑match recall across multiple seeds.

**Independent Test**: Can be fully tested by fine‑tuning both models on bAbI task and measuring exact‑match recall accuracy across multiple random seeds.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for recall metric calculation in `tests/unit/test_metrics.py`
- [X] T011 [P] [US1] Integration test for training loop memory constraints in `tests/integration/test_training_memory.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement DistilGPT2 baseline wrapper (`code/models/base.py`). **Logic**: This task implements the "attempt" logic required by FR-003/US-1. It MUST call `load_gpt2_medium()` (T006). If an OOM exception occurs, it MUST catch the exception, log the deviation in `artifacts/results/hyperparams_log.json`, and then fallback to `DistilGPT2`. The wrapper must expose the same interface as the spatial model; selection logic lives in `code/models/loading.py`. Addresses FR‑001, FR‑002, and the spec's requirement for a baseline non-spatial variant (SC-001). **Note**: T012 catches the exception raised by T006; T006 does NOT handle fallback internally.
- [X] T014 [US1] Implement training loop (`code/training/loop.py`) with adaptive batch size (8 → 4) and, if RSS > 6 GB at batch size 4, cap the dataset to **[deferred] of the original** (or the maximum contiguous subset that fits within 6 GB RAM, whichever is smaller) (FR‑010). **Dependency**: Must call `code/training/memory_monitor.py` (T005) for capping logic. Include detailed logging of memory usage and batch‑size decisions (FR‑003, FR‑010). **Enforce single-core execution** (set `torch.set_num_threads(1)`).
- [X] T015 [P] [US1] Implement evaluation script (`code/evaluation/metrics.py`) to compute exact‑match recall per seed and store results in `artifacts/results/recall_accuracy.json`. **Schema**: `{ "seeds": [int], "accuracies": [float], "mean": float, "std": float }`. **Constraint**: Must use a range of seeds..
- [X] T016 [US1] Implement main execution entry point (`code/main.py`) to orchestrate download → model loading → train (across multiple seeds) → evaluate. **Dependency**: Must run after T014 and T015. Must generate `artifacts/results/run_summary.json` with keys: `seeds` (list of ints), `accuracies` (list of floats), `effective_batch_size` (int), `runtime_seconds` (float). **Note**: This task orchestrates T014 and T015; it depends on their code being available.
- [X] T017 [US1] Log hyperparameters and memory usage per run (including final batch size and any dataset capping) in `artifacts/results/hyperparams_log.json`. **Dependency**: Must run after T014. **Content**: Explicitly note the 6 GB RAM threshold, the logic used for capping ([deferred] hard-cap or max contiguous subset if RSS > 6GB at batch 4), and any deviations (e.g., gpt2-medium fallback). **Note**: Merged from T017a and T017b.
- [X] T017c [US1] Verify total runtime ≤ 5 hours; write `artifacts/results/runtime_report.json` with `runtime_seconds` and a boolean `within_limit`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis Framework with Multiple Comparison Correction (Priority: P2)

**Goal**: Perform paired statistical testing across seeds with multiple‑comparison correction and effect‑size calculation.

**Independent Test**: Can be fully tested by running paired t‑tests on recall accuracy across seeds and verifying p‑values and confidence intervals are computed correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for t‑test and Cohen's d calculation in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement statistical analysis module (`code/evaluation/stats.py`) with paired two‑tailed t‑tests, Shapiro‑Wilk normality check, and fallback to Wilcoxon signed‑rank test.
- [X] T020 [US2] Implement multiple‑comparison correction (Bonferroni or Holm-Bonferroni) for the three dataset comparisons (bAbI, LAMBADA, Story Cloze) (FR‑006). **Logic**: If `min(uncorrected_p_values) < 0.001`, apply Holm-Bonferroni; otherwise apply Bonferroni. This matches the spec's assumption for "overly conservative" cases.
- [X] T021 [US2] Implement effect‑size calculation (Cohen's d) with confidence intervals (FR‑007). Output to `artifacts/results/statistical_summary.json`.
- [X] T022 [US2] Generate statistical summary report `artifacts/results/statistical_summary.json` containing p‑values, corrected p‑values, effect sizes, and confidence intervals for each dataset. **Dependency**: Must run after T015/T016 produce recall accuracy results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Structural Metric Quantification for Spatial Organization (Priority: P2)

**Goal**: Measure and report structural correlates (interference distance, slot occupancy, coordinate variance) to validate spatial organization efficacy.

**Independent Test**: Can be fully tested by computing the interference distance metric and verifying a measurable difference between spatial and non‑spatial variants.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for interference distance calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement interference distance metric in `code/evaluation/metrics.py`. The metric must be computed **separately** for the spatial variant and the non‑spatial baseline, and the results stored in `artifacts/results/interference_distance.json` with fields `spatial`, `baseline`, and `delta`. **Constraint**: Must use the **same dataset samples** for both variants to ensure a valid comparison.
- [X] T025 [P] [US3] Implement slot occupancy distribution logger in `code/evaluation/metrics.py` that records the distribution **per epoch** for each run; output to `artifacts/results/slot_occupancy_epoch_{epoch}.csv`.
- [X] T026 [P] [US3] Implement coordinate variance logger in `code/evaluation/metrics.py` that records variance **per epoch**; output to `artifacts/results/coordinate_variance_epoch_{epoch}.csv`.
- [X] T027 [US3] Extend `code/main.py` to run interference‑injection experiments after standard evaluation. **Mechanism**: Assign semantically unrelated items to *adjacent* grid coordinates (Manhattan distance = 1) as per FR-011. Log results to `artifacts/results/interference_metrics.json` with fields `spatial_recall`, `baseline_recall`, `delta`, and `p_value`. **Dependency**: Must run after T014/T015.
- [X] T028 [US3] Add documentation to `research.md` under a new "Structural Metrics" heading, describing the interference‑distance methodology, slot‑occupancy logging, and coordinate‑variance tracking. **Requirement**: Must link to the specific code implementation in `code/evaluation/metrics.py` to ensure traceability to FR-011.
- [X] T031 [US3] Extend `code/evaluation/metrics.py` to compute a "Spatial Coherence Score" (addressing Rosalind Franklin's concern). **Metric**: Calculate the variance of embedding vectors within adjacent grid cells vs. distant cells (Manhattan distance > 2) to quantify structural organization in latent space. Output to `artifacts/results/spatial_coherence.json`. **Note**: Moved from Phase 6 to Phase 3 as it modifies `code/evaluation/metrics.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Response & Mechanism Formalization (Priority: P2)

**Goal**: Address specific reviewer concerns regarding the binding problem, consolidation mechanisms, and formal mapping between spatial coordinates and transformer architecture.

**Independent Test**: Verification that `research.md` and `spec.md` explicitly define the consolidation mechanism and the address/content mapping, and that code implements a "stabilization" phase or weight-update rule.

### Implementation for Reviewer Concerns

- [X] T029 [US3] Implement a "Consolidation Phase" in `code/training/loop.py` that simulates synaptic stabilization (addressing Eric Kandel's concern). **Mechanism**: After each epoch, apply an Exponential Moving Average (EMA) update (alpha=0.1) to the spatial slot embeddings based on usage frequency, mimicking protein-synthesis stabilization. Log the "stabilization factor" in `artifacts/results/consolidation_log.json`. **Note**: Moved from Phase 6 to Phase 2/3 as it modifies `code/training/loop.py`. Addresses FR-011 (Stability).
- [X] T030 [P] [US3] Implement a formal address-to-content mapping document in `docs/contracts/spatial_mapping.md`. **Content**: Explicitly define the mapping function $f: (x,y) \to \text{AttentionHead}$ using Modulo arithmetic (x%H, y%W) to distinguish between physical location (address) and logical interpretation (content) as per John von Neumann's EDVAC report. **Requirement**: Must also include the definition of the "Traversal Sequence" as a distinct computational layer from the "Spatial Addressing" layer, satisfying John von Neumann's requirement for separating order and quantity. **Note**: This task now includes the "Traversal Sequence" definition previously assigned to T042 (removed). Addresses FR-001.
- [X] T033 [US3] Add a "Stability under Interference" benchmark in `code/evaluation/metrics.py` (addressing Eric Kandel's stability concern). **Metric**: Measure recall accuracy after injecting competing context sequences over multiple time steps to test long-term retention resistance. Log to `artifacts/results/stability_test.json`. Addresses FR-011.
- [X] T034 [US3] Refactor `code/models/spatial.py` to include an auxiliary position-encoder regularizer (addressing David Krakauer's concern). **Mechanism**: Add a regularization term to the loss function that penalizes stochastic divergence in spatial coordinate assignment (L2 norm of coordinate gradients, weight=0.01), ensuring deterministic mapping where required. Addresses FR-001.

**Note**: Tasks T032 and T035 were removed as they lacked traceable Functional Requirements in the spec. T036 was removed as it was rejected and its requirements are now covered by T030. T039, T040, T041, and T042 were removed as part of the Phase 7 cut.

**Checkpoint**: All reviewer concerns regarding mechanism, formalism, and stability are addressed.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 Refactor `code/models/spatial.py` to reduce memory footprint (addressing Eric Kandel concern on structural stability).
- [X] T038 Optimize `code/training/loop.py` to reduce training time (addressing John von Neumann concern on overhead).
- [ ] T039 [P] Additional unit tests for edge cases (dataset mismatch, OOM recovery) in `tests/unit/`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 results** (T015/T016) for statistical comparison
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 results** (T014/T015) for interference injection
- **Phase 6 (Reviewer Response)**: **Depends on US3** (T024-T028) to ensure metrics are available for validation.
- **Phase 7 (Dynamic/Plasticity)**: REMOVED. Concepts defined in T043 (Phase 0).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **T007b** is a prerequisite for T013 and T014.
- **T014/T015** must be completed before T016.
- **T017** must run after T014.
- **T020-T022** must run after T015/T016.

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
4. Add User Story 3 (T024‑T028, T031) → Test independently → Deploy/Demo
5. Add Phase 6 (T029‑T034) → Address Reviewer Concerns → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (T012, T014, T015, T016, T017, T017c)
 - Developer B: User Story 2 (T019, T020, T021, T022)
 - Developer C: User Story 3 (T024, T025, T026, T027, T028, T031)
 - Developer D: Phase 6 (T029‑T034) - Reviewer Response
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
- **Constraint Enforcement**: All tasks involving training or data loading must enforce single-core execution (`OMP_NUM_THREADS=1`, `torch.set_num_threads(1)`) to strictly adhere to the Spec's "single CPU core" constraint.
- **Data Capping Logic**: Where tasks mention capping the dataset, the logic is "[deferred] of the original size" (or max contiguous subset) if RSS > 6 GB at batch size 4 (Resolution of FR-010's placeholder).
- **Baseline Model**: DistilGPT2 is the primary baseline for this project due to hardware constraints; gpt2-medium is the theoretical target. T012 implements the attempt logic for gpt2-medium.
- **Interference Injection**: Must use adjacent grid coordinates (Manhattan distance = 1) as per FR-011.
- **Multiple Comparison Correction**: Use Holm-Bonferroni if min(uncorrected_p) < 0.001, else Bonferroni.
- **Reviewer Specifics**:
 - **Eric Kandel**: Tasks T029 (Consolidation), T033 (Stability), T037 (Memory Footprint) address the need for structural change, stabilization, and the distinction between short/long term memory.
 - **John von Neumann**: Tasks T030 (Formal Mapping + Traversal Sequence), T034 (Regularizer) address the address/content distinction, computational overhead, and the distinction between order and quantity.
 - **Rosalind Franklin**: Task T031 (Spatial Coherence Score) addresses the need for a measurable structural correlate.
 - **David Krakauer**: Task T034 (Regularizer) and T030 (Mapping) address the binding problem and stochastic divergence.
 - **Ada Lovelace**: Task T043 (Research) addresses the distinction between operations and variables and the "weaving" of recall by defining the concepts in `research.md`.
- **Phase 7 Removal Justification**: Phase 7 (Dynamic/Plasticity) and its tasks (T039, T040, T041, T042) were removed to focus on core spatial memory. The specific reviewer concerns related to these tasks are addressed as follows:
 - **Ada Lovelace (Jacquard-loom analogy)**: Addressed by T043 in Phase 0.
 - **Eric Kandel (Synaptic Plasticity/Hebbian)**: Deferred. The "Consolidation Phase" (T029) using EMA is the implemented mechanism.
 - **Eric Kandel (Recall Stability under Decay)**: Deferred. "Stability under Interference" (T033) is the implemented metric.
 - **John von Neumann (Traversal Sequence)**: Addressed by T030 in Phase 6.
- **FR-010 Implementation Note**: The placeholder "[deferred]" in FR-010 is implemented as "[deferred] of the original size" in tasks T005 and T014.