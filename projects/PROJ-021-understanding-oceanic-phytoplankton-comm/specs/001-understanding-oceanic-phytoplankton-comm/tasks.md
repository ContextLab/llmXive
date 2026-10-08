# Tasks: Understanding Oceanic Phytoplankton Communities through Remote Sensing and Oceanographic Data

**Input**: Design documents from `/specs/001-phytoplankton-vlm-analysis/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-021-understanding-oceanic-phytoplankton-comm/`)
- [X] T002 Initialize Python 3.11 project with dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, torch, transformers, xarray, netCDF4, matplotlib, seaborn, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create configuration manager in `code/utils/config.py` (seeds, paths, hyperparameters, memory limits)
- [X] T005 [P] Implement CPU-only data loader utilities in `code/utils/data_loaders.py` (streaming, sampling to fit available RAM, strict error handling: NO synthetic fallback)
- [X] T006 Create base schema definitions in `specs/001-phytoplankton-vlm-analysis/contracts/` (phytoplankton_sample.schema.yaml, model_performance.schema.yaml)
- [X] T007 [P] Implement versioning utility in `code/05_versioning_state.py` (SHA-256 hashing logic to be called by Advancement-Evaluator Agent, not standalone script)
- [X] T008 Setup logging infrastructure in `code/utils/logging_config.py` (structured logs for pipeline monitoring)
- [X] T009a [P] Create `aligned_dataset.schema.yaml` in `specs/001-phytoplankton-vlm-analysis/contracts/`. **Definition**: Must include fields: `lat` (float), `lon` (float), `timestamp` (datetime), `basin` (string), `temp` (float), `salinity` (float), `nutrients` (float), `chlorophyll_a` (float), `quality_flags` (int). **Depends on**: None.
- [X] T009 [P] [US1] Contract test for schema validation in `tests/contract/test_schemas.py` (validates `aligned_dataset.schema.yaml` created in T009a). **Depends on T009a**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest, align, and preprocess multi-modal satellite and oceanographic data into a unified, CPU-tractable dataset.

**Independent Test**: Run the pipeline script on a sample subset; verify output is a single aligned CSV/NetCDF with <5% missing values, correct basin stratification, and memory usage <7GB.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Integration test for data alignment in `tests/integration/test_pipeline.py` (verifies temporal/spatial alignment logic)

### Implementation for User Story 1

- [ ] T011a [US1] Fetch NOAA/Copernicus Reanalysis data (Temperature, Salinity, Nutrients) from the verified physical oceanography source **CMEMS** to `data/raw/copernicus_global_reanalysis.nc`. **Dataset ID**: `cmems-global-analysis-forecast-phys-001-004`. **CRITICAL**: This task targets the physical drivers (Temperature, Salinity, Nutrients) as required by FR-001 and Constitution Principle VI, NOT the target variable (Chlorophyll). **Verification Step**: After download, verify the NetCDF file contains variables 'thetao' (temperature), 'so' (salinity), and 'nitrate' (or equivalent nutrient variable). **MUST ALSO VERIFY** that the variable 'chl' (chlorophyll) is ABSENT to enforce Multi-Modal Independence. If 'chl' is present or required variables are missing, raise an exception and halt. **Depends on T005**.
- [X] T011a_verify [US1] Verify and checksum `data/raw/copernicus_global_reanalysis.nc` using `code/05_versioning_state.py`. Update `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` with hash. **FAIL LOUDLY** if fetch failed or checksum mismatch (NO synthetic fallback). **Exit with code 1** and log "ERROR: Checksum mismatch for reanalysis.nc" to stderr. **Depends on T011a**.
- [X] T011b [US1] Fetch MODIS Aqua/Terra ocean color data from verified source `nasa/modis-aqua-l3-v6` (HuggingFace ID) to `data/raw/modis.nc`. **Depends on T005**.
- [X] T011b_verify [US1] Verify and checksum `data/raw/modis.nc`. Update state YAML. **FAIL LOUDLY** if fetch failed or checksum mismatch. **Exit with code 1** and log "ERROR: Checksum mismatch for modis.nc" to stderr. **Depends on T011b**.
- [X] T011c [US1] Fetch SeaBASS in-situ data (Chl-a, SST, Salinity) from verified source `noaa/seabass` (HuggingFace ID, public access, no API key required) to `data/raw/seabass.csv`. **Depends on T005**.
- [X] T011c_verify [US1] Verify and checksum `data/raw/seabass.csv`. Update state YAML. **FAIL LOUDLY** if fetch failed or checksum mismatch. **Exit with code 1** and log "ERROR: Checksum mismatch for seabass.csv" to stderr. **Depends on T011c**.
- [ ] T015a [US1] Implement strict quality flag filtering in `code/01_data_ingestion.py` to exclude MODIS pixels with "cloud" (flag=1) or "high aerosol" (flag=2) flags (per spec Edge Cases) from the fetched data (T011b_verify). **Output**: Write filtered MODIS data to `data/processed/modis_filtered.nc`. **Depends on T011b_verify**.
- [ ] T015b [US1] **Create In-Situ Mask**: Read the content of `data/raw/seabass.csv` (from T011c_verify) to perform a spatial join between the MODIS/Reanalysis grid and SeaBASS points. Generate an `in_situ_validity_mask.nc` file at `data/processed/in_situ_mask.nc` which marks grid cells as valid/invalid based on in-situ data presence. **Output**: Write the mask to `data/processed/in_situ_mask.nc`. **Depends on T011c_verify, T015a**.
- [ ] T012 [US1] Implement spatial/temporal alignment in `code/02_preprocessing.py` (grid reanalysis and MODIS to a coarser resolution, create monthly composites). **Depends on T015b, T009a**.
- [ ] T012a [US1] Implement linear interpolation for gaps ≤ 2 months and **quantify interpolation error** in `code/02_preprocessing.py`. **Metric**: Calculate RMSE between interpolated values and a **temporal hold-out set** (mask the last 2 months of each continuous time series segment before interpolation). Log summary metrics to `data/logs/interpolation_error_summary.json`. **Depends on T012**.
- [ ] T012b [US1] Implement logic to flag gaps > 2 months for EXCLUSION (not imputation) in `code/02_preprocessing.py`. Update dataset mask. **Depends on T012a**.
- [ ] T012c [US1] **Unified Masking**: Implement logic to **apply the unified mask** (from `data/processed/in_situ_mask.nc` generated in T015b and exclusion flags from T012b) to grid cells in the aligned dataset. **Output**: Write the cleaned dataset to `data/processed/aligned_intermediate.nc`. **Depends on T012b, T015b**.
- [ ] T013a [US1] Validate ≥10-year temporal overlap in `code/02_preprocessing.py` on the **aligned** dataset (output of T012). **Logic**: Dynamically check if `max(timestamp) - min(timestamp) >= 10 years` regardless of start year. Implement stratified train/val/test split logic by ocean basin, outputting split indices to `data/processed/split_indices.json`. **Depends on T012, T015b**.
- [ ] T013 [US1] Implement basin stratification and unified masking in `code/02_preprocessing.py` (retain basin ID, apply unified missing data mask across all sources). **Input**: Read from `data/processed/aligned_intermediate.nc` (output of T012c). **Note**: Exclusion of missing in-situ data is already handled in T015b/T012c; T013 only applies the final unified mask and stratification. **Depends on T012c, T009a**.
- [ ] T013b [US1] Implement memory enforcement and logging in `code/02_preprocessing.py` to monitor RAM usage and enforce GB limit, logging to `data/logs/memory_enforcement.log`. **Depends on T013**.
- [ ] T017 [US1] Generate final aligned dataset artifact in `data/processed/aligned_dataset.nc` (verify no missing values due to misalignment). **Depends on T013b, T009a**.
- [ ] T017a [US1] Calculate missing value percentage in `code/02_preprocessing.py` and verify SC-004 compliance (≤5% missing). **Verify SC-004 compliance: if missing_value_pct > 5.0, raise an exception and halt the pipeline**. Log result to `data/logs/missing_value_report.json`. **Depends on T017**.

---

## Phase 4: User Story 2 - Baseline and VLM Model Training (Priority: P2)

**Goal**: Train and evaluate a Random Forest baseline and a lightweight CLIP-based VLM (<500M params) on CPU.

**Independent Test**: Execute training script; verify RF completes <2h, VLM completes <4h with early stopping if needed, and output metrics (RMSE, R², MAE) for both.

### Tests for User Story 2 ⚠️

- [X] T032 [P] [US2] Contract test for model metrics schema in `tests/contract/test_schemas.py` (validates model_performance.schema.yaml)
- [X] T039 [P] [US2] Integration test for CPU feasibility in `tests/integration/test_pipeline.py` (verifies runtime <6h and RAM <7GB for full training)

### Implementation for User Story 2

- [X] T018 [US2] Implement Random RF baseline in `code/03_model_training.py` (≤500 trees, scikit-learn, CPU-only, train/val split). **Depends on T017 (US1)**.
- [ ] T019 [US2] Implement lightweight CLIP-based VLM fine-tuning in `code/03_model_training.py` (concatenated image/text inputs). **Model**: `facebook/clip-vit-base-patch32` (approx 150M params) with text encoder. **Prompt**: "Temperature: {temp}, Salinity: {sal}, Nutrients: {nut}". **Logic**: CPU-only. **CRITICAL**: If standard loading fails due to OOM, **DO NOT** attempt 8-bit quantization. Instead, retry ONCE with **`facebook/clip-vit-tiny`** (approx 28M params) and **`batch_size=4`**. If this specific fallback also fails, set `vlm_fallback=True` in `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml`, log "VLM Failed (Baseline Used)", and **DO NOT** proceed with VLM evaluation. **Output**: Always produce a model artifact or a fallback flag. **Depends on T017**.
- [ ] T020_pred [US2] Generate test set predictions artifact in `data/processed/predictions_test.csv`. **Logic**: Run both RF (T018) and VLM (T019, if successful). If `vlm_fallback` flag is set (read from state YAML), generate predictions only from RF and mark VLM column as "N/A". **Depends on T018, T019**.
- [X] T020 [US2] Generate model performance artifact in `data/artifacts/model_comparison.csv` (includes basin-stratified R² scores, RMSE, MAE for both RF and VLM). **Handle VLM Failure**: This task MUST read the `vlm_fallback` flag from `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` produced by T019. If the flag is set, the artifact MUST still be generated with RF metrics and the VLM column explicitly marked as "N/A (Failed)". **Depends on T018, T020_pred**.
- [ ] T019a [US2] Perform statistical significance test in `code/04_evaluation.py` to validate if VLM R² exceeds baseline by ≥0.05. **Logic**: Perform an **appropriate statistical test** (paired t-test if data is normal, otherwise Wilcoxon signed-rank test) using the confidence level (alpha) from `config.py`. **CRITICAL**: Do not hardcode a p-value threshold. Calculate and report the raw p-value and the test statistic. If `vlm_fallback` flag is set (read from state YAML), execute the logic to record `p_value = "N/A"` and `status = "VLM Failed to Exceed Baseline"` in `data/artifacts/significance_test.json`. **This result constitutes a failure to meet SC-001**. **Depends on T020**.
- [ ] T020b [US2] **Basin Variance Metric**: Calculate the raw difference between the highest and lowest basin R² scores (max - min) to satisfy SC-005. Output this single metric value to `data/artifacts/basin_r2_difference.json`. **If VLM failed, report RF-only variance or 'N/A'**. **Depends on T020**.
- [ ] T020c [US2] **Optional Statistical Test**: Perform a Kruskal-Wallis H-test to determine if the variance in R² scores across basins is statistically significant (optional, for deeper analysis). **Condition**: Run ONLY if the number of unique basins in the test set is > 3. **If basin count <= 3, SKIP this task and write `data/artifacts/basin_variance_significance.json` with content `{"skipped": true, "reason": "Basin count <= 3"}`**. Output test statistic and p-value to `data/artifacts/basin_variance_significance.json` if run. **Depends on T020b**.
- [ ] T020a [US2] **Basin Variance Report**: Generate a report and visualization of the variance in R² scores across basins (using the metric from T020b) as required by SC-005. **Output**: Write report to `data/artifacts/basin_variance_report.md` and visualization to `data/artifacts/basin_variance_viz.png`. **If VLM failed, report RF-only variance or 'N/A'**. **Depends on T020b**.

---

## Phase 5: User Story 3 - Feature Importance and Driver Quantification (Priority: P3)

**Goal**: Quantify driver contributions using permutation importance and generate spatial visualization maps.

**Independent Test**: Run feature importance analysis; verify output includes ranked driver list (sum=1.0) and spatial maps (GeoTIFF/PNG) for each basin.

### Tests for User Story 3 ⚠️

- [X] T021 [P] [US3] Contract test for feature importance output in `tests/contract/test_schemas.py` (validates The importance scores sum to unity within a small tolerance.).
- [X] T022 [P] [US3] Integration test for visualization generation in `tests/integration/test_pipeline.py` (verifies map files are generated correctly)

### Implementation for User Story 3

- [ ] T023 [US3] Implement permutation importance analysis in `code/04_evaluation.py` (rank drivers, normalize scores to sum=1.0 using L1 norm, verify sum equals unity within a specified tolerance). **CRITICAL**: **Check `vlm_fallback` flag first**. If set, skip VLM-specific importance analysis and instead perform analysis on the RF baseline (T018), logging "Analysis performed on Baseline (VLM Failed)". **Multicollinearity**: Handle multicollinearity using `statsmodels.stats.outliers_influence.variance_inflation_factor`. If VIF > 5 for any feature, log a "WARNING: High Multicollinearity Detected" and set `high_multicollinearity: true` in the output artifact, but proceed without PCA. **Validation Gate**: Calculate the sum of importance scores. **If the sum does not equal a normalized value (within tolerance), raise an exception and halt the pipeline**. Write a `validation_status` field ('PASS'/'FAIL') to `data/artifacts/feature_importance.json` based on whether the sum of importance scores is within tolerance of 1.0. **Depends on T018, T020_pred**.
- [X] T025 [US3] Implement in-situ correlation analysis in `code/04_evaluation.py` (calculate correlation coefficient r between predictions and in-situ measurements per basin). **Input**: Read predictions from `data/processed/predictions_test.csv` (produced by T020_pred). **Depends on T020_pred, T017, T011c_verify**.
- [ ] T026 [US3] Generate final driver attribution artifacts in `data/artifacts/feature_importance_maps/` (include legend and basin labels). Implement spatial aggregation logic to ensure maps are at the same resolution as the aligned dataset, handling necessary resampling without introducing artifacts. **Depends on T023, T025**.
- [X] T024 [US3] Implement spatial visualization generation in `code/04_evaluation.py` (create GeoTIFF/PNG maps of top driver importance per basin). **Depends on T023**.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T050 [P] [Orchestration] Implement End-to-End Pipeline Orchestration in `code/06_pipeline_orchestrator.py` to measure total runtime from T011a to T026, enforce **hard time limit** using `try/except` block catching `subprocess.TimeoutExpired` (cross-platform) and **GB RAM limit**. If limits exceeded, **check `state/projects/...yaml` for `vlm_fallback` flag**; if present, allow pipeline to continue with baseline results; otherwise, **FAIL/STOP immediately** (do not continue). Aggregate memory logs from T013b and T018. Output `data/logs/pipeline_summary.json`. **Depends on T026**.
- [X] T041 [P] Update `quickstart.md` with execution instructions for the full pipeline, including specific commands (`python code/06_pipeline_orchestrator.py`), environment variables (`MEMORY_LIMIT_GB`, `RUNTIME_LIMIT_HOURS`, `NOAA_API_KEY`), and expected runtime outputs (summary JSON).
- [X] T028 Code cleanup and refactoring in `code/` (remove debug prints, optimize memory usage)
- [X] T029 [P] Run full integration test suite and verify all acceptance scenarios pass
- [X] T030 [P] Update `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` with final artifact hashes
- [X] T031 [P] Validate `research.md` and `data-model.md` against generated artifacts

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Ingestion before preprocessing
- Preprocessing before training
- Training before evaluation
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
Task: "Contract test for schema validation in tests/contract/test_schemas.py"
Task: "Integration test for data alignment in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement SeaBASS data ingestion in code/01_data_ingestion.py"
Task: "Implement spatial/temporal alignment in code/02_preprocessing.py"
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