# Tasks: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

**Input**: Design documents from `/specs/001-assess-ml-predictive-power/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
- [X] T002 Initialize Python project with `pandas`, `scikit-learn`, `rdkit`, `pyyaml`, `pytest`, `pydantic` in `code/requirements.txt`
- [X] T003 [P] Create `code/setup.cfg` with black/ruff configuration (max-line-length=88, target-version=py311) and linting tool configuration. **Prerequisite: T002**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and data preparation that MUST be complete before ANY user story can begin.
**Note**: This phase includes data ingestion, sanitization, fingerprinting, and scaffold generation to ensure US1 and US2 can start in parallel after completion.
**Execution Order**: Tasks T014-T017 MUST complete before T010 is fully utilized, but T010 (Scaffold Gen) is moved here to unblock US2 splitting logic. T019 (Download) must complete before T014-T017.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with pinned random seeds, path constants, and hyperparameter grids for RF/SVM
- [X] T005 [P] Implement `code/utils/io.py` for robust Parquet/CSV loading, checksumming, and batch processing to manage memory < 7GB
- [X] T006 [P] Create `code/preprocessing/__init__.py` and `code/modeling/__init__.py` package structures
- [ ] T007a [P] Create `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` defining fields: `smiles` (string, non-null), `yield` (float, 0.0-100.0), `reaction_class` (string), `fingerprint_ecfp` (list of int, length 2048), `fingerprint_maccs` (list of int, length 167). **Content**: Write a valid YAML file with the following structure:
```yaml
type: object
properties:
 smiles: { type: string, minLength: 1 }
 yield: { type: number, minimum: 0.0, maximum: }
 reaction_class: { type: string, minLength: 1 }
 fingerprint_ecfp: { type: array, items: { type: integer }, minItems: "sufficient for molecular representation", maxItems: "sufficient for molecular representation" }
 fingerprint_maccs: { type: array, items: { type: integer }, minItems: [fixed_length], maxItems: [fixed_length] }

The specific value to remove/generalize: [fixed_length]
required: [smiles, yield, reaction_class, fingerprint_ecfp, fingerprint_maccs]
```
**Prerequisite: None**
- [ ] T007b [P] Implement `code/utils/validators.py` to load and enforce `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` using `pydantic` (v2). **Validation**: Load schema from `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml`, validate a sample row, and raise error on mismatch. **Prerequisite: T007a**
- [ ] T008a [P] Create `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml` defining fields: `model_type` (string), `hyperparameters` (dict), `metrics` (dict with keys R2, RMSE, MAE), `split_ratios` (dict). **Content**: Write a valid YAML file with the following structure:
```yaml
type: object
properties:
 model_type: { type: string }
 hyperparameters: { type: object }
 metrics:
   type: object
   properties:
     R2: { type: number }
     RMSE: { type: number }
     MAE: { type: number }
   required: [R2, RMSE, MAE]
 split_ratios: { type: object }
required: [model_type, hyperparameters, metrics, split_ratios]
```
**Prerequisite: None**
- [ ] T008b [P] Implement `code/utils/validators.py` to load and enforce `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml` using `pydantic`. **Validation**: Load schema from `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml`, validate a sample output object, and raise error on mismatch. **Prerequisite: T008a**
- [X] T009 Create `data/raw/.gitkeep` and `data/processed/.gitkeep` directories to ensure directory structure exists
- [ ] T019 [US1] Implement `code/preprocessing/download.py`: Download USPTO dataset. **Primary Source**: HuggingFace ID `farside/uspto-yields`. **Action**: Fetch data to `data/raw/uspto_raw.parquet` using `datasets.load_dataset("farside/uspto-yields", split="train")`. **Traceability**: Log the source used and SHA256 checksum to `data/results/download_checksum.txt`. **Failure**: If the fetch fails, raise `FileNotFoundError` with a clear message. **DO NOT** implement fallback mechanisms to ensure strict reproducibility (Constitution Principle I & III). **Verification**: Check if the dataset ID exists before fetching. **Prerequisite: T002** (FR-001, Constitution I).
- [ ] T014 [US1] Implement `code/preprocessing/sanitize.py`: Load `data/raw/uspto_raw.parquet`. **Step 1**: Verify SHA256 checksum matches `data/results/download_checksum.txt`. If file contains "FAILED", raise `FileNotFoundError` with message "Download failed, no data available". **Step 2**: Use `rdkit.Chem.MolStandardize.Cleaner().clean()` to remove salts and `rdkit.Chem.rdmolops.RemoveHs()` to standardize. Output sanitized SMILES. (FR-002). **Prerequisite: T019**. **Note**: If download fails or checksum mismatch, raise error (no synthetic fallback).
- [X] T015 [US1] Implement `code/preprocessing/sanitize.py`: Handle yield parsing (ranges vs. single values). **Action**: Read `config.py` parameter `YIELD_RANGE_STRATEGY` (options: 'midpoint', 'exclude'). If 'midpoint', parse "50-60%" as 55.0. If 'exclude', drop rows with range formats. **Action**: Log the strategy used and exclusion counts to `data/results/data_quality_report.json`. **Action**: Document the rationale for the chosen strategy in the report. (Edge Cases). **Prerequisite: T014**
- [ ] T016 [US1] Implement `code/preprocessing/fingerprints.py`: Generate ECFP and MACCS vectors for all reactants/reagents. **Action**: Log the actual bit lengths generated (ECFP=2048, MACCS=167) to `data/results/fingerprint_dimensions.log` and include in the data quality report. **Action**: Implement **chunked/streamed processing** to generate fingerprints in batches to prevent OOM. (FR-003, SC-005). **Prerequisite: T015**
- [ ] T017 [US1] Implement `code/preprocessing/ingest.py`: **Unified Pipeline Orchestration**. **Action**: Orchestrate T014 (Sanitization), T015 (Yield Parsing), and T016 (Fingerprinting) in sequence. **Action**: Implement **batched/chunked loading** of the raw data to prevent OOM during processing. **Action**: Log exclusion reasons and calculate `exclusion_fraction` (excluded_rows / total_rows) **during processing**. Output `data/processed/cleaned_reactions.parquet`. **Validation**: Validate output against `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` (T007a). **Action**: Output `data/results/data_quality_report.json` containing `exclusion_fraction`, exclusion reasons, yield parsing strategy, and rationale. (FR-001, FR-009, SC-005). **Prerequisite: T016**
- [ ] T010 [Blocking Prerequisite for US2] Implement `code/preprocessing/scaffold.py`: Generate Murcko scaffold grouping keys from `data/processed/cleaned_reactions.parquet` using `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol(makeChiral=False, minNonRingSize=0)`. **Output**: `data/processed/scaffold_groups.parquet` with a **mandatory column named 'scaffold_id'** (string) and `reaction_class`. **Prerequisite: T017**. **Note**: This task is the **final step** of Phase 2, ensuring T017 completes before T010. It is a prerequisite for T022 (Splitting). **Schema Enforcement**: The output file MUST contain a column named exactly 'scaffold_id'.
- [X] T027b [US2/Foundational] **Create/Update** `code/utils/memory_profiler.py`: **Implement logic** for memory profiling. **Action**: Create a decorator/wrapper function `@profile_memory` that uses `tracemalloc` and `psutil` to log **aggregate peak RAM** during execution. **Action**: Use `psutil.virtual_memory().total` to retrieve total system RAM. **Action**: Wrap the execution of T017 (Unified Pipeline), T024 (RF Training), and T025 (SVM Training) with this wrapper. **Action**: Output `data/results/memory_profile.log` and `data/results/runtime_profile.json` containing peak RAM for each wrapped step. **Validation**: Assert total system RAM < 7GB for each step. (SC-004, FR-009, FR-010). **Prerequisite: T005** (Note: T027b is now a standalone utility task, completed before T024/T025).

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

**Note**: T014-T017 are implementation tasks for US1, completed in Phase 2 to enable parallel US2 execution.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset generated)

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train Random Forest and SVM regressors with grid search/CV to identify optimal configurations under CPU constraints.

**Independent Test**: Run grid search on a small fixed validation subset and verify best hyperparameters are selected and R² is measurable.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Integration test for training pipeline on a subset in `tests/integration/test_training_pipeline.py`

### Implementation for User Story 2

- [ ] T022a [US2/Foundational] Implement `code/modeling/split.py`: **Stratified-by-Class + Intra-Class Scaffold Split**. **Algorithm**: 1) Load `data/processed/scaffold_groups.parquet` (from T010) and `data/processed/cleaned_reactions.parquet` (from T017). 2) **Identify Cross-Class Scaffolds**: Find scaffold IDs that appear in multiple `reaction_class` values. 3) **Assign Primary Class**: For each scaffold group, determine its "primary" reaction class (the one with the most samples) and assign the **entire group** to that class for splitting purposes. **DO NOT exclude data**. 4) **Group Remaining Data**: Group the remaining data by `reaction_class` and `scaffold_id`. 5) **Apply Stratification**: Stratify groups by `reaction_class` to satisfy Constitution Principle VI. 6) Assign all members of a scaffold group to the same split (train/val/test). 7) Handle edge cases: classes with only one scaffold (assign to train), small classes (merge or exclude with warning). **Output**: `data/processed/excluded_scaffolds.json` (list of cross-class scaffolds that were assigned to a primary class), `data/processed/stratified_groups.csv` (columns: `group_id`, `split`, `reaction_class`, `scaffold_id`), `data/results/split_log.json` (keys: `train_ratio`, `val_ratio`, `test_ratio`, `cross_class_scaffolds_handled`). **Prerequisite: T017, T010** (FR-004, Constitution VI). **Note**: This task cannot start until Phase 2 (including T010) is fully complete.
- [ ] T022c [US2] Implement `code/modeling/split.py`: **Implement logic** for generating train and validation splits. **Action**: From the stratified groups (T022a), assign a majority of groups to train and a minority to validation. Output `data/processed/train_indices.csv` and `data/processed/validation_indices.csv`. **Action**: **Output** `data/processed/remaining_groups.parquet` containing the groups NOT assigned to train or validation. **Constraint**: Verify no `scaffold_id` appears in both train and validation. **Prerequisite: T022a**
- [ ] T022d [US2] Implement `code/modeling/split.py`: **Implement logic** for generating strictly held-out test sets. **Action**: Load `data/processed/remaining_groups.parquet` (from T022c). Assign these remaining groups to the test set. Output `data/processed/held_out_test_indices.csv` (strictly for final evaluation, SC-001/SC-002). **Constraint**: Verify no `scaffold_id` appears in train, validation, or test splits. **Prerequisite: T022c**
- [ ] T022e [US2/SC-003] Implement `code/modeling/split.py`: **Generate SC-003 Held-Out Validation Set**. **Action**: Load `data/processed/cleaned_reactions.parquet` (from T017) and `data/processed/scaffold_groups.parquet` (from T010). **Action**: **Exclude** the groups assigned to Train, Val, and Test (load `train_indices.csv`, `validation_indices.csv`, `held_out_test_indices.csv`). **Action**: From the remaining disjoint groups, assign a subset to the SC-003 validation set (reusing the Validation set logic if necessary, or creating a disjoint set if data volume permits). Output `data/processed/sc003_val_indices.csv`. **Constraint**: Ensure this set is disjoint from train, val, and test sets. **Prerequisite: T022a, T022c, T022d**
- [X] T024 [US2] Implement `code/modeling/train.py`: Train Random Forest with grid search (k-fold CV) for `n_estimators` and `max_depth` (FR-005). **Action**: Implement **batched/chunked training** to ensure RAM < 7GB by loading data in fixed-size batches and using a generator-based approach. **Action**: Wrap execution with `@profile_memory` (T027b). **Prerequisite: T022c, T027b**
- [X] T025 [US2] Implement `code/modeling/train.py`: Train SVM with grid search for `C` and `kernel` (linear/RBF) (FR-005). **Action**: Implement **batched/chunked training** to ensure RAM < 7GB by loading data in fixed-size batches (e.g., a substantial number of rows) and using a generator-based approach. **Action**: Wrap execution with `@profile_memory` (T027b). **Prerequisite: T022c, T027b**
- [ ] T028 [US2] **Create/Update** `code/modeling/save_models.py`: Save best model artifacts and hyperparameters to `data/results/best_models/`. **Action**: Create directory `data/results/best_models/` if it does not exist using `mkdir -p`. Save models (RF and SVM) and hyperparameters to this directory. **Prerequisite: T024, T025**
- [ ] T026a [US2] **Create/Update** `code/modeling/evaluate.py`: Evaluate best models on held-out test set. **Action**: Load `data/processed/held_out_test_indices.csv` (from T022d) to ensure independence. Output `data/results/test_metrics.json` with keys `R2` (float, 4 decimals), `RMSE` (float, 4 decimals), `MAE` (float, 4 decimals). (FR-006). **Prerequisite: T024, T025, T022d, T028**
- [ ] T031 [US3] **Create/Update** `code/modeling/evaluate.py`: Compute per-reaction-class R² and RMSE metrics. **Action**: Load `data/processed/held_out_test_indices.csv` (from T022d) to ensure independence. **Action**: **Filter** classes with sample count `n > 20`. **Action**: **Calculate** generalization gap (Training R² - Test R²) for each filtered class. **Action**: Output `data/results/per_class_metrics.json` and `data/results/generalization_gap_report.json` (containing filtered classes, gap values, and pass/fail status for SC-002). (FR-007, SC-002). **Prerequisite: T026a, T028**
- [ ] T032a [US3] **Create/Update** `code/modeling/evaluate.py`: Compute permutation importance for Random RF. Parameters: `n_repeats=10`, `random_seed=42`. Output `data/results/permutation_importance.json` with keys `feature_index`, `importance_score` (float). (FR-008). **Prerequisite: T026a, T028**
- [ ] T033 [US3] **Create/Update** `code/modeling/evaluate.py`: **Unified Feature Importance Mapping**. Map top fingerprint bits to **molecular substructures** in a single report. **Algorithm**: Use `rdkit.Chem.rdMolDescriptors.GetMorganFingerprintAsBitVect` with `bitInfo` to map bits to atom indices. **Step 1**: Identify which reactant/reagent molecule each atom belongs to. **Step 2**: Extract the subgraph surrounding the atom (radius 2) to define the **associated substructure**. **Aggregation**: Sum all bits mapping to the same substructure (SMILES string). **Collision Handling**: Detect and count instances where multiple bits map to the same substructure or one bit maps to multiple substructures. **Output**: `data/results/feature_importance_report.json` with keys `substructure_smiles`, `aggregated_score`, `bit_indices`, `collision_count`, `collision_details` (list of objects: `{bit_index, atom_indices, substructure_smiles}`). (FR-008, SC-003). **Prerequisite: T032a, T028**
- [ ] T034 [US3] Generate final `data/results/final_report.json` containing all metrics, split ratios, and feature importance (FR-006, FR-007, FR-008)
- [ ] T035a [US3] **Create/Update** `code/modeling/evaluate.py`: Define 'high-yield' threshold by calculating the **top [deferred] quantile of yield across the ENTIRE dataset** (global constant). Load the **held-out validation set for SC-003** (from `data/processed/sc003_val_indices.csv` from T022e) and `data/results/feature_importance_report.json` (from T033). **Action**: For each reaction in the **SC-003 validation set**, use RDKit (`MolFromSmiles` and `HasSubstructMatch`) to check if the reaction's reactant/reagent SMILES contain the top substructures. Calculate the frequency of high-yield reactions (using the global threshold) that contain these features in the **SC-003 validation set**. Output `data/results/sc003_validation.json` with `frequency`, `threshold`, and `pass_fail_status` (frequency > 0.80). **Action**: Record pass/fail status in `data/results/final_report.json`. (FR-006, FR-007, FR-008, SC-001, SC-002, SC-003, SC-005). **Prerequisite: T022c, T022e, T033, T028**. **Note**: Reaction center mapping (T033) is used for SC-003 verification. **Strict Ordering**: Ensure T022c completes before T022e, and T022e completes before T035a.

**Checkpoint**: All user stories should now be independently functional and results aggregated

---

## Phase 5: User Story 3 - Generalization and Feature Importance Analysis (Priority: P3)

**Goal**: Evaluate generalization across reaction classes and identify predictive substructures.

**Independent Test**: Run evaluation script on test set to generate per-class metrics and a ranked list of predictive bits/substructures.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for feature importance report schema in `tests/contract/test_importance_report.py`
- [X] T030 [P] [US3] Integration test for generalization analysis in `tests/integration/test_generalization.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T036 [P] Update `README.md` with quickstart instructions and dependency installation
- [ ] T037 Code cleanup: Run `ruff check --fix` and `black` on `code/` directory
- [ ] T038 Performance optimization: Ensure full pipeline runs within 6 hours on **free-tier CPU runner**
- [ ] T039 [P] Run full test suite (`pytest`) to ensure all contract and unit tests pass
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility from scratch

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Internal Order**: T019 (Download) requires T002. T014-T017 (Ingest) must complete before T010 (Scaffold). T010 is the final step of Phase 2. T027b (Profiling) is a standalone utility task completed before T024/T025.
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