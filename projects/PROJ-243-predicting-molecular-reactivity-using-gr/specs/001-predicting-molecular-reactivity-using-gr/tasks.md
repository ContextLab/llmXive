---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Input**: Design documents from `/specs/001-predicting-molecular-reactivity/`
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

- [ ] T001a [P] Create data directory: `data/raw`
- [ ] T001b [P] Create data directory: `data/processed`
- [ ] T001c [P] Create data directory: `data/assets`
- [ ] T002 [P] Create code and artifact directories: `code`, `artifacts`, `tests`
- [X] T003 [P] Initialize Python 3.11 project with `requirements.txt` (pinning `torch`, `rdkit`, `torch-geometric`, `scikit-learn`, `pandas`, `datasets`, `networkx`, `psutil`, `pyyaml`, `requests`, `chembl_webresource_client`)
- [ ] T004 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005-manual [P] **RUN REFERENCE VALIDATOR**: Implement and run `code/utils/validator.py` to verify all citations in `research.md` against primary sources (DOIs/URLs). **BLOCKING**: Must pass before T010a-manual and T010d-manual. **DELIVERABLE**: Validation report in `artifacts/validation_report.json`. **DEPENDS ON**: None.

- [ ] T010a-manual [P] [FR-008] **CURATE REFERENCE SUBSTRUCTURES**: Manually download the dataset from **DOI: 10.1038/s41597-020-00628-6** (Zenodo record ID: **10.5281/zenodo.3932859**). **INSTRUCTIONS**: Navigate to the Zenodo page, identify the file ending in `.csv` or `.parquet` corresponding to Table 2, and download it to `data/raw/source_ref_table2.csv`. Manually verify the content against the source literature. **ERROR HANDLING**: If the file cannot be found or verified, **HARD FAIL**. **Deliverable**: `data/raw/source_ref_table2.csv`. **DEPENDS ON**: T005-manual.

- [ ] T010a-parse [P] [FR-008] **PARSE ZENODO DATA**: Implement `code/curate_reference.py` to parse `data/raw/source_ref_table2.csv`. **INSTRUCTIONS**: Load the CSV. Map columns explicitly: `SMILES` (or `smiles`) -> `smiles`, `Source` (or `source`) -> `source_doi`, `Description` (or `description`) -> `description`. If column names differ, log the detected names and fail if a mapping cannot be inferred. **DO NOT** generate synthetic data. **Deliverable**: `data/raw/reference_substructures_raw.csv`. **DEPENDS ON**: T010a-manual.

- [ ] T010d-manual [P] [FR-009] **CURATE KINETIC DATASET**: Manually download the dataset from **DOI: 10.1093/nar/gky1079** (Table 1). **INSTRUCTIONS**: Navigate to the source, identify Table 1, and download the data to `data/raw/kinetic_source.csv`. Manually verify the content. **Deliverable**: `data/raw/kinetic_source.csv`. **DEPENDS ON**: T005-manual.

- [ ] T010d-script [P] [FR-009] **TAG KINETIC DATASET**: Implement `code/curate_kinetic.py` to parse `data/raw/kinetic_source.csv`. **INSTRUCTIONS**: Load the CSV. Map columns explicitly: `SMILES` (or `smiles`) -> `smiles`, `Rate Constant` (or `rate_constant` or `k`) -> `rate_constant`, `Temperature` (or `temperature` or `T`) -> `temperature`, `Source` (or `source_doi`) -> `source_doi`. Add `reaction_type` column by mapping `reaction_ec` (EC number) to categories using this EXPLICIT lookup table:
 - `EC 1.x.x.x` -> `oxidation_reduction`
 - `EC 2.x.x.x` -> `transferase`
 - `EC 3.x.x.x` -> `hydrolase`
 - `EC 4.x.x.x` -> `lyase`
 - `EC 5.x.x.x` -> `isomerase`
 - `EC 6.x.x.x` -> `ligase`
 - If the `reaction_class` text contains 'nucleophilic', set `reaction_type` = `nucleophilic_attack`.
 - If the `reaction_class` text contains 'electrophilic', set `reaction_type` = `electrophilic_attack`.
 - If the `reaction_class` text contains 'pericyclic', set `reaction_type` = `pericyclic_reaction`.
 - **HARD FAILURE**: If the dataset contains an insufficient number of entries after extraction, OR if the `reaction_type` column is missing/empty for any entry, the task MUST fail. **DO NOT** generate synthetic data. **Deliverable**: `data/raw/kinetic_dataset_raw.csv`. **DEPENDS ON**: T010d-manual.

- [ ] T010g [P] [FR-008/FR-009/Data Hygiene] **DEFINE CHECKSUM SCHEMA**: Create `data/raw/checksums_schema.json` defining the **expected structure** (keys, file paths, version) for the checksums file. **DO NOT** pre-populate with expected hashes. This is a static contract definition. **DEPENDS ON**: None.

- [ ] T010h-external [P] [FR-008/FR-009/Data Hygiene] **COMPUTE AND POPULATE CHECKSUMS (EXTERNAL)**: Verify that `data/raw/reference_substructures_raw.csv` and `data/raw/kinetic_dataset_raw.csv` exist. Compute their SHA-256 hashes and write them to `data/raw/checksums.json` using the schema defined in T010g. **MUST** fail if files are missing. **DEPENDS ON**: T010a-parse, T010d-script, T010g.

- [ ] T010b [P] [FR-008] Verify checksum (SHA-256) of `data/raw/reference_substructures_raw.csv` against the hash in `data/raw/checksums.json`. **DEPENDS ON**: T010h-external.

- [ ] T010c [P] [FR-008] Ingest verified data into `data/assets/reference_substructures.csv` with schema validation. **NOTE**: This file is the canonical input for T030. **DEPENDS ON**: T010b.

- [ ] T010c-utilize [P] [FR-008] **UTILIZE REFERENCE SET**: Implement `code/utilize_reference.py` to load `data/assets/reference_substructures.csv` and verify its presence and schema before downstream tasks. **Deliverable**: Log entry confirming utilization. **DEPENDS ON**: T010c.

- [ ] T010e [P] [FR-009] Verify checksum (SHA-256) of `data/raw/kinetic_dataset_raw.csv` against the hash in `data/raw/checksums.json`. **DEPENDS ON**: T010h-external.

- [ ] T010f [P] [FR-009] Ingest verified external kinetic data into `data/assets/kinetic_dataset.csv` with schema validation. **NOTE**: This file is the canonical input for T031. **DEPENDS ON**: T010e.

- [ ] T010f-utilize [P] [FR-009] **UTILIZE KINETIC DATASET**: Implement `code/utilize_kinetic.py` to load `data/assets/kinetic_dataset.csv` and verify its presence and schema before downstream tasks. **Deliverable**: Log entry confirming utilization. **DEPENDS ON**: T010f.

- [ ] T010m [P] [FR-008/FR-009] **VERIFY CURATION**: Run the Reference Validator (`code/utils/validator.py`) on `data/raw/reference_substructures_raw.csv` and `data/raw/kinetic_dataset_raw.csv` to verify the extracted data against the source DOIs. **MUST** fail if verification fails. **DEPENDS ON**: T010a-parse, T010d-script.

- [ ] T013 [P] [US1] **DOWNLOAD QM9**: Stream QM9 from `torch_geometric.datasets.QM9` to `data/raw/qm9_subset.parquet`. **DELIVERABLE**: `data/raw/qm9_subset.parquet`. **DEPENDS ON**: None.

- [ ] T010h-qm9 [P] [FR-001/Data Hygiene] **COMPUTE QM9 CHECKSUM**: Compute SHA-256 hash for `data/raw/qm9_subset.parquet` and append to `data/raw/checksums.json`. **DEPENDS ON**: T013.

- [ ] T010i [P] [FR-001/FR-009] **VALIDATE DATA AVAILABILITY**: Ensure `data/assets/kinetic_dataset.csv` (T010f), `data/assets/reference_substructures.csv` (T010c), and `data/raw/qm9_subset.parquet` (T013) exist and are non-empty. **DEPENDS ON**: T010c, T010f, T013, T010h-qm9. **NOTE**: This task is the final gate for Phase 2.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download QM9 subset and preprocess into graph structures using only CPU resources, ensuring memory safety.

**Independent Test**: The pipeline can be fully tested by executing the data download and preprocessing script on a CPU-only runner and verifying that the output graph objects are correctly formed and fit within memory limits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T011 [P] [US1] Unit test for SMILES parsing and exclusion logic in `tests/unit/test_parsing.py`
- [ ] T012 [P] [US1] Integration test for full download → preprocess flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T014a [US1] **Preprocess Graphs**: Implement `code/02_preprocess_graphs.py` logic to convert SMILES to graphs using RDKit. **Includes**:
 1. **Memory Safety Logic**: During batch processing, if memory usage exceeds **4 GB**, trigger **subset sampling** by **iteratively reducing the number of molecules processed by [deferred]** until memory usage drops below 4 GB. Log the specific adjustment in `artifacts/memory_adjustment.log`.
 2. **Streaming Strategy**: Use `pandas.read_parquet(..., chunksize=...)` to process the dataset in chunks, ensuring the full dataset contributes to the result without holding it all in memory. Log the sampling strategy used.
 3. Invalid SMILES handling: Log and exclude molecules; target < 0.1% exclusion. **CRITICAL**: Write exclusion count and list of excluded IDs to `artifacts/exclusion_report.json` (machine-readable JSON, not just log text) as part of this task's execution.
 4. **VALIDATION**: Immediately after writing the report, validate that the exclusion count is < 0.1%. If this threshold is exceeded, **log a WARNING** and flag the run as `DATA_QUALITY_ISSUE` in the report. **DO NOT** crash the pipeline.
 5. **Deliverable**: **Serialize preprocessed graphs to `data/processed/graphs_intermediate.pt` (PyTorch Geometric format)**. This persistent artifact is REQUIRED for downstream tasks. **CRITICAL**: This task MUST save the intermediate graph objects to disk to ensure reproducibility and allow T017/T016 to resume without re-processing. **DO NOT** rely on in-memory objects only.
 6. **Explicit Deliverables**: Ensure `artifacts/exclusion_report.json`, `artifacts/memory_adjustment.log`, and `data/processed/graphs_intermediate.pt` are written and validated as part of this task's execution. **DEPENDS ON**: T013.
- [ ] T014c [US1] **Validate Exclusions**: Verify `artifacts/exclusion_report.json` exists and count < 0.1%. Verify `artifacts/memory_adjustment.log` if applicable. **DEPENDS ON**: T014a.
- [ ] T017 [US1] **Generate Murcko Scaffold Splits**: Implement `code/03_split_data.py` to perform Murcko scaffold splitting on the **intermediate graphs from `data/processed/graphs_intermediate.pt`** (T014a). **Output**: Train/Val/Test **indices files** saved to `data/processed/splits/`. **Deliverable**: `data/processed/splits/train_indices.pt`, `data/processed/splits/val_indices.pt`, `data/processed/splits/test_indices.pt`. **DEPENDS ON**: T014a.
- [ ] T016 [US1] [US1] **Serialization**: Serialize preprocessed graphs (using the **split indices files** from T017 to filter `data/processed/graphs_intermediate.pt`) to `data/processed/graphs.pt` (PyTorch Geometric format) with derivation logs and schema validation. **Deliverable**: `data/processed/graphs.pt`. **DEPENDS ON**: T014a, T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train lightweight Spectral GNN, Heterophily-aware GNN, and Random Forest baseline; compare performance.

**Independent Test**: The training and evaluation loop can be tested independently by running the training script for a fixed number of epochs and verifying that both models converge and produce metric logs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017-test [P] [US2] Unit test for model architecture initialization (CPU mode) in `tests/unit/test_models.py`
- [ ] T018 [P] [US2] Integration test for training loop convergence in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement lightweight Spectral GNN architecture in `code/models/spectral_gnn.py` (CPU-only, no CUDA). **MUST** implement as distinct architecture (FR-002).
- [ ] T020 [US2] Implement Heterophily-aware GNN architecture in `code/models/hetero_gnn.py` (based on VR-GNN principles, CPU-only). **MUST** implement as distinct architecture (FR-002).
- [ ] T021a [US2] Implement Random Forest baseline using Morgan fingerprints in `code/models/random_forest_baseline.py`. **MUST** implement as distinct baseline (FR-004).
- [ ] T022 [US2] Implement `code/train_models.py` to train all three models (Spectral GNN, Hetero GNN, Random Forest) for a sufficient number of epochs (with early stopping: patience=5, metric='val_loss') targeting the prediction of DFT-derived properties. **Note**: Convergence criteria defined in `code/config.py`, not hardcoded. **CRITICAL**: Save the best model weights for each model to `artifacts/weights/best_{model_name}.pt` (e.g., `best_spectral_gnn.pt`) to ensure T025 has a deterministic target to archive. **CPU SAFETY**: If memory usage exceeds a substantial threshold during training, trigger a **subset sampling** strategy (**reduce dataset size by [deferred] iteratively until memory < 4 GB**) and re-run, logging the adjustment. **DO NOT** use GPU escape hatches or external GPU environments. **DEPENDS ON**: T019, T020, T021a.
- [ ] T022b [US2] [FR-007] **Log Artifacts**: Implement `code/utils/artifact_logger.py` to explicitly log model weights, attribution maps, and metrics to the repository as required by FR-007. **CRITICAL**: This task must run after T022 and T023a to ensure all artifacts are logged. **Deliverable**: Structured logs in `artifacts/logs/artifact_log.json`. **DEPENDS ON**: T022, T023a.
- [ ] T023a [US2] **Generate Predictions**: Implement `code/04_evaluate.py` to generate predictions for all models. **Deliverable**: Output `artifacts/predictions.json` with model predictions. **DEPENDS ON**: T022.
- [ ] T023b [US2] **Compute Metrics**: Implement metric computation (MSE, MAE, Pearson R) in `code/04_evaluate.py`. **Deliverable**: Output `artifacts/metrics.json` with metrics for all models. **DEPENDS ON**: T023a.
- [ ] T023c-define [US2] **DEFINE COMPARISON STRATEGY**: Explicitly define the comparison matrix and Bonferroni correction factor (N) for the statistical tests. **LOGIC**: Determine if comparisons are pairwise (GNN vs RF) or 3-way (Spectral vs Hetero vs RF). Set N accordingly. **Deliverable**: Write `artifacts/comparison_strategy.json` with `n_comparisons` and `alpha_adj`. **DEPENDS ON**: T023b.
- [ ] T023f [US2] **Independence Check (Optional)**: Implement `code/04_independence_check.py` to calculate pairwise Tanimoto similarity of errors. **LOGIC**: If errors are correlated (p < 0.05), log a warning and recommend Wilcoxon for sensitivity analysis. **Deliverable**: Write `artifacts/independence_check_results.json` with `correlation_coefficient`, `p_value`, and `recommended_test`. **DEPENDS ON**: T023b.
- [ ] T023c-primary [US2] **Execute Primary Statistical Test**: Implement statistical tests in `code/04_evaluate.py`. **PRIMARY**: Paired t-test (as per FR-006). **CRITICAL**: **ALWAYS** run the Paired t-test regardless of T023f output. Apply Bonferroni correction (alpha_adj = 0.05/N, where N is from T023c-define). **MANDATORY**: Do not replace the t-test with Wilcoxon. **Explicit Step**: Run statistical tests and record results in `artifacts/model_comparison_raw.json` to satisfy FR-006. **Deliverable**: Write output to `artifacts/model_comparison_raw.json` with schema `{model: {mse, mae, pearson_r, predictions}, statistical_tests: {primary_test: 't-test', p_value_ttest, alpha_adj}}`. **DEPENDS ON**: T023b, T023c-define.
- [ ] T023c-sensitivity [US2] **Execute Sensitivity Statistical Test**: Implement Wilcoxon signed-rank test in `code/04_evaluate.py`. **CONDITIONAL**: **ONLY** run if T023f exists AND reports correlated errors (p < 0.05). If T023f is skipped or reports no correlation, skip this task. **Deliverable**: Append `p_value_wilcoxon` to `artifacts/model_comparison_raw.json`. **DEPENDS ON**: T023b, T023f.
- [ ] T023e [US2] **Generate Comparison Report & Justification**: Format the results from `artifacts/model_comparison_raw.json` into `artifacts/model_comparison_results.json` with the specified schema. **MUST** read the 'primary_test' field from the raw file and write the final formatted version. **Additionally**: Write `artifacts/statistical_justification.md` explicitly explaining the choice of statistical tests: **Paired t-test** (Primary, per FR-006) and **Wilcoxon signed-rank test** (Sensitivity, per Plan.md Methodological Note, conditional on T023f). **CRITICAL**: This artifact documents the fixed requirement (FR-006 mandates t-test) and the conditional nature of the sensitivity check. **Deliverable**: Finalized `artifacts/model_comparison_results.json` and `artifacts/statistical_justification.md`. **DEPENDS ON**: T023c-primary, T023c-sensitivity, T023f.
- [ ] T024 [US2] [US2] **Integration Test**: Write `tests/integration/test_statistics.py` to verify that `code/utils/metrics.py` (T007) correctly implements the paired t-test (PRIMARY) and Wilcoxon signed-rank test (SENSITIVITY) using mock data with known outcomes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

**Goal**: Identify structural/electronic features contributing to predictions and validate against curated references.

**Independent Test**: The attribution analysis can be tested by running the GNNExplainer on a subset of molecules and verifying valid importance scores against the curated reference set.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for attribution score calculation in `tests/unit/test_attribution.py`
- [ ] T027 [P] [US3] Contract test for attribution output schema in `tests/contract/test_attribution_schema.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/05_attribution.py` using GNNExplainer or gradient-based methods to generate importance scores. **Deliverable**: Intermediate importance scores (in-memory or temporary JSON). **DEPENDS ON**: T022.
- [ ] T029 [US3] Load curated reference set of known reactive substructures from `data/assets/reference_substructures.csv` (produced by T010c). **DEPENDS ON**: T010c-utilize.
- [ ] T030 [US3] Implement logic to aggregate importance scores across the dataset and rank the most significant structural/electronic features.
- [ ] T030a [US3] **Extract Subgraphs**: Implement logic to extract subgraphs from attributed molecules. **DEPENDS ON**: T028.
- [ ] T030b [US3] **Compute Similarity**: Compute Tanimoto similarity between extracted subgraph fingerprints and reference fingerprints. **THRESHOLD**: 0.85. **DEPENDS ON**: T030a, T029.
- [ ] T030c-feasibility [US3] **Validate VF2 Feasibility**: Run a benchmark of VF2 Subgraph Isomorphism on a representative subset of the dataset. **LOGIC**: If VF2 execution time > 1 hour or memory > 2 GB, **FLAG** and instruct T030c-calc to use the fallback heuristic. **Deliverable**: `artifacts/vf2_feasibility_report.json`. **DEPENDS ON**: T030a, T029.
- [ ] T030c-calc [US3] **Calculate Alignment**: Compute the alignment score between the top attributed substructures (from T030) and the curated reference set (from T029). **ALGORITHM**:
 1. **IF** `vf2_feasibility_report.json` indicates VF2 is feasible, use **VF2 Subgraph Isomorphism** (`networkx.algorithms.isomorphism.GraphMatcher`) to find matches.
 2. **ELSE**, use a **Tanimoto-based subgraph matching heuristic** (compare fingerprints of all possible subgraphs) as a fallback.
 3. For each match, extract the Morgan fingerprint of the matched subgraph. **CONVERSION**: If subgraphs are SMILES, use `Chem.MolFromSmiles`; if graph objects, convert to `rdkit.Chem.RWMol`.
 4. Calculate **Tanimoto similarity** between the matched subgraph's fingerprint and the reference fingerprint. **PARAMETERS**: Radius=2, nBits=2048.
 5. **MATCH THRESHOLD**: A match is valid if Tanimoto similarity >= 0.85.
 6. **ALIGNMENT SCORE FORMULA**: `Alignment Score = (Count of Valid Matches) / (Total Reference Substructures)`.
 7. **EDGE CASE**: If `Total Reference Substructures` is zero, return score 0.0. If `Count of Valid Matches` exceeds total, cap score at 1.0.
 8. Aggregate scores to produce the final alignment metric.
 9. **Write** `artifacts/alignment_score.json` containing the score.
 **Deliverable**: Write `artifacts/alignment_score.json` containing the score. **DEPENDS ON**: T030b, T030c-feasibility.
- [ ] T030c-verify [US3] **Validate Attribution Results**: Load `artifacts/alignment_score.json` and `data/assets/reference_substructures.csv`. Re-run the matching logic on a subset of attributed subgraphs to verify the matching process against the reference set. **CRITICAL**: This task explicitly validates the *results* (the logic/matching process) against the reference set, satisfying the 'utilize' requirement. **Deliverable**: Write `artifacts/alignment_validation_report.json` confirming the validation passed. **DEPENDS ON**: T030c-calc, T029.
- [ ] T030d [US3] [US3] **Verify Alignment**: Write `tests/contract/test_alignment_threshold.py` to assert that the score in `artifacts/alignment_score.json` is >= 0.7 (SC-003).
- [ ] T031 [US3] Load the full `data/assets/kinetic_dataset.csv` (produced by T010f) AND the full `artifacts/model_comparison_results.json` (produced by T023e); validate correlation between predicted gap and experimental rates for the **filtered** dataset. **CRITICAL**: Filter the kinetic dataset to include ONLY reaction types where the HOMO-LUMO gap is a known dominant predictor: **'nucleophilic_attack'**, **'electrophilic_attack'**, **'pericyclic_reaction'**. **Do not** validate on the entire dataset if it contains other reaction types. **MUST** include a descriptive log entry analyzing reaction types where the proxy is theoretically strongest, but restrict scientific interpretation to those specific reaction types. **ERROR HANDLING**: If the specific reaction types are not found in the dataset, **LOG A WARNING** and proceed with available data. **ERROR HANDLING**: If the filtered dataset contains **< 20 molecules**, **FAIL THE VALIDATION STEP** with status `VALIDATION_IMPOSSIBLE`. Log the exact count and reason. **DO NOT** proceed with correlation calculation. This ensures SC-006 (n>=20) is not falsely claimed. **Deliverable**: `artifacts/proxy_validation_report.json` containing `correlation_full_dataset`, `correlation_filtered_dataset` (only if n>=20), `correlation_by_reaction_type_descriptive`, `mechanistic_consistency_notes`, and `data_availability_flag` (set to 'INSUFFICIENT_DATA' if n<20). **ERROR HANDLING**: If `data/assets/kinetic_dataset.csv` is missing, log 'MISSING_DATA' and exit gracefully. **DEPENDS ON**: T010f (Kinetic Data), T023e (Comparison Results).
- [ ] T032 [US3] **Generate Attribution Maps**: Finalize the attribution maps and validation reports in `artifacts/`. **Deliverable**: `artifacts/attribution_maps.json` (finalized JSON file). **DEPENDS ON**: T028, T030, T030c-calc, T030c-verify.
- [ ] T025 [US3] **Archive All Artifacts**: Log all model weights (`artifacts/weights/best_*.pt`), attribution maps (`artifacts/attribution_maps.json`), metrics (`artifacts/metrics.json`), comparison results (`artifacts/model_comparison_results.json`), validation reports (`artifacts/proxy_validation_report.json`, `artifacts/alignment_validation_report.json`), and statistical justification (`artifacts/statistical_justification.md`) to `artifacts/final_archive.tar.gz` (compressed archive) with checksums. **MUST** include attribution maps and metrics explicitly. **DEPENDS ON**: T022, T023e, T032, T031.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` (include `quickstart.md` with run instructions)
- [ ] T034 Code cleanup and refactoring to ensure type hints and docstrings are complete
- [ ] T035 Performance optimization: Verify end-to-end runtime ≤ 6 hours and memory ≤ 4 GB on CI. **INSTRUCTIONS**: Use `psutil` to log peak RSS memory and `time` module for runtime. Assert against GB/6h in `tests/integration/test_performance.py`. **Deliverable**: Pass/Fail report in `artifacts/performance_report.json`.
- [ ] T036 [P] Additional unit tests for edge cases (invalid SMILES, download failures) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure all artifacts are reproducible
- [ ] T038 Verify `state/` YAML is updated with SHA-256 hashes of final artifacts
- [ ] T039 [P] Final review of all artifacts against Constitution principles

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
- **User Story 2 (P2)**: Depends on US1 (requires preprocessed data)
- **User Story 3 (P3)**: Depends on US2 (requires trained models)

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

### Specific Task Dependencies (Critical for Execution)

- **T014a** (Preprocess) MUST complete before **T017** (Splitting).
- **T017** (Splitting) MUST complete before **T016** (Serialization).
- **T010a-manual** and **T010d-manual** MUST complete before **T010a-parse** and **T010d-script**.
- **T010a-parse** and **T010d-script** MUST complete before **T010c** and **T010f**.
- **T010h-external** (Populate Checksums) MUST complete before **T010b** and **T010e** (Verify Checksums).
- **T010g** (Define Schema) MUST complete before **T010h-external** (Populate Checksums).
- **T010h-qm9** (Populate Checksums) MUST complete before **T010i** (Validate Data Availability) for QM9.
- **T010h-external** (Populate Checksums) MUST complete before **T010i** (Validate Data Availability) for External.
- **T030a** (Extract) and **T030b** (Similarity) are now in Phase 5, ensuring they are available after US2 completes.
- **T031** (Validate Correlation) MUST complete after **T023e** (Comparison Report & Justification), **T010f** (Kinetic Data), and **T010d-script** (Tagging).
- **T023a**, **T023b**, **T023c-define**, **T023c-primary**, **T023c-sensitivity**, **T023e** are sequential within Phase 4. **T023e** (Report & Justification) now depends on **T023c-primary** (Tests).
- **T023a** depends on **T022**.
- **T023b** depends on **T023a**.
- **T023f** (Independence Check) depends on **T023b**.
- **T023c-sensitivity** (Sensitivity Test) depends on **T023b** AND **T023f** (for conditional Wilcoxon logic).
- **T023c-primary** (Primary Test) depends on **T023b** AND **T023c-define**.
- **T023e** (Report) depends on **T023c-primary** and **T023c-sensitivity**.
- **T025** (Archive All Artifacts) MUST complete after **T022** (Training), **T023e** (Report), **T032** (Attribution Maps), and **T031** (Proxy Validation). This is the single final archive step.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SMILES parsing and exclusion logic in tests/unit/test_parsing.py"
Task: "Integration test for full download → preprocess flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download_data.py to fetch QM9 subset..."
Task: "Implement code/02_preprocess_graphs.py to convert SMILES to graphs..."
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
 - Developer B: User Story 2 (waiting for data)
 - Developer C: User Story 3 (waiting for models)
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