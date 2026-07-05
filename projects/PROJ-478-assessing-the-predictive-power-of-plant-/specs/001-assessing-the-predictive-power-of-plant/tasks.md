# Tasks: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

**Input**: Design documents from `/specs/feat-assess-plant-traits/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `src/`, `src/data/`, `src/modeling/`, `src/analysis/`, `src/utils/` directories
- [X] T001b [P] Create `data/raw`, `data/processed`, `data/metadata`, `results` directories
- [X] T001c [P] Create `tests/unit`, `tests/integration`, `tests/contract` directories
- [X] T002 Initialize a Python project with dependencies in `requirements.txt` (scikit-learn, pandas, geopandas, rasterio, rasterstats, pyyaml, requests, tqdm, numpy, statsmodels, linearmodels)
- [X] T003 [P] Configure linting (flake/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/utils/config.py` with constants, random seeds, and resource limits (max_depth=10, n_estimators=100)
- [~] T005 [P] Implement `src/utils/logging.py` for structured logging and provenance tracking
- [~] T007 Implement `src/data/loaders.py` for raster loading utilities and coordinate alignment checks
- [~] T008 Implement `src/data/preprocess.py` for spatial thinning (default 10 km, min 1 km) and density-based background sampling using exactly **[deferred] points** per species (as per Spec Assumptions)
- [~] T009 Setup environment configuration management and checksum verification for raw downloads

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate a climate‑only SDM for a single species (Priority: P1) 🎯 MVP

**Goal**: Establish a baseline SDM using only climate variables for a single species (e.g., *Helianthus annuus*) to serve as a reference point.

**Independent Test**: Run the workflow for one species and verify that a cleaned occurrence file, climate rasters, and cross‑validated AUC/TSS values are produced, retaining ≥80% of raw records.

### Tests for User Story 1

- [~] T010 [P] [US1] Unit test for spatial thinning logic in `tests/unit/test_preprocess.py` (verify record retention ≥80%)
- [~] T011 [P] [US1] Integration test for GBIF fetch and cleaning in `tests/integration/test_fetch_gbif.py` (verify duplicate removal and coordinate validity)

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `src/data/fetch_gbif.py` to retrieve records, remove duplicates, and apply spatial thinning (FR-001)
- [~] T013 [P] [US1] Implement `src/data/fetch_climate.py` to download WorldClim v2.1 rasters covering the convex hull and align to occurrences (FR-002) <!-- FAILED: unspecified -->
- [~] T014 [US1] Implement `src/modeling/train_rf.py` for training a Random Forest classifier (climate-only) using **5-fold cross-validation** (per Spec Constitution) to calculate AUC and TSS (SC-001, SC-002)
- [~] T015 [US1] Implement `src/modeling/metrics.py` to calculate and report AUC and TSS values (SC-001, SC-002)
- [~] T016 [US1] Add error handling for "No occurrence records" and "Model training failure" (retry with reduced max_depth)
- [~] T017 [US1] Add logging for data provenance and thinning statistics <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 8, column 1:
 The code uses only imports from...
 ^
could not find expected ':'
 in "<unicode string>", line 8, column 245:
... statistics as specified in US1.
 ^) -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Add functional trait covariates and re‑train the SDM (Priority: P2)

**Goal**: Augment the climate-only model with species-level functional traits.
**Critical Note**: The Spec (FR-004) mandates using **known trait values** for the held-out species. The Plan's "Trait Imputation" strategy is implemented as an optional validation step (T021b) to avoid circularity, but the primary task (T021a) must satisfy the Spec requirement.

**Independent Test**: Run the workflow for a subset of species using LOSO; verify that the model uses **known** trait values for the test species (Spec) and optionally compare with imputed traits (Plan).

### Tests for User Story 2

- [~] T018 [P] [US2] Unit test for TRY data fetching and source verification (Handbook 2013) in `tests/unit/test_fetch_traits.py`
- [~] T019 [P] [US2] Integration test for LOSO loop logic in `tests/integration/test_loso_cv.py` (verify **known trait values** usage for test set per Spec FR-004)

### Implementation for User Story 2

- [~] T020 [P] [US2] Implement `src/data/fetch_traits.py` to retrieve SLA, seed mass, and plant height from TRY public subset; verify source metadata and explicitly flag values as **'unverified protocol'** if source is not 'Handbook 2013' (FR-003, FR-010)
- [~] T022a [US2] Implement `src/analysis/collinearity.py` to merge climate and trait data for the full predictor set across all species (prerequisite for VIF)
- [~] T022 [US2] Implement `src/analysis/collinearity.py` to compute Variance Inflation Factor (VIF) for the full predictor set using the merged data from T022a and flag VIF > 5 (FR-011, SC-005)
- [~] T023 [US2] Implement logic to flag/exclude species with missing traits and log exclusion reasons (FR-006)
- [~] T021a [US2] Implement `src/modeling/loso_cv.py` to orchestrate the full LOSO cycle: train on N-1 species, **use the known trait values** of the 1 held-out species as inputs, and evaluate (FR-004, US-2)
- [~] T021b [US2] Implement `src/modeling/loso_cv.py` (optional branch) to **predict traits** for the held-out species using a climate-niche model trained on N-1 species (Plan Override of FR-004), and evaluate using these imputed values <!-- ATOMIZE: requested -->
- [~] T024 [US2] Integrate both **known** (T021a) and **imputed** (T021b) trait data into the Random Forest training pipeline for the "climate + traits" configuration, ensuring the Spec-compliant path (known values) is the default
- [~] T025 [US2] Add explicit disclaimer logic in the report generation to frame relationships as associative, not causal (FR-007)
- [~] T025b [US2] Add explicit documentation in the final report explaining the **Trait Imputation** strategy as a Plan override of Spec FR-004 to ensure scientific validity
- [~] T025c [US2] Create a formal note in `research.md` or `plan.md` documenting the Spec-Plan divergence regarding Trait Imputation (FR-004 override) to ensure traceability

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Conduct a comparative statistical analysis across 50 species (Priority: P3)

**Goal**: Evaluate at the community level whether trait-augmented models outperform climate-only models using **paired two-sided t-test** (Spec FR-005) and sensitivity analysis. The Plan's LMM is an additional analysis step (T028b).

**Independent Test**: Execute the full pipeline for all focal species, run the paired t-test with Bonferroni correction, and verify sensitivity analysis results meet success criteria.

### Tests for User Story 3

- [~] T026 [P] [US3] Unit test for t-test logic and Bonferroni correction in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T028a [US3] Implement `src/analysis/stats.py` to perform **paired two-sided t-test** on AUC/TSS differences across species, apply **Bonferroni correction**, and calculate **Cohen's d** (FR-005, FR-008, SC-003)
- [ ] T028b [US3] Implement `src/analysis/stats.py` (optional branch) to perform **Linear Mixed-Effects Modeling (LMM)** with random species effects to account for non-independence (Plan Override of FR-005)
- [ ] T029 [US3] Report fixed effects, variance components (if LMM used), **Bonferroni-corrected p-values**, and **Cohen's d** from the t-test (FR-005, SC-003)
- [ ] T030 [US3] Implement sensitivity analysis sweep over thresholds {0.01, 0.02, 0.05} to verify direction of improvement consistency **≥ 67% (at least 2 out of 3)** and generate the specific sensitivity table (FR-009, SC-004)
- [ ] T031 [US3] Generate final JSON/CSV reports: `results/model_results.json`, `results/stats_report.json`, `results/sensitivity_analysis.json`
- [ ] T032 [US3] Add validation to ensure all VIF > 5 findings are reflected in the final report with appropriate caveats (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033 [P] Documentation updates in `docs/` including data provenance and methodology notes
- [ ] T034 [P] Implement **chunked loading** in `src/data/loaders.py` to ensure memory usage stays within acceptable limits during LOSO
- [ ] T035 [P] Implement **sequential species iterator** in `src/modeling/loso_cv.py` to manage RAM during full pipeline execution
- [ ] T036 [P] Additional unit tests for edge cases (missing traits, zero records) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure the full pipeline executes within 6 hours on CPU-only runner
- [ ] T038 Verify reproducibility by re-running with fixed seeds and comparing checksums

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1's data fetching logic for climate
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2's model results

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
Task: "Unit test for spatial thinning logic in tests/unit/test_preprocess.py"
Task: "Integration test for GBIF fetch and cleaning in tests/integration/test_fetch_gbif.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/fetch_gbif.py"
Task: "Implement src/data/fetch_climate.py"
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
- **Critical**: All Random Forest training must use `max_depth=10` and `n_estimators=100` to comply with CPU-only runner constraints.
- **Critical**: **Spec FR-004 Compliance**: The primary LOSO task (T021a) MUST use **known trait values** for the held-out species. The Plan's "Trait Imputation" (T021b) is an optional validation step.
- **Critical**: **Spec FR-005 Compliance**: The primary statistical task (T028a) MUST implement the **paired two-sided t-test** with Bonferroni correction and Cohen's d. The Plan's LMM (T028b) is an optional add-on.
- **Critical**: **Sensitivity Analysis**: Task T030 MUST verify the **≥ 67% (2 out of 3)** consistency metric across thresholds.
- **Critical**: **Data Hygiene**: Task T008 MUST use exactly **[deferred] background points**.
- **Critical**: **Trait Verification**: Task T020 MUST flag 'unverified protocol' for non-Handbook 2013 sources.