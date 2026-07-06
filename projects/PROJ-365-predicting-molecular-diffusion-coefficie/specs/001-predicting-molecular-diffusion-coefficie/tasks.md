# Tasks: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Input**: Design documents from `/specs/001-predict-molecular-diffusion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw`, `data/processed`, `data/checksums.json`)
- [ ] T001b [P] Create `data/logs` directory for ingestion logs (Required by T005)
- [ ] T001c [P] Create `data/artifacts` directory for model checkpoints and reports (Required by T027, T025b)
- [ ] T002 Initialize Python 3.11 project and generate `code/requirements.txt` with pinned versions (`rdkit`, `torch` (CPU), `torch-geometric` (CPU), `scikit-learn`, `pandas`, `pyyaml`, `psutil`, `pytest`, `thermo`)
- [ ] T003 [P] Configure `pyproject.toml` for linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/config.py` to manage paths, random seed (fixed), and environment variables
- [ ] T005 [P] Implement `code/utils/logging.py` with specific log tags: `[MISSING_DATA_EXCLUDED]`, `[ERROR_SMILES]`; write to `data/logs/ingestion.log` in plain text with timestamp (FR-007)
- [ ] T006 [P] Implement `code/utils/monitor.py` to enforce a fixed runtime limit of **6 hours (21600 seconds)** and GB RAM limit (SC-005); raise `ResourceLimitExceeded` if exceeded (FR-003, SC-003, SC-005)
- [ ] T006b [P] Implement `code/utils/graph_safety.py` to detect high molecular weight molecules and implement **sampling or truncation logic during featurization** (before memory allocation) to prevent memory crashes (Spec Edge Case, SC-005)
- [ ] T007 [P] [US1] Implement `code/ingestion/fetch_nist.py` to programmatically retrieve experimental diffusion data from NIST TRC **primarily via `thermo` library**; **IF fetch fails (no verified dataset), invoke T007b (Synthetic Generator) to create a synthetic dataset for pipeline validation and proceed**; this task MUST NOT fail the pipeline if real data is missing (US1, FR-001, Constitution Principle II, Plan Phase 0)
- [ ] T007b [P] [US1] Implement `code/ingestion/generate_synthetic.py`: Generate a synthetic dataset of molecule-solvent pairs using Stokes-Einstein physics or random structure **strictly for structural integrity and code execution**; this task MUST be invoked by T007 if real data fetch fails (Plan Phase 0, CRITICAL DATA NOTE)
- [ ] T008 [P] [US1] Implement `code/ingestion/validate.py` to define SMILES validation logic and exclusion logic for missing solvent variables (FR-001, FR-007)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Featurization Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest experimental diffusion data, validate SMILES, and convert to graph representations + solvent descriptors.

**Independent Test**: Run on a sample of molecules (real or synthetic) and verify output JSONL contains valid PyTorch Geometric Data objects and solvent descriptors, with no missing critical fields.

### Implementation for User Story 1

- [ ] T008b [US1] Implement `code/ingestion/run_validation.py` to execute the validation logic from T008 on fetched/generated data (Depends on T007 OR T007b, T008)
- [ ] T010 [P] [US1] Implement `code/ingestion/featurize.py`: Convert SMILES to `MoleculeGraph` (RDKit) with atom nodes and bond edges **AND** compute `SolventDescriptor` (viscosity, dielectric constant) from CSV input (US1, FR-002)
- [ ] T012 [US1] Implement `code/ingestion/ingest.py`: Main pipeline to read CSV, validate (T008b), featurize, and write `data/processed/featurized.jsonl` (Depends on T008b, T010)
- [ ] T013 [US1] Implement error handling in `ingest.py` to exclude records with missing data and log with `[MISSING_DATA_EXCLUDED]`
- [ ] T014 [US1] Implement error handling in `ingest.py` to skip invalid SMILES and log with `[ERROR_SMILES]` without crashing
- [ ] T015 [US1] Add contract test in `tests/contract/test_featurization.py` to validate JSONL schema against `specs/001-predicting-molecular-diffusion-coefficie/contracts/dataset.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Optimized GNN Training and Baseline Comparison (Priority: P2)

**Goal**: Train a lightweight MPNN on CPU, compare against a Linear Regression baseline (with descriptors), and perform statistical significance testing.

**Independent Test**: Execute training on ≤ 5,000 molecules; verify completion in ≤ 30 mins on CPU; verify model artifacts saved; verify report contains RMSE and Pearson r for GNN and Linear Regression baseline.

### Implementation for User Story 2

- [ ] T016 [P] [US2] Implement `code/models/mpnn.py`: Define a single-layer Message Passing Neural Network (CPU-only, no CUDA)
- [ ] T017 [P] [US2] Implement `code/models/baseline.py`: Define **Linear Regression** baseline using fingerprints + solvent descriptors (Mandatory for FR-005 t-test)
- [ ] T019a [P] [US2] Implement `code/training/cv_strategy.py` (Part 1): **Detect dataset size and strata sparsity**; **IF dataset < 50 molecules or solvent types are sparse, switch to Leave-One-Out (LOO) validation**; **ELSE use k-fold stratified by solvent type** (FR-004, Spec Edge Cases, SC-003)
- [ ] T019 [US2] Implement `code/training/train.py` (Part 1): Implement **5-fold/LOO** stratified data splitter with **fixed random seed** and **stratification by solvent type** (or LOO if T019a dictates) (FR-004, Depends on T019a)
- [ ] T041 [US2] Implement `code/training/train.py` (Part 2): Implement **5-fold/LOO** cross-validation training loop using the splitter from T019, **training MPNN (T016) and Linear Regression Baseline (T017)**, saving `ModelCheckpoint` artifacts to `data/artifacts/`. **This task MUST explicitly invoke the device check (log "Device: CPU", verify `torch.cuda.is_available() is False`) at the startup of the training pipeline** (Depends on T019, T016, T017, T019a)
- [ ] T020 [US2] Implement `code/training/evaluate.py`: Calculate Pearson r and RMSE for GNN and Linear Regression Baseline on held-out test set (Depends on T041)
- [ ] T021 [US2] Implement `code/training/evaluate.py`: Perform paired t-test on per-sample absolute errors comparing GNN vs Linear Regression to determine statistical significance (FR-005); **IF p >= 0.05 or r < 0.3, generate a 'defined negative finding' report explicitly stating the null result as per SC-001** (Depends on T020)
- [ ] T023 [US2] Add integration test in `tests/integration/test_training_pipeline.py` to verify end-to-end training and evaluation flow

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Methodological Robustness Check (Priority: P3)

**Goal**: Perform sensitivity analysis on hyperparameters and verify model robustness via ablation studies.

**Independent Test**: Run sensitivity script; verify output report shows metric fluctuations across hyperparameter ranges and confirms stability (or lack thereof).

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `code/training/sensitivity.py` (Part 1): Define hyperparameter grid (Message Passing Steps {discrete range}, Learning Rates {1e-3, 1e-4})
- [ ] T042 [P] [US3] Implement `code/training/sensitivity.py` (Part 2): Implement sweep loop to re-train/evaluate models across the grid defined in T024
- [ ] T043 [US3] Implement `code/training/sensitivity.py` (Part 3): Generate sweep report with table of metrics (Depends on T042)
- [ ] T025a [P] [US3] Implement `code/training/ablation_pipeline.py`: **Modify the model input pipeline (from T041) to accept a `remove_solvent` flag** for both GNN and Linear Regression Baseline (FR-006, SC-004)
- [ ] T025b [US3] Implement `code/training/ablation_study.py`: **Orchestrate re-training** using the pipeline from T025a with `remove_solvent=True` for **BOTH GNN and Baseline**; **generate `data/artifacts/ablation_report.json` containing the variation in correlation coefficients (r) between the full model and the ablated model for BOTH architectures** to isolate the 'graph contribution' (Depends on T041, T019a, T025a)
- [ ] T026 [US3] Implement `code/training/robustness.py`: **Detect dataset size (using T019a logic) and switch CV strategy if < 50 molecules**; **calculate Pearson r on the full dataset and on the dataset excluding a small, high-residual subset of samples**, writing results to `data/artifacts/outlier_analysis.json` (Depends on T019a, T041)
- [ ] T027 [US3] Generate final report in `data/artifacts/sensitivity_report.md` summarizing stability of Pearson r > 0.7 across variations; **must include a table of Pearson r values for message passing steps 1, 2, 3 and ablation results**
- [ ] T028 [US3] Add unit test in `tests/unit/test_sensitivity_logic.py` to verify hyperparameter sweep logic

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates: Write `code/README.md` with execution instructions and data source requirements
- [ ] T030 Code cleanup and refactoring of `code/` imports and dependencies
- [ ] T031 [P] Add `pytest` unit tests for `utils/monitor.py` to verify memory/time gating logic
- [ ] T032 Run `quickstart.md` validation (if created) or manual end-to-end verification on synthetic data
- [ ] T033 Update `plan.md` with actual dataset source found (NIST/Zenodo) or confirm "Simulation Study" status

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US1 (P1)**: Must complete first to generate data for US2/US3
  - **US2 (P2)**: Depends on US1 data output
  - **US3 (P3)**: Depends on US2 trained models
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (Data Ingestion) to produce `featurized.jsonl`
- **User Story 3 (P3)**: Depends on US2 (Training) to produce trained models and results

### Within Each User Story

- Models/Featurization before Training
- Training before Evaluation
- Evaluation before Sensitivity/Ablation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **US1 Implementation (T010)** can run in parallel with T008
- **US2 Implementation (T016, T017)** can run in parallel
- **US3 Implementation (T024, T025a)** can run in parallel (after US2 completion)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch model implementations for User Story 2 together:
Task: "Implement code/models/mpnn.py: Define a single-layer Message Passing Neural Network"
Task: "Implement code/models/baseline.py: Define Linear Regression baseline (T017)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion & Featurization)
4. **STOP and VALIDATE**: Test ingestion on sample data, verify JSONL schema
5. Proceed to US2 only if data pipeline is stable

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo data pipeline (MVP!)
3. Add User Story 2 → Train model, verify CPU constraints, compare baselines
4. Add User Story 3 → Run sensitivity analysis, verify robustness
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Pipeline)
   - Developer B: User Story 2 (Model & Training)
   - Developer C: User Story 3 (Analysis & Robustness)
   *Note: Developer B and C must wait for Developer A's data output.*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **CRITICAL**: Do not use `load_in_8bit`, `bitsandbytes`, or `device_map="cuda"`. The runner is CPU-only.
- **CRITICAL**: All data must be real (NIST/Zenodo) or explicitly synthetic for "Simulation Study" reframing. No fake numbers.
- **CRITICAL**: If no real data exists, T007 must trigger T007b to generate synthetic data for validation; do not fail the pipeline.
- **CRITICAL**: Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence