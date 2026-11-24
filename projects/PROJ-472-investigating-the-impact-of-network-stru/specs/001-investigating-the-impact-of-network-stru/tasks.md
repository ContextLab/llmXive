# Tasks: Investigating the Impact of Network Structure on Neural Avalanche Dynamics  

**Input**: `spec.md`, `plan.md`, `data‑model.md`, contract schemas in `specs/001‑investigating‑the‑impact‑of‑network‑stru/contracts/`  

The checklist follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
`[P]` = can run in parallel (no file overlap).  
`[USx]` = user‑story identifier (US1 = data pipeline, US2 = metric computation, US3 = statistical association).  

---  

## Phase 0 – Project Planning & Validation  

- [ ] T000 [P] Draft a high‑level data‑acquisition plan that outlines matched dMRI + EEG participant indexing and defines verification criteria for ID alignment.  
- [ ] T001 Create project directory layout (`code/`, `tests/`, `data/`) and add a README.  
- [X] T002 Pin Python dependencies in `code/requirements.txt` (including `mne`, `networkx`, `powerlaw`, `mrtrix3` system binary, etc.).  

## Phase 1 – Project Setup (shared infrastructure)

- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.  

## Phase 2 – Foundational Configuration & Documentation  

- [ ] T004 [P] Add `code/config.py` with constants:  
  - `DMRI_DATASET_URL = "https://openneuro.org/datasets/ds004230"`  
  - `EEG_DATASET_URL = "https://openneuro.org/datasets/ds004231"`  
  - `HCP_MMP_URL = "https://openneuro.org/datasets/ds004230/files/HCP_MMP1.0_Glasser2016.zip"`  
  - `SENSITIVITY_THRESHOLDS = [0.70, 0.75, 0.80]`  
  - `N_MIN = 10` (minimum subjects for correlation).  
- [ ] T005 [P] Initialise `data/raw/`, `data/processed/`, `data/results/` and create `data/raw/.checksums.json` placeholder.  
- [ ] T006 Create core data‑model classes (`Participant`, `StructuralConnectome`, `AvalancheRecord`) in `code/data/models.py`.  
- [ ] T007 Add a project‑wide logger (`code/utils/logger.py`).  
- [ ] T008 Load environment variables from a `.env` file (paths, seeds).  

### Documentation (auto‑generated)

- [ ] T025a [P] Generate `specs/001‑investigating‑the‑impact‑of‑network‑stru/quickstart.md` with installation steps, required system packages (MRtrix3, MNE‑Python) and the command to run the full pipeline.  
  - **Verification**: `tests/test_quickstart_generation.py` checks file existence and required sections.  
- [ ] T025b [P] Generate `specs/001‑investigating‑the‑impact‑of‑network‑stru/data‑model.md` (already present).  
  - **Verification**: `tests/test_data_model_doc.py` asserts file matches schema description.  
- [ ] T025c [P] Generate `specs/001‑investigating‑the‑impact‑of‑network‑stru/research.md` placeholder for later manuscript hand‑off.  
  - **Verification**: `tests/test_research_md.py` checks file creation.  

---  

## Phase 3 – User Story 1: Data Pipeline Integration (Priority P1)  

**Goal**: Acquire matched diffusion‑MRI and resting‑state EEG from OpenNeuro and produce a unified participant‑indexed store (real data only).  

- [ ] T009 [US1] Implement `code/data/download.py` to stream‑download:  
  - dMRI tractography (`ds004230`) into `data/raw/dMRI/`.  
  - Resting‑state EEG (`ds004231`) into `data/raw/EEG/`.  
  - Verify each file’s SHA‑256 against entries in `data/raw/.checksums.json`.  
  - Write `data/processed/routing_state.json` with keys `has_matched_eeg`, `n_subjects_dMRI`, `n_subjects_EEG`, and data‑path pointers.  
  - **Verification**: `tests/test_download_alignment.py` confirms subject IDs are identical across modalities.  
- [ ] T010 **[US1]** Implement `code/data/preprocess_dMRI.py` to:  
  - Download `HCP_MMP1.0_Glasser2016.zip` if missing (via `config.HCP_MMP_URL`).  
  - Extract the parcellation file.  
  - For each subject’s tractography (`*.tck`) run MRtrix3 `tck2connectome` to generate a weighted adjacency matrix (`.npy`).  
  - Save matrices to `data/processed/connectomes/sub-{id}/connectome.npy`.  
  - Record the computed SHA‑256 of the parcellation zip in `data/processed/parcellation_hash.json` and compare it to the sentinel value.  
  - **Verification**: `tests/test_preprocess_dMRI.py` asserts a known subject’s matrix shape and successful hash check.  
- [ ] T011a [US1] Implement `code/data/check_availability.py` that reads `routing_state.json` and writes `data/processed/data_availability_status.json` with `"has_real_data": true/false`.  
- [ ] T011b [US1] Implement `code/data/preprocess_EEG.py` (real‑EEG path). Runs only if `has_real_data` is true: band‑pass 1‑40 Hz, down‑sample to 250 Hz, ICA cleaning via MNE‑Python, and writes cleaned FIF files to `data/processed/eeg/sub-{id}/eeg_cleaned.fif`.  
- [ ] T011d [US1] Implement `code/data/generate_unit_test_data.py` that creates a tiny synthetic dataset with an injected Spearman ρ≈0.7, saved as `data/processed/unit_test/metrics_ground_truth.csv`.  
- [ ] T012 [US1] Implement `code/data/quality_control.py` to:  
  - For **real** EEG, flag subjects with >30 % channels removed after ICA.  
  - For structural graphs, flag subjects whose connectivity matrix is disconnected (`networkx.is_connected`).  
  - Output `data/processed/usable_subjects.json` (list of IDs) and compute `pipeline_quality_rate` (proportion of usable subjects).  
  - **Verification**: `tests/test_quality_control.py` checks JSON fields and correct flagging.  
- [ ] T012‑verify Add verification step to confirm `usable_subjects.json` and `pipeline_quality_rate` are present and correctly formatted.  
- [ ] T013 [US1] Implement `code/data/store.py` that merges structural and EEG paths into a unified index `data/processed/unified_participant_store.json` with fields `{subject_id, structural_path, eeg_path, data_type}`.  

**Checkpoint** – After T013 the data pipeline is end‑to‑end (real only) and can be validated independently.  

---  

## Phase 3.5 – Sample‑Size Gate (blocking before statistics)

- [ ] T029c **[US3]** Add a runtime gate in `code/main.py` that reads `usable_subjects.json`, compares its length to `config.N_MIN`, writes an updated `routing_state.json` with `"status": "proceed"` or `"limited"` and, if limited, creates `data/results/insufficient_sample_report.md`.  
  - **Verification**: `tests/test_sample_gate.py` ensures routing_state status and report generation.  

---  

## Phase 4 – User Story 2: Metric Computation (Priority P2)  

- [ ] T014 [US2] Implement `code/analysis/network_metrics.py` to compute for each subject: mean degree, mean clustering coefficient, and rich‑club coefficient (using NetworkX). Save to `data/results/structural_metrics.csv`.  
- [ ] T014a [US2] **Package required inputs for independent US2 execution** – copy each subject’s structural connectome (`data/processed/connectomes/sub-{id}/connectome.npy`) and cleaned EEG (`data/processed/eeg/sub-{id}/eeg_cleaned.fif`) into a US‑2‑specific directory `data/us2_input/`. This enables US‑2 tasks to run without invoking US‑1 tasks directly.  
- [ ] T015 [US2] Implement `code/analysis/avalanches.py` to detect neural avalanches:  
  1. Load the **raw** EEG (pre‑ICA) to compute the 75 th percentile amplitude per subject.  
  2. Z‑score the full EEG trace.  
  3. Threshold the z‑scored signal at the transformed percentile value.  
  4. Identify contiguous spatiotemporal events and write `data/processed/avalanches/sub-{id}/avalanche_events.csv`.  
- [ ] T015‑verify Add verification that percentile is computed on raw signal before z‑scoring (`tests/test_avalanche_percentile.py`).  
- [ ] T015c [US2] Aggregate all avalanche event tables, fit power‑law models (size & duration) with likelihood‑ratio comparison, and write `data/results/avalanche_metrics.csv` (exponents, model‑fit status).  
- [ ] T016 [US2] Implement `code/analysis/fitting.py` (power‑law package) with explicit handling of convergence failures (log error, mark `model_fit_status = "fit_failed"`).  
- [ ] T016‑verify Add verification that distinct error code is logged and participants are excluded when fitting fails (`tests/test_fitting_error_code.py`).  
- [ ] T017 [US2] Create `code/analysis/export_metrics.py` that merges `structural_metrics.csv` and `avalanche_metrics.csv` into a single participant‑level file `data/results/metrics_combined.csv`.  
- [ ] T018 [P] Add unit tests for network metrics (`tests/test_network_metrics.py`) and avalanche detection (`tests/test_avalanches.py`).  

---  

## Phase 5 – User Story 3: Statistical Association & Robustness (Priority P3)  

- [ ] T019a [US3] **Package combined metrics for independent US3 execution** – copy `data/results/metrics_combined.csv` into a US‑3‑specific directory `data/us3_input/`. This allows the statistical pipeline to run without depending on US‑2 execution order.  
- [ ] T019 [US3] Implement `code/analysis/stats.py` – Spearman rank correlation between each structural metric and each avalanche exponent. Reads `data/us3_input/metrics_combined.csv`.  
- [ ] T019‑verify Add verification that `stats.py` raises an error if required columns are missing.  
- [ ] T020 [US3] Extend `stats.py` with a non‑parametric permutation test (≥ 1000 shuffles) and max‑stat family‑wise error correction.  
- [ ] T021 [US3] Add VIF calculation for degree + clustering predictors; write `data/results/collinearity_status.json` with fields `high_collinearity` (bool) and `vif_value`.  
- [ ] T021‑verify Add verification that JSON contains both fields and correct boolean logic.  
- [ ] T022 [US3] Implement `code/analysis/sensitivity.py` that repeats the correlation pipeline for each threshold in `config.SENSITIVITY_THRESHOLDS` and writes `data/results/sensitivity_summary.csv`.  
- [ ] T022‑verify Add verification that three distinct threshold runs are present in the summary file.  
- [ ] T023 [US3] Implement `code/analysis/report.py` that:  
  - Reads all result files.  
  - Generates `data/results/report.md` with tables, scatter plots, and explicit **associational** language only.  
  - Calls the causal‑keyword validator (see T032).  
  - Reads `data/results/collinearity_status.json` and inserts the mandated sentence when high collinearity is detected.  
- [ ] T023‑verify Add verification that the collinearity sentence appears when appropriate (`tests/test_report_collinearity_sentence.py`).  
- [ ] T024 [P] Add integration tests (`tests/test_stats.py`) that load the synthetic ground‑truth CSV from T011d and assert that the pipeline recovers the injected correlation, significance, and VIF flag.  

---  

## Phase 6 – Revision & Compliance Tasks (addressing reviewer concerns)

- [ ] T031 [US3] Standardise threshold values in `sensitivity.py` to use `config.SENSITIVITY_THRESHOLDS`.  
  - **Verification**: `tests/test_threshold_config_usage.py` ensures the config list is imported.  
- [ ] T032 [US3] Add a causal‑keyword guard in `report.py` that raises `RuntimeError` if prohibited words appear.  
  - **Verification**: `tests/test_causal_guard.py` injects a prohibited term and expects an error.  
- [ ] T033 [US2] Ensure `fitting.py` logs a distinct error code and excludes participants when power‑law fitting fails.  
  - **Verification**: `tests/test_fitting_exclusion.py` checks log and output file.  

---  

## Phase 7 – Polishing & Edge‑Case Tests  

- [ ] T040 [P] Add unit tests for disconnected graphs and power‑law convergence (`tests/test_edge_cases.py`).  
- [ ] T036 [P] Add test for the insufficient‑sample pathway (`tests/test_null_result.py`).  
- [ ] T037 [P] Add test for causal‑framing validator (`tests/test_report_framing.py`).  
- [ ] T038 [P] Add test for proper handling of power‑law fit failures (`tests/test_fitting.py`).  
- [ ] T039 [P] Add test for the sensitivity sweep using the three hard‑coded thresholds (`tests/test_sensitivity.py`).  
- [ ] T041 [P] Add test that `download.py` streams large files without exceeding memory (`tests/test_streaming.py`).  
- [ ] T042 [P] Add test that the report correctly flags simulated EEG as “simulation_only” and enforces associational framing (`tests/test_synthetic_detection.py`). *(Note: simulation is only used for unit‑test data, not for primary analysis.)*  
- [ ] T043 [P] Add test that VIF ≥ 5 triggers the high‑collinearity message in the final report (`tests/test_vif_enforcement.py`).  
- [ ] T044 [P] Add test that `download.py` rejects any non‑OpenNeuro URLs and fails loudly if the expected datasets are missing (`tests/test_download_validation.py`).  
- [ ] T045 [P] Add test that permutation results are reproducible given a fixed seed (`tests/test_permutation_reproducibility.py`).  
- [ ] T046 [P] Add test that model‑comparison logic selects the power‑law only when statistically preferred (`tests/test_model_comparison.py`).  

---  

## Phase 8 – Final Validation & Execution Readiness  

- [ ] T047 [P] Remove all silent‑fallback `try/except` blocks from `download.py`; any network error now raises `ConnectionError`.  
  - **Verification**: `tests/test_silent_fallback_removed.py` scans source for prohibited patterns.  
- [ ] T048 [P] Ensure `download.py` uses `datasets.load_dataset(..., streaming=True)` for files > 100 MB and logs chunk sizes.  
  - **Verification**: `tests/test_streaming_usage.py` asserts streaming flag is set.  
- [ ] T049 **[US3]** Extend `report.py` to read `data/results/collinearity_status.json`; if `high_collinearity` is true, insert the sentence:  
  > “High collinearity (VIF ≥ 5) detected between degree and clustering coefficient. Independent predictive effects are not claimed.”  
  - **Verification**: `tests/test_report_collinearity_sentence.py` (also listed in Phase 5).  
- [ ] T050 **[US3]** Run a full end‑to‑end test with a tiny synthetic dataset (N = 5):  
  - Command: `python code/main.py --test-mode --n-subjects=5`.  
  - Produce `data/results/integration_test_report.md` containing pipeline logs, routing‑state summary, and a success flag.  
  - **Verification**: `tests/test_integration_report.py` checks file existence, success flag, and recorded runtime ≤ 6 h.  
- [ ] T061 **[US3]** Record total pipeline runtime (wall‑clock) in `data/results/runtime_metrics.json` and assert it is ≤ 6 h.  
  - **Verification**: `tests/test_runtime_ceiling.py` validates the JSON value.  

---  

## Phase 9 – Post‑Analysis Review (triggered by `/speckit.analyze`)

- [ ] T051 **[US3]** Add checksum verification for both dMRI and EEG files after download (compare against `data/raw/.checksums.json`).  
  - **Verification**: `tests/test_checksum_verification.py` ensures mismatch raises error.  
- [ ] T052 **[US3]** Clarify in `avalanches.py` that the 75 th percentile is computed on the **raw** signal before z‑scoring and then applied to the z‑scored trace.  
  - **Verification**: `tests/test_avalanche_percentile_logic.py` checks ordering.  
- [ ] T053 **[US3]** Extend the causal‑keyword guard to scan all generated figures, tables, and log files for prohibited language.  
  - **Verification**: `tests/test_figure_keyword_guard.py` validates scanning.  
- [ ] T054 **[US3]** Refine `fitting.py` decision tree: select power‑law only if it beats both exponential **and** log‑normal in the likelihood‑ratio test (p < 0.05).  
  - **Verification**: `tests/test_fitting_decision_tree.py` confirms logic.  
- [ ] T055 **[US3]** Add a retry mechanism to the permutation test (max 3 attempts) and fallback to a conservative p‑value (1.0) if convergence fails.  
  - **Verification**: `tests/test_permutation_retry.py` forces failure and checks fallback.  
- [ ] T056 **[US3]** Document every simulation parameter in `config.py` with explanatory comments (kept for unit‑test synthetic data).  
  - **Verification**: `tests/test_config_documentation.py` parses comments.  
- [ ] T057 **[US3]** Add unit test `tests/test_threshold_sensitivity.py` that checks correlation results differ across the three thresholds.  
- [ ] T058 **[US3]** Add unit test `tests/test_collinearity_diagnostics.py` that verifies VIF calculation and flagging logic on a crafted high‑collinearity dataset.  
- [ ] T059 **[US3]** Add unit test `tests/test_data_quality_filtering.py` that ensures subjects with >30 % bad EEG channels or disconnected graphs are excluded.  
- [ ] T060 **[US3]** Implement a compliance‑checker script (`code/validation/compliance_check.py`) that automatically verifies every functional requirement (FR‑001 – FR‑011) and success criterion (SC‑001 – SC‑006), outputting a concise JSON report.  
  - **Verification**: `tests/test_compliance_checker.py` validates JSON schema and content.  

---  

### Dependency & Execution Order Summary  

| Phase | Key Tasks (must complete before next phase) |
|-------|--------------------------------------------|
| 0 & 1 & 2 | T000‑T008 (project skeleton, config, docs) |
| 3 & 3.5 | T009‑T013, T029c (data pipeline & sample‑size gate) |
| 4 | T014‑T018 (metric computation) |
| 5 | T019‑T024 (statistical analysis) |
| 6 | T031‑T033 (threshold standardisation, causal guard, fit handling) |
| 7 | T040‑T046 (edge‑case unit tests) |
| 8 | T047‑T061 (final validation, runtime measurement) |
| 9 | T051‑T060 (post‑analysis review & compliance) |

All tasks respect data flow: downstream tasks depend only on artifacts produced by their prerequisites. Parallel‑safe tags (`[P]`) are applied only to tasks that do not share mutable files. A script run from the project resolves `state/...` INSIDE the project, leaving a stale shadow of canonical state that the verifier then reads and rejects honest work against — PROJ-9999 lost two whole runs to exactly that.  

---  

**All unchecked tasks (including the reopened ones T010, T049, T050) are now fully specified with verification steps and will be completed before the project can transition from `planned` → `tasked` → `analyze_in_progress`.**  