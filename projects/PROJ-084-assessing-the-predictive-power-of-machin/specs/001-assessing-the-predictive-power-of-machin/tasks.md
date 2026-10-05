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
- [X] T003 [P] Create `code/setup.cfg` with black/ruff configuration (max-line-length=88, target-version=py) and linting tool configuration. **Prerequisite: T002**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and data preparation that MUST be complete before ANY user story can begin.
**Note**: This phase includes data ingestion, sanitization, fingerprinting, scaffold generation, batch processing, and splitting to ensure US1 and US2 can start in parallel after completion.
**Execution Order**: Tasks T019 (Download) -> T014 (Sanitize) -> T015 (Yield Parsing) -> T016 (Fingerprinting) -> T017 (Orchestration) -> T010 (Scaffold Gen) -> T021 (Batch Processing) -> T022a (Splitting Analysis) -> T022b (Splitting Execution). T027a (Utility Creation) is a standalone utility task completed before T024/T025. T027b (Log Aggregation) runs after T024/T025. T007a -> T007b. T008a (includes validator).
**CRITICAL NOTE**: T010 must complete after T017 to generate the scaffold groups required by US2. The phrase "utilized before completed" in previous notes was incorrect; T010 is the producer of scaffold IDs.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with pinned random seeds, path constants, and hyperparameter grids for RF/SVM. **Action**: Define `YIELD_RANGE_STRATEGY` constant (options: 'midpoint', 'exclude'). **Default**: 'midpoint'. **Action**: Define `SC003_HIGH_YIELD_PERCENTILE` constant (default: 0.90). **Action**: Define `USPTO_DATASET_ID` constant (default: 'farama/USPTO_Yields'). **Action**: Define `TRAIN_VAL_TEST_SPLIT_RATIOS` constant (default: `{'train': 0.7, 'val': 0.15, 'test': 0.15}`). **Action**: Define `BATCH_SIZE_ROWS` constant (default: 700000). **Action**: Define `MAX_RETRIES` constant (default: 3). **Action**: Define `SC003_HIGH_YIELD_SUBSET_PERCENTAGE` constant (default: 0.05). (FR-001, Constitution I). **Prerequisite: T002**.
- [X] T005 [P] Implement `code/utils/io.py` for robust Parquet/CSV loading, checksumming, and batch processing to manage memory < 7GB
- [X] T006 [P] Create `code/preprocessing/__init__.py` and `code/modeling/__init__.py` package structures
- [ ] T007a [P] **Define Dataset Schema**. **Action**: Create `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` (relative path from repo root) defining fields: `smiles` (string, non-null), `yield` (float, 0.0-100.0), `reaction_class` (string), `fingerprint_ecfp` (list of boolean, length 2048), `fingerprint_maccs` (list of boolean, length 167). **Content**: Write a valid YAML file with the following structure:
```yaml
type: object
properties:
 smiles:
 type: string
 minLength: 1
 yield:
 type: number
 minimum: 0.0
 maximum: 100.0
 reaction_class:
 type: string
 minLength: 1
 fingerprint_ecfp:
 type: array
 items:
 type: boolean
 description: "ECFP fingerprint vector (binary bits: true/false)"
 fingerprint_maccs:
 type: array
 items:
 type: boolean
 description: "MACCS key fingerprint (binary bits: true/false)"
required:
 - smiles
 - yield
 - reaction_class
 - fingerprint_ecfp
 - fingerprint_maccs
```
**Action**: Verify file creation by running `cat specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml`. **Prerequisite: T002** (FR-001).
**Verification**:
 1. Run `cat specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` to confirm file existence and content.
- [ ] T007b **Implement Dataset Validator**. **Action**: Implement `code/utils/validators.py` to load and enforce `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` using `pydantic`. **Validation**: Load schema from `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml`, validate a sample row, and raise error on mismatch. **Action**: Run `python -c "from code.utils.validators import validate_dataset_schema; validate_dataset_schema()"` to confirm the validator loads and runs without error. **Action**: If verification fails, raise SystemExit(1). **Prerequisite: T007a** (Note: T007b is NOT parallel-safe with T007a due to file dependency).
- [ ] T008a **Define Output Schema and Validator**. **Action**: Create `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml` defining fields: `model_type` (string), `hyperparameters` (dict), `metrics` (dict with keys R2, RMSE, MAE), `split_ratios` (dict). **Content**: Write a valid YAML file with the following structure:
```yaml
type: object
properties:
 model_type:
 type: string
 hyperparameters:
 type: object
 metrics:
 type: object
 properties:
 R2:
 type: number
 RMSE:
 type: number
 MAE:
 type: number
 required:
 - R2
 - RMSE
 - MAE
 split_ratios:
 type: object
required:
 - model_type
 - hyperparameters
 - metrics
 - split_ratios
```
**Action**: Immediately implement `code/utils/validators.py` to load and enforce `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml` using `pydantic`. **Validation**: Load schema from `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml`, validate a sample output object, and raise error on mismatch. **Action**: Run `cat specs/001-assess-ml-predictive-power/contracts/output.schema.yaml` to confirm file existence and content. **Action**: Run `python -c "from code.utils.validators import validate_output_schema; validate_output_schema()"` to confirm the validator loads and runs without error. **Action**: If verification fails, raise SystemExit(1). **Prerequisite: T002**.
**Verification**:
 1. Run `cat specs/001-assess-ml-predictive-power/contracts/output.schema.yaml` to confirm file existence and content.
 2. Run `python -c "from code.utils.validators import validate_output_schema; validate_output_schema()"` to confirm the validator loads and runs without error.
- [X] T009 Create `data/raw/.gitkeep` and `data/processed/.gitkeep` directories to ensure directory structure exists
- [ ] T019 [US1] Implement `code/preprocessing/download.py`: Download USPTO dataset. **Primary Source**: Verify the dataset source against the HuggingFace dataset ID 'farama/USPTO_Yields'. **Action**: **Step 1**: Verify the dataset ID is 'farama/USPTO_Yields'. If the dataset ID does not match, raise `FileNotFoundError` with message "Dataset source mismatch: The dataset ID in the spec does not point to a verified source." **Step 2**: Use `datasets.load_dataset("farama/USPTO_Yields", split='train')` to fetch the data directly. **Step 3**: Convert the dataset to a Pandas DataFrame and save to `data/raw/uspto_raw.parquet`. **Step 4**: If the fetch fails (HTTP error, timeout, or dataset not found), retry up to `MAX_RETRIES` (3) times. If all retries fail, raise `FileNotFoundError` with message "Dataset verification failed: Canonical source could not be accessed. No synthetic fallback allowed." **DO NOT** implement synthetic fallback mechanisms to ensure strict reproducibility (Constitution Principle I & III). **Traceability**: Log the source URL and SHA256 checksum to `data/results/download_checksum.txt`. **Action**: Log the row count of the downloaded dataset to `data/results/download_log.txt`. **Prerequisite: T002** (FR-001, Constitution I).
- [ ] T014 [US1] **Sequential Pipeline Step 1**: Implement `code/preprocessing/sanitize.py`: Load `data/raw/uspto_raw.parquet`. **Step 1**: Verify SHA256 checksum matches `data/results/download_checksum.txt`. If file contains "FAILED", raise `FileNotFoundError` with message "Download failed, no data available". **Step 2**: Use `rdkit.Chem.MolStandardize.Cleaner().clean()` to remove salts and `rdkit.Chem.rdmolops.RemoveHs()` to standardize. Output sanitized SMILES to `data/processed/sanitized_reactions.parquet`. (FR-002). **Prerequisite: T019**. **Note**: If download fails or checksum mismatch, raise error (no synthetic fallback).
- [X] T015 [US1] **Sequential Pipeline Step 2**: Implement `code/preprocessing/sanitize.py`: Handle yield parsing (ranges vs. single values). **Action**: Read `config.py` parameter `YIELD_RANGE_STRATEGY`. **Default**: 'midpoint'. **Action**: If 'midpoint', parse the midpoint of the range (e.g., "50-60%" -> 55.0) using a regex `r"(\d+)-(\d+)"`. If 'exclude', drop rows with range formats. **Action**: Log the strategy used (including the default if not set) and exclusion counts to `data/results/data_quality_report.json`. **Action**: Calculate `exclusion_fraction` as `excluded_rows / total_rows` based on this default strategy if config is unset. **Action**: Document the rationale for the chosen strategy in the report. (Edge Cases). **Prerequisite: T014**
- [ ] T016 [US1] **Sequential Pipeline Step 3**: Implement `code/preprocessing/fingerprints.py`: Generate ECFP and MACCS vectors for all reactants/reagents. **Action**: Log the actual bit lengths generated (ECFP=2048, MACCS=167) to `data/results/fingerprint_dimensions.log` and include in the data quality report. **Action**: Implement **chunked/streamed processing** to generate fingerprints in batches to prevent OOM. **Action**: Compute SHA256 checksum of `data/results/fingerprint_dimensions.log` and record it in `data/results/checksums.json`. (FR-003, SC-005). **Prerequisite: T015**
- [ ] T017 [US1] **Unified Pipeline Orchestration**. **Action**: Define the orchestration logic to call T014 (Sanitization), T015 (Yield Parsing), and T016 (Fingerprinting) in sequence. **Action**: Implement **batched/chunked loading** of the raw data to prevent OOM during processing. **Action**: Log exclusion reasons and calculate `exclusion_fraction` (excluded_rows / total_rows) **during processing**. **Action**: Output `data/processed/cleaned_reactions.parquet`. **Action**: Validate output against `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` (T007a). **Action**: If `dataset.schema.yaml` is missing, raise `FileNotFoundError` with message "Schema file missing. Ensure T007a is completed successfully." **Action**: Output `data/results/data_quality_report.json` containing `exclusion_fraction`, exclusion reasons, yield parsing strategy, and rationale. **Action**: Compute SHA256 checksum of `data/results/data_quality_report.json` and record it in `data/results/checksums.json`. **Action**: Validate `data/results/checksums.json` itself and record its hash in the project state file. (FR-001, FR-009, SC-005). **Prerequisite: T016**
- [ ] T010 [Blocking Prerequisite for US2] Implement `code/preprocessing/scaffold.py`: Generate Murcko scaffold grouping keys from `data/processed/cleaned_reactions.parquet` using `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol(makeChiral=False, minNonRingSize=0)`. **Output**: `data/processed/scaffold_groups.parquet` with a **mandatory column named 'scaffold_id'** (string) and `reaction_class`. **Action**: Log the count of unique scaffolds generated to `data/results/scaffold_generation_log.txt`. **Prerequisite: T017**. **Note**: This task is the **final step** of Phase 2, ensuring T017 completes before T010. It is a prerequisite for T021 (Filtering) and T022a (Splitting). **Schema Enforcement**: The output file MUST contain a column named exactly 'scaffold_id'.
- [ ] T021 [US2/Foundational] **Batch Process Full Dataset**. **Action**: **Step 1**: Load `data/processed/cleaned_reactions.parquet` (from T017). **Action**: **Step 2**: Calculate batch size dynamically based on available RAM. **Formula**: `BATCH_SIZE_ROWS = 700000` (derived from 7GB RAM limit and MB/10k rows estimate). **Action**: **Step 3**: Process the full dataset in batches using the calculated batch size. **Action**: **Step 4**: Concatenate batches and output `data/processed/batched_reactions.parquet`. **Action**: Log the number of batches processed and the total number of reactions processed to `data/results/batch_processing_log.json`. (FR-009, SC-004). **Prerequisite: T017**. **Note**: This task ensures the dataset is processed in batches without reducing the dataset size.
- [ ] T022a [US2/Foundational] **Load and Analyze Scaffold Groups**. **Action**: Load `data/processed/scaffold_groups.parquet` (from T010) and `data/processed/batched_reactions.parquet` (from T021). **Prerequisite: T010, T021**. **Note**: Ensure `reaction_class` column exists. **Action**: Group data by `scaffold_id` and `reaction_class`. **Action**: Identify scaffold IDs that appear in multiple `reaction_class` values. **Action**: Log these cross-class scaffold IDs to `data/processed/cross_class_scaffolds.json`. **Action**: **DO NOT** exclude them; instead, prepare for split assignment where the entire scaffold group is assigned to one split. (FR-004, Constitution VI). **Rationale**: This strict scaffold-based split is required to satisfy FR-004's "scaffold-based" mandate while preventing data leakage and ensuring class representation as per Constitution VI.
- [ ] T022b [US2/Foundational] **Perform Stratified-by-Class + Intra-Class Scaffold Grouping Split**. **Algorithm**:
 1. **Group Data**: Group the data by `reaction_class` first (Primary Split).
 2. **Stratify**: Within each `reaction_class`, group by `scaffold_id` (Secondary Split).
 3. **Assign Splits**: Assign all members of a scaffold group to the same split (train/val/test) using split ratios defined in `config.py` (Train: 0.7, Val: remaining portion, Test: remaining portion). Ensure no `scaffold_id` appears in multiple splits.
 4. **Handle Cross-Class Scaffolds**: For scaffold groups that appear in multiple reaction classes, assign the entire scaffold group to the split where it appears most frequently. **Action**: If a class has only one scaffold, assign it to the split with the most remaining capacity to preserve the global 70/15/15 ratio. **Action**: Log a WARNING if the class-level ratio deviates > 5% from target. **Action**: Log excluded data counts (if any) but do not drop data solely based on cross-class status.
 5. **Verify Class Presence**: **Step 5**: Verify that every `reaction_class` with n > 20 samples is present in the test set. If a class is missing, log a warning "CLASS_MISSING_IN_TEST_SET" and attempt to adjust the split or raise an error if adjustment is not possible.
 6. **Derive SC-003 Validation Set**: From the *Training* set (not Validation set), **sort the data by yield (descending)** and assign the **top [deferred] (rounded up)** of the Training set to the SC-003 Validation set. **Action**: Calculate the 90th percentile of the Training set yields. **Action**: Define 'high-yield' as reactions with yield > 90th percentile of the Training set. **Action**: Output `data/processed/sc003_val_indices.csv` (subset of train_indices, size=top [deferred] of Train set). **Action**: Log the 90th percentile threshold value used.
 7. **Output**:
 - `data/processed/stratified_groups.csv` (columns: `group_id`, `split`, `reaction_class`, `scaffold_id`)
 - `data/results/split_log.json` (keys: `train_ratio`, `val_ratio`, `test_ratio`, `cross_class_scaffolds_handled`, `total_samples_after_exclusion`, `class_presence_verified`, `sc003_threshold`)
 - `data/processed/train_indices.csv`
 - `data/processed/validation_indices.csv`
 - `data/processed/held_out_test_indices.csv`
 - `data/processed/sc003_val_indices.csv` (subset of train_indices, size=top [deferred] of Train set)
 - **`data/results/split_ratios_final.json`**: Explicitly log the exact split ratios (train/val/test) used to satisfy FR-004.
 **Constraint**: Verify no `scaffold_id` appears in multiple splits. Handle edge cases: classes with only one scaffold (assign to train), small classes (merge or exclude with warning). (FR-004, Constitution VI, SC-002, SC-003). **Plan Justification**: This 'Stratified-by-Class + Intra-Class Scaffold Grouping' split is the required implementation to satisfy FR-004's "scaffold-based" mandate while preventing data leakage and ensuring class representation. The scaffold grouping ensures no leakage. **Prerequisite: T022a**. **Note**: This task cannot start until Phase 2 (including T010) and T021 are fully complete.
- [X] T024 [US2] Implement `code/modeling/train.py`: Train Random Forest with grid search (k-fold CV) for `n_estimators` and `max_depth` (FR-005). **Action**: **Memory Enforcement**: Before training, load data in chunks of `BATCH_SIZE_ROWS` (700000). If OOM occurs, reduce batch size by a substantial margin and retry up to `MAX_RETRIES` (3) times. Use `n_jobs=-1` for parallelization. **Action**: Wrap execution with `@profile_memory` (T027a). **Action**: Ensure chunk sizes align with T027a's RAM limit (7GB). **Prerequisite: T022b, T027a**
- [X] T025 [US2] Implement `code/modeling/train.py`: Train SVM with grid search for `C` and `kernel` (linear/RBF) (FR-005). **Action**: **Memory Enforcement**: Before training, load data in chunks of `BATCH_SIZE_ROWS` (700000). If OOM occurs, reduce batch size by [deferred] and retry up to `MAX_RETRIES` (3) times. Use `n_jobs=-1` for parallelization. **Action**: Wrap execution with `@profile_memory` (T027a). **Action**: Ensure chunk sizes align with T027a's RAM limit (7GB). **Prerequisite: T022b, T027a**
- [X] T028 [US2] **Create/Update** `code/modeling/save_models.py`: Save best model artifacts and hyperparameters to `data/results/best_models/`. **Action**: Create directory `data/results/best_models/` if it does not exist using `mkdir -p`. Save models (RF and SVM) and hyperparameters to this directory. **Prerequisite: T024, T025**
- [~] T026a [US2] **Create/Update** `code/modeling/evaluate.py`: Evaluate best models on held-out test set AND training set. **Action**: Load `data/processed/held_out_test_indices.csv` (from T022b) to ensure independence. **Action**: **Evaluate on Test Set**: Output `data/results/test_metrics.json` with keys `R2` (float, 4 decimals), `RMSE` (float, 4 decimals), `MAE` (float, 4 decimals). **Action**: **Evaluate on Training Set**: Load `data/processed/train_indices.csv` and evaluate the model to generate baseline R². Output `data/results/train_metrics.json` with keys `R2`, `RMSE`, `MAE`. (FR-006, SC-002). **Prerequisite: T024, T025, T028, T022b**. **Note**: T028 ensures models are saved before evaluation.
- [ ] T027a [US2/Foundational] **Create Utility**: Create/Update `code/utils/memory_profiler.py`: **Implement logic** for memory profiling and runtime logging. **Action**: Create a decorator/wrapper function `@profile_memory` that uses `tracemalloc` and `psutil` to log **aggregate peak RAM** during execution. **Action**: Use `psutil.virtual_memory().total` to retrieve total system RAM. **Action**: Use `time.time()` to measure wall-clock time. **Action**: Output `data/results/memory_profile_{task_id}.log` (unique per task, e.g., `memory_profile_rf.log`, `memory_profile_svm.log`) to prevent race conditions. **Action**: Ensure thread-safe logging with unique file names for each task (e.g., `memory_profile_{task_id}.log`) to prevent race conditions if tasks run in parallel. **Validation**: Assert total system RAM < 7GB for each step. **Action**: Output JSON containing `peak_ram_mb` and `wall_clock_time_seconds` to the log file. (SC-004, FR-009, FR-010). **Prerequisite: T005**. **Note**: This task creates the utility file and is a blocking prerequisite for T024/T025. It must be completed before T024/T025 to be used as a decorator.
- [ ] T027b [US2/Foundational] **Aggregate Logs**. **Action**: After T024 and T025 complete, aggregate the logs generated by the `@profile_memory` decorator into a single report. **Action**: Output `data/results/memory_profile.log` and `data/results/runtime_profile.json` containing peak RAM and runtime for each wrapped step. **Validation**: Assert total system RAM < 7GB for each step. (SC-004, FR-009, FR-010). **Prerequisite: T024, T025**. **Note**: This task is NOT parallel-safe and must run after training.
- [ ] T031 [US3] **Create/Update** `code/modeling/evaluate.py`: Compute per-reaction-class R² and RMSE metrics. **Action**: Load `data/processed/held_out_test_indices.csv` (from T022b) to ensure independence. **Action**: **Filter** classes with sample count `n > 20`. **Action**: **Calculate** generalization gap (Training R² from `train_metrics.json` - Test R² from `test_metrics.json`) for each filtered class. **Action**: Output `data/results/per_class_metrics.json` and `data/results/generalization_gap_report.json` (containing filtered classes, gap values, and pass/fail status for SC-002). (FR-007, SC-002). **Prerequisite: T026a, T028, T022b**
- [ ] T032a [US3] **Create/Update** `code/modeling/evaluate.py`: Compute permutation importance for Random RF. Parameters: `n_repeats=5`, `random_state=42`, `n_jobs=-1`. Output `data/results/permutation_importance.json` with keys `feature_index`, `importance_score` (float). (FR-008). **Prerequisite: T026a, T028**
- [ ] T033a [US3] **Create/Update** `code/modeling/evaluate.py`: **Bit-to-Atom Mapping**. **Action**: Use `rdkit.Chem.rdMolDescriptors.GetMorganFingerprintAsBitVect` with `bitInfo` to map bits to atom indices. **Action**: Output `data/results/bit_mapping.json` with keys `bit_index`, `atom_indices`, `molecule_id`. (FR-008). **Prerequisite: T032a, T028**
- [ ] T033b [US3] **Create/Update** `code/modeling/evaluate.py`: **Reaction Center Identification**. **Action**: For each reaction, identify the **reaction center** by comparing reactant and product bond orders. **Logic**: Use `rdkit.Chem.rdChemReactions.ReactionFromSmarts` with a standard template to parse the reaction. **Step 1**: Extract reactant and product molecules. **Step 2**: Calculate the difference in bond order (product bond order - reactant bond order) for all bonds. **Threshold**: Select all bonds where the absolute difference is >= 1.0. **Edge Case Handling**: If no bonds meet the threshold, select the atom pair with the highest reactivity score based on atom type priority (e.g., heteroatoms > carbon). If multiple bonds meet the threshold, select the one with the highest absolute bond order change magnitude. **Output Format**: For each reaction center, record `atom_indices` (list of ints), `bond_changes` (list of objects: `{bond_index, old_order, new_order}`), `ambiguous` (boolean, True if multiple centers detected), and `reaction_center_count` (int). **Action**: **Explicitly acknowledge bit collisions**: If multiple bits map to the same substructure or one bit maps to multiple substructures, set `bit_collision_acknowledged` to True in the output. **Action**: Output `data/results/reaction_centers.json`. (FR-008). **Prerequisite: T033a**
- [ ] T033c [US3] **Create/Update** `code/modeling/evaluate.py`: **Unified Feature Importance Mapping**. **Action**: **Step 1**: Extract the subgraph surrounding the reaction center atom within a defined topological radius (e.g., `radius=2`). **Action**: **Step 2**: Sum all bits mapping to the same substructure (SMILES string). **Collision Resolution**: **Sum the importance scores** of all bits mapping to the same substructure to determine the aggregated score. **Action**: **Step 3**: Detect and count instances where multiple bits map to the same substructure or one bit maps to multiple substructures. **Action**: **Step 4**: Rank and Select Top Subset: Sort substructures by `aggregated_score` descending and select a representative subset of top-ranked substructures. **Action**: **Step 5**: Output `data/results/feature_importance_report.json` with keys `substructure_smiles`, `aggregated_score`, `bit_indices`, `collision_count`, `collision_details` (list of objects: `{bit_index: int, substructure_smiles: str, score: float}`). **Action**: Include a specific list `top_3_substructures` in the output. (FR-008, SC-003). **Prerequisite: T033b**
- [ ] T035a [US3] **Create/Update** `code/modeling/evaluate.py`: **SC-003 Validation**. **Action**: **Step 1: Define Threshold**. Define 'high-yield' as reactions with yield > 90th percentile of the yields in the Training set (calculated in T022b). **Action**: **Step 2: Calculate Frequency**. Load `data/processed/sc003_val_indices.csv` (from T022b Step 6), `data/results/feature_importance_report.json` (from T033c), and `data/results/best_models/` (from T028). **Action**: Identify high-yield reactions in the SC-003 Validation set using the **quantile threshold** (this matches the definition of 'high-yield' in SC-003). **Action**: Calculate the frequency of high-yield reactions that contain the top-ranked substructures identified in `top_3_substructures`. **Action**: Determine `pass_fail_status` based on whether frequency > 0.80. **Fallback**: If the SC-003 Validation set has a small number of reactions above the threshold, log a warning "INSUFFICIENT_HIGH_YIELD_SAMPLES" and report `pass_fail_status: "INSUFFICIENT_DATA"`. **Output**: `data/results/sc003_validation.json` with `frequency`, `yield_threshold`, `frequency_threshold`, and `pass_fail_status` (frequency > 0.80 or "INSUFFICIENT_DATA"). **Action**: Record pass/fail status in `data/results/final_report.json`. (FR-006, FR-007, FR-008, SC-001, SC-002, SC-003, SC-005). **Prerequisite: T022b, T033c, T028**. **Note**: Reaction center mapping (T033) is used for SC-003 verification. **Strict Ordering**: Ensure T022b completes before T035a.

**Checkpoint**: All user stories should now be independently functional and results aggregated

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

- [X] T024 [US2] Implement `code/modeling/train.py`: Train Random RF (see Phase 2). **Prerequisite: T022b, T027a**
- [X] T025 [US2] Implement `code/modeling/train.py`: Train SVM (see Phase 2). **Prerequisite: T022b, T027a**
- [X] T028 [US2] Save models (see Phase 2). **Prerequisite: T024, T025**
- [~] T026a [US2] Evaluate models (see Phase 2). **Prerequisite: T024, T025, T028, T022b**
- [ ] T027b [US2/Foundational] Aggregate logs (see Phase 2). **Prerequisite: T024, T025**
- [ ] T031 [US3] Per-class metrics (see Phase 2). **Prerequisite: T026a, T028, T022b**
- [ ] T032a [US3] Permutation importance (see Phase 2). **Prerequisite: T026a, T028**
- [ ] T033a [US3] Bit-to-atom mapping (see Phase 2). **Prerequisite: T032a, T028**
- [ ] T033b [US3] Reaction center identification (see Phase 2). **Prerequisite: T033a**
- [ ] T033c [US3] Unified feature importance mapping (see Phase 2). **Prerequisite: T033b**
- [ ] T035a [US3] SC-003 validation (see Phase 2). **Prerequisite: T022b, T033c, T028**

**Checkpoint**: All user stories should now be independently functional and results aggregated

---

## Phase 5: User Story 3 - Generalization and Feature Importance Analysis (Priority: P3)

**Goal**: Evaluate generalization across reaction classes and identify predictive substructures.

**Independent Test**: Run evaluation script on test set to generate per-class metrics and a ranked list of predictive bits/substructures.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for feature importance report schema in `tests/contract/test_importance_report.py`
- [X] T030 [P] [US3] Integration test for generalization analysis in `tests/integration/test_generalization.py`

- [ ] T034 [US3] Generate final `data/results/final_report.json` containing all metrics, split ratios (from `data/results/split_ratios_final.json`), and feature importance (FR-006, FR-007, FR-008). **Prerequisite: T031, T033c, T035a, T022b**.

**Checkpoint**: All user stories should now be independently functional and results aggregated

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T036 [P] Update `README.md` with quickstart instructions and dependency installation
- [ ] T037 Code cleanup: Run `ruff check --fix` and `black` on `code/` directory
- [ ] T038 Performance optimization: Ensure full pipeline runs within 6 hours on **free-tier CPU runner**. **Action**: Use `n_jobs=-1` for parallelization, implement chunked processing, and profile with `tracemalloc` to identify bottlenecks. **Prerequisite: T039**.
- [ ] T039 [P] Run full test suite (`pytest`) to ensure all contract and unit tests pass
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility from scratch

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Internal Order**: T019 (Download) requires T002. T014-T017 (Ingest) must complete before T010 (Scaffold). T010 is the final step of Phase 2. T021 (Batch Processing) must complete before T022 (Splitting). T027a (Utility Creation) is a standalone utility task completed before T024/T025. T027b (Log Aggregation) runs after T024/T025. T007a -> T007b. T008a (includes validator).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 (T010, T017, T021)
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
 - **Note**: T014, T015, T016, T017 are sequential, not parallel.
 - **Note**: T007a and T007b are sequential, not parallel.
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
- **Constraint Reminder**: All tasks must run on free-tier CI (CPU, sufficient RAM, no GPU). Use `scikit-learn` and `rdkit` only.