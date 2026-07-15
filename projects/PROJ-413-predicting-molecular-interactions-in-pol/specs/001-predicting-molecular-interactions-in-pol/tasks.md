# Tasks: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

**Input**: Design documents from `/specs/001-polymer-interaction-gnn/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-413-predicting-molecular-interactions-in-pol/`) by executing: `mkdir -p data/raw data/curated data/processed code/data code/models code/analysis code/utils results analysis docs tests/contract tests/integration`. Also create `.flake8` and `pyproject.toml` with black config. <!-- ATOMIZE: requested -->
- [ ] T002 Initialize Python project by creating `code/requirements.txt` with pinned versions (torch, torch-geometric, rdkit, datasets, pandas, scipy, scikit-learn) and executing `pip install -r code/requirements.txt` in the virtualenv.
- [X] T004 Setup utility scripts for checksumming and state hashing (`code/utils/hash_state.py`).
- [X] T005 [P] Implement random seed fixing utility for reproducibility across all scripts in `code/utils/seed_utils.py`.
- [ ] T006 [P] [FR-002] [US-1] Create base data structures for `MolecularGraph` and `InterfacePair` entities in `code/models/entities.py` with explicit class signatures for node/edge attributes.
- [X] T007 [P] Configure error handling infrastructure by creating `code/utils/exceptions.py` defining `class DataError(Exception)` and `class TrainingTimeoutError(Exception)`.
- [ ] T008 [P] Setup logging infrastructure to track runtime and memory usage in `results/performance.json` via `code/utils/logger.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Construction (Priority: P1) 🎯 MVP

**Goal**: Download MolNet data, cross-reference with NIST/Literature, and construct a validated dataset of polymer-filler interface pairs with adhesion energy measurements.

**Independent Test**: Verify the data pipeline executes without errors, produces `data/curated/curated_dataset.csv` with ≥100 rows (target ≥500) of interface pairs, and confirms all required variables (atom types, bond types, adhesion energy) are present with ≤5% missing values per column.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for data download and checksum verification in `tests/contract/test_data_download.py`.
- [ ] T010 [P] [US1] Integration test for variable validation and missing value flagging in `tests/integration/test_data_validation.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement MolNet download via `datasets.load_dataset('molnet',...)` in `code/data/download.py` with SHA256 checksum recording. **Note**: This task fetches all required fields (polymer_smiles, filler_smiles, adhesion_energy). If these fields are missing, the script MUST trigger the hard abort logic (E-DATA-001) defined in T013. The Plan overrides the Spec's NIST cross-reference requirement; if MolNet lacks data, the pipeline aborts.
- [~] T012 [US1] **DELETED**: NIST cross-referencing removed. The Plan explicitly rejects the NIST fallback as scientifically invalid due to lack of structured API. The Spec's FR-001 requirement for NIST is superseded by the Plan's "hard abort" strategy.
- [X] T013 [US1] Implement hard abort logic with exit code E-DATA-001 if adhesion energy is missing OR row count <100 in `code/data/clean.py`. **Note**: This task enforces the Plan's "hard abort" logic, overriding the Spec's proxy fallback as scientifically invalid.
- [X] T014 [US1] Implement data cleaning and validation script in `code/data/clean.py` to flag missing values (≤5% threshold) and process data if row count ≥100.
- [X] T015 [US1] Implement 'Limited Power' warning logic in `code/data/clean.py`: if 100 ≤ rows < 500, log warning and calculate margin of error (e.g., `1.96 * std / sqrt(n)`).
- [ ] T016 [US1] Generate `data/curated/curated_dataset.csv` with complete molecular graph structures and adhesion energy measurements.
- [~] T017 [US1] Extract hand-crafted descriptors (degree, density, clustering coefficient) from `data/curated/curated_dataset.csv` and save to `data/processed/descriptors.csv` in `code/data/descriptor_extractor.py`.
- [~] T018 [US1] Update `state/projects/PROJ-413-...yaml` with SHA256 hash of `curated_dataset.csv` via `utils/hash_state.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training Execution (Priority: P2)

**Goal**: Train a 3-layer Graph Attention Network (GAT) on the curated data using CPU-only execution, ensuring convergence within 6 hours and ≤6GB RAM.

**Independent Test**: Execute the training script on a CPU-only environment, confirm completion within 4.5 hours (hard limit 6h), peak memory ≤6GB, and verify training loss convergence (MSE reduction ≥50%).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for GAT model architecture definition in `tests/contract/test_gat_model.py`.
- [X] T020 [P] [US2] Integration test for checkpointing and resume functionality in `tests/integration/test_training_resume.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement 3-layer Graph Attention Network (GAT) using `torch_geometric.nn.GATConv` in `code/models/gat.py` (3 layers, hidden=64, dropout=0.5). **CRITICAL NOTE**: Although Spec FR-003 mandates a GCN, the Plan's "Critical Note on Spec Alignment" explicitly states the model MUST be a GAT to satisfy attention requirements and handle feature weighting. This task implements the GAT as per the Plan, overriding the Spec's GCN requirement.
- [~] T022 [US2] Implement SMILES-to-heterogeneous graph conversion in `code/data/graph_build.py` using `rdkit.Chem.rdmolfiles.MolFromSmiles` to generate `data/processed/graphs.pt` from `data/curated/curated_dataset.csv`.
- [~] T023 [US2] Generate `analysis/topology_audit.md` from `graph_build.py` listing node counts, edge counts, and pruning statistics.
- [ ] T024 [US2] Save processed graphs to `data/processed/graphs.pt`.
- [ ] T025 [US2] Implement checkpointing logic every 10 epochs to `results/checkpoint_{epoch}.pt` in `code/models/train.py`.
- [ ] T026 [US2] Implement training loop in `code/models/train.py` with 80/20 train-test split, batch ≤32, MSE loss, fixed seed, and logic to trigger T025 if runtime > 4.5h.
- [ ] T027 [US2] Implement timeout logic (hard fail >6h) in `code/models/train.py` that triggers T025 checkpointing if 4.5h < runtime ≤ 6h, and fails if >6h.
- [ ] T028 [US2] Train final model and save to `results/model.pt`.
- [ ] T029 [US2] Log runtime and memory usage to `results/performance.json`.
- [ ] T030 [US2] Update `state/projects/PROJ-413-...yaml` with hashes for `model.pt` and `graphs.pt`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation & Attribution (Priority: P3)

**Goal**: Validate model significance via permutation test (full re-training), perform gradient-based attribution, and report VIF for collinearity.

**Independent Test**: Run permutation test (1000 iterations, 5 epochs each), confirm p < 0.05, identify ≥3 topological features with std > 0.1, and compute VIF on hand-crafted descriptors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for permutation test logic and p-value calculation in `tests/contract/test_permutation.py`.
- [ ] T032 [P] [US3] Integration test for attribution and VIF reporting in `tests/integration/test_analysis.py`.

### Implementation for User Story 3

- [ ] T033 [US3] Implement full re-training permutation test in `code/analysis/perm_test.py` with 1000 permutations on the full dataset, using 5 epochs per permutation to fit the 6h runtime limit. Compare MSE against baseline and save permuted MSEs to `results/permuted_mses.csv`. *Note: This meets FR-005's 1000 iteration count while respecting the Plan's feasibility constraints.*
- [ ] T034 [US3] Calculate 0.95 quantile of permuted baseline MSEs from `results/permuted_mses.csv` and compute p-value in `code/analysis/stat_utils.py`.
- [ ] T035 [US3] Implement gradient-based Integrated Gradients attribution in `code/analysis/attribution.py` on a set of test samples using the trained model from T028.
- [ ] T036 [US3] Implement VIF calculation on hand-crafted descriptors from `data/processed/descriptors.csv` in `code/analysis/collinearity.py`.
- [ ] T037 [US3] Aggregate attribution results and identify topological features with std > 0.1.
- [ ] T038 [US3] **DELETED**: Task removed. The Plan explicitly states that attention mechanisms do NOT handle collinearity; VIF (T036) handles collinearity reporting. Verifying that "attention handles collinearity" is scientifically incorrect and contradicts the Plan.
- [ ] T039 [US3] Apply Bonferroni/Holm correction to p-values in `results/stats.csv` if >1 metric present.
- [ ] T040 [US3] Calculate Family-Wise Error Rate (FWER) and verify correction effectiveness, logging result in `results/stats.csv`.
- [ ] T041 [US3] Generate `results/stats.csv` with columns: metric, observed_value, p_value, corrected_p_value, vif_score, fwer.
- [ ] T042 [US3] Generate `results/attribution.json` with feature importance rankings.
- [ ] T043 [US3] Update `state/projects/PROJ-413-...yaml` with hashes for `stats.csv`, `attribution.json`, `performance.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Power Analysis & Reporting

**Purpose**: Document power analysis and final packaging

- [ ] T051 [P] Document power analysis assumptions (medium effect size, α=0.05) and determine Required N in `analysis/power_analysis.md` with sections: Effect Size, Alpha, Power, Required N, Limitations.
- [ ] T052 [P] Compile final report referencing `results/` and `analysis/` artifacts exclusively.
- [ ] T053 [P] Verify all artifacts have corresponding SHA256 hashes in `state/projects/PROJ-413-...yaml`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for model input

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
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data download and checksum verification in tests/contract/test_data_download.py"
Task: "Integration test for variable validation and missing value flagging in tests/integration/test_data_validation.py"

# Launch all models for User Story 1 together:
Task: "Implement MolNet download via datasets.load_dataset in code/data/download.py"
```

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
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Adhere to CPU-only constraints (cores, limited RAM, 6h limit). No GPU, no 8-bit quantization, no large models.
- **CRITICAL**: Data pipeline MUST abort with E-DATA-001 if adhesion energy is missing or <100 rows; NO proxy metrics allowed (Plan overrides Spec).
- **CRITICAL**: Permutation test MUST involve 1000 permutations (iterations) with 5 epochs each to satisfy Spec FR-005 while fitting the 6h limit.
- **CRITICAL**: GAT (T021) uses `GATConv` as per Plan's override of Spec FR-003.
- **CRITICAL**: Attention/GCN weights handle feature weighting; collinearity is handled via VIF (T036) and reported separately.
- **CRITICAL**: Physical Parameterization (Phase 6) has been removed as it was unauthorized scope and created circular dependencies.