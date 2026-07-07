# Tasks: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Input**: Design documents from `/specs/001-telomere-lifespan-impact/`
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

- [ ] T001A [P] Create data directory structure: `data/raw`, `data/processed`, `data/phylogeny`, `results`, `logs`, `contracts`, `tests`
- [ ] T001B [P] Create code directory structure: `code/R`, `code/tests`
- [X] T003 [P] Initialize a Python project with `requirements.txt` (pandas, requests, numpy, matplotlib, seaborn, rpy2, sha256 utilities) and an R environment with `renv.lock` (installing `rotl`, `lme4`, `phylolm`, `ape`, `caper`, `anage` via R)
- [X] T004 [P] Configure linting (ruff/black) and formatting tools for both Python and R

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T005 [P] Implement `utils.py` with `generate_checksum(file_path)` and `update_state_file(hash_map)` functions for SHA256 validation
- [ ] T005A [P] Initialize `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml` with empty `artifact_hashes` map and initial timestamp (depends on T005 for structure)
- [X] T006 Create `run_pipeline.sh` orchestration script with input hash verification logic (depends on T005, T005A)
- [X] T008 [P] Create base schema definitions in `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`
- [X] T009 [P] Configure logging infrastructure to write to `logs/` and handle memory pressure detection (>6GB)
- [~] T010 [P] Setup environment configuration management for API keys (Dryad/AnAge) and random seeds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Integration and Cleaning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, clean, standardize, and merge telomere and ecological data into a single analysis-ready CSV.

**Independent Test**: Run ingestion script against a known subset; verify output CSV contains >90% of unique species, valid IDs, standardized units (kb), and no duplicates.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Unit test for Dryad URL parsing and CSV loading in `tests/test_ingest.py`
- [~] T012 [P] [US1] Unit test for unit conversion logic (qPCR to kb) in `tests/test_clean.py`
- [~] T013 [P] [US1] Integration test for full merge pipeline with synthetic data in `tests/test_clean.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement `code/01_discover_data.py` to query Dryad API and extract valid dataset IDs; halt if 0 results found.
- [~] T015 [US1] Implement `code/02_ingest_data.py` to download raw CSVs from Dryad (using `requests`) and AnAge (using direct CSV fetch or `anage` R package via `rpy2`), applying SHA256 checksums. **Do NOT use `rotl` for AnAge data**.
- [~] T016 [US1] Implement `code/03_clean_merge.py` to filter for wild-caught/early-life individuals, convert all telomere units to kilobases (kb), and log unconvertible records to `logs/unconvertible_units.csv`.
- [~] T017 [US1] Implement merge logic in `code/03_clean_merge.py` to join telomere data with AnAge ecological data (migration, body mass) on species name; exclude unmatched records and log to `logs/missing_data_log.csv`. Include validation to ensure output `data/processed/merged_data.csv` meets schema requirements (columns: `species`, `telomere_length_kb`, `lifespan`, `migration_status`, `body_mass_g`) AND explicitly verifies the 'wild-caught' filter was applied.
- [~] T019 [US1] Implement memory pressure check in `code/03_clean_merge.py` to trigger chunked processing or subsampling if RAM > 6GB.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

**Goal**: Fit a PGLS model to quantify the association between telomere length and lifespan, accounting for phylogeny, and perform sensitivity analysis.

**Independent Test**: Run modeling script; verify model converges, outputs fixed effect/p-value, and that p-value matches manual calculation on synthetic data.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Unit test for phylogenetic tree fetching via `rotl` in `tests/test_model.py`
- [~] T021 [P] [US2] Unit test for PGLS formula construction and R script invocation in `tests/test_model.py`

### Implementation for User Story 2

- [~] T022 [US2] Implement `code/04_model_pglS.py` to extract unique species from `data/processed/merged_data.csv` and fetch the corresponding phylogenetic tree from `rotl` (Newick format) to `data/phylogeny/`. **Must run before T023/T024**.
- [~] T023 [US2] Create `code/R/01_fit_pglS.R` to define and fit the PGLS model. Use `phylolm` (selected for iterative lambda estimation capability as per plan.md) to ensure phylogenetic covariance structure is derived from data. The model formula will be implemented as `lifespan ~ telomere_length` with the tree passed as the covariance matrix argument to match the conceptual requirement `lifespan ~ telomere_length + phylogenetic_covariance`.
- [~] T024 [US2] Implement `code/04_model_pglS.py` to call the R script via `rpy2`, passing the merged data and tree, and capturing the summary statistics (coefficient, SE, p-value, lambda). Implement logic to handle low power cases (<15 species) by logging the exact string "Low Power: Phylogenetic inference unreliable" and skipping the modeling step (do not halt the entire pipeline abruptly) instead of failing or proceeding.
- [~] T025 [US2] Implement `code/04_model_pglS.py` to save model results to `results/model_summary.csv` and log the phylogenetic signal (lambda).
- [~] T026 [US2] Create `code/R/02_sensitivity.R` to perform LOOCV (if species count >= 10) or jackknife sensitivity analysis (if species count < 10), outputting `results/sensitivity_log.csv` with columns: `species_id`, `coefficient`, `se`, `p_value`, `method_justification`. **Depends on T025**.
- [ ] T027A [US2] Implement wrapper in `code/04_model_pglS.py` to call `02_sensitivity.R`, log the justification for the chosen method (LOOCV vs jackknife based on species count), and validate the output schema of `sensitivity_log.csv`.
- [ ] T027B [US2] Add validation to ensure the PGLS model correctly handles the `SpeciesRecord` entity aggregation: verify that input data is grouped by species and means calculated before modeling.
- [ ] T030A [US2] Implement `code/05_visualize.py` to generate a forest plot of the fixed effects for the base model with 95% CI, saved as `results/association_forest.png`. **Depends on T025**.

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Ecological Moderator Analysis (Priority: P3)

**Goal**: Test if the telomere-lifespan relationship varies by migratory behavior using an interaction term and generate visualizations.

**Independent Test**: Run extended model; verify output includes interaction coefficient and standard error; verify plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T031 [P] [US3] Unit test for interaction term parsing in `tests/test_model.py`
- [~] T032 [P] [US3] Unit test for plot generation (matplotlib/seaborn) in `tests/test_visualize.py`

### Implementation for User Story 3

- [ ] T033 [US3] Create `code/R/03_fit_moderator.R` to define and fit the extended PGLS model (`lifespan ~ telomere_length * migration_status`) using `phylolm` with interaction term logic, ensuring consistency with the base model engine.
- [ ] T034 [US3] Update `code/04_model_pglS.py` (or create `code/06_moderator.py`) to call the moderator R script, read `results/model_summary.csv` from US2 to calculate AIC difference vs base model, extract the interaction coefficient and p-value. **Depends on T025**.
- [ ] T035 [US3] Update `code/05_visualize.py` to generate a grouped scatter plot with separate regression lines for "Migratory" and "Resident" species, saved as `results/moderator_plot.png`. This task fulfills the FR-007 requirement for the moderator scatter plot. **Depends on T034**.
- [ ] T036 [US3] Add validation to ensure `results/moderator_plot.png` correctly visualizes the interaction effect and species grouping.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037A [P] Update README with installation steps and pipeline overview
- [ ] T037B [P] Update quickstart.md with pipeline execution example and expected outputs
- [ ] T038 Code cleanup and refactoring of `utils.py` and `run_pipeline.sh`
- [ ] T041 Performance optimization for data loading (chunking) if RAM usage approaches limits
- [ ] T042 [P] Additional unit tests for edge cases (missing data, unit conversion failures) in `tests/`
- [ ] T043 Security hardening: Ensure no API keys are hardcoded in `code/`
- [ ] T044 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Depends on US1 completion (needs `data/processed/merged_data.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (needs base model results and data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T006 which depends on T005/T005A)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Dryad URL parsing in tests/test_ingest.py"
Task: "Unit test for unit conversion logic in tests/test_clean.py"

# Launch all models for User Story 1 together:
Task: "Implement 02_ingest_data.py"
Task: "Implement 03_clean_merge.py"
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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence