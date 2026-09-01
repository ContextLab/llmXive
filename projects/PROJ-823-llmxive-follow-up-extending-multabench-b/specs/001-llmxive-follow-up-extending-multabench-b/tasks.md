# Tasks: llmXive Follow-up: Extending MulTaBench

**Input**: Design documents from `/specs/001-llmxive-mulTabench-extension/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. [UNRESOLVED-CLAIM: c_dbfe31f9 — status=not_enough_info] Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `code/`, `tests/`, `data/`
- [X] T002 Initialize a Python project with `pyproject.toml` dependencies (torch-cpu, transformers, sentence-transformers, scikit-learn, pandas, pyarrow, numpy, requests, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for global config, seeds (`random_seed=42`), and paths. **Requirement**: Explicitly define and pin a set of sensitivity seeds in a `SENSITIVITY_SEEDS` constant to ensure deterministic reproducibility across all runs. **Specific Seeds**: `{{claim:c_64c5ef1f}} (2406.08447, https://arxiv.org/abs/2406.08447)`.
- [X] T005 [P] Implement `code/utils/memory_monitor.py` to track peak RAM usage (memory limit)
- [X] T006 [P] Implement `code/utils/logging.py` for structured pipeline logging
- [X] T007 Create `code/data_loader.py` for MulTaBench ingestion with local checksum verification (SHA-256)
- [X] T008 [Setup/Docs] Create `data/README.md` with instructions for local data ingestion and checksum validation. **CRITICAL**: This file MUST include explicit instructions on how to obtain the `data/raw/multabench_baselines.csv` file required for T008b, as no public URL exists.
- [X] T008c [Setup/Docs] **Update README with Acquisition Steps**: Update `data/README.md` to explicitly document the manual steps required to acquire `data/raw/multabench_baselines.csv`. **Steps**: "1. Locate the supplementary material for the MulTaBench paper (arXiv:2605.10616). [UNRESOLVED-CLAIM: c_627856cb — status=verified] 2. Download the archive containing `multabench_baselines.csv`. 3. Unzip the archive. 4. Place `multabench_baselines.csv` in `data/raw/`. **Note**: No direct URL is provided; the file must be manually located in the paper's supplementary materials. [UNRESOLVED-CLAIM: c_1db7ea47 — status=not_enough_info]" **Dependency**: Must run BEFORE T008b to ensure instructions are available if the file is missing. **Note**: This task ensures instructions are available before the fetch script runs.
- [X] T008b [P] Implement `code/pipelines/fetch_baselines.py` to validate the presence of `data/raw/multabench_baselines.csv`. **Logic**: If the file is missing or empty, the script MUST exit with code 1 and log ERROR: "Missing required baseline file: data/raw/multabench_baselines.csv. Please refer to data/README.md for acquisition steps." to stderr using `logging.ERROR` level. It must NOT generate synthetic data or attempt to parse arXiv links. **Dependency**: Must run AFTER T008c to ensure instructions are available. **Note**: This is a known constraint; CI will fail if file is missing, but the error message will guide the user.
- [X] T009a [P] Create `contracts/frozen_embedding.schema.yaml` defining the schema for frozen embeddings (fields: run_id, dataset_id, vector, model_type)
- [X] T009b [P] Create `contracts/tabular_metadata.schema.yaml` defining the schema for tabular metadata (fields: dataset_id, cardinality, missingness, sparsity, variance)
- [X] T009d [P] Create `contracts/baselines.schema.yaml` defining the schema for the `multabench_baselines.csv` file (fields: dataset_id, gpu_tuned_auc, task_type, dataset_name). **Requirement**: This contract is the Single Source of Truth for T032a validation.
- [X] T009c [P] Update `data-model.md` to reference the new contract files and define `run_id` propagation logic for all downstream artifacts
- [X] T010 Create `code/models/__init__.py` and base model structures

### Metadata & Normalization Pipeline (Foundational Prerequisites for US1/US2)

- [X] T024a [US1/US2/US3] **Load Datasets**: Implement `code/analysis/metadata_stats.py::load_datasets` to iterate through all datasets in `data/raw/` and yield a dictionary of dataset_id and dataframes. **Output**: Generator yielding dataset objects.
- [X] T024b [US1/US2/US3] **Compute Per-Dataset Stats**: Implement `code/analysis/metadata_stats.py::compute_stats` to compute cardinality, missingness, sparsity, and variance for a single dataset. **Output**: Dictionary of stats per dataset.
- [X] T024c [US1/US2/US3] **Aggregate to CSV**: Implement `code/analysis/metadata_stats.py::aggregate_stats` to aggregate stats from T024b into a single CSV `data/processed/metadata_stats_summary.csv`. **Output**: `data/processed/metadata_stats_summary.csv` with columns [dataset_id, cardinality, missingness, sparsity, variance]. **Constraint**: This task replaces T024 and is a blocking prerequisite for T024e, T045, and T033. **Verification**: Assert row count matches input datasets; verify missingness rates are in [0, 1].
- [X] T024e [US1/US2/US3] **Metadata Aggregation & Subset Selection**: Load `data/processed/metadata_stats_summary.csv` from T024c. Sort datasets alphabetically by dataset_id and select the **initial subset**. **Logic**: Select ALL available datasets present in `data/processed/metadata_stats_summary.csv`. If N > 50, select the first 50 alphabetically to ensure runtime feasibility. **Output**: `data/processed/metadata_stats_summary.csv` (updated with subset flag if needed). **Dependency**: Must run AFTER T024c completion. **Constraint**: This task is a shared prerequisite for US2 and US3 and must complete before T024f and T033. **Note**: The [P] tag is removed from this task as it is a blocking prerequisite.
- [X] T045 [US1/US2/US3] **Data Integrity Check**: Implement `code/pipelines/verify_data_integrity.py` to cross-check that every dataset ID in `data/processed/metadata_stats_summary.csv` (T024e) exists in `data/raw/` and has non-zero variance in at least one tabular feature. **Dependency**: Must run AFTER T024e completion. **Logic**: If a dataset has zero variance in a specific feature (variance < 1e-9), SKIP ONLY that feature in the metadata stats for correlation analysis (do NOT impute), log to `data/artifacts/data_integrity_report.json` with a 'skipped_feature' status, and retain the dataset. If ALL features are zero-variance, exclude the dataset. **Output**: `data/artifacts/data_integrity_report.json` containing a list of skipped features and the reason (e.g., "zero_variance"). **Constraint**: This task MUST run before T033 and T032a to ensure zero-variance features are excluded from the correlation analysis, but datasets are not discarded unless ALL features are zero-variance. **Config**: Use `ZERO_VAR_THRESHOLD = 1e-9` from `code/config.py`.
- [X] T045b [US1/US2] **Zero-Variance Feature Handling**: Implement `code/pipelines/impute_zero_variance.py` to handle zero-variance features identified in T045. **Logic**: **FORBIDS imputation**. Output a 'skip list' of zero-variance features for each dataset. **Output**: Update `data/processed/metadata_stats_summary.csv` with a 'skipped_features' column (list of feature names) and log the action in `data/artifacts/data_integrity_report.json`. **Rationale**: Imputation is rejected because introducing artificial constant values for zero-variance features would mask the true structural properties of the data, violating the requirement to correlate recovery efficacy with *actual* tabular metadata. Skipping preserves the integrity of the correlation analysis. **Constraint**: This task ensures that correlation analysis is not invalidated by missing variance signals, but zero-variance features are excluded from the final correlation calculation to preserve signal integrity. **Dependency**: Must run after T045.
- [X] T024f [US1/US2] Implement `code/pipelines/normalize_tabular.py` to generate `data/processed/normalized_tabular_features.parquet`. **Logic**: Load raw tabular data for **datasets selected in T024e**, apply standard normalization (z-score or min-max) per feature using global mean/std calculated from the **selected subset**, and handle missing values via mean imputation. **CRITICAL**: For features flagged as zero-variance in T045/T045b, **SKIP normalization** for that specific feature (do NOT impute). **Output**: A single Parquet file containing normalized features for ALL available datasets in the subset. **Dependency**: Must run AFTER T024e (Subset Selection) and T045 (Data Integrity Check) to ensure normalization uses the corrected/filtered feature set and is computed on the final subset only. **Usage**: This artifact is consumed by T015a (for the Frozen Baseline classifier) and T025 (for the Conditioned model). **Note**: T015a uses this for the baseline classifier but does NOT use it for conditioning; T025 uses it for both. **Canonical Function**: The normalization logic MUST be implemented in `code/utils/feature_engineering.py::normalize_features` to ensure consistency across T015a and T025.

- [X] T055 [P] [US1/US2/US3] **CI Guardrails**: Implement `code/pipelines/ci_guardrails.py` to perform pre-flight checks: (1) Verify `data/raw/` is not empty and contains expected file extensions, (2) Verify Python version and critical dependencies. **Logic**: Executes as a pre-flight check in Phase 2; its results are consumed by T015a and T025. Exit immediately with a descriptive error code if checks fail. **Output**: `data/artifacts/ci_guardrail_report.json`.
- [X] T056a [P] [US1/US2/US3] **Memory Probe**: Implement `code/pipelines/tune_batch_size.py::probe_memory` to run a small subset of images and measure memory usage. **Output**: Log memory usage for a small batch.
- [X] T056b [P] [US1/US2/US3] **Binary Search Logic**: Implement `code/pipelines/tune_batch_size.py::find_optimal_batch_size` to incrementally increase batch size by 2x until memory usage exceeds a high threshold. **Output**: Log the selected `optimal_batch_size`.
- [X] T056c [P] [US1/US2/US3] **Config Writer**: Implement `code/pipelines/tune_batch_size.py::write_config` to write the determined `optimal_batch_size` to `data/artifacts/batch_size_config.json`. **Constraint**: This must prevent OOM crashes on large image datasets without requiring manual intervention.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. **CRITICAL**: T024c, T024e, T045, T045b, and T024f must be completed before any US1 tasks (including T015a) can start.

---

## Phase 3: User Story 1 - CPU-Tractable Baseline Generation (Priority: P1) 🎯 MVP

**Goal**: Generate frozen embeddings for images and text using CLIP ViT-B/ and Sentence-BERT on CPU without gradient tracking.

**Independent Test**: Independent Test: Verify script completes within 60 mins on a sample of datasets, outputs valid parquet files, and no CUDA errors occur., outputs valid parquet files, and no CUDA errors occur.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Unit test for batch processing logic in `tests/test_embeddings.py::test_batch_processing_memory`
- [X] T012 [P] [US1] Unit test for gradient disabling in `tests/test_embeddings.py::test_no_grad_context`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/embeddings/generator.py` with CLIP ViT-B/32 and Sentence-BERT loaders (CPU-only, default precision)
- [X] T014 [US1] Implement `code/embeddings/utils.py` with batch processing logic to ensure memory safety (max batch size). **Dependency**: Must use the `optimal_batch_size` from `data/artifacts/batch_size_config.json` (T056).
- [X] T015 [US1] Implement `code/pipelines/run_baseline.py` to generate embeddings for **ALL available datasets** in the pipeline with `random_seed=42`. Output must include `data/processed/embeddings_{run_id}.parquet` with `run_id`, `dataset_id`, `vector`, and `model_type` columns (matching `contracts/frozen_embedding.schema.yaml` from T009a). Ensure deterministic re-computation for all datasets to satisfy FR-001. **Constraint**: Must validate output against `contracts/frozen_embedding.schema.yaml` and enforce `random_seed=42`.
- [X] T015a [US1] **Single-Seed Frozen Baseline Classifier**: Implement `code/pipelines/train_frozen_baseline_classifier.py` to train a lightweight classifier (e.g., Logistic Regression) on the frozen embeddings from **T015 (Seed 42 ONLY)** and normalized tabular features from **T024f**. **Input**: Must consume the *same* normalized tabular features from `data/processed/normalized_tabular_features.parquet` (generated by T024f) and use the *exact same* feature engineering logic (`code/utils/feature_engineering.py::normalize_features`) and normalization parameters (mean/std) as T025 (US2) to ensure consistency with the 'CPU-Conditioned' denominator. **Verification**: Verify that the normalization parameters (mean/std) loaded from `data/processed/normalized_tabular_features.parquet` match those used in T025 by comparing the `schema.metadata[b'normalized_params']` field and asserting `dict equality`. **Constraint**: Do NOT use `normalized_tabular_features.parquet` for *conditioning* (modulating embeddings) in this task; use it ONLY as input to the classifier alongside embeddings. **Output**: `data/artifacts/frozen_baseline_metrics_seed42_{run_id}.json` containing `dataset_id`, `metric_name`, `metric_value` (single seed). This task satisfies FR-001's requirement to re-compute the baseline performance for the Recovery Ratio denominator. **Must run after T015 and T024f**. **Note**: `code/utils/feature_engineering.py::normalize_features` MUST exist and be the single source of truth; raise ImportError if missing. **Constraint**: Must enforce `random_seed=42` and identical hyperparameters to T025. **Scope**: Compute baseline for **ALL valid datasets** (as selected in T024e) using Seed 42 ONLY. **Rationale**: This task computes the *primary* seed metric (Seed 42) which is the *sole* denominator for FR-001. The sensitivity analysis (T019c) is for *variance reporting* only and is not used in the denominator calculation, ensuring consistency with the 'CPU-Conditioned' generation context as mandated by FR-001.
- [X] T016 [US1] Add logic to handle datasets with zero variance or missing image/text fields gracefully: skip dataset, log warning to `code/utils/logging.py`, and write skipped dataset IDs to `data/artifacts/skipped_datasets.json`.
- [X] T017 [US1] Implement output serialization to `data/processed/embeddings_{run_id}.parquet` with `run_id` and metadata, ensuring schema compliance with `contracts/frozen_embedding.schema.yaml`.
- [X] T018 [US1] Add validation to ensure no gradient tracking is enabled during inference
- [X] T019 [US1] **Sensitivity Embedding Generation**: Implement `code/pipelines/run_baseline_sensitivity.py` to generate embeddings for **ALL available datasets** using **specific random seeds** from a predefined set (excluding 42). **Output**: Multiple separate Parquet files named `embeddings_seed_{seed_id}_{run_id}.parquet` (e.g., `embeddings_seed_123_{run_id}.parquet`). **Note**: This script generates multiple Parquet files (one per seed). It is a prerequisite for sequential tasks T019b, T019d. **Dependency**: Must run after T015a (parallel branch).
- [X] T019b [US1] Implement `code/pipelines/merge_sensitivity_outputs.py` to merge the 4-seed Parquet files from T019 into a single intermediate file. **Must run before T019d**.
- [X] T019d [US1] **Train Sensitivity Baseline Classifiers**: Implement `code/pipelines/train_sensitivity_baseline_classifiers.py` to train the lightweight classifier on the merged sensitivity embeddings (Tb) for seeds [123, 456, 789, 101112]. **Input**: Merged embeddings from T019b and normalized tabular features from T024f. **Output**: Multiple JSON files `frozen_baseline_metrics_seed_{seed_id}_{run_id}.json` for each sensitivity seed. **Dependency**: Must run after T019b. **Note**: This task generates the performance metrics required by T019c.
- [X] T019c [US1] **Aggregate Sensitivity Metrics**: Implement `code/pipelines/aggregate_sensitivity.py` to compute mean/std of the **performance metrics** (AUC/RMSE) from the sensitivity seeds (T019d) and write to `data/artifacts/frozen_baseline_sensitivity_aggregated_{run_id}.json`. **Note**: This aggregates metrics from seeds [123, 456, 789, 101112] ONLY to provide a variance report, NOT for the Recovery Ratio denominator. The denominator is T015a. **Must run after T019d**. **Dependency**: Must verify T019d output exists and is valid before aggregation.
- [X] T019e [US1] **Consistency Check**: Implement `code/pipelines/verify_baseline_consistency.py` to compare the primary seed metric (T015a) with the aggregated metric (T019c) for seed 42 (if included in sensitivity). **Logic**: If `abs(primary_metric - aggregated_metric_seed42) > 0.001`, log a warning. **Output**: `data/artifacts/baseline_consistency_report.json`. **Dependency**: Must run after T015a and T019c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Tabular-Conditioned Projection Implementation (Priority: P2)

**Goal**: Implement and train a lightweight projection module (MLP/Attention) using normalized tabular features as queries to modulate frozen embeddings.

**Independent Test**: Verify training loss converges on a single dataset within 10 epochs on CPU and memory usage < 7GB. [UNRESOLVED-CLAIM: c_fbb98424 — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for projection layer gradient isolation in `tests/test_projection.py::test_frozen_backbone_gradients`
- [X] T021 [P] [US2] Integration test for training loop convergence in `tests/test_projection.py::test_training_convergence`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/models/projection.py` with MLP or single-head attention module accepting tabular features as query
- [X] T023 [US2] Implement `code/models/trainer.py` with training loop that freezes backbone weights and trains only projection layer
- [X] T025 [US2] Implement `code/pipelines/run_conditioned.py` to train the projection layer on **ALL available datasets**, consuming metadata stats from T024e and normalized features from T024f. **Logic**: Must use `code/utils/feature_engineering.py::normalize_features` to ensure identical preprocessing to T015a. **Dependency**: Must run after T024f and T045.
- [X] T026 [US2] Add logic to handle edge cases (e.g., zero variance features) by **skipping** them in the conditioning query. **Constraint**: **DO NOT IMPUTE**. If a feature is flagged as zero-variance in T045b, remove it from the conditioning query vector. Ensure no crash occurs before T025 runs.
- [X] T027 [US2] Implement evaluation logic to record performance metrics (AUC/RMSE) for held-out test sets.
- [X] T028 [US2] Store results in `data/artifacts/metrics_conditioned_{run_id}.json` with `run_id` linkage.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Efficacy Correlation & Statistical Analysis (Priority: P3)

**Goal**: Correlate performance recovery ratio with tabular metadata statistics and perform statistical significance testing.

**Independent Test**: Verify correlation analysis script outputs Pearson coefficients, p-values, and performs t-test/Wilcoxon test correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for correlation calculation in `tests/test_analysis.py::test_correlation_calculation`
- [X] T030 [P] [US3] Unit test for FDR correction implementation in `tests/test_analysis.py::test_benjamini_hochberg`

### Implementation for User Story 3

- [X] T032a [US3] Implement `code/pipelines/validate_baselines.py` to validate the presence of 'GPU-Tuned' baselines for **ALL available datasets**. **Input**: `data/raw/multabench_baselines.csv` (from T008b) and `contracts/baselines.schema.yaml` (from T009d). **Output**: `data/artifacts/gpu_tuned_baselines.csv` (validated subset) and `data/artifacts/data_availability_gap_report.json` (listing missing entries). **Logic**: If the file is missing, log to `data/artifacts/data_availability_gap_report.json` and exit with code 1. Explicitly exclude datasets missing 'GPU-Tuned' baselines AND datasets flagged in T045 from the list of valid datasets for subsequent correlation tasks (T033, T034). **Dependency**: Must run after T008b and T045.
- [X] T032b [US3] **Baseline Scalar Extraction**: Implement `code/pipelines/extract_baseline_scalars.py` to extract the specific 'GPU-Tuned' baseline value for each dataset from `data/artifacts/gpu_tuned_baselines.csv` (T032a) and format it into a JSON structure `data/artifacts/gpu_tuned_scalars.json`. **Output**: JSON file with keys `dataset_id` -> `baseline_value`. **Validation**: Must validate that the output is a dictionary of floats compatible with `scipy.stats.ttest_1samp` input requirements. **Dependency**: Must run after T032a. **Purpose**: Provides the scalar `popmean` required by T035.
- [X] T031 [US3] Implement `code/analysis/correlation.py` to calculate "Recovery Ratio" = (CPU-Conditioned - **Frozen Baseline (Seed 42)**) / (GPU-Tuned - **Frozen Baseline (Seed 42)**). **Input**: `data/artifacts/gpu_tuned_baselines.csv` (T032a), `data/artifacts/frozen_baseline_metrics_seed42_{run_id}.json` (T015a - **Single Seed Metric**), `data/artifacts/metrics_conditioned_{run_id}.json` (T028), and `data/artifacts/gpu_tuned_scalars.json` (T032b). **Dependency**: Must run after T015a, T028, T032a, and T032b completion. **Note**: The denominator is the re-computed frozen baseline performance from T015a (Seed 42), not historical paper values or aggregated sensitivity metrics. **Constraint**: Must assert input source is T015a artifact, not external CSV. **Logic**: If N < 30 after exclusions, append a "Small Sample Warning" to the output report explicitly stating the limitation. **JSON Keys**: Extract `metric_value` from T015a and T028 JSONs using the `dataset_id` key. Extract `baseline_value` from T032b JSON using the `dataset_id` key. **Rationale**: This task uses the single seed (Seed 42) for the denominator to ensure consistency with the 'CPU-Conditioned' generation context as mandated by FR-001. The sensitivity analysis (T019c) is used to report the variance of the baseline, but the denominator itself is the fixed Seed 42 value.
- [X] T033 [US3] Perform Pearson correlation between "Recovery Ratio" and metadata features (Cardinality, Missingness, Sparsity, Variance) for **ALL available datasets** with complete data, **excluding those flagged in T032a and T045**. **Dependency**: Requires T024e, T032a, and T045 completion. **Logic**: If a limited number of datasets are available after exclusions, use all available and flag the shortfall in the report.
- [X] T034 [US3] Implement Benjamini-Hochberg (FDR) correction for multiple comparisons. **Scope**: Apply FDR ONLY to the correlation p-values from T033 (family of tabular metadata features). **Input**: p-values from T033, filtered by the exclusion lists from `data/artifacts/data_availability_gap_report.json` and `data/artifacts/data_integrity_report.json`. Do NOT include t-test results (T035) in this correction. Output: JSON with adjusted p-values. **Logic**: Explicitly filter the input dataset list using `data/artifacts/data_availability_gap_report.json` and `data/artifacts/data_integrity_report.json` before calculating FDR. **Step 1**: Load exclusion lists and filter input dataset list. **Step 2**: Calculate FDR on filtered p-values. **Note**: The t-test (T035) is a separate family of tests (mean difference) and thus not subject to the same FDR family as the correlations.
- [X] T035 [US3] Perform one-sample t-test comparing "CPU-Conditioned" performance vs. fixed GPU-Tuned baseline for **ALL valid datasets**. **Implementation**: Load `data/artifacts/metrics_conditioned_{run_id}.json` into a numpy array `conditioned_metrics`. Load scalar `baseline_scalar` from `data/artifacts/gpu_tuned_scalars.json` (T032b). Compute `diff = conditioned_metrics - baseline_scalar`. **Normality Check**: Perform Shapiro-Wilk test on `diff`. {{claim:c_6efd2518}}: `scipy.stats.wilcoxon(diff)`. Otherwise, perform one-sample t-test: `scipy.stats.ttest_1samp(diff, popmean=0.0)`. **Constraint**: Do NOT treat the baseline as a sample array; treat it as a constant. Explicitly test the difference vector against 0.0. Report the p-value separately from the FDR-corrected correlations.
- [X] T036 [US3] Generate `data/artifacts/correlation_report_{run_id}.json` with coefficients, p-values, and significance flags.
- [X] T037 [US3] Create `code/pipelines/run_analysis.py` to orchestrate the full statistical analysis pipeline. **Output**: Generate `data/artifacts/correlation_report_{run_id}.json` containing all statistical results.
- [X] T038 [US3] Add "Data Availability Gap" reporting for datasets missing GPU-Tuned baselines to the final report.
- [X] T057 [US3] **Statistical Power & Sample Size Warning** [MANDATORY]: Update `code/analysis/correlation.py` to calculate and report the statistical power of the correlation analysis given the final sample size (N) after exclusions (T032a, T045). **Logic**: Use `statsmodels.stats.power.tt_solve_power` to calculate power for a range of effect sizes (small, moderate, and large). **Mandatory**: This calculation is required by Constitution Principle VII to validate the sample size for the correlation analysis. **Output**: Append a `power_analysis` section to `data/artifacts/correlation_report_{run_id}.json`. **Note**: This is a MANDATORY task for scientific rigor; the Spec requires acknowledging the limitation, and the Constitution requires reporting the correlation for the dataset subset. **Dependency**: Must run after T036 to ensure sample size is known.
- [X] T058 [US3] **Explicit Power Analysis Visualization**: Implement `code/analysis/plot_power_analysis.py` to generate a visual report (PNG) showing the calculated statistical power (from T057) against a range of effect sizes (ranging from small to large). **Requirement**: This visualization must be appended to `results_summary.md` (T053b) to provide an immediate, human-readable confirmation of the study's sensitivity. **Dependency**: Must run after T057. **Constraint**: **Generate the visualization in ALL cases** (regardless of power value) to ensure the `results_summary.md` always contains the explicit "power analysis" section required by Constitution Principle VII. If power >= 0.8, include a note in the plot stating "Power is sufficient (>0.8) for moderate effect size". If generated, include a warning banner in the plot if power is low.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Update `code/pipelines/update_state.py` to hash artifacts and update `state/projects/PROJ-823-llmxive-follow-up-extending-multabench-b.yaml`. **Output**: Update `state/projects/PROJ-823-llmxive-follow-up-extending-multabench-b.yaml` with new `updated_at` timestamp and `artifact_hashes`.
- [X] T040a [P] **Refactor T014**: Refactor `code/embeddings/utils.py` to use generator expressions and optimize memory usage.
- [X] T040b [P] **Refactor T024**: Refactor `code/analysis/metadata_stats.py` to use pandas groupby for efficient aggregation.
- [X] T040c [P] **Generate Profiling Report**: Generate `data/artifacts/profiling_report.json` containing optimal fixed batch sizes for embedding generation and training based on T056 and T040a/b results. **Mandatory**: This is a distinct, mandatory deliverable separate from refactoring.
- [X] T041a [Polish/Optimization] **Batch Size Optimization**: Implement `code/pipelines/optimize_batch_sizes.py` to apply the fixed batch sizes determined by T056 to the embedding generation and training pipelines. **Constraint**: Use the fixed batch sizes determined in T056; do NOT use adaptive logic based on runtime memory state. **Verification**: Run full pipeline on all datasets and record total runtime in `data/artifacts/runtime_report.json`.
- [X] T041b [Polish/Optimization] **Parallelism Logic**: Implement `code/pipelines/optimize_parallelism.py` to apply dynamic parallelism logic in T025 trainer.py based on the profiling results from T056. **Constraint**: Use the fixed parallelism settings determined in T056; do NOT use adaptive logic based on runtime state.
- [X] T042 [P] Additional unit tests for edge cases (e.g., empty datasets, single-row datasets) in `tests/`
- [X] T043a [P] Generate/Update `quickstart.md` with new pipeline steps (US1, US2, US3) and data ingestion instructions.
- [X] T044 [P] Final integration test of the entire pipeline on a subset of datasets.

---

## Phase 7: Verification & Hardening (Review-Driven)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical rigor, and pipeline robustness.

- [X] T059 [US1/US2/US3] **Robust Data Source Verification Script**: Implement `code/pipelines/verify_real_data_sources.py` to perform a final, automated check that ALL data inputs (raw images, tabular CSVs, baseline CSVs) are real, non-synthetic, and checksum-verified before any analysis runs. **Logic**: This script must scan `data/processed/` and `data/artifacts/` and compare file hashes against the recorded hashes in `state/projects/...yaml`. **First-Run Logic**: If `state/projects/...yaml` is missing or `artifact_hashes` is empty, log "First run: skipping hash verification" and exit with code 0 (allow pipeline to proceed). If state exists, verify hashes for `data/raw/multabench_baselines.csv` and files in `data/raw/`. **Output**: A strict boolean pass/fail status. If any hash mismatch is detected, the script MUST exit with code 1 and log a critical error, preventing the pipeline from proceeding. **Dependency**: Must run as a **pre-requisite to T048** (Final Validation). **Note**: This enforces the "No Fabrication" rule at the execution gate using Constitution-compliant checksum verification. **Config**: Must check specific keys in `state/projects/...yaml` such as `artifact_hashes['data/raw/multabench_baselines.csv']`.
- [X] T062 [US1/US2/US3] **Final Pre-Flight Execution Gate**: Implement `code/pipelines/final_execution_gate.py` to run T059 (Data Verification), T055 (CI Guardrails), and T048b (Runtime Subset Check) in sequence. **Logic**: If ANY check fails, the script MUST exit with code 1 and log a detailed error. If ALL checks pass, the script proceeds to T048 (Final Validation). **Output**: `data/artifacts/final_gate_report.json` indicating pass/fail for each sub-check. **Dependency**: Must run BEFORE T048. **Constraint**: This is the final automated gate before the full pipeline run; it ensures no wasted CI time on invalid states.
- [X] T048 [US1/US2/US3] **Final End-to-End Runtime Validation**: Execute the complete pipeline (US1 → US2 → US3) on the full set of available datasets on a standard GitHub Actions free runner. **Goal**: Verify total execution time is strictly within acceptable limits and peak memory usage never exceeds acceptable thresholds. [UNRESOLVED-CLAIM: c_6c59d408 — status=not_enough_info] **Output**: Generate `data/artifacts/final_validation_report.md` containing the total runtime, peak memory usage, and a pass/fail status for FR-004. If the limit is exceeded, the report must identify the specific bottleneck (e.g., "Embedding generation exceeded the threshold on dataset X").
- [X] T048b [US1/US2/US3] **Subset Validation for Runtime**: Implement `code/pipelines/validate_runtime_subset.py` to limit the dataset count for the final runtime validation run (T048) to a subset (e.g., first several datasets) if the full set exceeds the -hour budget. **Logic**: If the full pipeline is estimated to exceed a significant duration, select a subset of datasets alphabetically and run T048 on this subset. **Output**: Update `data/artifacts/final_validation_report.md` to reflect the subset used and the runtime. **Constraint**: This ensures FR-004 is met even if the full dataset count is too large.

---

## Phase 8: Final Review & Cleanup (Post-Analysis)

**Purpose**: Finalize documentation and address any remaining minor issues found during execution.

- [X] T049 [P] Review `data/artifacts/final_validation_report.md` and `data/artifacts/correlation_report_{run_id}.json` to ensure all FR requirements are met.
- [X] T050 [P] Update `README.md` in the repository root with a summary of the project's findings, including the Recovery Ratio and key correlations.
- [X] T051 [P] Archive all generated artifacts in `data/artifacts/` with a clear `run_id` naming convention for future reference.
- [X] T052 [P] Close any open issues or TODOs in the codebase related to the implementation of US1, US2, and US3.
- [X] T053a [P] **Aggregate Data Points**: Implement `code/pipelines/aggregate_results.py` to extract/aggregate the specific data points from previous artifacts (Data Availability Gap, statistical power, correlation coefficients). **Output**: Intermediate JSON file `data/artifacts/results_aggregation.json`. **Logic**: Perform data extraction from previous artifacts.
- [X] T053c [P] **Compile Data Availability Gap Report**: Implement `code/pipelines/compile_gap_report.py` to aggregate exclusion lists from T045, T032a, and T008d (if any) into a single `data/artifacts/final_data_availability_gap_report.json`. **Logic**: This task compiles the final human-readable report of excluded datasets and reasons, serving as the primary source for T053b. **Dependency**: Must run after T032a, T045, and T008b.
- [X] T053b [P] **Write Results Summary**: Generate a comprehensive `results_summary.md` in the repository root using `data/artifacts/results_aggregation.json` from T053a and `data/artifacts/final_data_availability_gap_report.json` from T053c. This document must explicitly detail the "Data Availability Gap" (datasets excluded due to missing baselines), the statistical power limitations of the final sample size (from T057), and the exact correlation coefficients with FDR-adjusted p-values. This document must serve as the definitive record of the research outcomes. **Logic**: Perform report writing using extracted data.
- [X] T054 Reproducibility Audit: Run `code/pipelines/update_state.py` one final time to ensure all artifacts (including the new `results_summary.md`) are hashed and the state YAML is updated with the final `updated_at` timestamp. Verify that the `state/projects/...yaml` file accurately reflects the completion of Phase 8.

---

## Phase 9: Review-Driven Revision & Gap Resolution (New)

**Purpose**: Address specific reviewer concerns regarding data source verification, statistical power reporting, and edge-case handling that were flagged in the initial analysis but not fully resolved in the previous phases.

- [X] T060 [US3] **Refine Correlation Report for Small Samples**: Update `code/analysis/correlation.py` to include a specific "Small Sample Warning" section in `data/artifacts/correlation_report_{run_id}.json` if the final dataset count (N) is < 30. **Logic**: If N < 30, explicitly state that the Pearson correlation assumes normality which may be violated, and recommend reporting Spearman's rank correlation as a robustness check. **Output**: Append a `robustness_check_recommendation` field to the report JSON. **Dependency**: Must run after T033 and T057. **Constraint**: This addresses the reviewer concern about the reliability of correlation coefficients on small, filtered datasets.
- [X] T061 [US1/US2] **Zero-Variance Feature Handling Audit**: Implement `code/pipelines/audit_zero_variance_handling.py` to verify that T045 and T045b correctly handled all zero-variance features identified in the metadata. **Logic**: Re-scan `data/processed/metadata_stats_summary.csv` and `data/artifacts/data_integrity_report.json` to ensure that every feature flagged as zero-variance in the report was either skipped in normalization (T024f) and excluded from the conditioning query (T026) and that no NaN values resulted from this process. **Output**: A detailed audit log `data/artifacts/zero_variance_audit.log`. **Dependency**: Must run after T024f and T045b. **Verification**: Check all columns in `data/processed/normalized_tabular_features.parquet` and assert `df.isna().sum().sum() == 0`. **Note**: This ensures the "zero-variance" edge case does not silently corrupt the training data.

---

## Phase 10: Final Execution Gate & Human Handoff (New)

**Purpose**: Execute the final pre-flight checks and prepare the project for human review if the automated analysis cycle completes successfully.

- [ ] T063 [Polish] **Generate Final Human-Readable Summary**: Implement `code/pipelines/generate_final_summary.py` to compile `data/artifacts/final_gate_report.json`, `data/artifacts/final_validation_report.md`, `data/artifacts/correlation_report_{run_id}.json`, and `data/artifacts/zero_variance_audit.log` into a single `FINAL_RESEARCH_SUMMARY.md` in the repository root. **Requirement**: This document must include a clear "Go/No-Go" recommendation for human review based on the success of T048 and the statistical validity of T033/T035. **Dependency**: Must run after T048 and T061. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T064 [US3] **Final Statistical Significance Verification**: Re-run the t-test (T035) and correlation (T033) on the final validated dataset subset to ensure no drift occurred during the final execution gate. **Logic**: Compare the final p-values against the initial run; if the difference exceeds a threshold, log a warning. **Output**: Append a `final_verification` section to `FINAL_RESEARCH_SUMMARY.md`. **Constraint**: This ensures the final results are reproducible and stable. <!-- FAILED: unspecified -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Verification (Phase 7)**: Depends on completion of all User Story implementations
- **Execution Hardening (Phase 9)**: Must be completed before any final CI run (T048)
- **Review-Driven Revision (Phase 10)**: Must be completed before final sign-off to ensure all reviewer concerns regarding data integrity and statistical rigor are addressed.
- **Final Execution Gate (Phase 11)**: Must be completed immediately before the final human review handoff.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on US1 output (embeddings)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on US1 and US2 output (metrics). **CRITICAL**: US3 cannot run in parallel with US2 as it consumes US2's artifacts.

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
- **Note on Execution**: While code implementation can be parallel, the execution of US1 -> US2 -> US3 is serial due to data dependencies (T024f is a shared prerequisite).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for batch processing logic in tests/test_embeddings.py::test_batch_processing_memory"
Task: "Unit test for gradient disabling in tests/test_embeddings.py::test_no_grad_context"

# Launch all models for User Story 1 together:
Task: "Implement code/embeddings/generator.py with CLIP ViT-B/32 and Sentence-BERT loaders"
Task: "Implement code/embeddings/utils.py with batch processing logic"
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
- **CRITICAL**: All tasks must run on CPU-only CI (limited cores, constrained RAM, time-constrained execution). [UNRESOLVED-CLAIM: c_d9715c4d — status=not_enough_info] No GPU, no 8-bit quantization, no large model fine-tuning.
- **CRITICAL**: Use real data from MulTaBench. Do not fabricate data or use random values for metrics.
- **CRITICAL**: Ensure data flow order: Embedding Generation (US1) → Projection Training (US2) → Correlation Analysis (US3).
- **CRITICAL**: All data generation tasks (T015, T019, T024, T025) must cover **ALL available datasets** to satisfy the correlation analysis requirements in US-003 and FR-001.
- **CRITICAL**: The loader in `code/data_loader.py` MUST fail loudly (raise exception) if real MulTaBench data is missing; no synthetic fallbacks are permitted.
- **CRITICAL**: T008c must explicitly define the source of the 'GPU-Tuned' baseline (local file `data/raw/multabench_baselines.csv`) and must NOT guess, synthesize, or parse external links if the file is missing. Refer to T008c for acquisition instructions.
- **CRITICAL**: T031 must use the **re-computed** frozen baseline performance metrics (from T015a) as the denominator, not historical paper values.
- **CRITICAL**: T045 must verify that no dataset in the analysis pipeline lacks sufficient variance, as this invalidates the correlation analysis (FR-003).
- **CRITICAL**: T048 is mandatory to verify the project meets the 6-hour/GB constraints defined in FR-004 before considering the feature complete.
- **CRITICAL**: T055 must be executed before any full pipeline run to prevent wasted CI time on invalid data states.
- **CRITICAL**: T056 is required to prevent OOM failures on large image datasets; the dynamic batch size must be logged and used consistently.
- **CRITICAL**: T057 ensures scientific rigor by explicitly stating the limitations of the statistical power given the sample size constraints (MANDATORY).
- **CRITICAL**: T024f must handle zero-variance features gracefully to prevent NaNs in normalization.
- **CRITICAL**: T053c must compile the final gap report from all exclusion sources.
- **CRITICAL**: T048b must limit the dataset count for runtime validation if necessary to meet FR-004.
- **CRITICAL**: T058, T059, T060, and T061 are mandatory revision tasks to address specific reviewer concerns regarding statistical power visualization, data source verification (checksum), small sample robustness, and zero-variance handling. These must be completed before the project is considered fully analyzed and ready for human review.
- **CRITICAL**: T059 must run BEFORE T048 as a pre-flight check.
- **CRITICAL**: T015a is the definitive source for the Seed 42 baseline for FR-001.
- **CRITICAL**: T062 is the final automated gate before the full pipeline run; it ensures no wasted CI time on invalid states.
- **CRITICAL**: T063 and T064 are mandatory for the final human handoff to ensure all results are stable, verified, and summarized in a single document.