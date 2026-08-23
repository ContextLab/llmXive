# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Input**: Design documents from `/specs/001-phase-change-predictive-power/`
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
- [ ] T001b [P] Create code directories: `code/data`, `code/models`, `code/utils`.
- [ ] T001c [P] Create test directories: `tests/unit`, `tests/integration`, `tests/contract`.
- [X] T002 Initialize Python project with `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `numpy`, `matplotlib`, `requests`, `pyyaml` dependencies. **Deliverable**: Create `requirements.txt` pinning all versions.
- [ ] T003a [P] Configure linting in `pyproject.toml`: Add `[tool.black]` and `[tool.isort]` sections with standard project settings. **Deliverable**: `pyproject.toml` with valid configuration blocks.
- [ ] T003b [P] Configure formatting in `.flake8`: Create file with max-line-length=88 and ignore settings for flake8. **Deliverable**: `.flake8` file with valid configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `config.yaml` for API keys, random seeds, time/memory constraints, and `top_n` (with a note: "Research Decision Required: This value must be finalized in the research phase before final validation").
- [ ] T005 [P] Implement basic logging infrastructure and error handling in `code/utils/`
- [ ] T005a [US1] Implement `code/data/fetch_matbench.py`: Fetch the **Matbench Melting Points** dataset using the `matbench` Python package. **Constraint**: No fallback to synthetic data; if `matbench` fails to load, the script must raise a `FileNotFoundError` with a clear message. Save raw data to `data/raw/matbench_melting_points.json`. **Must run after T002**.
- [ ] T005b [US1] Implement `code/data/target_consistency_check.py`: A script to load the data from `data/raw/matbench_melting_points.json`, calculate the Pearson correlation between `melting_point` and `latent_heat` (if available in the dataset), and write the decision (`target: latent_heat` or `target: melting_point`) and coefficient to `data/results/target_decision.json`. **Must run after T005a**.
- [X] T006a [US1] Execute `code/data/target_consistency_check.py` to perform the Phase 0 Target Consistency Check. **Must run after T005b, T004, and T005**.
- [ ] T006b [US1] Define the JSON schema for `target_decision.json` in `contracts/target_decision.schema.yaml`. Keys: `target` (string), `coefficient` (float), `decision_rationale` (string), `target_override` (boolean, optional). **Must run before T007**.
- [ ] T006c [US1] Define the JSON schema for `fallback_decision.json` in `contracts/fallback_decision.schema.yaml`. Keys: `status` (string, enum: ["fallback_triggered"]), `reason` (string), `triggered_by` (string, task ID). **Must run before T013a**.
- [ ] T007 [US1] Create `contracts/dataset.schema.yaml` in YAML format. Must define a *superset* schema including both `latent_heat` and `melting_point` columns to accommodate dynamic target selection. **Must run after T006b**.
- [X] T007a [US1] Implement runtime validation logic in `code/utils/schema_validator.py`: A script that loads `data/results/target_decision.json` to determine the active target field name and validates the processed dataset against the static `dataset.schema.yaml`. **Logic**: The validator must explicitly check for the *presence* of the active target column and the *absence* (or null status) of the inactive one, enforcing the dynamic target constraint at runtime. **Must run after T007 and before T015**.
- [X] T008 Implement `code/utils/stability_checks.py` for NaN/Inf validation and memory monitoring
- [X] T009 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`. **Must run after T007**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Materials Data (Priority: P1) 🎯 MVP

**Goal**: Retrieve a curated subset of Materials Project data, compute elemental/structural descriptors, and prepare a clean dataset for modeling within 7GB RAM.

**Independent Test**: Execute the data retrieval script and verify that the output CSV contains at least 5,000 compounds with non-null values for melting point, latent heat (where available), and the computed feature columns, fitting within 7 GB RAM.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [US1] Integration test for data pipeline in `tests/integration/test_pipeline.py`. **Must run after T015** to ensure full pipeline implementation is complete.

### Implementation for User Story 1

- [ ] T011b [US1] Implement `code/data/compute_full_dataset.py`: Load the full Matbench dataset (or the largest feasible subset within RAM), handle missing values, and prepare for feature engineering. **Must run after T005a**.
- [ ] T011c [US1] Implement `code/data/validate_nist_overlap.py`: Check if the Matbench dataset contains compounds with `latent_heat` values that overlap with a potential NIST subset (if NIST data is available via a verified public CSV). **Conditional**: If NIST data is inaccessible or empty, log the state and proceed without computing an overlap count, triggering the fallback logic downstream. Save `nist_overlap_count.json` only if successful. **Must run after T011b**.
- [ ] T012 [US1] Implement `code/data/compute_descriptors.py` to: (1) Generate elemental descriptors (atomic number, electronegativity, radius), (2) Generate crystal graph representations using `pymatgen`'s `StructureGraph`, (3) Handle missing structures, NaN/Inf values, and memory constraints, and (4) Apply fallback logic based on `nist_overlap_count.json` (if exists) and `data/results/target_decision.json`. **Must run after T011b and T011c**.
- [ ] T014 [US1] Implement `code/utils/collinearity_utils.py` for Variance Inflation Factor (VIF) analysis to detect definitional dependencies (e.g., atomic radius vs ionic radius). **Must run after T012**.
- [ ] T015 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline (fetch -> feature engineering -> VIF check -> save processed CSV). **Must run after T007a**.
- [ ] T013 [US1] Implement `code/data/fetch_literature_pcm.py`: Fetch literature PCM data using a **cascading fallback strategy**: (1) Attempt to load a verified public CSV of known PCMs (e.g., from a NIST Webbook mirror or a curated GitHub repository); (2) If the public fetch fails or returns <50 samples, load a **pre-bundled, checksummed, and pre-mapped CSV** of 50 known PCMs located at `data/external/bundled_pcms_mapped.csv`. **CRITICAL**: The bundled CSV MUST be pre-mapped to MP IDs and contain valid target values. The script must always produce a valid, non-empty `data/external/literature_pcms_raw.csv` with a substantial number of rows. **Must run after T004**.
- [ ] T013a [US1] Implement `code/data/map_literature_pcm.py`: Map literature PCMs to Materials Project IDs using `pymatgen`. Read `data/results/target_decision.json` to determine the target variable (`latent_heat` or `melting_point`) and adapt mapping logic. Save mapped dataset to `data/external/literature_pcms_mapped.csv`. **Must run after T013 and T006a**. **Logic**: If the source is the bundled CSV (pre-mapped), skip mapping validation and copy directly. If the source is dynamic, enforce the mapping check. If the final mapped count is < 50 for dynamic sources, raise a critical error (pipeline must not proceed with insufficient validation data). Do NOT mutate `target_decision.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Baseline and Interpretable Models (Priority: P2)

**Goal**: Train Random Forest, Gradient Boosting, SHAP-analyzed trees, and PySR symbolic regression models on CPU within a constrained time window., ensuring R² > 0.0.

**Independent Test**: Run the training pipeline and verify that models achieve R² > 0.0 on the validation set and that symbolic regression terminates within 4 hours.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`

### Implementation for User Story 2

- [ ] T017a [US2] Implement `code/models/train_random_forest.py`: Train Random Forest model with fixed random seeds and memory constraints.
- [ ] T017b [US2] Implement `code/models/train_gradient_boosting.py`: Train Gradient Boosting model with fixed random seeds and memory constraints.
- [ ] T017c [US2] Implement `code/models/train_shap_analysis.py`: Perform SHAP analysis on the trained tree ensemble to generate ranked feature importances without GPU.
- [ ] T019 [US2] Implement `code/models/train_symbolic.py` using PySR with: Strict time budget of a few hours, Regularized feature set (post-VIF from T014), Logic to output at least one explicit mathematical formula. **Crucially**, save the best formula to `data/results/symbolic_formula.json` in a structured format. **If PySR fails to converge to a formula with R² > 0.0 after exhaustive retries with relaxed constraints, generate a 'SHAP-derived symbolic proxy'**: Construct a simplified linear formula using the top 3 SHAP features and their coefficients from the Random Forest/Gradient Boosting model. **Do NOT use Lasso as a fallback.** **Must run after T014**.
- [ ] T020 [US2] Implement `code/models/evaluate.py` to compute R² scores, perform paired t-tests between baselines and interpretable models (SC-002), and log performance metrics. **Ensure the exact same test split indices are used for both model types**.
- [ ] T021 [US2] Add logic to `code/models/evaluate.py` to flag limitations if PySR fails to converge (r < 0.0) and default to SHAP results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Governing Factors and Sensitivity (Priority: P3)

**Goal**: Validate derived rules against external literature PCMs, perform sensitivity analysis on thresholds, and finalize associational framing.

**Independent Test**: Apply derived rules to an external set of literature PCMs and performance drop ≤ 10% compared to test set; generate sensitivity analysis report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Integration test for validation pipeline in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T023a [US3] Implement `code/data/generate_validation_config.py`: Determine `top_n` for validation. **Logic**: Read `top_n` from `config.yaml`. **CRITICAL**: This value is a research parameter. If `config.yaml` contains the placeholder value (e.g., 10), set a flag `research_decision_required: true` in `data/results/validation_config.json` and log a warning that the final validation must be re-run with the empirically derived `top_n` from the research phase. Do NOT hard-code `min(10, total)`. **Must run after T013a and T019**.
- [ ] T023 [US3] Implement external validation logic in `code/models/validate_external.py`:
 - Load literature PCMs (from `data/external/literature_pcms_mapped.csv` or `data/external/literature_pcms_proxy.csv` via T013a/T013b).
 - Read `data/results/target_decision.json` to determine the target variable (`latent_heat` or `melting_point`). **If `data/results/fallback_decision.json` exists and `status: "fallback_triggered"`, use `melting_point` regardless of `target_decision.json`**.
 - Read `top_n` from `data/results/validation_config.json`.
 - Load derived symbolic rules from `data/results/symbolic_formula.json`. **Must explicitly check for the `status: "failed"` flag in the loaded JSON**. If `status: "failed"`, load the fallback artifact logic (or skip formula validation if no formula exists). **Must run after T013a and T019**.
 - Rank the **Top `top_n`** highest-value PCMs based on the target variable.
 - Calculate ranking accuracy on the Top `top_n`.
 - (SC-003).
 - Save results to `data/results/validation_results.json`.
- [ ] T024 [US3] Implement sensitivity analysis in `code/utils/stability_checks.py`: Sweep feature importance thresholds across the full valid range defined in `config.yaml` (default: low to medium sensitivity in incremental steps). Use the external validation set (`data/external/literature_pcms_mapped.csv` or `data/external/literature_pcms_proxy.csv`) as ground truth and `data/results/target_decision.json` for the target variable. Report false-positive/false-negative rates (FR-004, SC-004). Save report to `data/results/sensitivity_report.json`. **Must run after T013a and T019**.
- [ ] T025 [US3] Add final collinearity diagnostic in `code/utils/collinearity_utils.py` to flag any remaining definitional dependencies and adjust interpretation to descriptive/associational (FR-006).
- [ ] T026a [US3] Generate correlation analysis report section in `research.md` summarizing SC-001. **Report the outcome of the Phase 0 gate (which target was selected) and the Pearson coefficient that justified it**, replacing any '[deferred]' placeholders with measured values. **Read the coefficient explicitly from `data/results/target_decision.json`**. **Use `top_n` from `data/results/validation_config.json`**.
- [ ] T026b [US3] Generate model comparison report section in `research.md` summarizing SC-002 (R² comparison results and t-test). **Insert measured values from T020**.
- [ ] T026c [US3] Generate final report in `research.md` and `paper/` drafts that explicitly includes:
 - Generalization accuracy on literature set (SC-003) from `data/results/validation_results.json`.
 - Sensitivity analysis results (SC-004) from `data/results/sensitivity_report.json`.
 - **Explicit associational framing** (FR-007) stating findings are correlational, not causal. **Must read the exact text of the 'Assumptions' section from `plan.md` (specifically the bullet point about 'observational nature' and 'imputation bias') and inject it verbatim**.
 - **Insert measured values from previous steps**, replacing any '[deferred]' placeholders.
 - **Use `top_n` from `data/results/validation_config.json`**.
 - **Must run after T023 and T024**.
 - **Reads from plan.md**.
- [ ] T027 [US3] Run reproducibility check: Execute full pipeline end-to-end on a fresh runner to verify checksums and artifact hashes (Phase 3, Step 1).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. **Dependencies**: Depends on completion of US1, US2, and US3.

- [ ] T028 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T029 Code cleanup and refactoring (remove unused imports, optimize memory usage)
- [ ] T030 [P] Additional unit tests for descriptor computation and stability checks in `tests/unit/`
- [ ] T031 Run `quickstart.md` validation to ensure all steps are reproducible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data quality, memory usage)
5. Proceed to US2 only if US1 succeeds

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Validate data pipeline
3. Add User Story 2 → Test independently → Validate model training within time limits
4. Add User Story 3 → Test independently → Validate external generalization
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data pipeline)
 - Developer B: User Story 2 (Model training) - can start once US1 data is available
 - Developer C: User Story 3 (Validation) - can start once US2 models are available
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
- **CRITICAL**: All tasks must run on CPU-only free-tier CI (a limited number of cores, limited RAM, time-limited execution). No GPU, no 8-bit quantization, no large LLMs.
- **CRITICAL**: Use real data sources only (Matbench, NIST, literature DOIs, bundled CSVs). No synthetic/fake data generation.
- **CRITICAL**: Do not hard-code empirical values (like top-N counts or sweep ranges) unless explicitly derived from research or defined in the spec.
- **CRITICAL**: SC-003 requires `top_n` to be derived from the literature dataset size (min of 10 or total). Do not hard-code 10.
- **CRITICAL**: If PySR fails, use the 'SHAP-derived symbolic proxy' as the ultimate fallback; do NOT use Lasso or a 'failed' artifact.
- **CRITICAL**: If NIST data is missing, do not fail; log and proceed.
- **CRITICAL**: If literature mapping fails < 50 samples for dynamic sources, raise a critical error; do NOT proceed with insufficient data.
- **CRITICAL**: If the literature DOI is inaccessible or returns <50 samples, T013 must switch to the pre-mapped bundled fallback dataset immediately.
- **CRITICAL**: T013a must strictly enforce the >= 50 samples threshold for dynamic sources; any other failure mode in T013a (e.g., parsing errors) must raise an exception to prevent silent data corruption.
- **CRITICAL**: The sensitivity analysis in T024 must explicitly sweep the threshold range defined in `config.yaml` (default: a range from zero to a moderate upper bound in small increments) and must NOT hard-code the range in the script to ensure flexibility for future iterations.
- **CRITICAL**: All scripts reading `data/results/target_decision.json` must include a runtime check for the `target_override` flag (from `fallback_decision.json`) and must log a warning if the target is being forced to `melting_point` due to the fallback condition.
- **CRITICAL**: T007 must define a superset schema including both `latent_heat` and `melting_point` to accommodate dynamic target selection.
- **CRITICAL**: T026c must read the 'Assumptions' section from `plan.md` to ensure Single Source of Truth.
