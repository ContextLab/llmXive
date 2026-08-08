# Tasks: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

**Input**: Design documents from `/specs/001-chemo-biomarker-discovery/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

- [X] T001a [P] Create project directory structure: `src/`, `data/raw/`, `data/processed/`, `results/`, `results/meta_analysis/`, `tests/`, `specs/001-chemo-biomarker-discovery/contracts/`, `state/`
- [X] T001b [P] Initialize `.gitignore` (exclude `data/raw/*`, `__pycache__`, `.env`) and `README.md`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scikit-learn, rpy2, biopython, requests, scipy, psutil, sva)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/config.py`: Define paths, random seeds, FDR thresholds, CPU/memory limits, and `MAX_VARIANCE_GENES`
- [X] T005 [P] Implement `src/utils.py`: Logging setup, checksum generation, and timeout watchdog (h limit)
- [X] T006 [P] Create schema definitions in `specs/001-chemo-biomarker-discovery/contracts/` (dataset.schema.yaml, model_output.schema.yaml, meta_analysis.schema.yaml). **Requirement**: Explicitly define `dataset.schema.yaml` with fields for sample_id, tumor_type, response_label, expression_vector, and set_type, **referencing the Key Entities section in spec.md (Sample, GenePanel, Model) to ensure field types and structure align with the defined data model**. **Constraint**: Compute and store a SHA256 checksum for each schema file in `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` immediately after creation to satisfy Constitution Principle V (Versioning Discipline).
- [X] T007 Implement `src/__init__.py` and basic `src/main.py` orchestrator skeleton
- [X] T008 Setup `pytest` configuration and contract test harness for YAML schema validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download TCGA/GEO data, verify response labels (Data Feasibility Gate), harmonize IDs, normalize data, and split into discovery/training sets.

**Independent Test**: Run acquisition on a subset of cancer types; verify `data/processed/` contains ≥100 samples per type, harmonized HGNC symbols, variance-stabilized values, and distinct discovery/training splits.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/data_acquisition.py`: Download TCGA RNA-seq HTSeq-Counts and clinical metadata for **≥3 tumor types** via TCGAbiolinks (FR‑001). **Requirement**: Dynamically discover available tumor types. **Checksum**: Compute a cryptographic hash **only after** the file is fully downloaded, verified, and deemed valid. **Atomicity**: Ensure checksums are written atomically to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` in the `artifact_hashes` map **only for successful downloads**. **Do NOT** store in memory only. **Do NOT** write checksums for failed or skipped files.
- [ ] T013 [US1] Implement `src/data_acquisition.py`: Download GEO datasets via GEOquery (FR‑002). **Requirement**:
 1. Iterate through configured GEO IDs.
 2. If a dataset file cannot be fetched, log an error, skip the file, and **DO NOT** write a checksum to the state file.
 3. If a dataset exists but lacks response labels (RECIST/CR/PR), **skip that specific dataset**, log a warning, **decrement the `valid_geo_count` variable**, and **continue** to the next dataset. **Do NOT** halt immediately on a single failure.
 4. **Checksum**: Compute SHA256 for each successfully downloaded and **verified** GEO file and append to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` **only after verification is complete**. **Atomicity**: Ensure checksums are written atomically.
 5. After iterating through all configured GEO IDs, check if `valid_geo_count` < 2. If so, **halt execution with exit code 1** and write `data/feasibility_gate.json` with `status: "halted"`, `reason: "insufficient_geo_datasets"`.
 6. Proceed to the Feasibility Gate (T014) using the **updated** `valid_geo_count` variable. **Constraint**: The pipeline MUST halt if <2 valid GEO datasets are found, as per Spec Edge Cases and Plan Phase 0.
- [ ] T014 [US1] Implement **Data Feasibility Gate** in `src/data_acquisition.py`:
 1. **TCGA Gate**: If the count of valid TCGA tumor types is **< 3**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"` and `reason: "insufficient_tcga_types"`.
 2. **GEO Gate**: If the `valid_geo_count` (datasets with labels) is **< 2**, **Terminate execution** with exit code 1 and write `data/feasibility_gate.json` with `status: "halted"` and `reason: "insufficient_geo_datasets"`. **Clarification**: This is a hard failure; the pipeline does NOT proceed to internal validation if GEO < 2, as this violates the Independent Test criteria for US-1 and US-3.
 3. **Proceed**: If TCGA ≥ 3 **AND** `valid_geo_count` ≥ 2, write `data/feasibility_gate.json` with `status: "ready"`.
 4. **Logging**: Explicitly **log a warning if total download size > 5 GB** as specified in Spec FR‑001 before proceeding.
 5. **Checksum Finalization**: Ensure all checksums from T012/T013 are atomically written to `state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml` before exiting or proceeding.
- [ ] T015 [US1] Implement `src/preprocessing.py`: Harmonize Ensembl/Entrez to HGNC symbols using `mygene`/`biomaRt`; filter if coverage <95% (FR‑003).
- [ ] T017 [US1] Implement `src/preprocessing.py`: Filter low‑expression genes (CPM < 1 in > 80% samples) **after** harmonization and apply DESeq2 Variance‑Stabilizing Transformation (VST) via rpy2 (FR‑004). **Output**: VST‑normalized matrix saved to `data/processed/`. **Note**: This task must complete before batch correction (T016).
- [ ] T016 [US1] **Batch Correction**: Implement `src/preprocessing.py` to align platforms (FR‑014). **Logic**:
 1. **Step 1**: Attempt to apply **ComBat** (via `rpy2`/`sva`) on the combined VST-normalized matrix (TCGA + GEO).
 2. **Step 2**: If ComBat fails (e.g., due to batch size constraints), **attempt** Quantile Matching as a fallback.
 3. **Step 3**: If **both** ComBat and Quantile Matching fail, **halt** the pipeline with a clear error message.
 4. **Requirement**: This task runs after T017. **Constraint**: **Do NOT** use ComBat-seq. **Logging**: Record `batch_correction: "ComBat"` or `batch_correction: "Quantile_Matching"` in `results/summary.md` upon success.
- [ ] T020 [US1] Implement `src/preprocessing.py`: **Split data** for each tumor type into a `discovery_set` (for gene selection) and `training_set` (for model fitting) with a **stratified split maintaining the original class distribution** (FR‑013, Plan T020). **Output**: Save distinct CSV/Parquet files to `data/processed/{tumor_type}_discovery_set.csv` and `data/processed/{tumor_type}_training_set.csv`.
- [ ] T011 [P] [US1] Integration test for Feasibility Gate logic in `tests/integration/test_feasibility_gate.py`. **Requirement**: **Assert** that T014 writes `data/feasibility_gate.json` correctly in two specific scenarios: 1) **TCGA < 3**: Write `status: "halted"`, `reason: "insufficient_tcga_types"`. 2) **GEO < 2** (regardless of TCGA count): Write `status: "halted"`, `reason: "insufficient_geo_datasets"` and **halt execution**. **Assert**: The file content matches the specific Plan T011/T013 outcomes exactly. **Logical Dependency**: T014 (implementation of the gate logic). **Clarification**: This test asserts that the pipeline DOES NOT proceed if GEO < 2, ensuring full compliance with the Independent Test requirement for external validation. **Mocking**: Use mocked data files to simulate the TCGA < 3 and GEO < 2 scenarios to allow the test to run independently of network availability.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

**Goal**: Perform differential expression analysis dynamically per LOO iteration, identify cross-tumor biomarkers using REML, and generate a fixed gene panel.

**Independent Test**: Verify the selection logic (intersection/union) can be executed on a small sample of discovery sets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for REML meta-analysis calculation in `tests/unit/test_meta_analysis.py`
- [X] T022 [P] [US2] Integration test for LOO-Blind DE and panel selection logic on 3 tumor types (simulated) in `tests/integration/test_biomarker_discovery.py`

### Implementation for User Story 2

- [ ] T023a [US2] [DEPRECATED] Implement `src/differential_expression.py`: **Run DESeq2 Wald test on the static discovery set**. **Input**: `data/processed/{tumor_type}_discovery_set.csv`. **Constraint**: **DO NOT** use this output for the final meta-analysis. This task is deprecated in favor of T023b. **Output**: Significant genes per tumor type saved to `data/processed/{tumor_type}_de_results_static.csv`.
- [ ] T023b [US2] Implement `src/differential_expression.py`: **Run LOO-Blind DE Analysis**. **Logic**: For each tumor type `T` (held-out):
 1. **Subset**: Select data from all other tumor types (N-1) using `data/processed/{type}_discovery_set.csv`.
 2. **DE Analysis**: Run DESeq2 Wald test on this N-1 subset (FDR < 0.05, |log2FC| > 1.0). **Constraint**: **DO NOT** include the held-out type `T` in this analysis.
 3. **Output**: Save results to `data/processed/loo_iteration_{T}_de_results.csv`. **Requirement**: This output is the **sole source** for the meta-analysis in T027.
- [ ] T025 [US2] Implement `src/meta_analysis.py`: Define function to compute intersection of significant genes across ≥2 tumor types (FR‑006).
- [ ] T026 [US2] Implement `src/meta_analysis.py`: Define function to fallback to **union of top‑ranked genes (≤50)** if intersection is empty; **must write `fallback_reason: "intersection_empty"` to `results/summary.md`** as a hard requirement (FR‑006).
- [ ] T027 [US2] Implement `src/meta_analysis.py`: Define function to compute **Random-Effects Meta-Analysis (REML)** p-values and rank genes. **Requirement**: **Explicitly implement REML** (e.g., using `metafor` or `statsmodels`) to account for correlation between tumor types. **Override Note**: This overrides Spec FR-006's mention of Stouffer's method to comply with Plan Constraints and Constitution Principle VII (Statistical Rigor). **Document this override** in `results/summary.md`. **Input**: P-values and effect sizes from T023b (LOO-Blind results). **Output**: Combined p-values and ranked gene list.
- [ ] T028 [US2] Implement `src/meta_analysis.py`: Save **the final selected gene panel** (post‑intersection/union/fallback) to `results/meta_analysis/gene_panel.json` (conforms to `contracts/gene_panel.schema.yaml`) (FR‑006, Plan T028). **Do NOT save only logic**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (logic defined and panel generated)

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Build tumor‑type‑specific models using the fixed gene panel, perform nested CV, external validation, and statistical significance testing.

**Independent Test**: Train tumor‑specific models; run k‑fold nested CV on training set; validate on ≥2 GEO datasets; verify AUC ≥0.75 and calibration.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T029 [P] [US3] Contract test for model output schema in `tests/contract/test_model_schema.py`. **Requirement**: Verify that model output conforms to `model_output.schema.yaml` including all required fields. **Functions to test**: `validate_model_output`, `check_schema_compliance`.
- [ ] T030 [P] [US3] Integration test for full modeling and validation pipeline in `tests/integration/test_modeling.py`. **Requirement**: Use a small subset of `data/processed/` to verify end‑to‑end training, LOO, and external validation logic. **Functions to test**: `test_full_pipeline`, `test_loo_validation`.

### Implementation for User Story 3

- [ ] T031 [US3] Implement `src/modeling.py`: Build **Tumor‑type‑specific** Elastic‑Net Logistic Regression models using the **fixed gene panel** derived from Phase 2 (FR‑007). **Requirement**: Train one model per tumor type on the `training_set`. Do NOT pool data. **Dependency**: Depends on T028 success. **Input**: Load `results/meta_analysis/gene_panel.json` before training.
- [ ] T032 [US3] Implement `src/modeling.py`: Perform **Nested Cross‑Validation** on the **training_set** (FR‑007). **Logic**: **Load the fixed gene panel from `results/meta_analysis/gene_panel.json` (T028) BEFORE the CV loop begins**. **DO NOT** perform any gene selection or panel generation logic inside the nested CV loop. Use the fixed panel for all folds to prevent data leakage (FR‑013). **Dependency**: Depends on T028 success.
- [ ] T033 [US3] **LOO Validation Pre-Check**: Implement `src/validation.py`.
 1. **Pre-Check**: Count distinct tumor types (N) present in the loaded training sets. **If N < 3**, **Terminate execution immediately** with exit code 1, **raise a RuntimeError with a clear message "LOO validation requires at least 3 tumor types; found N types"**, and write `data/feasibility_gate.json` (`status: "halted"`, `reason: "insufficient_loo_types"`). This ensures that after hold‑out, at least 2 types remain (N‑1 ≥ 2). **Constraint**: The error must be propagated as a hard failure, not just a file write.
 2. **Input Check**: Verify that `data/processed/` contains `*_discovery_set.csv` and `*_batch_corrected.csv` files for all expected tumor types. If missing, halt with error "Missing required input files for LOO validation".
 3. **Output**: If N ≥ 3, proceed to T033b.
- [ ] T033b [US3] **Implement LOO Loop**: Implement `src/validation.py`.
 1. **Loop**: For each tumor type `T`:
    - **Subset**: Select data from all other tumor types (N-1).
    - **Train**: Train the model on the N-1 types using the fixed gene panel.
    - **Test**: Evaluate on the held-out type `T`.
    - **Record**: Record LOO AUC for each held-out type.
 2. **Output**: Aggregate results across all LOO iterations.
- [ ] T034 [US3] Implement `src/validation.py`: **External GEO Validation**. For each successfully downloaded GEO dataset, re‑normalize to the TCGA VST scale (using the same batch‑correction method recorded in T016), apply the trained per‑type model, and compute ROC‑AUC. If no GEO datasets are available, set `external_validation_status: "skipped"` in `results/summary.md`.
- [ ] T035 [US3] Implement `src/validation.py`: Compute ROC‑AUC, Precision‑PR, and Calibration Curves (deciles) (FR‑009). For deciles with ≥20 samples, ensure deviation ≤ ±10%; otherwise report CI and flag as 'underpowered'.
- [ ] T036 [US3] Implement `src/validation.py`: Perform DeLong's test against clinical covariates‑only baseline (FR‑011).
- [ ] T037 [US3] Implement `src/validation.py`: Handle class imbalance: **use stratified k‑fold for ALL cases**; apply cost‑sensitive learning **only if** responder ratio <20% (Edge Cases).
- [ ] T038 [US3] Implement `src/validation.py`: **Bonferroni Correction** (Single Source of Truth):
 1. **Pre‑Check**: Verify that `results/meta_analysis/gene_panel.json` exists and contains a non‑empty `selected` list. **If missing or empty, raise an error and halt**.
 2. **Meta‑Analysis**: Read `results/meta_analysis/gene_panel.json`. Calculate `m_meta` as the **number of genes in the final selected panel** (i.e., `len(selected_genes_in_panel)`), **NOT** the number of genes tested in discovery. Apply correction where `m = m_meta`. **Explicitly implement this logic** to satisfy Spec FR-010.
 3. **DeLong's Test**: Calculate `m_delong = number of model comparisons`. Apply correction where `m = m_delong`.
 4. **Threshold**: Adjusted p‑value must be < 0.01 (FR‑010). **Explicitly implement both distinct m calculations**, ensuring `m_meta` is derived from the final panel size regardless of whether it came from intersection or union.
 5. **Dependency**: This task requires reading the intermediate DE results from `data/processed/{tumor_type}_de_results.csv` (generated by T023) to verify the scope of the discovery phase if needed for logging, but the correction `m` is strictly the final panel size.
- [ ] T039 [US3] Implement `src/main.py`: Enforce runtime timeout and memory limit using `psutil` and watchdog; **write `results/runtime_metrics.json`** with `timeout_triggered` and `peak_memory_mb` (FR‑012, SC‑004, SC‑005).
- [ ] T040 [US3] Generate `results/summary.md` with final metrics, panel size, validation results, and fallback flags (FR‑006, FR‑009).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `specs/001-chemo-biomarker-discovery/quickstart.md`
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization (sequential processing of tumor types to save RAM) (Plan: Sequential Processing)
- [ ] T044a1 [P] Unit test for `train_model` empty input in `tests/unit/test_modeling.py`. **Requirement**: Create fixture `tests/fixtures/empty_input.csv` and implement `test_train_model_handles_empty_input` with specific assertion that the function raises `ValueError`.
- [ ] T044a2 [P] Unit test for `train_model` class imbalance in `tests/unit/test_modeling.py`. **Requirement**: Create fixture `tests/fixtures/imbalanced_input.csv` and implement `test_train_model_handles_imbalanced_classes` with specific assertion on cost-sensitive weights.
- [ ] T044b1 [P] Unit test for `nested_cv` parameter search in `tests/unit/test_modeling.py`. **Requirement**: Create fixture `tests/fixtures/cv_input.csv` and implement `test_nested_cv_selects_optimal_params` with specific assertion on returned alpha/lambda.
- [ ] T044b2 [P] Unit test for `nested_cv` leakage prevention in `tests/unit/test_modeling.py`. **Requirement**: Create fixture `tests/fixtures/leakage_check.csv` and implement `test_nested_cv_prevents_data_leakage` with specific assertion that no data from test folds is used in training.
- [ ] T044c1 [P] Unit test for `loo_validation` pre-check in `tests/unit/test_modeling.py`. **Requirement**: Create fixture `tests/fixtures/loo_small_input.csv` and implement `test_loo_validation_halts_on_insufficient_types` with specific assertion on error message.
- [ ] T044c2 [P] Unit test for `loo_validation` loop logic in `tests/unit/test_modeling.py`. **Requirement**: Create fixture `tests/fixtures/loo_normal_input.csv` and implement `test_loo_validation_correct_iteration` with specific assertion on the number of iterations and held-out types.
- [ ] T045 Run `quickstart.md` validation to ensure full pipeline execution on CPU‑only runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data output (specifically `discovery_set`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 logic and US1 `training_set`

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data acquisition before preprocessing
- Preprocessing before splitting (T020)
- Splitting before Differential Expression (T023)
- Differential Expression before meta‑analysis
- Meta‑analysis before modeling
- Modeling before validation

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for Feasibility Gate logic in tests/integration/test_feasibility_gate.py"

# Launch parallel implementation tasks:
Task: "Implement data acquisition for TCGA in src/data_acquisition.py"
Task: "Implement data acquisition for GEO in src/data_acquisition.py"
Task: "Implement ID harmonization and splitting in src/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including Split T020)
4. **STOP and VALIDATE**: Test User Story 1 independently (Data Feasibility Gate, Normalization, Splitting)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Candidate Gene Panel Logic)
4. Add User Story 3 → Test independently → Deploy/Demo (Tumor‑specific Models & Validation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline & Splitting)
 - Developer B: User Story 2 (Biomarker Discovery Logic on Discovery Set)
 - Developer C: User Story 3 (Modeling on Training Set)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **CPU Constraint**: All tasks must be implementable on a limited number of CPU cores, a constrained amount of RAM, and no GPU.
- **Data Integrity**: Never fabricate data; use real TCGA/GEO sources via verified mirrors. **Fallback to verified mock data only if real API fails verification**.
- **FR‑013 Compliance**: Strict separation of discovery (gene selection) and training (model fitting) sets is mandatory. DE is performed ONCE on the full discovery set (or N-1 subset for LOO).
- **FR‑007 Compliance**: Models must be tumor‑type‑specific, not pooled.
- **FR‑014 Compliance**: **ComBat** (for continuous VST data) is the primary method for batch correction; **fallback to Quantile Matching** if ComBat fails; **do NOT use ComBat-seq**.
- **FR‑008 Compliance**: LOO validation must halt if the dataset drops to a minimal number of types where LOO is invalid. The task logic must explicitly raise an error and exit.
- **FR‑010 Compliance**: Distinct Bonferroni correction logic for meta‑analysis (m = **number of genes in the final panel**) vs DeLong's test (m = comparisons). Ensure both are correctly calculated and applied.
- **FR‑006 Compliance**: The fallback to union of top-ranked genes must be explicitly triggered only when the intersection is empty, and the reason must be logged in `results/summary.md`.
- **FR‑001/002 Compliance**: Ensure all data downloads are verified against the expected checksums and that missing response labels cause the specific dataset to be skipped, not the entire pipeline, unless the minimum thresholds are not met. **Pipeline must halt if <2 valid GEO datasets exist**.
- **FR‑012 Compliance**: Ensure all tasks are optimized for the CPU-only GitHub Actions runner constraints (≤6h, ≤7GB RAM) by using streaming, chunked processing, and separate R processes where necessary.
- **Meta-Analysis Method**: Use **Random-Effects Meta-Analysis (REML)** for cross-tumor integration as mandated by the Plan and Constitution, overriding Spec FR-006's mention of Stouffer's method.