# Tasks: llmXive follow-up: extending "FastContext: Training Efficient Repository Explorer for Coding Agents"

**Input**: Design documents from `/specs/001-llmxive-fastcontext-lite/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/` by executing: `mkdir -p data/raw data/processed data/results code tests/unit tests/integration specs/contracts state` <!-- FAILED: unspecified -->
- [X] T001b Initialize `state/` directory structure and create empty `state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml` file to ensure T004 has a valid target path.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `requirements.txt` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/requirements.txt` by executing: `cat > requirements.txt << 'EOF'
scikit-learn==1.4.0
pandas==2.1.0
networkx==3.2.1
transformers==4.40.0
datasets==2.18.0
pytest==8.1.0
torch==2.2.0
EOF`
- [X] T003a [P] Create `.ruff.toml` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with rules: `["E", "F", "I", "W"]` and `target-version = "py311"` (FR-001)
- [X] T003b [P] Create `pyproject.toml` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with black configuration: `line-length = 88 `, `target-version = ["py311"]` (FR-001)
- [X] T004 Implement `code/versioning.py` to compute content hashes for `data/` and `code/` artifacts and update `state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml` (Requires T001b completion) with a JSON schema containing `artifact_hashes` (map of filename: sha256 string) and `updated_at` (ISO 8601 timestamp string) (Constitution Principle V)
- [X] T005 [P] Create base data models and schema definitions in `code/__init__.py` and `contracts/`
- [X] T006 [P] Setup environment configuration management for dataset paths and model IDs in `code/config.py`
- [ ] T007 Implement data download utility in `code/data_loader.py` to fetch `princeton-nlp/SWE-bench_Lite` via `datasets` library, specifically version tag: v.0, split: test, and verify checksums (FR-001)
- [ ] T007b Implement `code/annotation_extractor.py` to extract and map 'ground-truth relevant files' from SWE-bench task annotations to a CSV format (`data/raw/ground_truth_annotations.csv`) containing `repo_id`, `issue_id`, and `ground_truth_file_paths` for validation (FR-001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Structural Regularity Scoring and Dataset Split (Priority: P1) 🎯 MVP

**Goal**: Implement static analysis to score repositories and split them into "Regular" and "Irregular" sets.

**Independent Test**: Run the static analysis script on a small sample of known repositories and verify the output CSV contains a "regularity_score" column and the split logic correctly assigns the top half to the "Regular" set and the bottom half to the "Irregular" set.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T008 [P] [US1] Unit test `tests/unit/test_static_analysis.py::test_directory_naming_returns_score_1_0_for_standard_layout` using fixture `sample_repo_standard` (contains `src/`, `tests/`, `docs/`) to assert `calculate_dir_score` returns a normalized value indicating complete alignment. <!-- FAILED: unspecified -->
- [ ] T009 [P] [US1] Unit test `tests/unit/test_static_analysis.py::test_import_pattern_analysis_returns_score_0_5_for_mixed_imports` using fixture `sample_repo_mixed_imports` (contains `import os`, `from. import x`) to assert `calculate_import_score` returns a moderate value <!-- FAILED: unspecified -->
- [X] T010 [P] [US1] Unit test `tests/unit/test_stratification.py::test_stratification_splits_50_50_by_regular_score` using fixture `sample_scores_csv` (n=10, scores ranging from low to high) to assert `split_repos` returns two lists of a fixed size

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/static_analysis.py` to calculate `regularity_score` using the formula: `* dir_score + w1 * test_score + w2 * import_score, where w1 and w2 are adjustable weights determined during the optimization phase.`.
 - `dir_score`: Binary check for presence of `src/`, `tests/`, `docs/` (A binary indicator where 1 if all present, 0 if none, linear interpolation for partial).
 - `test_score`: Binary check for `tests/` directory presence (The presence of the feature, coded as a binary indicator, is evaluated using the method described in [Citation]. This approach aligns with the research question regarding the occurrence of the phenomenon, as outlined in [Citation].).
 - `import_score`: Ratio of absolute imports (`import pkg`) to total imports (Maximum if all absolute, 0.0 if all relative).
 (FR-001)
- [X] T012 [US1] Implement `code/static_analysis.py` to handle edge cases (missing test files, extreme irregularity) with fallback logic returning a default score (baseline parameter for initial evaluation).
- [X] T013 [US1] Implement `code/stratification.py` to sort repositories by score and split into "Regular" and "Irregular" sets of approximately equal size
- [ ] T014 [US1] Implement data export logic to write `data/processed/regularity_scores.csv` with repo IDs and scores

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - FastContext-Lite Execution and Metric Collection (Priority: P2)

**Goal**: Execute the FastContext-Lite pipeline and the original FastContext (4B) baseline to collect metrics.

**Independent Test**: Run the FastContext-Lite pipeline on a single "Regular" repository and verify that it outputs a JSON log containing `context_precision`, `total_tokens`, and `exploration_latency_ms` without requiring a GPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Integration test `tests/integration/test_pipeline.py::test_fastcontext_lite_runs_on_regular_repo` using fixture `sample_regular_repo` to assert `run_lite_pipeline` completes in < 5s and returns valid JSON log <!-- FAILED: unspecified -->
- [X] T017 [P] [US2] Integration test `tests/integration/test_pipeline.py::test_original_fastcontext_4b_runs_on_cpu` using fixture `sample_regular_repo` to assert `run_baseline_4b` completes on CPU (no CUDA) with explicit OOM/timeout handling (max limited duration, 7GB RAM) and returns valid JSON log (FR-004)
- [X] T018 [P] [US2] Unit test `tests/unit/test_metrics_logger.py::test_log_schema_validates_required_fields` using mock data to assert `validate_log` passes for schema containing `context_precision`, `total_tokens`, `wall_clock_latency`

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/fastcontext_lite.py` with deterministic parser: "Parse issue description to extract keywords, search file tree for matching paths in tests/, src/, and docs/, and return top-K snippets based on TF-IDF similarity to the issue keywords." (Input: JSON `{"file_path": str, "content": str}`, output: `{"retrieved_snippets": list, "token_count": int}`) and TF-IDF index (params: `ngram_range=(variable lower bound,)`, `max_features=10000 `, `analyzer='word'`) ensuring CPU-only execution (FR-003)
- [X] T020 [US2] Implement chunking logic in `code/fastcontext_lite.py` to handle large repositories within RAM limits (e.g., streaming file reads, sliding window indexing) to prevent OOM on 7GB runners.
- [X] T021a [US2] Implement `code/baseline_runner.py` to load `princeton-nlp/fastcontextb ` (original FastContext model) in default precision on CPU (no bitsandbytes/quantization) as the PRIMARY baseline for FR-004 and Constitution Principle VII. Use `revision: main `, `prompt_template: fastcontext-v `, and `device_map: cpu ` with `max_memory: a sufficient amount of memory to handle the experimental workload, as determined by the system requirements and the scale of the data processing tasks outlined in the method.`. (FR-004) <!-- ATOMIZE: requested -->
- [X] T022 [US2] Implement `code/metrics_logger.py` to record `context_precision`, `total_tokens`, and `wall_clock_latency` for every run
- [~] T023 [US2] Implement orchestration logic in `code/main.py` to run Lite (T019) and Baseline (T021a) pipelines on the stratified sets (Requires T021a completion) and save logs to `data/results/exploration_logs.jsonl` (FR-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Analysis and Boundary Detection (Priority: P3)

**Goal**: Perform statistical analysis to compare metrics and identify performance boundaries.

**Independent Test**: Provide two mock datasets (one "Regular", one "Irregular") with pre-calculated metrics and verify the analysis script outputs the p-value for the Regular set comparison and the degradation percentage for the Irregular set.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test `tests/unit/test_analysis.py::test_paired_ttest_returns_significant_pvalue_for_mock_regular_data` using mock data (diffs=[,, 0.15]) to assert `run_ttest` returns p < 0.05
- [ ] T025 [P] [US3] Unit test `tests/unit/test_analysis.py::test_degradation_calc_returns_correct_percent` using mock data (baseline=100, lite=90) to assert `calc_degradation` returns a positive scalar value.
- [ ] T026 [P] [US3] Unit test `tests/unit/test_analysis.py::test_boundary_detection_identifies_threshold` using mock data (sensitivity analysis framework) to assert `find_threshold` returns a valid float.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/analysis.py` to perform power analysis (threshold=0.8, {{claim:c_6ac13cd6}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)) and select between paired t-test and Wilcoxon signed-rank test based on sample size. Use `scipy.stats.shapiro` for normality check; if p < 0.05, use Wilcoxon. (FR-005)
- [ ] T028b [US3] Implement `code/analysis.py` to calculate descriptive statistics (mean, std) AND **continuous regression analysis** (slope, R-squared) correlating `regularity_score` with performance delta for the "Regular" set (FR-005) (Requires T023 completion)
- [ ] T029 [US3] Implement `code/analysis.py` to calculate performance degradation percentage for the "Irregular" set by comparing Lite metrics against the **Baseline** (T021a) (FR-006, SC-004)
- [ ] T030 [US3] Implement `code/analysis.py` to perform regression analysis correlating `regularity_score` with performance delta (Redundant with T028b for Regular set, but covers Irregular set trend if needed)
- [ ] T031 [US3] Implement output generation to write `data/results/statistical_summary.json` with exact schema: `{ "p_value": float, "effect_size": { "cohen_d": float }, "degradation_percent": float, "boundary_threshold": float, "regression_slope": float, "r_squared": float }` (FR-005, FR-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `README.md` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/` with installation instructions, usage examples, and contribution guidelines (FR-001)
- [ ] T032b [P] Update `docs/` with API documentation for `code/static_analysis.py`, `code/fastcontext_lite.py`, and `code/analysis.py` (FR-001)
- [ ] T033 Code cleanup and refactoring
- [ ] T034 Performance optimization for TF-IDF indexing on large repos
- [ ] T035 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T036 Run quickstart.md validation and end-to-end pipeline check

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup **(Phase 1): No dependencies - can start immediately
- **Foundational **(Phase 2): Depends on Setup completion - BLOCKS all user stories
- **User Stories **(Phase 3+): All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish **(Final Phase): Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 **(P1): Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 **(P2): Can start after Foundational (Phase 2) - Depends on US1 data split
- **User Story 3 **(P3): Can start after Foundational (Phase 2) - Depends on US2 metric logs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/orchestration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/Utilities within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test directory naming returns score 1.0 in tests/unit/test_static_analysis.py::test_directory_naming_returns_score_1_0_for_standard_layout"
Task: "Unit test import pattern analysis in tests/unit/test_static_analysis.py::test_import_pattern_analysis_returns_score_0_5_for_mixed_imports"

# Launch all models for User Story 1 together:
Task: "Implement code/static_analysis.py to calculate regularity_score..."
Task: "Implement code/stratification.py to sort repositories by score..."
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
- **Constraint Reminder**: All models must run on CPU-only (no CUDA/8-bit quantization). Data must be real (SWE-bench Lite). **CRITICAL**: The primary baseline for comparison MUST be the original FastContext (4B model) as per FR-004 and Constitution Principle VII. T021a is the mandatory implementation for this baseline.