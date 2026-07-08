# Tasks: Predicting Molecular Complexity with Information Theory

**Input**: Design documents from `/specs/PROJ-431-predicting-molecular-complexity/`
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

- [ ] T001a Create project directory structure: `data/raw`, `data/processed`, `results/models`, `results/reports`, `results/plots`, `code`, `tests` (Reference: `projects/PROJ-431-predicting-molecular-complexity-with-inf/`)
- [ ] T001b Create `scripts/init_structure.sh` to automate directory creation and initial file scaffolding
- [X] T002 Create `code/requirements.txt` containing pinned versions of rdkit, pandas, numpy, scikit-learn, matplotlib, pyyaml
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils.py` for logging, SMILES validation (RDKit), file I/O, and **mandatory dataset verification hard gate**: Abort execution with error if input CSV lacks `smiles`, `logS`, or `logP` columns (FR-008, Plan: Dataset Verification)
- [X] T005 Create `code/entropy.py` skeleton with function signatures for `compute_atom_entropy` and `compute_bond_entropy` (FR-002, FR-003)
- [X] T006 Create `code/model.py` skeleton for Ridge Regression training and sensitivity analysis (FR-006, FR-011)
- [~] T007 Create `code/viz.py` skeleton for scatter plot generation with regression lines (FR-007)
- [~] T008 Create `code/cli.py` entry point with sub-commands `compute_entropy`, `train_model`, `plot_correlation` (FR-009)
- [~] T009 Setup data directory structure (`data/raw`, `data/processed`, `results/models`, `results/reports`, `results/plots`)
- [~] T034 [Rev] **Clarify Information Metrics (Code)**: Update `code/entropy.py` docstrings to explicitly document that "entropy" refers to **Shannon entropy of degree distributions** (topological) (FR-002, FR-003)
- [~] T035 [Rev] **Clarify Information Metrics (Doc)**: Update `docs/data-model.md` to explicitly document the entropy definition (FR-002, FR-003)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Information‑Theoretic Complexity Scores (Priority: P1) 🎯 MVP

**Goal**: Generate entropy-based complexity scores for a curated set of molecules.

**Independent Test**: Provide a CSV containing a representative set of SMILES strings; run the pipeline and verify that a new CSV with two additional columns (`atom_entropy`, `bond_entropy`) is produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Unit test for `compute_atom_entropy` logic in `tests/unit/test_entropy.py`
- [~] T011 [P] [US1] Unit test for `compute_bond_entropy` logic in `tests/unit/test_entropy.py`
- [~] T012 [P] [US1] Integration test for malformed SMILES handling (logging/skipping) in `tests/integration/test_cli.py`
- [~] T013 [P] [US1] Integration test for 10k molecule processing time limit (≤30 min) in `tests/integration/test_performance.py`. **Task**: Create `test_10k_molecules_under_30min` that loads a REAL 10k molecule dataset (or verified real-world proxy), runs `compute_entropy`, and asserts execution time < 1800s. (FR-001, SC-003)

### Implementation for User Story 1

- [~] T014 [US1] Implement `compute_atom_entropy` in `code/entropy.py` using RDKit atom degree distribution (FR-002)
- [~] T015 [US1] Implement `compute_bond_entropy` in `code/entropy.py` using RDKit bond degree distribution (FR-003)
- [~] T016 [US1] Implement `compute_entropy` CLI command in `code/cli.py` to read CSV, apply entropy functions, and write intermediate CSV. **Logic**: Handle missing row values (NaN) for `logS`/`logP` by skipping those rows for downstream modeling but preserving them in the entropy-only output. **Note**: This produces an intermediate artifact only. (FR-001, FR-005)
- [~] T017 [US1] **Implement metadata join logic** in `code/utils.py` or `code/cli.py` to merge the entropy-enriched CSV with `logS`/`logP` columns, producing the **final enriched CSV** required for US2 input. **Constraint**: This is the ONLY task that produces the final joined dataset. (FR-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train & Evaluate Ridge Regression Models (Priority: P2)

**Goal**: Assess whether entropy scores predict aqueous solubility (logS) and membrane permeability (logP) using Ridge Regression.

**Independent Test**: Using the output CSV from Story 1 (including `logS` and `logP` columns), run the `train_model` script and confirm that a model file is saved and a JSON report containing RMSE and Pearson r for each property is generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Unit test for 80/20 train/test split with seed 42 in `tests/unit/test_model.py`
- [~] T019 [P] [US2] Unit test for Bonferroni and Benjamini-Hochberg correction logic in `tests/unit/test_model.py`
- [~] T020 [P] [US2] Integration test for model training and report generation in `tests/integration/test_model.py`
- [~] T021 [P] [US2] Integration test for baseline comparison (Mean, MW+Atom Count) in `tests/integration/test_baseline.py`

### Implementation for User Story 2

- [~] T023 [US2] Implement `train_model` CLI command with 80/20 split (seed 42) and Ridge Regression (α=1.0) in `code/model.py`. **Input**: Requires output from T017 (`data/processed/enriched.csv`). (FR-005, FR-006)
- [~] T024 [US2] Implement calculation of RMSE and Pearson r on test set, saving `ridge_logS.pkl` and `ridge_logP.pkl` (FR-006)
- [~] T025 [US2] Implement baseline models (Mean, MW-only, MW+Atom Count) and Partial Correlation analysis to control for molecular size (Plan: Baseline & Confounding Control). **Output**: Generate baseline metrics for comparison. (Plan: Statistical Methodology)
- [~] T027 [US2] Implement sensitivity analysis sweep across alpha values spanning low, medium, and high magnitudes.. **Metric**: Calculate relative range ((max - min) / mean) for RMSE and Pearson r. **Output**: Append stability metrics to `results/reports/sensitivity_sweep.json`. (FR-011, SC-010)
- [~] T026 [US2] Implement JSON report generation. **Content**: Include RMSE, Pearson r, Bonferroni-adjusted p-values, **Benjamini-Hochberg (FDR) adjusted p-values**, and the **Entropy-vs-Size comparison table**. **Logic**: Evaluate Scientific Success Criterion (Entropy RMSE < Size baseline RMSE). **Output**: Save to `results/reports/metrics.json`. (FR-006, FR-010, Plan: Baseline & Confounding Control)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize Entropy vs. Physicochemical Properties (Priority: P3)

**Goal**: Visualize the relationship between entropy scores and target properties.

**Independent Test**: Invoke `plot_correlation` utility; verify PNG files with regression lines and R² annotations are created.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Unit test for plot rendering (labels, line, R²) in `tests/unit/test_viz.py`
- [~] T029 [P] [US3] Integration test for plot generation in `tests/integration/test_viz.py`

### Implementation for User Story 3

- [~] T030 [US3] Implement `plot_correlation` CLI command in `code/viz.py` to generate scatter plots (FR-007)
- [~] T031 [US3] Add logic to overlay linear regression line and annotate R² on plots (FR-007)
- [~] T032 [US3] Ensure plots are saved as PNG with ≥300 dpi resolution and proper axis labels (SC-004)
- [~] T033 [US3] Generate `entropy_vs_logS.png` and `entropy_vs_logP.png` for both entropy types (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Validation (Research Review Resolution)

**Purpose**: Address specific reviewer concerns regarding information-theoretic definitions and statistical rigor.

- [ ] T038 [P] [Rev] **Finalize Justification**: Update `docs/research.md` with the final justification based on actual correlation results (Plan: Justify Metric Selection)
- [ ] T039 [P] [Rev] **Explicitly Enumerate Candidate Measures**: In `docs/research.md`, create a section comparing Shannon Entropy (degree distribution), Mutual Information, and Algorithmic Complexity (Kolmogorov) to justify why Shannon degree entropy was chosen for solubility/permeability prediction, addressing the reviewer's concern about "formal framing" (Review: john-von-neumann-simulated)
- [ ] T040 [P] [Rev] **Define Structural vs. Functional Information**: In `docs/research.md`, add a subsection distinguishing "structural information" (topological graph properties) from "functional information" (physicochemical outcome) and explain how the chosen metric bridges this gap, directly addressing the reviewer's analogy to self-reproducing automata (Review: john-von-neumann-simulated)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `README.md` and `docs/quickstart.md`
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization across all stories
- [ ] T044 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Revision (Phase 6)**: Can run in parallel with implementation, but must be completed before final validation
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires entropy-enriched CSV from T017 as input)
- **User Story 3 (P3)**: Depends on US2 completion (requires model reports and enriched CSV)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T034/T035 which are sequential dependencies for implementation)
- All Revision tasks (Phase 6) can run in parallel with implementation tasks
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for compute_atom_entropy logic in tests/unit/test_entropy.py"
Task: "Unit test for compute_bond_entropy logic in tests/unit/test_entropy.py"

# Launch all models for User Story 1 together:
Task: "Implement compute_atom_entropy in code/entropy.py"
Task: "Implement compute_bond_entropy in code/entropy.py"
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
 - Developer B: User Story 2 (after T018/T019)
 - Developer C: User Story 3 (after T026)
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