# Tasks: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Input**: Design documents from `/specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY - the spec's User Stories define specific "Independent Test" scenarios that must be implemented.

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

- [X] T001b Define the "Spatial Organization" concept in `research.md`. **Requirement**: Must explicitly define the spatial organization mechanism as per FR-001. **Output**: Updated `research.md` under the section header `## Conceptual Framework`. **Note**: This task defines the spatial organization mechanism required for conceptual clarity; implementation details are deferred. **Conceptual Note**: While analogies like "Jacquard-loom" or "Traversal Sequence" may be used in documentation for clarity, they are NOT implementation requirements and must not be confused with the FR-001 implementation. **Specific Content**: The definition must reference FR-001 explicitly in the first sentence and state that the mechanism uses a "Learned Embedding Lookup" based on content, not a deterministic hash. **Status**: Definition Complete (Implementation Deferred).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/` directory structure (code, data, artifacts, tests). **Constraint**: Must enforce single-core execution environment (set `OMP_NUM_THREADS=1` and `torch.set_num_threads()`) to strictly adhere to Spec Assumptions and SC-007/SC-008.
- [X] T001c Create `.gitignore` and `README.md` placeholders
- [X] T001d Initialize `requirements.txt` at `projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/code/requirements.txt` with pinned dependencies (including `torch`, `transformers`, `datasets`, `scipy`, `bitsandbytes`, `pandas`, `numpy`, `pyyaml`). **Constraint**: Path must exactly match FR-012.
- [X] T001e Create `__init__.py` files for `code/`, `code/models/`, `code/training/`, `code/evaluation/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement dataset download and verification script (`code/data/download.py`) for the three permitted datasets:
 - bAbI Task via `datasets.load_dataset("babi", "task3_10k")`
 - LAMBADA via `datasets.load_dataset("lambada")`
 - Story Cloze Test via `datasets.load_dataset("story_cloze")`
 - Each download must compute and store a cryptographic hash checksum in `data/raw/checksums.json`.
- [X] T005a [P] Implement memory monitoring utility (`code/training/memory_monitor.py`) to track RSS and trigger batch‑size reduction. **Logic**: Must measure process RSS after each batch. If RSS > 6.0 GB, signal the trainer to reduce batch size. **Output**: `memory_log.json` with peak RSS per batch. **Constraint**: Must not handle capping logic; only monitoring and signaling.
- [X] T005b [P] Implement dataset capping logic (`code/data/capper.py`) to cap the training dataset to the **maximum contiguous subset that fits within 6 GB RAM** (FR‑010) if RSS > 6 GB at batch size 4. **Algorithm**: Binary search on sample count to find the largest N such that RSS < 6GB at batch size 4. **Fallback**: If even a single sample exceeds memory, the system MUST raise a `RuntimeError` with a clear message; it must not return an empty dataset or loop. **Output**: Log `subsampling_rate` and `cap_reason` in `training_run.schema.yaml`. **Dependency**: Must be callable by T014c. **Deviation Note**: This task implements a "maximum contiguous subset" logic as a necessary adaptation to Principle VI (Computational Constraints) because a fixed percentage is infeasible without knowing dataset size.
- [X] T006 [P] Implement model loading utilities (`code/models/loading.py`) that provide functions to load:
 - `gpt2-medium` (with 4‑bit quantization) when RAM permits.
 - **Behavior**: `load_gpt2_medium()` MUST raise an OOM exception if memory is insufficient; it MUST NOT handle fallback internally. The fallback logic (dataset capping) resides in the orchestrator (T014c). **Note**: DistilGPT2 is NOT implemented as a fallback to preserve the experimental subject.
- [X] T007 [P] Implement 2‑D grid memory slot data structures (`code/models/memory_slot.py`) and EpisodicChunk schema (`code/models/episodic_chunk.py`).
- [X] T013 [P] Implement cosine similarity calculation for soft‑addressed retrieval (FR‑002) in `code/models/spatial.py`. **Note**: Moved to Foundational as it is a core utility for the spatial model. **Independence**: This task is independent of T036 and can run in parallel. **Dependency**: None.
- [X] T036 [P] Implement coordinate assignment logic for episodic chunks (FR‑001). This task must define the algorithm for mapping episodic chunks to (x, y) coordinates in the 2-D grid using a **Learned Embedding Lookup** based on content. **Algorithm**: Content-based learned embedding lookup. **Overflow Handling**: FIFO eviction (oldest slot overwritten) if capacity (8x8=64) is exceeded. **Constraint**: MUST NOT use deterministic hash or modulo arithmetic. **Prerequisite**: Must be completed before T014a and T024. **Dependency**: T013 (for similarity calculation).
- [X] T008 [P] Configure experiment logging and artifact storage (`code/utils/logger.py`) to write JSON/CSV to `artifacts/results/`.
- [X] T008b Create YAML schema for training run metadata: `artifacts/schemas/training_run.yaml`.
- [X] T008c Draft quickstart guide: `docs/quickstart.md`.
- [X] T008d Draft contracts document: `docs/contracts.md`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Spatial Memory Implementation and Baseline Comparison (Priority: P1) 🎯 MVP

**Goal**: Implement the spatial‑memory transformer variant and baseline, train on bAbI Task 3, and measure exact‑match recall across multiple seeds.

**Independent Test**: Can be fully tested by fine‑tuning both models on bAbI task and measuring exact‑match recall accuracy across multiple random seeds.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Note on Parallelism**: While marked [P] for parallel *writing*, these tests cannot *execute* until T014a/T014c are complete.

- [X] T010 [P] [US1] Contract test for recall metric calculation in `tests/unit/test_metrics.py`
- [X] T011 [P] [US1] Integration test for training loop memory constraints in `tests/integration/test_training_memory.py`
- [X] T039a [P] [US1] Unit test for OOM recovery and capping logic in `tests/unit/test_oom_recovery.py`.
- [X] T039b [P] [US1] Unit test for dataset mismatch handling in `tests/unit/test_dataset_mismatch.py`.
- [X] T039c [P] [US1] Unit test for interference injection logic in `tests/unit/test_intervention.py`.

### Implementation for User Story 1

- [X] T012a [US1] Implement **Non-Spatial Baseline** wrapper (`code/models/base.py`). **Logic**: This task implements the standard non-spatial baseline (GPT-2 medium) without any external memory buffer. It serves as the primary control for the spatial effect. **Constraint**: Must NOT include a memory buffer. If OOM occurs, the system must cap the dataset as per FR-010. **Dependency**: T006. **Note**: This is the baseline required to isolate the "external memory benefit" confound.
- [X] T012b [US1] Implement **Non-Spatial External Memory Buffer** control variant (`code/models/base.py`). **Logic**: This task implements the control variant with a non-spatial external memory buffer (no spatial grid) to isolate the "external memory benefit" confound as per US-1. **Constraint**: Must NOT use spatial coordinates. If OOM occurs, the system must cap the dataset as per FR-010. **Dependency**: T006. **Note**: This task is distinct from T012a.
- [X] T014a [US1] Implement training loop skeleton (`code/training/loop.py`) with basic forward/backward pass. **Dependency**: Must call `code/models/loading.py` (T006) and `code/models/spatial.py` (T013/T036).
- [X] T014b [US1] Integrate memory monitoring (`code/training/memory_monitor.py` from T005a) into the training loop. **Logic**: Must measure RSS after each batch and signal batch size reduction if RSS > 6.0 GB.
- [X] T014c [US1] Integrate dataset capping logic (`code/data/capper.py` from T005b) into the training loop. **Logic**: If RSS > 6 GB at batch size 4, wrap the dataset loader to yield only the maximum contiguous subset fitting in 6GB. **Dependency**: Must call T005b.
- [X] T014d [US1] Implement detailed logging of memory usage and batch‑size decisions (FR‑003, FR‑010). **Dependency**: Must run after T014b and T014c.
- [ ] T015 [P] [US1] Implement evaluation script (`code/evaluation/metrics.py`) to compute exact‑match recall per seed and store results in `artifacts/results/recall_accuracy.json`. **Schema**: `{ "seeds": [int], "accuracies": [float], "mean": float, "std": float }`. **Constraint**: Must use a range of seeds. **Note**: This task is a consumer of T014's output artifacts (model checkpoints). <!-- FAILED: unspecified -->
- [X] T016a [US1] Implement download and model loading orchestration (`code/main.py` part 1). **Logic**: Must handle dataset fetching and model loading for spatial, non-spatial baseline (T012a), and non-spatial buffer control (T012b) variants.
- [X] T016b [US1] Implement training orchestration (`code/main.py` part 2). **Logic**: Must run T0 across multiple seeds for all three variants.
- [X] T016c [US1] Implement evaluation and reporting orchestration (`code/main.py` part 3). **Logic**: Must run T015, compute hyperparameter logs, verify runtime ≤ 5 hours (log deviation to `run_summary.json` if exceeded), and generate `artifacts/results/run_summary.json`. **Dependency**: Must run after T016b. **Content**: Explicitly note the 6 GB RAM threshold, the logic used for capping (**maximum contiguous subset** if RSS > 6GB at batch 4), and any deviations. **Failure Mode**: If runtime > 5 hours, the script MUST abort, log the violation, and exit with a non-zero code. **Correction**: Removed `runtime_report.json` generation; runtime status is logged to `run_summary.json`.
- [X] T017 [US1] Log hyperparameters and memory usage per run (including final batch size and any dataset capping) in `artifacts/results/hyperparams_log.json`. **Dependency**: Must run after T014d. **Content**: Explicitly note the 6 GB RAM threshold, the logic used for capping (**maximum contiguous subset** if RSS > 6GB at batch 4), and any deviations. **Note**: Merged from T017a and T017b.

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
- [X] T040b [US2] Implement validation pipeline script (`scripts/validate_quickstart.sh`) to ensure `artifacts/results/run_summary.json` is generated and validated against the schema. **Requirement**: Must fail if `run_summary.json` is missing or invalid. **Dependency**: T016c must be completed.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Structural Metric Quantification for Spatial Organization (Priority: P2)

**Goal**: Measure and report structural correlates (interference distance, slot occupancy, coordinate variance) to validate spatial organization efficacy.

**Independent Test**: Can be fully tested by computing the interference distance metric and verifying a measurable difference between spatial and non‑spatial variants.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for interference distance calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement interference distance metric in `code/evaluation/metrics.py`. **Logic**: The metric must be computed **separately** for the spatial variant and the non‑spatial baseline. **Requirement**: Must assign semantically unrelated items (similarity < 0.2) to *adjacent* grid coordinates (Manhattan distance = 1) for the spatial model, and to random indices for the non-spatial model. **Output**: Store results in `artifacts/results/interference_distance.json` with fields `spatial_recall`, `baseline_recall`, `delta`, and `p_value`. **Constraint**: Must use the **same dataset samples** for both variants to ensure a valid comparison. **Dependency**: Must run after T014a-d (trained models). **Correction**: Dependency updated to rely on artifact availability, not T016c completion.
- [ ] T025 [P] [US3] Implement slot occupancy distribution logger in `code/evaluation/metrics.py` that records the distribution **per epoch** for each run; output to `artifacts/metrics/slot_occupancy_epoch_{epoch}.json`. **Format**: JSON list of integers.
- [ ] T026 [P] [US3] Implement coordinate variance logger in `code/evaluation/metrics.py` that records variance **per epoch**; output to `artifacts/metrics/coordinate_variance_epoch_{epoch}.json`. **Format**: JSON object with variance fields.
- [X] T027 [US3] Extend `code/main.py` to run interference‑injection experiments after standard evaluation. **Mechanism**: Call T024 to compute the metric. Log results to `artifacts/results/run_summary.json` (appended to existing data). **Dependency**: MUST depend on the **existence** of the trained model artifact produced by T014a-d. **Correction**: Removed dependency on T016c completion to allow parallel execution. Removed `interference_metrics.json` artifact requirement; results appended to `run_summary.json`.
- [ ] T028 [P] [US3] Add documentation to `research.md` under a new "Structural Metrics" heading, describing the interference‑distance methodology, slot‑occupancy logging, and coordinate‑variance tracking. **Requirement**: Must link to the specific code implementation in `code/evaluation/metrics.py` to ensure traceability to FR-011.
- [X] T049 [US3] Update `research.md` to include a "Structural Correlate Validation" section (addressing Rosalind Franklin's structural concern). **Content**: Define the "Spatial Coherence Score" metric (a quantitative measure of latent space organization) and describe the control condition where spatial organization is removed. Must include a clear prediction about how this metric correlates with episodic recall performance. **Requirement**: Must link to the implementation of the interference distance metric (T024) as the primary experimental validation of this hypothesis. **Dependency**: Must run after T024 to ensure the metric is implemented and available for validation. **Note**: Moved from Phase 6 to Phase 5 to ensure US3 is independently shippable. **Checkpoint Note**: T049 is the final step of US3.

**Note**: Tasks T032 and T035 were removed as they lacked traceable Functional Requirements in the spec. T036 was removed as it was rejected and its requirements are now covered by T036 (Phase 2). T039, T040, T041, and T042 were removed as part of the Phase 7 cut. T029 (EMA) was removed as it was scope creep. T033, T034, T047, T048 were removed as scope creep or spec violations.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Response & Mechanism Formalization (Priority: P2)

**Goal**: Address specific reviewer concerns regarding the binding problem, consolidation mechanisms, and formal mapping between spatial coordinates and transformer architecture.

**Independent Test**: Verification that `research.md` and `spec.md` explicitly define the consolidation mechanism and the address/content mapping, and that code implements a "stabilization" phase or weight-update rule.

### Implementation for Reviewer Concerns

- [X] T030 [P] [US3] Implement a formal address-to-content mapping document in `docs/contracts/spatial_mapping.md`. **Content**: Explicitly define the mapping function based on **Learned Embedding Lookup** (as implemented in T036) to distinguish between physical location (address) and logical interpretation (content) as per John von Neumann's EDVAC report. **Requirement**: Must also include the definition of the "Traversal Sequence" as a distinct computational layer from the "Spatial Addressing" layer, satisfying John von Neumann's requirement for separating order and quantity. **Note**: This task documents the logic implemented in T036. Addresses FR-001. **Correction**: Removed the requirement for a direct $f: (x,y) \to \text{AttentionHead}$ mapping as it is outside the spec's scope.

**Note**: Tasks T031, T044, T045, T046 were removed as scope creep. T029 was removed as it was scope creep. T033, T034, T047, T048 were removed as scope creep or spec violations.

**Checkpoint**: All reviewer concerns regarding mechanism, formalism, and stability are addressed.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 Refactor `code/models/spatial.py` to reduce memory footprint (general optimization). **Note**: This is a general optimization task and does NOT re-implement any deferred mechanisms (e.g., Stabilization Phase, Hebbian rules) which were removed as scope creep.
- [X] T038 Optimize `code/training/loop.py` to reduce training time (addressing John von Neumann concern on overhead). <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->

**Note**: Tasks T044 (Traversal Sequence), T045 (Computational Cost), T046 (Synaptic Plasticity) were removed as they implemented unapproved metrics and mechanisms not in the spec.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Phase 6 (Reviewer Response)**: **Depends on US3** (T024-T028, T049) to ensure metrics are available for validation.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 results** (T015/T016) for statistical comparison
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 results** (T014/T015) for interference injection
- **Phase 6 (Reviewer Response)**: **Depends on US3** (T024-T028, T049) to ensure metrics are available for validation.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **T036** is a prerequisite for T014a and T024.
- **T014a-d** must be completed before T015 and T016b.
- **T016c** must run after T016b.
- **T020-T022** must run after T015/T016.
- **T040b** must run after T016c to validate the summary.
- **T049** must run after T024.
- **T027** must run after T014a-d (training).
- **T055, T056, T057, T058** were removed as part of Phase 8 removal.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **T039a, T039b, T039c** can run in parallel as they test distinct edge cases.
- **T014a, T014b, T014c, T014d** can run in parallel as they implement distinct components of the training loop.
- **T016a, T016b, T016c** can run in parallel as they implement distinct stages of the orchestration.
- **T055, T057** can run in parallel as they test distinct properties (stability vs. cost) on the same trained models. **Note**: These tasks are removed.

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
2. Add User Story 1 (T012a‑T012b, T014a-d, T015, T016a-c, T017) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (T019‑T022, T040b) → Test independently → Deploy/Demo
4. Add User Story 3 (T024‑T028, T049) → Test independently → Deploy/Demo
5. Add Phase 6 (T030) → Address Reviewer Concerns → Deploy/Demo
6. **Phase 7 and Phase 8 are REMOVED** to adhere to spec constraints.
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (T012a, T012b, T014a-d, T015, T016a-c, T017)
 - Developer B: User Story 2 (T019, T020, T021, T022, T040b)
 - Developer C: User Story 3 (T024, T025, T026, T027, T028, T049)
 - Developer D: Phase 6 (T030) - Reviewer Response
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
- **Data Capping Logic**: Where tasks mention capping the dataset, the logic is **maximum contiguous subset** (via binary search) if RSS > 6 GB at batch size 4 (Resolution of FR-010's placeholder). **Deviation Note**: This is a necessary adaptation to Principle VI (Computational Constraints) as a percentage-based cutoff is infeasible without knowing dataset size.
- **Baseline Model**: Non-Spatial Baseline (T012a) and Non-Spatial External Memory Buffer Control (T012b) are the required variants. T012a is the standard baseline; T012b isolates the buffer effect.
- **Interference Injection**: Must use adjacent grid coordinates (Manhattan distance = 1) as per FR-011.
- **Multiple Comparison Correction**: Use Holm-Bonferroni if min(uncorrected_p) < 0.001, else Bonferroni.
- **Reviewer Specifics**:
 - **Eric Kandel**: Tasks T033 (Stability) and T047 (Stabilization Phase) were removed as they were scope creep. T029 (EMA) was removed as scope creep. **Phase 7 (T050, T051, T053)** and **Phase 8 (T055, T056)** were **REMOVED** as they implemented deferred mechanisms. The consolidation and stability concerns are out of scope for this iteration.
 - **John von Neumann**: Tasks T030 (Formal Mapping + Traversal Sequence) and T048 (Cost Analysis - removed) address the address/content distinction. T030 now focuses on the learned embedding lookup as per spec. **Phase 7 (T054)** and **Phase 8 (T057, T058)** were **REMOVED** as they implemented deferred mechanisms.
 - **Rosalind Franklin**: Task T031 (Spatial Coherence Score) was removed as scope creep; FR-011 (Interference Distance) is the mandated metric. **Phase 7 (T052)** was **REMOVED**. **Phase 5 (T049)** addresses the structural concern by defining a measurable correlate and control condition.
 - **David Krakauer**: Task T034 (Regularizer - removed) and T030 (Mapping) address the binding problem and stochastic divergence. **Phase 7 (T054)** was **REMOVED**.
 - **Ada Lovelace**: Task T043 (Research) was removed as it defined deferred mechanisms. The "Jacquard-loom analogy" is defined in T001b as a conceptual aid only. **Status**: Definition Complete (Implementation Deferred).
- **Phase 7 & 8 Removal Justification**: Phase 7 (T050-T054) and Phase 8 (T055-T058) were **REMOVED** to focus on core spatial memory and adhere to the spec's explicit deferral of binding architectures, formal mapping, and alternative metrics. The specific reviewer concerns related to these tasks are addressed as follows:
 - **Eric Kandel (Synaptic Plasticity/Hebbian)**: **REMOVED** as scope creep. The spec explicitly defers binding architectures.
 - **Eric Kandel (Recall Stability under Decay)**: **REMOVED** as scope creep. The spec explicitly defers alternative metrics.
 - **John von Neumann (Traversal Sequence)**: Addressed by T001b and T030 in Phase 0/6 as a documentation requirement only.
 - **John von Neumann (Computational Cost)**: Addressed by T048 (removed) as it was not required. **Phase 8 (T057)** was **REMOVED**.
 - **Rosalind Franklin (Structural Correlate)**: Addressed by FR-011 (Interference Distance), T049. **Phase 7 (T052)** was **REMOVED**.
 - **T044 (Computational Cost Profiler)**: Removed as scope creep. However, T014 and T015 now include instrumentation hooks (latency logging) that would support T044 if re-added, resolving the dependency logic concern.
 - **T045 (Structural Validation)**: Removed as scope creep.
 - **T046 (Refactor spatial_mapping.md)**: Removed as scope creep.
- **FR-010 Implementation Note**: The placeholder "[deferred]" in FR-010 is implemented as "maximum contiguous subset" (via binary search) in tasks T005a, T005b, and T014c. **Deviation Note**: This is a necessary adaptation to Principle VI (Computational Constraints) as a percentage-based cutoff is infeasible without knowing dataset size.
- **Removed Tasks**: T033, T034, T043, T047, T048, T050, T051, T052, T053, T054, T055, T056, T057, T058, T059, T060, T061, T062, T063 were removed due to scope violations or lack of spec authorization. T004b was removed as it forced a parameter not in the spec.
- **Artifact Correction**: `runtime_report.json` and `interference_metrics.json` are no longer generated. Runtime status is logged to `run_summary.json`. Interference results are appended to `run_summary.json`.
