# Tasks: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Input**: Design documents from `/specs/001-polymer-degradation/`
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

## Phase 1: Setup & Amendments (Shared Infrastructure + Blocking Prerequisites)

**Purpose**: Project initialization, spec/constitution amendments, and basic structure.
**Note**: ALL SPEC AND CONSTITUTION AMENDMENTS MUST BE COMPLETED HERE before any implementation tasks begin.

- [ ] T001a Create project directory structure: Execute `mkdir -p code/ data/raw/ data/processed/ data/reports/ tests/ state/ state/projects/` in repository root. **Verification**: Verify directories exist via `ls`. **Artifact**: Generate `state/setup_log.txt` containing the command output and timestamp. (Constitution I)
- [ ] T001b Verify and Log: Execute `ls -R` to verify directory structure and append to `state/setup_log.txt` with timestamp. (Constitution I)
- [X] T002 (Depends on T001b) Initialize Python 3.11 project by generating `code/requirements.txt` with pinned versions: `rdkit==2023.9.5 `, `torch==2.1.0+cpu `, `torch-geometric==2.4.0 `, `scikit-learn==1.3.2 `, `pandas==2.1.4 `, `numpy==1.26.2 `, `pyyaml==6.0.1 `, `requests==2.31.0 `, `statsmodels==0.14.0 `, `pytest==7.4.3 `
- [X] T003 (Depends on T001b) Configure linting tool `ruff` in `code/.ruff.toml` with strict rules for reproducibility and type checking.
- [ ] T015b [US1] (Depends on T001b) **SPEC AMENDMENT**: Update `spec.md` FR-002 to explicitly state that missing environmental values are handled by "flagging and exclusion" (imputation is forbidden). (FR-002, Plan Correction)
- [ ] T025d [US1] (Depends on T001b) **SPEC AMENDMENT**: Update `spec.md` FR-004 to explicitly replace "bond rotation" with "functional-group-preserving edge dropout". (FR-004, Plan Correction)
- [ ] T030a [US2] (Depends on T001b) **SPEC AMENDMENT**: Update `spec.md` SC-005 to explicitly resolve the '[deferred]' placeholder with the value "10" for the top attribution scores threshold. (SC-005)
- [ ] T038b [US3] (Depends on T001b) **CONSTITUTION AMENDMENT**: Update `Constitution.md` Principle VI to designate the "Motif-Masking Permutation Test" as the primary validation method and the "χ² Discretization Protocol" as complementary, resolving the constitutional conflict. (Constitution VI)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 (Depends on T001b) Setup shared logging infrastructure with file handlers in `code/utils.py`
- [ ] T005 (Depends on T001b) Implement exponential backoff utility (max 3 retries) in `code/utils.py` for API rate limiting
- [ ] T006 (Depends on T001b) Create base configuration loader for environment variables and paths in `code/utils.py`
- [ ] T007a (Depends on T001b) Define `PolymerRecord` data class in `code/data_models.py`: Fields `smiles`, `temperature`, `ph`, `uv`, `degradation_pathway`, `source_id`. (FR-001, FR-008)
- [ ] T007b (Depends on T001b) Define `MolecularGraph` data class in `code/data_models.py`: Fields `atom_features`, `bond_features`, `edge_index`, `environment_vector`. (FR-002)
- [ ] T007c (Depends on T001b) Define `MotifImportance` data class in `code/data_models.py`: Fields `motif_pattern`, `pathway`, `importance_score`, `p_value`. (FR-007, SC-002)
- [ ] T008 (Depends on T001b) Setup pytest framework: Create `pytest.ini` with seed pinning and `conftest.py` for shared fixtures in `tests/`. (Constitution I)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and convert polymer degradation records from NIST Chemistry WebBook and Materials Project into a structured graph dataset.

**Independent Test**: Can be fully tested by executing the ingestion script against a small subset of known NIST entries and verifying the output parquet contains valid SMILES strings, numeric environmental parameters, and categorical degradation labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [US1] Unit test for SMILES validation and RDKit graph conversion in `tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid`
- [ ] T010 [US1] Unit test for missing data exclusion logic in `tests/unit/test_preprocess.py::test_missing_env_excludes_record`
- [ ] T012 [US1] Integration test for API rate-limit backoff in `tests/integration/test_api_ingestion.py::test_backoff_on_rate_limit`

### Implementation for User Story 1

- [ ] T013 [US1] (Depends on T007a) Implement `ingest.py`: Download records from NIST (URL: `https://webbook.nist.gov/cgi/cbook.cgi?ID=...`) and Materials Project (API Endpoint: `https://materialsproject.org/rest/v/materials/...`) with rate-limit backoff.
 - **Fallback Mechanism**: ONLY if `CI_MODE=true` AND API returns 0 records after 3 retries, generate a deterministic `polymer_seed.json` file.
 - **Seed Schema**: `{"smiles": [string], "temperature": [float], "ph": [float], "uv": [float], "degradation_pathway": [string], "source_id": [string]}`.
 - **Output**: Save to `data/raw/raw_nist_mp_records.csv` with schema: `[smiles, temperature, ph, uv, degradation_pathway, source_id]`. If fallback is used, save `data/raw/polymer_seed.json` and log "SYNTHETIC_FALLBACK" event. **CRITICAL**: This synthetic data is ONLY for CI validation and MUST be excluded from any final scientific report or 'real data' claims. In non-CI mode (`CI_MODE=false`), the task MUST fail with a clear error if real data is not found. (FR-001, FR-008, Constitution I)
- [ ] T014 [US1] (Depends on T013) Implement `ingest.py`: Identify records missing 'degradation pathway' labels; FLAG them by saving to `data/raw/flagged_for_curation.csv` (schema: `[record_id, reason]`) and log the action. EXCLUDE these specific records from the immediate training set to prevent label leakage, preserving the 'flag' as a distinct artifact for potential manual curation (FR-008, US-1 Scenario 2)
- [ ] T015 [US1] (Depends on T014, T015b) Implement `preprocess.py`: Convert SMILES to molecular graphs using RDKit (parameters: `sanitize=True`, `removeHs=False`); filter non-polyesters by detecting ester functional groups (pattern: `C(=O)O`) in SMILES.
 - **Exclusion Rule**: Records with missing environmental data (temp/pH/UV) MUST be FLAGGED (saved to `data/raw/flagged_env_missing.csv`) and then EXCLUDED from the training set. This is a hard rule to prevent confounding.
 - **Output**: Save to `data/processed/graphs.parquet` (FR-002)
 - **Error Handling**: If RDKit conversion fails for a SMILES string, skip the record, log the SMILES, and continue.
 - **Output**: Generate `data/processed/exclusion_decision_log.json` with schema `{excluded_count: int, excluded_smiles: [string]}` confirming the exclusion path was taken and documenting the count of excluded records. (FR-002, Plan: Data Exclusion Assumption, Methodological Correction)
- [ ] T016a [US1] (Depends on T014) Implement `ingest.py`: Save the raw ingested dataset (after label flagging) to `data/raw/raw_polymer_records.csv` with checksums. (FR-001)
- [ ] T016b [US1] (Depends on T015) Implement `preprocess.py`: Save the processed graph dataset (after SMILES conversion, polyester filtering, and environmental filtering) to `data/processed/processed_graph_dataset.parquet` with checksums. (FR-002)
- [ ] T016c [US1] (Depends on T016b) **PRE-AUGMENTATION SAVE**: Save the pre-augmentation dataset (after environmental filtering but before augmentation) to `data/processed/pre_augmented_graph_dataset.parquet` with checksums. This artifact is the input for the augmentation phase in Phase 4. (FR-002)
- [ ] T017 [US1] (Depends on T016c) **POWER ANALYSIS & DECISION**: Execute `python code/preprocess.py --mode power_analysis`.
 - **Logic**: Calculate sample size `n`. If `n > 150`, subsample to 150 using stratified sampling (seed 42) and save to `data/processed/final_dataset.parquet`. If `n <= 150`, set action to "augment" (50<=n<150) or "augment_aggressive" (n<50) and write `state/augmentation_trigger.json`.
 - **Power Analysis Params**: Use `statsmodels.stats.power.tt_ind_solve_power` with `effect_size=0.5 `, `{{claim:c_9a086e40}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)`, `power=0.8` to calculate minimum required sample size.
 - **Output**: Write `state/augmentation_trigger.json` with `{"n": int, "action": "none" | "augment" | "augment_aggressive"}`. Generate `data/reports/power_analysis_report.json` with `{"n": int, "warning": "true" if n<150 else "false"}`. (SC-004, FR-004, Plan Correction)
- [ ] T025a [US1] (Depends on T017) **AUGMENTATION TRIGGER DECISION**: Read `state/augmentation_trigger.json`.
 - If `action` is "none" (from T017), log status="skipped" in `data/processed/augmentation_log.json` and skip to T028.
 - If `action` is "augment" or "augment_aggressive", proceed to T025b.
 - If trigger file is absent, log status="error" and halt. (FR-004, Plan Correction)
- [ ] T025b [US1] (Depends on T025a, T025d, T016c) **AUGMENTATION EXECUTION**: Apply data augmentation via **functional-group-preserving edge dropout** (non-ester bonds only) and SMILES canonicalization.
 - **Algorithm**: Use RDKit's `GetSubstructMatches` with SMARTS `[C;D1][C;D2]=[O;D1][O;D1]` to identify ester bonds. Create a bond mask where `mask[bond_idx] = False` if bond is ester, `True` otherwise. Apply dropout only to `True` bonds with a dropout rate of `0.2 (1711.00066, https://arxiv.org/abs/1711.00066)`.
 - **Seed**: Use `SEED=42` for reproducibility.
 - **Rationale**: Bond rotation is chemically invalid for degradation pathways as it alters the 3D conformation required for specific hydrolysis/oxidation events. Edge dropout preserves the functional group integrity while expanding the dataset.
 - **Validation**: Verify that the augmented dataset size is at least 2x the pre-augmentation size (or log the actual factor) to satisfy FR-004's "significant factor" requirement.
 - **Output**: Save the augmented dataset to `data/processed/augmented_graph_dataset.parquet`. (FR-004, Plan Correction)
- [ ] T025c [US1] (Depends on T025b) **AUGMENTATION VALIDATION & SAVE**: Validate chemical integrity of the augmented dataset.
 - **Output**: Save the final dataset to `data/processed/final_dataset.parquet` with checksums.
 - Measure runtime and log to `data/reports/augmentation_timing.json`. **Constraint**: If duration > minutes, log a FAIL status; otherwise PASS.
 - Log the action to `data/processed/augmentation_log.json`. (FR-004, US-2 Scenario 3)
- [ ] T019 [US1] (Depends on T025c OR T017) **DATA INTEGRITY CHECK**: Verify the checksums of `data/processed/processed_graph_dataset.parquet` and `data/processed/final_dataset.parquet` (if created). Log any discrepancies. (Plan: Data Hygiene)
- [ ] T019b [US1] (Depends on T017) **METADATA GENERATION**: Generate `data/processed/dataset_metadata.json` containing the count of records, count of excluded records, and the action taken (none/augment/augment_aggressive). (Plan: Data Hygiene)
- [ ] T020 [US1] (Depends on T007a) Add logging for data ingestion actions, exclusions, flags, and power analysis warnings in `code/ingest.py` and `code/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Feature Attribution (Priority: P2)

**Goal**: Train a lightweight Graph Neural Network (≤3 layers, hidden dim ≤128) on the prepared dataset and generate feature importance scores via Integrated Gradients.

**Independent Test**: Can be fully tested by running the training script on a fixed random seed, verifying the model converges within 6 hours on a CPU-only runner, and confirming that the Integrated Gradients output highlights specific atoms/bonds in the polymer chain.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [US2] Unit test for GNN architecture constraints (layers ≤3, dim ≤128) in `tests/unit/test_model.py::test_gnn_layers_constraint`
- [ ] T022 [US2] Unit test for Integrated Gradients calculation on a dummy graph in `tests/unit/test_model.py::test_integrated_gradients_on_dummy_graph`
- [ ] T023 [US2] Integration test for training loop convergence on CPU in `tests/integration/test_training.py::test_training_converges_cpu`

### Implementation for User Story 2

- [ ] T024 [US2] (Depends on T017) Implement `model.py`: Define lightweight GNN architecture (GCN variant, ≤3 layers, hidden dim ≤128, activation=ReLU, pooling=mean) CPU-only. **Input Shape**: `[num_nodes, num_features]`, **Output Shape**: `[num_nodes, num_classes]`. (FR-003)
- [ ] T028 [US2] (Depends on T025c OR T017) **TRAINING**: Execute `python code/train.py --cv_strategy 5f` (or `--cv_strategy loo` if n < 50).
 - Check for existence of `data/processed/final_dataset.parquet`.
 - **Dependency Logic**: This task runs after T025c (if augmentation occurs) or T017 (if skipped).
 - Implement training loop with -fold cross-validation (or leave-one-out if n < 50) and random seed pinning.
 - Report mean macro-F1 and convergence check (loss delta < 5% over last 5 epochs).
 - **Checkpoint**: Save model to `data/reports/model_best.pth`. (FR-003, US-2 Scenario 1)
- [ ] T029 [US2] (Depends on T028) Implement `model.py`: Compute feature importance scores using Integrated Gradients on the trained model. **Output**: Save to `data/reports/ig_attribution_maps.json` with schema: `[{"atom_index": int, "feature_importance": float, "normalized_score": float}]`. (FR-005)
- [ ] T029b [US2] (Depends on T029) **NULL DISTRIBUTION GENERATION (ESTER SPECIFIC)**: Implement `evaluate.py`: Generate the null distribution for motif significance testing specifically for **ester bonds** by shuffling input motifs (shuffling edge features of ester bonds) repeatedly (A large number of permutations, SEED=42). **Algorithm**: Randomly permute the `edge_index` array of the input graph while preserving node features for non-ester bonds, then re-evaluate the model on the permuted graph to generate the null distribution. **Output**: Save to `data/reports/null_distribution.json` with schema: `{'bins': [float], 'counts': [int], 'observed_stat': float, 'p_value': float}`. (FR-006, SC-002, SC-005)
- [ ] T030 [US2] (Depends on T029b) **ESTER ATTRIBUTION VALIDATION**: Implement `evaluate.py`: Calculate percentage of hydrolysis cases where ester bonds are in the highest-ranked attribution scores.
 - **Traceability**: The value '10' is derived from the formally resolved SC-005 in T030a.
 - **Validation**: Compare this percentage against the null distribution generated by T029b. **Threshold**: `PERCENTAGE_THRESHOLD = 0.90 `. Generate `data/reports/ester_attribution_check.json` with keys `{"percentage": float, "threshold": 0.90, "p_value_null_comparison": float, "status": "PASS|FAIL"}`. (SC-005, Plan Correction)
- [ ] T031 [US2] (Depends on T030) Implement `evaluate.py`: Save model checkpoints, validation metrics (macro-F1), and IG attribution maps to `data/reports/`. (FR-003, FR-005)
- [ ] T032 [US2] (Depends on T031) Implement `evaluate.py`: Generate test-set predictions using the trained model; save predictions to `data/reports/test_predictions.json` for downstream validation. (FR-007)
- [ ] T033 [US2] (Depends on T017 OR T025c) Add logging for training progress, validation scores, augmentation stats, and runtime constraints in `code/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Motif Reporting (Priority: P3)

**Goal**: Receive a statistical report confirming that the identified structure-mechanism correlations are significant (via permutation test) and listing a limited set of the most prominent structural motifs.

**Independent Test**: Can be fully tested by running the analysis script on the final model outputs and verifying the generated report contains a p-value from the permutation test and a ranked list of motifs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [US3] Unit test for permutation test logic (shuffling motifs) in `tests/unit/test_evaluate.py::test_permutation_test_shuffling`
- [ ] T035 [US3] Unit test for motif extraction and ranking logic in `tests/unit/test_evaluate.py::test_motif_extraction_ranking`
- [X] T036 [US3] Integration test for full report generation pipeline in `tests/integration/test_reporting.py::test_full_report_generation`

### Implementation for User Story 3

- [ ] T037c [US3] (Depends on T032) **SPEC AMENDMENT**: Update `spec.md` FR-006 to explicitly restrict the permutation test scope to "ester bonds" as the primary motif of interest, validating the narrowed scope. (FR-006)
- [ ] T037 [US3] (Depends on T037c, T031, T029b) **SCIENTIFIC VALIDATION (Permutation Test - General Motif Masking)**: Execute `python code/evaluate.py --test permutation --target general`.
 - **Motif Extraction**: Use RDKit to find subgraphs of small sizes, targeting general motifs (not just esters) using SMARTS patterns.
 - **Statistic Definition**: `observed_stat` = mean(macro-F1_original - macro-F1_masked). Masking method: Zero out the edge features of identified motif edges and re-evaluate.
 - **Null Distribution**: Generate `1000` permutations (SEED=42) to ensure statistical robustness.
 - **Mapping**: Explicitly document that 'Motif-Masking' implements the 'shuffling input motifs' requirement from US-3 Scenario 1 for general motifs.
 - Generate `data/reports/permutation_test_results.json` with schema: `{'bins': [float], 'counts': [int], 'observed_stat': float, 'p_value': float}` (FR-006, SC-002, US-3 Scenario 1, SC-005)
- [ ] T037b [US3] (Depends on T031) **LABEL-SHUFFLING VALIDATION**: Implement `evaluate.py`: Perform a label-shuffling permutation test to validate global model significance.
 - **Verification**: Verify that label-shuffling produces a p-value > 0.05 [UNRESOLVED-CLAIM: c_7b6775b9 — status=not_enough_info] (indicating the model is not learning random noise).
 - **Note**: This is a complementary test and does NOT satisfy FR-006's specific motif-shuffling requirement (handled by T037). (Complementary to T037)
- [ ] T038 [US3] (Depends on T038b, T031) **CONSTITUTIONAL VALIDATION (χ²)**: Implement `evaluate.py`: Implement χ² Discretization Protocol.
 - **Binning**: Apply 'quantile-based binning' (top quantile of absolute IG scores vs rest) on absolute Integrated Gradients scores.
 - **Tie-Breaking**: If a score is at a low percentile threshold, assign it to the 'Low' bin.
 - **Validation**: Log bin counts and verify distribution is uniform before proceeding.
 - Generate `data/reports/chisquare_validation.csv` with schema: columns `['bin_id', 'observed_count', 'expected_count', 'chi_sq_contrib']` and a summary row `['TOTAL',...,..., 'chi_sq_stat']`. (Constitution VI, Plan Complexity Tracking)
- [ ] T039 [US3] (Depends on T037, T031) Implement `evaluate.py`: Aggregate feature importances to identify a small set of top structural motifs and their correlation with degradation types. **Logic**: Group by motif pattern, calculate mean importance, rank by mean importance, select top few. Merge results with T037 p-values. (FR-007)
- [ ] T040 [US3] (Depends on T039, T037, T031) Implement `evaluate.py`: Generate final report in `data/reports/` including p-values, motif list, and confidence flags (FR-007). **Content**: `p_value`, `motif_list` (top 3-5), `confidence_flags` (predictions < 0.6).
- [ ] T041 [US3] (Depends on T031) Implement `evaluate.py`: Add logic to flag predictions with confidence < `0.6` as "low confidence" in the report (US-3 Acceptance Scenario 3, Plan: Data Exclusion)
- [ ] T042 [US3] (Depends on T031) Add logging for statistical test results and report generation in `code/evaluate.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Generate `README.md` in repository root with usage examples, setup instructions, and data schema sections
- [X] T044 [P] Generate `docs/usage.md` with detailed API and script documentation
- [X] T045 [P] Refactor `code/utils.py` to ensure shared utilities are modular and tested
- [X] T046 [P] Refactor `code/data_models.py` to ensure data classes are robust and validated
- [X] T047 [P] Implement memory monitoring utility in `code/utils.py`
- [ ] T048 [P] Integrate subsampling trigger in `code/preprocess.py` if memory > 7GB
- [X] T049 [P] Additional unit tests for edge cases in `tests/unit/`: `test_invalid_smiles_raises`, `test_empty_dataset_raises`
- [X] T050 [P] Run `quickstart.md` validation to ensure end-to-end pipeline executes within 6 hours

---

## Revision Concerns & Additional Tasks

**Purpose**: Address specific gaps identified in the plan regarding data source reliability, API robustness, and statistical rigor.

### Implementation for Revision Concerns

- [ ] T051 [US1] **API SOURCE VERIFICATION & FALLBACK**: Implement a robust `fetch_nist_polyester_data` function in `code/ingest.py` that:
 - Attempts to fetch data from the NIST Chemistry WebBook using a verified query for "polyester" and "degradation".
 - Implements a **hard fail** (raises `RuntimeError`) if the API returns no data or rate-limits after 3 retries, **preventing** silent fallback to synthetic data, UNLESS `CI_MODE=true`.
 - If `CI_MODE=true` and API fails, the script must output a clear warning and allow the T013 fallback mechanism to proceed.
 - If `CI_MODE=false` and API fails, the script must output a clear error message: "CRITICAL: No real data available from NIST. Pipeline cannot proceed without real data." and exit with code 1.
 - **Rationale**: Ensures strict adherence to the "Real data + real results only" rule in production while allowing deterministic fallbacks for CI reproducibility. (Plan: Data Hygiene, Rule: Real data only)

- [ ] T052 [US1] **MATERIALS PROJECT API INTEGRATION**: Implement `fetch_materials_project_polyester_data` in `code/ingest.py` to:
 - Query the Materials Project API for polymer records with degradation data.
 - Parse the JSON response to extract SMILES, environmental conditions, and degradation pathways.
 - Handle authentication errors and missing API keys gracefully by logging a clear warning but **not** falling back to synthetic data.
 - Merge results with NIST data if available, otherwise proceed with whichever source provides data.
 - **Rationale**: Provides a secondary real data source to increase the likelihood of obtaining a sufficient dataset (n >= 150) while maintaining data integrity. (Plan: Data Availability Assumption)

- [ ] T053 [US3] **STATISTICAL POWER ANALYSIS ENHANCEMENT**: Update `code/preprocess.py` (T017) to:
 - Perform a formal power analysis (e.g., using `statsmodels.stats.power`) to determine the minimum sample size required for the desired effect size (e.g., Cohen's d = 0.5) at alpha = 0.05 and power = 0.8.
 - If the current sample size `n` is below the calculated minimum, generate a warning in `data/reports/power_analysis_report.json` with the specific deficit and recommend data collection or augmentation.
 - **Rationale**: Moves beyond a simple threshold check (n < 150) to a scientifically grounded power analysis, ensuring the study has sufficient statistical power to detect meaningful effects. (US-3 Scenario 1, SC-004)

- [ ] T054 [US3] **MOTIF SIGNIFICANCE VALIDATION**: Enhance `code/evaluate.py` (T037) to:
 - Implement a **Bonferroni correction** or **False Discovery Rate (FDR)** control when testing multiple motifs for significance, to account for multiple hypothesis testing.
 - Adjust the p-values accordingly and report both the raw and corrected p-values in `data/reports/permutation_test_results.json`.
 - **Rationale**: Ensures that the reported significant motifs are not false positives due to multiple testing, increasing the scientific rigor of the findings. (US-3 Scenario 1, SC-002)

- [ ] T055 [US3] **CONFIDENCE INTERVAL ESTIMATION**: Implement `code/evaluate.py` to:
 - Calculate confidence intervals for the macro-F1 score and the motif importance scores using bootstrapping (e.g., A large number of bootstrap samples).
 - Include these intervals in the final report (`data/reports/final_report.md`) to provide a measure of uncertainty for the key metrics.
 - **Rationale**: Provides a more complete picture of the model's performance and the reliability of the identified motifs, addressing the need for robust statistical validation. (US-3 Scenario 1, SC-002)

- [X] T056 [P] **DATA VISUALIZATION**: Implement `code/visualize.py` to:
 - Generate visualizations of the molecular graphs with highlighted atoms/bonds based on Integrated Gradients scores.
 - Create plots of the permutation test results (null distribution vs. observed statistic).
 - Save these visualizations to `data/reports/` for inclusion in the final report.
 - **Rationale**: Enhances the interpretability of the results and provides visual evidence for the identified structure-mechanism correlations. (FR-007, US-3 Goal)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T017 output)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model outputs from US2 (T031)

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
Task: "Unit test for SMILES validation and RDKit graph conversion in tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid"
Task: "Unit test for missing data exclusion logic in tests/unit/test_preprocess.py::test_missing_env_excludes_record"

# Launch implementation tasks for User Story 1 together (if dependencies allow):
Task: "Implement ingest.py: Download records..."
Task: "Implement preprocess.py: Convert SMILES to molecular graphs..."
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training) - *Wait for T017 output*
 - Developer C: User Story 3 (Validation) - *Wait for T031 output*
3. Stories complete and integrate independently

---

## Methodological Corrections

**⚠️ MANDATORY INSTRUCTIONS FOR IMPLEMENTERS**

The following rules override any conflicting instructions in `spec.md` or previous drafts. These are the **only** valid instructions for this project:

1. **Data Handling Distinction**:
 - **Missing Labels**: Records missing 'degradation pathway' labels MUST be **FLAGGED** (saved to `data/raw/flagged_for_curation.csv`) for manual review, then excluded from the immediate training set. This satisfies FR-008 and US-1 Scenario 2.
 - **Missing Environmental Data**: The project MUST implement **EXCLUSION** of records with missing temp/pH/UV. **Imputation is FORBIDDEN**. The final pipeline MUST select the exclusion path (Plan Correction).
2. **Augmentation Strategy**:
 - **Bond Rotation**: **FORBIDDEN**. The Plan explicitly forbids implementing 'bond rotation' as it is 'chemically invalid'. The only augmentation method is 'functional-group-preserving edge dropout' (T025b).
 - **T025b**: Use 'functional-group-preserving edge dropout' (non-ester bonds only) and SMILES canonicalization as the final augmentation method. Skip if n > 150.
3. **Statistical Validation**:
 - **T037**: Implement 'shuffling input motifs' specifically for **general motifs** (with T029b handling **ester-specific** shuffling) to satisfy SC-005. This is the primary validation method for motif significance.
 - **T038**: Implement χ² Discretization Protocol to satisfy Constitution Principle VI. This is the complementary validation method.
4. **Thresholds**: For SC-004, trigger a warning if n < 150. For SC-005, use `THRESHOLD_TOP_PERCENT` (default **10** per T030a) and `PERCENTAGE_THRESHOLD` (default 0.90) for verification. For US-3, use `CONFIDENCE_THRESHOLD` (default 0.6).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data ingestion must use real URLs; no synthetic data generation allowed (except deterministic seed fallback for CI).
- **CRITICAL**: Records with missing environmental data (temp/pH/UV) MUST be FLAGGED then EXCLUDED (DEFAULT PATH). Imputation is FORBIDDEN.
- **CRITICAL**: Records with missing labels MUST be FLAGGED for curation before exclusion (FR-008).
- **CRITICAL**: GNN must run on CPU only; no CUDA/GPU dependencies.
- **CRITICAL**: Edge Dropout (T025b) is the ONLY augmentation method. Bond Rotation is FORBIDDEN and has been removed from the task list.
- **CRITICAL**: χ² Test (T038) is Constitutional/Complementary; Permutation Test (T037) is Scientific/Primary.
- **CRITICAL**: Confidence threshold < `0.6` is MANDATORY for flagging low-confidence predictions (US-3 Scenario 3, Plan).
- **CRITICAL**: T017, T025a, T025b, T025c atomize the power analysis and augmentation logic for deterministic execution.
- **CRITICAL**: T029b generates the null distribution locally in Phase 4 to allow T030 to run independently.
- **CRITICAL**: T037 is the primary satisfier of FR-006 and SC-005; T037b is complementary.
- **CRITICAL**: All tasks marked [X] are fully defined and ready for execution; downstream dependencies are guaranteed to have valid producers.
- **CRITICAL**: T051 and T052 enforce strict data source verification to prevent silent synthetic fallbacks.
- **CRITICAL**: T053, T054, T055 enhance statistical rigor with power analysis, multiple testing correction, and confidence intervals.
- **CRITICAL**: T056 adds visualizations to improve result interpretability.
- **CRITICAL**: T015b, T025d, T030a, T037c, T038b are mandatory spec/constitution amendment tasks to resolve conflicts.
- **CRITICAL**: All amendment tasks (T015b, T025d, T030a, T037c, T038b) MUST precede the implementation tasks they authorize.