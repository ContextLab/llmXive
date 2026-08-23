# Tasks: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

**Input**: Design documents from `/specs/001-code-maintainability-impact/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per implementation plan (`projects/PROJ-247-evaluating-the-impact-of-code-generation/`) by executing: `mkdir -p data/raw data/processed data/ground_truth data/logs code/utils tests/unit tests/contract docs/paper scripts`.
- [X] T001b Validate directory structure against plan.md by checking existence of all required directories and logging any missing paths to `data/logs/structure_validation.log`. (Depends on T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note**: T007 (Models) MUST complete before T005 and T006. T005 and T006 are parallel to each other but sequential to T007.

- [X] T007 Create base data models/entities in `code/utils/models.py` (Repository, CodeBlock, MaintenanceEvent, MatchedPair) using dataclasses with type hints.
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` containing pinned versions for: transformers, onnxruntime, radon, scikit-learn, pandas, requests, matplotlib, statsmodels, datasets, PyGithub.
- [X] T003 [P] Configure linting and formatting by creating `.flake8` (max-line-length=88, exclude=venv), `pyproject.toml` (black target-version=py311), and `.editorconfig` (indent_size=4, end_of_line=lf) with the specified rules.
- [X] T005 [P] Implement `code/utils/github_client.py` with rate-limit handling, shallow clone logic (depth=100), and 404 error handling for deleted repos. **[P] applies only to T005 vs T006, not T007.**
- [X] T006 [P] Implement `code/utils/classifier.py` wrapping `transformers` CodeBERT model via `onnxruntime` for CPU-only inference. **[P] applies only to T005 vs T006, not T007.**
- [X] T008 Configure error handling and logging infrastructure by creating `code/utils/logging_config.py` with JSON format, TimedRotatingFileHandler (maxBytes=1MB, backupCount=5), and log output to `data/logs/`.
- [X] T009 Setup environment configuration management by creating `.env.example` with keys `GITHUB_TOKEN`, `DATA_PATH`, `LOG_PATH` and a validation script `scripts/validate_env.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Curation, Tagging, and Matching (Priority: P1) 🎯 MVP

**Goal**: Identify a representative set of active repos, tag code blocks via CodeBERT, and perform propensity score matching with a one-to-one ratio.

**Independent Test**: Run on a sample of repositories.; verify `data/processed/matched_pairs_filtered.csv` contains valid tags, matched pairs, and no duplicates; verify `data/ground_truth/manual_labels.csv` is created.

### Implementation for User Story 1

- [X] T010a [P] [US1] Implement `code/01_data_curation.py` script: GitHub Search API integration (topics:llm-generated, topic:copilot). Search for repos matching criteria.
- [X] T010b-impl [US1] Execute primary search: Query GitHub API for repos with `topic:llm-generated` OR `topic:copilot` AND `stars>=5` AND `updated_at > 90 days ago`. Output results to `data/raw/repo_list.csv`. Stop when a sufficient number of repos are found or a predefined limit of API calls is reached. (Depends on T010a)
- [X] T010c-impl [US1] Execute secondary search: If `data/raw/repo_list.csv` contains < 50 repos, query GitHub API for `q="LLM generated code" OR "Copilot generated"` (in code) with same activity filters. Append to `data/raw/repo_list.csv` until 50 repos found or 5000 API calls made. (Depends on T010b-impl)
- [X] T011 [US1] Implement repository cloning logic in `code/01_data_curation.py`: shallow clone (depth=100), filter by activity (≥1 commit/90 days, ≥5 stars).
- [X] T011a [US1] Implement repository metadata extraction in `code/01_data_curation.py`: retrieve `stargazers_count`, `created_at`, and `updated_at` for each repo and store in `data/raw/repo_metadata.csv` for use in matching.
- [ ] T012 [US1] Implement code block extraction logic: Parse Python files using `ast` (extract functions/classes) and JS files using `acorn` (via `tree-sitter`). Extract code blocks. **Output**: `data/raw/code_blocks.csv` with schema: `block_id, file_path, start_line, end_line, language, content_hash`. (Depends on T011)
- [ ] T012b [US1] Implement verification logic for `git mv` detection: Run `git log --follow` on each block's file path. Exclude block ONLY if file path hash changes OR directory level changes (indicating complete structural refactor). **Log**: `data/logs/refactor_exclusions.log` with format: `block_id, old_path, new_path, reason`. **Verify** by running `tests/unit/test_git_mv_detection.py` and ensuring [deferred] pass rate; generate `data/logs/refactor_validation_report.json`. (Depends on T012)
- [ ] T013 [US1] Integrate CodeBERT classifier (ONNX) in `code/01_data_curation.py`: tag blocks as LLM/Human with confidence ≥ 0.8; exclude low-confidence blocks. Log exclusions to `data/logs/classifier_exclusions.log`. (Depends on T012)
- [X] T014 [US1] Implement static complexity metric extraction using `radon` (cyclomatic complexity, nesting depth, LOC) in `code/01_data_curation.py`. **Output**: Append metrics to `data/raw/code_blocks.csv`. (Depends on T012)
- [ ] T015 [US1] Implement 1:1 nearest-neighbor propensity score matching in `code/utils/matching.py`. **Algorithm**: 1. Fit a logistic regression model using `cyclomatic_complexity` and `LOC` (from T014) as covariates to predict probability of being LLM-generated. 2. Calculate propensity scores for all blocks. 3. Perform 1:1 nearest-neighbor matching on propensity scores between LLM and Human blocks within the same repository. **Output**: `data/processed/matched_pairs.csv`. (Depends on T011a, T014)
- [ ] T016 [US1] Enforce repository inclusion criteria: Exclude repos with <5 LLM and <5 Human blocks after tagging. **Output**: Filter `data/processed/matched_pairs.csv` to `data/processed/matched_pairs_filtered.csv`. **Log**: `data/logs/repo_exclusions.csv`. (Depends on T015)
- [X] T017a [US1] Implement ground truth selection: randomly select ≥10 blocks for manual verification, save to `data/ground_truth/manual_labels.csv`. (Depends on T013)
- [ ] T017b [US1] Calculate classifier precision and recall on the ground truth subset from T017a by comparing predicted labels (from T013) against ground truth. **Verify** by running `tests/unit/test_classifier_metrics.py` against a mock dataset. Save results to `data/ground_truth/classifier_metrics.json` as required by FR-007. (Depends on T017a, T013)
- [X] T018 [US1] Add checksum generation for `data/ground_truth/manual_labels.csv` and record in `state/checksums.json`. (Depends on T017a)
- [X] T019 [US1] Add checkpoint mechanism in `code/01_data_curation.py`: save progress per repo to resume if interrupted (time limit).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Longitudinal Metric Extraction (Priority: P2)

**Goal**: Extract code churn and bug fix latency metrics for matched blocks over a multi-month window.

**Independent Test**: Run on repo with known history; verify "days to fix" and "lines changed" match manual `git log` verification.

### Implementation for User Story 2

- [X] T020a [US2] Implement `code/02_metric_extraction.py`: Load `matched_pairs_filtered.csv` (from T016).
- [X] T020b [US2] Query commit history for a multi-month window post-introduction for each block.
- [X] T020c [US2] Parse commit logs for changes to specific blocks.
- [ ] T021 [US2] Implement bug fix latency calculation: Parse commit messages for "Fixes #N" or "Closes #N" using regex. Extract issue number N. Query GitHub API for issue N to confirm resolution status. Calculate time difference between the commit timestamp and the issue closed timestamp. **Output**: `data/processed/metrics_longitudinal.csv` with columns: `block_id, latency_days, issue_id`. (Depends on T020c)
- [ ] T022 [US2] Implement code churn calculation: Aggregate lines added/deleted for each block in a multi-month window (excluding initial commit). **Output**: Append to `data/processed/metrics_longitudinal.csv` with columns: `block_id, lines_added, lines_deleted, window_start, window_end`. (Depends on T020c)
- [ ] T023 [US2] Handle edge cases: Exclude pairs with null latency from latency analysis (but retain for churn). **Log**: `data/logs/latency_exclusions.log` with format: `pair_id, reason`. (Depends on T021, T022)
- [ ] T024 [US2] Handle repo deletion/private status during window: Gracefully exclude from analysis count with 404 handling. **Log**: `data/logs/repo_deletion.log`. **Output**: Update `data/processed/metrics_longitudinal.csv` by removing rows for deleted repos. (Depends on T020c)
- [ ] T025 [US2] Save processed metrics to `data/processed/metrics_longitudinal.csv` with schema validation. (Depends on T021, T022, T023, T024)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform Wilcoxon Signed-Rank tests on matched pairs, apply Benjamini-Hochberg correction, and generate visualizations.

**Independent Test**: Run on mock dataset; verify Wilcoxon test returns expected p-values and effect sizes; verify PNG plots render <10MB on CPU.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/03_analysis.py`: Load `metrics_longitudinal.csv` (requires T025) and `matched_pairs_filtered.csv` (requires T015). (Depends on T025, T015)
- [ ] T027a [US3] Calculate W-statistic and p-value using `scipy.stats.wilcoxon` on matched pairs to compare maintainability metrics between LLM and Human groups, as required by FR-005.
- [ ] T027b [US3] Calculate Cohen's d effect size for the observed differences.
- [ ] T027c [US3] Save Wilcoxon results to `data/processed/wilcoxon_results.json`. (Depends on T027a, T027b)
- [X] T027d [US3] Document the amendment to Constitution Principle VI in `docs/paper/constitution_amendment.md`: explain why Wilcoxon Signed-Rank is used instead of Mann-Whitney U for paired data.
- [ ] T028 [US3] Implement Benjamini-Hochberg correction for multiple comparisons across churn and latency tests applied to Wilcoxon p-values. **Output**: `data/processed/bh_corrected_pvalues.json`. (Depends on T027c)
- [X] T028a [US3] Document Benjamini-Hochberg assumptions and verify logic based on code output in `docs/paper/methodology.md`, ensuring traceability to code/data. (Depends on T028)
- [ ] T029 [US3] Implement Sensitivity Analysis: Adjust effect sizes using misclassification rates from `manual_labels.csv` (ground truth). **Output**: `data/processed/sensitivity_analysis.csv`. (Depends on T017b)
- [ ] T029b [US3] Read existing classifier precision/recall metrics from `data/ground_truth/classifier_metrics.json` (produced by T017b). Compare against SC-006 threshold (0.85) defined in `code/utils/config.py`. **If threshold not met**: Block execution of T030 and T032, and append a JSON object to `docs/paper/limitations.json` with keys `threshold_met` (bool) and `reason` (string). (Depends on T017b)
- [ ] T030 [US3] Generate visualizations: Box plots and density plots for churn/latency using `matplotlib` (CPU-only); save as PNG <10MB. **Files**: `docs/paper/fig_churn_boxplot.png`, `docs/paper/fig_latency_density.png`. (Depends on T026)
- [ ] T031 [US3] Perform post-hoc power analysis on final matched pair count using `scipy.stats.power_analysis` with effect size=0.5, alpha=0.05, targeting ≥0.80 power. **Output**: `data/processed/power_analysis.json` with format: `{"power": 0.XX, "threshold_met": true/false}`. (Depends on T015, T025)
- [ ] T032 [US3] Generate final report summary: p-values, effect sizes (Cohen's d), bias-corrected confidence intervals, and FDR. **Output**: `docs/paper/results_summary.md` with structured sections. (Depends on T027c, T028, T029, T030, T031)
- [ ] T033 [US3] Save all statistical artifacts to `data/processed/` and `docs/paper/`. **Files**: `data/processed/wilcoxon_results.json`, `data/processed/bh_corrected_pvalues.json`, `data/processed/power_analysis.json`, `data/processed/sensitivity_analysis.csv`. (Depends on T032)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a-1 [P] [Polish] Generate data model documentation in `docs/paper/data-model.md`. **Dependencies**: T012 (code_blocks schema), T021 (latency schema), T022 (churn schema), T025 (final metrics schema). (Depends on T012, T021, T022, T025)
- [ ] T034a-2 [P] [Polish] Generate schema YAML definitions in `contracts/`. **Files**: `contracts/dataset.schema.yaml`, `contracts/metrics.schema.yaml`, `contracts/ground_truth_schema.schema.yaml`. **Dependencies**: T012, T021, T022, T025. (Depends on T012, T021, T022, T025)
- [ ] T034b [P] [Polish] Create `quickstart.md` (Prerequisites, Installation, Execution, Expected Outputs) and update `docs/paper/methodology.md` with final execution paths. **Dependencies**: T034a-1, T034a-2, T027-T031. (Depends on T034a-1, T034a-2, T027, T028, T029, T030, T031)
- [ ] T034c [P] [Polish] Update `docs/paper/results_summary.md` with final visualizations and interpretation. **Dependencies**: T032, T030. (Depends on T032, T030)
- [ ] T035 [P] [Polish] Code cleanup and refactoring: Refactor `code/01_data_curation.py` and `code/02_metric_extraction.py` to reduce cyclomatic complexity < 10. **Verify**: Run `radon cc code/01_data_curation.py` and ensure max complexity is < 10; if not, refactor until it is. Log results to `data/logs/cyclomatic_complexity_report.txt`. **Dependencies**: T012, T021, T022, T025. (Depends on T012, T021, T022, T025)
- [ ] T035a [P] [Polish] Performance optimization: Use `cProfile` to identify CPU bottlenecks and `iostat` to measure I/O wait in `code/01_data_curation.py` and `code/02_metric_extraction.py`; assert I/O wait < 10% and ensure pipeline completes within 6h. **Dependencies**: T035. (Depends on T035)
- [ ] T036 [P] [Polish] Run contract tests for data schemas in `tests/contract/`. **Dependencies**: T015, T025, T034a-1, T034a-2. (Depends on T015, T025, T034a-1, T034a-2)
- [ ] T037 [P] [Polish] Security hardening: Add `.env` to `.gitignore` and implement log scrubber in `code/utils/logging_config.py` to strip `GITHUB_TOKEN` from logs. (Depends on T008)
- [ ] T038 [P] [Polish] Create `scripts/validate_repro.sh` to verify end-to-end reproducibility: clone repo, install deps, run main pipeline, verify exit code 0 and existence of `data/processed/statistical_results.json`. (Depends on T034a-1, T034a-2, T034b)
- [ ] T039 [P] [Polish] Run `bash scripts/validate_repro.sh` to verify end-to-end reproducibility; verify exit code 0 and existence of `data/processed/statistical_results.json`. (Depends on T038, T033)

**Checkpoint**: All documentation and polish tasks can run in parallel with the final stages of US3 (T031, T032) once core data generation (T025) is complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T007 (Models) must complete before T005/T006 (which depend on models). T005 and T006 are NOT parallel to T007.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational.
 - **User Story 2 (P2)**: Can start after Foundational, but **depends on US1 output** (`matched_pairs_filtered.csv`).
 - **User Story 3 (P3)**: Can start after Foundational, but **depends on US1 and US2 outputs** (`matched_pairs_filtered.csv`, `metrics_longitudinal.csv`, `manual_labels.csv`).
- **Polish (Final Phase)**: Depends on all desired user stories being complete, BUT with parallel execution enabled for documentation and cleanup tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 output** (`matched_pairs_filtered.csv`).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US1 and US2 outputs**.
- **CRITICAL**: US3 CANNOT start until US2 is complete. The claim that all stories can run in parallel is FALSE for US3.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] (T005, T006) can run in parallel **after** T007 completes.
- Once Foundational phase completes, **User Story 1** can start.
- **User Story 2** can start **only after** US1 produces `matched_pairs_filtered.csv`.
- **User Story 3** can start **only after** US1 produces `matched_pairs_filtered.csv` AND US2 produces `metrics_longitudinal.csv`.
- **Polish Tasks**:
 - **T034a-1 (Schemas)** can run in parallel with T026-T031 once T012, T021, T022, T025 are complete.
 - **T035 (Cleanup)** can run in parallel with T026-T031 once T012, T021, T022, T025 are complete.
 - **T034b (Quickstart)** can run in parallel with T032 once T034a-1 and T027-T031 are complete.
 - **T038 (Repro Script)** can run in parallel with T032-T033.
 - **T039 (Validate Repro)** runs last, after T038 and T033.
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories **cannot** be worked on in parallel if they have data dependencies (e.g., US3 cannot start before US2).

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
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T007 first, then T005/T006).
2. Once Foundational is done:
 - Developer A: User Story 1
3. Once US1 completes:
 - Developer B: User Story 2
4. Once US2 completes:
 - Developer C: User Story 3
5. Stories complete and integrate independently.
6. **Parallel Polish**: Once T025 (US2 end) is complete, Developer D can start T034a-1/T034a-2 (Docs) and T035 (Cleanup) immediately, while Developer C finishes T031-T033.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All model inference (CodeBERT) MUST use `onnxruntime` (CPU) only. No GPU, no 8-bit quantization requiring CUDA.
- **CRITICAL**: All data must be real. No synthetic/fake datasets for input. Use live GitHub API.
- **CRITICAL**: Statistical analysis uses Wilcoxon Signed-Rank tests for matched pairs as per FR-005, not LMM.
- **CRITICAL**: Propensity matching MUST include block-level complexity (T014) and repo-level covariates (T011a) as per FR-008.
- **CRITICAL**: Ground truth precision/recall calculation (FR-007) must occur in US1 phase (T017b), not deferred to US3.
- **CRITICAL**: T017b and T018 depend on T017a. T020 depends on T016. T026 depends on T025 and T016.
- **CRITICAL**: T012, T012b, T016, T021, T022, T023, T024, T025, T027, T028, T029, T030, T031, T032, T033 are now explicitly defined with output artifacts and schemas to ensure executability and constraint preservation.
- **CRITICAL**: T034a-1 and T034a-2 are designed to run in parallel with the final stages of US3 (T031-T033) once core data generation (T025) is complete, resolving previous blocking concerns.
- **CRITICAL**: T021 MUST strictly enforce the "Fixes #N" / "Closes #N" pattern and map to issues via commit diff file paths; any ambiguity must result in exclusion to prevent false positives in latency calculation.
- **CRITICAL**: T012b MUST implement `git log --follow` to detect renames; if a block's path changes significantly (directory level), it must be excluded to ensure valid longitudinal tracking.
- **CRITICAL**: T029b must block T030 and T032 if precision/recall threshold is not met.