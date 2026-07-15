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

- [ ] T004b1 [P] Generate `contracts/dataset.schema.yaml` defining the schema for input microbiome and EEG feature matrices (US-1)
- [ ] T004b2 [P] Generate `contracts/output.schema.yaml` defining the schema for `matched_pairs.csv`, `distribution_groups.csv`, and `analysis_results.json` (US-2)
- [X] T004 [P] Implement data schema validation using `pydantic` or `jsonschema` based on `contracts/dataset.schema.yaml` (Depends on T004b1, T004b2) <!-- FAILED: unspecified -->
- [X] T005 [P] Setup logging infrastructure to output structured logs to `artifacts/preprocess.yaml` and `artifacts/analysis_results.json`
- [ ] T006 [P] Create utility functions for checksum verification (MD5/SHA256) to enforce `artifacts/checksums.txt` protocol
- [ ] T007 Implement random seed management utility to ensure reproducibility across statistical runs (must be importable by all analysis scripts)
- [ ] T008 Create base configuration loader to read `preprocess.yaml` parameters (filter bands, ICA settings, pseudocount)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Preprocessing & Virtual Cohort Matching (Priority: P1) 🎯 MVP

**Goal**: Acquire AGP and OpenNeuro data, preprocess them, and attempt Virtual Cohort Matching. If matching fails (<10 pairs), automatically switch to Distributional Comparison.

**Independent Test**: Verify that (1) microbiome CSV has ≥100 rows, (2) EEG CSV has ≥50 subjects, (3) `matched_pairs.csv` has ≥10 rows OR `distribution_groups.csv` is generated with valid group sizes.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data loading in `tests/contract/test_data_loading.py` (verify schema compliance for matched pairs or distribution groups)
- [ ] T011 [P] [US1] Integration test for full preprocessing and matching pipeline in `tests/integration/test_preprocessing.py` (verify file existence, row counts, and successful path selection) <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/preprocess_microbiome.py` to download AGP data from ` (or execute 'Manual Download + Checksum' protocol if URL fails). Run QIIME2 version `2023.5` with CLI command `qiime feature-table summarize --i-table table.qza --o-visualization table.qzv` followed by `qiime taxa barplot` to generate genus-level abundances. Apply pseudocount=0.5. Output `data/processed/microbiome_features.csv`. **NOTE: The Plan mandates 'Virtual Cohort Matching' (Path A) or 'Distributional Comparison' (Path B). This task implements the data preparation for both paths.**
- [~] T013 [P] [US1] Implement `code/preprocess_eeg.py` to download OpenNeuro dataset `ds000248` (Spec/Constitution mandate). Filter (0.5–45 Hz), run FastICA (20 components), epoch (2-min), compute alpha power (Welch's method). Filter subjects with <80% valid epochs. Output `data/processed/eeg_features.csv`. **NOTE: Output the available subjects (target ≥50); log a warning if count < 50.**
- [X] T014 [US1] Implement `code/match_cohorts.py` to perform **Virtual Cohort Matching** (Path A) and fallback logic (Path B):
 1. Load `microbiome_features.csv` and `eeg_features.csv`.
 2. **Path A (Matching)**: Match AGP and OpenNeuro subjects based on (Age, Sex, BMI) using **Nearest-Neighbor** matching (scikit-learn `NearestNeighbors`) as the PRIMARY method.
 3. **Fallback Logic**: If Nearest-Neighbor fails to converge or returns <10 pairs, attempt Propensity Score matching as a secondary method.
 4. **Decision Criterion**: If ≥10 valid matched pairs are found (via either method):
 - Write `data/processed/matched_pairs.csv`.
 - Log "Path A Selected: Virtual Cohort Matching successful (N={pairs})".
 - Exit with code 0.
 5. **Path B (Fallback)**: If <10 valid pairs are found after both methods:
 - Split AGP data into High/Low abundance groups (median split) for top taxa.
 - Assign EEG subjects to these groups based on demographic similarity or random assignment if metadata allows (as per Plan's Distributional logic).
 - Write `data/processed/distribution_groups.csv`.
 - Log "Path B Selected: Insufficient matches (N={pairs}). Switching to Distributional Comparison."
 - Exit with code 0.
 6. **NOTE**: This task replaces the abandoned 'Ecological Aggregation' logic. It strictly follows the Plan's Two-Path Strategy and resolves the ambiguity between Nearest-Neighbor and Propensity Score by prioritizing Nearest-Neighbor.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently, with data ready for either Path A or Path B analysis.

---

## Phase 4: User Story 2 - Statistical Analysis and Association Testing (Priority: P1)

**Goal**: Compute CLR-transformed means, run Spearman correlation (Path A) OR Distributional tests (Path B), apply FDR, and run permutation tests.

**Independent Test**: Verify CLR transformation correctness, Spearman rho calculation (Path A) OR Mann-Whitney U (Path B), FDR application, and permutation null distribution generation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for CLR transformation function in `tests/unit/test_transformations.py` (verify log(0) handling with pseudocount)
- [~] T019 [P] [US2] Unit test for FDR correction in `tests/unit/test_statistics.py` (verify Benjamini-Hochberg logic)

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement CLR transformation in `code/correlation_analysis.py` applying pseudocount=0.5 to subject-level data (Path A) or group-level means (Path B)
- [X] T021 [US2] Implement alpha power aggregation per subject/group in `code/correlation_analysis.py` using Welch's method results from Phase 1
- [X] T022 [US2] Implement **Conditional Statistical Testing** in `code/correlation_analysis.py`:
 - **If Path A (matched_pairs.csv exists)**: Perform Spearman correlation between **the 20 taxa with the highest mean relative abundance** and mean alpha power per matched pair. Apply Benjamini-Hochberg FDR (q<0.1).
 - **If Path B (distribution_groups.csv exists)**: Perform Mann-Whitney U or Kolmogorov-Smirnov tests comparing alpha power distributions between High/Low abundance groups.
 - **NOTE**: Strictly follow the Plan's conditional logic. Do NOT use PCoA axes for the primary test unless specified as a secondary diagnostic.
- [~] T023 [US2] Implement collinearity diagnostics: Calculate **Variance Inflation Factor (VIF)** for the 20 taxa tested in T022 (Path A only) to satisfy FR-009. Report VIF values in `artifacts/analysis_results.json`. For Path B, report group separation statistics instead.
- [~] T024 [US2] Implement permutation testing to generate null distribution:
 - **Path A**: Shuffle subject labels in matched pairs.
 - **Path B**: Shuffle group labels in distribution groups.
 - **Pass the random seed (from T007) explicitly as `random_state`** to ensure reproducibility.
 - Set `perm_test_passed` boolean if observed statistic exceeds the 95th percentile of null distribution in `code/correlation_analysis.py`.
- [~] T025 [US2] Inject the exact string "Note: This analysis is associational only; no causal inference is made." into all result JSONs and reports
- [~] T026 [US2] Output `artifacts/analysis_results.json` containing correlation coefficients (Path A) OR test statistics (Path B), p-values, q-values, VIF values (if applicable), and permutation flags

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, with results corresponding to the selected path.

---

## Phase 5: User Story 3 - Results Visualization and Reporting (Priority: P2)

**Goal**: Generate publication-ready visualizations (Scatter plots for Path A OR Distribution plots for Path B).

**Independent Test**: Verify existence of scatter plots with regression lines (Path A) OR boxplots/violin plots (Path B) and stratified distribution plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for visualization outputs in `tests/contract/test_visualizations.py` (verify file types and presence)

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/visualization.py` to generate **Conditional Visualizations**:
 - **Path A**: Scatter plots of matched pairs (alpha power vs. CLR-transformed mean abundance for top significant taxa) with regression line, R², and 95% CI.
 - **Path B**: Boxplots/Violin plots of alpha power distribution by High/Low abundance groups with sample sizes labeled.
- [ ] T030 [US3] Ensure all plots include sample sizes and the associational disclaimer
- [ ] T031 [US3] Save all figures to `artifacts/` with canonical naming (e.g., `scatter_matched.png` or `boxplot_distribution.png`)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` including data provenance and methodological notes
- [ ] T034 Code cleanup and refactoring of statistical functions
- [ ] T035a Refactor `code/correlation_analysis.py` to reduce cyclomatic complexity (<10) and improve readability
- [ ] T036a Optimize memory usage in `code/preprocess_eeg.py` and `code/match_cohorts.py` to ensure <5GB RAM usage; verify runtime <6 hours. **Generate `artifacts/performance_report.json` containing `{"max_memory_mb": <int>, "total_runtime_seconds": <int>, "peak_cpu_percent": <int>}` to prove constraints were met.**
- [ ] T037 [P] Additional unit tests for edge cases (NaN handling, zero-abundance taxa) in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`matched_pairs.csv` OR `distribution_groups.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results

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
Task: "Integration test for full preprocessing pipeline in tests/integration/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement preprocess_microbiome.py"
Task: "Implement preprocess_eeg.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data counts and successful path selection)
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
 - Developer A: User Story 1 (Data Pipeline & Matching)
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
- **CRITICAL**: The `plan.md` mandates a "Two-Path Strategy" (Virtual Cohort Matching or Distributional Comparison). The tasks above strictly follow this Plan, replacing the abandoned "Ecological Correlation" logic from the original Spec.
- **CRITICAL**: The `plan.md` references 'ds000246' while tasks and constitution reference 'ds000248'. The tasks have been updated to use 'ds000248' as per the Spec/Constitution. The `plan.md` MUST be updated to 'ds000248' to resolve the contradiction.
- **CRITICAL**: Task T014 now implements the explicit decision criterion for Path A vs Path B (≥10 pairs threshold), resolving the ambiguity regarding Nearest-Neighbor vs Propensity Score by selecting Nearest-Neighbor as the primary method and defining the fallback logic clearly.
- **CRITICAL**: Task T004b has been split into T004b1 and T004b2 to provide the required granularity for schema generation.