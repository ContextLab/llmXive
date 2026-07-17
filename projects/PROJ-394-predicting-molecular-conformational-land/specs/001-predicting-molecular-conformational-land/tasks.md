# Tasks: Predicting Molecular Conformational Landscapes with Variational Autoencoders

**Input**: Design documents from `/specs/001-predict-conformer-vae/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-394-predicting-molecular-conformational-land/`) by executing: `mkdir -p code/{data,models,utils,tests/unit,tests/integration} data/raw data/processed docs && touch code/__init__.py code/utils/__init__.py code/models/__init__.py code/data/__init__.py code/tests/__init__.py code/tests/unit/__init__.py code/tests/integration/__init__.py`
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`. **IMPORTANT**: Do NOT include `xtb` in `requirements.txt` as it is a C++ binary. Instead, add a comment in `requirements.txt` and a script `code/scripts/install_xtb.sh` that installs `xtb` via `conda-forge` (preferred) or system package manager (apt) as per Spec Assumptions. Python deps: `torch==2.3.0`, `rdkit==2024.3.1`, `joblib==1.4.2`, `statsmodels==0.14.2`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `huggingface-hub==0.23.4`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement global seed setting utility in `code/utils/seeds.py` (numpy, torch, python random)
- [X] T005 [P] Setup structured logging in `code/utils/logging.py` (JSON format, file + console handlers)
- [X] T006 [P] Create base data schema in `code/contracts/molecule.schema.yaml` (JSON Schema) with properties: `smiles` (string), `graph` (object), `latent_vector` (array of 64 floats), `conformer_set` (array of objects)
- [X] T007 [P] Create metrics schema in `code/contracts/metrics.schema.yaml` (JSON Schema) with properties: `spearman_rho` (float), `p_value` (float), `confidence_interval` (array of 2 floats)
- [X] T008 [P] Setup environment configuration management in `code/config.py` (paths, hyperparameters, CPU thread limits)
- [X] T009 [P] Implement robust error handling wrapper for `xtb` subprocess calls in `code/data/energy_calc.py` (retry logic, timeout, logging)
- [X] T009b [P] [Constitution VI] Implement `code/data/xtb_metadata.py` to capture, version, and archive the exact `xtb` command-line flags, convergence criteria, and version info for every calculation into `data/calculation_metadata/` as required by Constitution Principle VI.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Train a graph‑based VAE on 2D molecular graphs (Priority: P1) 🎯 MVP

**Goal**: Train a Variational Autoencoder that consumes only 2‑D graph representations (derived from SMILES) to learn a latent space encoding structural information.

**Independent Test**: Run the training pipeline on a curated subset of the ZINC15 dataset and verify that the loss converges and a saved checkpoint is produced.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for SMILES-to-graph conversion in `code/tests/unit/test_data_loader.py` (assert graph properties match input)
- [ ] T011 [P] [US1] Unit test for VAE architecture (encoder/decoder) shapes in `code/tests/unit/test_vae.py` (assert latent dim=64, reconstruction matches input dim)
- [ ] T012 [US1] Integration test for training loop on A set of molecules in `code/tests/integration/test_training.py` (Depends on T017; asserts checkpoint exists, loss ≤ 0.15)

### Implementation for User Story 1

- [ ] T013 [US1] Implement ZINC15 data download script in `code/data/download_zinc.py` using HuggingFace `datasets.load_dataset('zinc15', split='train')`, verify canonical source match per Constitution Principle I, and save checksums to `data/checksums.json`
- [ ] T013b [P] [US1] Verify ZINC15 source match: Write a script to confirm `zinc15` dataset ID maps to the canonical ZINC15 source URL as required by Constitution Principle I, logging the result
- [ ] T014 [P] [US1] Implement SMILES to RDKit Graph conversion in `code/data/preprocess.py` (FR-001)
- [ ] T015 [US1] Implement MPNN Encoder and Decoder in `code/models/vae.py` (2 layers, A hidden dimension of moderate size will be employed to balance model capacity and computational efficiency., ReLU activation, A latent space of appropriate dimensionality will be employed to encode the data structure., CPU-only)
- [ ] T016 [US1] Implement training loop in `code/train.py` (CPU threads=2, batch size tuned for <7GB RAM, seed pinned)
- [ ] T017 [US1] Implement checkpoint saving and loading logic in `code/train.py` (save `vae_checkpoint.pt` with optimizer state and epoch)
- [ ] T018 [US1] Implement inference script to encode held-out SMILES in `code/models/vae.py` (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predict conformer‑energy rankings from latent vectors (Priority: P1)

**Goal**: Generate an initial conformer ensemble, optimize with GFN2-xTB, and predict energy rankings using the VAE latent vector.

**Independent Test**: For a test molecule, generate an initial conformer ensemble, perform multi-start geometry optimization using GFN2-xTB, obtain the VAE latent vector, rank conformers, and compute Spearman ρ.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for GFN2-xTB wrapper in `code/tests/unit/test_energy_calc.py` (run real xtb on benzene, verify energy output format)
- [ ] T020 [P] [US2] Unit test for Spearman correlation and Bonferroni correction in `code/tests/unit/test_metrics.py`
- [ ] T021 [US2] Integration test for end-to-end ranking on a single molecule in `code/tests/integration/test_ranking.py` (Depends on T023, T025)

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement ETKDG conformer generation in `code/data/preprocess.py` (a limited set of conformers, seed pinned)
- [ ] T023 [US2] Implement GFN2-xTB geometry optimization wrapper in `code/data/energy_calc.py` (parallelized via joblib n_jobs=2, FR-004, calls T009b for metadata logging)
- [ ] T024 [US2] Implement linear regression head for energy prediction in `code/models/linear_head.py` (input dim=64, output dim=1)
- [ ] T025 [US2] Implement end-to-end ranking pipeline in `code/evaluate.py` (latent vector -> predicted scores via T024 -> rank, Depends on T017, T024)
- [ ] T026 [US2] Implement Spearman ρ and Bonferroni-adjusted p-value calculation in `code/evaluate.py` (FR-005, FR-008)
- [ ] T027 [US2] Implement sensitivity analysis loop in `code/evaluate.py` explicitly sweeping α over a range of small numeric values (FR-010) and saving results to `data/sensitivity_analysis.json` with columns `alpha`, `p_value`, `rho`.
- [ ] T028 [US2] Implement power analysis function in `code/evaluate.py` using `statsmodels`, {{claim:c_16294c32}} (Wikipedia: Statistical significance, https://en.wikipedia.org/wiki/Statistical_significance), power=0.8) and save report to `data/power_analysis_report.txt` (FR-012)
- [ ] T029 [US2] Implement workflow success rate validation (≥95% success) in `code/data/energy_calc.py` (FR-011)

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Benchmark against baseline models and perform ablations (Priority: P2)

**Goal**: Compare VAE performance against ECFP4 fingerprints and random vectors, and test if adding 3D descriptors improves results.

**Independent Test**: Run three parallel experiments (VAE, Fingerprint, Random) and an ablation (VAE+3D), reporting Spearman ρ for each.

### Tests for User Story 3

- [ ] T030 [P] [US3] Unit test for ECFP4 fingerprint generation in `code/tests/unit/test_baselines.py`
- [ ] T031 [P] [US3] Integration test for baseline comparison table generation in `code/tests/integration/test_benchmarks.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement ECFP4 fingerprint regression baseline in `code/evaluate.py` (Depends on T017, T025) (FR-006)
- [ ] T033 [US3] Implement random latent vector baseline in `code/evaluate.py` (Depends on T017, T025) (FR-006)
- [ ] T034 [P] [US3] Implement 3D descriptor calculation (moment of inertia, radius of gyration) for the *molecule* in `code/data/preprocess.py` (molecular-level features)
- [ ] T034b [P] [US3] Implement per-conformer 3D descriptor extraction in `code/data/preprocess.py` (calculate descriptors for each conformer geometry, save to `data/conformer_descriptors.json`) to support FR-007 ablation.
- [ ] T035 [US3] Implement VAE+3D ablation study in `code/evaluate.py` (concatenate *per-conformer* descriptors from T034b to latent vector) (Depends on T017, T025, T034b) (FR-007)
- [ ] T036 [US3] Implement statistical significance test for Δρ (VAE vs VAE+3D) in `code/evaluate.py`
- [ ] T037 [US3] Generate final comparison table and report in `code/evaluate.py`

**Checkpoint**: At this point, User Stories 1, 2, and 3 should all work independently

---

## Phase 6: Reviewer Revision - Experimental Validation Context (Priority: P2)

**Goal**: Address the reviewer's concern regarding experimental validation (X-ray diffraction) by clarifying the scope, validating against the physics-based baseline, and documenting the limitation in `research.md`.

### Implementation for Revision

- [ ] T038 [US2] Update `code/evaluate.py` to explicitly log and report that results are associative (correlation) and not causal (FR-009)
- [ ] T039 [P] Update `research.md` to add a "Validation Strategy" section explicitly stating:
 - The reference standard is GFN2-xTB (physics-based), not experimental X-ray diffraction.
 - X-ray diffraction validation is out of scope for this dataset (ZINC15) and hardware constraints.
 - The "validation" consists of internal consistency checks (convergence rates) and statistical significance of correlations.
- [ ] T040 [P] Update `research.md` to add a "Limitations" section acknowledging the lack of experimental diffraction data and the reliance on semi-empirical methods, as required by FR-009
- [ ] T041 [US2] Implement a specific check in `code/evaluate.py` that logs the GFN2-xTB convergence rate and compares model performance (ρ) against the statistical significance threshold (Depends on T026)

**Checkpoint**: Reviewer concerns addressed; scope boundaries clearly defined in documentation.

---

## Phase 7: Pilot & Edge Case Handling (Priority: P2)

**Goal**: Generate concrete runtime data for the plan and handle edge cases.

### Implementation for Pilot & Edge Cases

- [ ] T047a [P] Select a specific subset of molecules from the ZINC15 dataset for the pilot benchmark.
- [ ] T047b [P] Run the conformer generation and GFN-xTB optimization pipeline on the 50-molecule subset defined in T047a.
- [ ] T047c [P] Generate a runtime report in `data/pilot_runtime.json` containing average time per molecule, total time, and success rate, to update `plan.md` Compute Feasibility section.
- [ ] T048 [P] Implement dataset size check in `code/data/preprocess.py` to raise a clear error and print the minimum sample size (from T028) if the input dataset has < 1,000 molecules

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `docs/quickstart.md` and `docs/README.md`
- [ ] T043a [P] Code cleanup: Remove unused imports from all files in `code/`.
- [ ] T043b [P] Code cleanup: Refactor loops in `code/data/energy_calc.py` (lines 45-60) to use list comprehensions.
- [ ] T044 Performance optimization: Tune `joblib` parallelism (n_jobs=2) and `torch` thread counts (threads=2) to meet the runtime constraint (SC-005) with a target of < 2 hours for `energy_calc.py`
- [ ] T045 [P] Run full integration test suite on GitHub Actions runner
- [ ] T046 Security hardening: Ensure no sensitive keys or paths are hardcoded

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Revision (Phase 6)**: Can be done in parallel with US3, but documentation updates (T039, T040) should be final before release.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires VAE weights from US1 for full evaluation, but the *infrastructure* (conformer gen, xtb wrapper) can be built independently.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires US1 and US2 implementations for full comparison.

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
Task: "Unit test for SMILES-to-graph conversion in code/tests/unit/test_data_loader.py"
Task: "Unit test for VAE architecture in code/tests/unit/test_vae.py"

# Launch all models for User Story 1 together:
Task: "Implement MPNN Encoder and Decoder in code/models/vae.py"
Task: "Implement training loop in code/train.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Training)
4. Complete Phase 4: User Story 2 (Ranking)
5. **STOP and VALIDATE**: Test US1 and US2 independently.
6. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Revision tasks (Phase 6) → Finalize documentation
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (VAE Training)
 - Developer B: User Story 2 (Conformer Gen + Ranking)
 - Developer C: User Story 3 (Baselines + Ablation)
3. Stories complete and integrate independently.
4. Developer D (or rotate): Implement Revision tasks (Phase 6) to address reviewer feedback.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must be executable on CPU-only (2 cores, 7GB RAM) within 6 hours. No GPU/CUDA, no 8-bit quantization, no large model loading.