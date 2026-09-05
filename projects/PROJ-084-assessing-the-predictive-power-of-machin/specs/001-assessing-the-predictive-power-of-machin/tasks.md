# Tasks: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

**Input**: Design documents from `/specs/001-assess-ml-predictive-power/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/` at repository root
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

- [ ] T001a Create `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/` directories using `mkdir -p`
- [X] T001b Create `code/config.py`, `code/__init__.py`, `code/requirements.txt`, `tests/__init__.py`
- [X] T002 Initialize Python project with `pandas`, `scikit-learn`, `rdkit`, `pyyaml`, `pytest` in `code/requirements.txt`
- [X] T003a [P] Create `code/setup.cfg` with black/ruff configuration (max-line-length=88, target-version=py311). **Prerequisite: T002**
- [X] T003b Update `code/setup.cfg` with linting tool configuration. **Prerequisite: T003a, T002**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and data preparation that MUST be complete before ANY user story can begin.
**Note**: This phase includes data ingestion, sanitization, fingerprinting, and scaffold generation to ensure US1 and US2 can start in parallel after completion.
**Execution Order**: Tasks T014-T017 MUST complete before T010 is fully utilized, but T010 (Scaffold Gen) is moved here to unblock US2 splitting logic. T019 (Download) must complete before T014-T017.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with pinned random seeds, path constants, and hyperparameter grids for RF/SVM
- [X] T005 [P] Implement `code/utils/io.py` for robust Parquet/CSV loading, checksumming, and batch processing to manage memory < 7GB
- [X] T006 [P] Create `code/preprocessing/__init__.py` and `code/modeling/__init__.py` package structures
- [ ] T007a [P] Create `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` defining fields: `smiles` (string, non-null), `yield` (float, 0.0-100.0), `reaction_class` (string), `fingerprint_ecfp` (list of int, length 2048), `fingerprint_maccs` (list of int, length 167). **Prerequisite: None**
- [ ] T007b [P] Implement `code/utils/validators.py` to load and enforce `dataset.schema.yaml` using `pydantic` (v2). **Validation**: Load schema, validate a sample row, and raise error on mismatch. **Prerequisite: T007a**
- [ ] T008a [P] Create `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml` defining fields: `model_type` (string), `hyperparameters` (dict), `metrics` (dict with keys R2, RMSE, MAE), `split_ratios` (dict). **Prerequisite: None**
- [ ] T008b [P] Implement `code/utils/validators.py` to load and enforce `output.schema.yaml` using `pydantic`. **Validation**: Load schema, validate a sample output object, and raise error on mismatch. **Prerequisite: T008a**
- [X] T009 Create `data/raw/.gitkeep` and `data/processed/.gitkeep` directories to ensure directory structure exists
- [ ] T019 [US1] Implement `code/preprocessing/download.py`: Download USPTO dataset. **Primary Source**: `wget` on verified public DOI URL (`https://huggingface.co/datasets/chembl/USPTO_yield/resolve/main/uspto_yield.parquet `) to `data/raw/uspto_raw.parquet`. **Fallback**: None. **Action**: Save output to `data/raw/uspto_raw.parquet`, compute SHA256 checksum, log checksum to `data/results/download_checksum.txt`. **Failure**: If source fails, raise `FileNotFoundError` with message "No verified canonical data source available". **Prerequisite: T002** (FR-001, Constitution II).
- [ ] T014 [US1] Implement `code/preprocessing/sanitize.py`: Load `data/raw/uspto_raw.parquet`. **Step 1**: Verify SHA256 checksum matches `data/results/download_checksum.txt`. **Step 2**: Use `rdkit.Chem.MolStandardize.Cleaner().clean()` to remove salts and `rdkit.Chem.rdmolops.RemoveHs()` to standardize. Output sanitized SMILES. (FR-002). **Prerequisite: T019**. **Note**: If download fails or checksum mismatch, raise error (no synthetic fallback).
- [X] T015 [US1] Implement `code/preprocessing/sanitize.py`: Handle yield parsing (ranges vs. single values). Parse "50-60%" as midpoint 55.0; exclude unparseable entries with logging. (Edge Cases) **Prerequisite: T014**
- [ ] T016 [US1] Implement `code/preprocessing/fingerprints.py`: Generate ECFP and MACCS vectors for all reactants/reagents. **Action**: Log the actual bit lengths generated (ECFP=2048, MACCS=167) to `data/results/fingerprint_dimensions.log` and include in the data quality report. **Action**: Implement **chunked/streamed processing** to generate fingerprints in batches to prevent OOM. (FR-003, SC-005). **Prerequisite: T015**
- [X] T017a [US1] Implement `code/preprocessing/ingest.py`: **Implement logic** for orchestrating sanitization (T014), yield parsing (T015), and fingerprinting (T016). **Action**: Implement **batched/chunked loading** of the raw data to prevent OOM during processing. (FR-009). **Prerequisite: T014, T015, T016**
- [ ] T017b [US1] Implement `code/preprocessing/ingest.py`: **Implement logic** for writing sanitized and fingerprinted data to `data/processed/cleaned_reactions.parquet`. **Validation**: Validate output against `dataset.schema.yaml` (columns: smiles, yield, reaction_class, fingerprint_ecfp, fingerprint_maccs; types: string, float, string, list[int], list[int]). (FR-001). **Prerequisite: T017a**
- [ ] T018a [US1] Implement `code/preprocessing/ingest.py`: **Implement logic** for logging exclusion reasons and calculating `exclusion_fraction` (excluded_rows / total_rows). (SC-005). **Prerequisite: T017b**
- [ ] T018b [US1] Implement `code/preprocessing/ingest.py`: **Implement logic** to output `data/results/data_quality_report.json` containing `exclusion_fraction` and exclusion reasons. **Prerequisite: T018a**
- [ ] T010 [Blocking Prerequisite for US2] Implement `code/preprocessing/scaffold.py`: Generate Murcko scaffold grouping keys from `data/processed/cleaned_reactions.parquet` using `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol(makeChiral=False, minNonRingSize=0)`. Output `data/processed/scaffold_groups.parquet` with column `scaffold_id`. **Prerequisite: T017b**. **Note**: This task is the **final step** of Phase 2, ensuring T017b completes before T010. It is a prerequisite for T022 (Splitting).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw USPTO data, sanitize structures, and generate ECFP4/MACCS fingerprints for a clean, analysis-ready dataset.

**Independent Test**: Run the preprocessing script on a small subset and verify the output CSV contains valid SMILES, non-null fingerprint vectors, and correct yield values without training a model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Unit test for salt removal and SMILES standardization in `tests/unit/test_sanitize.py`
- [X] T013 [P] [US1] Unit test for fingerprint dimensionality (ECFP4=2048, MACCS=167) in `tests/unit/test_fingerprints.py`

**Note**: T014-T018 are implementation tasks for US1, completed in Phase 2 to enable parallel US2 execution.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset generated)

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train Random Forest and SVM regressors with grid search/CV to identify optimal configurations under CPU constraints.

**Independent Test**: Run grid search on a small fixed validation subset and verify best hyperparameters are selected and R² is measurable.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Integration test for training pipeline on a subset in `tests/integration/test_training_pipeline.py`

### Implementation for User Story 2

- [ ] T022a [US2] Implement `code/modeling/split.py`: **Stratified-by-Class + Intra-Class Scaffold Split**. **Algorithm**: 1) Group data by `reaction_class` and `scaffold_id` (from T010). 2) **Apply Stratification**: Stratify groups by `reaction_class` to satisfy Constitution Principle VI (ensuring representation) within the primary scaffold-based grouping defined in FR-004. 3) Assign all members of a scaffold group to the same split (train/val/test). 4) Handle edge cases: classes with only one scaffold (assign to train), small classes (merge or exclude with warning). **Prerequisite: T010, T018b** (FR-004, Constitution VI).
- [ ] T022b [US2] Implement `code/modeling/split.py`: **Implement logic** for generating split artifacts. **Action**: Output `data/processed/stratified_groups.csv` (columns: `group_id`, `split`, `reaction_class`) and `data/results/split_log.json` (exact split ratios). **Prerequisite: T022a**
- [ ] T022c [US2] Implement `code/modeling/split.py`: **Implement logic** for generating strictly held-out sets. **Action**: Output `data/processed/tuning_validation_indices.csv` (for model tuning) and `data/processed/sc003_verification_indices.csv` (a distinct, strictly held-out set for SC-003 verification, NOT used for tuning). **Constraint**: Verify no `scaffold_id` appears in multiple splits. **Prerequisite: T022b**
- [X] T024 [US2] Implement `code/modeling/train.py`: Train Random Forest with grid search (k-fold CV) for `n_estimators` and `max_depth` (FR-005). **Action**: Implement **batched/chunked training** to ensure RAM < 7GB by loading data in fixed-size batches (e.g., 5000 rows) and using a generator-based approach. **Prerequisite: T022c**
- [X] T025 [US2] Implement `code/modeling/train.py`: Train SVM with grid search for `C` and `kernel` (linear/RBF) (FR-005). **Action**: Implement **batched/chunked training** to ensure RAM < 7GB by loading data in fixed-size batches (e.g., 5000 rows) and using a generator-based approach. **Prerequisite: T022c**
- [ ] T026a [US2] **Create/Update** `code/modeling/evaluate.py`: Evaluate best models on held-out test set. Output `data/results/test_metrics.json` with keys `R2` (float, 4 decimals), `RMSE` (float, 4 decimals), `MAE` (float, 4 decimals). (FR-006). **Prerequisite: T024, T025**
- [ ] T027b [US2] **Create/Update** `code/utils/memory_profiler.py`: **Implement logic** for memory profiling. **Action**: Use `tracemalloc` and `psutil` to profile peak RAM during the *loading of the largest chunk* (from T017a) and the *training process* (T024/T025). Output `data/results/memory_profile.log` and `data/results/runtime_profile.json`. **Validation**: Assert peak RAM < 7GB. (SC-004, FR-009, FR-010). **Prerequisite: T024, T025**
- [ ] T028 [US2] Save best model artifacts and hyperparameters to `data/results/best_models/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained and validated)
**Parallel Note**: Once Phase 2 (Foundational) is complete, T022 (US2 Splitting) can be implemented. **T031 (US3 Evaluation) CANNOT run in parallel with T022** as it depends on T022 via T026a. T022 must be completed before T031 can begin.

---

## Phase 5: User Story 3 - Generalization and Feature Importance Analysis (Priority: P3)

**Goal**: Evaluate generalization across reaction classes and identify predictive substructures.

**Independent Test**: Run evaluation script on test set to generate per-class metrics and a ranked list of predictive bits/substructures.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for feature importance report schema in `tests/contract/test_importance_report.py`
- [X] T030 [P] [US3] Integration test for generalization analysis in `tests/integration/test_generalization.py`

### Implementation for User Story 3

- [ ] T031a [US3] **Create/Update** `code/modeling/evaluate.py`: Compute per-reaction-class R² and RMSE metrics. Output `data/results/per_class_metrics.json` as a list of objects: `[{reaction_class, R2, RMSE, MAE},...]`. (FR-007, SC-002). **Prerequisite: T026a**
- [ ] T032a [US3] **Create/Update** `code/modeling/evaluate.py`: Compute permutation importance for Random RF. Parameters: `n_repeats=10`, `random_seed=42`. Output `data/results/permutation_importance.json` with keys `feature_index`, `importance_score` (float). (FR-008). **Prerequisite: T026a**
- [~] T033a [US3] **Create/Update** `code/modeling/evaluate.py`: Map top fingerprint bits to **molecular substructures and reaction centers**. **Algorithm**: Use `rdkit.Chem.rdMolDescriptors.GetMorganFingerprintAsBitVect` with `bitInfo` to map bits to atom indices. **Step 1**: Identify which reactant/reagent molecule each atom belongs to. **Step 2**: Extract the subgraph at the reactant-reagent boundary to define the **reaction center**. **Step 3**: Extract the surrounding substructure for **associated substructures**. Aggregation: Sum all bits mapping to the same substructure/reaction center. Output `data/results/substructure_importance.json` with keys `substructure_smiles`, `aggregated_score`, `bit_indices`, `is_reaction_center`. **Schema**: `substructure_smiles` (string), `aggregated_score` (float), `bit_indices` (list of int), `is_reaction_center` (boolean). (FR-008, SC-003). **Prerequisite: T032a**
- [~] T033b [US3] **Create/Update** `code/modeling/evaluate.py`: Map top fingerprint bits to **reaction centers** using RDKit reaction SMARTS parsing and atom mapping to identify reactant-reagent relationships. Output `data/results/reaction_center_importance.json` with keys `reaction_center_smiles`, `aggregated_score`, `bit_indices`. **Schema**: `reaction_center_smiles` (string), `aggregated_score` (float), `bit_indices` (list of int). (FR-008). **Prerequisite: T032a**
- [ ] T034 [US3] Generate final `data/results/final_report.json` containing all metrics, split ratios, and feature importance (FR-006, FR-007, FR-008)
- [ ] T035a [US3] **Create/Update** `code/modeling/evaluate.py`: Define 'high-yield' threshold by calculating a high-percentile quantile of yield in the training set. Load `data/processed/sc003_verification_indices.csv` (from T022c) and `data/results/substructure_importance.json` (from T033a). **Action**: For each reaction in the held-out set, use RDKit (`MolFromSmiles` and `HasSubstructMatch`) to check if the reaction's reactant/reagent SMILES contain the top 3 substructures. Calculate the frequency of high-yield reactions that contain these features. Output `data/results/sc003_validation.json` with `frequency` and `threshold`. **Action**: Calculate pass/fail status (frequency > 0.80) and **record pass/fail status in `data/results/final_report.json`**. (FR-006, FR-007, FR-008, SC-001, SC-002, SC-003, SC-005). **Prerequisite: T022c, T033a**. **Note**: Reaction center mapping (T033b) is NOT used for SC-003 verification.

**Checkpoint**: All user stories should now be independently functional and results aggregated

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T036 [P] Update `README.md` with quickstart instructions and dependency installation
- [ ] T037 Code cleanup: Run `ruff check --fix` and `black` on `code/` directory
- [ ] T038 Performance optimization: Ensure full pipeline runs within 6 hours on 2-CPU runner
- [ ] T039 [P] Run full test suite (`pytest`) to ensure all contract and unit tests pass
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility from scratch

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Internal Order**: T019 (Download) requires T002. T014-T017 (Ingest) must complete before T010 (Scaffold). T010 is the final step of Phase 2.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 (T010, T017)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, respecting internal order T014-T017 -> T010)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T031 (US3) **cannot** run in parallel with T022 (US2) due to dependency chain T022 -> T026a -> T031.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for salt removal in tests/unit/test_sanitize.py"

# Launch all models for User Story 1 together:
Task: "Implement sanitize.py in code/preprocessing/sanitize.py"
Task: "Implement fingerprints.py in code/preprocessing/fingerprints.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Clean dataset generated)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Analysis)
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
- **Constraint Reminder**: All tasks must run on free-tier CI (CPU, 7GB RAM, no GPU). Use `scikit-learn` and `rdkit` only.