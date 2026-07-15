# Tasks: Predicting Molecular Halide Binding Affinities with Machine Learning

**Input**: Design documents from `/specs/001-predicting-molecular-halide-binding-affinities/`
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

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `projects/PROJ-446-predicting-molecular-halide-binding-affi/` root directory (`mkdir -p projects/PROJ-446-predicting-molecular-halide-binding-affi`) <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T002 Create `code/` and `code/utils/` directories (`mkdir -p projects/PROJ-446-predicting-molecular-halide-binding-affi/code/utils`)
- [X] T003 Create `data/` and `docs/` root directories (`mkdir -p projects/PROJ-446-predicting-molecular-halide-binding-affi/{data,docs}`)
- [X] T004 Create `data/raw/`, `data/processed/`, `data/simulated/` and `docs/paper/` directories (`mkdir -p projects/PROJ-446-predicting-molecular-halide-binding-affi/data/{raw,processed,simulated} docs/paper`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Initialize Python 3.11 project with dependencies. **Create file at `code/requirements.txt`** with content: scikit-learn>=1.4.0, rdkit, pandas, numpy, requests, beautifulsoup4, pyyaml, pytest.
- [X] T006 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T007 [P] Implement configuration management (`code/utils/config.py`: random seeds, paths, solvent list)
- [X] T008 [P] Implement schema validators (`code/utils/validators.py`: `dataset.schema.yaml` validation logic)
- [X] T009 Create `code/utils/logger.py` with JSON format and rotating file handler for logging infrastructure.
- [X] T010 [P] Configure global error handling middleware and exception hooks in `code/utils/`.
- [X] T011 Create `state.yaml` artifact tracking hooks for content hashing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and filter experimental halide binding data from NIST/PubChem; fallback to simulated data if insufficient real data is found.

**Independent Test**: Can be fully tested by running the data pipeline on a small sample subset (or simulated data) and verifying the output CSV contains valid binding constants, halide identities, solvent tags, and molecular descriptors for ≥3 halides per host.

### Implementation for User Story 1

- [X] T012 [US1] Implement NIST/PubChem scraper (`code/01_data_ingestion.py`): Use `requests` with 2s delay, exponential backoff (max 3 retries), `BeautifulSoup` parsing. Filter for solvents: acetonitrile, chloroform, DCM. <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement data validation and cleaning (`code/01_data_ingestion.py`): Parse SMILES/InChI, exclude records with invalid structures or missing halide identities, standardize units (log K vs ΔG).
- [ ] T014 [US1] Implement host-halide filtering (`code/01_data_ingestion.py`): Retain only hosts with ≥3 different halide measurements (F⁻, Cl⁻, Br⁻, I⁻) for within-host comparison.
- [ ] T015 [US1] Implement molecular descriptor generation (`code/02_feature_engineering.py`): Generate ECFP fingerprints and RDKit descriptors (charge_density, cavity_volume) for all host molecules.
- [ ] T016 [US1] Implement Simulated Data Fallback (`code/01_data_ingestion.py`): Trigger if <50 hosts found. **Step 1:** Count occurrences of `halide_identity` in the available data and identify the most abundant halide (mode). **Step 2:** Generate data using `log K_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)` (RDKit calculated). **Step 3:** Store the identified most abundant halide in a config variable. **Step 4:** **Validate the generated DataFrame against `dataset.schema.yaml`**. **Step 5:** **Write the validated DataFrame to a temporary file `data/simulated/temp_simulated_data.csv` and write a state flag `SIMULATED_MODE=True` to `data/simulated/state.json`**. **Step 6:** Log specific warning: "WARNING: Insufficient data (<50 hosts). Comparative analysis aborted. Switching to single-halide prediction mode with simulated data." **Output:** Ensure the temp file and state flag are persisted.
- [ ] T017 [US1] Save processed dataset to `data/processed/halide_binding_data.csv` with schema compliance check. **Responsibility:** This task is the sole writer of the final CSV file. **Logic:** If `data/simulated/state.json` exists and `SIMULATED_MODE` is True, read the DataFrame from `data/simulated/temp_simulated_data.csv`. Otherwise, use the cleaned data from T014. Validate against schema and write to `data/processed/halide_binding_data.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (either with real or simulated data).

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with host-identity splitting to prevent data leakage.

**Independent Test**: Can be fully tested by training a random forest model on the preprocessed dataset and verifying that cross-validation produces R² and RMSE metrics without data leakage (i.e., same host molecule identity does not appear in both train and validation sets within a fold) and completes within the defined time/RAM limits.

### Implementation for User Story 2

- [X] T018 [US2] Implement host-identity stratified splitter (`code/03_model_training.py`): Ensure no host molecule appears in both train and validation sets within a fold.
- [X] T019 [US2] Implement Random Forest training (`code/03_model_training.py`): Use scikit-learn default hyperparameters, CPU-only, k-fold CV. Record R² and RMSE per fold.
- [X] T020 [US2] Implement Gradient Boosting training (`code/03_model_training.py`): Use scikit-learn default hyperparameters, CPU-only, k-fold CV. Record R² and RMSE per fold.
- [X] T021 [US2] Implement resource monitoring (`code/03_model_training.py`): Log peak RAM usage and runtime. **Verification:** Explicitly compare runtime against the 6-hour threshold and RAM against 7GB threshold defined in SC-003. **Fail** the task if either threshold is exceeded.
- [ ] T022 [US2] Save model run artifacts to `data/processed/model_runs.json` (includes model_type, folds, metrics, feature importances). **Dependency:** Must run after T019 and T020 complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data pipeline feeds model training).

---

## Phase 5: User Story 3 - Feature Importance Analysis and Visualization (Priority: P3)

**Goal**: Perform feature stability analysis and generate partial dependence plots to identify robust predictive determinants.

**Independent Test**: Can be fully tested by running feature stability analysis on a trained model and verifying the output includes a ranked list of top features with stability scores (coefficient of variation < 0.3), plus partial dependence plots for at least 2 key features.

### Implementation for User Story 3

- [X] T023 [US3] Implement feature stability analysis (`code/04_feature_analysis.py`): Run multiple bootstrap resamples, calculate coefficient of variation (CV) for the top features. Flag features with CV ≥ 0.3 as "unstable".
- [X] T024 [US3] Implement Partial Dependence Plot generation (`code/04_feature_analysis.py`): Generate plots for ≥2 key features (e.g., hydrogen-bond donor count, cavity size) across the halide series (F⁻→Cl⁻→Br⁻→I⁻).
- [X] T025 [US3] Implement Physical Plausibility Check (`code/04_feature_analysis.py`): **Logic:** Dynamically identify the **top feature** from the stability ranking. Verify that the sign of its coefficient aligns with first-principles electrostatics (e.g., if top feature is charge density, positive sign implies increased affinity; if top feature is cavity volume, verify sign aligns with steric expectations). If the sign contradicts the expected physical principle for that specific feature, flag as "physically implausible".
- [~] T026 [US3] Generate feature interpretation summary table mapping features to chemical hypotheses. **Dependency:** Must run after T023 and T025 complete.
- [ ] T027 [US3] Save analysis outputs to `data/processed/feature_analysis.json` and `docs/paper/figures/`.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: User Story 4 - Statistical Rigor & Reporting (Priority: P4)

**Goal**: Perform pairwise statistical comparisons using Bootstrap Confidence Intervals and generate final associational report.

**Independent Test**: Can be fully tested by running the comparison script on the cross-validation results and verifying the output report contains 95% confidence intervals for performance differences and an associational disclaimer.

### Implementation for User Story 4

- [X] T028 [US4] Implement Bootstrap Confidence Interval calculation (`code/05_statistical_reporting.py`): **Requirement:** MUST NOT use Paired Wilcoxon signed-rank test. **Algorithm:** Resample rows from the full measurement set a sufficient number of times to ensure statistical robustness. For each resample, compute the mean R² and RMSE for each halide group. Calculate the difference in means between halide pairs. Extract the lower and upper percentiles of the difference distribution to form the confidence interval.
- [X] T029 [US4] Implement power analysis check (`code/05_statistical_reporting.py`): Verify N ≥ 10 per halide group. **Output:** If N < 10 for any group, report the analysis as "underpowered" AND explicitly report the CI width as the string **"wide"** in the output JSON and report.
- [X] T030 [US4] Implement final report generation (`code/05_statistical_reporting.py`): Include explicit "associational, not causal" disclaimer. Flag differences ≥ 0.1 with 95% CI. **Requirement:** Explicitly document the exclusion of validated questionnaires/psychometric instruments (referencing Spec Assumptions) to explain why the "Verified Accuracy" gate for measurement validity does not apply.
- [X] T031 [US4] Handle "Simulated Data Mode" logic (`code/05_statistical_reporting.py`): **Logic:** Explicitly read `data/simulated/state.json`. If `SIMULATED_MODE` is True: (1) **Hard-abort** all comparative analysis (US-4) logic immediately; (2) Generate a warning log stating: "WARNING: Simulated Data Mode active. Project FAILS to answer the primary comparative research question."; (3) Write a report section explicitly stating the comparative analysis is unanswerable and aborted.
- [ ] T032 [US4] Save final report to `docs/paper/report.md` and summary stats to `data/processed/statistical_summary.json`.

**Checkpoint**: All user stories should now be independently functional and the final report generated.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T033 [P] Update `README.md`: Add a section describing the project goal, dependencies, and how to run the pipeline.
- [X] T034 [P] Update `docs/quickstart.md`: Add step-by-step instructions for setting up the environment and running the first task.
- [X] T035 [P] Update `docs/API.md` (or code docstrings): Ensure all public functions in `code/` have descriptive docstrings.
- [~] T036 Run `ruff check --fix` and `black` format on all `code/` files; ensure no lint errors remain.
- [~] T037 Performance optimization across all scripts (ensure CPU constraints met)
- [~] T038 Run quickstart.md validation to ensure reproducibility
- [X] T039 Update `state.yaml` with final artifact hashes

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US2/US3 metrics

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all data ingestion tasks for User Story 1 together:
Task: "Implement NIST/PubChem scraper"
Task: "Implement data validation and cleaning"
Task: "Implement host-halide filtering"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (check simulated data fallback if real data missing)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- **Critical Constraint**: All modeling must run on CPU-only CI with limited vCPU and RAM resources. No GPU/CUDA, no 8-bit/4-bit quantization, no large LLMs.
- **Critical Constraint**: If real data is insufficient, the pipeline MUST trigger the simulated data fallback (FR-011) and explicitly abort comparative analysis.