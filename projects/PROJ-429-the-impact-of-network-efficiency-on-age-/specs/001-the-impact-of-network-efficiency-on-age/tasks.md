---
description: "Task list template for feature implementation"
---

# Tasks: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Input**: Design documents from `/specs/001-network-efficiency-aging/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  

Include exact file paths in descriptions.

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per `plan.md` structure)  
- Paths shown below assume single project structure defined in `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md`
- [X] T002 Initialize Python 3.11 project with virtualenv and `requirements.txt` (MNE, NetworkX, SciPy, Pandas, Statsmodels, PyWavelets)
- [ ] T003 [P] Configure linting and formatting tools
- [ ] T042d [P] Create `contracts/dataset.schema.yaml` defining the schema for input data validation (columns: participant_id, age, cognitive_instrument, cognitive_score, signal_quality). **Dep**: T001.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented  

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `docs/decisions/epoch_length.md`. **Content**:
  - `# Epoch Length Decision`
  - `## Rationale`: "Longer epochs provide sufficient spectral resolution for coherence estimation in the low-to-moderate frequency band, reducing variance compared to shorter epochs. This aligns with the ratified specification which mandates a defined number of training epochs."
  - `## Impact`: "Increased epoch duration improves signal‑to‑noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting‑state analysis."
  - `## Spec Reference`: Explicitly references `spec.md` which already mandates the required number of epochs.
  - **Deliverable**: Verify file exists with this structure. **Verify consistency with spec.md v1.1** to ensure no divergence. **Dep**: T001.
- [X] T014b [P] Create `docs/decisions/connectivity_metric.md`. **Content**:
  - `# Connectivity Metric Decision`
  - `## Rationale`: "Imaginary Coherence is selected over standard Coherence to mitigate volume conduction effects (field spread) which artificially inflate connectivity estimates. This is a standard practice in EEG functional connectivity analysis to ensure valid graph metrics."
  - `## Impact`: "Overrides the generic 'Coherence' requirement in FR‑003 with 'Imaginary Coherence' for scientific validity. This decision is ratified here to close the traceability gap."
  - `## Spec Reference`: Explicitly overrides FR‑003 for this project.
  - **Deliverable**: Verify file exists with this structure. **Dep**: T001.
- [X] T014c [P] **Formal Ratification**: Update `docs/decisions/` and `spec.md` references to formally ratify the 'Imaginary Coherence' deviation as a Design Decision (T014b) to satisfy traceability requirements. **Dep**: T014b.
- [X] T014d [P] **Spec Amendment**: Create `specs/001-the-impact-of-network-efficiency-on-age/spec_amendment_imag_coherence.md` documenting the approved deviation from FR‑003 (use of Imaginary Coherence) and confirming that the original formula constraints (global/local efficiency) remain applicable. **Dep**: T014c.
- [X] T004 [P] Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length). **Config Note**: Set `epoch_length_sec = 10` as per `spec.md` v1.1 and `docs/decisions/epoch_length.md`. **Deliverable**: Generate the 'initial version map of all source code artifacts with SHA‑256 hashes' required by FR‑006 (code only). Output file path: `state/version_map.yaml`. **Dep**: T014, T014b, T014c.
- [X] T025a [US2] [P] Create `data/config/cognitive_instrument_registry.yaml` with hard‑coded list of valid instruments (MMSE, MoCA) and references as per FR‑007. **Dep**: T004.
- [X] T005 [P] Implement `code/data/download.py` for PhysioNet/TUH access (accession ID: `tuh_eeg`), checksumming, and metadata validation. **Validation Logic**:
  1. **Schema Check**: Verify the existence and validity of `contracts/dataset.schema.yaml` (T042d) before proceeding.  
  2. **Age Check**: Filter for `age >= 18`.  
  3. **FR‑007 Compliance**: Validate `cognitive_instrument` field against the registry defined in `data/config/cognitive_instrument_registry.yaml` (T025a).  
     - If valid: Mark as **Valid**.  
     - If invalid instrument: Mark as **Invalid Instrument** (flag for exclusion in analysis, DO NOT block pipeline).  
     - If missing: Mark as **Missing Cognitive Data** (flag for exclusion in analysis, DO NOT block pipeline).  
  4. **Exit Logic**:  
     - If `total_valid_eeg_count == 0` → status **BLOCKED**, **exit code 1** (failure).  
     - If `missing_cognitive_count > 0` OR `invalid_instrument_count > 0` → status **PARTIAL**, exit code 0, log warning.  
     - Else status **OK**, exit code 0.  
  5. **Deliverable**: Write validation results to `data/quality/download_report.json` with schema `{"valid_count": int, "invalid_instrument_count": int, "missing_cognitive_count": int, "total_count": int, "status": "OK" | "PARTIAL" | "BLOCKED"}`. **Dep**: T042d, T025a.
- [X] T005_run [P] **Execute** `code/data/download.py` to generate `data/raw/` and `data/quality/download_report.json`. **Verification**: Ensure `download_report.json` exists, is non‑empty, and matches the schema (especially the `status` field). **Dep**: T005.
- [X] T042 [P] Implement chunked streaming in `code/data/download.py` using `mne.io.read_raw_edf` with offset/length parameters to handle large TUH corpus files without exceeding RAM limits. **Dep**: T005.
- [X] T006 [P] Implement `code/data/preprocess.py` for MNE‑Python pipeline. **Steps**:  
  1. Band‑pass filter 1‑40 Hz (`mne.filter.filter_data`).  
  2. ICA artifact removal (`mne.preprocessing.ICA`).  
  3. Epoch into **10‑second** segments (per `code/config.py` & `docs/decisions/epoch_length.md`).  
  4. Reject epochs with >50 % artifacts.  
  5. Calculate SNR per epoch; flag SNR < 10 dB.  
  **Dep**: T004.
- [X] T006_run [P] **Execute** `code/data/preprocess.py` to generate `data/processed/epochs/` (`*.fif`). **Verification**: Confirm epoch files exist, non‑NaN, and SNR flags are recorded in `data/quality/epoch_quality.json`. **Dep**: T006, T005_run.
- [X] T043 [P] Implement chunked streaming in `code/data/preprocess.py` to process epochs in batches, keeping memory < 6 GB during ICA and filtering. **Dep**: T006.
- [X] T007 [P] Implement `code/network/connectivity.py` for **Imaginary Coherence** calculation (Welch method on fixed‑duration epochs) to address volume conduction as per ratified Design Decision **T014b** (overrides FR‑003). Enforce CPU‑only execution (`device='cpu'`). **Dep**: T014b, T014c.
- [X] T007_run [P] **Execute** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/` (`*.npy`). **Verification**: Confirm CPU‑only execution (SC‑001) and that adjacency matrices match the standard 10‑20 montage dimensions. **Dep**: T007, T006_run.
- [X] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient, Modularity. **Formula Constraints**:  
  - Compute **Characteristic Path Length** explicitly.  
  - `Global_Efficiency = 1.0 / Path_Length`.  
  - `Local_Efficiency = 1.0 / mean_shortest_path(subgraph)` (subgraph‑based).  
  **Dep**: T007.
- [X] T008_run [P] **Execute** `code/network/metrics.py` to generate `data/results/network_metrics.csv`. **Implementation Note**:  
  - Inject `trace_id` as SHA‑256 of concatenated hashes of all input connectivity matrix files (`data/processed/connectivity_matrices/*.npy`) **plus** hashes of relevant code files (`code/network/metrics.py`, `code/network/connectivity.py`).  
  - Update `state/version_map.yaml` with the new CSV hash.  
  **Dep**: T008, T007_run.
- [X] T009 [P] Implement `code/stats/correction.py` for Bonferroni/FDR multiple‑comparison correction.
- [X] T010 [P] Implement `code/state/version_map.py` to manage SHA‑256 hashes and `updated_at` timestamps (Constitution Principle V).
- [X] T011 [P] [US1] Unit test for `code/network/metrics.py` that constructs a synthetic graph with known global and local efficiency values (e.g., a ring graph) and verifies the computed metrics match the expected formulas within 1e‑6 tolerance. **Dep**: T008.
- [X] T012 [P] [US1] Integration test for end‑to‑end preprocessing and metric generation (`tests/integration/test_pipeline.py`). **Dep**: T006_run, T008_run.
- [X] T013 [US1] [Dep: T005_run] Validate `download.py` output: ensure `data/raw/` contains TUH corpus with metadata flags; verify `download_report.json` exists and matches schema. **Dep**: T005_run.
- [X] T015 [US1] [Dep: T007_run] Validate `connectivity.py` output: ensure `data/processed/connectivity_matrices/` contains `.npy` files with dimensions matching the standard EEG montage. Verify non‑NaN values. **Dep**: T007_run.
- [X] T016 [US1] [Dep: T008_run] Validate derivation: verify `network_metrics.csv` respects formula constraints (global = 1/PL, local = 1/mean shortest path subgraph). Produce `efficiency_check.json` (`{"formula_verified": bool, "max_deviation": float}`) with `max_deviation` < 1e‑6. **Dep**: T008_run.
- [X] T017 [US1] [Dep: T016] Update `network_metrics.csv` to include a `signal_quality_flag` column (`Low Signal Quality` for SNR < 10dB).
- [X] T018a [US1] [Dep: T008_run] Sensitivity analysis – sweep network density thresholds 0.1‑0.9 (step 0.1) → `sensitivity_density_report.csv`. Schema: `threshold, metric_name, mean_value, std_dev, is_stable`.
- [X] T018b [US1] [Dep: T006_run, T007_run] Sensitivity analysis – vary artifact‑rejection thresholds → `sensitivity_artifact_report.csv`. Schema: `rejection_threshold, metric_name, std_dev, is_stable`.
- [X] T018c [US1] Aggregate sensitivity results → `sensitivity_summary.json`. **Schema**: `{"density_stable": bool, "artifact_stable": bool, "overall_stable": bool, "status": "PASS" | "FAIL", "reason": str}`. Derive `status` as PASS only if both density and artifact analyses are stable; otherwise FAIL with explanatory reason. **Dep**: T018a, T018b.
- [X] T018d [US1] Generate consolidated sensitivity documentation `data/results/sensitivity_report.md` summarizing the findings from T018a‑T018c, including tables and interpretation. **Dep**: T018c.
- [X] T019 [US1] Validate that `trace_id` column exists in `network_metrics.csv` and contains valid SHA‑256 hex strings. **Dep**: T008_run.
- [X] T020 [US1] Validate output schema of `network_metrics.csv` (`participant_id, age, global_efficiency, local_efficiency, clustering_coeff, modularity, trace_id, signal_quality_flag`) and data types. **Dep**: T019.
- [X] T027 [US2] Implement `code/stats/power.py` to perform **Monte Carlo MDES analysis**:  
  1. Use the actual participant count from `download_report.json`.  
  2. Simulate datasets across a range of effect sizes to find the smallest r detectable with ≥ 80 % power (MDES).  
  3. Also compute power for the target r = 0.3 to report `power_for_r03`.  
  4. Output `data/results/power_analysis.json` with schema `{"mdes": float, "power_for_r03": float, "is_sufficient": bool, "simulation_seed": 42, "actual_n": int}` where `is_sufficient` is true if `power_for_r03 >= 0.80` **and** `mdes <= 0.3`.  
  **Dep**: T005_run.
- [X] T027_run [US2] Execute `code/stats/power.py` → generate `power_analysis.json`. **Dep**: T027.
- [X] T027b [US2] Halt check: if `is_sufficient == false` **AND** `actual_n < 85`, log warning *“Study underpowered for cognitive analysis; skipping cognitive visualization tasks”* and skip downstream US2/US3 tasks (T031, T031_run, T034, T035) while continuing to Phase 5. Also skip if `download_report.json` status is **PARTIAL** or **BLOCKED**. **Dep**: T027_run.
- [X] T023 [US2] Implement Spearman correlation (metrics ↔ Age & Cognitive Score) with Bonferroni/FDR correction. **Dep**: T008_run, T025b, T025c.
- [X] T023_run [US2] Execute `code/stats/correlation.py` → generate `data/results/correlation_results.csv` with columns `metric_name,outcome,spearman_r,p_value,p_adjusted,n,trace_id`. **Trace_id** computed as SHA‑256 of concatenated hashes of `data/results/network_metrics.csv` and the correlation script code. **Dep**: T023, T008_run.
- [X] T028 [US2] Validate `trace_id` column exists in `correlation_results.csv` and contains valid SHA‑256 hex strings. **Dep**: T023_run.
- [X] T029 [US2] Validate output schema (`metric_name,outcome,spearman_r,p_value,p_adjusted,n,trace_id`) and data types. **Dep**: T028.
- [X] T053 [US2] Sensitivity analysis of multiple‑comparison correction methods (Bonferroni vs. FDR) → `correction_sensitivity_report.csv`. Schema: `method,metric_name,outcome,p_adjusted,is_stable`. **Dep**: T023_run.
- [X] T031 [US3] Implement `code/stats/regression.py` (Cognition ~ Efficiency + Age + Sex + Education) with VIF check. Executes only if `download_report.json` status is **OK**. **Dep**: T008_run, T005_run.
- [X] T031_run [US3] Execute `code/stats/regression.py` → generate `data/results/regression_results.csv` with columns `outcome,predictor,coef,std_err,t_value,p_value,trace_id`. **Trace_id** = SHA‑256 of concatenated hashes of `data/results/network_metrics.csv`, `data/results/correlation_results.csv` (if used), and the regression script. **Dep**: T031, T008_run.
- [X] T032 [US3] Create `regression_summary.json` containing a `warnings` array; if `power_analysis.json` shows `is_sufficient == false`, append *“Low Power for Cognitive Analysis”* to the array. **Dep**: T027_run, T031_run.
- [X] T033 [US3] Implement `code/viz/plots.py` to generate age‑stratified bar plots with confidence intervals. Always executes (EEG‑only viz). Output files: `figures/age_stratified_metrics_{metric}.png`. **Dep**: T008_run.
- [X] T054 [US2] Implement a visualization to display correlation coefficients between network metrics and Age/Cognitive score with confidence intervals → `figures/correlation_heatmap.png`. **Dep**: T023_run.
- [X] T056 [US3] Implement network‑topology visualizations (`plot_connectome` & `plot_topomap`) for each age group → `figures/topology_age_{group}.png`. **Dep**: T008_run.
- [X] T034 [US3] Generate regression table `data/results/regression_table.csv` with coefficients, standard errors, p‑values, and injected `trace_id`. **Dep**: T031_run, T032.
- [X] T035 [US3] Validate output schema (`outcome,predictor,coef,std_err,t_value,p_value,trace_id`) and data types for `regression_table.csv`. **Dep**: T034.
- [X] T036 [US3] Generate final summary report `report/final_report.md` aggregating data‑quality metrics, power analysis, FWER validation, low‑power warnings, and sensitivity summary. **Dep**: T052, T027_run, T053, T018d, T032.
- [X] T064a [US1] Implement precise SNR calculation in `code/data/preprocess.py` and ensure epochs with SNR < 10 dB are flagged correctly; add unit test `tests/unit/test_snr.py`. **Dep**: T006.
- [X] T065a [US2] Implement sensitivity analysis of correlation results to multiple‑comparison methods (Bonferroni vs. FDR) and produce `correlation_correction_sensitivity.csv`. **Dep**: T023_run.
- [X] T066a [US3] Explore alternative network topology visualizations (different colormaps, node size scaling by strength) and output example figures `figures/topology_alt_{scheme}.png`. Document choices in `docs/visualization_alternatives.md`. **Dep**: T056.
- [X] T037 [P] Documentation updates in `docs/` (README, quickstart.md)
- [X] T038 Code cleanup and refactoring
- [X] T039 Performance optimization (ensure execution < 6 h on free‑tier CI)
- [X] T040 [P] Additional unit tests in `tests/unit/`
- [X] T041 Run `quickstart.md` validation to ensure end‑to‑end reproducibility
- [X] T058 [P] Add GitHub Actions CI workflow (`.github/workflows/ci.yml`) to run linting, tests, and the full pipeline on the free CPU runner.
- [X] T059 [P] Add unit tests for network‑topology visualizations (`tests/unit/test_viz.py`).
- [X] T060 [P] Document power‑analysis methodology and results in `docs/power_analysis.md`.
- [X] T061 [P] Gracefully handle missing cognitive scores: participants without cognitive data are excluded from cognitive‑specific analyses but retained for age‑only analyses, with logging. **Dep**: T025a, T023.
- [X] T062 [P] After every artifact generation step (e.g., `network_metrics.csv`, `correlation_results.csv`, `regression_results.csv`), update `state/version_map.yaml` with the new SHA‑256 hash and timestamp.
- [X] T063 [P] Create a lightweight Dockerfile for reproducible local execution (CPU‑only) and publish to GitHub Container Registry.

---

- [ ] T064 [US1] **Reviewer Concern: FR-002 Epoching**. Add a task to re‑validate the epoching process in `code/data/preprocess.py` to ensure the SNR calculation is accurate and the epoch filtering criteria (SNR < 10dB) are correctly applied. Reference: # Prior research-stage reviews (Epoching SNR).
- [ ] T065 [US2] **Reviewer Concern: Statistical Analysis**. Add a task to implement a sensitivity analysis to assess the robustness of the correlation results to different multiple comparison correction methods (Bonferroni vs. FDR). Reference: # Prior research-stage reviews (Statistical Correction).
- [ ] T066 [US3] **Reviewer Concern: Visualization**. Add a task to explore alternative visualization techniques for network topology changes across age groups, such as using different color schemes or node sizes to represent the strength of connectivity. Reference: # Prior research-stage reviews (Network Visualization).