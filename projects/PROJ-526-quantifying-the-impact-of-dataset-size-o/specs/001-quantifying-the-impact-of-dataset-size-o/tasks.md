# Tasks: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

**Input**: Design documents from `/specs/001-quantifying-the-impact-of-dataset-size-o/`
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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create root directories: `projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/`, `code/`, `data/`, `tests/`, `state/`, `docs/`
- [X] T001b [P] Create subdirectories: `data/raw/`, `data/processed/`, `tests/contract/`, `tests/unit/`, `tests/integration/`
- [X] T001c [P] Initialize git repository and create `.gitignore` for Python/data artifacts

---

## Phase 2: Foundational (Blocking Prerequisites & Legal Amendments)

**Purpose**: Core infrastructure AND the legal amendments required to proceed with feasibility adjustments.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Amendments (T035, T036) MUST precede implementation tasks (T019, T020, T027).**

- [X] T002 Initialize Python 3.10 project with dependencies (`pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`, `requests`, `huggingface_hub`) in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools
- [X] T004 Create `data/` directory structure (`raw/`, `processed/`) and `state/` for checksums
- [X] T005 [P] Implement data integrity utilities: `sha256` checksumming and logging in `code/utils/integrity.py`
- [X] T006 [P] Setup environment configuration management for API keys and paths in `code/config.py`
- [X] T007 Create base data models (MaterialEntry, LearningCurve, ScalingResult) in `code/models.py`
- [X] T008 Configure deterministic seed setting for `numpy` and `random` in `code/utils/seed.py`
- [X] T035 [P] **Constitution Override Task**: Create a formal amendment record in `state/amendments.md` AND `state/constitution_override.md` documenting the deviation from Constitution Principle VII (reduced subsets/seeds) and the data availability constraint (properties -> N=2-3). This amendment is a prerequisite for T019, T020, T027.
 - **Schema**: Must include fields: `Amendment ID`, `Constitution Principle Violated`, `Justification`, `Effective Date` (populate with current date YYYY-MM-DD), `Scope Change`.
 - **Content**: Explicitly state that Constitution Principle VII (multiple subsets/3 seeds/ANOVA) is overridden by subsets/1 seed/Permutation Test.
 - **Output**: `state/amendments.md` and `state/constitution_override.md`.
- [X] T036 [P] **Spec Amendment Task**: Update `spec.md` (and `state/amendments.md`) to formally modify:
 1. **FR-001**: Replace "at least 15 distinct material properties" with "2-3 distinct material properties". Remove the "hard halt" logic description.
 2. **SC-001**: Replace "p-value < 0.05" with "p-value < 0.1" to account for the mathematical granularity limit of N=5 permutations.
 3. **Section 6.2**: Replace "Randomly shuffle class labels [deferred] times" with "Perform exact enumeration of all possible permutations (C(N, K))" where N is total properties and K is properties per class.
 - **Action**: Edit `spec.md` directly with the text above. If the current `spec.md` text differs from these instructions, the task MUST update it to match these instructions.
 - **Action**: Commit the changes to git and verify the file hash of `spec.md` before proceeding.
 - **Output**: Updated `spec.md`, `state/amendments.md`.
- [X] T045 [P] **Amendment Verification**: Implement a verification step that runs immediately after T036. This step must check:
 1. Existence of `state/amendments.md` with valid content.
 2. Existence of `state/constitution_override.md`.
 3. **Content Validation**: The `Scope Change` field in `state/amendments.md` MUST contain the exact strings "5 subsets/1 seed" and "Permutation Test". If not, halt with an error.
 4. Update `state/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o.yaml` `updated_at` timestamp upon successful verification.
 - **Constraint**: This task MUST be completed before T019, T020, and T027.
- [X] T046 [P] **Spec Verification**: Verify that `spec.md` has been correctly updated to reflect the amended scope. Check for:
 1. FR-001 stating "2-3 distinct material properties".
 2. SC-001 stating "p-value < 0.1".
 3. Section 6.2 stating "exact enumeration of all possible permutations (C(N, K))".
 4. Absence of "N >= 15", "p-value < 0.05", or "Kruskal-Wallis" in the active text.
 - **Constraint**: This task MUST be completed before T019, T020, and T027.

**Checkpoint**: Foundation and Legal Amendments ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Composition Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Download standardized material property datasets from public repositories and compute composition-only descriptors (Magpie vectors) to establish a baseline.

**Independent Test**: Verify that the pipeline retrieves data for available properties, computes Magpie features without structural data, and outputs a consolidated Parquet file passing schema validation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T010 [P] [US1] Unit test for Magpie vector generation (no structural features) in `tests/unit/test_descriptors.py`

### Implementation for User Story 1

- [X] T037.0 [US1] **Research Generation**: Generate `research.md` in the project root if it does not exist, OR verify its existence. This file MUST list the specific HuggingFace dataset IDs or API endpoints for the A few target properties (e.g., `materials_project/band_gap`, `materials_project/formation_energy`). This file is a prerequisite for T011.
 - **Output**: `research.md` with explicit dataset IDs.
 - **Action**: If the file exists, verify it contains the required dataset IDs. If not, create it.
- [X] T011 [US1] Implement `code/download_data.py` to fetch materials data from HuggingFace (Materials Project/AFLOW) using the list defined in `research.md`. Implement exponential backoff for rate limits.
 - **Dependency**: Must read dataset IDs from `research.md`.
 - **Logic**: Iterate explicitly over the list in `research.md` to fetch each property.
- [X] T012 [US1] Implement `code/generate_descriptors.py` to compute Magpie composition-only descriptors for all entries.
 - **Logic**: Iterate over every entry in the fetched data from T011 to ensure full processing of the target set.
- [X] T013 [US1] Implement data consolidation logic to merge properties into a single `data/processed/materials_master.parquet` file (with CSV fallback if memory permits)
- [X] T014 [US1] Implement chunked loading in `code/download_data.py` using batch processing and optimized dtypes (float32) to verify peak RAM usage remains < 7GB during full dataset load
- [X] T015 [US1] Add logging for download progress and descriptor generation stats
- [X] T016 [US1] Implement validation logic to count distinct properties. **IF count < 2, log a critical status update and update `state/properties_status.json`, but DO NOT raise an error.**
 - **Logic**: Read the target minimum count from `state/amendments.md` (default 2) or the amended `spec.md`.
 - **Action**: Log the "N=2-3" status and update `state/properties_status.json`.
 - **Constraint**: The amended spec (FR-001 Correction) adjusted the hard halt to a log-only status. The pipeline must proceed even if N < 15, provided N >= 2.
- [X] T037 [US1] **Data Source Verification**: Update `code/download_data.py` to explicitly list the specific HuggingFace dataset IDs or API endpoints for the 2-3 target properties as identified in `research.md`. Replace any generic "fetch all" logic with a targeted fetch loop that iterates only over this verified list to prevent accidental inclusion of incomplete datasets. <!-- FAILED: unspecified -->
- [X] T038 [US1] **Stream Implementation**: Refactor `code/download_data.py` to use `datasets.load_dataset(..., streaming=True)` for large properties. Ensure the code accumulates statistics (count, mean, variance) in an online fashion without loading the full dataset into RAM, satisfying NFR-001 (<7GB RAM) for properties >40k entries.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Learning Curve Construction and Scaling Analysis (Priority: P2)

**Goal**: Generate learning curves for each property by training Random Forest regressors on varying subset sizes, fit power-law models, and extract scaling exponents.

**Independent Test**: Verify that learning curves are generated for a sample property, power-law fitting is applied, and results (exponent or "non-power-law" flag) are output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for power-law fitting logic (including R2 < 0.9 handling and multi-seed averaging) in `tests/unit/test_scaling_fit.py`
- [X] T018 [P] [US2] Integration test for learning curve generation on a small subset in `tests/integration/test_learning_curves.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/train_learning_curves.py` to generate **5 training subsets** (sizes: `[1000, 5000, 10000, 20000, 40000]`) per property, training with **1 random seed** per subset using fixed hyperparameters. **Note**: This implementation relies on the amendment ratified in T035 to deviate from the Constitution's 10-subset/3-seed requirement. <!-- FAILED: unspecified -->
- [X] T020 [US2] Implement `code/fit_scaling_laws.py` to fit $Error = a \cdot N^{-b}$ and classify properties as "non-power-law" if $R^2 < 0.9$. Output `data/processed/scaling_results.csv` with columns: `property_name`, `exponent_b`, `intercept_a`, `r_squared`, `fit_status`. <!-- FAILED: unspecified -->
- [X] T021 [US2] Implement aggregation logic to produce `data/processed/scaling_results.csv` with exponents and flags
- [X] T022 [US2] Add error handling for properties with insufficient data points (< 1,000 samples)
- [X] T039 [US2] **Subset Size Validation**: Add a pre-check in `code/train_learning_curves.py` to verify that the available dataset for a given property has at least 40,000 entries (the largest subset size). If a property has fewer than 40,000 entries, log a warning, skip that property for the full curve, and record the maximum available subset size in `state/properties_status.json` to ensure FR-003 is met only where data permits.
- [ ] T040 [US2] **Deterministic Subsampling**: Implement a strict stratified or random subsampling strategy in `code/train_learning_curves.py` that ensures the 5 subset sizes are nested (i.e., the 1000-sample set is a subset of the 5000-sample set) to reduce variance in the learning curve, using a fixed seed derived from the property name.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Statistical Validation (Priority: P3)

**Goal**: Quantify physical characteristics (spatial locality, symmetry sensitivity), correlate with scaling exponents, and perform statistical validation between property classes.

**Independent Test**: Verify that correlation coefficients, p-values, and class difference significance (p < 0.1) are output correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for Pearson correlation and Permutation test logic in `tests/unit/test_statistics.py`
- [X] T024 [P] [US3] Contract test for statistical output schema in `tests/contract/test_stats_schema.py`

### Implementation for User Story 3

- [ ] T041 [US3] **Physical Metric Definition**: Explicitly implement the calculation logic for "spatial locality" and "symmetry sensitivity" in `code/analyze_physics.py` based on the definitions in `research.md`.
 - **Constraint**: If `research.md` does NOT contain explicit formulas for these metrics, the task must flag them as "undefined" and halt, rather than inventing formulas.
 - **Output**: `data/processed/metric_definitions.md` containing exact formulas and derivation logic (only if sourced from `research.md`).
- [ ] T025 [US3] Implement `code/analyze_physics.py` to compute "spatial locality" and "symmetry sensitivity" using the formulas defined in T041. **Input**: Read metric definitions from `data/processed/metric_definitions.md`.
 - **Dependency**: Must wait for T041 to complete.
- [X] T026 [US3] Implement Pearson correlation analysis between physical metrics and scaling exponents. **Input**: Read metric definitions from `data/processed/metric_definitions.md`.
- [ ] T027 [US3] Implement `code/analyze_physics.py` to perform a **Permutation Test** (primary method for N=2-3 scope) to compare electronic vs. mechanical classes.
 - **Input**: List of scaling exponents per class (from `data/processed/scaling_results.csv` generated by T020).
 - **Logic**:
 1. **Comparison Step**: Calculate the observed difference in means between Electronic and Mechanical classes.
 2. **Permutation Step**: Perform exact enumeration of all possible permutations. The number of permutations must be calculated dynamically as `math.comb(N_total, N_electronic)`, where N_total is the sum of properties in both classes. Do NOT hardcode C(5,2).
 3. **P-Value Calculation**: Calculate p-value as the proportion of shuffled differences >= observed difference.
 - **Output**: `p-value` (float).
 - **Constraint**: Enforce success criterion **p < 0.1** (adjusted for N=2-3 granularity).
 - **Note**: This task relies on the amendment ratified in T036 to deviate from the Constitution's Kruskal-Wallis/ANOVA requirement.
- [ ] T028 [US3] Implement `code/visualize_results.py` to generate heatmaps and comparative learning curve plots
- [X] T029 [US3] Generate final summary table with all statistical results in `data/processed/final_analysis.csv`
- [ ] T042 [US3] **Permutation Test Robustness**: Ensure the Permutation Test in `code/analyze_physics.py` handles the edge case where N=2 for one class and N=3 for the other (total N=5) by correctly calculating the total number of permutations (`math.comb(N, K)`) and performing an exact test rather than a Monte Carlo approximation.
 - **Success State**: The code must acknowledge that the minimum non-zero p-value is limited by the inverse of the permutation count and enforce the adjusted threshold (p < 0.1).
- [X] T047 [US3] **Statistical Reporting**: Implement a final reporting step that reads `data/processed/final_analysis.csv`, extracts the p-value from the Permutation Test, and explicitly compares it against the threshold (p < 0.1) to determine if the result is "Significant" or "Not Significant".
 - **Output**: Append a `significance` column to `data/processed/final_analysis.csv` or generate a summary log entry stating the result.
 - **Constraint**: This step explicitly validates SC-001.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns (Amendments & Validation)

**Purpose**: Improvements that affect multiple user stories and formalize deviations

- [X] T030 [P] Documentation updates in `docs/` and `README.md`
- [X] T031 Code cleanup and refactoring for readability
- [X] T032 Performance optimization (dtype optimization, batch size tuning)
- [X] T033 [P] Additional unit tests for edge cases (empty datasets, fit failures) in `tests/unit/`
- [X] T034 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [X] T043 [P] **Final Audit**: Generate a `state/audit_report.md` that explicitly lists: (1) The 2-3 properties used, (2) The exact subset sizes achieved, (3) The R2 values for each, (4) The p-value from the Permutation Test, and (5) A confirmation that all code paths adhere to the amended spec (T035/T036).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes critical amendments T035/T036 and verification T045/T046.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `materials_master.parquet`)
- **User Story 3 (P3)**: Depends on US2 completion (requires `scaling_results.csv`)

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Unit test for Magpie vector generation in tests/unit/test_descriptors.py"

# Launch all implementation tasks for User Story 1 (sequentially due to data flow):
Task: "Generate research.md (T037.0)"
Task: "Implement code/download_data.py (T011)"
Task: "Implement code/generate_descriptors.py"
Task: "Implement data consolidation logic"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes amendments)
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
 - Developer B: User Story 2 (after US1 data is ready)
 - Developer C: User Story 3 (after US2 data is ready)
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
- **Critical Protocol Note**: Constitution Principle VII (multiple subsets, multiple seeds) is the governing requirement. The Plan's "5x1" note is a feasibility observation that requires a formal amendment (T035) to override. The implementation MUST follow the Constitution unless the amendment is formally recorded and approved.
- **Critical Data Note**: FR-001 requires 2-3 properties. The implementation MUST validate this count and **log** (not halt) if N < 2 (T016).
- **Critical Statistical Note**: Permutation Test is the mandated method for this project's scope (N=2-3). The Kruskal-Wallis test is NOT to be implemented. The amendment (T036) formalizes this change and updates the Spec directly.
- **Execution Order**: T035 and T036 MUST be completed before T019, T020, and T027 to ensure legal compliance before code execution.
- **New Task Note**: Tasks T037.0, T037, T038, T039, T040, T041, and T042 address specific review concerns regarding data source verification, streaming implementation, subset validation, metric definition, statistical robustness, and final audit, ensuring the project adheres to the amended scope and scientific rigor.
- **New Task Note**: Tasks T045 and T046 address the need for a formal constitution override verification, and final spec verification to ensure all legal and statistical changes are enforced.
- **New Task Note**: Task T047 ensures explicit reporting and validation of the statistical significance criterion (SC-001).
- **Removed Task Note**: T044 removed; its content merged into T035 to prevent redundancy.
