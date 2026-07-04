# Tasks: GC Content and Thermal Stability of Archaeal tRNA Stems

**Input**: Design documents from `/specs/001-gc-content-thermal-stability/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-674-gc-content-and-thermal-stability-of-arch/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, numpy, scipy, requests, biopython, statsmodels, dendropy, pyyaml, sklearn)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create data directory structure: `data/raw/`, `data/processed/`, `data/results/`, `data/metadata.json`
- [ ] T005 [P] Define `contracts/dataset.schema.yaml` for raw/processed tRNA data validation
- [ ] T006 [P] Define `contracts/analysis_output.schema.yaml` for statistical result validation
- [ ] T007 Create `code/utils.py` with logging, checksum generation (SHA-256), and validation helpers
- [ ] T008 Configure environment variable management for API keys (if needed) and database snapshot IDs
- [ ] T008b [US1] Update `research.md` Assumptions section to explicitly state: "Hydration conditions are inherent in the biological context of OGT values retrieved from literature/databases and are not experimentally controlled in this computational analysis."
- [ ] T009 Create `code/__init__.py` and package structure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download ≥30 archaeal species tRNA sequences and OGT metadata, parse stem regions, and compute GC percentages.

**Independent Test**: Verify script outputs a CSV with ≥30 species, valid OGT values, and stem GC percentages, and logs excluded species.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [ ] T011 [P] [US1] Unit test for stem parsing logic (cloverleaf model) in `tests/unit/test_parse_stems.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download.py`: Fetch tRNA sequences from GtRNAdb (real URL) and OGT metadata from BacDive/Literature (real CSV/JSON). Output to `data/raw/gtrnadb_raw.fasta`. Log database snapshot IDs. Validate output against `contracts/dataset.schema.yaml`.
- [ ] T013 [US1] Implement `code/parse.py`: Parse sequences using standard cloverleaf secondary structure models (config: `data/config/cloverleaf_model.json`) to identify D-stem, Anticodon-stem, Acceptor-stem. Compute GC% per stem. Output to `data/processed/stem_gc_parsed.csv`.
- [ ] T014 [US1] Implement `code/parse.py`: Handle edge cases (missing OGT, missing stem annotations) by excluding species and logging counts. Ensure final dataset ≥30 valid species.
- [ ] T015 [US1] Implement `code/analyze.py` (partial): Calculate composite stem GC (mean of all stems) and per-stem GCs. Store in `data/processed/stem_gc_data.csv`.
- [ ] T016 [US1] Add validation in `code/download.py` to match species IDs (Levenshtein > 0.9) and filter for OGT < 45°C and ≥ 45°C representation.
- [ ] T017 [US1] Add logging for excluded species and excluded tRNA types (FR-001, FR-002, FR-003).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Correlation Testing (Priority: P2)

**Goal**: Perform linear regression, multiple-comparison correction, and permutation testing to validate correlation between stem GC and OGT.

**Independent Test**: Verify permutation test executes ≥1000 iterations, outputs p-value, and applies correction.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_output_schema.py`
- [ ] T019 [P] [US2] Unit test for permutation test logic (≥1000 iterations) in `tests/unit/test_permutation.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/analyze.py`: Perform Weighted Least Squares (WLS) regression of OGT ~ Composite Stem GC, weighted by `tRNA_count`. Output r, p-value, 95% CI to `data/results/regression_stats.json`.
- [ ] T020b [US2] Implement `code/analyze.py`: Perform mandatory OLS regression of OGT ~ Composite Stem GC using `scipy.stats` (FR-004). Append results to `data/results/regression_stats.json` for comparison with WLS.
- [ ] T021 [US2] Implement `code/analyze.py`: Apply Benjamini-Hochberg correction for multiple stem-type tests (FR-005).
- [ ] T022 [US2] Implement `code/analyze.py`: Run permutation test (≥1000 iterations) shuffling GC values across species to generate null distribution and empirical p-value (FR-006). **MUST RUN UNCONDITIONALLY**, even if no phylogenetic tree is available. Append results to `data/results/regression_stats.json`.
- [ ] T023 [US2] Implement `code/analyze.py`: Append "CAUTION: Associational findings only..." to results JSON if no random assignment/identification strategy (FR-009).
- [ ] T024 [US2] Implement `code/analyze.py`: Calculate Minimum Detectable Effect Size (MDES) and record `[deferred]` for exact power calculations (FR-010).
- [ ] T025 [US2] Integrate with User Story 1 components (load `data/processed/stem_gc_data.csv`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Phylogenetic Controls and Sensitivity Analysis (Priority: P3)

**Goal**: Apply Phylogenetic Independent Contrasts (PIC) if tree available, and perform sensitivity analysis on thresholds.

**Independent Test**: Verify PIC runs if tree exists, sensitivity sweep reports variation in r and p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`
- [ ] T027 [P] [US3] Integration test for PIC execution path in `tests/integration/test_pic.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/analyze.py`: Attempt to load phylogenetic tree from `data/raw/archaea_tree.nwk`. If available, ultrametricize and compute PIC contrasts for GC and OGT. Run regression on contrasts (FR-007). If missing, log "PIC skipped; results associational" and ensure `data/results/regression_stats.json` reflects `pic_adjusted_r: null`.
- [ ] T029 [US3] Implement `code/analyze.py`: Ensure that if no tree is available, the **permutation test (T022) is NOT skipped**. Only the PIC step is skipped. Record the "Associational" flag in results.
- [ ] T030 [US3] Implement `code/analyze.py`: Perform sensitivity analysis sweeping min sequence length {low, medium, high} nt and regression methods {OLS, Huber}. Report variation in r and p-value to `data/results/sensitivity_report.json` (FR-008, SC-004).
- [ ] T031 [US3] Implement `code/analyze.py`: Handle tree subset mismatch (exclude species not in tree) and report subset N in `data/results/sensitivity_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation & Compliance (Priority: P2)

**Goal**: Finalize documentation and ensure all spec requirements are met.

### Implementation for Documentation

- [ ] T032 [US1] [Marie Curie] Verify and log sample size in `data/metadata.json`: Ensure ≥30 species are documented and report power limitations explicitly as per FR-010.
- [ ] T033 [US2] [Spec Compliance] Verify `data/results/regression_stats.json` contains all required fields: `pearson_r`, `p_value`, `ci_95`, `perm_p_value`, `pic_adjusted_r`, `associational_flag`.
- [ ] T034 [P] Documentation updates in `research.md` and `quickstart.md`
- [ ] T035 Code cleanup and refactoring in `code/`
- [ ] T036 Performance optimization (ensure pipeline runs <4h on free-tier)
- [ ] T037 [P] Additional unit tests for edge cases (missing data, empty trees) in `tests/unit/`
- [ ] T038 Run quickstart.md validation and ensure all artifacts checksummed
- [ ] T039 Generate final `data/results/analysis_report.json` with all stats, flags, and disclaimers

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Documentation (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (needs `stem_gc_data.csv`)
  - **T020b (OLS)** and **T020 (WLS)** and **T022 (Permutation)** are mandatory and independent of tree availability.
- **User Story 3 (P3)**: Depends on US2 (needs regression results) and US1 (needs tree data subset)
  - **T028 (PIC)** is conditional on tree availability.
- **Documentation (Phase 6)**: Can run in parallel with US2/US3 implementation as they are analysis extensions

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for stem parsing logic in tests/unit/test_parse_stems.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py"
Task: "Implement code/parse.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (≥30 species, valid GC%)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
   - Ensure T020b (OLS) and T022 (Permutation) are implemented as mandatory.
4. Add User Story 3 → Test independently → Deploy/Demo
   - Ensure T028 handles missing tree gracefully.
5. Add Documentation → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Stats - OLS, WLS, Permutation)
   - Developer C: User Story 3 (PIC/Sensitivity)
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
- **CRITICAL**: All data sources (GtRNAdb, BacDive) must be real, reachable URLs. No synthetic data.
- **CRITICAL**: All statistical methods must be CPU-tractable (no 8-bit quantization, no GPU).
- **CRITICAL**: Permutation test (T022) is MANDATORY regardless of tree availability. Only PIC (T028) is conditional.
- **CRITICAL**: OLS regression (T020b) is MANDATORY per FR-004.
- **CRITICAL**: Unapproved scope creep tasks (outlier analysis, scaling laws, H-bond energy) have been removed.