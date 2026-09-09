# Tasks: Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power

**Input**: Design documents from `/specs/001-gut-microbiome-eeg-alpha/`
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

- [X] T001a Create `code/`, `data/`, `artifacts/`, `tests/` directories in repository root
- [X] T001b Create `data/raw/agp_microbiome/` and `data/raw/openneuro_eeg/` subdirectories
- [X] T001c Create `data/processed/`, `artifacts/`, `tests/contract/`, `tests/integration/`, `tests/unit/` subdirectories
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scipy, scikit-learn, mne, skbio, matplotlib, seaborn, pyyaml, qiime2==2023.5)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004b1 [P] Define and Write `contracts/dataset.schema.yaml` with explicit fields: `age` (int), `sex` (str), `bmi` (float), `diet` (str), `alpha_power` (float), `taxon_abundances` (dict). **Independently executable from T004b2.** (US-1)
- [ ] T004b2 [P] Define and Write `contracts/output.schema.yaml` with explicit fields for `stratum_id`, `stratum_mean_alpha_power`, `stratum_taxa_means` (dict), `valid_strata_count`. **Independently executable from T004b1.** (US-1)
- [ ] T004 [US1] Implement data schema validation using `pydantic` or `jsonschema` based on `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`. **Depends on T004b1, T004b2**. (US-1) <!-- FAILED: unspecified -->
- [X] T005 [P] Setup logging infrastructure to output structured logs to `artifacts/preprocess.yaml` and `artifacts/analysis_results.json`
- [ ] T006 [P] Create utility functions for checksum verification (SHA256) to generate `artifacts/checksums.txt` for all files in `data/`. (US-1)
- [X] T007 [P] Create `code/seed_manager.py` with a `set_seed(seed=42)` function to ensure reproducibility across statistical runs. (US-2)
- [X] T008 [P] Create base configuration loader to read `artifacts/preprocess.yaml` (filter bands, ICA settings, pseudocount) and write the initial `artifacts/preprocess.yaml` with required parameters. (US-1)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Preprocessing & Ecological Aggregation (Priority: P1) 🎯 MVP

**Goal**: Acquire AGP and OpenNeuro data, preprocess them, and aggregate into demographic strata. Compute mean alpha power and taxa abundances per stratum. **CRITICAL: Implement Spec-mandated Ecological Aggregation with hard exit if <5 valid strata exist.**

**Independent Test**: Verify that (1) Microbiome CSV has ≥100 rows, (2) EEG CSV has ≥50 subjects, (3) `data/processed/stratum_features.csv` contains valid strata with ≥5 subjects each, and (4) `artifacts/strata_report.json` contains `valid_strata_count` ≥ 5.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data loading in `tests/contract/test_data_loading.py` (verify schema compliance for stratum features)
- [X] T011a [P] [US1] Integration test for Ecological Aggregation success in `tests/integration/test_ecological_aggregation.py` (verify file existence, row counts, and strata count)
- [X] T011b [P] [US1] Integration test for <5 strata exit condition in `tests/integration/test_strata_exit.py` (verify exit code 1 and error log)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/preprocess_microbiome.py` to download AGP data from ` (or execute 'Manual Download + Checksum' protocol if URL fails). Run QIIME2 version `2023.5` to generate genus-level abundances. Apply pseudocount=0.5. Output `data/processed/microbiome_features.csv`. **FAIL LOUDLY**: Raise `FileNotFoundError` if download fails. Use SHA256 for checksums. (US-1)
- [ ] T013 [P] [US1] Implement `code/preprocess_eeg.py` to download OpenNeuro dataset `ds000248` (Spec/Constitution mandate). Filter (low-pass to high-pass frequency range), run FastICA (a set of components), epoch (-min), compute alpha power (Welch's method). Filter subjects with <80% valid epochs. Output `data/processed/eeg_features.csv`. **NOTE**: Use `ds000248`. (US-1)
- [X] T014 [US1] Implement `code/ecological_aggregation.py` to perform **Ecological Aggregation** (FR-003):
 1. Load `microbiome_features.csv` and `eeg_features.csv`.
 2. **Handle Missing Data**: For subjects with missing demographics (Age, Sex, BMI, Diet), apply **Exclusion** as the primary method. If exclusion results in <5 subjects in a potential stratum, attempt **Documented Median Imputation** only if it helps reach the threshold; otherwise, exclude.
 3. **Aggregate**: Group subjects into demographic strata (Age bins, Sex, BMI bins, Diet).
 4. **Count Valid Strata**: Identify groups with ≥5 subjects in *both* cohorts (AGP and OpenNeuro).
 5. **Output**: Write `data/processed/raw_stratum_agg.csv` (containing subject IDs, stratum ID, and raw data) and `artifacts/strata_report.json` (containing `valid_strata_count`).
 6. **Exit Logic**: If `valid_strata_count` < 5, log ERROR: "Insufficient valid strata (<5) for ecological analysis", and exit with code 1. Otherwise, exit with code 0. (US-1)
- [X] T015 [US1] Implement `code/compute_stratum_means.py` to compute final stratum features (**Depends on T014**):
 1. Load `data/processed/raw_stratum_agg.csv`.
 2. **Compute Means**: Calculate mean alpha power (Welch's method result) per stratum. Calculate mean taxa abundance per stratum.
 3. **CLR Transformation**: Apply CLR transformation (pseudocount=0.5) to the mean taxa abundances per stratum (FR-004).
 4. **Output**: Write `data/processed/stratum_features.csv` containing `stratum_id`, `mean_alpha_power`, `clr_taxa_abundances` (dict), and `n_subjects`. (US-1, US-2)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently, with stratum-level data ready for analysis.

---

## Phase 4: User Story 2 - Statistical Analysis and Association Testing (Priority: P1)

**Goal**: Compute Spearman correlation on stratum-level means, apply FDR, and run permutation tests.

**Independent Test**: Verify CLR transformation correctness, Spearman rho calculation on stratum means, FDR application, and permutation null distribution generation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for CLR transformation function in `tests/unit/test_transformations.py` (verify log(0) handling with pseudocount)
- [X] T019 [P] [US2] Unit test for FDR correction in `tests/unit/test_statistics.py` (verify Benjamini-Hochberg logic)

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement CLR transformation utility in `code/utils.py` (pseudocount=0.5). (US-2)
- [X] T021 [US2] Implement alpha power aggregation utility in `code/utils.py` using Welch's method results. (US-2)
- [ ] T022 [US2] Implement Spearman correlation analysis (**Depends on T015**):
 - Load `data/processed/stratum_features.csv`.
 - **Select Top 20 Taxa**: Compute the mean relative abundance of each taxon across *all* strata in the file. Select the taxa with the highest mean abundance..
 - **Correlation**: Perform Spearman correlation between the CLR-transformed abundances of these 20 taxa and `mean_alpha_power` per stratum.
 - **FDR**: Apply Benjamini-Hochberg FDR correction (q<0.1).
 - **Output**: Write `artifacts/correlation_results.json` (rho, p-value, q-value, significance flag) and `artifacts/top_taxa.txt`. (US-2)
- [ ] T023 [US2] Implement collinearity diagnostics (**Depends on T022**):
 - Calculate **Variance Inflation Factor (VIF)** for the 20 taxa tested in T022.
 - Report VIF values in `artifacts/analysis_results.json`. (US-2)
- [ ] T024 [US2] Implement permutation testing to generate null distribution (**Depends on T015**):
 - **Path**: Permute `mean_alpha_power` labels across strata (1000 iterations).
 - **Pass the random seed (from T007) explicitly as `random_state`**.
 - Set `perm_test_passed` boolean if observed max absolute Spearman rho exceeds the upper percentile of null distribution. (US-2)
- [ ] T025 [US2] Inject the exact string "Note: This analysis is associational only; no causal inference is made." into all result JSONs and reports. (US-2)
- [ ] T026 [US2] Output `artifacts/analysis_results.json` containing correlation coefficients, p-values, q-values, VIF values, permutation flags, and `valid_strata_count` read from `artifacts/strata_report.json`. (US-2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, with results corresponding to the stratum-level analysis.

---

## Phase 5: User Story 3 - Results Visualization and Reporting (Priority: P2)

**Goal**: Generate publication-ready visualizations of stratum-level correlations.

**Independent Test**: Verify existence of scatter plots with regression lines and stratified distribution plots of stratum means.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for visualization outputs in `tests/contract/test_visualizations.py` (verify file types and presence)

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/visualization.py` to generate **Stratum-Level Visualizations** (**Depends on T022, T015**):
 - **Scatter Plots**: For significant taxa (q<0.1), plot `mean_alpha_power` vs. `CLR-transformed mean abundance` with regression line, R², and 95% CI.
 - **Heatmap**: Correlation heatmap of top 20 taxa vs. alpha power.
 - **Distribution Plots**: Histograms/boxplots of alpha power distribution across strata.
 - **Labels**: Include sample sizes (n_subjects) and associational disclaimer.
 - **Output**: Save figures to `artifacts/` (e.g., `scatter_stratum.png`, `heatmap_stratum.png`). (US-3)
- [ ] T030 [US3] Ensure all plots include the associational disclaimer. (US-3)
- [ ] T031 [US3] Save all figures to `artifacts/` with canonical naming. (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` including data provenance and methodological notes
- [ ] T034 Code cleanup and refactoring of statistical functions
- [ ] T035a Refactor `code/correlation_analysis.py` (if created) to reduce cyclomatic complexity (<10)
- [ ] T036a Optimize memory usage in `code/preprocess_eeg.py` and `code/ecological_aggregation.py` to ensure <5GB RAM usage; verify runtime <6 hours. **Generate `artifacts/performance_report.json`**. (US-1)
- [ ] T037 [P] Additional unit tests for edge cases (NaN handling, zero-abundance taxa) in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T039 [P] Update `plan.md` to correct the OpenNeuro dataset ID from `ds000246` to `ds000248` in the Summary and Constitution Check sections. **Verification**: Grep for `ds000246` and replace with `ds000248`. (US-1)
- [ ] T040 [P] Add explicit error handling in `code/preprocess_eeg.py` and `code/preprocess_microbiome.py` to fail loudly (raise exception) if real data download fails, ensuring no synthetic fallback is triggered. (US-1)
- [ ] T041 [US1] Validate SC-001: Read `artifacts/strata_report.json` and assert `valid_strata_count` >= 5. Log pass/fail to `artifacts/validation_report.json`. (US-1)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T015 (stratum features)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T015 (stratum features)

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
Task: "Contract test for data loading in tests/contract/test_data_loading.py"
Task: "Integration test for Ecological Aggregation in tests/integration/test_ecological_aggregation.py"

# Launch all models for User Story 1 together:
Task: "Implement preprocess_microbiome.py"
Task: "Implement preprocess_eeg.py"
Task: "Implement ecological_aggregation.py"
Task: "Implement compute_stratum_means.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ecological Aggregation)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data counts, strata count, and exit logic)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Statistical results)
4. Add User Story 3 → Test independently → Deploy/Demo (Visualizations)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline & Aggregation)
 - Developer B: User Story 2 (Statistics)
 - Developer C: User Story 3 (Visualization)
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
- **CRITICAL**: The `plan.md` references 'ds000246' while tasks and constitution reference 'ds000248'. Task T039 addresses the plan update.
- **CRITICAL**: Task T014 now implements the explicit Ecological Aggregation logic (grouping, missing data handling, strata count) as the primary path, removing the abandoned 'Virtual Cohort Matching' strategy.
- **CRITICAL**: Task T015 computes mean alpha power and CLR transformation on stratum-level means, satisfying FR-004 and FR-005.
- **CRITICAL**: Task T022 performs Spearman correlation on stratum-level means, satisfying FR-006.
- **CRITICAL**: Task T024 performs permutation testing on stratum-level data, satisfying FR-007.
- **CRITICAL**: Task T029 generates visualizations of stratum-level correlations, satisfying FR-008.
- **CRITICAL**: Task T004b1 and T004b2 are independent and write to distinct files.
- **CRITICAL**: Task T014 fails loudly if <5 valid strata exist, as mandated by the Spec.
- **CRITICAL**: Task T014 specifies 'Exclusion' as the primary method for missing demographics.
- **CRITICAL**: Task T022 explicitly computes global mean abundance to select the top 20 taxa.
- **CRITICAL**: Task T039 includes explicit verification steps.
- **CRITICAL**: Task T006, T007, T008 are updated to explicitly create required artifacts.
- **CRITICAL**: Task T012 and T013 use verified URLs or fail loudly.
- **CRITICAL**: The 'Virtual Cohort Matching' strategy is removed from the tasks to align with the Spec's Ecological Correlation requirement.