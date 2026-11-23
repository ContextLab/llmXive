# Tasks: llmXive follow-up: extending Intern-Atlas

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-intern-atlas/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: `mkdir -p projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/{code/data,code/utils,code/models,code/analysis,data/raw,data/processed,data/cache,tests/unit,tests/integration,paper/results,state}`. **Note**: Ensure `code/` and `data/` are direct subdirectories of the project root `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/`, not nested inside each other.
- [ ] T002 Initialize Python 3.11 project:
 1. Create `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/code/requirements.txt` with pinned versions of dependencies listed in the spec (pandas, numpy, scikit-learn, networkx, requests, pyyaml, seaborn, matplotlib, python-Levenshtein, statsmodels).
 2. Create a verification script or task to run `pip install -r code/requirements.txt` and confirm installation. **Source of truth**: The `requirements.txt` must exist at `code/requirements.txt` to support isolated virtualenv execution (Constitution Principle I).
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.
**⚠️ CRITICAL BLOCKING**: Phase 3 (User Stories) CANNOT START until ALL tasks in Phase 2 (T008a-c, T009a-c) are marked complete.

- [X] T004 [P] Create `code/utils/constants.py` defining constants for date ranges (recent years), edge types (`improves`, `replaces`, `extends`), and retraction label mappings (Robust, Fragile, Retraction-Only)
- [X] T005 [P] Create `code/utils/graph_utils.py` with helper functions for graph loading, edge filtering, and metadata validation
- [X] T007 [P] Configure environment configuration (`.env.example`) and logging infrastructure (`code/utils/logging_config.py`) with keys for `DATA_PATH`, `LOG_LEVEL`, `SEED`

### Data Model & Contracts (Split for Atomic Execution)

- [ ] T008a [P] Create `MethodNode` schema in `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/specs/001-llmxive-follow-up-extending-intern-atlas/data-model.md`. **Format**: Add a YAML block defining fields: `paper_id`, `title`, `year`, `outgoing_edges`, `incoming_citations`.
- [ ] T008b [P] Create `RetractionLabel` schema in `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/specs/001-llmxive-follow-up-extending-intern-atlas/data-model.md`. **Format**: Add a YAML block defining fields: `paper_id`, `status`, `source`, `retraction_reason`.
- [ ] T008c [P] Create `TopologicalFeatures` schema in `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/specs/001-llmxive-follow-up-extending-intern-atlas/data-model.md`. **Format**: Add a YAML block defining fields: `bottleneck_resolution_ratio`, `branching_entropy`, `citation_count`, `retraction_status_binary`.
- [ ] T009a [P] Create `dataset.schema.yaml` in `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/specs/001-llmxive-follow-up-extending-intern-atlas/contracts/`. **Content**: Define input/output CSV schema including `retraction_status_binary` (derived field from T016).
- [ ] T009b [P] Create `model.schema.yaml` in `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/specs/001-llmxive-follow-up-extending-intern-atlas/contracts/`. **Content**: Define model parameters and metrics schema.
- [ ] T009c [P] Create `output.schema.yaml` in `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/specs/001-llmxive-follow-up-extending-intern-atlas/contracts/`. **Content**: Define final report schema.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest Intern-Atlas graph and retraction databases to compute topological features and labels for nodes from a historical period.

**Independent Test**: The pipeline can be tested by running the extraction script on a small subset and verifying the output CSV contains computed features and correct binary labels.

### Tests for User Story 1 (Scaffolding - Parallel)

> **NOTE**: Create these test files first (empty or with placeholders) to define the interface. Execution happens after implementation.

- [X] T010 [P] [US1] Scaffold unit test file `tests/unit/test_feature_extraction.py` for edge type filtering logic (empty file creation)
- [X] T011 [P] [US1] Scaffold unit test file `tests/unit/test_graph_utils.py` for Levenshtein fuzzy matching logic (empty file creation)
- [X] T012 [P] [US1] Scaffold integration test file `tests/integration/test_pipeline.py` for full extraction pipeline on synthetic data (empty file creation)

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data/extract_intern_atlas.py`: Load graph, filter nodes by year (2010-2018), **import and call `abort_if_llm_inferred()` from `code/utils/graph_utils.py`** to enforce human-annotated edge types; if LLM-inferred types found, **ABORT immediately**. Handle missing edge types.
- [ ] T014 [P] [US1] Implement `code/data/compute_features.py`: Calculate `bottleneck_resolution_ratio` (improves/replaces edges / total outgoing) and `branching_entropy` (Shannon entropy of downstream method types); handle nodes with 0 outgoing edges gracefully
- [ ] T015 [US1] Implement `code/data/merge_retractions.py`: Map nodes to retraction databases using exact DOI match first, then fuzzy match using `python-Levenshtein.ratio` (ratio **>= 0.95**).
 - **NOTE: Plan Constraint Override**: The Plan.md Constraints section explicitly revises the threshold from FR-011's `>= 0.85` to `>= 0.95` for precision. This task implements the Plan constraint.
 - Implement duplicate resolution (earliest date, then alphabetical journal).
 - **Logging**: Log all nodes that fail the match threshold and the count of dropped nodes to ensure data loss is transparent.
 - **Depends on**: T009a-c (Schemas must exist for validation).
- [ ] T016 [US1] Implement label mapping logic in `code/data/merge_retractions.py` to assign label `1` (Fragile), `2` (Retraction-Only), or `0` (Robust) based on retraction reason (FR-004).
 - **Mapping Rules**: "methodological error" -> 1, "irreproducibility" -> 1, "fraud" -> 2, "other" -> 0.
 - **Output**: Preserve all three states in `data/processed/features_2010_2018.csv`.
 - **Depends on**: T009a-c.
 - **Test Coverage**: Write unit tests in `tests/unit/test_label_mapping.py` covering:
 - `test_label_mapping_methodological_error_returns_1`
 - `test_label_mapping_fraud_returns_2`
 - `test_label_mapping_robust_returns_0`
 - `test_label_mapping_irreproducibility_returns_1`
 - `test_binary_conversion_preserves_0_1` (Input status=0 -> Binary=0; Input status=1 -> Binary=1)
 - `test_binary_conversion_maps_2_to_0` (Input status=2 -> Binary=0)
 - **Binary Conversion**: Create a binary `retraction_status_binary` column (1=1, 0=0 or 2) for modeling, ensuring the original `retraction_status` (0,1,2) is preserved.
- [ ] T017 [US1] Implement main pipeline orchestrator in `code/data/run_extraction.py` to chain extraction, feature computation, and merging.
 - **CRITICAL**: This function MUST call T013-T016 logic.
 - **Pre-Check**: **Before** processing, verify the source retraction database contains entries for the 2010-2018 window. If the source is empty, **ABORT** immediately with the exact message: "No ground truth labels found for the specified time window; analysis cannot proceed."
 - **Validation**: Use `pandas.read_csv` to load the output file and assert `retraction_status_binary` is in `df.columns`. If not, ABORT.
 - **Output**: `data/processed/features_2010_2018.csv`.
 - **Depends on**: T016.
- [ ] T017b [US1] Validate contracts: Run schema validation on `data/processed/features_2010_2018.csv` against `specs/001-llmxive-follow-up-extending-intern-atlas/contracts/dataset.schema.yaml`.
 - **Abort if validation fails**.
 - **Depends on**: T017, T009a.

### Execution for User Story 1 (Sequential - After Implementation)

- [X] T018 [US1] Execute unit tests in `tests/unit/test_feature_extraction.py` (**Depends on**: T013)
- [ ] T019 [US1] Execute unit tests in `tests/unit/test_graph_utils.py` (**Depends on**: T005)
- [ ] T020 [US1] Execute integration tests in `tests/integration/test_pipeline.py` (**Depends on**: T017)
- [ ] T020b [US1] Execute unit tests in `tests/unit/test_label_mapping.py` (**Depends on**: T016)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train and compare topological vs. citation-only models to predict retraction status.
**Note**: Implements both Binary (FR-005/006) and 3-class (Exploratory) models.

**Independent Test**: The training script can be run with a fixed seed; output must show AUC-ROC for both models.

### Tests for User Story 2 (Scaffolding - Parallel)

- [ ] T021 [P] [US2] Scaffold unit test file `tests/unit/test_model_training.py` for data split logic (stratified time-based)
 - **NOTE**: Can run in parallel with T022, but requires T017b to be complete before execution.
- [ ] T022 [P] [US2] Scaffold integration test file `tests/integration/test_pipeline.py` for model training and evaluation
 - **NOTE**: Can run in parallel with T021, but requires T017b to be complete before execution.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/models/train_baseline.py`: Train **Binary Logistic Regression** using only `citation_count` and `publication_year` to predict `retraction_status_binary` (from T016).
 - **Note**: This is the baseline for the binary problem.
 - Ensure stratified time-based split (early period train, later period val) using `train_test_split` with `stratify=y` and `shuffle=False`.
 - **Depends on**: T017b (Data Validation).
- [ ] T023b [US2] Implement `code/models/train_topological_binary.py`: Train **Binary Logistic Regression** using only `bottleneck_resolution_ratio` and `branching_entropy` to predict `retraction_status_binary` (from T016).
 - **Depends on**: T017b (Data Validation).
- [ ] T023c [US2] Implement `code/models/train_baseline_multinomial.py`: Train **Multinomial (3-class) Logistic Regression** baseline using only `citation_count` and `publication_year` to predict the full `retraction_status` (0=Robust, 1=Fragile, 2=Retraction-Only).
 - **Note**: This task addresses FR-006 for the 3-class case, ensuring comparative analysis for the 'Retraction-Only' class is possible.
 - **Depends on**: T017b (Data Validation).
- [ ] T024 [US2] Implement `code/models/train_topological_multinomial.py`: Train **Multinomial (3-class) Logistic Regression** using only `bottleneck_resolution_ratio` and `branching_entropy` to predict the full `retraction_status` (0=Robust, 1=Fragile, 2=Retraction-Only).
 - **Note**: This is an exploratory extension to handle the 3-class nature of the label defined in FR-004, distinct from the binary focus of T023/T023b.
 - **DO NOT** collapse or ignore class 2. Output coefficients for all three classes.
 - **Depends on**: T017b (Data Validation), T023c (for comparative baseline).
- [ ] T025 [US2] Implement `code/models/evaluate.py`: Calculate AUC-ROC (One-vs-Rest for 3-class, Binary for others), Precision, Recall, F1 for **T023, T023b, T023c, and T024**.
 - Generate PR curves.
 - Compute delta metrics between Topological Binary (T023b) and Citation Baseline (T023), and Topological Multinomial (T024) and Citation Baseline Multinomial (T023c).
 - Save results to `data/processed/model_results.json`.
 - **Depends on**: T023, T023b, T023c, T024.
- [ ] T026 [US2] Implement comparison logic to report if topological model provides independent predictive power over citation baseline for the binary problem.

### Execution for User Story 2 (Sequential - After Implementation)

- [ ] T027 [US2] Execute unit tests in `tests/unit/test_model_training.py`
- [ ] T028 [US2] Execute integration tests in `tests/integration/test_pipeline.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform permutation tests and threshold sweeps to ensure findings are not spurious.

**Independent Test**: The robustness script generates a distribution of AUC scores from permuted labels; result must show observed AUC significantly exceeds the mean of permuted distributions.

### Tests for User Story 3 (Scaffolding - Parallel)

- [ ] T029 [P] [US3] Scaffold unit test file `tests/unit/test_robustness.py` for permutation test logic
- [ ] T030 [P] [US3] Scaffold unit test file `tests/unit/test_robustness.py` for collinearity diagnostics (VIF/MI)

### Implementation for User Story 3

- [ ] T031a [US3] Implement `code/analysis/standard_permutation.py`: Perform **Standard Permutation Test** with **exactly n=100 iterations** (as per FR-007) on the **Binary Model (T023b)** results by shuffling labels. Set `random_seed=42` before shuffling. Compare observed AUC to permuted distribution.
 - **Depends on**: T023b.
- [ ] T031b [US3] Implement `code/analysis/stratified_permutation.py`: Perform **Stratified Permutation Test** with **n=100 iterations** on the **3-class Model (T024)** results, controlling for `field_of_study` and `publication_venue`. Set `random_seed=42` before shuffling.
 - **Depends on**: T024.
- [ ] T031c [US3] Implement `code/analysis/method_comparison.py`: **Compare and Select** between the results of T031b (Stratified Permutation) and T034 (Covariate Adjustment).
 - **Logic**: Evaluate both methods on stability and interpretability. If both pass, document the choice. If one fails, select the other. This task resolves the "OR" in FR-012 by defining a selection logic.
 - **Output**: A report section in `data/processed/method_selection_report.json` stating which method was selected and why.
 - **Depends on**: T031b, T034.
- [ ] T032 [US3] Implement `code/analysis/sensitivity_analysis.py`: Run threshold sweep over the **specific set {0.3, 0.5, 0.7}** (as per FR-008 and SC-002); calculate and report FPR/FNR for each; calculate VIF and MI for predictors; flag instability if VIF > 5 or MI > 0.1.
 - **Depends on**: T023b, T024.
- [ ] T033 [US3] Implement structural coupling diagnostic: If VIF > 5, re-run model with single predictor or composite metric and report as sensitivity analysis
- [ ] T034 [US3] Implement covariate adjustment: **Mandatory Execution**. Run Logistic Regression with `field_of_study` and `publication_venue` as covariates to control for confounding variables (as per FR-012).
 - **Note**: This task runs **in parallel** with T031b to provide an additional robustness check. It is NOT conditional on T031b failure.
 - **Depends on**: T024.

### Execution for User Story 3 (Sequential - After Implementation)

- [ ] T035 [US3] Execute unit tests in `tests/unit/test_robustness.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Artifact Generation (Polish)

**Purpose**: Generate final results and update `research.md`.

- [ ] T036 [P] Aggregate metrics from `model_results.json` and sensitivity analysis outputs into `data/processed/final_metrics_summary.csv`
- [ ] T036a [P] **Archive the full 3-state `retraction_status` column distribution** (counts for 0, 1, 2) into `results/metrics.yaml` under a `label_distribution` section to ensure the 'Retraction-Only' (2) category is preserved in the final audit trail. **Depends on**: T016/T016b.
- [ ] T036b [US3] **Calculate Significance**: Compute the p-value and the boolean result of the significance test (observed AUC > mean_permuted + 2*std) from T031a/T031b. Record these metrics in `data/processed/final_metrics_summary.csv` and `results/metrics.yaml` to ensure SC-003 is machine-verifiable.
 - **Depends on**: T031a, T031b.
- [ ] T037 [US3] Generate plots: Save PR curve to `data/processed/plots/pr_curve.png`, Permutation distribution to `data/processed/plots/permutation_dist.png`, and **Threshold sensitivity plot to `data/processed/plots/threshold_sweep.png` (MUST explicitly label points {0.3, 0.5, 0.7} on x-axis, include legend for FPR/FNR values from `threshold_sweep_metrics.json`, and use `matplotlib.pyplot` with `dpi=300` resolution as per SC-002)**. **Depends on**: T032.
- [ ] T038 [US3] Generate final report to `specs/001-llmxive-follow-up-extending-intern-atlas/research.md` including sections: Methodology, Results (citing `data/processed/final_metrics_summary.csv`), and Limitations.
- [ ] T038b [US3] Verify report: Check that `research.md` exists and contains at least 3 specific metrics from `data/processed/final_metrics_summary.csv` (AUC, VIF, FPR/FNR).
- [ ] T039 [P] Review and update `data-model.md` and `contracts/` in `specs/001-llmxive-follow-up-extending-intern-atlas/` if implementation diverged from initial schema (if not caught by T017b/T025b/T034).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**. Phase 3 cannot start until T008a-c and T009a-c are complete.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs processed features)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained models)
 - **T031a, T031b, T032, T034 explicitly depend on T023b/T024** (Model artifacts)

### Within Each User Story

- Tests (Scaffolding) MUST be created FIRST (parallel)
- Implementation follows
- Test Execution follows Implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **T017 (Orchestrator)**: MUST run strictly after T016 completion to ensure binary column availability.
- **T023, T023b, T023c, T024**: MUST run after T017b completes.
- **T034 (Covariate Adjustment)**: MUST run after T024 completes (Parallel with T031b).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T008a-c, T009a-c) can run in parallel (within Phase 2)
- Test Scaffolding tasks within a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (only after US1 data is ready for US2/US3)

---

## Parallel Example: User Story 1

```bash
# Launch all test scaffolding for User Story 1 together:
Task: "Scaffold unit test file tests/unit/test_feature_extraction.py"
Task: "Scaffold unit test file tests/unit/test_graph_utils.py"

# Launch core implementation tasks in parallel (different files):
Task: "Implement code/data/extract_intern_atlas.py"
Task: "Implement code/data/compute_features.py"
# T015, T016 must wait for T009a-c (Phase 2)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Pipeline)
4. **STOP and VALIDATE**: Test extraction on synthetic data; verify CSV output matches schema
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Data Pipeline)
3. Add User Story 2 → Test independently → Deploy/Demo (Modeling)
4. Add User Story 3 → Test independently → Deploy/Demo (Robustness)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Extraction)
 - Developer B: User Story 2 (Modeling) - *Note: Can start once US1 data schema is defined, but needs actual data output to run fully*
 - Developer C: User Story 3 (Robustness) - *Note: Needs US2 models to run*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Ensure the system aborts with the exact error message if ground truth is missing; no synthetic fallback is allowed.
- **Critical**: Ensure edge types are strictly human-annotated; exclude any LLM-inferred edges to prevent semantic leakage.
- **Critical**: Ensure permutation tests are stratified by field/venue to control confounding (T031b) AND standard permutation (T031a) is run.
- **Critical**: Ensure the retraction-only label (2) is preserved in the model as a distinct class (3-class multinomial) in T024, while T023b uses the binary collapsed label.
- **Critical**: Ensure T034 runs unconditionally as a parallel robustness check, not just as a fallback.
- **Critical**: Ensure T017 explicitly quotes the required abort error message and validates the source database.
- **Critical**: Ensure T015 uses Levenshtein ratio >= 0.95 as per Plan.md Constraints (override of FR-011) and logs unmatched nodes.
- **Critical**: T023, T023b, T023c, and T024 are NOT parallel relative to T017b; they must wait for data validation. T021 and T022 are parallel relative to each other but also depend on T017b.
- **Critical**: T031c must compare T031b and T034 to resolve the "OR" in FR-012.