# Tasks: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

**Input**: Design documents from `/specs/001-molecular-structure-dssc-performance/`
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

- [ ] T001 Create project structure: Execute `mkdir -p code/data code/models code/analysis code/utils data/raw data/processed results tests` and create empty `__init__.py` files in each `code/` subdirectory.
- [ ] T002 Initialize Python 3.10 project: Create `code/requirements.txt` with pinned versions for `torch==2.1.0`, `torch-geometric==2.4.0`, `rdkit==2023.9.5`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `pyyaml==6.0.1`, `requests==2.31.0`. Verify installation with `pip install -r code/requirements.txt --dry-run`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` (for black) with standard configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Implement `code/utils/config.py`: Define `SEED`, `DEVICE` (force 'cpu'), and path constants.
- [ ] T005 [P] Implement `code/utils/logger.py`: Define `setup_logger()` returning a logger that writes to `code/logs/app.log` and stdout.
- [ ] T006 [P] Implement `code/utils/data_loader.py`: Define `load_csv(path: str) -> pd.DataFrame` and `save_csv(df: pd.DataFrame, path: str) -> None`.
- [ ] T007 Setup `state.yaml` for artifact checksums and version tracking: Create initial `state.yaml` with empty `artifact_hashes` map.
- [ ] T008 [P] Implement `code/utils/retry_utils.py`: Define `retry_request(url, max_retries=3, backoff_factor=2)` for exponential backoff.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest Nazeer et al. DSSC dataset, parse SMILES, standardize structures, and generate graph features.

**Independent Test**: Execute `code/data/download.py` and `code/data/preprocess.py` to verify output is a valid `pandas` DataFrame with standardized SMILES, graph features, and PCE column, with no missing critical values.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement `code/data/download.py` (Download Only): 
    1. Download `dssc_dataset.csv` from Zenodo (Nazeer et al., Record ID: 10.5281/zenodo.4921127, DOI: 10.5281/zenodo.4921127) to `data/raw/dssc_dataset.csv`.
    2. Implement retry logic with exponential backoff (max 3 retries) on failure.
    3. Do NOT perform checksum verification in this task; ensure file is written to disk.
- [ ] T010 [US1] Implement `code/data/download.py` (Verification): 
    1. Fetch checksum from Zenodo API metadata endpoint for `dssc_dataset.csv`.
    2. Compare local file checksum with Zenodo metadata.
    3. Raise `ChecksumMismatchError` if mismatch.
    4. Verify PCE units (%): Check that PCE column values are expressed as percentages within the standard range.
    5. If deviant, append entry to `data/processed/review_queue.json` with format `{"smiles": <s>, "value": <v>, "unit": <u>, "status": "flagged_for_review"}`.
    6. Raise `PCEAnomalyError` if any anomalies are found to ensure manual review is triggered.
    *(Depends on T009)*
- [ ] T011 [US1] Implement `code/data/preprocess.py`: Load raw CSV, remove salts, canonicalize tautomers, and generate canonical SMILES using RDKit (FR-002).
    *(Depends on T010)*
- [ ] T012 [US1] Implement `code/data/preprocess.py`: Compute atom features (atomic number, hybridization) and bond features (type, aromaticity) for each molecule.
    *(Depends on T011)*
- [ ] T013 [US1] Implement `code/data/preprocess.py`: Handle invalid SMILES by logging to `failed_molecules.log` with format `SMILES: <string> | Error: <message>` and excluding from training set.
    *(Depends on T012)*
- [ ] T014 [US1] Implement `code/data/preprocess.py`: Export standardized data to `data/processed/graph_data.pt` (PyTorch Geometric format) and `data/processed/cleaned_data.csv`.
    *(Depends on T013)*
- [ ] T015 [P] [US1] Unit test: Verify salt removal and tautomer canonicalization on known edge cases in `tests/unit/test_preprocess.py` (use mock/static test data).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation on CPU (Priority: P2)

**Goal**: Train GCN and Random Forest models using scaffold-aware cross-validation on CPU, compute metrics, and perform statistical comparison.

**Independent Test**: Run `code/models/train.py` to verify completion within 6 hours, production of model artifacts, and output of `results/metrics.json` containing MAE, RMSE, R², and statistical test results.

### Implementation for User Story 2

- [ ] T016 [P] [US2] Implement `code/data/split.py`: Extract Bemis-Murcko scaffolds and perform scaffold-aware 5-fold cross-validation split (FR-004).
- [ ] T017 [P] [US2] Implement `code/models/gcn.py`: Define GCN architecture (≤2 layers, hidden size 128) optimized for CPU execution (FR-003).
- [ ] T018 [P] [US2] Implement `code/models/rf_baseline.py`: Generate Morgan fingerprints and train Random Forest baseline (FR-005).
- [ ] T019 [US2] Implement `code/models/train.py`: 
    1. Implement the core GCN training loop logic (forward/backward pass) for a sufficient number of epochs per fold to ensure model convergence.
    2. Wrap the training loop with a hard timeout of a fixed duration.
    3. If timeout is reached, save partial weights to `results/model_artifacts/` and raise `TimeLimitExceeded` (do NOT reduce epochs).
    4. Implement CPU-only device enforcement.
    5. Integrate scaffold split (T016) and models (T017, T018).
    6. Aggregate all metrics (MAE, RMSE, R²) and save to `results/metrics.json` (FR-005, FR-006).
    *(Note: This task consolidates the core loop, timeout wrapper, and integration into a single executable unit.)*
- [ ] T021 [US2] Implement `code/analysis/stats.py`: Compute fold-wise MAE, RMSE, and R² for both models.
    *(Note: Aligns with plan.md's statistical methodology)*
- [ ] T022 [US2] Implement `code/analysis/stats.py`: 
    1. Perform **paired t-test** (PRIMARY) on fold-wise MAE between GCN and RF as required by FR-006.
    2. Calculate **Cohen's d** (PRIMARY) effect size as required by SC-003.
    3. (Optional) Also compute Wilcoxon signed-rank test and Cliff's Delta for robustness check, but ensure t-test/Cohen's d are the primary reported metrics.
    4. Output p-value and effect sizes to `results/metrics.json`.
    *(Note: Primary method follows Spec FR-006 and SC-003 which mandate t-test/Cohen's d).*
    *(Depends on T021)*
- [ ] T023 [US2] Implement `code/models/train.py`: Aggregate all metrics and save to `results/metrics.json` (FR-005, FR-006).
    *(Depends on T022)*
- [ ] T024 [P] [US2] Integration test: Verify scaffold split ensures no scaffold overlap between train/test sets in `tests/integration/test_scaffold_split.py`.
- [ ] T025 [P] [US2] Integration test: Verify training completes within 6-hour limit on simulated CPU environment in `tests/integration/test_training_timeout.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Motif Extraction (Priority: P3)

**Goal**: Extract substructures (motifs) contributing to high PCE predictions and summarize recurring patterns.

**Independent Test**: Run `code/analysis/interpret.py` on a held-out high-PCE molecule to verify output of ranked subgraphs with importance scores and a summary of top-5 recurring motifs.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/analysis/interpret.py`: Apply Integrated Gradients (or attention weights) to GCN predictions to generate node-level importance scores (FR-007).
- [ ] T027 [US3] Implement `code/analysis/interpret.py`: Extract subgraphs from high-importance nodes and aggregate recurring motifs across the dataset.
- [ ] T028 [US3] Implement `code/analysis/interpret.py`: Perform graph isomorphism check to ensure identified motifs are distinct (non-isomorphic) (SC-005). Save unique motifs to `results/motifs_unique.pt` and update `metrics.json` with `unique_motif_count`.
- [ ] T029 [US3] Implement `code/analysis/interpret.py`: 
    1. Perform a statistical enrichment test of identified motifs against a null distribution of random subgraphs to distinguish signal from bias (Plan Phase 3 Validation Step).
    2. Generate summary report of top motifs with frequency counts and textual descriptions (FR-008).
    *(Depends on T028)*
- [ ] T030 [US3] Implement `code/analysis/interpret.py`: Update `results/metrics.json` to include the `motifs` key with the extracted data.
    *(Depends on T029)*
- [ ] T031 [US3] Unit test: Verify motif extraction logic on a molecule with a known high-importance substructure in `tests/unit/test_interpret.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Contingency & Fallback

**Purpose**: Handle edge cases and fallback mechanisms required by spec assumptions

- [ ] T032 [US3] Implement `code/analysis/interpret.py` fallback: If Integrated Gradients fails due to CPU constraints (timeout or memory error) (triggered by T023 failure), automatically switch to Random Forest feature importance (Spec Assumptions).
    *(Note: Explicitly defines the conditional path: if IG fails -> switch to RF).*
    *(Depends on T026, T031)*

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation: Update `README.md` to include a "Usage" section with the command `python code/main.py`.
- [ ] T034 [P] Code Quality: Apply `black` formatting and `ruff --fix` to all files in `code/`.
- [ ] T035 [P] Performance: Implement batch processing in `code/models/train.py` to ensure peak memory usage < 6GB.
- [ ] T036 [P] Testing: Add `tests/unit/test_stats.py::test_ttest` and `test_cohens_d` to verify robustness checks in T022.
- [ ] T037 Run `quickstart.md` validation to ensure full pipeline reproducibility.
- [ ] T038 Verify `results/metrics.json` schema compliance with `contracts/model_output.schema.yaml`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`data/processed/`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model artifacts (`results/model_artifacts/`)

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
# Launch all tasks for User Story 1 that are independent:
Task: "Download DSSC dataset from Zenodo in code/data/download.py"
Task: "Unit test for salt removal using mock data in tests/unit/test_preprocess.py"
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
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Modeling)
   - Developer C: User Story 3 (Interpretability)
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