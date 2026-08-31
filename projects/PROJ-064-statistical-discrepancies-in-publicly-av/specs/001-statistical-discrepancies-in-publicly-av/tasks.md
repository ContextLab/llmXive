# Tasks: Statistical Discrepancies in Publicly Available Election Data

**Input**: Design documents from `/specs/001-statistical-discrepancies/`
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

- [ ] T001 Initialize project directory structure: Create `projects/PROJ-064-statistical-discrepancies-in-publicly-av/` with `code/`, `data/` (raw/processed), `tests/`, `docs/`, `state/`, and `config/` subdirectories in one atomic step.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure: `data/raw/`, `data/processed/` and `state/` for checksums in `projects/PROJ-064-statistical-discrepancies-in-publicly-av/`
- [ ] T005 [P] Implement base logging infrastructure and error handling framework in `code/`
- [X] T007 Create base data models/entities (Jurisdiction, Discrepancy) in `code/models.py` AND define the output schema (columns: `precinct_sum`, `county_reported`, `discrepancy_abs`, `discrepancy_pct`, `missing_data` flag) for downstream tasks.
- [X] T008 Implement content hashing utility for artifacts in `code/utils/hashing.py`
- [ ] T009a Implement GitHub Actions workflow trigger for `--verify-reproducible` to re-run analysis on a fresh CI runner in `.github/workflows/verify_reproducible.yml`
- [X] T006 [P] Create `traceability_map.json` generator script in `code/utils/traceability.py` to link output metrics to source data rows (Depends on T007 schema definition; ready for use in US1/US2)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and normalize election data from verified sources into a unified format with calculated discrepancies.

**Independent Test**: The pipeline can be tested by running the data ingestion script against a small, fixed sample of known CSV files and verifying that the output DataFrame contains the expected columns (`precinct_sum`, `county_reported`, `discrepancy_abs`, `discrepancy_pct`) with no nulls in critical fields.

### Implementation for User Story 1

- [X] T014 [US1] Implement `ingestion.py` to: 1) Download data from OpenElections/State CSVs using verified URLs or Hugging Face mirrors; 2) Implement Synthetic Data Fallback logic (ONLY for validation/testing) that generates data matching *only* the available variables (excluding missing ones) using default Normal(0, 1) noise if parameters are not in config; 3) Parse raw CSVs, normalize aggregation levels, and handle format deviations; 4) Raise clear errors if required variables (precinct votes, county totals) are missing; 5) Skip records with zero county votes and log warnings; 6) Flag "directional anomalies" (precinct sum > county total) and exclude from Negative Binomial fit; 7) Apply documented imputation rules or flag records with `missing_data` marker; 8) Validate temporal alignment of precinct/county boundaries with election cycle year. in `code/ingestion.py` and `code/discrepancy.py`
- [X] T016 [US1] Implement validation logic to ensure required variables (precinct votes, county totals) exist, raising clear errors if missing in `code/ingestion.py`
- [X] T017 [US1] Implement logic to calculate `precinct_sum`, `county_reported`, `discrepancy_abs`, and `discrepancy_pct` in `code/discrepancy.py`
- [X] T018 [US1] Implement edge case handling: skip records with zero county votes, log warnings, and exclude from relative discrepancy analysis in `code/discrepancy.py`
- [X] T019 [US1] Implement logic to flag "directional anomalies" (precinct sum > county total) and exclude from Negative Binomial fit if non-negative error assumption is violated in `code/discrepancy.py`
- [X] T020 [US1] Implement missing data handling: apply documented imputation rules or flag records with `missing_data` marker in `code/discrepancy.py`
- [X] T021 [US1] Ensure raw data is saved to `data/raw/` with checksums and processed data to `data/processed/` in `code/main.py`
- [X] T022 [US1] Implement logic to validate temporal alignment of precinct/county boundaries with election cycle year in `code/ingestion.py`

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests AFTER implementation to ensure they verify the correct schema and logic. Depends on T007 (Data Models & Schema).

- [X] T010 [P] [US1] Unit test for data ingestion with mock CSV files in `tests/test_ingestion.py` (Schema defined in T007)
- [X] T011 [P] [US1] Contract test verifying output schema (precinct_sum, county_reported, etc.) in `tests/test_ingestion.py`
- [X] T012 [P] [US1] Test for missing data handling (imputation vs. flagging) in `tests/test_ingestion.py`
- [X] T013 [P] [US1] Test for auto-detection of file delimiters in `tests/test_ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Null Model Simulation and Statistical Testing (Priority: P2)

**Goal**: Construct Negative Binomial and Permutation null models, perform Anderson-Darling and KS tests, and frame findings as associational deviations.

**Independent Test**: The analysis module can be tested by feeding it a synthetic dataset with known properties (Negative Binomial distributed noise) and verifying that the p-values from the Anderson-Darling and KS tests align with the expected distribution (high p-values) within ±0.05 tolerance, using seed=42.

### Implementation for User Story 2

- [ ] T027 [US2] Implement `simulation.py` to: 1) Generate a Negative Binomial null model from theoretical priors or pre-aggregation permutation; 2) Implement chunked processing (1000 iterations/batch) to stay under a moderate RAM footprint; 3) Aggregate results (accumulate log-likelihoods/p-values) to ensure statistical equivalence to a full-scale run; 4) If NB fit fails (convergence error), switch to permutation-based null model as fallback; 5) Use seed=42. in `code/simulation.py`
- [ ] T028 [US2] Implement `simulation.py` to generate a permutation-based null model simulating random clerical error within geographic boundaries (used as fallback or secondary model) in `code/simulation.py`
- [ ] T029 [US2] Implement Monte Carlo simulation with 10,000 iterations (seed=42) using chunked processing (see T045) to stay under 7 GB RAM in `code/simulation.py`
- [ ] T045 [US2] [P] Implement logic to handle memory constraints via deferred iterations per batch during Monte Carlo in `code/simulation.py` (Optimization for T029)
- [ ] T030 [US2] Implement Anderson-Darling test comparing observed discrepancies against the simulated null distributions in `code/analysis.py`
- [ ] T031 [US2] Implement Kolmogorov-Smirnov test comparing observed vs. null distributions in `code/analysis.py`
- [ ] T032 [US2] Implement logic to calculate p-values for each jurisdiction individually against the null distribution in `code/analysis.py`
- [ ] T033 [US2] Implement logic to frame all findings as "associational deviations from random expectation" in the output reports in `code/analysis.py`
- [ ] T034 [US2] Implement fallback to permutation-based null model if Negative Binomial fit fails in `code/simulation.py`
- [ ] T035 [US2] Implement VIF calculation for predictors if regression is extended: Check if 'population density, precinct size' exist in config; if yes, calculate VIF and flag if > 5; if no, mark SC-006 as 'Not Applicable' in `code/analysis.py`
- [ ] T029b [US2] [P] Verify chunked aggregation matches full-run simulation: Run a small-scale full simulation and compare with chunked aggregation of the same data to ensure statistical equivalence. in `code/analysis.py`

### Tests for User Story 2 ⚠️

- [ ] T023 [P] [US2] Unit test for Negative Binomial null model generation with synthetic data in `tests/test_simulation.py`
- [ ] T024 [P] [US2] Unit test for Permutation-based null model generation in `tests/test_simulation.py`
- [ ] T025 [P] [US2] Unit test for Anderson-Darling and KS test outputs against known distributions in `tests/test_simulation.py`
- [ ] T026 [P] [US2] Test for non-circular null model construction (independent of observed anomalies) in `tests/test_simulation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on thresholds and models, and generate visualizations (histograms, Q-Q plots, heatmaps) using CPU-tractable libraries.

**Independent Test**: The visualization module can be tested by running the sensitivity sweep and verifying that the output files (plots) are generated and that the sensitivity report correctly lists the variation in flagged jurisdiction counts.

**⚠️ DEPENDENCY**: This phase depends on Phase 4 completion (T027-T035).

### Implementation for User Story 3

- [ ] T039a [US3] [P] Generate `config/sensitivity_thresholds.yaml` with concrete values: primary_threshold=0.5%, sweep_thresholds={0.01%, 0.05%, 0.1%, [deferred]} to resolve [deferred] markers from spec FR-005 in `config/sensitivity_thresholds.yaml`
- [ ] T039 [US3] Implement sensitivity analysis in `code/analysis.py` that loads thresholds from `config/sensitivity_thresholds.yaml` (MUST contain concrete values; halt if [deferred] found) and compares Negative Binomial vs. Permutation null models, generating a UNIFIED report correlating variation in flagged counts across BOTH dimensions (threshold AND model) in `code/analysis.py`
- [ ] T041 [US3] Implement `viz.py` to generate histograms of observed vs. simulated discrepancies using `matplotlib`/`seaborn`, reading null distribution from `data/processed/null_distributions.json` in `code/viz.py`
- [ ] T042 [US3] Implement `viz.py` to generate Q-Q plots comparing observed vs. null distributions in `code/viz.py`
- [ ] T043 [US3] Implement `viz.py` to generate a table or heatmap of top jurisdictions by discrepancy magnitude in `code/viz.py`
- [ ] T044 [US3] Ensure all visualizations are saved as static image files within the available disk limit in `code/viz.py`
- [ ] T046 [US3] Generate the final sensitivity report including variation in false-positive rates across thresholds and models in `code/analysis.py`

### Tests for User Story 3 ⚠️

- [ ] T036 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/test_analysis.py`
- [ ] T037 [P] [US3] Unit test for visualization generation (histograms, Q-Q plots) in `tests/test_viz.py`
- [ ] T038 [P] [US3] Integration test verifying memory usage stays under 7 GB during sensitivity sweep in `tests/test_analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. Depends on US1 and US2 output schemas.

- [ ] T006 [P] Create `traceability_map.json` generator to link output metrics to source data rows (Depends on US1 and US2 output schemas) - **Note: Script created in Phase 2; execution now.**
- [ ] T047a [P] Generate `docs/quickstart.md` with end-to-end pipeline execution instructions in `docs/`
- [ ] T047b [P] Generate `docs/data-model.md` with entity definitions and schema details in `docs/`
- [ ] T048 [P] Refactor `code/simulation.py` to reduce Monte Carlo loop complexity from O(n^2) to O(n log n) where possible. **Deliverable**: Refactored code with benchmark script. **Verification**: Run `code/benchmark_simulation.py` and confirm runtime is reduced by at least 20% compared to the baseline O(n^2) implementation on a sample of 1000 iterations.
- [ ] T049 [P] Benchmark Monte Carlo chunking to ensure < 6h execution time for 10k iterations. **Deliverable**: Benchmark report. **Verification**: Execute `code/benchmark_simulation.py` with full 10k iterations; confirm total runtime is < 6 hours on the target runner environment and log memory usage stays < 7 GB.
- [ ] T050 [P] Additional unit tests for edge cases (zero votes, missing data) in `tests/`
- [ ] T051 Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [ ] T052 Generate `traceability_map.json` linking all final statistics to source data rows (Uses T006 script)

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 simulation results

### Within Each User Story

- Implementation tasks MUST be completed before tests
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
# Launch all implementation tasks for User Story 1 together:
Task: "Implement ingestion.py to download data from OpenElections in code/ingestion.py"
Task: "Implement logic to calculate discrepancies in code/discrepancy.py"

# Then launch all tests for User Story 1:
Task: "Unit test for data ingestion with mock CSV files in tests/test_ingestion.py"
Task: "Contract test verifying output schema in tests/test_ingestion.py"
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
5. Each story adds value without breaking previous stories

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
- Implement code FIRST, then write tests to verify
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data must be real (streamed or sampled) or explicitly synthetic for validation only. No silent fallbacks to fake data.
- **Memory Constraints**: Ensure Monte Carlo simulation uses chunked processing to stay under 7 GB RAM.
- **Statistical Rigor**: Null models must be constructed independently of observed anomalies to avoid circular reasoning.
- **Framing**: All findings must be framed as associational deviations from random expectation.