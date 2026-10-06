# Tasks: llmXive follow-up: extending "FastContext: Training Efficient Repository Explorer for Coding Agents"

**Input**: Design documents from `/specs/001-llmxive-fastcontext-lite/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/` by executing: `mkdir -p data/raw data/processed data/results code tests/unit tests/integration specs/contracts state`

- [X] T001b Initialize `state/` directory structure and create empty `state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml` file to ensure T004 has a valid target path.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python project with `requirements.txt` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/requirements.txt` by executing: `cat > requirements.txt << 'EOF'
scikit-learn==1.4.0
pandas==2.1.0
networkx==3.2.1
transformers==4.40.0
datasets==2.18.0
pytest==8.1.0
torch==2.2.0+cpu
scipy==1.12.0
nltk==3.8.1
EOF` followed by `pip install -r requirements.txt` to enforce CPU-only execution (using the explicit +cpu wheel) and prevent CUDA dependencies. (Constitution Principle I)
- [ ] T003a [P] Create `.ruff.toml` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with rules: `["E", "F", "I", "W"]` and `target-version = "py3"` (FR-001)
- [X] T003b [P] Create `pyproject.toml` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with black configuration: `line-length = 88 `, `target-version = ["py311"]` (FR-001)
- [X] T004 Implement `code/versioning.py` to compute content hashes for `data/` and `code/` artifacts and update `state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml` (Requires T001b completion) with a JSON schema containing `artifact_hashes` (map of filename: sha256 string) and `updated_at` (ISO 8601 timestamp string) (Constitution Principle V)
- [X] T005 [P] Create base data models and schema definitions in `code/__init__.py` and `contracts/`
- [X] T006 [P] Setup environment configuration management for dataset paths and model IDs in `code/config.py`
- [X] T007 [P] Implement data download utility in `code/data_loader.py` to fetch `princeton-nlp/SWE-bench_Lite` via `datasets` library, specifically revision: main, split: test, and verify checksums (FR-001)
- [ ] T007b-1 [P] [US1] **Schema Discovery**: Implement `code/annotation_extractor.py` (Step 1) to inspect the first 100 records of the SWE-bench JSONL fetched in T007. Identify the correct field name for ground truth (checking 'ground_truth_files', 'ground_truth', 'hints'). Output `data/raw/schema_discovery.json` with the detected field name. Raise `ValueError` if the field is ambiguous or missing. **Note**: This step is sequential within the task but the task itself is parallel-safe relative to other Phase 2 tasks. (FR-001, Requires T007 completion)
- [ ] T007b-2 [P] [US1] **Extraction**: Implement `code/annotation_extractor.py` (Step 2) to extract `instance['<detected_field>']` using the field name from T007b-1. Map to `repo_id`, `issue_id`, `ground_truth_file_paths` (JSON-encoded list). Write to `data/raw/ground_truth_annotations.csv`. Raise `ValueError` if the field is missing or null for any record to prevent silent fallback to synthetic data. **Note**: This extracted data is for validation ONLY and must be decoupled from the heuristic scoring logic in T011. (FR-001, Requires T007b-1 completion)
- [ ] T007b-3 [P] [US1] **Data Hygiene**: Implement `code/annotation_extractor.py` (Step 3) to record the derivation logic (script path `code/annotation_extractor.py`) and the SHA256 checksum of `data/raw/ground_truth_annotations.csv` in `state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml` (Constitution Principle III). (FR-001, Requires T007b-2 completion)
- [X] T011 [US1] Implement `code/static_analysis.py` to calculate `regularity_score` using the formula: `dir_score + w1 * test_score + w2 * import_score`.
 - `dir_score`: Binary check for presence of `src/`, `tests/`, `docs/` (1 if all present, 0 if none, linear interpolation for partial).
 - `test_score`: Calculate the relative depth of the `tests/` directory from the project root or `src/` root. Normalize depth to a unitless score where `1.0 - (min_depth / max_expected_depth) `. Handle multiple test directories by taking the minimum depth. This measures 'placement' relative to the root or source structure.
 - `import_score`: Use `networkx` to build an import graph. Calculate the ratio of internal imports (within the repo) to total imports and the graph density. Score = `0.5 * internal_ratio + 0.5 * (1 - graph_density) `.
 - Weights `w1` and `w2` must be loaded from `code/config.py` (defaults documented as standard if pilot study T007c is not yet run). (FR-001)
- [X] T012 [US1] Implement `code/static_analysis.py` to handle edge cases (missing test files, extreme irregularity) with fallback logic returning a default score (baseline parameter for initial evaluation).
- [X] T013 [US1] Implement `code/stratification.py` to sort repositories by score and split into "Regular" and "Irregular" sets of approximately equal size
- [X] T014 [US1] Implement data export logic to write `data/processed/regularity_scores.csv` with repo IDs and scores

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Structural Regularity Scoring and Dataset Split (Priority: P1) 🎯 MVP

**Goal**: Implement static analysis to score repositories and split them into "Regular" and "Irregular" sets.

**Independent Test**: Run the static analysis script on a small sample of known repositories and verify the output CSV contains a "regularity_score" column and the split logic correctly assigns the top half to the "Regular" set and the bottom half to the "Irregular" set.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T008 [P] [US1] Unit test `tests/unit/test_static_analysis.py::test_directory_naming_returns_score__0_for_standard_layout` using fixture `sample_repo_standard` (contains `src/`, `tests/`, `docs/`) to assert `calculate_dir_score` returns a normalized value indicating complete alignment.
- [X] T009 [P] [US1] Unit test `tests/unit/test_static_analysis.py::test_import_pattern_analysis_returns_score__5_for_mixed_imports` using fixture `sample_repo_mixed_imports` (contains `import os`, `from. import x`) to assert `calculate_import_score` returns a moderate value
- [X] T010 [P] [US1] Unit test `tests/unit/test_stratification.py::test_stratification_splits_50_50_by_regular_score` using fixture `sample_scores_csv` (n=10, scores ranging from low to high) to assert `split_repos` returns two lists of a fixed size

### Implementation for User Story 1

- [ ] T007c [US1] **Pilot Validation**: Implement `code/pilot_validation.py` to run a simple retrieval baseline on a small sample (n=20) from `data/processed/regularity_scores.csv` (requires T014 completion) and compute correlation between `regularity_score` and retrieval precision. If {{claim:c_f710e678}}, flag the stratification strategy for review. Output `data/processed/pilot_correlation.json`. **Dependency Note**: This task MUST complete before T027 to provide pilot data for power analysis. (Phase 0.5 Risk Mitigation, Requires T014 completion)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - FastContext-Lite Execution and Metric Collection (Priority: P2)

**Goal**: Execute the FastContext-Lite pipeline and the original FastContext (distilled) baseline to collect metrics.

**Independent Test**: Run the FastContext-Lite pipeline on a single "Regular" repository and verify that it outputs a JSON log containing `context_precision`, `total_tokens`, and `exploration_latency_ms` without requiring a GPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Integration test `tests/integration/test_pipeline.py::test_fastcontext_lite_runs_on_regular_repo` using fixture `sample_regular_repo` to assert `run_lite_pipeline` completes in < 5s and returns valid JSON log
- [ ] T017 [P] [US2] Integration test `tests/integration/test_pipeline.py::test_original_fastcontext_4b_runs_on_cpu` using fixture `sample_regular_repo` to assert `run_baseline_4b` completes on CPU (no CUDA) with explicit OOM/timeout handling (max limited duration, sufficient RAM) and returns valid JSON log (FR-004)
- [ ] T018 [P] [US2] Unit test `tests/unit/test_metrics_logger.py::test_log_schema_validates_required_fields` using mock data to assert `validate_log` passes for schema containing `context_precision`, `total_tokens`, `wall_clock_latency`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/fastcontext_lite.py` with deterministic parser: "Parse issue description to extract keywords using TF-IDF on issue text, remove stop-words using the NLTK English stop-word list, and use regex pattern `[A-Za-z_][A-Za-z0-9_]*::[A-Za-z0-9_]*` for code identifiers to search file tree for matching paths in tests/, src/, and docs/, and return top-K snippets based on TF-IDF similarity to the issue keywords." (Input: JSON `{"file_path": str, "content": str}`, output: `{"retrieved_snippets": list, "token_count": int}`) and TF-IDF index (params: `ngram_range=(1, 2) `, `max_features=10000 `, `analyzer='word' `) ensuring CPU-only execution. MUST implement **streaming file reads and sliding window indexing** for TF-IDF index construction to guarantee OOM prevention on large repositories within RAM limits. (FR-003, Requires T007b-3 completion, Requires T014 completion)
- [ ] T019b [US2] **Benchmark Script**: Implement `code/benchmark_lite.py` to run the FastContext-Lite engine on a subset of repositories and record wall-clock latency and memory usage. Output `data/results/lite_benchmark.json` to validate streaming/chunking performance. (FR-003, Requires T019 completion)
- [ ] T021a-1 [US2] **CPU Runner**: Implement `code/baseline_runner.py` (Step 1) to load `princeton-nlp/fastcontext-4b ` (original 4B model) in default precision and run on CPU (`device_map: cpu`). Record `hardware: cpu` flag. **CRITICAL**: The FastContext-Lite pipeline (T019) must run strictly on CPU. This task is for the Baseline only. (FR-004, Requires T007b-3 completion, Requires T014 completion)
- [ ] T021a-2 [US2] **GPU Escape Hatch**: Implement `code/baseline_runner.py` (Step 2) to detect OOM errors during CPU execution of the Baseline ONLY. If OOM occurs, re-run on a single GPU (`device_map: auto`, `max_memory` configured for ~16GB VRAM) and record a flag `hardware: gpu`. The script MUST NOT fall back to a smaller model or synthetic data. (FR-004, Requires T021a-1 completion)
- [ ] T021a-3 [US2] **Metric Normalization**: Implement `code/baseline_runner.py` (Step 3) to normalize metrics for the GPU run. Calculate `tokens/sec` (total_tokens / wall_clock_latency) and record this normalized value in the log file `data/results/exploration_logs.jsonl` in the same schema as CPU runs. This ensures Constitution VII compliance by allowing fair comparison despite hardware differences. (FR-004, Requires T021a-2 completion)
- [ ] T022 [US2] Implement `code/metrics_logger.py` to record `context_precision`, `total_tokens`, and `wall_clock_latency` for every run
- [ ] T023 [US2] Implement orchestration logic in `code/main.py` to run Lite (T019) and Baseline (T021a-1/2/3) pipelines on the stratified sets (Requires T019, T021a-3, and T014 completion) and save logs to `data/results/exploration_logs.jsonl` (FR-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Analysis and Boundary Detection (Priority: P3)

**Goal**: Perform statistical analysis to compare metrics and identify performance boundaries.

**Independent Test**: Provide two mock datasets (one "Regular", one "Irregular") with pre-calculated metrics and verify the analysis script outputs the p-value for the Regular set comparison and the degradation percentage for the Irregular set.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test `tests/unit/test_analysis.py::test_paired_ttest_returns_significant_pvalue_for_mock_regular_data` using mock data (diffs=[0.1, 0.15, 0.2]) to assert `run_ttest` returns p < 0.05
- [ ] T025 [P] [US3] Unit test `tests/unit/test_analysis.py::test_degradation_calc_returns_correct_percent` using mock data (baseline=100, lite=90) to assert `calc_degradation` returns a positive scalar value.
- [ ] T026 [P] [US3] Unit test `tests/unit/test_analysis.py::test_boundary_detection_identifies_threshold` using mock data (sensitivity analysis framework) to assert `find_threshold` returns a valid float.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/analysis.py` to perform power analysis (threshold=0.8, {{claim:c_698f6a76}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value), effect_size derived from pilot data (T007c) OR default to Cohen's d=0.5 if pilot data is missing). **Fallback Logic**: If T007c output `data/processed/pilot_correlation.json` is missing, log a WARNING and proceed with the default effect size. **Output Requirement**: Write `effect_size_source` ("pilot" or "default_d0.5") to `data/results/statistical_summary.json` to document the justification. Select between paired t-test and Wilcoxon signed-rank test based on sample size. Perform continuous regression analysis correlating `regularity_score` with performance delta for the full dataset. Use `scipy.stats.shapiro` for normality check; if p < 0.05, use Wilcoxon. Citations: Scipy 1.12.0 stats docs (https://docs.scipy.org/doc/scipy/reference/stats.html) and Cohen for power analysis. (FR-005, Requires T023 completion, Requires T007c completion (optional))
- [ ] T028b [US3] Implement `code/analysis.py` to calculate descriptive statistics (mean, std) AND **continuous regression analysis** (slope, R-squared) correlating `regularity_score` with performance delta across the FULL dataset (both Regular and Irregular sets) to identify boundary conditions (FR-005) (Requires T023 completion)
- [ ] T029 [US3] Implement `code/analysis.py` to calculate performance degradation percentage for the "Irregular" set by comparing Lite metrics against the **Baseline** (T021a-3) AND explicitly compare this result against the 10% precision drop threshold defined in SC-004. **Output Requirement**: Write `degradation_percent` and `boundary_exceeded` (boolean) to `data/results/statistical_summary.json`. (FR-006, SC-004, Requires T023 completion)
- [ ] T031 [US3] Implement output generation to write `data/results/statistical_summary.json` with exact schema: `{ "p_value": float, "effect_size": { "cohen_d": float }, "effect_size_source": "pilot" | "default_d0.5", "degradation_percent": float, "boundary_threshold": null | float, "boundary_exceeded": boolean, "regression_slope": float, "r_squared": float }`. If `boundary_threshold` is deferred per SC-005, output `null`. (FR-005, FR-006, Requires T023 completion, Requires T027 completion, Requires T029 completion)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `README.md` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/` with installation instructions, usage examples, and contribution guidelines (FR-001)
- [ ] T032b [P] Update `docs/` with API documentation for `code/static_analysis.py`, `code/fastcontext_lite.py`, and `code/analysis.py` (FR-001)
- [ ] T033a [P] Code cleanup: Remove unused imports from all files in `code/`
- [ ] T033b [P] Code cleanup: Enforce line length < 88 in all `code/` files
- [ ] T033c [P] Code cleanup: Add type hints to all public functions in `code/`
- [ ] T035a [P] Unit test `tests/unit/test_edge_cases.py::test_empty_repo_handling` for empty repository handling.
- [ ] T035b [P] Unit test `tests/unit/test_edge_cases.py::test_binary_files_only_handling` for binary-only repository handling.
- [ ] T035c [P] Unit test `tests/unit/test_edge_cases.py::test_circular_imports_handling` for circular import handling.
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
- **User Story 2 **(P2): Can start after Foundational (Phase 2) - Depends on US1 data split (T014)
- **User Story 3 **(P3): Can start after Foundational (Phase 2) - Depends on US2 metric logs and US1 pilot data (T007c)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/orchestration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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
3. Complete Phase 3: User Story 1 (including T007c pilot validation)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (including T007c) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (including T007c)
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
- **Constraint Reminder**: All models must run on CPU-only (no CUDA/8-bit quantization) unless a GPU escape hatch is triggered by OOM. Data must be real (SWE-bench Lite). **CRITICAL**: The primary baseline for comparison MUST be the original 4B model (`princeton-nlp/fastcontext-4b `). T021a-1/2/3 implements a GPU escape hatch to ensure the experiment runs even if CPU RAM is exceeded, with normalized metrics.