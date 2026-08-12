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

- [X] T004b Perform a priori power analysis for the planned random seeds. **Output**: Append to `docs/power_analysis_report.md` under section "Power Analysis" documenting required effect size, assumed variance, and justification for N=5. **Parameters**: Paired t-test, alpha=0.05, assumed effect size (Cohen's d) = 0.5. **Action**: Calculate required N for power=0.8, alpha=0.05, d=0.5 using `scipy.stats.power.t_test_power` and document if N > 5.
- [X] T043 [P] Define the "Jacquard-loom analogy" and "Traversal Sequence" concept in `research.md`. **Requirement**: Must explicitly define the analogy to distinguish between "Memory Palace" (variables) and "Traversal Algorithm" (operations). Must define the "Synaptic Plasticity" mechanism and "Recall Stability under Decay" metric parameters (noise distribution, scaling factor) for future research. **Output**: Updated `research.md` with these definitions. **Note**: This task is for future research planning only; the implementation is deferred. **Note**: This task also defines the "Jacquard-loom analogy" required by T039 (now removed) and the "Traversal Sequence" required by T042 (now removed).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/` directory structure (code, data, artifacts, tests). **Constraint**: Must enforce single-core execution environment ONLY if RSS > 6GB or if the runner has only 1 core. Check `os.cpu_count()`; if > 1, set `OMP_NUM_THREADS` to respect the runner's core capability while staying within the RAM limit. Do NOT unconditionally set `torch.set_num_threads(1)` unless memory pressure is detected.
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
- [X] T005 [P] Implement memory monitoring utility (`code/training/memory_monitor.py`) to track RSS and trigger batch‑size reduction to a lower value and, if RSS > 6 GB at batch size 4, cap the training dataset by iteratively reducing the sample count N (starting from total size) until RSS < 6GB. Log the final effective N and the `cap_reason` (FR‑010). **Note**: Must log the decision and final hyperparameters (FR‑003).
- [X] T006 [P] Implement model loading utilities (`code/models/loading.py`) that provide functions to load:
 - `gpt2-medium` (with 4‑bit quantization) when RAM permits.
 - **Behavior**: `load_gpt2_medium()` MUST attempt to load the model. If memory is insufficient, it MUST allow the training loop (T014) to attempt adaptive recovery (batch size reduction, dataset capping) as required by FR-003 and FR-010 before raising an OOM exception. The task must NOT unconditionally crash; it must enable the training loop to implement adaptive strategies first. Addresses FR‑003, FR‑010.
- [X] T007 [P] Implement 2‑D grid memory slot data structures (`code/models/memory_slot.py`) and EpisodicChunk schema (`code/models/episodic_chunk.py`).
- [X] T007b Implement coordinate assignment logic for episodic chunks (FR‑001). This task must define the algorithm for mapping episodic chunks to (x, y) coordinates in the 2-D grid. **Algorithm**: Learned embedding lookup based on content (not deterministic hash). **Overflow Handling**: FIFO eviction (oldest slot overwritten) if capacity (8x8=64) is exceeded. **Prerequisite**: Must be completed before T013 and T014.
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

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Note on Parallelism**: While marked [P] for parallel *writing*, these tests cannot *execute* until T012/T014 are complete.

- [X] T010 [P] [US1] Contract test for recall metric calculation in `tests/unit/test_metrics.py`
- [X] T011 [P] [US1] Integration test for training loop memory constraints in `tests/integration/test_training_memory.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement DistilGPT2 baseline wrapper (`code/models/base.py`). **Logic**: This task implements the "attempt" logic required by FR-003/US-1. It MUST call `load_gpt2_medium()` (T006). If an OOM exception occurs, it MUST catch the exception, log the deviation in `artifacts/results/hyperparams_log.json`, and then raise the exception (no fallback to DistilGPT2). The wrapper must expose the same interface as the spatial model. Addresses FR‑001, FR‑002, and the spec's requirement for a baseline non-spatial variant (SC-001). **Note**: T012 catches the exception raised by T006; T006 does NOT handle fallback internally.
- [X] T014 [US1] Implement training loop (`code/training/loop.py`) with adaptive batch size (reduced) and, if RSS > 6 GB at batch size 4, cap the dataset by iteratively reducing the sample count N (starting from total size) until RSS < 6GB (FR‑010). **Dependency**: Must call `code/training/memory_monitor.py` (T005) for capping logic. Include detailed logging of memory usage, batch‑size decisions, AND hyperparameters (FR‑003, FR‑010) in `artifacts/results/hyperparams_log.json`. **Note**: Threading is restricted only if RSS > 6GB (delegated to T005 logic).
- [X] T015 [P] [US1] Implement evaluation script (`code/evaluation/metrics.py`) to compute exact‑match recall per seed and store results in `artifacts/results/recall_accuracy.json`. **Schema**: `{ "seeds": [int], "per_seed_accuracies": [float], "mean": float, "std": float, "p_values": [float], "confidence_intervals": [[float, float]], "runtime_validation": { "within_limit": bool, "runtime_seconds": float } }`. **Constraint**: Must use a range of seeds.
- [X] T016 [US1] Implement main execution entry point (`code/main.py`) to orchestrate download → model loading → train (across multiple seeds) → evaluate. **Dependency**: Must be implemented after T014 and T015 are implemented. Must generate `artifacts/results/run_summary.json` with keys: `seeds` (list of ints), `accuracies` (list of floats), `effective_batch_size` (int), `runtime_seconds` (float). **Note**: This task orchestrates T014 and T015; it depends on their code being available. It must also verify total runtime ≤ 5 hours and write `artifacts/results/runtime_report.json` with `runtime_seconds` and a boolean `within_limit`. **Requirement**: Must save the trained model checkpoint to `artifacts/models/checkpoint_{seed}.pt` after each run to ensure T027 (Interference Injection) has the necessary artifact.
- [X] T017 [US1] (Merged into T014) Log hyperparameters and memory usage per run (including final batch size and any dataset capping) in `artifacts/results/hyperparams_log.json`. **Dependency**: Merged into T014. **Content**: Explicitly note the 6 GB RAM threshold, the logic used for capping (iterative reduction until RSS < 6GB), and any deviations (e.g., gpt2-medium OOM).
- [X] T017c [US1] (Merged into T016) Verify total runtime ≤ 5 hours; write `artifacts/results/runtime_report.json` with `runtime_seconds` and a boolean `within_limit`. **Dependency**: Merged into T016.

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
- [X] T022 [US2] Generate statistical summary report `artifacts/results/statistical_summary.json` containing p‑values, corrected p‑values, effect sizes, and confidence intervals for each dataset. **Dependency**: Must run after T015/T016 produce recall accuracy results AND T019/T020/T021 are implemented.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Structural Metric Quantification for Spatial Organization (Priority: P2)

**Goal**: Measure and report structural correlates (interference distance, slot occupancy, coordinate variance) to validate spatial organization efficacy.

**Independent Test**: Can be fully tested by computing the interference distance metric and verifying a measurable difference between spatial and non‑spatial variants.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for interference distance calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement interference distance metric in `code/evaluation/metrics.py`. The metric must be computed **separately** for the spatial variant and the non‑spatial baseline, and the results stored in `artifacts/results/interference_distance.json` with fields `spatial`, `baseline`, and `delta`. **Constraint**: Must use the **same dataset samples** for both variants to ensure a valid comparison.
- [X] T025 [P] [US3] Implement slot occupancy distribution logger in `code/evaluation/metrics.py` that records the distribution **per epoch** for each run; output to `artifacts/results/slot_occupancy_epoch_{epoch}.csv`. **Format**: CSV must contain a single row with a list of integers representing the count of items per slot (64 columns). **Requirement**: Must match FR-008's "list of integers" specification.
- [X] T026 [P] [US3] Implement coordinate variance logger in `code/evaluation/metrics.py` that records variance **per epoch**; output to `artifacts/results/coordinate_variance_epoch_{epoch}.csv`. **Format**: CSV must contain a single row with a single float value representing the trace of the 2D covariance matrix. **Requirement**: Must match FR-009's "trace of the 2D covariance matrix" specification.
- [X] T027 [US3] Extend `code/main.py` to run interference‑injection experiments after standard evaluation. **Mechanism**: Assign semantically unrelated items to *adjacent* grid coordinates (Manhattan distance = 1) as per FR-011. Log results to `artifacts/results/interference_metrics.json` with fields `spatial_recall`, `baseline_recall`, `delta`, and `p_value`. **Dependency**: Must run after T014/T015 AND T024 (implementation of interference logic). Must load the model checkpoint saved by T016.
- [X] T028 [US3] Add documentation to `research.md` under a new "Structural Metrics" heading, describing the interference‑distance methodology, slot‑occupancy logging, and coordinate‑variance tracking. **Requirement**: Must link to the specific code implementation in `code/evaluation/metrics.py` to ensure traceability to FR-011.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Response & Mechanism Formalization (Priority: P2)

**Goal**: Address specific reviewer concerns regarding the binding problem, consolidation mechanisms, and formal mapping between spatial coordinates and transformer architecture.

**Independent Test**: Verification that `research.md` and `spec.md` explicitly define the consolidation mechanism and the address/content mapping, and that code implements a "stabilization" phase or weight-update rule.

### Implementation for Reviewer Concerns

- [X] T034 [US3] Refactor `code/models/spatial.py` to include an auxiliary position-encoder regularizer (addressing David Krakauer's concern). **Mechanism**: Add a regularization term to the loss function that penalizes stochastic divergence in spatial coordinate assignment (L2 norm of coordinate gradients, weight=0.01), ensuring deterministic mapping where required. Addresses FR-001.

**Note**: Tasks T029 (Consolidation), T030 (Formal Mapping), T031 (Spatial Coherence), T032, T033, T035, T036, T039, T040, T041, T042, T044, T045, T046, T049, T050, T051 were removed as they lacked traceable Functional Requirements, contradicted the spec, or represented unapproved scope creep. Specifically:
- T033 was removed to avoid duplicating FR-011 with a different definition.
- T047-T051 were removed as they address reviewer concerns not reflected in the spec's Functional Requirements (e.g., formal mapping, biological plausibility, protein synthesis).

**Checkpoint**: All reviewer concerns regarding mechanism, formalism, and stability are addressed.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 Refactor `code/models/spatial.py` to reduce memory footprint (addressing Eric Kandel concern on structural stability).
- [X] T038 Optimize `code/training/loop.py` to reduce training time (addressing John von Neumann concern on overhead).
- [ ] T039 [P] Additional unit tests for edge cases (dataset mismatch, OOM recovery) in `tests/unit/`.

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

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 results** (T015/T016) for statistical comparison
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 results** (T014/T015) for interference injection
- **Phase 6 (Reviewer Response)**: **Depends on US3** (T024-T028) to ensure metrics are available for validation.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **T007b** is a prerequisite for T013 and T014.
- **T014/T015** must be completed before T016.
- **T020-T022** must run after T015/T016 AND T019-T021.
- **T027** must run after T016 (checkpoint save) and T024.
- **T034** must run after T014 (training).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note on T010/T011**: While marked [P] for parallel *writing*, they cannot *execute* until T012/T014 are complete.

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
2. Add User Story 1 (T012‑T016) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (T019‑T022) → Test independently → Deploy/Demo
4. Add User Story 3 (T024‑T028) → Test independently → Deploy/Demo
5. Add Phase 6 (T034) → Address Reviewer Concerns → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (T012, T014, T015, T016)
 - Developer B: User Story 2 (T019, T020, T021, T022)
 - Developer C: User Story 3 (T024, T025, T026, T027, T028)
 - Developer D: Phase 6 (T034) - Reviewer Response
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
- **Constraint Enforcement**: All tasks involving training or data loading must enforce single-core execution (`OMP_NUM_THREADS=1`, `torch.set_num_threads(1`) ONLY if RSS > 6GB or if the runner has only 1 core, to strictly adhere to the Spec's "single CPU core" constraint while respecting available resources.
- **Data Capping Logic**: Where tasks mention capping the dataset, the logic is "iteratively reduce N until RSS < 6GB" (Resolution of FR-010's placeholder).
- **Baseline Model**: gpt2-medium is the only target; no DistilGPT2 fallback is implemented. T012 raises OOM if gpt2-medium fails.
- **Interference Injection**: Must use adjacent grid coordinates (Manhattan distance = 1) as per FR-011.
- **Multiple Comparison Correction**: Use Holm-Bonferroni if min(uncorrected_p) < 0.001, else Bonferroni.
- **Reviewer Specifics**:
 - **Eric Kandel**: Tasks T037 (Memory Footprint) address structural stability. Tasks T049-T051 (Consolidation, Protein Synthesis) were removed as unapproved scope.
 - **John von Neumann**: Tasks T047-T048 (Formal Mapping, Overhead) were removed as unapproved scope.
 - **Rosalind Franklin**: Task T031 was removed; the primary metric is FR-011 (Interference Distance).
 - **David Krakauer**: Task T034 (Regularizer) addresses the binding problem.
 - **Ada Lovelace**: Task T043 (Research) defines concepts; implementation tasks T044 were removed as unapproved scope.
- **Phase 7/8 Removal Justification**: Phase 7 (Computational Formalism) and Phase 8 (Biological Plausibility) were removed to focus on core spatial memory. Tasks T047-T051 were removed as they lacked corresponding Functional Requirements in the spec.
- **FR-010 Implementation Note**: The placeholder "[deferred]" in FR-010 is implemented as "iterative reduction until RSS < 6GB" in tasks T005 and T014.
- **T006 Update**: T006 no longer unconditionally crashes; it allows the training loop to attempt adaptive recovery (batch reduction, capping) before failing, satisfying FR-003/FR-010.
- **T015 Schema Update**: T015 now outputs `per_seed_accuracies`, `p_values`, `confidence_intervals`, and `runtime_validation` to satisfy SC-004/SC-007 and support T019.
- **T016 Checkpoint Save**: T016 now explicitly saves model checkpoints to `artifacts/models/` to support T027.
- **T025/T026 Format Update**: T025 and T026 now explicitly specify CSV row structure (list of 64 integers for occupancy, scalar for variance) to match FR-008/FR-009.
- **T010/T011 Mandatory**: T010 and T011 are now MANDATORY, not OPTIONAL, to satisfy the spec's "Independent Test" requirements.