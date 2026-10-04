# Tasks: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-lens-rethink/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential - must run after specific predecessors due to resource contention or data flow
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

**Purpose**: Project initialization, basic structure, and **Contract Creation**.

- [X] T001 [P] Define and Execute Project Directory Structure: Create `projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/` including `data/raw`, `data/processed`, `data/logs`, `data/external`, `code`, `code/data`, `code/tests`, `code/utils`, `code/models`, `docs`. **Requirement**: Ensure `data/` and `code/` are **sibling directories** at the project root. **Implementation**: Execute the following shell commands: `mkdir -p projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/{data/raw,data/processed,data/logs,data/external,code,code/data,code/tests,code/utils,code/models,docs}` and `touch projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/{code/__init__.py,data/__init__.py}`.
- [X] T002 [P] Initialize a Python project with `requirements.txt` (xgboost, scikit-learn, transformers, spacy, datasets, pandas, numpy, pydantic, jsonschema, **torch**). **Note**: `torch` (CPU-only version) is a **REQUIRED dependency** for CPU-only BERT inference in T014a; it is NOT optional.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools. **Requirement**: Create `.ruff.toml` and `pyproject.toml` with black settings. **Implementation**: Write configuration files to repository root.
- [X] T004a [P] [Setup] Create data schema contracts in `specs/001-llmxive-follow-up-extending-lens-rethink/contracts/` (dataset, feature_vector, deviation_target, significance_results). **Note**: Moved to Phase 1 to ensure contracts exist before validation tasks (T018a). **Requirement**: Define `DataSchemaError` message "Missing required dataset or column: pick-a-pic/human_rating" for FR-003.
- [X] T004b [P] [Setup] **Contract Test Scaffolding & Error Factory**: 1) Create `code/tests/contract/` directory and implement basic scaffolding for contract validation tests (e.g., `test_dataset_schema.py`). 2) Implement a unified `DataSchemaError` factory function in `code/utils/errors.py` that generates the standardized error message pattern "Missing required dataset or column: {source}/{column}". **Requirement**: This task ensures the "Single Source of Truth" validation loop is complete per Spec Assumptions. **Dependency**: Requires T004a. **Note**: While T004b logically depends on T004a (schema definition), the physical implementation (creating empty test scaffolding) can run in parallel if T004a creates the file first. **Implementation**: Create directory and files.
- [X] T005 [P] Setup `code/__init__.py` and directory structure (`data/`, `code/`, `tests/`) - create empty `__init__.py` files and ensure directories `data/raw`, `data/processed`, `code/data`, `code/tests`, `code/utils`, `code/models` exist as **siblings** at the project root (not nested).
- [X] T006 [P] Implement basic logging infrastructure in `code/utils/logging.py`.
- [X] T007 [P] Create base data model entities: `code/models/caption_record.py` (class `CaptionRecord`) and `code/models/linguistic_feature_vector.py` (class `LinguisticFeatureVector`).
- [X] T008 [P] Setup environment configuration management (seed pinning, path constants) in `code/config.py`.
- [ ] T009 [S] [US1] Implement `code/data/download.py` to **materialize** the `pick-a-pic` dataset to `data/raw/pick-a-pic.parquet` (or equivalent) via `datasets.load_dataset(..., streaming=True)`. **Requirement**: Explicitly validate the presence of the 'human_rating' column. **Crucial**: Check for dataset availability; if `load_dataset` fails, **raise `DataSchemaError`** with the exact message "Missing required dataset or column: pick-a-pic/human_rating". **Note**: This task MUST materialize the file to disk before T010 can checksum it. **Note**: Consumes output stream from HuggingFace. **Fallback**: If the full dataset exceeds RAM/disk limits during streaming, materialize a verified subset (e.g., a representative sample of manageable size) and log the subset size. **Implementation**: Execute download script.
- [X] T013 [S] [US1] **REMOVED**: Task T013 (Stratified Random Sampling) has been removed as it contradicted the Spec requirement to use the full dataset. The analysis will now process the full dataset or fail loudly.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Data Acquisition to ensure Producer-before-Consumer.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T010 [S] [Setup] Implement checksumming logic in `code/data/download.py` and update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with raw data hashes. **Dependency**: This task MUST run AFTER T009 (Data Loading) is complete and the raw file is materialized to `data/raw/pick-a-pic.parquet`.
- [X] T014a [S] [US1] Implement `def compute_linguistic_uncertainty_proxy(caption: str) -> float` in `code/features.py` using `bert-base-uncased` on CPU. Explicitly apply natural logarithm to perplexity (`ln(perplexity)`) per FR-001. **Requirement**: **Explicitly separate** two error paths: 1) **Timeout (FR-001)**: If calculation exceeds a predefined time threshold (**5 seconds**, configured as `BERT_TIMEOUT_SECONDS` in `code/config.py`), exclude sample, log `caption_id` with reason 'TIMEOUT_EXCEEDED'. 2) **Inference Failure (FR-012)**: If BERT model loading or inference fails (e.g., model not found), catch exception, log `caption_id` with reason 'BERT_FAILURE', and exclude the row. **Atomic Exclusion**: If BERT fails, **immediately exclude the row** and do NOT proceed to compute other features for this record. **Note**: Consumes output stream from T009.
- [X] T014b [S] [US1] **Preliminary Validation**: Validate `compute_linguistic_uncertainty_proxy` logic and produce `results/validation_report.json` (US1). **Note**: This task validates the feature logic itself. Final Constitution Enforcement is handled by T045 in Phase 5.
- [ ] T015 [S] [US1] Implement `def compute_syntactic_depth(caption: str) -> int` in `code/features.py` using `spaCy` (FR-002). **Requirement**: If the caption is too short to compute a meaningful dependency tree depth (e.g., single words), EXCLUDE the sample from the training matrix and log the exclusion reason with the specific caption ID (FR-011). **Output**: Must write exclusion logs to `data/logs/exclusions.log`.
- [ ] T015b [S] [US1] **Exclusion Log Processing**: Read `data/logs/exclusions.log` (generated by T014a, T015), aggregate exclusion counts by reason, and write a summary to `data/processed/exclusion_summary.json`. **Dependency**: Requires completion of T014a and T015. **Fallback**: If `exclusions.log` is missing, create an empty summary file and log a warning.
- [X] T016a [P] [US1] Implement `def compute_noun_phrase_density(caption: str) -> float` in `code/features.py`.
- [X] T016b [P] [US1] Implement `def compute_token_diversity(caption: str) -> float` in `code/features.py`.
- [X] T017 [US1] Implement `def extract_features_batch(captions: list[str]) -> pd.DataFrame` in `code/features.py` with edge case handling (short captions -> exclude & log, BERT failure -> log & exclude, timeout -> exclude & log). **Note**: T014a's timeout logic excludes the sample.
- [X] T018a [S] [US1] Implement validation logic in `code/utils/validation.py`: 1) Load `specs/001-llmxive-follow-up-extending-lens-rethink/contracts/feature_vector.schema.yaml`, 2) Validate DataFrame against schema using `pydantic`, 3) Raise `ValueError` on mismatch. **Requirement**: Also validate raw dataset availability and 'human_rating' column presence before feature vector validation (FR-003). **Dependency**: Requires T004a (Contracts). **Note**: Runs after T017 to validate its output. **Fallback**: If `feature_vector.schema.yaml` is missing, create it based on the spec definition before validation.
- [X] T018b [S] [US1] Create `code/data/features.py` script wrapper to **consume processed raw data stream from T009**, call extraction functions, **call T018a for schema validation**, and save to `data/processed/features.csv`. **Dependency**: Requires T018a.
- [ ] T018c [S] [US1] **Stratified Split for Validation**: Implement logic to split `data/processed/features.csv` into `data/processed/features_train.csv` and `data/processed/features_held_out.csv` using a stratified split (by caption length or other metric) to satisfy FR-009. **Output**: Save both files. **Requirement**: Explicitly produce the **held-out subset** required by FR-009 for construct validity. **Dependency**: Requires T018b.

### Tests for User Story 1

- [X] T019 [P] [US1] Write unit test scaffolding for `compute_linguistic_uncertainty_proxy` in `code/tests/test_features.py` (verify `ln(perplexity)` calculation and exclusion logic)
- [ ] T020 [P] [US1] Write unit test scaffolding for `compute_syntactic_depth` in `code/tests/test_features.py` (verify spaCy dependency tree depth)
- [ ] T021 [P] [US1] Write integration test scaffolding for full feature extraction pipeline in `code/tests/test_features.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Calculate Alignment Deviation Score (Priority: P2)

**Goal**: Calculate the target variable $Y = | \text{CLIP\_Score} - \text{Human\_Rating} |$ from human preference data.

**Independent Test**: Feed a dataset with known CLIP/Human values; verify deviation calculation is correct and rows with missing human ratings are excluded.

### Implementation for User Story 2

- [ ] T021a [S] [US2] Implement `def validate_clip_scores(dataset: pd.DataFrame) -> pd.DataFrame` in `code/data/preprocess.py`. **Requirement**: Check for the presence of the 'clip_score' column in the 'pick-a-pic' dataset. If absent, raise `DataSchemaError` with the **unified message** from T004b: "Missing required dataset or column: pick-a-pic/clip_score". **Note**: This task validates pre-computed scores per FR-003; it does NOT generate scores via inference. **Input**: Output of T009 (Data).
- [ ] T022 [S] [US2] Implement `def normalize_and_calculate_deviation(clip_scores: list[float], human_ratings: list[float]) -> list[float]` in `code/data/preprocess.py`. **Atomic operation**: 1) **Fail Loudly**: If 'human_rating' column is missing in input, raise `DataSchemaError` immediately. 2) Perform **Shapiro-Wilk distributional check** on inputs. 3) If non-Gaussian (p < 0.05), apply **rank-based inverse normal transformation (INT)**. 4) If Gaussian, apply Z-score normalization (subtract mean, divide by standard deviation). 5) Calculate absolute difference $| \text{CLIP} - \text{Human} |$. **Input**: Output of T021a. **Requirement**: Explicitly exclude samples where human rating is missing (NaN) before conversion (FR-003).
- [ ] T025a [US2] Implement deviation logic in `code/data/preprocess.py`: 1) Merge raw data, calculate deviation, exclude missing ratings. 2) Check for zero variance in target variable ($| \text{CLIP} - \text{Human} |$). 3) If variance is 0, **raise a `ValueError` with the exact message "Target not learnable: zero variance detected"** and halt execution (FR-010).
- [ ] T025b [S] [US2] Create `code/data/preprocess.py` script wrapper to call T025a, save `data/processed/deviation.csv` (validated against contract). **Dependency**: Requires T025a. **Implementation**: Execute script to generate output file.
- [ ] T025c [S] [US2] **Merge Features and Targets**: Implement `code/data/train.py` function to merge `data/processed/features_train.csv` and `data/processed/deviation.csv` into a single training matrix (X, y). **Requirement**: Ensure alignment by `caption_id`. **Output**: Save merged matrix to `data/processed/training_matrix.csv`. **Dependency**: Requires T018c and T025b.

### Tests for User Story 2

- [ ] T026 [P] [US2] Write unit test scaffolding for Z-score normalized deviation calculation in `code/tests/test_preprocess.py` (verify absolute difference on Z-score normalized inputs)
- [ ] T027 [P] [US2] Write unit test scaffolding for missing rating handling in `code/tests/test_preprocess.py` (verify row exclusion)
- [ ] T028 [P] [US2] Write integration test scaffolding for full deviation pipeline in `code/tests/test_preprocess.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Train CPU-Only Predictor and Rank Features (Priority: P3)

**Goal**: Train XGBoost on CPU to predict deviation and perform rigorous statistical significance testing.

**Independent Test**: Run training on a subset; verify model converges, correlation > 0.0, and outputs feature importance JSON.

### Implementation for User Story 3

- [ ] T029a [S] [US3] Implement `def train_xgboost(X: np.array, y: np.array) -> xgb.XGBRegressor` in `code/data/train.py` (CPU only, **k=5 fold CV with quantile-based stratification** for regression target, FR-004). **Requirement**: Explicitly set k=5 and stratification strategy for reproducibility (Constitution Principle I). **Input**: Output of T025c.
- [X] T029b [S] [US3] **Preliminary Validation**: Validate `train_xgboost` logic and produce `results/validation_report.json` (US3). **Note**: This task validates the training logic itself. Final Constitution Enforcement is handled by T045 in Phase 5.
- [ ] T030 [S] [US3] Implement `def calculate_permutation_importance(model, X, y) -> dict` in `code/data/train.py` (FR-005). **Requirement**: This must be a specific "permutation-based significance test" involving N=1,000 shuffles to generate a null distribution, followed by p-value calculation. **Requirement**: Use **Benjamini-Hochberg** correction to control FDR $\le 0.05$ (per FR-006). **Constraint**: If N=1,000 permutations cannot be completed (e.g., timeout > 6h), reduce N to the maximum feasible count (min(N, max_iterations)) and log the reduction to preserve CPU-tractability. Log seed, method (Benjamini-Hochberg), and iteration count.
- [ ] T031 [S] [US3] Implement `def run_label_permutation_test(model, X, y, n_iter=1000) -> dict` in `code/data/train.py`. **Requirement**: Enforce a fixed iteration count of N=1,000 by default with pinned seeds to ensure reproducibility (FR-006). **Do NOT** dynamically reduce n_iter. Calculate p-values and apply **Benjamini-Hochberg** (per FR-006). Log seed, method, and iteration count. **Constraint**: If N=1,000 cannot be reached, **raise an error**.
- [ ] T032 [S] [US3] Implement `def apply_benjamini_hochberg(p_values: list[float], alpha=0.05) -> list[float]` in `code/data/train.py` (FDR < 0.05, log seed, method, and iteration count, per FR-006). **Note**: Explicitly implements the Benjamini-Hochberg procedure as required by FR-006.
- [X] T032b [S] [US3] **Plan Correction**: Update `specs/001-llmxive-follow-up-extending-lens-rethink/plan.md` to replace the mention of "Benjamini-Yekutieli" with "Benjamini-Hochberg" in Phase 3, T030, to align with FR-006 and resolve the cross-document contradiction. **Requirement**: This task ensures the Plan reflects the Spec (Single Source of Truth). **Implementation**: Execute sed or python script to edit plan.md.
- [ ] T033 [S] [US3] Implement sensitivity analysis loop in `code/data/train.py`. **Requirements**: 1) Accept a **parameterized list of seeds** (read from `config.yaml` key `sensitivity_seeds`). **Constraint**: If the seed list is empty or undefined, **raise an error**. **Default**: Use seeds [42, 123, 456, 789, 101112]. 2) **For each seed**: a) Load cached data (no regeneration). b) Train model (T029a). c) Run significance tests (T030-T032). 3) Perform a **significance threshold sweep** (alpha) over {0.01, 0.05, 0.1} as required by FR-006. 4) Aggregate feature importance rankings across seeds and thresholds. 5) Calculate **mean rank and standard deviation** for each feature. 6) Output a JSON file `results/stability_metrics.json` with **distinct keys** for `alpha_sweep_results` (mean rank/std dev across alpha levels) and `seed_sweep_results` (mean rank/std dev across seeds) to satisfy both FR-006 and SC-005. **Dependency**: Requires T029a-T032. **Note**: This task explicitly triggers specific task variants per seed to measure model variance only (no data resampling). **Implementation**: Execute script to generate output file.
- [ ] T034a [US3] Create `code/data/train.py` script wrapper for single run: load features and targets, train model (T029a), run significance tests (T030-T032), save `results/significance.json`.
- [ ] T034b [S] [US3] Create `code/data/train.py` script wrapper for sensitivity analysis: call T033, aggregate results, generate the JSON table with mean rank and std dev across significance threshold sweeps, and save `results/stability_metrics.json`. **Dependency**: Requires T033. **Implementation**: Execute script to generate output file.
- [X] T035 [US3] Add logging for Pearson correlation, memory footprint, and wall-clock time (SC-001, SC-002, SC-003). Note: SC-004 logging handled by T032, SC-005 logging handled by T033.

### Tests for User Story 3

- [ ] T036 [P] [US3] Write unit test scaffolding for permutation importance calculation in `code/tests/test_train.py` (verify output JSON structure and p-value calculation).
- [ ] T037 [P] [US3] Write unit test scaffolding for Benjamini-Hochberg correction logic in `code/tests/test_train.py`
- [ ] T038 [P] [US3] Write integration test scaffolding for full training pipeline in `code/tests/test_train.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Versioning, Constitution Enforcement & Finalization

**Purpose**: Ensure reproducibility, enforce Constitution, and finalize artifacts.

- [X] T045 [S] [Constitution] **Final Constitution Gate**: Execute `pytest code/tests/test_constitution.py`. **Ordering**: Must run **after T014a (Features) and T029a (Training) are complete, and AFTER the completion of the entire US1 implementation block (including T018b) and the entire US3 implementation block (including T034a)**. This ensures only valid code results in processed artifacts and state updates. **Note**: Runs after completion of US1 and US3 implementation blocks (including T018b and T034a).
- [X] T039 [S] Generate SHA-256 hashes for all `data/processed/` files and update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with `artifact_hashes` map. **Dependency**: Requires T010 (raw data checksum), T025b (processed data), **T018b (US1 completion)**, **T034a (US3 completion)**, and **T045 (Constitution Gate)**.
- [X] T040 [S] Update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with `updated_at` timestamp. **Dependency**: Requires T039.
- [X] T041 [S] Archive `code/` and `results/` for final review: create `archive/PROJ-925-{timestamp}.tar.gz` containing `code/` and `results/`
- [X] T042 [S] Run `quickstart.md` validation
- [ ] T043 [P] [Constitution] Implement `code/tests/test_constitution.py`: Add static analysis to scan `code/features.py` for forbidden imports (`PIL`, `opencv`, `torch.cuda`, `tensorflow`). If found, raise `ImportError` with specific message.
- [ ] T044 [P] [Constitution] Implement `code/tests/test_constitution.py`: Add static analysis to scan `code/data/train.py` for CUDA usage. Explicitly verify `torch.set_num_threads(1)` and `torch.set_num_interop_threads(1)` are called at startup. Raise `ImportError` if `torch.cuda` is imported.
- [ ] T046 [US3] [FR-007] Implement `def compute_textual_covariates(caption: str) -> dict` in `code/features.py`. Logic: 1) Count **caption length (number of tokens)**. 2) Count **distinct noun phrases** (FR-007 definition). **Constraint**: Must use text-only methods (spaCy), no image data. **Requirement**: Explicitly include 'caption length (number of tokens)' and 'textual description complexity' (defined strictly as the count of distinct noun phrases, per FR-007).
- [X] T047 [S] [US3] [FR-007] Update `train_xgboost` (T029a) to accept and include `textual_covariates` (caption length and textual description complexity) as input features in the regression model to control for confounds. **Dependency**: Requires T046. **Implementation**: Modify model training function to accept and use covariates.

---

## Phase 6: Advanced Statistical Validation (FR-007, FR-008, FR-009)

**Purpose**: Implement specific advanced validation requirements for confounds, noise sensitivity, and construct validity.

- [X] T048 [S] [US3] [FR-008] Implement `def inject_noise_to_human_ratings(human_ratings: list[float], std_devs: list[float]) -> list[list[float]]` in `code/utils/stats.py`. Logic: Generate synthetic Gaussian noise for varying standard deviations. **Requirement**: Explicitly define `std_devs` as a sequence of non-negative values representing the noise injection range. **Implementation**: Write function to stats.py.
- [ ] T049 [S] [US3] [FR-008] Extend `code/data/train.py` to run a sensitivity analysis loop: for each noise level in T048, re-train the model and record feature importance rankings. Output `results/noise_sensitivity.json` containing mean rank and std dev across noise levels. **Requirement**: Explicitly iterate 'for each noise level' and output the specific JSON structure (mean rank/std dev). **Implementation**: Add loop to train.py.
- [X] T050a [S] [US1] [FR-009] **Acquire Expert Annotation Baseline**: Implement logic to acquire or generate `data/external/expert_annotations.json` if the semantic entropy baseline is unavailable. **Requirement**: 1) Attempt to load `data/external/semantic_entropy_baseline.json`. 2) If missing, attempt to load `data/external/expert_annotations.json`. 3) If **NEITHER** exists, **proceed without baseline comparison** and log a warning that construct validity check is incomplete due to missing external data (do NOT fail the pipeline). **Note**: This task belongs to US1 validation logic but is placed in Phase 6 to ensure the held-out split (T018c) is complete. **Dependency**: Requires T018c.
- [X] T050 [S] [US1] [FR-009] Implement `def validate_uncertainty_proxy(features_df: pd.DataFrame, held_out_subset: pd.DataFrame) -> float` in `code/utils/validation.py`. Logic: Compute correlation between `ln(perplexity)` and a **semantic entropy baseline** (default) OR **expert annotation** (from T050a) on a held-out subset of captions. **Requirement**: Use a **stratified [deferred] split** for the held-out subset (from T018c). If correlation coefficient is < 0.3, log a warning and flag construct validity risk in the final report. [UNRESOLVED-CLAIM: c_5e8727f0 — status=not_enough_info] **Dependency**: Requires T050a and T018c.
- [ ] T051 [S] [US1] [FR-009] Update `code/data/features.py` to call T050 on a held-out subset of the data. **Requirement**: Explicitly log a warning if correlation < 0.3 and flag construct validity risk in the final report.

---

## Phase 7: Error Handling & Contract Verification

**Purpose**: Enforce Single Source of Truth for error handling and schema consistency.

- [X] T004b [S] [Setup] **Error Message Factory**: (Merged into Phase 1 T004b). Verify that T009 and T021a use the unified `DataSchemaError` factory function in `code/utils/errors.py`. **Requirement**: Ensure the error message logic matches the schema definitions in `contracts/`.

---

## Phase 8: Integration & Final Validation (Revision Additions)

**Purpose**: Ensure end-to-end pipeline correctness and final validation of all requirements.

- [X] T052 [S] [US3] **End-to-End Pipeline Integration**: Create `code/run_pipeline.py` that orchestrates the full flow: Data Download (T009) -> Feature Extraction (T018b) -> Deviation Calculation (T025b) -> Training & Significance (T034a) -> Stability Analysis (T034b) -> Validation Reports. **Requirement**: This task must verify that all intermediate outputs exist and are valid before proceeding to the next stage. **Dependency**: Requires T018b, T025b, T034a, T034b. **Implementation**: Write orchestration script.
- [X] T053 [S] [US3] **Final Report Generation**: Generate a comprehensive `results/final_report.md` that includes: 1) Summary of feature extraction statistics, 2) Deviation score distribution, 3) Model performance metrics (Pearson correlation, R²), 4) Top 5 feature importances with p-values, 5) Sensitivity analysis results (stability metrics), 6) Construct validity assessment, 7) Noise sensitivity assessment. **Requirement**: Must aggregate results from T034b, T049, T051. **Dependency**: Requires T034b, T049, T051. **Implementation**: Write report generation script.
- [X] T054 [P] [US3] **Documentation Completion**: Update `docs/README.md` with full pipeline description, usage instructions, and expected outputs. **Requirement**: Must include examples of running each phase independently and the full pipeline. **Dependency**: Requires completion of all implementation tasks. **Implementation**: Update README.md.
- [ ] T055 [P] [Setup] **Reproduc8ility Verification**: Create a `reproducibility_checklist.md` that documents all seeds, hyperparameters, and data sources used to ensure the experiment can be exactly reproduced. **Requirement**: Must list all pinned seeds, model versions, and dataset versions. **Dependency**: Requires T008 (config) and all implementation tasks. **Implementation**: Write checklist file.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately. **Includes T004a (Contracts)**.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes Data Acquisition (T009-T010) to ensure data is ready before Feature Extraction**. **Includes T010 (Checksumming) which now runs after T009**.
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion.
 - **US1 (Feature Extraction)**: Depends on Phase 2 (Data) to have a valid stream. **Explicitly depends on T004a (Contracts) for T018a**.
 - **US2 (Deviation)**: Depends on Phase 2 (Data), T021a (CLIP), and T022 (Human Ratings).
 - **US3 (Training)**: Depends on US1 (Features) and US2 (Deviation) outputs being merged. **Explicitly depends on T029a-T032**.
- **Constitution Enforcement (Phase 5)**: Must pass before any training or feature extraction is finalized.
- **Advanced Validation (Phase 6)**: Depends on US1 (Features) and US3 (Training) core logic being complete.
- **Error Handling (Phase 7)**: Depends on Setup (Contracts) and Data Loading (T009) to verify error messages.
- **Finalization (Phase 5)**: Depends on all user stories and validation phases being complete.
- **Integration & Final Validation (Phase 8)**: Depends on all previous phases being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational + Data Acquisition.
- **User Story 2 (P2)**: Can start after Foundational + Data Acquisition.
- **User Story 3 (P3)**: Can start after US1 and US2 outputs are available.

### Within Each User Story

- Implementation tasks MUST precede their corresponding test scaffolding tasks
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (except T009, T010 which are [S])
- **US1 (T014a-T018) and US2 (T021a-T025b) can run in parallel** (T021a is now [S] as it depends on T009).
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together:
Task: "Implement compute_linguistic_uncertainty_proxy in code/features.py"
Task: "Implement compute_syntactic_depth in code/features.py"
Task: "Implement compute_noun_phrase_density in code/features.py"
Task: "Implement compute_token_diversity in code/features.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Write unit test scaffolding for compute_linguistic_uncertainty_proxy in code/tests/test_features.py"
Task: "Write unit test scaffolding for compute_syntactic_depth in code/tests/test_features.py"
Task: "Write integration test scaffolding for full feature extraction pipeline in code/tests/test_features.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Data)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently on a small sample
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Feature extraction working → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Deviation calculation working → Test independently → Deploy/Demo
4. Add User Story 3 → Model training and significance testing working → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Features)
 - Developer B: User Story 2 (Deviation)
 - Developer C: User Story 3 (Training)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = Sequential or require specific isolation (e.g., T009, T010, T045)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (write scaffolding first)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Data loader must NOT use synthetic fallbacks. If real data fetch fails, the script must crash.
- **CRITICAL**: All training and inference must be CPU-only (no CUDA).
- **CRITICAL**: Streaming is required for data loading to fit RAM constraints.
- **CRITICAL**: Z-score normalization MUST precede deviation calculation (FR-003) (with INT fallback).
- **CRITICAL**: `ln(perplexity)` MUST be used for Linguistic Uncertainty Proxy (FR-001).
- **CRITICAL**: Sensitivity analysis (SC-005) requires model seed iteration (T033).
- **CRITICAL**: T021a MUST validate pre-computed CLIP scores and raise DataSchemaError if missing.
- **CRITICAL**: T018a MUST validate against `specs/.../contracts/feature_vector.schema.yaml` using `pydantic` AND raw dataset schema.
- **CRITICAL**: T025a MUST raise "Target not learnable: zero variance detected" on zero variance.
- **CRITICAL**: T033 MUST perform a sensitivity sweep over significance thresholds (0.01, 0.05, 0.1).
- **CRITICAL**: T051 MUST log a warning and flag construct validity risk in the final report if correlation < 0.3.
- **CRITICAL**: T014a MUST enforce 5-second timeout per caption (exclude sample, do NOT flag) AND separate BERT failure logic.
- **CRITICAL**: T022 MUST implement Shapiro-Wilk check and INT fallback.
- **CRITICAL**: T030/T032 MUST use **Benjamini-Hochberg** correction (per FR-006, overriding Plan.md).
- **CRITICAL**: T046 MUST calculate textual description complexity (count of distinct noun phrases ONLY).
- **CRITICAL**: T050 MUST implement semantic entropy baseline path OR expert annotation (T050a).
- **CRITICAL**: T009 MUST check for dataset availability and fail loudly.
- **CRITICAL**: T004b MUST enforce unified error message factory.
- **CRITICAL**: T002 MUST list `torch` as required.
- **CRITICAL**: T014a MUST explicitly handle FR-012 (BERT failure -> exclude) distinct from timeout.
- **CRITICAL**: T023 (conversion logic) is REMOVED; T021a/T022 assume 'human_rating' exists.
- **CRITICAL**: T013b, T013c (data regeneration) are REMOVED; T033 only varies model seeds.
- **CRITICAL**: T010 MUST run AFTER T009.
- **CRITICAL**: T045 is the Final Constitution Gate, running BEFORE T039/T040.
- **CRITICAL**: T029a MUST use k=5 fold CV with quantile-based stratification.
- **CRITICAL**: T050a MUST acquire expert annotation baseline if semantic entropy is unavailable.
- **CRITICAL**: T032b MUST correct Plan.md to match Spec (FR-006) regarding Benjamini-Hochberg.
- **CRITICAL**: T033 MUST fail loudly if seed list is empty.
- **CRITICAL**: T030/T031 MUST fail loudly if N=1,000 permutations cannot be reached.
- **CRITICAL**: T022 MUST fail loudly if 'human_rating' is missing.
- **CRITICAL**: T014a MUST atomically exclude rows on BERT failure.
- **CRITICAL**: T050a MUST fail loudly if neither baseline source exists.
- **CRITICAL**: T018c MUST create the held-out subset for T050.
- **CRITICAL**: T025c MUST merge features and targets before training.
- **CRITICAL**: T052 MUST orchestrate the full pipeline end-to-end.
- **CRITICAL**: T053 MUST generate the final comprehensive report.
- **CRITICAL**: T054 MUST complete all documentation.
- **CRITICAL**: T055 MUST verify reproducibility.
