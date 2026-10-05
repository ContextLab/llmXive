# Tasks: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

**Input**: Design documents from `/specs/001-molecular-topology-selectivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**CRITICAL SPEC REVISION NOTICE**: The source `spec.md` currently mandates Poisson Regression (FR-004) which contradicts the `plan.md` (which deems it scientifically invalid). This `tasks.md` strictly follows the `plan.md` (Ordinal Logistic Regression). The `spec.md` MUST be revised in the next round to remove FR-004 and align with the Plan. Tasks T060 and T061 are added to drive this revision.

**Tests**: All test tasks listed below are REQUIRED to satisfy Constitution Principle I (Reproducibility).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-083-investigating-the-relationship-between-m/`) by executing: `mkdir -p code data/raw data/processed data/models tests code/utils docs/reports contracts` and verifying the tree matches `plan.md`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (rdkit, pandas, scikit-learn, statsmodels, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections and running `ruff init`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/`, `data/processed/`, `data/models/`, `code/`, `tests/` directory structure (Verify T001)
- [X] T005 [P] Implement base data loader and SMILES parser utility in `code/utils/smiles_parser.py`
- [X] T006 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T007 Create base schema definitions for `ReactionRecord` and `TopologicalDescriptor` in `contracts/` by creating `contracts/reaction_record.schema.yaml` and `contracts/topological_descriptor.schema.yaml` using YAML format.
- [X] T008 Setup environment configuration management for random seeds and file paths in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: Symmetry Group Definition & Invariance Validation (Priority: P2)

**Purpose**: Define the mathematical symmetry group and implement validation logic BEFORE any modeling or target extraction occurs. This resolves circular dependencies.

**Independent Test**: Verify that topological indices remain constant when the reactant graph is permuted by any element of the defined symmetry group.

### Implementation for Symmetry Group Definition

- [X] T043 [P] Define the mathematical symmetry group $G$ for Electrophilic Aromatic Substitution in `docs/reports/symmetry_group_definition.md`.
 - **Scope**: Must explicitly identify the group of graph automorphisms that preserve the aromatic ring structure and the electrophilic attack site.
 - **Constraint**: Must distinguish between global graph automorphisms and local site permutations.
 - **Deliverable**: File must contain: 1. Formal definition of group G, 2. List of generators, 3. Proof of invariance for Wiener index.
- [X] T044 [US2] Implement a `SymmetryValidator` class in `code/utils/symmetry.py` that takes a `ReactionRecord` and a `SymmetryGroup` definition.
 - **Function**: Apply all permutations in $G$ to the reactant graph and re-calculate Wiener, Balaban, and Zagreb indices.
 - **Assertion**: Assert that `index(original) == index(permutated)` for all $g \in G$.
 - **Refactor**: Extend preliminary checks from Phase 4 (T054-T056).
- [X] T045 [US2] Generate a "Coordinate Independence" report in `docs/reports/coordinate_independence_report.md`.
 - **Content**: For a random sample of molecules, demonstrate that indices are invariant under the defined group $G$.
 - **Failure Condition**: If any index varies, the task fails and logs the specific transformation causing the variance.
 - **Deliverable**: File must contain sections: 'Methodology', 'Sample Molecules', 'Variance Results', and report 'Max deviation < 1e-9 '.
- [X] T046 [US2] Refactor `code/descriptors.py` to cache index calculations based on the canonical graph representation (orbit representatives) to ensure efficiency during validation.
- [X] T047 [US3] Implement the "Symmetry Check" step in `code/modeling.py` (FR-008)
 - **Logic**: If `SymmetryValidator` (from T044) fails for >1% of the dataset, log a warning and switch to **Descriptive Statistics** (do NOT halt execution).
 - **Dependency**: Must run after T044 is complete.

**Checkpoint**: The project now explicitly defines the symmetry group and proves that the chosen topological indices are invariants under the relevant physical transformations.

---

## Phase 4: User Story 2 - Topological Descriptor Calculation & Symmetry (Priority: P2)

**Goal**: Compute Wiener, Balaban, and Zagreb indices for reactant molecules and verify symmetry invariance.

**Independent Test**: Run on benzene (Wiener=27), toluene (Wiener=33), nitrobenzene (Wiener=45)

### Tests for User Story 2 (REQUIRED)

- [X] T016 [P] [US2] Unit test for Wiener index calculation on reference molecules in `tests/unit/test_descriptors.py`
- [X] T017 [P] [US2] Unit test for Balaban and Zagreb index calculations in `tests/unit/test_descriptors.py`
- [X] T018 [P] [US2] Performance test ensuring full filtered EAS set calculation < 15 mins on 2-core runner in `tests/perf/test_descriptor_perf.py`
- [X] T019 [P] [US2] Unit test for graph automorphism detection in `tests/unit/test_symmetry.py`

### Implementation for User Story 2 & Symmetry (FR-002, FR-008)

- [X] T020 [US2] Implement Wiener index calculator in `code/descriptors.py` (FR-002)
- [X] T021 [US2] Implement Balaban index calculator with graph connectivity checks in `code/descriptors.py` (FR-002)
- [X] T022 [US2] Implement Zagreb index calculator in `code/descriptors.py` (FR-002)
- [ ] T023 [US2] Implement logic to flag "invalid topology" for disconnected graphs, exclude from analysis, and log to `data/processed/disconnected_graphs.csv` with checksum (FR-002).
 - **Output Schema**: CSV must have columns: `smiles`, `reaction_id`, `error_type`.
- [ ] T054 [P] [US2] Unit test `test_wiener_invariance_permutation` in `tests/unit/test_index_stability.py`
 - **Logic**: Verify Wiener index remains constant under graph permutation.
- [ ] T055 [P] [US2] Unit test `test_balaban_invariance_permutation` in `tests/unit/test_index_stability.py`
 - **Logic**: Verify Balaban index remains constant under graph permutation.
- [ ] T056 [P] [US2] Unit test `test_zagreb_invariance_permutation` in `tests/unit/test_index_stability.py`
 - **Logic**: Verify Zagreb index remains constant under graph permutation.
- [ ] T024 [US2] Implement **Preliminary** graph automorphism detection using `rdkit` or `networkx` to verify molecule canonicalization in `code/utils/symmetry.py` (FR-008).
 - **Note**: This task now depends on T043 (Formal Group Definition) which is in Phase 3.
- [ ] T025 [US2] Add explicit **Preliminary** invariance check: Calculate indices for a molecule and its canonicalized form; assert equality in `code/utils/symmetry.py` (FR-008).
- [ ] T026 [US2] Implement **Preliminary** sensitivity analysis: Rotate/permute molecular graph representation and verify index stability in `code/utils/symmetry.py` (FR-008).
- [ ] T027 [US2] Write descriptor table to `data/processed/descriptors.csv` with checksum generation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, and preliminary symmetry invariance is verified.

---

## Phase 5: User Story 1 - Data Ingestion and Reaction Filtering (Priority: P1) 🎯 MVP

**Goal**: Download USPTO dataset, parse SMILES, filter for EAS reactions, and ensure data integrity.

**Independent Test**: Run ingestion on a small subset; verify output CSV contains only EAS reactions and row count matches expected subset size.

### Tests for User Story 1 (REQUIRED)

- [ ] T009 [P] [US1] Contract test for EAS pattern matching in `tests/unit/test_ingestion.py`
- [ ] T010 [P] [US1] Integration test for full ingestion pipeline on small subset in `tests/integration/test_ingestion_pipeline.py`
 - **Execution note**: This test MUST run after T011-T015 are complete to verify the implementation.

### Implementation for User Story 1

- [ ] T011 [US1] Implement USPTO-50k downloader in `code/ingestion.py` (FR-001)
- [ ] T012 [US1] Implement SMILES parser with error handling for malformed data in `code/ingestion.py` (FR-006)
- [ ] T013 [US1] Implement EAS pattern matcher (aromatic ring + electrophilic substitution logic) in `code/ingestion.py` (FR-001)
- [ ] T014 [US1] Implement logic to log critical errors and halt if N_EAS < `MIN_EAS_COUNT` in `code/ingestion.py`.
 - **Function Signature**: `def validate_eas_count(df: pd.DataFrame) -> None`.
 - **Gate Logic**: If `len(df) < MIN_EAS_COUNT` (read from `code/config.py`), raise `SystemExit(1)` with message "ERROR: N_EAS < MIN_EAS_COUNT. Pipeline halted." to prevent Phase 5 execution.
- [ ] T015 [US1] Write filtered dataset to `data/processed/eas_reactions.csv` with checksum generation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.
**Critical Dependency Note**: Phase 7 (Modeling) depends on Phase 5 completion AND N_EAS >= `MIN_EAS_COUNT`.

---

## Phase 6: User Story 3 - Statistical Modeling and Validation (Priority: P3)

**Goal**: Model relationship between topology and selectivity using Ordinal Logistic Regression and Random Forest Classifier (only if Ordinal Logistic fails) with proper symmetry checks. **Depends on Phase 3 (Symmetry) and Phase 5 (Data) completion.**

**Independent Test**: Run on synthetic dataset with deterministic symmetry-based target; verify model recovers known distribution patterns.

### Tests for User Story 3 (REQUIRED)

- [ ] T028 [P] [US3] Contract test for Ordinal Logistic Regression training in `tests/unit/test_modeling.py`
- [ ] T029 [P] [US3] Contract test for Random Forest classification in `tests/unit/test_modeling.py`
- [ ] T030 [P] [US3] Contract test for Descriptive Statistics fallback in `tests/integration/test_modeling_fallback.py`
- [ ] T031 [P] [US3] Synthetic test with deterministic symmetry-based target generation in `tests/unit/test_modeling_synthetic.py`
 - **Logic**: Generate target via deterministic symmetry class logic (not Poisson).

### Implementation for User Story 3

- [ ] T032 [US3] Implement **selectivity target** extraction (Regioisomer Diversity Count from reactant symmetry) in `code/modeling.py` (FR-003).
 - **Algorithm**: Calculate graph automorphism orbits on reactant aromatic ring to determine non-equivalent sites.
 - **Logic**: Target is **always** derived from reactant symmetry. No "default to 0" fallback.
 - **Function Signature**: `def calculate_regioisomer_count(smiles: str) -> int` in `code/modeling.py` and add column `target_count` to the processed DataFrame.
 - **Depends on**: T043 (Symmetry Group Definition) and T015 (Filtered Dataset).
- [ ] T033 [US3] Implement **Ordinal Logistic Regression** model in `code/modeling.py` (Plan Requirement)
- [ ] T035 [US3] Implement 5-fold CV logic with automatic switch to LOO if N < 20 in `code/modeling.py` (FR-005)
- [ ] T036 [US3] Implement VIF calculation for collinearity diagnostics and sequential analysis logic if VIF > 5 in `code/modeling.py`
- [ ] T037 [US3] Implement degenerate target detection (variance=0) and switch to **Descriptive Statistics** in `code/modeling.py` (FR-007)
 - **Note**: Zero-Inflated Poisson and Binary Classification are explicitly excluded per Plan.
- [ ] T038 [US3] Implement Bonferroni-corrected significance testing (p < 0.0167) and report generation in `code/modeling.py`
- [ ] T039 [US3] Evaluate R² against SC-002 threshold (R² > 0.05). If MDE is unachievable, calculate the MDE value, report descriptive statistics, log the MDE value and explicit "Project Analysis Complete" state in `data/models/results.json` (SC-002).
 - **Gate Logic**: If MDE is unachievable, output descriptive statistics and log state; do NOT exit with code 1. The exit code 0 indicates a valid scientific outcome (underpowered study), not a failure.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Research Revision & Reporting (Priority: P2)

**Goal**: Finalize reports, documentation, and validation based on completed modeling.

- [ ] T041 [US3] Update `research.md` to explicitly state that indices are invariant under the defined symmetry group, addressing the "coordinate-dependent artifact" concern
- [ ] T042 [US3] Generate final summary report in `docs/reports/` including sensitivity analysis results (T044, T045)
- [ ] T060 [P] Update `spec.md` and `research.md` to explicitly remove the Poisson Regression requirement (FR-004) and update the synthetic test description (User Story 3) to reflect the deterministic symmetry-based generation logic.
 - **Reason**: Resolves the contradiction between spec and plan.
- [ ] T061 [P] Update `spec.md` and `data-model.md` to remove the "default to 0" fallback description for the target variable.
 - **Reason**: Resolves the contradiction between spec and plan regarding target derivation.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Update `docs/quickstart.md` with symmetry analysis instructions (from T043-T047)
- [ ] T049 [P] Update `docs/data-model.md` with FR-008 invariance definitions
- [ ] T050 [P] Remove unused imports in `code/ingestion.py`, `code/descriptors.py`, `code/modeling.py`
- [ ] T051 [P] Refactor descriptor functions in `code/descriptors.py` for readability and modularity
- [ ] T052 [P] Run quickstart.md validation
- [ ] T053 [P] Verify descriptor calculation time < 15 mins on full filtered EAS set (SC-003) in `tests/perf/test_descriptor_perf.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Symmetry Validation (Phase 3)**: Depends on Phase 2. **CRITICAL**: Must complete before Phase 6 (Modeling) and Phase 5 (Data Ingestion) to provide the SymmetryGroup definition.
- **User Stories (Phase 5+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **User Story 3 (Phase 6)**: Depends on Phase 5 (Data), Phase 4 (Descriptors), and Phase 3 (Symmetry Check).
 - **Critical**: Phase 6 requires Phase 3 completion (Symmetry Check).
- **Research Revision (Phase 7)**: Depends on Phase 4 (US2 Descriptors + Symmetry) and Phase 6 (US3 Modeling)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (data), US2 (descriptors + symmetry), and Phase 3 (Symmetry Check).
 - **Critical**: Phase 6 requires Phase 5 completion AND N_EAS >= `MIN_EAS_COUNT` (enforced by T014).
 - **Critical**: Phase 6 requires Phase 3 completion (Symmetry Check).
- **Research Revision (P2)**: Depends on US2 completion to verify invariance
- **Symmetry Validation (P2)**: Depends on US2 (T020-T022) to have working descriptor calculators

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD)
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
# Launch all tasks for User Story 1 together (if tests requested):
Task: "Contract test for EAS pattern matching in tests/unit/test_ingestion.py"
Task: "Integration test for full ingestion pipeline in tests/integration/test_ingestion_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement USPTO-50k downloader in code/ingestion.py"
Task: "Implement SMILES parser in code/ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: Symmetry Definition (Required for modeling logic)
4. Complete Phase 5: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Phase 3 (Symmetry) → Define group G
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Descriptors + Symmetry)
 - Developer C: Phase 3 (Symmetry Group Definition & Validation)
 - Developer D: User Story 3 (Modeling - waits for Phase 3)
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
- **Critical Revision**: Tasks T024-T026 and Phase 3 (T043-T047) address the "invariance under transformation" concern raised in the prior research review by **albert-einstein-simulated**. These must be completed to validate the scientific premise that topological indices are not coordinate-dependent artifacts.
- **FR-008**: Added to authorize Symmetry Invariance Analysis tasks (per Plan.md Critical Scope Clarification).
- **Phase 3**: Specifically addresses the reviewer's request to "explicitly define the symmetry group and demonstrate that the chosen indices are invariant under the transformations that the electron density undergoes during the electrophilic attack."
- **Plan Alignment**: All Poisson Regression and Zero-Inflated Poisson tasks have been removed per the Plan's "Critical Scope Clarification" which deems them scientifically invalid for the deterministic target. Replaced with Ordinal Logistic Regression and Descriptive Statistics.
- **Phase Ordering**: Phase 3 (Symmetry Validation) now runs BEFORE Phase 6 (Modeling) to resolve circular dependencies.
- **T034 Removal**: Random Forest Regression (T034) was removed as it violates the Plan's rejection of regression on deterministic targets.
- **T039 Update**: T039 no longer halts the pipeline on low R²; it outputs descriptive statistics and logs MDE as per Plan.
- **T014 Update**: T014 now explicitly raises SystemExit(1) if N_EAS < `MIN_EAS_COUNT` (configurable).
- **T023 Update**: T023 now logs disconnected graphs to a specific file with checksum and schema.
- **T027 Update**: T027 now includes checksum generation.
- **T032 Update**: T032 now explicitly describes the graph automorphism algorithm and function signature.
- **T018/T053 Update**: Performance tests now specify "full filtered EAS set".
- **T035 Update**: T035 now specifies "N < 20" threshold for LOO.
- **T040/T047 Update**: Symmetry Check logic moved to Phase 3 (T047) to ensure it is available before Phase 6 starts.
- **T040 Removal**: T040 was removed from Phase 5 to resolve circular dependency; logic consolidated into T047 (Phase 3).
- **T054-T056 Update**: Renamed from T044-T046 to avoid ID collision with Phase 3 implementation tasks.
- **T060/T061 Update**: Added to explicitly drive the necessary spec revisions.