# Tasks: Predicting Molecular Permeability of Polymers via Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-permeability/`
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

 Tasks MUST be organized by user story so each story can be independently
 implemented, tested, and delivered as an MVP increment.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create standard project directory structure as defined in `plan.md`: Ensure directories for raw data, processed data, models, and evaluation results are created. **Constraint**: Follow the structure defined in `plan.md` exactly.
- [X] T001b Create initial project files: Create files `requirements.txt` and `main.py` in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Deliverable**: Create `.ruff.toml` and `pyproject.toml` with explicit configuration for reproducibility. **Config**: Set `target-version = "py311"`, `line-length = 100`, and `select = ["E", "F", "W", "I"]` for ruff; `line-length = 100` for black.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup seed management and random state pinning in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/utils.py`
- [X] T005 [P] Implement logging infrastructure with level configuration in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/utils.py`
- [X] T006 [P] Create base `PolymerGraph` entity class in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/polymer_graph.py` with node/edge feature schemas (atom type, hybridization, bond type) **ONLY**. **Constraint**: Do NOT include 3D features (radii, bond length) as per FR-001.
- [X] T007 Create `PermeabilityRecord` data model in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/permeability_record.py`
- [X] T008 Setup CPU-only PyTorch environment check in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Load raw polymer data from NIST/PubChem, parse SMILES into valid graphs, and verify data integrity. **Constraint**: Real data is the ONLY valid source for SC-001. Simulation is strictly prohibited and must cause execution to halt if invoked.

**Independent Test**: Run ingestion script; verify output HDF5 contains valid PolymerGraph objects, correct record counts, AND that the scaffold split indices are generated and valid. If real data is missing, the script MUST exit with a non-zero code and a clear error message.

### Implementation for User Story 1

- [ ] T010 [US1] Implement NIST/PubChem data fetcher in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py`. **Logic**:
 1. Attempt to load real polymer data using `datasets.load_dataset('polymer_science/permeability_nist', split='train')`.
 2. If that fails, attempt `datasets.load_dataset('pubchem_polymer', split='train')`.
 3. If both fail, attempt to fetch from verified raw URLs (e.g., NIST raw CSV links) using `requests` or `pandas.read_csv`.
 4. If all real data sources fail, raise a `DataUnavailableError` with the message "FATAL: No real data available from NIST/PubChem. Real experimental data is required. Simulation is not a valid substitute. Execution halted." and exit with code 1.
 5. If real data is loaded, save to `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/polymer_raw.csv`.
 6. Log the source used. **CRITICAL**: No simulation fallback is permitted.
 7. **Output**: Save raw data checksums to `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/checksums.json`.
- [ ] T011a [US1] Implement SMILES-to-PolymerGraph parser in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py` using RDKit. **Logic**: Handle stereochemistry; convert SMILES to graph object. **Specific Action**: If a SMILES string contains undefined stereochemistry (e.g., `@?`), treat the bond as a single bond to ensure graph validity, as per spec acceptance scenarios.
- [ ] T011b [US1] Implement molecular weight calculation for repeat units in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py`. **Dependency**: T011a. **Logic**: Calculate MW of the repeat unit; flag if < 1000 Da.
- [ ] T012 [US1] Implement data cleaning logic in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py`: exclude entries with missing permeability; identify duplicates by SMILES string. **Logic for Duplicates**: If duplicates exist, calculate the arithmetic mean of log-permeability. **Logic for Conflicts**: If the variance between duplicate permeability values exceeds a defined threshold (e.g., > 0.5 log units), flag the entry for manual review by writing to `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/review_log.csv` with status "FLAGGED_CONFLICT" and reason "High variance in duplicate values". **Constraint**: **Always exclude** entries where calculated MW of the repeat unit < 1000 Da. Log these exclusions to `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/review_log.csv` with reason "MW < 1000 Da". **Do NOT** rely on environment variables; the rule is deterministic.
- [X] T013 [US1] Implement node/edge feature extraction (atom type, hybridization, bond type) in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/preprocessing.py`. **Constraint**: Use ONLY 2D features defined in FR-001 as the core schema.
- [ ] T014 [US1] Save cleaned dataset to HDF5/Parquet in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5`. **Dependency**: T013 must complete before T014 to ensure feature completeness.
- [ ] T020 [US1] Implement Murcko scaffold splitting logic in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/preprocessing.py`. **Input**: `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/polymers.h5`. **Algorithm**: Use `rdkit.Chem.MurckoScaffold.GetScaffoldForMol(mol, includeChirality=True)` to extract scaffolds. **Rule**: Convert scaffold to canonical SMILES string; use string hashing for strict identity match. Exclude any molecule from the test set if its scaffold SMILES is present in the training set. **Output**: Save split indices to `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/processed/scaffold_split_indices.json`. **Dependency**: T014 must complete before T020.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a CPU-tractable GNN and compare against Random Forest/Linear baselines using strict scaffold splits.

**Independent Test**: Execute training pipeline; verify GNN loss decreases, RF baseline runs, and metrics are reported in JSON.

### Implementation for User Story 2

- [ ] T009 [US2] Implement gradient clipping utility function (max norm threshold 1.0) in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/trainer.py`. **Note**: This task defines the utility function to be used by T024c.
- [X] T021 [US2] Implement Message-Passing GNN (3 layers, 64 hidden dimensions) in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/gnn.py` using CPU-compatible PyTorch. **Constraint**: Must use float32 precision; no mixed precision or 8-bit quantization. Must consume input features defined in FR-001 (atom type, hybridization, bond type). **Dependency**: T020.
- [X] T022 [US2] Implement Random Forest baseline using ECFP4 fingerprints in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/baselines.py`
- [X] T023 [US2] Implement Linear Regression baseline using RDKit descriptors in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/baselines.py`
- [ ] T024a [US2] Implement training loop structure in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/trainer.py`. **Requirement**: Define forward pass, loss calculation, and optimizer step.
- [ ] T024b [US2] Implement early stopping callback in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/trainer.py`. **Requirement**: Stop if validation loss does not improve for 10 epochs.
- [ ] T024c [US2] Apply gradient clipping in training loop in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/models/trainer.py`. **Requirement**: Use utility function from T009 to clip gradients to max norm 1.0. **Dependency**: T009.
- [X] T025 [US2] Implement evaluation logic to compute R², MAE, and Pearson correlation in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/metrics.py`
- [X] T026 [US2] Generate JSON report comparing GNN vs. Baselines on test set in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/report.py`. **Dependency**: T021, T022, T023 must complete before T026 to ensure all baselines are included.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform Wilcoxon signed-rank tests, VIF analysis, and sensitivity sweeps to validate model robustness.

**Independent Test**: Run stats script; verify p-values, VIF flags, and stability metrics are generated.

### Implementation for User Story 3

- [X] T031 [US3] Implement k-fold cross-validation wrapper in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`
- [X] T032 [US3] Implement Wilcoxon signed-rank test for GNN vs. RF performance in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`
- [X] T033 [US3] Implement Variance Inflation Factor (VIF) calculation for baseline descriptors in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`
- [X] T034 [US3] Implement sensitivity analysis sweeping R² thresholds across {0.25, 0.30, 0.35} in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/stats.py`. **Logic**: For each threshold, calculate 'successful_prediction_rate' = (count of CV folds where fold R² > threshold) / total folds. **Output**: Generate a JSON file at `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/results/sensitivity_sweep.json` containing the sweep results with keys: `threshold` (float), `successful_prediction_rate` (float), and `stability_metric` (standard deviation of `successful_prediction_rate` across the sweep). **Input**: Read from T031's k-fold output.
- [X] T035 [US3] Generate final statistical report including p-values and VIF flags in `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/report.py`
- [X] T037 [US3] Add unit tests for statistical functions in `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/unit/test_stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T062a [P] Performance: Optimize graph batching in `gnn.py` to reduce peak RSS memory usage. **Deliverable**: Run `python -m memory_profiler` on the training loop to capture baseline. Apply optimization: Use `torch.utils.data.DataLoader` with `num_workers=0` and `pin_memory=False`. Record memory usage logs. **Constraint**: Do not claim a specific % reduction; demonstrate the reduction in logs.
- [X] T063 [P] Additional unit tests for feature extraction in `projects/PROJ-512-predicting-molecular-permeability-of-pol/tests/unit/test_features.py`
- [ ] T064 [P] Run quickstart.md validation: Verify execution without error and production of `polymers.h5`, `metrics.json`, `sensitivity_sweep.json` artifacts.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (specifically the scaffold split from T020 which consumes T014's artifact). Note: T014 (Save) must complete after T013 to ensure feature completeness. T021 depends on T020.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires models from US2.
- **Polish (Final Phase)**: Requires T014 (Data) and T020 (Split) from US1.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 can start
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase N tasks T062a-T064 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic ingestion)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Train GNN with 2D features → Test independently → Deploy/Demo
4. Add User Story 3 → Validate statistics → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Model Training + Topology Control)
 - Developer C: User Story 3 (Statistical Validation)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM, time-limited execution). No GPU, no 8-bit quantization, no large LLMs.
- **Data Integrity**: All data must be real (NIST/PubChem via HuggingFace or verified URLs). The pipeline MUST halt with a clear error if real data is missing. No simulation fallbacks are permitted. SC-001 is ONLY valid with real data.
- **Scope Compliance**: Tasks strictly adhere to FR-001 and FR-003. Only 2D SMILES features (atom type, hybridization, bond type) are used as the core schema. Phase 6 (Structural Parameters) has been removed to ensure strict alignment with the ratified spec.
- **Review Compliance**: Removed tasks T040-T045 (Phase 6) and T009a (Simulation) to ensure strict alignment with Spec requirements and Success Criteria. Phase 6 was removed as it introduced unapproved scope creep (Structural Parameters) violating FR-001 and Constitution Principle VI. T010 updated to remove simulation fallback and enforce "fail loudly". T012 updated to include "flag for manual review" logic. T011a updated to specify "treat undefined bonds as single".
