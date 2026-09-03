# Tasks: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

**Input**: Design documents from `/specs/001-code-complexity-bug-prediction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must be done first or in order)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0.0: Constitutional Compliance (Strictly Sequential, Blocking)

**Purpose**: Resolve the Constitutional Conflict (Plan vs Spec on statistical methods) by following the parent llmXive amendment procedure before any project setup. This phase MUST complete successfully before any directory creation or code execution.

**⚠️ CRITICAL**: Execution is BLOCKED until the Constitution is amended via PR and human confirmation.

- [ ] T000a [S] Generate Constitution Amendment Deliverables. **Logic**: Generate the PR description and Sync Impact Report as artifacts for human submission. **Content**: The PR must include the proposed text change (replacing Pearson/McNemar with Point-Biserial/Permutation), scientific justification, and a `Sync Impact Report`. **Deliverable**: Files `amendment_pr_description.md` and `amendment_sync_impact_report.md`. **Note**: This task does NOT merge the PR; it prepares the artifacts for human submission. **Note**: This task unblocks T000b.
- [ ] T000b [S] Wait for Human Intervention. **Logic**: Halt execution and wait for a human to merge the PR and update the Constitution. **Validation**: Check for the existence of `amendment_ratified.md` (a marker file created by the human after merging). **Deliverable**: Exit code 0 if `amendment_ratified.md` exists; non-zero (and halt pipeline) if missing. **Note**: This task depends on T000a (artifacts generated) and requires human action.
- [ ] T000c [S] Verify Constitution Update. **Logic**: Check that the Constitution file (`constitutions/FR-030.md`) has been updated with the new Principle VI text and a version bump, matching the `amendment_ratified.md` marker. **Validation**: Grep for the new statistical methods and the updated version line. **Deliverable**: Exit code 0 on success, non-zero (and halt pipeline) if the amendment is not verified. **Note**: This task depends on T000b.

## Phase 0.1: Project Setup (Sequential, depends on 0.0)

**Purpose**: Create the physical directory structure and environment required for all subsequent tasks.

- [ ] T001c [S] Create `code/` directory structure: `code/`, `code/src/`, `code/tests/`, `code/data/raw/`, `code/data/processed/`, `code/data/results/`. **Command**: `mkdir -p code/src code/tests code/data/raw code/data/processed code/data/results`. **Verification**: `if [ ! -d code/src ]; then exit 1; fi`.
- [X] T001e [P] Implement Time-Limit Enforcement Wrapper. **Logic**: Create `code/run_pipeline.sh` with a `timeout 6h` wrapper that executes the *entire* pipeline. **Deliverable**: `code/run_pipeline.sh` with timeout logic. **[SC-005]** **Depends on**: T001c. **Note**: Merge into `code/run_pipeline.sh` without overwriting T001f's changes.
- [X] T001f [P] Implement Global Memory Limit Enforcement. **Logic**: Add a system-level memory limit to `code/run_pipeline.sh` to hard-fail the process if memory exceeds a predefined threshold. **Deliverable**: Updated `code/run_pipeline.sh` with memory limit logic. **[SC-005]** **Depends on**: T001c. **Note**: Merge into `code/run_pipeline.sh` without overwriting T001e's changes.
- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `pandas==2.1.0`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `tree-sitter==0.20.0`, `tree-sitter-java==0.20.0`, `pytest==7.4.0`. (Note: `defects4j` CLI and PMD are installed separately in T002c).
- [X] T002b [P] Configure `code/pyproject.toml` with project metadata, entry points for scripts, and dependency groups.
- [X] T002c [P] Implement `code/setup_cli.sh` to install `defects4j` CLI tool and PMD (Java static analysis tool). **Exact Command**: `apt-get update && apt-get install -y openjdk-17-jdk=17.0.9+1 pmd-bin=7.0.0`. **Verification**: `defects4j --version` and `pmd --version`. **Note**: System packages must be pinned to ensure reproducibility. **[FR-001]** **[FR-002]**
- [X] T002f [P] Configure linting (flake8) and formatting (black) tools in `code/pyproject.toml` or separate config files.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Implement `code/src/config.py` to define environment variables for Defects4J path, fixed random seeds (seed=42), and memory limits. **[FR-005]**
- [X] T004b [S] Create and implement `code/src/ingest.py`. **Logic**: Skeleton with `NotImplementedError` removed. Implement logic to download Defects4J v2.0+ subset via CLI wrapper. **Algorithm**: Select projects alphabetically by project ID until cumulative **raw disk size** (measured via `du -sb` on the cloned repo directory) exceeds a substantial threshold. Include strict error handling to raise `DataFetchError` if CLI fails, ensuring NO synthetic fallback. **[FR-001]** **[SC-005]**
- [X] T005 [P] Define metric extraction interface in `code/src/metrics.py`: Specify function signatures for calculating Cyclomatic Complexity (via PMD CLI), Halstead Volume (via JavaParser-based custom script), and LOC. The interface must support both tools.
- [X] T007 [P] Create `code/data/processed/features.csv` schema validator and checksum generator (`code/data/checksums.json`). **[FR-001]**
- [X] T008 [P] Create skeleton `code/run_pipeline.sh` orchestration script to enforce execution order (Ingest -> Metrics -> Labeling -> Analysis), noting that Analysis scripts are not yet implemented.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Metric Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest a subset of Defects4J Java projects and compute a labeled feature matrix (metrics + bug label).

**Independent Test**: The pipeline produces a `features.csv` where rows = valid Java files, columns include metrics and binary target, with no nulls in numeric columns.

### Implementation for User Story 1

- [X] T013 [S] [US1] Implement `code/src/ingest.py` logic to clone a representative sample of projects, filter for `.java` files, and enforce a bounded **raw disk size** limit via dynamic subset validation. **Logic**: Must `git checkout the specific bug-introduction commit` for each project before metric extraction. **Note**: This task completes the logic started in T004b. **[FR-001]** **Depends on**: T004b.
- [ ] T014b [P] [US1] Implement Python wrapper script for PMD CLI integration to calculate Cyclomatic Complexity for every Java file. **Exact CLI**: `pmd -f xml -d <dir> -rulesets rulesets/java/complexity.xml`. **Parsing Logic**: Parse PMD XML output, identify all `<violation>` tags, and **sum the 'complexity' attribute** of each tag to produce the integer Cyclomatic Complexity score. **Error Handling**: If a file cannot be parsed by PMD (syntax error) OR if the required ruleset file is missing, **log the file path, increment an `exclusion_count`, write a formatted error message to stderr and `exclusion.log`, and raise a `ToolchainError` to halt the pipeline**. **No fallback** to other rulesets is permitted. **Prerequisite**: T000c (Constitution Update). **Depends on**: T013. **[FR-002]**
- [X] T014c [P] [US1] Implement `code/src/metrics/halstead.py` using **javaparser-python (v3.x)** to compute Halstead Volume. **Algorithm**: Parse Java AST, count operators (N1) and operands (N2), count unique operators (n1) and unique operands (n2). **Token Mapping**: Use standard Java token definitions as per the official JavaParser documentation (https://github.com/javaparser/javaparser/wiki/Token-Definitions). **Note**: `javaparser-python` invokes the canonical JavaParser library, satisfying the 'Java-compatible' constraint. **Error Handling**: If parsing fails, log the file path and skip it, raising a warning but not halting. **Prerequisite**: T000c (Constitution Update). **Depends on**: T013. **[FR-002]**
- [X] T015 [US1] Implement `code/src/labeling.py` logic to cross-reference commits with file changes to set `is_buggy` flag. **Input**: Defects4J commit JSON (schema: `{"commit_hash": "str", "files": ["str"]}`). **Output**: binary label. **Logic**: If file path in commit diff, set `is_buggy=1`, else `0`. **[FR-003]**
- [X] T016 [US1] Implement exclusion logic in `code/src/ingest.py` for generated code/non-Java files with logging. **[FR-001]**
- [X] T017 [S] [US1] Generate `code/data/processed/features.csv` with columns: `file_path`, `cc`, `halstead`, `loc`, `is_buggy`. **Depends on**: T014b, T014c, T015, T016. **[FR-001]**
- [ ] T018 [S] [US1] Implement `validate_features()` function in `code/src/ingest.py`. **Logic**: Check for NaN values in metric columns (`cc`, `halstead`, `loc`). If NaNs found, **DROP the row** and log the count. **Deliverable**: Generate `code/data/processed/exclusions.log` listing all dropped file paths and reasons **as a primary deliverable required for the Independent Test verification**. **Fail Condition**: If the resulting dataset is empty, raise a `DataIntegrityError` and halt the pipeline. **This step MUST run after T017 to ensure the final artifact meets the acceptance criteria.** **[FR-001]** **Depends on**: T017.
- [X] T019 [S] [US1] Implement global memory monitoring in `code/src/monitor.py` to track **aggregate** RAM usage periodically (at regular intervals or at major data load checkpoints) using `logging.info`. **Logic**: Use `psutil` to calculate the sum of the main process and any spawned child processes' RSS. **Frequency**: Log at regular intervals or at major checkpoints. **Fail Condition**: If logged aggregate memory > 7GB, raise `MemoryLimitExceeded` and exit 1. **[SC-005]** **Depends on**: T018.

### Phase 2b: Testing for User Story 1 (Sequential - Requires Implementation Complete)

> **NOTE**: These tasks MUST run AFTER T013-T019 are complete. They are marked [S] (Sequential) relative to the implementation phase to enforce the "Implementation before Test" dependency.

- [X] T010a [S] [US1] Unit test `test_cc_returns_int` in `code/tests/test_metrics.py` (mock Java file input). **Depends on**: T014b.
- [X] T010b [S] [US1] Unit test `test_halstead_returns_float` in `code/tests/test_metrics.py` (mock Java file input). **Depends on**: T014c.
- [X] T011a [S] [US1] Unit test `test_labeling_maps_commit_to_1` in `code/tests/test_labeling.py` (verify bug-introduction commit mapping). **Depends on**: T015.
- [X] T012a [S] [US1] Integration test `test_pipeline_shape` in `code/tests/test_pipeline.py` (verify `features.csv` shape and content). **Depends on**: T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Correlation Analysis and Baseline Modeling (Priority: P2)

**Goal**: Calculate correlations and train baseline models (Logistic Regression, Random Forest) using Repeated 5-Fold Cross-Validation.

**Independent Test**: Analysis script outputs a report with Point-Biserial/Spearman correlations and mean ROC-AUC/F scores from multiple folds.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/src/analysis.py` to compute Point-Biserial and Spearman correlations with p-values. **Logic**: Must output both coefficient and p-value. **Deliverable**: Generate `code/data/results/correlation_report.json` containing keys: `metric`, `point_biserial_r`, `point_biserial_p`, `spearman_rho`, `spearman_p`. **Prerequisite**: T000c (Constitution Update). **[FR-004]**
- [X] T023 [S] [US2] Implement `code/src/modeling.py` to train Logistic Regression and Random Forest with **Repeated 5-Fold Cross-Validation (10 repeats, seed=42)** on the **Full Metric Set**. **Logic**:
 1. **Outer Loop**: Split data into multiple folds and repeat the process across several iterations to generate a comprehensive set of splits.
 2. **Model Training**: Train Logistic Regression and Random Forest on the **full set of metrics** (CC, Halstead, LOC) for each training split.
 3. **Evaluation**: Calculate ROC-AUC and F1-score on the test split.
 4. **Outputs**: Save aggregated prediction arrays for the 'Full Metric Set' models to `code/data/results/predictions_full.json`.
 **Deliverable**: `code/data/results/predictions_full.json` containing predictions for all 50 test splits. **[FR-005]** **[SC-002]**
- [X] T024 [S] [US2] Implement aggregation logic to calculate mean ROC-AUC and F-score with standard deviation across **all individual folds**. **Logic**: Aggregate the raw prediction arrays from T023 and compute statistics over the full set of 50 fold predictions. **Formula**: Compute the arithmetic mean and sample standard deviation of the 50 individual ROC-AUC values. **Deliverable**: Generate `code/data/results/baseline_metrics.json` with keys: `mean_roc_auc`, `std_roc_auc`, `mean_f1`, `std_f1`. **[FR-005]** **[SC-002]** **Depends on**: T023.
- [ ] T025 [US2] Handle class imbalance: Detect zero-buggy-file projects and log warnings/skip gracefully. **Strategy**: Skip project with warning if buggy count is zero.
- [ ] T029 [S] [US2] Implement `code/src/modeling.py` to extract feature importance weights from the trained Random Forest model (from T023) to identify the 'Single Best Metric'. **Aggregation**: **Calculate the mean importance across all 50 folds** (10 repeats * 5 folds). **Prerequisite**: T000c (Constitution Update). **[FR-007]** **[SC-004]** **Depends on**: T023.
- [ ] T029b [S] [US2] Implement validation logic for 'Single Best Metric' selection and tie-breaking. **Logic**: If T029 finds multiple metrics with equal highest importance, select the one with the highest Point-Biserial correlation coefficient (from T021) as a tie-breaker. **Deliverable**: Generate `code/data/results/validation_report.md` confirming the selection logic is deterministic and outputting the 'Single Best Metric' name. **Depends on**: T029, T021. **[FR-006]**
- [ ] T026a [S] [US2] Generate `code/data/results/correlation_report.json`. **Logic**: Ensure p-values are included. **Depends on**: T021.
- [ ] T026b [S] [US2] Generate `code/data/results/baseline_metrics.json`. **Logic**: Ensure statistics are calculated over 50 folds. **Depends on**: T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Feature Importance and Statistical Significance (Priority: P3)

**Goal**: Identify feature importance and perform Paired Permutation Test to validate model differences.

**Independent Test**: Final report includes ranked feature importances and a p-value from the Paired Permutation Test.

### Implementation for User Story 3

- [ ] T030 [S] [US3] Implement `code/src/modeling.py` to train the **'Single Best Metric' Model** using the **same Repeated 5-Fold splits** as T023. **Input**: The 'Single Best Metric' name from T029b. **Logic**: Re-run the 10x5 CV loop using only the single best metric column. **Output**: Save aggregated prediction arrays to `code/data/results/predictions_single.json`. **Depends on**: T029b. **[FR-006]**
- [ ] T031 [S] [US3] Implement Paired Permutation Test in `code/src/analysis.py` comparing ROC-AUC distributions from T030 (Single Best) vs T023 (Full Set). **Null Hypothesis**: No difference in ROC-AUC distributions. **Test Statistic**: Difference in mean ROC-AUC. **Permutations**: A large number of iterations (shuffle labels, recalculate ROC-AUC difference). **Threshold**: alpha=0.05. **Prerequisite**: T000c (Constitution Update). **Output**: `code/data/results/statistical_significance_report.json` with keys: `p_value`, `permutation_seed`, `num_permutations`. **[FR-006]** **[SC-003]** **Depends on**: T030, T023.
- [ ] T032 [US3] Generate `code/data/results/feature_importance_ranking.json`.
- [ ] T033 [US3] Compile final `code/results/final_report.md` summarizing all findings. **Depends on**: T032, T031, T026. **Content**: Correlation table, baseline metrics, feature importance ranking, permutation test p-value, and visualization.
- [ ] T034 [US3] Implement `code/src/viz.py` to create bar chart of ROC-AUC scores and table of correlations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027b [P] [US3] Unit test for permutation test logic in `code/tests/test_analysis.py` (verify p-value calculation).
- [ ] T028 [P] [US3] Visualization test in `code/tests/test_viz.py` (verify bar chart generation).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 Code cleanup and refactoring (remove debug prints, ensure type hints).
- [ ] T039 [P] Additional unit tests for edge cases (empty projects, parsing errors) in `code/tests/unit/`.
- [ ] T0036 [S] Documentation updates: Add `quickstart.md` with instructions to run `code/run_pipeline.sh`. **Content Requirements**: Must include exact commands to run `code/run_pipeline.sh`, expected input/output paths, and error handling instructions. **Prerequisite**: T001c (run_pipeline.sh) must be functional. **Note**: Moved to Phase 5 to ensure script is functional before documentation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0.0)**: No dependencies - can start immediately (after T000a)
- **Setup (Phase 0.1)**: Depends on Phase 0.0 completion - BLOCKS all user stories
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 2+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution**: Integrated into core phases (see T004, T019, T021, T033).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs `features.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (needs model predictions)

### Within Each User Story

- Implementation MUST be written BEFORE tests
- Ingestion/Labeling before Metrics
- Correlation before Modeling
- Modeling before Significance Testing

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (after T000c)
- All Foundational tasks marked [P] (Metrics, Labeling) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement code/src/ingest.py logic..."
Task: "Implement code/src/metrics.py logic..."
Task: "Implement code/src/labeling.py logic..."

# Launch all tests for User Story 1 together (AFTER implementation):
Task: "Unit test for metric extraction logic in code/tests/test_metrics.py"
Task: "Unit test for labeling logic in code/tests/test_labeling.py"
Task: "Integration test for full ingestion pipeline in code/tests/test_pipeline.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0.0: Constitutional Compliance (T000a -> T000b -> T000c)
2. Complete Phase 0.1: Setup
3. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 2: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify `features.csv`)
6. Deploy/demo if ready

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
 - Developer A: User Story 1 (Ingest/Metrics)
 - Developer B: User Story 2 (Correlation/Modeling)
 - Developer C: User Story 3 (Significance/Viz)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential, must be done first
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint Check**: All tasks must run on CPU-only CI with a limited number of cores and memory.

The research question, method, and references remain unchanged as per the original planning document requirements. Do not use GPU-specific libraries or 8-bit quantization.
- **Statistical Note**: Execution is unblocked by T000a (Generate Deliverables) -> T000b (Human Wait) -> T000c (Verify Merge).
- **Data Integrity Note**: T004b and T019 ensure that no synthetic data is ever generated and memory limits are respected, adhering to the "Real data only" principle.
- **CV Note**: T023 and T030 strictly implement Repeated 5-Fold CV without nested selection, ensuring valid paired comparisons for FR-006.
- **Ordering Note**: T014b/c (Metric Extraction) now precede T017 (CSV Gen), which precede T018 (Validation). T030 depends on T029b.
- **Size Note**: T004b and T013 measure raw disk size directly, not file count.