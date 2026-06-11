---
description: "Task list for Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index"
---

# Tasks: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Input**: Design documents from `/specs/004-quantifying-the-complexity-of-knot-diagr/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `docs/` at repository root
- Paths shown below assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan with exact paths: code/, data/, data/raw/, data/processed/, data/plots/, docs/, docs/reproducibility/, docs/reproducibility/logs/, config/, tests/

---

## Phase 1.5: Plan Deliverables (Required by Project Structure)

**Purpose**: Create all documentation files listed in plan.md Project Structure

- [ ] T003a [P] Create quickstart.md per plan.md Project Structure
- [ ] T003b [P] Create data-model.md per plan.md Project Structure
- [ ] T003c [P] Create research.md per plan.md Project Structure
- [ ] T003d [P] Create contracts/ directory with contract files per plan.md Project Structure
- [ ] T003e [P] Implement Reference-Validator Agent integration for citation verification per Constitution Principle II

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create config/complexity_weights.yaml with default equal weights (1:1 ratio between crossing number and braid index)
- [ ] T005 [P] Implement utils/reproducibility_utils.py with random seed pinning, SHA-256 checksum computation for data files, content hash generation for all artifacts, artifact hash tracking in state file, and state file update logic when artifacts change per Constitution Principle V
- [ ] T006 [P] Implement utils/retry_utils.py with exponential backoff (initial delay=2s, max delay=[deferred], multiplier=2) per FR-010 and Reference-Validator integration from T003e
- [ ] T007 [P] Create base data models/entities (KnotRecord, InvariantsDataset) in code/data/
- [ ] T008 [P] Setup pytest test infrastructure in code/tests/
- [ ] T009 [P] Document measurement precision thresholds for all computed invariants in docs/reproducibility/derivation_notes.md per Constitution Principle VII; thresholds must be defined in config/complexity_weights.yaml before analysis begins
- [ ] T010 [P] Document error margins in classification with concrete numbers in docs/reproducibility/derivation_notes.md per Constitution Principle VII; reference config/complexity_weights.yaml for threshold values

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas/KnotInfo including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤13

**Independent Test**: Can be fully tested by executing the data download script and verifying the output contains all prime knots with crossing number ≤13 with consistent representation of crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields

### Implementation for User Story 1

- [ ] T011 [US1] Implement code/data/download_knot_data.py with retry logic (FR-010) and caching to data/raw/knot_atlas_export.csv
- [ ] T012 [US1] Implement code/data/parse_knot_data.py to extract crossing number, braid index, hyperbolic volume, alternating classification per FR-002
- [ ] T013 [US1] Filter dataset to include only prime knots with complete hyperbolic volume data (exclude torus/satellite) per FR-014, document excluded in docs/reproducibility/excluded_knots.md
- [ ] T014 [US1] Handle ambiguous/missing alternating classification: exclude or mark as "unclassifiable" per FR-012, log counts in docs/reproducibility/classification_counts.md
- [ ] T015 [US1] Apply tie-breaking rules (prefer braid word over DT code, lexicographically first DT code) per FR-013, document in docs/reproducibility/tie_breaking_rules.md
- [ ] T015a [US1] Implement code/data/validate_tie_breaking.py to automate tie-breaking rule consistency checks per SC-008, output validation log to docs/reproducibility/validation_status.md
- [ ] T016 [US1] Validate dataset completeness against KnotInfo/HTW enumeration for crossing number ≤10 per SC-001, document in docs/reproducibility/validation_scope.md
- [ ] T017 [US1] Generate SHA-256 checksums for all data files per FR-009, record in docs/reproducibility/checksums.md
- [ ] T018 [US1] Generate reproducibility logs with timestamp, operation, input_file, output_file, parameters, status, duration_ms per FR-009

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Additional Invariants and Perform Exploratory Analysis (Priority: P2)

**Goal**: Compute additional invariants (arc index, Seifert circle count, bridge number) and perform exploratory data analysis including stratified scatter plots

**Independent Test**: Can be fully tested by generating scatter plots and summary statistics showing the crossing number vs. braid index relationship for alternating knots separately from non-alternating knots, with at least 3 additional invariants computed per knot

### Implementation for User Story 2

- [ ] T019a [P] [US2] Implement code/data/compute_invariants.py arc index computation via Birman-Menasco method per FR-003
- [ ] T019b [P] [US2] Implement code/data/compute_invariants.py Seifert circle count via Seifert's algorithm per FR-003
- [ ] T019c [P] [US2] Implement code/data/compute_invariants.py bridge number via Schubert's decomposition per FR-003
- [ ] T020 [US2] Flag records with missing_invariant_flags when diagram representations unavailable per FR-011, document in docs/reproducibility/uncomputable_invariants.md
- [ ] T021 [US2] Validate algorithm implementation against primary mathematical literature definitions (Birman & Menasco 1988, Seifert 1934, Schubert 1956) per FR-003/Constitution Principle VI, document in docs/reproducibility/algorithm_validation.md
- [ ] T022 [US2] Document invariant algorithms in docs/reproducibility/invariant_algorithms.md with citations (Birman & Menasco 1988, Seifert 1934, Schubert 1956) and primary literature verification notes
- [ ] T023 [US2] Implement code/analysis/exploratory_analysis.py to generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating per FR-004
- [ ] T024 [US2] Save exploratory plots as PNG with minimum resolution 1200x900 pixels to data/plots/crossing_vs_braid_stratified.png per SC-009
- [ ] T025 [US2] Compute and document coverage metric for computable invariants per SC-006

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fit Regression Models and Validate Composite Complexity Score (Priority: P3)

**Goal**: Fit multiple regression models, construct composite complexity score, and validate against exploratory validation sample

**Independent Test**: Can be fully tested by executing the regression and validation pipeline on an exploratory validation sample and producing correlation coefficients and goodness-of-fit metrics

### Implementation for User Story 3

- [ ] T026a [P] [US3] Implement code/analysis/regression_models.py linear regression (OLS) per FR-005
- [ ] T026b [P] [US3] Implement code/analysis/regression_models.py polynomial regression (maximum degree=2) per FR-005
- [ ] T026c [P] [US3] Implement code/analysis/regression_models.py logarithmic regression (base e) per FR-005
- [ ] T027 [US3] Compute variance inflation factors (VIF) for all predictors, flag if VIF > 5 per FR-005
- [ ] T028 [US3] Implement residual analysis to identify knot families (pretzel, torus) that deviate from global trend per FR-005
- [ ] T029 [P] [US3] Implement code/analysis/composite_score.py with default equal weights (1:1) per FR-006
- [ ] T030 [US3] Configure composite score weights via config/complexity_weights.yaml per FR-006
- [ ] T031 [US3] Create exploratory validation sample using random stratified split by crossing number per FR-007
- [ ] T032 [US3] Validate composite score correlation with hyperbolic volume per FR-007/SC-003
- [ ] T033 [US3] Compute Pearson AND Spearman correlations per FR-008/SC-003 (mandatory dual correlation)
- [ ] T034 [US3] Implement ANOVA testing with Levene's test for equal variances and Shapiro-Wilk test for normality per FR-008/SC-011
- [ ] T035 [US3] Use robust alternatives (Welch's ANOVA, Kruskal-Wallis) if assumptions violated per FR-008
- [ ] T036 [US3] Report effect sizes (Cohen's d for group comparisons, r/r² for correlations) per FR-008/SC-011
- [ ] T037 [US3] Document model metrics (R², AIC/BIC, MAE) for all 3+ model types per SC-002

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Handle edge cases with documented fallback behaviors and produce complete reproducibility documentation

**Independent Test**: Can be fully tested by (1) simulating edge cases and verifying appropriate flags/logs, AND (2) verifying all reproducibility artifacts are present

### Implementation for User Story 4

- [ ] T038 [US4] Generate derivation notes in docs/reproducibility/derivation_notes.md with formula citations, step-by-step logic, parameter values per FR-009/SC-004
- [ ] T039 [US4] Create docs/reproducibility/validation_status.md with validation script results per SC-008
- [ ] T040 [US4] Document all edge cases and fallback behaviors in docs/reproducibility/edge_cases.md per US4; edge case categories: API failures, missing invariants, ambiguous classifications, hyperbolic volume undefined, tie-breaking conflicts

**Checkpoint**: All edge cases handled and reproducibility documentation complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Run pytest unit tests: pytest code/tests/unit/
- [ ] T042 [P] Run pytest contract tests: pytest code/tests/contract/
- [ ] T043 [P] Run quickstart.md validation if present
- [ ] T044 Run static analysis and fix all linting errors: flake8 code/ exits 0; black --check code/ exits 0
- [ ] T045 Verify all checksums match recorded values in docs/reproducibility/checksums.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Plan Deliverables (Phase 1.5)**: No dependencies - can run in parallel with Setup
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories MUST proceed sequentially in priority order (P1 → P2 → P3 → P4)
  - [P] tasks within a phase can run in parallel
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies (SEQUENTIAL ORDER)

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: MUST complete after User Story 1 (requires parsed dataset from T011-T018)
  - [P] marker on T019a-T019c means invariants can compute in parallel, but only AFTER US1 completes
- **User Story 3 (P3)**: MUST complete after User Story 2 (requires computed invariants and exploratory analysis from T019a-T025)
  - [P] marker on T026a-T026c means regression models can fit in parallel, but only AFTER US2 completes
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - independent but integrates with all stories

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Plan Deliverables tasks (T003a-T003e) can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, T009-T010 (precision thresholds) must complete before analysis
- Within US2, T019a-T019c can run in parallel (different algorithms in same file), but T020-T025 depend on T019a-T019c
- Within US3, T026a-T026c can run in parallel (different models in same file), but T027-T037 depend on T026a-T026c
- All tests for a user story marked [P] can run in parallel
- Different user stories MUST proceed sequentially (US1 → US2 → US3 → US4)

---

## Parallel Example: User Story 1

```bash
# Sequential: download MUST complete before parse
# T011: Implement code/data/download_knot_data.py with retry logic
#   → produces data/raw/knot_atlas_export.csv
# T012: Implement code/data/parse_knot_data.py to extract invariant fields
#   → depends on T011's output

# After download completes, parse→filter→validate can proceed in parallel:
# T012: Parse knot data
# T013: Filter dataset (requires parsed data)
# T014: Handle ambiguous classification (requires parsed data)
# T015: Apply tie-breaking rules (requires parsed data)
# T015a: Validate tie-breaking rules (requires parsed data)
# T016: Validate completeness (requires parsed data)
# T017: Generate checksums (requires all data files)
# T018: Generate reproducibility logs (requires all operations)
```

---

## Parallel Example: User Story 2

```bash
# T019a-T019c MUST complete before T020-T025 (all depend on computed invariants):
# T019a: Implement arc index computation via Birman-Menasco method
# T019b: Implement Seifert circle count via Seifert's algorithm
# T019c: Implement bridge number via Schubert's decomposition
#   → produces invariants_dataset.parquet

# After T019a-T019c complete, T020-T025 can proceed (but T023-T025 depend on T020-T022):
# T020: Flag missing invariants (requires T019a-T019c output)
# T021: Validate against primary literature (requires T019a-T019c output)
# T022: Document algorithms (requires T019a-T019c output)
# T023: Generate exploratory plots (requires T020-T022)
# T024: Save plots (requires T023)
# T025: Compute coverage metric (requires T019a-T019c output)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 1.5: Plan Deliverables
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (dataset downloaded, parsed, validated)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Plan Deliverables + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Sequential Team Strategy

With multiple developers (sequential US progression):

1. Team completes Setup + Plan Deliverables + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (data download/parsing)
   - Upon US1 completion: Developer B: User Story 2 (invariant computation)
   - Upon US2 completion: Developer C: User Story 3 (regression models)
   - Upon US3 completion: Developer D: User Story 4 (edge cases/reproducibility)
3. Stories complete sequentially to respect data flow dependencies

---

## Notes

- [P] tasks = different files or different algorithms within same file, no cross-dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **IMPORTANT**: User stories MUST proceed sequentially (US1 → US2 → US3 → US4) due to data flow dependencies
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Review Concerns Addressed**:
  - Dan Rockmore: Tasks T044 (linting errors) - now includes exact verification criteria
  - Marie Curie: Tasks T009-T010 (measurement precision, concrete numbers) - MOVED TO PHASE 2 with threshold location references
- **Data Flow Order**: Download (T011) → Parse (T012) → Filter/Validate (T013-T018) → Compute Invariants (T019a-T019c) → Exploratory Analysis (T020-T025) → Regression (T026a-T037) → Edge Cases/Reproducibility (T038-T040)
- **Constitutional Compliance**:
  - Principle II (Verified Accuracy): T003e implements Reference-Validator Agent integration
  - Principle V (Versioning): T005 includes content hash generation, artifact hash tracking in state file, and state file update logic per Constitution Principle V
  - Principle VI (Invariant Consistency): T021 validates against primary mathematical literature
  - Principle VII (Statistical Thresholds): T009-T010 establish precision thresholds before analysis with threshold location references