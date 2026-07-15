# Tasks: Predicting the Impact of Molecular Chirality on Flavor Perception

**Input**: Design documents from `/specs/001-predict-chirality-flavor/`
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

- [ ] T001a Create project directory structure per implementation plan (`projects/PROJ-202-predicting-the-impact-of-molecular-chira/`)
- [X] T001b Create `code/requirements.txt` with pinned dependencies (rdkit, openmm, mdanalysis, scikit-learn, pandas, numpy, pymc, vina, requests, chembl-webresource-client)
- [ ] T001c Create `.gitkeep` files in `data/raw`, `data/processed`, `data/interim`, `code`, `tests`
- [ ] T002 [P] Initialize Python 3.11 virtualenv and install dependencies from `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/interim`) with `.gitkeep`
- [X] T005 [P] Create `code/00_setup_env.py` to verify environment constraints (CPU-only, RAM < 7GB check)
- [ ] T006 [P] Implement random seed pinning utility (`code/utils/seeding.py`) for reproducibility
- [ ] T007 [P] [FR-001/Key Entities/Constitution VI] Create base data models for Enantiomeric Pair, Receptor Complex, and Sensory Rating (`code/models/data_models.py`) per `data-model.md`. **CRITICAL**: Implement receptor preparation logic to fetch raw AlphaFold PDB structures and process them using **RDKit/OpenMM** for CPU-tractability. **Do not** use Modeller; the pipeline MUST use raw AlphaFold models directly as authorized by the Plan.md "Constitution Deviation" to meet CPU time constraints.
- [ ] T008 [P] Configure logging infrastructure to `data/logs/pipeline.log`
- [ ] T009 [P] Setup environment configuration management (`.env` for API keys if needed, default paths)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Docking Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download aroma molecule data and olfactory receptor structures, perform CPU-only molecular docking to generate binding affinity predictions for enantiomeric pairs.

**Independent Test**: The pipeline downloads a fixed subset of molecules (10 enantiomeric pairs) and receptors (5), runs AutoDock Vina, and outputs a CSV of binding affinities within 2 hours on a CPU-only runner. [UNRESOLVED-CLAIM: c_6a489f2b — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data download validity in `tests/contract/test_data_download.py`
- [ ] T011 [P] [US1] Integration test for docking execution time limit in `tests/integration/test_docking_time.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/01_download_data.py`: Fetch ≤20 enantiomeric SMILES from FlavorDB/ChEMBL and ≤5 AlphaFold PDBs. Ensure real URLs are used.
- [ ] T013 [P] [US1] Implement `code/02_prepare_receptors.py`: Filter receptors based on pLDDT ≥ 70 in the binding pocket region (residues within 6.0 Å of ligand COM). **Dependency**: Must use **raw AlphaFold PDBs processed in T007**. Do not use Modeller.
- [ ] T014 [US1] Implement `code/03_dock_enantiomers.py`: Run AutoDock Vina in CPU-only mode (no CUDA) for all ligand-receptor combinations. Output raw scores and RMSD. **Logging**: Log the baseline threshold (0.5 kcal/mol) and note the sensitivity analysis range {0.4, 0.5, 0.6} from FR-007.
- [ ] T015a [P] [US1] [FR-009] Rank and select top 5 ligand-receptor pairs by docking score and save to `data/processed/top_5_pairs.csv` to produce the artifact required for T016 (validation).
- [ ] T016 [US1] Implement `code/07_validation_docking.py`: Run SMINA and PLANTS scoring functions on the top 5 ranked pairs for robustness validation (FR-009).
- [ ] T017 [US1] Implement error handling for docking failures (steric clashes) to log errors and assign null scores, excluding from mean calculation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - MD Refinement & Interaction Fingerprinting (Priority: P2)

**Goal**: Run short molecular dynamics simulations on the top-scoring docked complexes to extract interaction fingerprints and validate poses.

**Independent Test**: For the top 10 ranked ligand-receptor complexes, the system runs 1ns MD simulations using implicit solvent and outputs interaction fingerprint matrices within 3 hours.

**⚠️ CONSTITUTIONAL DEVIATION**: This task implements GBSA MD instead of TIP3P as mandated by Constitution VI.
**Amendment ID**: [PENDING]
**Deviation justification**: CPU-only constraints (2 cores, 7GB RAM) make 10ns TIP3P infeasible within 6h total runtime. 1ns GBSA serves as a "stability screen" to filter grossly unstable poses. Results labeled "preliminary stability indicators". **Receptor Source**: This task consumes the **raw AlphaFold PDBs processed in T007**, ensuring compliance with the Plan.md's approved deviation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for MD trajectory file generation in `tests/contract/test_md_output.py`
- [ ] T019 [P] [US2] Integration test for memory usage constraint (≤7GB) during MD in `tests/integration/test_md_memory.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/04_md_refinement.py`: Select top 10 complexes by docking score (depends on T014). **Input**: Must use **raw AlphaFold PDBs processed in T007**. Configure OpenMM with a nanosecond-scale duration and GBSA implicit solvent model.
- [ ] T021 [US2] Implement `code/04_md_refinement.py` to run simulations on 2 CPU cores and ensure completion within 3 hours total (FR-004).
- [ ] T022 [US2] Implement `code/interaction_fingerprint.py`: Parse MD trajectories to extract interaction frequencies and output summary CSV.
- [ ] T023 [US2] Add validation to ensure MD simulations do not exceed RAM limits and handle crashes gracefully.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Perception Correlation (Priority: P3)

**Goal**: Statistically compare enantiomeric binding differences and correlate them with human sensory ratings to determine if stereoselectivity predicts flavor perception nuances.

**Independent Test**: The analysis script performs paired Wilcoxon tests on docking scores and Spearman correlations with sensory ratings, outputting p-values and effect sizes. [UNRESOLVED-CLAIM: c_04dbe0e0 — status=not_enough_info]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for statistical output format in `tests/contract/test_analysis_output.py`
- [ ] T025 [P] [US3] Integration test for FDR correction logic in `tests/integration/test_fdr_correction.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/06_statistical_analysis.ipynb` (or script): Load docking scores and sensory ratings. Handle missing FlavorDB ratings by excluding pairs (FR-011 fallback logic if <50% coverage).
- [ ] T027 [US3] Implement paired Wilcoxon signed-rank tests to compare enantiomeric docking scores (associational framing) (FR-005).
- [ ] T028 [US3] Implement Benjamini-Hochberg FDR correction for multiple comparisons (FR-006).
- [ ] T029 [US3] Implement Spearman correlation analysis between binding differences and sensory ratings (FR-003/US-3).
- [ ] T030 [US3] Implement sensitivity analysis script to sweep binding affinity thresholds {0.4, 0.5, 0.6} kcal/mol and generate CSV mapping threshold to significance rates (`data/processed/sensitivity_analysis.csv`) (FR-007).
- [ ] T031 [US3] Implement bootstrapped resampling with 10,000 iterations (Constitution VII) to obtain 95% confidence intervals for effect sizes (FR-010). **Note**: The [deferred] iteration count is explicitly mandated by Constitution Principle VII, resolving the Spec's deferred status.
- [ ] T032 [US3] Implement fallback strategy: If FlavorDB coverage is low, switch to curated ChEMBL set with established sensory differences (FR-011).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T034a Refactor `code/01_download_data.py` (T012) to use the new logging utility from T008
- [ ] T034b Refactor `code/04_md_refinement.py` (T020) to optimize memory usage and ensure stability
- [ ] T035 Validate total pipeline runtime < 6 hours on free-tier runner (2 CPU, 7GB RAM)
- [ ] T036 [P] Additional unit tests for data parsing utilities in `tests/unit/`
- [ ] T037 Run quickstart.md validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (docked poses)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs

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
Task: "Contract test for data download validity in tests/contract/test_data_download.py"
Task: "Integration test for docking execution time limit in tests/integration/test_docking_time.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download_data.py"
Task: "Implement code/02_prepare_receptors.py"
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
- **Critical Constraint**: All tasks must be feasible on CPU-only free-tier runners (2 CPU, 7GB RAM). No GPU/CUDA, no 8-bit quantization, no large LLMs.
- **Constitution VI Compliance**: Per Plan.md deviation, receptor preparation MUST use **raw AlphaFold models directly** (processed via RDKit/OpenMM) instead of Modeller to meet CPU time constraints.