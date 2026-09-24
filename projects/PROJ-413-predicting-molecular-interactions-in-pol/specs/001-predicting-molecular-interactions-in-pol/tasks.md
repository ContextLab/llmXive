# Tasks: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

**Input**: Design documents from `/specs/001-polymer-interaction-gnn/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification. [UNRESOLVED-CLAIM: c_f4459a5a — status=not_enough_info]

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

## Phase 0: Spec Alignment & Setup (Shared Infrastructure)

**Purpose**: Project initialization, Spec alignment, and basic structure

- [ ] T001a Create project directory structure per implementation plan (`projects/PROJ-413-predicting-molecular-interactions-in-pol/`) by executing: `mkdir -p data/raw data/curated data/processed code/data code/models code/analysis code/utils results analysis docs tests/contract tests/integration`.
- [ ] T001b [P] Initialize Git repository in `projects/PROJ-413-predicting-molecular-interactions-in-pol/` and create `.gitignore` for Python.
- [X] T001c [P] Create `.flake8`, `pyproject.toml`, and `code/requirements.txt` with pinned versions (torch, torch-geometric, rdkit, datasets, pandas, scipy, scikit-learn). <!-- FAILED: unspecified -->
- [X] T002 [P] Setup utility scripts for checksumming and state hashing (`code/utils/hash_state.py`).
- [X] T003 [P] [FR-002] [US-1] Create base data structures for `MolecularGraph` and `InterfacePair` entities in `code/models/entities.py` with explicit class signatures for node/edge attributes.
- [X] T004 [P] Configure error handling infrastructure by creating `code/utils/exceptions.py` defining `class DataError(Exception)` and `class TrainingTimeoutError(Exception)`.
- [ ] T005 [P] Setup logging infrastructure to track runtime and memory usage in `results/performance.json` via `code/utils/logger.py`.
- [X] T006 [P] Implement random seed fixing utility for reproducibility across all scripts in `code/utils/seed_utils.py`.
- [ ] T063 [US3] [CRITICAL] Update `spec.md` to reflect GAT implementation and clarify FR-007. **Action**: Modify `FR-003` to state "3-layer Graph Attention Network (GAT)" instead of "Graph Convolutional Network (GCN)". Modify `FR-007` to clarify that attention mechanisms handle feature weighting and VIF is reported separately. **Verification**: Assert `spec.md` contains updated text. **Authority**: Plan "Critical Note on Spec Alignment".

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Construction (Priority: P1) 🎯 MVP

**Goal**: Download MolNet data, cross-reference with NIST/Literature, and construct a validated dataset of polymer-filler interface pairs with adhesion energy measurements.

**Independent Test**: Verify the data pipeline executes without errors, produces `data/curated/curated_dataset.csv` with ≥100 rows (target ≥500) of interface pairs, and confirms all required variables (atom types, bond types, adhesion energy) are present with ≤5% missing values per column.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data download and checksum verification in `tests/contract/test_data_download.py`.
- [ ] T011 [P] [US1] Integration test for variable validation and missing value flagging in `tests/integration/test_data_validation.py`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement MolNet download via `datasets.load_dataset('molnet',...)` in `code/data/download.py` with SHA256 checksum recording. **Note**: Standard MolNet 'molecule' split does not contain polymer-filler interfaces. This task must attempt to fetch available data. If no valid data (polymer/filler pairs with adhesion energy) is found, the run MUST fail with E-DATA-001. No fallback is provided; Hard Abort is implemented per Plan override.
- [ ] T013 [P] [US1] Verify hard abort logic: Implement a contract test in `tests/contract/test_hard_abort.py` that simulates a missing 'adhesion_energy' field or <100 rows and asserts that `code/data/clean.py` raises `DataError` with exit code E-DATA-001 and logs the specific error message. **Plan Override**: This task validates the Plan's "hard abort" strategy (Section "Critical Note on Spec Alignment") which overrides Spec FR-001's NIST fallback.
- [ ] T014 [US1] Implement hard abort logic with exit code E-DATA-001 if adhesion energy is missing OR row count <100 in `code/data/clean.py`. **Note**: This task enforces the Plan's "hard abort" logic (Section "Critical Note on Spec Alignment" & "Spec Amendment Flags"), overriding the Spec's proxy fallback as scientifically invalid. It implements the compliance mechanism for FR-001's data acquisition requirement. **Authority**: Cites Plan "Critical Note". **Execution**: If `adhesion_energy` is missing or `len(df) < 100`, raise `DataError("E-DATA-001: Adhesion energy missing or insufficient data")`.
- [ ] T015 [US1] Implement data cleaning and validation script in `code/data/clean.py` to flag missing values (≤5% threshold) and process data if row count ≥100.
- [ ] T016 [US1] Implement 'Limited Power' warning logic in `code/data/clean.py`: if 100 ≤ rows < 500, log warning and calculate margin of error (e.g., `1.96 * std / sqrt(n)`).
- [ ] T017 [US1] Generate `data/curated/curated_dataset.csv` with complete molecular graph structures and adhesion energy measurements. **Schema**: Columns must be `polymer_smiles` (str), `filler_smiles` (str), `adhesion_energy` (float). **Validation**: Must have ≥100 rows, and missing values per column must be ≤5%. **Verification**: This task includes running `code/data/validate_curated.py` which asserts `row_count >= 100` and `missing_pct <= 0.05`. If validation fails, the task aborts with clear error.
- [ ] T018 [P] [US1] Extract hand-crafted descriptors (degree, density, clustering coefficient) from SMILES strings in `data/curated/curated_dataset.csv` using RDKit and save to `data/processed/descriptors.csv`. **Dependency**: This task runs ONLY if T017 (generate curated_dataset.csv) passes validation. **Must complete before T024** to ensure descriptors are available for VIF calculation (T046) before graph construction. **Implementation**: Use `rdkit.Chem.Descriptors` to calculate standard RDKit topological descriptors (e.g., degree, density, clustering). **Output Schema**: Columns `polymer_smiles`, `filler_smiles`, `polymer_degree`, `polymer_density`, `polymer_clustering`, `filler_degree`, `filler_density`, `filler_clustering`. **Verification**: Assert file exists and has correct columns.
- [ ] T019 [US1] Generate `data/processed/descriptors.csv` with calculated descriptors. **Verification**: Assert file exists and has correct columns.
- [ ] T020 [US1] Update `state/projects/PROJ-413-predicting-molecular-interactions-in-pol.yaml` with the calculated hash under key `artifact_hashes.curated_dataset`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training Execution (Priority: P2)

**Goal**: Train a Graph Attention Network (GAT) with multiple layers on the curated data using CPU-only execution, ensuring convergence within 6 hours and ≤6GB RAM.

**Independent Test**: Execute the training script on a CPU-only environment, confirm completion within 4.5 hours (hard limit 6h), peak memory ≤6GB, and verify training loss convergence (MSE reduction ≥50%).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for GAT model architecture definition in `tests/contract/test_gat_model.py`.
- [ ] T022 [P] [US2] Integration test for checkpointing and resume functionality in `tests/integration/test_training_resume.py`.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement 3-layer Graph Attention Network (GAT) using `torch_geometric.nn.GATConv` in `code/models/gat.py` (3 layers, hidden=64, dropout=0.5). **Plan Override**: Per `plan.md` Section "Critical Note on Spec Alignment" and "Spec Amendment Flags", this task implements GAT to satisfy attention requirements, overriding Spec FR-003's GCN requirement. **Dependency**: This task depends on T063 (Spec Update) completing to ensure Spec alignment. **Note**: This task requires the spec to be updated (see T063).
- [ ] T024 [US2] Implement SMILES-to-heterogeneous graph conversion in `code/data/graph_build.py` using `rdkit.Chem.rdmolfiles.MolFromSmiles` to generate `data/processed/graphs.pt` from `data/curated/curated_dataset.csv`. **Dependency**: Must run after T018 (descriptors) to ensure VIF data availability. **Feature Mapping**: `atom type -> integer ID`, `bond order -> float`. **Output Schema**: PyG `Data` object with `x` (node features), `edge_index`, `edge_attr`. **Verification**: Assert that loaded graph has `x.shape[1] == 14` (10 atom features + 4 bond features), `edge_index` is valid (no out-of-bounds), and `edge_attr` exists. **Note**: This generates the final graph schema with topological features only (node degree, edge connectivity, graph density) as per Spec FR-002.
- [ ] T025 [US2] Generate `analysis/topology_audit.md` from `graph_build.py` listing node counts, edge counts, and pruning statistics. **Required Sections**: 'Node Counts', 'Edge Counts', 'Pruning Statistics'. **Verification**: Assert file exists and contains required sections. **Note**: Removed 'Physical Parameterization Summary' as that phase was removed.
- [ ] T026 [US2] Save processed graphs to `data/processed/graphs.pt` and verify the file loads without error.
- [ ] T027 [US2] Implement checkpointing logic at periodic intervals to `results/checkpoint_{epoch}.pt` in `code/models/train.py`.
- [ ] T028 [US2] Implement training loop in `code/models/train.py` with 80/20 train-test split, batch ≤32, MSE loss, fixed seed. **Hyperparameters**: lr=0.001, epochs=50, optimizer=Adam. **Verification**: Assert `final_loss <= 0.5 * initial_loss`.
- [ ] T028b [US2] Integrate checkpointing logic from T027 into the training loop in `code/models/train.py` to trigger checkpointing if runtime > 4.5h.
- [ ] T029 [US2] Implement timeout logic (hard fail >6h) in `code/models/train.py` that triggers T027 checkpointing if 4.5h < runtime ≤ 6h, and fails if >6h.
- [ ] T030 [US2] Configure final training run in `code/models/train.py` to use the hyperparameters defined in T028 and select the model with the best validation loss.
- [ ] T031 [US2] Execute final training run and save the best model to `results/model.pt`.
- [ ] T032 [US2] Verify the model artifact `results/model.pt` loads without error and contains the expected architecture.
- [ ] T033 [US2] Log runtime and memory usage to `results/performance.json`. **Schema**: Keys `peak_memory_gb` (float), `total_runtime_seconds` (int), `epochs_completed` (int).
- [ ] T034 [US2] Calculate SHA256 hash of `results/model.pt` and `data/processed/graphs.pt` in `code/utils/hash_state.py`.
- [ ] T035 [US2] Update `state/projects/PROJ-413-predicting-molecular-interactions-in-pol.yaml` with the calculated hashes under keys `artifact_hashes.model` and `artifact_hashes.graphs`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation & Attribution (Priority: P3)

**Goal**: Validate model significance via permutation test (full re-training), perform gradient-based attribution, and report VIF for collinearity.

**Independent Test**: Run permutation test (100 iterations, 10 epochs each), confirm p < 0.05, identify ≥3 topological features with std > 0.1, and compute VIF on hand-crafted descriptors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 [P] [US3] Contract test for permutation test logic and p-value calculation in `tests/contract/test_permutation.py`.
- [ ] T037 [P] [US3] Integration test for attribution and VIF reporting in `tests/integration/test_analysis.py`.

### Implementation for User Story 3

- [ ] T038 [US3] Implement permutation loop in `code/analysis/perm_test.py` with **exactly 100 iterations** on a reduced subset, using **10 epochs per iteration**. **Pre-check**: Run a pilot epoch on a small sample subset. to measure `avg_epoch_time`. Calculate `total_estimated_time = 100 * 10 * avg_epoch_time`. If `total_estimated_time > 5h`, abort with error "Permutation test estimated time exceeds 5h limit". **Random Seed Strategy**: Fixed seed per permutation. **Metric**: MSE. **Plan Constraint**: These values are mandated by the Plan's feasibility constraints to fit the 6h limit.
- [ ] T039 [US3] Implement re-training logic for each permutation in `code/analysis/perm_test.py` using the GAT model from T023.
- [ ] T040 [US3] Save permuted MSEs to `results/permuted_mses.csv`. **Schema**: Column `permuted_mse` (float).
- [ ] T041 [US3] Calculate 0.95 quantile of permuted baseline MSEs from `results/permuted_mses.csv` in `code/analysis/stat_utils.py` using `numpy.quantile`.
- [ ] T042 [US3] Compute p-value using the formula `(count(permuted <= observed) + 1) / (N + 1)` and save to `results/stats.csv`.
- [ ] T043 [US3] Implement gradient-based Integrated Gradients attribution in `code/analysis/attribution.py` on a set of test samples using the trained model from T031. **Baseline**: Zero input graph (all features zeroed). **Steps**: 50. **Perturbation**: Randomly mask [deferred] of edges and zero-node features to approximate feature importance. **Aggregation**: Mean absolute importance. **Target Features**: Topological features (node degree, edge connectivity, graph density) derived from the graph structure as per Spec FR-006. **Verification**: Assert output contains at least 3 features with std > 0.1.
- [ ] T044 [US3] Run Integrated Gradients on the test set and aggregate results. **Output**: JSON file `results/attribution_raw.json` mapping feature names to mean absolute importance scores.
- [ ] T045 [US3] Aggregate attribution results and identify topological features with std > 0.1. **Output**: JSON with feature names and mean importance scores. **Criteria**: Features must be derived from the graph structure (e.g., node degree, edge connectivity) as per Spec FR-006.
- [ ] T046 [US3] Implement VIF calculation on hand-crafted descriptors from `data/processed/descriptors.csv` in `code/analysis/collinearity.py`. **Formula**: `1 / (1 - R^2)`. **Threshold**: VIF > 5. **Input Columns**: `polymer_degree`, `polymer_density`, `polymer_clustering`, `filler_degree`, `filler_density`, `filler_clustering`. **Output**: Save VIF scores to `results/vif_report.json`. **Verification**: Assert file exists and contains VIF scores for all descriptors.
- [ ] T047 [US3] Save VIF results to `results/stats.csv`. **Schema**: Append rows for each descriptor with columns `metric`, `vif_score`.
- [ ] T048 [US3] Select correction method (Bonferroni preferred) in `code/analysis/stat_utils.py`.
- [ ] T049 [US3] Apply Bonferroni correction to p-values in `results/stats.csv` if >1 metric present. **Formula**: `p_corrected = p * n`.
- [ ] T050 [US3] Update `results/stats.csv` with corrected p-values.
- [ ] T051 [US3] Generate `results/stats.csv` with columns: `metric`, `observed_value`, `p_value`, `corrected_p_value`, `vif_score`, `fwer`. **Data Types**: `metric` (str), `observed_value` (float), `p_value` (float), `corrected_p_value` (float), `vif_score` (float), `fwer` (float).
- [ ] T052 [US3] Generate `results/attribution.json` with feature importance rankings in descending order by mean importance. **Schema**: List of objects with `feature` (str) and `importance` (float). **Note**: Only topological features (degree, density, etc.) are included.
- [ ] T053 [US3] Calculate SHA256 hash of `results/stats.csv`, `results/attribution.json`, `results/performance.json` in `code/utils/hash_state.py`.
- [ ] T054 [US3] Update `state/projects/PROJ-413-predicting-molecular-interactions-in-pol.yaml` with the calculated hashes under keys `artifact_hashes.stats`, `artifact_hashes.attribution`, `artifact_hashes.performance`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Power Analysis & Reporting

**Purpose**: Document power analysis and final packaging

- [ ] T055 [P] Document power analysis assumptions (medium effect size f²=0.15, α=0.05, Power=0.80 (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics))) and determine Required N in `analysis/power_analysis.md`. **Required Sections**: Effect Size, Alpha, Power, Required N, Limitations. **Statistical Test**: Two-sample t-test. **Note**: Assumptions are based on topological features only as per Spec FR-002 and FR-006.
- [ ] T056 [P] Compile final report referencing `results/` and `analysis/` artifacts exclusively. **Structure**: Introduction, Methods, Results, Discussion. **Template**: Use the project's standard report template.
- [ ] T057 [P] Verify all artifacts have corresponding SHA256 hashes in `state/projects/PROJ-413-predicting-molecular-interactions-in-pol.yaml` by running `utils/verify_hashes.py`. **Criteria**: Exact filename match and key match in YAML.

**Checkpoint**: All user stories should now be independently functional

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
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

1. Complete Phase 0: Setup
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2: User Story 1
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
- **CRITICAL**: Permutation test MUST involve **exactly 100 iterations** with **10 epochs each** to satisfy Spec FR-005 while fitting the 6h limit.
- **CRITICAL**: GAT (T023) uses `GATConv` as per Plan's override of Spec FR-003. **Action**: T063 must update spec.md to reflect this.
- **CRITICAL**: Attention/GCN weights handle feature weighting; collinearity is handled via VIF (T046) and reported separately.
- **CRITICAL**: **SCOPE RESTRICTION**: The "Physical Parameterization" phase (T064-T066) has been removed as it was unauthorized scope creep. The model and analysis MUST now strictly include only topological features as defined in the Spec. The Plan's "Critical Note" regarding physical parameters was superseded by the Spec's strict scope.
- **CRITICAL**: The `analysis/physical_parameterization_report.md` is NO LONGER required.
- **CRITICAL**: **REVISION RESPONSE**: T064-T066 (Physical Parameterization) have been removed to align with the Plan's "Critical Note" and Spec's "topological features only" constraint.