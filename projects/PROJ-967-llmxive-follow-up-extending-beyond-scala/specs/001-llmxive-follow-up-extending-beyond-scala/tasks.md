# Tasks: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

**Input**: Design documents from `/specs/001-llmxive-entanglement-analysis/`
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

**Purpose**: Project initialization, contract definition, and artifact scaffolding

- [ ] T001a [P] Create project directories: Create directories `data/raw`, `data/processed`, `code`, `tests`, `results` inside `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` relative to repository root
- [X] T001b [P] Create empty project files: Create empty files `code/requirements.txt`, `.gitignore`, `pytest.ini` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/`
- [X] T001c [P] Write dependencies: Write `code/requirements.txt` with pinned versions of pandas, numpy, scikit-learn, scipy, pyyaml, pytest, ruff, black
- [ ] T001d [P] Create schema contracts: Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` defining the exact structure for input data and output features
- [ ] T001e [P] Initialize output artifacts: Create empty `data/processed/features.json` (with `[]` or `{}`) and `results/results.json` (with `{}`) to prevent file-not-found errors in downstream tasks
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw`, `data/processed`) and `.gitignore` for large files
- [X] T005 [P] Create `code/ingest.py` skeleton with argument parsing and logging setup
- [X] T006 [P] Create `code/features.py` skeleton with statistical helper functions
- [X] T007 [P] Create `code/train.py` skeleton with scikit-learn model configuration
- [X] T008 [P] Create `code/evaluate.py` skeleton for metrics calculation
- [X] T009 Setup `tests/` directory structure and `pytest.ini`
- [ ] T037 [P] [US1] Download Z-Reward dataset: Use `datasets.load_dataset('zreward/evaluation', split='train')` to fetch the dataset; verify file integrity via SHA256 checksum against `data/.checksums`; save to `data/raw/zreward_dataset.csv`; **FAIL LOUDLY** if checksum mismatch or fetch fails (trigger T039)
- [ ] T038 Validate dataset schema: Validate the presence of all rubric dimensions (Alignment, Realism, Aesthetics, Plausibility) and human annotation columns in `data/raw/zreward_dataset.csv` (if real) OR `data/raw/zreward_dataset_synthetic.csv` (if synthetic); raise error if schema mismatch detected; **DEPENDS: T037 (Download) must complete first (real) OR T039 (Synthetic) must complete first (fallback)**
- [ ] T039 [US1] Generate synthetic fallback: If T037 fails, generate synthetic data in `data/raw/zreward_dataset_synthetic.csv` using T039; log "FALLBACK MODE ACTIVATED" to `logs/ingest.log`; **PREREQUISITE: T001d (Schema) must be complete**; **NOT [P]**: Must wait for T001d
- [ ] T040 [P] [US1] Implement streaming loader in `code/ingest.py` for Z-Reward: Use `datasets.load_dataset('zreward/evaluation', split='train', streaming=True)`; **CONDITIONAL**: Only implement if estimated dataset size > 5GB; accumulate sample counts and statistics without loading the entire dataset into memory; explicitly log the chunk size and total rows processed to `logs/ingest.log`; **DEPENDS: T012 logic defined**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Ground-Truth Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest Z-Reward dataset, align teacher/student outputs with human annotations, and handle missing data gracefully.

**Independent Test**: A script loads the dataset, verifies the presence of all four rubric dimensions, flags missing data, and outputs a summary without crashing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for data loading and schema validation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`
- [X] T011 [P] [US1] Integration test for missing data handling and exclusion logic in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement Z-Reward dataset ingestion in `code/ingest.py` (load prompts, images, teacher logits, student scores, human annotations)
- [X] T013 [US1] Implement alignment logic in `code/ingest.py`: match teacher distributions, student scalars, and human annotations by sample ID
- [X] T014 [US1] Implement "primary quality dimension" identification logic in `code/ingest.py` based on prompt metadata (independent of scores)
- [X] T015 [US1] Implement chunked loading or sampling logic in `code/ingest.py` to ensure RAM usage stays < 7GB on free-tier runners
- [X] T016 [US1] Add summary output in `code/ingest.py`: print sample counts, missing data flags, dimension coverage stats (fidelity loss calculation moved to T024)
- [X] T039 [P] [US1] Implement synthetic data generator: Generate small, fake numpy arrays to test feature calculation logic; **MUST strictly adhere to the schema defined in `contracts/dataset.schema.yaml`** (4 rubric dimensions, human annotation format); **PREREQUISITE**: Verify `contracts/dataset.schema.yaml` exists (created in T001d)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entanglement Quantification and Feature Engineering (Priority: P2)

**Goal**: Calculate statistical descriptors (variance, entropy, skewness, kurtosis) per sample, and a per-sample dominant eigenvalue via local sliding window.

**Independent Test**: A script processes a fixed subset of teacher distributions and outputs a JSON record with calculated features, handling zero-variance cases gracefully.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for variance, entropy, skewness, kurtosis calculations in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`
- [X] T019 [P] [US2] Unit test for zero-variance edge case handling in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement variance and range calculation for 4 dimensions in `code/features.py`
- [X] T021 [US2] Implement entropy, skewness, and kurtosis calculation for teacher distributions in `code/features.py`
- [ ] T022 [US2] Implement per-sample dominant eigenvalue via local sliding window: For each sample, select K=20 nearest neighbors (based on Euclidean distance in 4D score space); compute the 4x4 covariance matrix of this local window; extract the dominant eigenvalue as the "local entanglement score" for that sample; **VALIDATION**: Ensure output is finite and non-NaN for all samples; **NOTE**: This replaces any global-only logic; requires storing a window of samples to compute local covariance.
- [X] T023 [US2] Implement zero-variance handling in `code/features.py`: set entropy to 0 and variance to 0 without crashing
- [X] T024 [US2] Implement "dimensional fidelity loss" calculation in `code/features.py`: Compute MAE between student scalar output and human-annotated score for the primary dimension (selected via metadata); flag and exclude samples with missing human annotations for the target dimension
- [ ] T025 [US2] Integrate Ingestion and Feature Engineering: Read aligned data from `code/ingest.py` (or intermediate state), compute all per-sample stats (T020-T021), compute the local eigenvalue (T022) using the K-nearest neighbors approach, calculate fidelity loss (T024), and write the complete feature set to `data/processed/features.json`; **DEPENDS: T012, T020-T024**; **VALIDATION**: Ensure output JSON matches `contracts/output.schema.yaml` and contains no null values for required keys (`sample_id`, `variance`, `entropy`, `local_eigenvalue`, `fidelity_loss`); **REPLACES T025a/T025b split to ensure logical continuity**.
- [ ] T041 [US2] Implement chunked feature accumulation in `code/features.py`: Modify the feature engineering loop to process data in chunks (streamed from `code/ingest.py`); for each chunk, compute local nearest neighbors *within the chunk* (approximation) or buffer a sliding window of samples to approximate the local eigenvalue; write partial results to `data/processed/features_chunk_{index}.json` (chunk_size=1000); **MERGE**: Concatenate all partial files, deduplicate by `sample_id`, and write to `data/processed/features.json`; **DEPENDS: T012 logic defined**; **NOTE**: True streaming of local eigenvalues is mathematically complex; this task implements a chunked approximation that balances memory and accuracy.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train a CPU-based Random Forest regressor to predict fidelity loss using entanglement features, with k-fold cross-validation and permutation test validation..

**Independent Test**: A script trains the model on a stratified split, runs 5-fold CV, and outputs R², MAE, and p-value (from permutation test) without using GPU.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US3] Unit test for Random Forest training and 5-fold CV execution in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_train.py`
- [X] T026 [P] [US3] Integration test for permutation test p-value calculation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_evaluate.py`

### Implementation for User Story 3

- [ ] T027a [US3] Implement Random Forest training setup in `code/train.py`: Read features from `data/processed/features.json`; configure train/test split with `test_size=0.2` and `random_state=42`; ensure CPU-only execution (`n_jobs=2`); **DEPENDS: T025**
- [ ] T027b [US3] Implement Random Forest training execution in `code/train.py`: Train model with `n_estimators=100`, `max_depth=None`, `random_state=42`; **DEPENDS: T027a**; **DO NOT SAVE YET**
- [ ] T027c [US3] Save model artifact: Serialize trained model from T027b to `results/model.pkl`; **DEPENDS: T027b**
- [ ] T028 [US3] Implement 5-fold cross-validation logic in `code/train.py` with stratified splitting
- [ ] T029 [US3] Implement evaluation script in `code/evaluate.py`: calculate mean R², std dev, MAE, and permutation test p-value
- [ ] T030a [US3] Implement permutation test logic: Compare model MAE against a null baseline (predicting mean loss) using a **permutation test** (n_permutations=1000, alpha=0.05, random_state=42) to verify statistically significant improvement (SC-002); output R², MAE, and permutation p-value
- [ ] T030b [US3] Write results: Serialize R², MAE, and p-value to `results/results.json`
- [ ] T031 [US3] Integrate training and evaluation: Read features from `data/processed/features.json`, train model, run CV, run permutation test, and write final metrics to `results/results.json`; **DEPENDS: T027a, T028, T030a**
- [ ] T042 [US3] Implement memory-efficient model training in `code/train.py`: Ensure the Random Forest training loads only the necessary feature subset from `data/processed/features.json` (e.g., using `pandas.read_json(..., lines=True)` with chunking); **MONITOR**: Use `tracemalloc` to monitor memory; trigger chunking if memory usage > 6GB; log memory usage peaks during training; **DEPENDS: T025**

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/quickstart.md`
- [ ] T033 Code cleanup and refactoring of `code/` directory
- [ ] T034 Profile and optimize feature engineering loop for CPU efficiency
- [~] T035 [P] Additional unit tests for edge cases in `tests/unit/`
- [~] T036 Run quickstart.md validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes Data Acquisition (T037, T038)** which must complete before US1 implementation (T012).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Acquisition (Phase 7 - Merged into Phase 2)**: Must complete before US1 implementation (T012) can successfully run on real data
- **T025 (Feature Integration)**: Must complete before T027a (Training)
- **T037 (Download)**: Must complete before T038 (Validation) (real path) OR T039 (Synthetic) must complete before T038 (fallback path)
- **T001d (Schema)**: Must complete before T039 (Synthetic Generator)
- **T012 (Ingestion)**: Must complete before T025 (Compute Features)
- **T027a (Config)**: Must complete before T027b (Train)
- **T027b (Train)**: Must complete before T027c (Save Model)
- **T030a (Permutation)**: Must complete before T030b (Write Results)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data alignment
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (target calculation) and US2 (features)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading before feature engineering
- Feature engineering before model training
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T038 and T039 which have strict dependencies**
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Data acquisition (T037) runs in parallel with Setup and Foundational tasks but must finish before T012

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for data loading and schema validation in tests/test_ingest.py"
Task: "Integration test for missing data handling in tests/test_ingest.py"

# Launch implementation tasks together:
Task: "Implement Z-Reward dataset ingestion in code/ingest.py"
Task: "Implement alignment logic in code/ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Data Acquisition)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with real data
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
 - Developer A: User Story 1 (Data ingestion)
 - Developer B: User Story 2 (Feature engineering)
 - Developer C: User Story 3 (Model training)
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
- **CRITICAL**: All data loading tasks (T012, T037, T040) must use real, reachable URLs (Z-Reward official repo) or package-based fetchers. No fake data or simulated datasets for final analysis.
- **CRITICAL**: All model training tasks must be CPU-only (no CUDA, no 8-bit quantization, no large LLMs). Use small models and sampled datasets if necessary.
- **CRITICAL**: Entanglement features (T022) MUST be computed using a **local sliding window** to derive a per-sample dominant eigenvalue; global-only logic is invalid.
- **CRITICAL**: Target variable (T024) MUST be calculated in `code/features.py` using metadata-based dimension selection, independent of model scores.
- **CRITICAL**: Data Acquisition (T037, T038) must complete before US1 implementation (T012) to ensure the ingestion script has real data to process.
- **CRITICAL**: Synthetic data generator (T039) MUST strictly adhere to `contracts/dataset.schema.yaml` to ensure test validity.
- **CRITICAL**: Streaming tasks (T040, T041, T042) are required to handle datasets exceeding the 7GB RAM limit on the free-tier runner; do not attempt to load the full dataset into memory.
- **CRITICAL**: T037 must include checksum verification; T039 is the fallback if T037 fails.
- **CRITICAL**: T040 is conditional on dataset size > 5GB to avoid over-engineering.
- **CRITICAL**: T001e initializes output files to prevent "file not found" errors.
- **CRITICAL**: T025 is the unified task for feature integration, replacing the previous split T025a/T025b to ensure logical continuity and address the "FAILED" markers.
- **CRITICAL**: T027b and T027c are split to separate training from serialization.
- **CRITICAL**: T038 and T039 are not [P] due to strict dependencies on T037 and T001d respectively.
- **CRITICAL**: T040 is not [P] due to dependency on T012 logic.
- **CRITICAL**: T041 implements a chunked approximation for local eigenvalues, acknowledging the impossibility of simple online streaming for local topology.