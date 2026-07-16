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

**Purpose**: Project initialization, basic structure, and **Contract Creation** (moved to Phase 1 to resolve dependency cycles).

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/`) by executing: `mkdir -p data/raw data/processed code code/tests code/utils code/models docs`. **Note**: `data/` and `code/` are **sibling directories** at the project root, NOT nested. `data/` holds raw/processed data; `code/` holds scripts.
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (xgboost, scikit-learn, transformers, spacy, datasets, pandas, numpy, torch, pydantic, jsonschema). **Note**: `torch` and `transformers` are required for CLIP and BERT inference.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 [P] Create data schema contracts in `specs/001-llmxive-follow-up-extending-lens-rethink/contracts/` (dataset, feature_vector, deviation_target, significance_results). **Note**: Moved to Phase 1 to ensure contracts exist before validation tasks (T018a).
- [X] T005 [P] Setup `code/__init__.py` and directory structure (`data/`, `code/`, `tests/`) - create empty `__init__.py` files and ensure directories `data/raw`, `data/processed`, `code/data`, `code/tests`, `code/utils`, `code/models` exist as **siblings** at the project root (not nested).
- [X] T006 [P] Implement basic logging infrastructure in `code/utils/logging.py`
- [X] T007 [P] Create base data model entities: `code/models/caption_record.py` (class `CaptionRecord`) and `code/models/linguistic_feature_vector.py` (class `LinguisticFeatureVector`)
- [X] T008 [P] Setup environment configuration management (seed pinning, path constants) in `code/config.py`
- [X] T009 [P] Implement `code/data/download.py` to stream `pick-a-pic` dataset via `datasets.load_dataset(..., streaming=True)` (Phase 0 of Plan)
- [X] T010 [P] Implement checksumming logic in `code/data/download.py` and update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with raw data hashes
- [X] T011 [P] Add validation in `code/data/download.py` to exclude rows with empty captions or missing images
- [X] T012 [P] Ensure data loader FAILS LOUDLY on fetch error (no synthetic fallback) - remove any `try/except` blocks that generate synthetic data
- [X] T013 [P] Implement stratified random sampling logic in `code/data/download.py` (strata columns, sample size) to be applied before feature extraction (Plan Assumption)
- [X] T013b [S] Implement deterministic data/feature regeneration wrapper in `code/data/download.py` that accepts a `seed` parameter to ensure reproducible data streams and feature vectors for sensitivity analysis (SC-005). **Note**: This task must be run sequentially or with distinct output paths per seed (e.g., `data/processed/seed_{seed}/`) to avoid race conditions. It ensures that for every seed used in T033, the data loading and feature extraction can be deterministically re-run.
- [X] T013c [S] Implement logic to vary the stratified sample composition (different random seeds for sampling) in `code/data/download.py` to assess stability against *data* variance, distinct from model variance. This addresses the need to test sample stability as implied by SC-005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Data Acquisition to ensure Producer-before-Consumer.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T014 [P] [US1] Implement `def compute_semantic_entropy(caption: str) -> float` in `code/features.py` using `bert-base-uncased` on CPU. Explicitly apply natural logarithm to perplexity (`ln(perplexity)`) per FR-001. Handle CPU-only errors explicitly.
- [ ] T015 [P] [US1] Implement `def compute_syntactic_depth(caption: str) -> int` in `code/features.py` using `spaCy` (FR-002). Assign default depth=0 for short captions.
- [ ] T016a [P] [US1] Implement `def compute_noun_phrase_density(caption: str) -> float` in `code/features.py`.
- [ ] T016b [P] [US1] Implement `def compute_token_diversity(caption: str) -> float` in `code/features.py`.
- [ ] T017 [US1] Implement `def extract_features_batch(captions: list[str]) -> pd.DataFrame` in `code/features.py` with edge case handling (short captions -> depth=0, BERT failure -> log & exclude)
- [ ] T018a [US1] Implement validation logic in `code/utils/validation.py`: 1) Load `specs/001-llmxive-follow-up-extending-lens-rethink/contracts/feature_vector.schema.yaml`, 2) Validate DataFrame against schema using `pydantic`, 3) Raise `ValueError` on mismatch. **Dependency**: Requires T004 (Contracts) - **T004 is in Phase 1**.
- [ ] T018b [US1] Create `code/data/features.py` script wrapper to **consume processed raw data stream from T009**, call extraction functions, **call T018a for schema validation**, and save to `data/processed/features.csv`. **Dependency**: Requires T018a.

### Tests for User Story 1

- [ ] T019 [P] [US1] Write unit test scaffolding for `compute_semantic_entropy` in `code/tests/test_features.py` (verify `ln(perplexity)` calculation)
- [ ] T020 [P] [US1] Write unit test scaffolding for `compute_syntactic_depth` in `code/tests/test_features.py` (verify spaCy dependency tree depth)
- [ ] T021 [P] [US1] Write integration test scaffolding for full feature extraction pipeline in `code/tests/test_features.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Calculate Alignment Deviation Score (Priority: P2)

**Goal**: Calculate the target variable $Y = | \text{CLIP\_Score} - \text{Human\_Rating} |$ from human preference data.

**Independent Test**: Feed a dataset with known CLIP/Human values; verify deviation calculation is correct and rows with missing human ratings are excluded.

### Implementation for User Story 2

- [ ] T021a [S] [US2] Implement `def compute_clip_scores(caption_image_pairs: list[dict]) -> list[float]` in `code/data/preprocess.py`. **Strategy**: 1) Check for existing `data/raw/clip_scores_cache.parquet`. 2) If missing, run inference on `openai/clip-vit-base-patch32` on CPU in batches, save to `data/raw/clip_scores_cache.parquet`. 3) If present, load from cache. **Note**: This task is [S] (Sequential) to avoid CPU contention with feature extraction (T014-T016b) and ensure cache is ready. **Clarification**: The inference step is a **one-time setup** to generate the "pre-computed" scores required by FR-003, ensuring the deviation calculation (T022) uses a static, cached artifact rather than re-running inference during the pipeline.
- [ ] T022 [P] [US2] Implement `def normalize_and_calculate_deviation(clip_scores: list[float], human_ratings: list[float]) -> list[float]` in `code/data/preprocess.py`. **Atomic operation**: 1) Normalize CLIP and Human ratings to [0,1], 2) Calculate absolute difference $| \text{CLIP} - \text{Human} |$ per FR-003. Ensure normalization precedes subtraction. **Input**: Output of T021a and T023.
- [ ] T023 [US2] Implement `process_human_ratings` in `code/data/preprocess.py` to explicitly convert 'winner/loser' pairs from Pick-a-Pic to normalized human ratings (0.0-1.0). Logic: winner=1.0, loser=0.0; for multiple choices, interpolate based on rank. Ensure this step produces the `human_ratings` input for T022.
- [ ] T025a [US2] Implement deviation logic in `code/data/preprocess.py`: 1) Merge raw data, calculate deviation, exclude missing ratings. 2) Check for zero variance in target variable ($| \text{CLIP} - \text{Human} |$). 3) If variance is 0, **raise a `ValueError` with the exact message "Target not learnable"** and halt execution.
- [ ] T025b [US2] Create `code/data/preprocess.py` script wrapper to call T025a, save `data/processed/deviation.csv` (validated against contract). **Dependency**: Requires T025a.

### Tests for User Story 2

- [ ] T026 [P] [US2] Write unit test scaffolding for normalized deviation calculation in `code/tests/test_preprocess.py` (verify absolute difference on normalized inputs)
- [ ] T027 [P] [US2] Write unit test scaffolding for missing rating handling in `code/tests/test_preprocess.py` (verify row exclusion)
- [ ] T028 [P] [US2] Write unit test for zero variance detection in `code/tests/test_preprocess.py` (verify "Target not learnable" error is raised)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Train CPU-Only Predictor and Rank Features (Priority: P3)

**Goal**: Train XGBoost on CPU to predict deviation and perform rigorous statistical significance testing.

**Independent Test**: Run training on a subset; verify model converges, correlation > 0.0, and outputs feature importance JSON.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `def train_xgboost(X: np.array, y: np.array) -> xgb.XGBRegressor` in `code/data/train.py` (CPU only, k-fold CV, FR-004)
- [ ] T030 [P] [US3] Implement `def calculate_permutation_importance(model, X, y) -> dict` in `code/data/train.py` (FR-005)
- [ ] T031 [US3] Implement `def run_label_permutation_test(model, X, y, n_iter=1000) -> dict` in `code/data/train.py`. **Optimization**: 1) Run a pilot (e.g., 50 iterations) to estimate time per iteration. 2) If [deferred] iterations exceed the time budget (e.g., > 30 mins per seed), dynamically reduce `n_iter` (e.g., to 200) and log a warning. 3) Calculate p-values and apply Benjamini-Hochberg. 4) Log seed and method. (FR-006, SC-004). **Note**: This optimization ensures FR-006's [deferred] iteration requirement is met where feasible, but falls back gracefully to meet SC-003 time limits.
- [ ] T032 [US3] Implement `def apply_benjamini_hochberg(p_values: list[float], alpha=0.05) -> list[float]` in `code/data/train.py` (FDR < 0.05, log seed and method, FR-006)
- [ ] T033 [US3] Implement sensitivity analysis loop in `code/data/train.py`. **Requirements**: 1) Accept a **parameterized list of seeds** (read from config). 2) **For each seed**: a) Call the `generate_data_for_seed(seed)` function implemented in `code/data/download.py` (by T013b) to **regenerate the entire feature/deviation dataset** with that seed. b) Save per-seed artifacts to `data/processed/seed_{seed}/features.csv` and `deviation.csv`. c) Load cached data. d) Train model (T029). e) Run significance tests (T030-T032). 3) Aggregate feature importance rankings across seeds. 4) Calculate **mean rank and standard deviation** for each feature. 5) Output a JSON file `results/stability_metrics.json` with the exact structure: `{"feature": {"mean_rank": float, "std_dev": float}}`. **Dependency**: Requires T013b, T013c (dynamic invocation), T029-T032. **Note**: This task explicitly triggers T013b/T013c per seed to measure data variance, not just model variance.
- [ ] T034a [US3] Create `code/data/train.py` script wrapper for single run: load features and targets, train model (T029), run significance tests (T030-T032), save `results/significance.json`.
- [ ] T034b [US3] Create `code/data/train.py` script wrapper for sensitivity analysis: call T033, aggregate results, save `results/stability_metrics.json`.
- [ ] T035 [US3] Add logging for Pearson correlation, memory footprint, and wall-clock time (SC-001, SC-002, SC-003). Note: SC-004 logging handled by T032, SC-005 logging handled by T033.

### Tests for User Story 3

- [ ] T036 [P] [US3] Write unit test scaffolding for permutation importance calculation in `code/tests/test_train.py`
- [ ] T037 [P] [US3] Write unit test scaffolding for Benjamini-Hochberg correction logic in `code/tests/test_train.py`
- [ ] T038 [P] [US3] Write integration test scaffolding for full training pipeline in `code/tests/test_train.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Versioning & Artifact Finalization

**Purpose**: Ensure reproducibility and state tracking.

- [ ] T039 Generate SHA-256 hashes for all `data/processed/` files and update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with `artifact_hashes` map
- [ ] T040 Update `state/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink.yaml` with `updated_at` timestamp
- [ ] T041 Archive `code/` and `results/` for final review: create `archive/PROJ-925-{timestamp}.tar.gz` containing `code/` and `results/`
- [ ] T042 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately. **Includes T004 (Contracts)**.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes Data Acquisition (T009-T013c) to ensure data is ready before Feature Extraction.**
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion.
 - **US1 (Feature Extraction)**: Depends on Phase 2 (Data) to have a valid stream. **Explicitly depends on T004 (Contracts) for T018a.**
 - **US2 (Deviation)**: Depends on Phase 2 (Data), T021a (CLIP), and T023 (Human Ratings).
 - **US3 (Training)**: Depends on US1 (Features) and US2 (Deviation) outputs being merged. **Explicitly depends on T013b/T013c (dynamic invocation per seed)**.
- **Finalization (Phase 5)**: Depends on all user stories being complete.

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
- All Foundational tasks marked [P] can run in parallel (except T013b, T013c which are [S])
- **US1 (T014-T018) and US2 (T021a-T025b) can run in parallel ONLY IF CPU resources allow.** T021a is marked [S] due to heavy CPU load; it should be serialized with other CPU-heavy tasks (like T014-T017) if the runner has limited cores.
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together:
Task: "Implement compute_semantic_entropy in code/features.py"
Task: "Implement compute_syntactic_depth in code/features.py"
Task: "Implement compute_noun_phrase_density in code/features.py"
Task: "Implement compute_token_diversity in code/features.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Write unit test scaffolding for compute_semantic_entropy in code/tests/test_features.py"
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
- [S] tasks = Sequential or require specific isolation (e.g., T013b, T013c, T021a)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (write scaffolding first)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Data loader must NOT use synthetic fallbacks. If real data fetch fails, the script must crash.
- **CRITICAL**: All training and inference must be CPU-only (no CUDA).
- **CRITICAL**: Streaming is required for data loading to fit RAM constraints.
- **CRITICAL**: Normalization MUST precede deviation calculation (FR-003).
- **CRITICAL**: `ln(perplexity)` MUST be used for semantic entropy (FR-001).
- **CRITICAL**: Stratified sampling MUST be applied before feature extraction (Plan Assumption).
- **CRITICAL**: Sensitivity analysis (SC-005) requires deterministic data regeneration per seed (T013b + T013c + T033).
- **CRITICAL**: T021a MUST compute CLIP scores (with caching) and T022 MUST consume them.
- **CRITICAL**: T018a MUST validate against `specs/.../contracts/feature_vector.schema.yaml` using `pydantic`.
- **CRITICAL**: T025a MUST raise "Target not learnable" on zero variance.
- **CRITICAL**: T033 MUST regenerate data per seed via `code/data/download.py` and cache to `data/processed/seed_{seed}/` before training.
- **CRITICAL**: T021a is [S] (Sequential) to avoid CPU contention.
- **CRITICAL**: T004 (Contracts) MUST be completed before T018a (Validation).
- **CRITICAL**: T033 MUST trigger T013b/T013c dynamically per seed to measure data variance.