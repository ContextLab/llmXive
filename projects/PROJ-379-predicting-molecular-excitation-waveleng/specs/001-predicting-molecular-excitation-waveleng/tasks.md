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

- [X] T001 [P] Initialize Project Structure and Verification Log: Create directories `projects/PROJ-379-predicting-molecular-excitation-waveleng/data/raw`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/data/processed`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/code`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/tests`, `projects/PROJ-379-predicting-molecular-excitation-waveleng/docs`. Write a `marker.txt` file to each created directory containing the string "verified". **Versioning**: Generate a SHA256 hash of the `marker.txt` content AND the directory path string. Update `state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml` with keys `{"artifact_hashes": {"<path>": "<hash>"}, "updated_at": "<ISO8601>"}`. Generate `data/processed/dir_verification.json` with keys `{"paths": [str], "status": "verified", "hashes": {str: str}}`. (Constitution V)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create `.flake8` and `pyproject.toml` with black configuration: `.flake8` must set `max-line-length = 88`, `max-complexity = 10`. `pyproject.toml` must configure black with `line-length = 88`.
- [X] T003 Implement `code/utils.py` with RDKit parsing helpers, logging setup, and CPU-only device configuration: Logging format must be `%(asctime)s - %(levelname)s - %(message)s`. Device string must be hardcoded as `device='cpu'`.
- [X] T004 [P] Create data directory structure (`data/raw/`, `data/processed/`) and create empty `data/checksums.txt`
- [X] T005 Implement `code/hash_artifacts.py` to compute content hashes for artifacts and update `state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml` (keys: `artifact_hashes` (dict), `updated_at` (ISO 8601 string)) (Constitution V)
- [X] T006 Define Pydantic models `Molecule` (fields: `smi: str`, `lambda_max: float`, `scaffold_id: str`) and `Scaffold` in `code/models.py`
- [X] T007a [Foundational] Implement `code/verify_accuracy_gate.py`: Execute Reference-Validator logic on dataset URLs (PubChem/SDBS/HF) BEFORE ingestion. **Scope**: Validate URL reachability (HTTP 200), AND title-token-overlap >= 0.7 against the cited source. **Title Extraction**: For HTML URLs, extract `<title>` tag; for API endpoints, extract `API Name` from response headers. **Output**: Write verification status to `data/processed/verification_gate.log` (JSON format). **Error**: Raise `FileNotFoundError` with message "Primary sources (PubChem/SDBS/HF) unreachable or title mismatch. Pipeline halted per FR-001." if validation fails. (Constitution II, FR-001). **This task blocks Phase 3.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw UV-Vis spectral data, parse SMILES to graphs, and produce a clean, scaffold-split dataset.

**Independent Test**: The pipeline can be fully tested by running the ingestion script on a sample subset and verifying that the output CSV contains valid SMILES, corresponding λmax values, and scaffold IDs, with no duplicate structures or missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Contract test for data ingestion output schema in `tests/test_ingest.py`: Assert output columns are exactly `["smi", "lambda_max", "scaffold_id"]` with types `str`, `float`, `str`

### Implementation for User Story 1

- [X] T008 [US1] Implement `code/ingest.py` (Fetch/Parse/Save/Sample):
 1. **Fetch Strategy**: Implement a three-tier fallback flow:
    - **Tier 1**: Attempt to fetch from Primary URL `https://pubchem.ncbi.nlm.nih.gov/rest/pug/...` (or specific SDF endpoint).
    - **Tier 2**: If Tier 1 fails (timeout, 404, etc.), attempt to fetch from Secondary URL `https://www.sdb.org/...` (or specific CSV endpoint).
    - **Tier 3**: If Tier 2 fails, attempt to fetch from HuggingFace dataset ID `zjunlp/mol-excitation-wavelengths` (or equivalent verified HF dataset).
    - **Constraint**: If ALL three tiers fail, raise `FileNotFoundError` with message "All data sources unreachable. Pipeline halted per FR-001."
 2. **Size Check**: Stream the header to count rows. If total rows > 6,979,172,352 bytes (6.5GB equivalent memory), enforce deterministic sampling using `itertools.islice` (fixed seed 42) to fit in RAM.
 3. **Parse/Validate**: Parse SMILES with RDKit. Validate `lambda_max_exp` column exists. If missing, raise error. Handle duplicates by retaining median λmax.
 4. **Edge Cases**:
 - If RDKit cannot parse SMILES: Log error, exclude row, continue.
 - If `lambda_max` is missing: Log error, exclude row, continue.
 5. **Save**: Write cleaned output to `data/processed/cleaned.csv`.
 6. **Logging**: Write `data/processed/sampling_log.json` with EXACT keys: `{"sample_size": int, "seed": 42, "method": "streaming_islice", "total_rows_scanned": int, "source_url": str, "source_tier": int}`.
 7. **Constraint**: Enforce streaming/sampling by default for large datasets to guarantee 7GB limit is never breached. (FR-001, Constitution II). **This task blocks T008.1, T010, T018.**

- [X] T008.1 [US1] Validate Final Dataset for SC-003: Read `data/processed/cleaned.csv`. Iterate through rows. **Logic**: If a row has invalid SMILES or missing `lambda_max`, **log error and exclude row from the final set**. **Constraint**: Only raise `ValueError` if the resulting dataset is empty OR if the test set size (after split) would be < 50 samples. (SC-003). **Dependency**: T008. **This task blocks T010, T014c, T015a.**

- [X] T009 [US1] Implement `code/validate_data.py`: Data Validity Gate. **Logic**: If only computed `lambda_max` values exist (no experimental), **Reframe SC-001**: Update `state/projects/...yaml` to set `sc001_status` to "computed_ground_truth" and log "SC-001 reframed: Experimental noise floor assumption invalid. Success criteria now based on computed ground truth." Exit with code 0. Do NOT silently proceed without updating state. (Constitution VI)

- [X] T009.1 [US1] Implement `code/bypass_gate.py`: Logic to allow `Final Verified Accuracy Gate` to bypass citation checks if `sc001_status` is "computed_ground_truth". **Output**: Write `data/processed/gate_bypass_flag.json`. **Dependency**: T009.

- [X] T010 [US1] Implement `code/split.py`: Generate Bemis-Murcko scaffolds. Split data into training, validation, and test sets. **Ratio Enforcement**: `test_size = floor(0.1 * N)`, `val_size = floor(0.1 * N)`, `train_size = N - test_size - val_size` (explicitly 80/10/10). **Verify**: No scaffold appears in >1 split. **Output**: Write split indices to `data/processed/split_indices.json` (FR-002, Constitution VII). **Dependency**: T008.1.

- [X] T010.5 [US1] Implement `code/merge_split.py`: Combine `cleaned.csv` and `split_indices.json`. **Output**: `data/processed/train_val_test.csv` with columns `[smi, lambda_max, scaffold_id, split]`, sorted by `smi`. **Dependency**: T010.

- [X] T011 [US1] Add logging for data ingestion, conflict resolution, and split statistics: Log levels `INFO`/`WARNING`/`ERROR`. Events: "duplicate_resolved", "split_complete", "scaffold_leakage_detected".

- [X] T018 [US1] Implement `code/power_analysis.py`: Calculate required sample size (`alpha=0.05`, `power=0.8`, `effect_size=0.5`). **Input**: Read `data/processed/split_indices.json` to determine N (test set size). **Output**: Write `data/processed/power_analysis.json` with `n`, `power_status` ("high_power" if n≥50, "low_power" otherwise). **Dependency**: T010.

- [X] T023a [US1] Implement `code/collinearity_check.py` (ECFP): Calculate Pearson r for ECFP bits. Flag if `r >= 0.9`. **Output**: `data/processed/collinearity_flags.json`. (FR-007) **Dependency**: T010. **This task blocks T014c.**

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
- [X] T014c [US2] Train Baseline Model: Execute training of the ECFP+Ridge baseline on the training set. **Dependency**: T023a (Collinearity Check). **Constraint**: If collinearity flags indicate unregularized features (r>=0.9), raise error or apply stronger regularization. **Output**: `data/processed/baseline_model.pkl`. **Dependency**: T008.1, T010.5, T014b, T023a. (FR-004)
- [X] T015a [US2] Implement `code/train.py` (Loop): Training loop with CPU-only execution, fixed seed `42`, and output `model.pt`. **Constraint**: Enforce 4-hour limit internally. If training time > 4 hours, stop training and raise `RuntimeError` with message "Training exceeded 4-hour limit per FR-003." (FR-003). **Dependency**: T008.1, T010.5, T014a.
- [X] T015b [US2] Implement `code/pipeline_wrapper.py`: A wrapper script that orchestrates `ingest.py`, `train.py`, and `evaluate.py`. **Logic**: Measure total wall-clock time from start of `ingest.py` to end of `evaluate.py`. **Budget Allocation**: Enforce total ≤ 6 hours. Allocate 1.5h for Ingest, 4.0h for Training (hard cap), 0.5h for Eval/Attribution. If Training hits 4h, abort immediately to save time for final steps. **Output**: `data/processed/timing.json`. **Constraint**: If total time > 6 hours, **raise `RuntimeError`** (do not just warn). (SC-002). **Dependency**: T008, T015a, T016.
- [X] T016 [US2] Implement `code/evaluate.py`:
 1. **Dependency**: Read `power_analysis.json`.
 2. **Logic**: If `n >= 50`, perform Wilcoxon signed-rank test. If `n < 50`, calculate effect size (**Cohen's d**) as descriptive data only.
 3. **SC-001**: Set `sc001_status = "PASS"` if `MAE < 30` (regardless of power, but note power status). If `MAE > 50`, set `sc001_status = "FAIL"`. Report `power_status` separately.
 4. **SC-005**: If Wilcoxon test fails to show significance (p > 0.05), flag for narrative explanation.
 5. **Output**: `data/processed/metrics_partial.json` with `mae`, `r2`, `wilcoxon_p_value` (if applicable), `effect_size` (Cohen's d), `power_status`, `sc001_status`. **Dependency**: T014c, T015a.
- [X] T016.1 [US2] Implement `code/evaluate.py` (Narrative): Generate a narrative explanation in `data/processed/evaluation_narrative.md` stating whether the GNN shows statistically significant improvement over the baseline or providing a clear explanation of parity if the test fails to show significance. (SC-005) **Dependency**: T016.
- [X] T017 [P] [US2] Test task for SC-001 logic: Write `tests/test_evaluate.py` to verify `sc001_status` logic.
- [X] T019 [US2] Enforce n≥50 constraint: Check `power_analysis.json`. If `n < 50`, set `low_power_flag=True` (log warning). Do NOT halt.
- [X] T020 [US2] Add versioning step in `code/train.py` to generate hashes for `model.pt` and update `state/` YAML.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Sensitivity Analysis (Priority: P3)

**Goal**: Analyze feature importance, perform sensitivity analysis on thresholds, and detect collinearity/redundancy.

**Independent Test**: The attribution script can be tested by running it on a representative subset of test molecules and verifying that it outputs a ranked list of contributing atoms/bonds for each molecule.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T007.1 [P] [US3] Contract test for redundancy masks output in `tests/test_collinearity.py`: Assert `redundancy_masks.json` structure. **Dependency**: T023b.
- [X] T021 [P] [US3] Contract test for attribution output format in `tests/test_explain.py`
- [X] T022 [P] [US3] Integration test for sensitivity sweep and collinearity flags in `tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T023b [US3] Implement `code/collinearity_check.py` (GNN Redundancy): **Dependency**: Trained GNN model (`model.pt` from T015a). Calculate latent cosine similarity for GNN subgraphs. Flag if `> 0.9`. Generate `redundancy_masks.json` (structure: `{ "subgraph_id": boolean }` where boolean indicates if the subgraph is redundant and should be masked). Aggregate subgraphs with similarity > 0.9. Set attribution weights to `0.0` for redundant subgraphs. (FR-007) **Dependency**: T015a.
- [X] T024 [US3] Implement `code/explain.py`: Perform GNNExplainer (steps=50, subset_size=10) on test set. **Output**: `data/processed/raw_attribution.json`. (FR-005)
- [X] T025 [US3] Apply and verify masking: Read `raw_attribution.json` and `redundancy_masks.json` (from T023b). Apply masks. **Output**: `data/processed/masked_attribution.json`. (FR-007) **Dependency**: T023b, T024.
- [X] T026a [US3] Implement `code/sensitivity.py` (Sweep): Sweep MAE thresholds from 15 nm to 55 nm in steps of 5 nm (`range(15, 56, 5)`). Calculate error rates for each. **Justification**: Document that range 15-55 nm is derived from SC-001 target (15-30nm), failure threshold (>50nm), and experimental noise floor (±15 nm). (FR-006)
- [X] T026b [US3] Generate Sensitivity Report: Write `data/processed/sensitivity_report.md` (mandatory narrative report) AND `data/processed/sensitivity_report.csv` (tabular data). Generate `sensitivity_plot.png` (optional, best-effort, skip if display unavailable but log warning). (SC-004)
- [X] T039 [US3] Implement explicit threshold justification in `code/sensitivity.py`: Update docstring of `sweep_thresholds` to include: "Sweep range (15-55 nm) derived from SC-001 target (nanoscale), failure threshold (nanoscale), and experimental noise floor (±15 nm)."
- [X] T027 [US3] Implement `code/analyze_results.py`: Aggregate `metrics_partial.json`, `power_analysis.json`, `redundancy_masks.json`, `masked_attribution.json`, `sensitivity_report.csv`, `evaluation_narrative.md` into `data/processed/metrics.json`. **Schema**: `{"mae": float|null, "r2": float|null, `wilcoxon_p_value`: float|null, `sc001_status`: str, `collinearity_flags`: dict|null, `redundancy_masks`: dict|null, `power_status`: str|null, `attribution_results`: dict|null, `narrative_summary`: str|null}`. **Constraint**: Use `null` for missing keys.
- [X] T029 [P] [US3] Update Documentation: Update `README.md` with "Quickstart" section (full pipeline instructions) AND "Interpretation Guide" (for `masked_attribution.json` and `metrics.json`). **Constraint**: Single task to avoid race conditions. (SC-004, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030a [P] Refactor: Extract `validate_molecule(smiles: str) -> bool` in `code/ingest.py`.
- [X] T030b [P] Refactor: Reduce cyclomatic complexity of `code/split.py` to < 10.
- [X] T031a [P] Performance: Optimize data loading in `code/ingest.py` with `workers=2` to target <30s.
- [X] T031b [P] Performance: Measure baseline graph construction overhead in `code/utils.py` and implement caching of RDKit objects to target a deferred reduction in overhead relative to the measured baseline.
- [X] T032 [P] Code cleanup: Remove unused imports using `autoflake` and `flake8`.

---

## Phase 7: Execution & Verification (Post-Implementation)

**Purpose**: Final validation steps before merging and closing the feature branch.

- [X] T040 [P] [US1] Execute `code/ingest.py` on a sample subset (first several rows) to verify pipeline flow and output schema.
- [X] T041 [P] [US2] Execute `code/train.py` with `--epochs=5` to verify model convergence and artifact generation.
- [X] T042 [P] [US3] Execute `code/explain.py` and `code/sensitivity.py` to verify attribution and sensitivity outputs.
- [X] T043 [P] [US1-US3] Run `pytest tests/` to ensure all unit and integration tests pass. **Artifact**: Generate `tests/pytest_report.json` containing summary of passed/failed tests. Run with isolation flags (`--isolation`) to prevent shared state issues. **Constraint**: Commit `pytest_report.json` as evidence of completion.
- [X] T044 [P] [All] Verify `data/processed/metrics.json` contains all required keys and valid data types.
- [X] T045 [P] [All] Generate final `state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml` with updated artifact hashes.
- [X] T046 [P] [All] Verify `data/processed/sampling_log.json` schema and write a validation report to `data/processed/sampling_review.txt`. **Schema**: Markdown with sections: Sample Size, Method, Power Status, Limitations. **Dependency**: T008, T018.
- [X] T047 [P] [US1-US3] **Final Data Integrity Gate**: Execute `code/verify_no_synthetic_fallback.py` to scan `data/processed/` artifacts and logs. **Logic**: Assert that the `source_url` field in `sampling_log.json` matches the primary PubChem/SDBS URLs. **AND** Verify the content hash of `data/processed/cleaned.csv` matches the hash recorded in `sampling_log.json` (if present) or re-compute and log it. If source mismatch or hash mismatch, raise `RuntimeError` with message "Data source mismatch or integrity failure. Pipeline halted per Constitution II." **Dependency**: T008, T044.
- [X] T047.1 [P] [All] **Final Verified Accuracy Gate (Citations)**: Re-run `code/validators/reference_validator.py` (CLI) on final artifacts and citations in `metrics.json` and `evaluation_narrative.md` against primary sources. **Invocation**: `python code/validators/reference_validator.py --input <file> --output <log> --regex "[Citation].*?https?://.*?"`. **Constraint**: If `sc001_status` is "computed_ground_truth" (from T009), bypass citation check. Else, if any citation fails title-token-overlap or reachability, raise `RuntimeError` with message "Final Verified Accuracy Gate failed. Pipeline halted per Constitution II." (Constitution II). **Dependency**: T047, T009.1.
- [X] T047.2 [P] [All] **Final Verified Accuracy Gate (Full)**: Re-run `code/validators/reference_validator.py` (CLI) on ALL final artifacts and citations in `metrics.json`, `evaluation_narrative.md`, and `sensitivity_report.md` against primary sources. **Invocation**: `python code/validators/reference_validator.py --input <file> --output <log> --regex "[Citation].*?https?://.*?"`. **Constraint**: If `sc001_status` is "computed_ground_truth" (from T009), bypass citation check. Else, if any citation fails title-token-overlap or reachability, raise `RuntimeError` with message "Final Verified Accuracy Gate failed. Pipeline halted per Constitution II." (Constitution II). **Dependency**: T047.1, T009.1.
- [X] T048 [P] [US2] **Compute Budget Re-Verification**: Re-run `code/pipeline_wrapper.py` (T015b) on the final full pipeline execution. **Logic**: Assert total wall-clock time is strictly ≤ 6 hours. If > 6 hours, generate `data/processed/timeoverage_report.md` detailing which phase exceeded limits and propose specific optimization (e.g., reduce epochs, batch size) for the next run. **Dependency**: T015b, T041, T047.2.
- [X] T049 [P] [US3] **Attribution Consistency Check**: Run `code/verify_attribution_masks.py` to ensure that `masked_attribution.json` values for flagged redundant subgraphs are exactly `0.0`. **Logic**: Load `redundancy_masks.json` and `masked_attribution.json`; assert intersection. **Dependency**: T023b, T025.

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

- **T007a** (Verify Accuracy Gate) blocks **T008** (Ingest).
- **T008.1** (SC-003 Validation) depends on **T008** (Ingest).
- **T010.5** depends on **T008.1** (validated data) and **T010** (split indices).
- **T018** depends on **T010** (split indices).
- **T023a** (ECFP Collinearity) depends on **T010** and must run before **T014c** (Baseline Training).
- **T023b** (GNN Redundancy) depends on **T015a** (Trained Model) and must run before **T025**.
- **T025** depends on **T024** (raw attribution) and **T023b** (masks).
- **T027** depends on **T016**, **T016.1**, **T018**, **T023a**, **T023b**, **T024**, **T025**, and **T026a**.
- **T029** is parallel-safe as it targets a single file with distinct sections.
- **T016** depends on **T018** (power analysis) to determine execution path (Wilcoxon vs Effect Size).
- **T016.1** depends on **T016** (metrics).
- **T008** (Ingest/Sample) is integrated into T008; no separate dependency.
- **T039** depends on **T026a** (sensitivity logic) to document threshold choices.
- **T040-T049** depend on all Phase 3-5 implementation tasks being complete.
- **T046** depends on **T008** (sampling log generation) and **T018** (power analysis).
- **T047** depends on **T008** and **T044** (final data artifacts).
- **T047.1** depends on **T047** and **T009.1** (bypass flag).
- **T047.2** depends on **T047.1** and **T009.1**.
- **T048** depends on **T015b**, **T041**, and **T047.2**.
- **T049** depends on **T023b** and **T025**.
- **T014c** depends on **T023a** (Collinearity Check).
- **T007.1** depends on **T023b** (moved to Phase 5).

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
- **Final Verification**: T047, T047.1, T047.2, T048, T049 are mandatory pre-merge checks to ensure no fabrication, compute budget compliance, and attribution integrity.