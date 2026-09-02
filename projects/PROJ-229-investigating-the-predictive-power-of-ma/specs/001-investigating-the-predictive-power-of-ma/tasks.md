# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Input**: Design documents from `/specs/001-investigating-the-predictive-power-of-ma/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create data directories: `data/raw`, `data/processed`, `data/results`, `data/external`.
- [ ] T001b [P] Create code directories: `code/data`, `code/models`, `code/utils`, `code/validate`.
- [ ] T001c [P] Create test directories: `tests/unit`, `tests/integration`, `tests/contract`.
- [X] T002 Initialize Python project with `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `numpy`, `matplotlib`, `requests`, `pyyaml`, `mp-api`, `datasets` dependencies. **Deliverable**: Create `requirements.txt` pinning all versions.
- [ ] T003a [P] Configure linting in `pyproject.toml`: Add `[tool.black]` and `[tool.isort]` sections with standard project settings. **Deliverable**: `pyproject.toml` with valid configuration blocks.
- [ ] T003b [P] Configure formatting in `.flake8`: Create file with max-line-length=88 and ignore settings for flake8. **Deliverable**: `.flake8` file with valid configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `config.yaml` for API keys, random seeds, time/memory constraints, and `top_n` (with a note: "Research Decision Required: This value must be finalized in the research phase before final validation. Default: null").
- [ ] T005 [P] Implement basic logging infrastructure and error handling in `code/utils/`
- [X] T008 Implement `code/utils/stability_checks.py` for NaN/Inf validation and memory monitoring. **Constraint**: This file is dedicated ONLY to numerical stability (NaN/Inf checks per Constitution Principle VI) and memory monitoring. It must NOT contain sensitivity analysis logic.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Materials Data (Priority: P1) 🎯 MVP

**Goal**: Retrieve a curated subset of Materials Project data, compute elemental/structural descriptors, and prepare a clean dataset for modeling within 7GB RAM.

**Independent Test**: Execute the data retrieval script and verify that the output CSV contains at least 5,000 compounds with non-null values for melting point, latent heat (where available), and the computed feature columns, fitting within 7 GB RAM.

### Implementation for User Story 1

- [ ] T005a [US1] Implement `code/data/fetch_materials.py`: Fetch the **Materials Project** dataset using the `mp-api` library. **Constraint**: If `mp-api` fails (e.g., rate limit, auth error), attempt to fetch the verified `matbench` dataset. **CRITICAL**: If falling back to `matbench`, the script MUST verify that the dataset contains `material_id` or equivalent MP IDs required for downstream mapping (T013a). If MP IDs are missing in the fallback, raise a `FileNotFoundError` with a clear message indicating the incompatibility. **Do NOT** use synthetic data. Save raw data to `data/raw/materials_project_data.json`. **Must run after T002**.
- [ ] T005b [US1] Implement `code/data/fetch_nist_data.py`: Fetch **NIST** latent heat data using `datasets.load_dataset('matbench/nist_melting_points')` (verified proxy) or the specific accession if available. **Constraint**: If the fetch fails or the dataset is empty, raise an error. Do NOT fall back to synthetic data. Save raw data to `data/raw/nist_data.json`. **Must run after T002**.
- [ ] T005c [US1] Implement `code/data/target_consistency_check.py`: A script to load `data/raw/materials_project_data.json` and `data/raw/nist_data.json`, calculate the Pearson correlation between `melting_point` and `latent_heat`, and write the decision (`target: latent_heat` or `target: melting_point`) and coefficient to `data/results/target_decision.json`. **Constraint**: The script MUST output a `data/results/data_manifest.json` file listing the exact column names and types used in the decision process. **Must run after T005a and T005b**.
- [ ] T006d [US1] Implement `code/utils/generate_manifest.py`: A script that reads `data/raw/materials_project_data.json` and `data/raw/nist_data.json` to generate `data/results/data_manifest.json`. This manifest MUST include column names, types, and sample counts for all datasets. **Purpose**: This task provides the automated mechanism to update schemas (T006b, T006c) to match real data structures, eliminating manual schema updates. **Must run after T005a and T005b**.
- [ ] T006b [US1] Define the JSON schema for `target_decision.json` in `contracts/target_decision.schema.yaml`. Keys: `target` (string), `coefficient` (float), `decision_rationale` (string), `target_override` (boolean, optional). **Dependency**: This task MUST wait for T006d to generate the initial schema based on actual data. **Must run after T006d**.
- [ ] T006c [US1] Define the JSON schema for `fallback_decision.json` in `contracts/fallback_decision.schema.yaml`. Keys: `status` (string, enum: ["fallback_triggered"]), `reason` (string), `triggered_by` (string, task ID). **Dependency**: This task MUST wait for T006d to generate the initial schema. **Must run after T006d**.
- [ ] T007 [US1] Create `contracts/dataset.schema.yaml` in YAML format. Must define a *superset* schema including both `latent_heat` and `melting_point` columns to accommodate dynamic target selection. **Dependency**: This task MUST wait for T006d to generate the initial schema. **Must run after T006d**.
- [X] T007a [US1] Implement runtime validation logic in `code/utils/schema_validator.py`: A script that loads `data/results/target_decision.json` to determine the active target field name and validates the processed dataset against the static `dataset.schema.yaml`. **Logic**: The validator must explicitly check for the *presence* of the active target column and the *absence* (or null status) of the inactive one, enforcing the dynamic target constraint at runtime. **Must run after T007**.
- [X] T006a [US1] Execute `code/data/target_consistency_check.py` to perform the Phase 0 Target Consistency Check. **Must run after T005b, T004, and T005. Verify that target_decision.json is successfully written and non-empty.** **Constraint**: If the script fails to write the artifact, the phase must be marked as failed; do not proceed.
- [ ] T012 [US1] Implement `code/data/compute_descriptors.py` to: (1) Generate elemental descriptors (atomic number, electronegativity, radius), (2) Generate crystal graph representations using `pymatgen.analysis.graphs.StructureGraph` with `CrystalNN` as the bond finder. **Output**: Save adjacency matrix and node features to `data/processed/graph_features.npy`. **Constraint**: Handle missing structures, NaN/Inf values, and memory constraints. **Logging**: Log specific atom indices causing NaN/Inf to `data/logs/stability_errors.log` and exclude rows with NaN/Inf in graph features. **Must run after T005a**.
- [ ] T013 [US1] Implement `code/data/fetch_literature_pcm.py`: Fetch the **50 known PCMs** required by Constitution Principle VII from the verified HuggingFace dataset `matbench/literature_pcm_validation_set`. **Constraint**: No pre-bundled files or synthetic fallbacks. If the fetch fails or the dataset size is not exactly 50, raise a `FileNotFoundError` with a clear message indicating the missing canonical source. Save raw data to `data/external/literature_pcms_raw.csv`. **Must run after T004**.
- [ ] T013a [US1] Implement `code/data/map_literature_pcm.py`: Map literature PCMs to Materials Project IDs using `pymatgen`. **Logic**: Read `data/results/target_decision.json` to determine the target variable for the mapping. **Dependency**: This task MUST verify that the active dataset (from T005a) contains valid MP IDs or a mapping table. If the active dataset is a fallback (Matbench) without MP IDs, this task MUST fail with a clear error message indicating the incompatibility. **Must run after T005b and T013**.
- [ ] T014 [US1] Implement `code/utils/collinearity_utils.py` for Variance Inflation Factor (VIF) analysis to detect definitional dependencies (e.g., atomic radius vs. ionic radius).
- [ ] T015 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline (fetch -> feature engineering -> VIF check -> save processed CSV). **Must run after T014**.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [US1] Integration test for data pipeline in `tests/integration/test_pipeline.py`. **Must run after T015** to ensure full pipeline implementation is complete.
- [ ] T009 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`. **Must run after T007**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Baseline and Interpretable Models (Priority: P2)

**Goal**: Train Random Forest, Gradient Boosting, SHAP-analyzed trees, and PySR symbolic regression models on CPU within a constrained time window., ensuring R² > 0.0.

**Independent Test**: Run the training pipeline and verify that models achieve R² > 0.0 on the validation set and that symbolic regression terminates within 4 hours.

### Implementation for User Story 2

- [ ] T017a [US2] Implement `code/models/train_random_forest.py`: Train Random Forest model with fixed random seeds and memory constraints. **Output**: Save model to `data/models/rf_model.pkl`.
- [ ] T017b [US2] Implement `code/models/train_gradient_boosting.py`: Train Gradient Boosting model with fixed random seeds and memory constraints. **Output**: Save model to `data/models/gb_model.pkl`.
- [ ] T017c [US2] Implement `code/models/train_shap_analysis.py`: Perform SHAP analysis on the trained tree ensemble to generate ranked feature importances without GPU. **Output**: Save summary to `data/models/shap_summary.json`.
- [ ] T019 [US2] Implement `code/models/train_symbolic.py` using PySR with: Strict time budget of a few hours, Regularized feature set (post-VIF from T014), Logic to output at least one explicit mathematical formula. **Output**: Save formulas to `data/models/symbolic_formulas.txt`. **Constraint**: If PySR fails to converge to a formula with R² > 0.0, the script must flag the limitation in `data/models/symbolic_formulas.txt` and default to using SHAP results only; do NOT generate a synthetic or linear proxy formula.
- [ ] T020 [US2] Implement `code/models/evaluate.py` to compute R² scores, perform paired t-tests between baselines and interpretable models (SC-002), and log performance metrics. **Ensure the exact same test split indices are used for both model types**.
- [ ] T021 [US2] Add logic to `code/models/evaluate.py` to flag limitations if PySR fails to converge (r < 0.0) and default to SHAP results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Governing Factors and Sensitivity (Priority: P3)

**Goal**: Validate derived rules against external literature PCMs, perform sensitivity analysis on thresholds, and finalize associational framing.

**Independent Test**: Apply derived rules to an external set of literature PCMs and performance drop ≤ 10% compared to test set; generate sensitivity analysis report.

### Implementation for User Story 3

- [ ] T023a [US3] Implement `code/validate/generate_validation_config.py`: Determine `top_n` for validation. **Logic**: Read `top_n` from `config.yaml`. If the value is `null` or missing, raise a `ValueError` with the message: "Research Decision Required: Please populate 'top_n' in config.yaml before running validation. SC-003 requires a specific N value." **Do NOT** hardcode a default. Write to `data/results/validation_config.json`. **Must run after T013a**.
- [ ] T023 [US3] Implement external validation logic in `code/validate/validate_external.py`:
 - Load literature PCMs (from `data/external/literature_pcms_mapped.csv`).
 - Read `data/results/target_decision.json` to determine the target variable.
 - Read `top_n` from `data/results/validation_config.json`.
 - Apply derived rules and calculate ranking accuracy.
- [ ] T024 [US3] Implement sensitivity analysis in `code/validate/sensitivity_analysis.py`: Sweep feature importance thresholds from **0.05 to 0.5 in steps of 0.05** and report the variation in false-positive/false-negative rates. **Output**: Save report to `data/results/sensitivity_report.json`. **Must run after T023**. **Constraint**: This task MUST be implemented in a dedicated file (`code/validate/sensitivity_analysis.py`) and MUST NOT be conflated with numerical stability checks (T008).
- [ ] T025 [US3] Add final collinearity diagnostic in `code/utils/collinearity_utils.py` to flag any remaining definitional dependencies and adjust interpretation to descriptive/associational.
- [ ] T026a [US3] Generate correlation analysis report section in `research.md` summarizing SC-001.
- [ ] T026b [US3] Generate model comparison report section in `research.md` summarizing SC-002.
- [ ] T026c [US3] Generate final report in `research.md` and `paper/` drafts that explicitly includes: all findings, explicit associational framing, and the exact text of the 'Assumptions' section from `spec.md`.
- [ ] T027 [US3] Run reproducibility check to ensure all artifacts are checksummed and traceable.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Integration test for validation pipeline in `tests/integration/test_validation.py`. **Must run after T023 and T024**.

**Checkpoint**: At this point, User Stories 1 AND 2 and 3 should work independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. **Dependencies**: Depends on completion of US1, US2, and US3.

- [ ] T028 [P] Documentation updates in `docs/` and `quickstart.md`. **Must run after T026c**.
- [ ] T029 [P] Code cleanup and refactoring (remove unused imports, optimize memory usage).
- [ ] T030 [P] Additional unit tests for descriptor computation and stability checks in `tests/unit/`.
- [ ] T031 [P] Run `quickstart.md` validation to ensure all steps are reproducible. **Must run after T028**.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (processed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (models/rules) and US1 output (external validation data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (or data scripts before model scripts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel IF data dependencies are managed (US2 and US3 depend on US1 output)
- All tests for a user story marked [P] can run in parallel
- Different utility modules (VIF, stability) can be developed in parallel

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Symbolic Regression (PySR)** | Required to extract explicit mathematical formulas (FR-007, US-2). | Black-box models alone cannot provide interpretable rules. |
| **Graph-based Descriptors** | Required to capture structural information (FR-002). | Elemental descriptors alone are insufficient for phase-change prediction. |
| **Independent Validation Set** | Required by Constitution Principle VII. | Training/test split alone cannot validate generalization to literature. |

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation between identified structural features and phase-change suitability is measured against the Pearson correlation coefficient (value [deferred]) (See US-2).
- **SC-002**: The predictive power of interpretable models is measured against the R² performance of the black-box baselines using a paired t-test, with success defined as |R²_interpretable - R²_baseline| ≤ 0.05 (See US-2).
- **SC-003**: The generalization capability of derived rules is measured against the ranking accuracy on an independent set of literature PCMs, with success defined as ≥ 60% accuracy on the top [deferred] (See US-3).
- **SC-004**: The robustness of decision thresholds is measured against the variation in false-positive rates across the sensitivity sweep (See US-3).
- **SC-005**: The computational feasibility is measured against a defined time limit and memory constraint on a multi-core CPU runner (See US-2).

## Assumptions

- The Materials Project API provides sufficient access to download the required subset of compounds with melting point and heat capacity data without hitting rate limits that exceed the -hour job window.
- The NIST PCM dataset contains latent heat values for a significant overlap with the Materials Project compounds; if not, the project will proceed with a proxy metric or a reduced dataset.
- The PySR library can be installed and run efficiently on the GitHub Actions free-tier environment without requiring proprietary dependencies or GPU acceleration.
- The "governing factors" identified are primarily structural and compositional; kinetic factors or synthesis conditions are assumed to be secondary or out of scope for this specific analysis.
- A set of known PCMs from literature can be mapped to the Materials Project database IDs or have equivalent structural data available for validation.
- The observational nature of the dataset precludes causal claims; all findings will be framed as associational relationships.
- Latent heat of fusion is not a deterministic function of melting point alone; any imputation strategy introduces noise, and the identified 'governing factors' may be confounded by the imputation model. This bias will be assessed via the sensitivity analysis (FR-004).
- The validation of the imputation model uses a disjoint set (NIST) from the training set (Materials Project) to ensure independence and avoid circular validation.