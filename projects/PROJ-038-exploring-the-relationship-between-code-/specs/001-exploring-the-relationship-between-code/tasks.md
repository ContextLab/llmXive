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

- [X] T000a [S] Generate Constitution Amendment Deliverables. **Logic**: Generate the PR description and Sync Impact Report as artifacts for human submission. **Content**: The PR must include the proposed text change (replacing Pearson/McNemar with Point-Biserial/Permutation), scientific justification, and a `Sync Impact Report`. **Deliverable**: Files `amendment_pr_description.md` and `amendment_sync_impact_report.md`. **Note**: This task does NOT merge the PR; it prepares the artifacts for human submission. **Note**: This task unblocks T000b.
- [X] T000b [S] Check for Ratification. **Logic**: Poll for the existence of `amendment_ratified.md`. **Command**: Execute `code/scripts/wait_for_ratification.sh` (if exists) or check for file existence. **Timeout**: 2 hours. **Validation**: Exit code 0 if `amendment_ratified.md` exists; non-zero (and halt pipeline) if missing after timeout. **Note**: This task depends on T000a (artifacts generated) and requires human action.
- [X] T000d [S] Block until Ratified (Manual Trigger). **Logic**: This task represents the manual trigger point where the pipeline waits for the human to merge the PR. **Validation**: Confirms the pipeline is paused until human intervention is detected. **Note**: This task is a placeholder for the manual trigger mechanism.
- [X] T000c [S] Verify Constitution Update. **Logic**: Check that the Constitution file `projects/PROJ-038-exploring-the-relationship-between-code-/constitutions/FR-030.md` has been updated with the new Principle VI text and a version bump, matching the `amendment_ratified.md` marker. **Validation**: Grep for the exact string: "All comparative model evaluations MUST utilize Paired Permutation Tests to establish statistical significance of performance differences. Relationships between individual metrics and bug targets MUST be quantified using Point-Biserial and Spearman Rank Correlation tests." AND the version line "1.0.1". **Deliverable**: Exit code 0 on success, non-zero (and halt pipeline) if the amendment is not verified. **Note**: This task depends on T000b.

## Phase 0.1: Project Setup (Sequential, depends on 0.0)

**Purpose**: Create the physical directory structure and environment required for all subsequent tasks.

- [X] T001c [S] Create `code/` directory structure: `code/`, `code/src/`, `code/tests/`, `code/data/raw/`, `code/data/processed/`, `code/data/results/`. **Command**: `mkdir -p code/src code/tests code/data/raw code/data/processed code/data/results`. **Verification**: `ls -R code/` to verify all directories exist. **Deliverable**: Directory structure created.
- [X] T001g [S] Implement Time and Memory Limit Enforcement Wrapper. **Logic**: Create `code/run_pipeline.sh` with a `timeout 6h` wrapper and a system-level memory limit (hard-fail if >7GB RAM). **Deliverable**: `code/run_pipeline.sh` with both timeout and memory limit logic. **[SC-005]** **Depends on**: T001c. **Note**: Merges T001e and T001f logic into a single script to avoid parallel conflicts.
- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `pandas==2.1.0`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `tree-sitter==0.20.0`, `tree-sitter-java==0.20.0`, `pytest==7.4.0`, `lxml==4.9.0`, `javaparser-python==3.24.0`. (Note: `defects4j` CLI and PMD are installed separately in T002c).
- [X] T002b [P] Configure `code/pyproject.toml` with project metadata, entry points for scripts, and dependency groups.
- [X] T002c [P] Implement `code/setup_cli.sh` to install `defects4j` CLI tool and PMD (Java static analysis tool). **Exact Command**: `apt-get update && apt-get install -y openjdk-17-jdk=17.0.9+1 pmd-bin=7.0.0`. **Verification**: `defects4j --version` and `pmd --version`. **Note**: System packages must be pinned to ensure reproducibility. **[FR-001]** **[FR-002]**
- [X] T002f [P] Configure linting (flake8) and formatting (black) tools in `code/pyproject.toml` or separate config files.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Implement `code/src/config.py` to define environment variables for Defects4J path, fixed random seeds (seed=42), and memory limits. **[FR-005]**
- [X] T004b [S] Create and implement `code/src/ingest.py`. **Logic**: Skeleton with `NotImplementedError` removed. Implement logic to download Defects4J v2.0+ subset via CLI wrapper. **Algorithm**: Select projects alphabetically by project ID until cumulative **raw disk size** (measured via `du -sb` on the cloned repo directory) exceeds a substantial threshold. Include strict error handling to raise `DataFetchError` if CLI fails, ensuring NO synthetic fallback. **[FR-001]** **[SC-005]**
- [X] T005 [P] Define metric extraction interface in `code/src/metrics.py`: Specify function signatures for calculating Cyclomatic Complexity (via PMD CLI), Halstead Volume (via JavaParser-based custom script for Halstead Volume), and LOC. The interface must support both tools.
- [X] T007 [P] Create `code/data/processed/features.csv` schema validator and checksum generator (`code/data/checksums.json`). **[FR-001]**
- [X] T008 [P] Create skeleton `code/run_pipeline.sh` orchestration script to enforce execution order (Ingest -> Metrics -> Labeling -> Analysis), noting that Analysis scripts are not yet implemented.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Metric Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest a subset of Defects4J Java projects and compute a labeled feature matrix (metrics + bug label).

**Independent Test**: The pipeline produces a `features.csv` where rows = valid Java files, columns include metrics and binary target, with no nulls in numeric columns.

### Implementation for User Story 1

- [X] T013a [S] [US1] Implement Project Selection Logic. **Logic**: Select projects alphabetically by project ID until cumulative **raw disk size** exceeds 7GB. **Validation**: Log the selected project list and total size. **Deliverable**: List of selected projects in `code/data/selected_projects.txt`. **[FR-001]** **Depends on**: T004b.
- [X] T013 [S] [US1] Implement `code/src/ingest.py` logic to clone a representative sample of projects, filter for `.java` files, and enforce a bounded **raw disk size** limit via dynamic subset validation. **Logic**: Must `git checkout the specific bug-introduction commit` for each project before metric extraction. **Note**: This task completes the logic started in T004b and uses T013a's selection. **[FR-001]** **Depends on**: T013a.
- [X] T014b [P] [US1] Implement Python wrapper script for PMD CLI integration to calculate Cyclomatic Complexity for every Java file. **Exact CLI**: `pmd -f xml -d <dir> -rulesets rulesets/java/complexity.xml`. **Parsing Logic**: Parse PMD XML output using `lxml` and XPath `//violation[@complexity]`, sum the 'complexity' attribute of each tag to produce the integer Cyclomatic Complexity score. **Error Handling**: If a file cannot be parsed by PMD (syntax error) OR if the required ruleset file is missing, **log the file path, increment an `exclusion_count`, write a formatted error message to stderr and `exclusion.log`, and skip the file (do NOT halt)**. **Verification**: Explicitly verify that the ruleset calculates 'Cyclomatic Complexity' and not a proxy. **Prerequisite**: T000c (Constitution Update). **Depends on**: T013. **[FR-002]**
- [X] T014c [P] [US1] Implement `code/src/metrics/halstead.py` using **javaparser-python==3.24.0** to compute Halstead Volume. **Algorithm**: Parse Java AST, count operators (N1) and operands (N2), count unique operators (n1) and unique operands (n2). **Token Mapping**: Use standard Java token definitions as per the official JavaParser documentation (https://github.com/javaparser/javaparser/wiki/Token-Definitions). **Note**: `javaparser-python` invokes the canonical JavaParser library, satisfying the 'Java-compatible' constraint. **Error Handling**: If parsing fails, log the file path and skip it, raising a warning but not halting. **Prerequisite**: T000c (Constitution Update). **Depends on**: T013. **[FR-002]**
- [X] T015 [US1] Implement `code/src/labeling.py` logic to cross-reference commits with file changes to set `is_buggy` flag. **Input**: Defects4J commit JSON (schema: `{"commit_hash": "str", "files": ["str"]}`). **Output**: binary label. **Logic**: If file path in commit diff, set `is_buggy=1`, else `0`. **[FR-003]** **Depends on**: T013.
- [X] T016 [S] [US1] Implement exclusion logic in `code/src/ingest.py` for generated code/non-Java files with logging. **Logic**: Exclude files based on T013's filter and T015's labeling. **Dependency**: Must run after T015 to ensure labeling is complete before exclusion. **Deliverable**: Log exclusion reasons to `exclusions.log`. **[FR-001]** **Depends on**: T013, T015.
- [X] T017a [S] [US1] Merge Partial Outputs. **Logic**: Aggregate partial outputs from T014b, T014c, T015, and T016 into a single temporary file. **Mechanism**: Append to temporary files then sort by file path to prevent race conditions. **Deliverable**: `code/data/processed/features_raw.csv`. **Depends on**: T014b, T014c, T015, T016.
- [X] T017b [S] [US1] Generate `code/data/processed/features_raw.csv` with columns: `file_path`, `cc`, `halstead`, `loc`, `is_buggy`. **Depends on**: T017a. **[FR-001]**
- [X] T018 [S] [US1] Implement `validate_features()` function in `code/src/ingest.py`. **Logic**: Check for NaN values in metric columns (`cc`, `halstead`, `loc`). If NaNs found, **DROP the row** and log the count. **Deliverable**: Generate `code/data/processed/features_clean.csv` (cleaned) and `code/data/processed/exclusions.log` listing all dropped file paths and reasons **as a primary deliverable required for the Independent Test verification**. **Format**: CSV with columns `file_path`, `reason`, `original_metrics`. **Fail Condition**: If the resulting dataset is empty, raise a `DataIntegrityError` and halt the pipeline. **This step MUST run after T017b to ensure the final artifact meets the acceptance criteria.** **[FR-001]** **Depends on**: T017b. **Note**: 'Successfully processed' implies 'successfully processed AND metric extraction succeeded without nulls'.
- [X] T019 [S] [US1] Implement global memory monitoring in `code/run_pipeline.sh` (T001g) to track **aggregate** RAM usage periodically (at regular intervals or at major data load checkpoints) using `logging.info`. **Logic**: Use `psutil` to calculate the sum of the main process and any spawned child processes' RSS. **Frequency**: Log at regular intervals or at major checkpoints. **Fail Condition**: If logged aggregate memory > 7GB, raise `MemoryLimitExceeded` and exit 1. **[SC-005]** **Depends on**: T001c. **Note**: Runs in background during T013-T017.

### Phase 2b: Testing for User Story 1 (Sequential - Requires Implementation Complete)

> **NOTE**: These tasks MUST run AFTER T013-T019 are complete. They are marked [S] (Sequential) relative to the implementation phase to enforce the "Implementation before Test" dependency.

- [X] T010a [S] [US1] Unit test `test_cc_returns_int` in `code/tests/test_metrics.py` (mock Java file input). **Assertion**: `assert cc == 5` for a specific mock file. **Depends on**: T014b.
- [X] T010b [S] [US1] Unit test `test_halstead_returns_float` in `code/tests/test_metrics.py` (mock Java file input). **Assertion**: `assert halstead > 0`. **Depends on**: T014c.
- [X] T011a [S] [US1] Unit test `test_labeling_maps_commit_to_1` in `code/tests/test_labeling.py` (verify bug-introduction commit mapping). **Assertion**: `assert label == 1`. **Depends on**: T015.
- [X] T012a [S] [US1] Integration test `test_pipeline_shape` in `code/tests/test_pipeline.py` (verify `features.csv` shape and content). **Assertion**: `assert df.shape[0] > 0` and `assert 'is_buggy' in df.columns`. **Depends on**: T017b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Correlation Analysis and Baseline Modeling (Priority: P2)

**Goal**: Calculate correlations and train baseline models (Logistic Regression, Random Forest) using Repeated 5-Fold Cross-Validation.

**Independent Test**: Analysis script outputs a report with Point-Biserial/Spearman correlations and mean ROC-AUC/F scores from multiple folds.

### Implementation for User Story 2

- [X] T021 [S] [US2] Implement `code/src/analysis.py` to compute Point-Biserial and Spearman correlations with p-values. **Logic**: Must output both coefficient and p-value. **Implementation**: Use `scipy.stats.pointbiserialr` for binary target and `scipy.stats.spearmanr` for rank correlation. **Deliverable**: Generate `code/data/results/correlation_report.json` with the following EXACT schema:
```json
{
  "metrics": [
    {
      "name": "string (e.g., 'Cyclomatic Complexity')",
      "point_biserial_r": "float (6 decimal places)",
      "point_biserial_p": "float (6 decimal places)",
      "spearman_rho": "float (6 decimal places)",
      "spearman_p": "float (6 decimal places)"
    }
  ]
}
```
**Note**: The root key MUST be `metrics` containing a list of objects. All float values must be rounded to a fixed precision.. **Prerequisite**: T000c (Constitution Update). **[FR-004]**
- [X] T023 [S] [US2] Implement `code/src/modeling.py` to train Logistic Regression and Random Forest with **Repeated 5-Fold Cross-Validation (Multiple repeats, seed=42)** on the **Full Metric Set**. **Logic**:
 1. **Outer Loop**: Split data into multiple folds and repeat the process across several iterations to generate a comprehensive set of splits.
 2. **Model Training**: Train Logistic Regression and Random Forest on the **full set of metrics** (CC, Halstead, LOC) for each training split.
 3. **Evaluation**: Calculate ROC-AUC and F1-score on the test split.
 4. **Outputs**: Save aggregated prediction arrays for the 'Full Metric Set' models to `code/data/results/predictions_full.json`.
 **Deliverable**: `code/data/results/predictions_full.json` containing predictions for all 50 test splits. **[FR-005]** **[SC-002]**
- [X] T024 [S] [US2] Implement aggregation logic to calculate mean ROC-AUC and F-score with standard deviation across **all individual folds**. **Logic**: Aggregate the raw prediction arrays from T023 and compute statistics over the full set of 50 fold predictions. **Formula**: Compute the arithmetic mean and sample standard deviation of the 50 individual ROC-AUC values. **Deliverable**: Generate `code/data/results/baseline_metrics.json` with keys: `mean_roc_auc`, `std_roc_auc`, `mean_f1`, `std_f1`. **[FR-005]** **[SC-002]** **Depends on**: T023.
- [X] T025 [S] [US2] Handle class imbalance: Detect zero-buggy-file projects and log warnings/skip gracefully. **Strategy**: Skip project with warning if buggy count is zero. **Logic**: `if buggy_count == 0: logger.warning(...); continue`. **[FR-006]**
- [X] T029 [S] [US2] Implement `code/src/modeling.py` to extract feature importance weights from the trained Random Forest model (from T023) to identify the 'Single Best Metric'. **Aggregation**: **Calculate the mean importance across all 50 folds** (10 repeats * 5 folds). **Prerequisite**: T000c (Constitution Update). **[FR-007]** **[SC-004]** **Depends on**: T023.
- [X] T029b [S] [US2] Implement validation logic for 'Single Best Metric' selection and tie-breaking. **Logic**: If T029 finds multiple metrics with equal highest importance, select the one with the highest Point-Biserial correlation coefficient (from T021) as a tie-breaker. **Deliverable**: Generate `code/data/results/validation_report.md` confirming the selection logic is deterministic AND `code/data/results/single_best_metric.txt` containing the exact metric name. **Output Format**: Markdown with EXACT sections:
  - `## Selection Logic`: Describe the algorithm.
  - `## Tie-Breaker Used`: State if used and why.
  - `## Selected Metric`: The exact name of the metric (e.g., "Cyclomatic Complexity").
  - `## Deterministic Confirmation`: **Output the cryptographic hash of the concatenated string of all input feature importances and correlation values, plus the random seed used.** This proves the selection is reproducible. **Note**: The 'Single Best Metric' output of T029b is the **sole** input for T030 and T031. **Depends on**: T029, T021. **[FR-006]**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Feature Importance and Statistical Significance (Priority: P3)

**Goal**: Identify feature importance and perform Paired Permutation Test to validate model differences.

**Independent Test**: Final report includes ranked feature importances and a p-value from the Paired Permutation Test.

### Implementation for User Story 3

- [X] T030 [S] [US3] Implement `code/src/modeling.py` to train the **'Single Best Metric' Model** using the **same Repeated 5-Fold splits** as T023. **Input**: The 'Single Best Metric' name from `code/data/results/single_best_metric.txt`. **Logic**: Re-run the 10x5 CV loop using only the single best metric column. **Output**: Save aggregated prediction arrays to `code/data/results/predictions_single.json`. **Depends on**: T029b. **[FR-006]**
- [X] T031 [S] [US3] Implement Paired Permutation Test in `code/src/analysis.py` comparing ROC-AUC distributions from T030 (Single Best) vs T023 (Full Set). **Null Hypothesis**: No difference in ROC-AUC distributions. **Test Statistic**: Difference in mean ROC-AUC. **Permutations**: **10000 iterations** (shuffle labels, recalculate ROC-AUC difference). **Threshold**: alpha=0.05. **Seed**: 42. **Prerequisite**: T000c (Constitution Update). **Output**: `code/data/results/statistical_significance_report.json` with keys: `p_value`, `permutation_seed`, `num_permutations`. **[FR-006]** **[SC-003]** **Depends on**: T030, T023.
- [X] T032 [US3] Generate `code/data/results/feature_importance_ranking.json`.
- [X] T033a [S] [US3] Define final report structure. **Logic**: Define the exact Markdown structure for the final report. **Content**: Headers: 'Executive Summary', 'Correlation Analysis', 'Baseline Modeling', 'Feature Importance', 'Statistical Significance'. **Table Formats**: 
  - Correlation table columns: 'Metric', 'r_pb', 'Point-Biserial p', 'rho', 'Spearman p'.
  - ROC-AUC table columns: 'Model', 'Mean ROC-AUC', 'Std ROC-AUC'.
 **Deliverable**: `code/results/final_report_template.md`. **[FR-006]**
- [X] T033c [S] [US3] Generate `code/results/final_report.md` **Introduction** section. **Content**: Write the Executive Summary and Introduction text based on the `final_report_template.md`.
- [X] T033d [S] [US3] Generate `code/results/final_report.md` **Correlation Analysis** section. **Content**: Render the correlation table from `correlation_report.json` with exact headers: `Metric`, `r_pb`, `Point-Biserial p`, `rho`, `Spearman p`.
- [X] T033e [S] [US3] Generate `code/results/final_report.md` **Baseline Modeling** section. **Content**: Render the ROC-AUC table from `baseline_metrics.json` with exact headers: `Model`, `Mean ROC-AUC`, `Std ROC-AUC`.
- [X] T033f [S] [US3] Generate `code/results/final_report.md` **Statistical Significance** section. **Content**: Write the text block stating the `p_value` from `statistical_significance_report.json` and the conclusion.
- [X] T033g [S] [US3] Generate `code/results/final_report.md` **Feature Importance** section. **Content**: Render the ranked list from `feature_importance_ranking.json`.
**Deliverable**: A complete `final_report.md` assembled from these atomic parts. **[FR-006]**
- [X] T034 [US3] Implement `code/src/viz.py` to create bar chart of ROC-AUC scores and table of correlations. **Library**: `matplotlib`. **Figure Size**: Standard dimensions appropriate for the publication format. **Color Scheme**: Blue for 'Full Set', Orange for 'Single Best'. **Table Format**: Seaborn table. **Deliverable**: `code/results/roc_auc_comparison.png`. **[FR-006]**

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027b [P] [US3] Unit test for permutation test logic in `code/tests/test_analysis.py` (verify p-value calculation). **Assertion**: `assert 0.0 < p_value < 1.0`.
- [X] T028 [P] [US3] Visualization test in `code/tests/test_viz.py` (verify bar chart generation). **Assertion**: `assert os.path.exists('roc_auc_comparison.png')`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 Code cleanup and refactoring (remove debug prints, ensure type hints).
- [X] T039 [P] Additional unit tests for edge cases (empty projects, parsing errors) in `code/tests/unit/`.
- [X] T0036 [S] Documentation updates: Add `quickstart.md` with instructions to run `code/run_pipeline.sh`. **Content Requirements**: Must include exact commands to run `code/run_pipeline.sh`, expected input/output paths, and error handling instructions. **Prerequisite**: T001c (run_pipeline.sh) must be functional. **Note**: Moved to Phase 5 to ensure script is functional before documentation.

---

## Revision Tasks: Addressing Executability Concerns (R1)

**Purpose**: Resolve specific executability gaps identified in the R1 analysis report by adding missing schema definitions, exact file paths, and structural requirements.

### Revision: Clarifying Constitution Verification (T000c)

- [ ] T040 [S] [Rev] Refine T000c verification logic. **Logic**: Update the verification command in T000c to use an explicit, absolute path resolution for the Constitution file. **Command**: `grep -F "All comparative model evaluations MUST utilize Paired Permutation Tests to establish statistical significance of performance differences. Relationships between individual metrics and bug targets MUST be quantified using Point-Biserial and Spearman Rank Correlation tests." "$(find . -path '*/constitutions/FR-030.md')"`. **Validation**: Ensure the grep command fails if the exact string is not found in the file located at the project's root `constitutions/FR-030.md` or the specific project path. **Deliverable**: Updated `T000c` task description in the pipeline script to include this explicit path resolution and exact string match. **[concern executability-e4da3e7b]**

### Revision: Defining Correlation Report Schema (T021)

- [ ] T041 [S] [Rev] Implement strict schema validation for `correlation_report.json`. **Logic**: Create a JSON Schema file `code/data/contracts/correlation_report.schema.json` that strictly defines the `metrics` array, the object structure, and the data types (number) with `minimum` and `maximum` bounds for float precision (6 decimal places). **Implementation**: Update T021 to generate this schema file and use `jsonschema` library to validate the generated `correlation_report.json` before saving. **Deliverable**: `code/data/contracts/correlation_report.schema.json` and updated T021 logic that fails the pipeline if the output does not match the schema. **[concern executability-d1baf06f]**

### Revision: Specifying Validation Report Structure (T029b)

- [ ] T042 [S] [Rev] Enforce exact structure for `validation_report.md`. **Logic**: Update T029b to generate `code/data/results/validation_report.md` using a pre-defined template string that includes the exact headers and formatting. **Template**:
  ```markdown
  # Validation Report: Single Best Metric Selection

  ## Selection Logic
  [Description of the algorithm used to select the metric]

  ## Tie-Breaker Used
  [Yes/No] - [Reason if Yes]

  ## Selected Metric
  [Exact Metric Name]

  ## Deterministic Confirmation
  SHA-256 Hash: [Hash Value]
  Input Seed: 42
  ```
  **Validation**: Add a check to ensure the generated file contains these exact headers. **[concern executability-8d8e2651]**

### Revision: Decomposing Final Report Generation (T033)

- [ ] T043 [S] [Rev] Split T033 into atomic content generation tasks. **Logic**: Replace the coarse T033 task with the following atomic tasks:
  - [ ] T033c [S] [US3] Generate `code/results/final_report.md` **Introduction** section. **Content**: Write the Executive Summary and Introduction text based on the `final_report_template.md`.
  - [ ] T033d [S] [US3] Generate `code/results/final_report.md` **Correlation Analysis** section. **Content**: Render the correlation table from `correlation_report.json` with exact headers: `Metric`, `r_pb`, `Point-Biserial p`, `rho`, `Spearman p`.
  - [ ] T033e [S] [US3] Generate `code/results/final_report.md` **Baseline Modeling** section. **Content**: Render the ROC-AUC table from `baseline_metrics.json` with exact headers: `Model`, `Mean ROC-AUC`, `Std ROC-AUC`.
  - [ ] T033f [S] [US3] Generate `code/results/final_report.md` **Statistical Significance** section. **Content**: Write the text block stating the `p_value` from `statistical_significance_report.json` and the conclusion.
  - [ ] T033g [S] [US3] Generate `code/results/final_report.md` **Feature Importance** section. **Content**: Render the ranked list from `feature_importance_ranking.json`.
  **Deliverable**: A complete `final_report.md` assembled from these atomic parts. **[concern executability-6f2304e6]**

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
- **Revision (Phase 5)**: Integrated into core phases (see T040-T043) to resolve R1 concerns.

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

1. Complete Phase 0.0: Constitutional Compliance (T000a -> T000b -> T000d -> T000c)
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
- **Statistical Note**: Execution is unblocked by T000a (Generate Deliverables) -> T000b (Check for Ratification) -> T000d (Block until Ratified) -> T000c (Verify Update).
- **Data Integrity Note**: T004b and T019 ensure that no synthetic data is ever generated and memory limits are respected, adhering to the "Real data only" principle.
- **CV Note**: T023 and T030 strictly implement Repeated 5-Fold CV without nested selection, ensuring valid paired comparisons for FR-006.
- **Ordering Note**: T014b/c (Metric Extraction) now precede T017 (CSV Gen), which precede T018 (Validation). T030 depends on T029b.
- **Size Note**: T004b and T013 measure raw disk size directly, not file count.
- **Revision Note**: T040-T043 address the specific executability concerns raised in R1 regarding schema definitions, file paths, and report structures.