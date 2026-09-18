# Tasks: Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-excitation-waveleng/`
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

- [X] T001a [P] Create project directory structure: Create directories `projects/PROJ-379-predicting-molecular-excitation-waveleng/data/raw`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/data/processed`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/code`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/tests`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/docs`. **Verification**: Write a `marker.txt` file to each directory containing the string "verified". Output a JSON log `data/processed/dir_verification.json` listing all created paths and their status.
- [X] T001b [P] Create `requirements.txt` with pinned versions: `rdkit==2023.9.5`, `torch==2.1.0+cpu`, `torch-geometric==2.4.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `numpy==1.24.0`, `pyyaml==6.0.1`, `pytest==7.4.0`
- [X] T001c [P] Create `README.md` with Quickstart section: Include a "Quickstart" header. Content must include: 1) `pip install -r requirements.txt` command, 2) `python code/ingest.py` command, 3) `python code/evaluate.py` command. Verify existence of "Quickstart" string.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create `.flake8` and `pyproject.toml` with black configuration: `.flake8` must set `max-line-length = 88`, `max-complexity = 10`. `pyproject.toml` must configure black with `line-length = 88`.
- [X] T003 Implement `code/utils.py` with RDKit parsing helpers, logging setup, and CPU-only device configuration: Logging format must be `%(asctime)s - %(levelname)s - %(message)s`. Device string must be hardcoded as `device='cpu'`.
- [X] T004 [P] Create data directory structure (`data/raw/`, `data/processed/`) and create empty `data/checksums.txt`
- [X] T005 Implement `code/hash_artifacts.py` to compute content hashes for artifacts and update `state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml` (keys: `artifact_hashes` (dict), `updated_at` (ISO 8601 string)) (Constitution V)
- [X] T006 Define Pydantic models `Molecule` (fields: `smi: str`, `lambda_max: float`, `scaffold_id: str`) and `Scaffold` in `code/models.py`
- [X] T007a [Foundational] Implement `code/verify_accuracy_gate.py`: Execute Reference-Validator logic on dataset URLs (PubChem/SDBS) BEFORE ingestion. **Scope**: Validate URL reachability and HTTP headers only. **Output**: Write verification status to `data/processed/verification_gate.log` (JSON format). **Error**: Raise `FileNotFoundError` with message "Primary sources (PubChem/SDBS) unreachable. Pipeline halted per FR-001." if validation fails. (Constitution II, FR-001). **This task blocks Phase 3.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw UV-Vis spectral data, parse SMILES to graphs, and produce a clean, scaffold-split dataset.

**Independent Test**: The pipeline can be fully tested by running the ingestion script on a sample subset and verifying that the output CSV contains valid SMILES, corresponding λmax values, and scaffold IDs, with no duplicate structures or missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Contract test for data ingestion output schema in `tests/test_ingest.py`: Assert output columns are exactly `["smi", "lambda_max", "scaffold_id"]` with types `str`, `float`, `str`

### Implementation for User Story 1

- [X] T008a [US1] Implement `code/ingest.py` (Fetch): Fetch raw UV-Vis data from **PubChem** (via `pubchempy`) or **SDBS** (via official URL). **Constraint**: No fallback to HuggingFace or other sources. If both fail, raise `FileNotFoundError` with message "Primary sources (PubChem/SDBS) unreachable. Pipeline halted per FR-001." (FR-001).
- [X] T008b [US1] Implement `code/ingest.py` (Parse/Validate): Parse SMILES with RDKit. Validate `lambda_max_exp` column exists. If missing, raise error. Handle duplicates by retaining median λmax. **Logging**: Log count of duplicates resolved.
- [X] T008c [US1] Implement `code/ingest.py` (Save/Sample): Write cleaned output to `data/processed/cleaned.csv`. **Sampling Logic**: If dataset > 7GB RAM, implement deterministic sampling using `itertools.islice` (fixed seed) to fit in RAM. **Output**: Write `data/processed/sampling_log.json` with EXACT keys: `{"sample_size": int, "seed": 42, "method": "itertools.islice", "total_rows_scanned": int}`. **Constraint**: If full dataset fits, do not sample. If sampling required, log warning.
- [X] T009 [US1] Implement `code/validate_data.py`: Data Validity Gate. **Logic**: If only computed `lambda_max` values exist (no experimental), **Reframe SC-001**: Update `state/projects/...yaml` to set `sc001_status` to "computed_ground_truth" and log "SC-001 reframed: Experimental noise floor assumption invalid. Success criteria now based on computed ground truth." Exit with code 0. Do NOT silently proceed without updating state.
- [X] T010 [US1] Implement `code/split.py`: Generate Bemis-Murcko scaffolds. Split data into training, validation, and test sets.. **Rounding**: Use `floor(0.1 * N)` for val/test sizes. **Verify**: No scaffold appears in >1 split. **Output**: Write split indices to `data/processed/split_indices.json` (FR-002, Constitution VII).
- [X] T010.5 [US1] Implement `code/merge_split.py`: Combine `cleaned.csv` and `split_indices.json`. **Output**: `data/processed/train_val_test.csv` with columns `[smi, lambda_max, scaffold_id, split]`, sorted by `smi`.
- [X] T011 [US1] Add logging for data ingestion, conflict resolution, and split statistics: Log levels `INFO`/`WARNING`/`ERROR`. Events: "duplicate_resolved", "split_complete", "scaffold_leakage_detected".
- [X] T034 [US1] Enforce "fail loud" policy in `code/ingest.py`: Ensure no `try/except` blocks catch download errors to substitute synthetic data. Any real fetch failure MUST raise `FileNotFoundError` with message "Primary sources (PubChem/SDBS) unreachable. Pipeline halted per FR-001."

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation (Priority: P2)

**Goal**: Train a lightweight GNN and baseline linear model, evaluate performance, and ensure CPU feasibility.

**Independent Test**: The training job can be tested by executing the training script on a fixed random seed and verifying that the model converges (loss decreases) and produces a test MAE and R² score in the expected range.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US2] Unit test for GNN architecture parameter count (<1M) in `tests/test_model.py`
- [X] T013 [P] [US2] Integration test for training loop convergence and artifact generation in `tests/test_train.py`

### Implementation for User Story 2

- [X] T014a [US2] Implement `code/model.py` (GNN): Define MPNN GNN (2 layers, hidden units, mean aggregation, <1M params). (FR-003)
- [X] T014b [US2] Implement `code/model.py` (Baseline): Define ECFP+Ridge Regression baseline (alpha=1.0). (FR-004)
- [X] T015a [US2] Implement `code/train.py` (Loop): Training loop with CPU-only execution, fixed seed `42`, and output `model.pt`. (FR-003)
- [X] T015b [US2] Implement `code/timing_logger.py`: Measure wall-clock time from `ingest.py` start to `evaluate.py` end. Output `data/processed/timing.json`. Verify ≤6 hours. Raise warning if exceeded.
- [X] T015c [US2] Implement `code/train.py` (Early Stop): Implement early stopping with `patience=5`, monitor `val_loss`. Log trigger event. (FR-003)
- [X] T018 [US2] Implement `code/power_analysis.py`: Calculate required sample size (`alpha=0.05`, `power=0.8`, `effect_size=0.5`). **Output**: Write `data/processed/power_analysis.json` with `n`, `power_status` ("high_power" if n≥50, "low_power" otherwise).
- [X] T016 [US2] Implement `code/evaluate.py`:
 1. **Dependency**: Read `power_analysis.json`.
 2. **Logic**: If `n >= 50`, perform Wilcoxon signed-rank test. If `n < 50`, calculate effect size (descriptive).
 3. **SC-001**: Set `sc001_status = "PASS"` if `MAE < 30` AND `n >= 50` (or `n < 50` with effect size acceptable). **Do NOT set FAIL solely due to n < 50**. Failure is `MAE > 50`.
 4. **Output**: `data/processed/metrics_partial.json` with `mae`, `r2`, `wilcoxon_p_value` (if applicable), `effect_size`, `power_status`, `sc001_status`.
- [X] T017 [P] [US2] Test task for SC-001 logic: Write `tests/test_evaluate.py` to verify `sc001_status` logic.
- [X] T019 [US2] Enforce n≥50 constraint: Check `power_analysis.json`. If `n < 50`, set `low_power_flag=True` (log warning). Do NOT halt.
- [X] T020 [US2] Add versioning step in `code/train.py` to generate hashes for `model.pt` and update `state/` YAML.
- [X] T035 [US2] Add early stopping trigger in `code/train.py`: Ensure `patience=5`, `metric=val_loss` is implemented.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Sensitivity Analysis (Priority: P3)

**Goal**: Analyze feature importance, perform sensitivity analysis on thresholds, and detect collinearity/redundancy.

**Independent Test**: The attribution script can be tested by running it on a representative subset of test molecules and verifying that it outputs a ranked list of contributing atoms/bonds for each molecule.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US3] Contract test for attribution output format in `tests/test_explain.py`
- [X] T022 [P] [US3] Integration test for sensitivity sweep and collinearity flags in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T023a [US3] Implement `code/collinearity_check.py` (ECFP): Calculate Pearson r for ECFP bits. Flag if `r >= 0.9`.
- [X] T023b [US3] Implement `code/collinearity_check.py` (GNN): Calculate latent cosine similarity for GNN subgraphs. Flag if `> 0.9`. Generate `redundancy_masks.json` (structure: `{ "molecule_id": [mask_array] }`). (FR-007)
- [X] T036 [US3] Add subgraph redundancy aggregation in `code/collinearity_check.py`: Aggregate subgraphs with similarity > 0.9. Set attribution weights to `0.0` for redundant subgraphs.
- [X] T024 [US3] Implement `code/explain.py`: Perform GNNExplainer (steps=50, subset_size=10) on test set. **Output**: `data/processed/raw_attribution.json`. (FR-005)
- [X] T025 [US3] Apply and verify masking: Read `raw_attribution.json` and `redundancy_masks.json`. Apply masks. **Output**: `data/processed/masked_attribution.json`. (FR-007)
- [X] T026a [US3] Implement `code/sensitivity.py` (Sweep): Sweep MAE thresholds from 10 to 50 nm in steps of nanoscale intervals (`range(15, 51, 5)`). Calculate error rates for each. (FR-006)
- [X] T026b [US3] Generate Sensitivity Report: Write `data/processed/sensitivity_report.csv` (mandatory). Generate `sensitivity_plot.png` (optional, best-effort, skip if display unavailable but log warning). (SC-004)
- [X] T039 [US3] Implement explicit threshold justification in `code/sensitivity.py`: Update docstring of `sweep_thresholds` to include: "Sweep range (15-50 nm) derived from SC-001 target (30 nm), failure threshold (50 nm), and experimental noise floor (±15 nm)."
- [X] T027 [US3] Implement `code/analyze_results.py`: Aggregate `metrics_partial.json`, `power_analysis.json`, `redundancy_masks.json`, `masked_attribution.json`, `sensitivity_report.csv` into `data/processed/metrics.json`. **Schema**: `{"mae": float|null, "r2": float|null, "wilcoxon_p_value": float|null, "sc001_status": str, "collinearity_flags": dict|null, "redundancy_masks": dict|null, "power_status": str|null, "attribution_results": dict|null}`. **Constraint**: Use `null` for missing keys.
- [X] T028a [P] [US3] Generate `quickstart.md`: Include sections "Install", "Run Pipeline", "Interpret Output".
- [X] T029b [P] Documentation: Update `README.md` with interpretation guide for `masked_attribution.json`.
- [X] T029a [P] Documentation: Update `README.md` "Quickstart" section with full pipeline instructions.
- [X] T030a [P] Refactor: Extract `validate_molecule(smiles: str) -> bool` in `code/ingest.py`.
- [X] T030b [P] Refactor: Reduce cyclomatic complexity of `code/split.py` to < 10.
- [X] T031a [P] Performance: Optimize data loading in `code/ingest.py` with `workers=2` to target <30s.
- [X] T031b [P] Performance: Implement RDKit caching with `cache_key=smiles`, `max_size=1000`.
- [X] T032 [P] Code cleanup: Remove unused imports using `autoflake` and `flake8`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029a [P] Documentation: Update `README.md` "Quickstart" section with instructions for running the full pipeline and interpreting `metrics.json`
- [X] T030a [P] Refactor: Extract validation logic in `code/ingest.py` into a separate function `validate_molecule(smiles)` to improve modularity
- [X] T030b [P] Refactor: Reduce cyclomatic complexity of `code/split.py` to <10 by extracting scaffold generation logic into a helper function
- [X] T031a [P] Performance: Optimize data loading in `code/ingest.py` by using multiprocessing to reduce loading time to <30s for a large set of molecules
- [X] T031b [P] Performance: Measure baseline graph construction overhead in `code/utils.py` and implement caching of RDKit objects to target a [deferred] reduction in overhead relative to the measured baseline.
- [X] T032 [P] Code cleanup: Remove unused imports and fix linting errors across `code/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained model from US2

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

### Explicit Task Dependencies

- **T007a** (Verify Accuracy Gate) blocks **T008a** (Ingest Fetch).
- **T010.5** depends on **T008c** (cleaned data) and **T010** (split indices).
- **T025** depends on **T024** (raw attribution) and **T023b** (masks).
- **T027** depends on **T016**, **T018**, **T023a**, **T023b**, **T024**, **T025**, and **T026a**.
- **T029b** and **T028a** are parallel-safe as they target distinct files (`README.md` vs `quickstart.md`).
- **T016** depends on **T018** (power analysis) to determine execution path (Wilcoxon vs Effect Size).
- **T008c** (Sampling) is integrated into T008; no separate dependency.
- **T039** depends on **T026a** (sensitivity logic) to document threshold choices.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data ingestion output schema in tests/test_ingest.py"

# Launch models for User Story 1 together:
Task: "Implement code/ingest.py: Fetch UV-Vis data..."
Task: "Implement code/validate_data.py: Data Validity Gate..."
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
- Avoid: vague tasks, cross-story dependencies that break independence
- **Critical Constraint**: All model training and data processing MUST run on CPU-only (vCPU, 7GB RAM) within 6 hours. No GPU, no 8-bit/4-bit quantization, no large models.
- **Data Integrity**: Real data must be streamed or sampled explicitly; synthetic fallbacks are strictly prohibited.
- **Fail Loud**: If real data fetch fails, raise an exception. Do NOT fall back to synthetic data.
- **Data Hygiene**: Raw data in `data/raw/`, processed data in `data/processed/`.
- **Reproducibility**: All random seeds must be logged and pinned.
- **Methodological Grounding**: Thresholds and sampling strategies must be explicitly justified.