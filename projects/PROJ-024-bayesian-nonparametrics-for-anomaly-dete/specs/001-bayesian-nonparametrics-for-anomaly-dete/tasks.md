# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series  

**Inputs**: `specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

The following checklist implements the full research pipeline while fixing all specification‑ and implementation‑level violations identified by the reviewers.  Each task is a single atomic unit that can be run, verified, and tracked independently.  All artifact paths are project‑owned (`code/`, `data/processed/`, `state/`).  Completed work from previous iterations is retained but any stale or non‑conforming artefacts have been reopened and re‑tasked.

---

## Phase 0 – Dataset discovery, generation, validation, and split  

- [ ] **T020** [P2] [US0] Search for real‑world datasets with known regime shifts using keywords “regime shift time series”, “anomaly benchmark”, “physionet arrhythmia” across UCI, NAB, and PhysioNet. If no verified sources are found, generate a **Validation Deferred** report (`data/processed/results/validation_deferred.md`) citing the search query and result count (FR‑017, FR‑017b).  
  - **Script**: `code/src/data/search_datasets.py`  
  - **Outputs**: `data/raw/` (populated only if sources found) and `data/processed/results/validation_deferred.md`.  

- [ ] **T003** [P2] [US1] Download and validate real‑world datasets (NAB & PhysioNet) using the verified URLs defined in the “Verified Datasets” block *only if* T020 discovers sources.   <!-- FAILED-IN-EXECUTION: code/src/data/download_datasets.py exit=1 -->
  - **Script**: `code/src/data/download_datasets.py`  
  - **Outputs**: `data/raw/<dataset_name>.csv`, `data/processed/results/data_checksums.json`.  
  - **Verification**:  
    1. SHA‑256 checksum matches JSON entry.  
    2. Row count ≥ 1 000.  
    3. Failure raises an exception (no silent fallback).  

- [ ] **T018** [P2] [US1] Load each univariate time series, enforce **≥ 1 000 observations**, and normalize to zero mean / unit variance (explicitly satisfies FR‑001).  
  - **Script**: `code/src/data/preprocessing.py`  
  - **Outputs**: `data/processed/normalized/<dataset_name>.parquet`.  
  - **Verification**:  
    1. Row count check (≥ 1000).  
    2. Mean ≈ 0, std ≈ 1 (tolerance 0.001).  

- [ ] **T025** [P2] [US1] Generate the synthetic dataset with injected anomalies **and** pre‑anomaly dynamics (increasing variance, autocorrelation) as required by FR‑021.  
  - **Script**: `code/src/data/synthetic_generator.py`  
  - **Outputs**: `data/processed/synthetic_generator_output.parquet`.  

- [ ] **T023** [P2] [US1] Validate that the synthetic generator implements the required pre‑anomaly dynamics and that its output statistics match expectations (FR‑022).  
  - **Script**: `code/src/data/verify_synthetic.py`  
  - **Outputs**: `data/processed/results/synthetic_verification.txt` (passes/fails with quantitative summary).  

- [ ] **T021** [P2] [US1] Create a **train/validation/test split** (70/15/15) for each dataset (real and synthetic). Store indices in `data/processed/split_indices.json`. This split is required before any threshold calibration (FR‑019).  
  - **Script**: `code/src/data/split.py`  
  - **Verification**:  
    1. No overlap between splits.  
    2. Each split contains at least one injected anomaly (if present).  

- [ ] **T005** [P1] [US1] Run the **first executable end‑to‑end analysis** on a minimal verified dataset (e.g., the smallest NAB series) to produce a real result file and confirm the pipeline works.  
  - **Command (documented in `quickstart.md`)**:  
    ```bash
    python -m code.src.scripts.run_pipeline \
        --config code/config.yaml \
        --dataset data/processed/normalized/nab_example.parquet \
        --output data/processed/posterior_trajectory.parquet
    ```  
  - **Outputs**:  
    * `data/processed/posterior_trajectory.parquet` (conforms to `posterior_trajectory.schema.yaml`)  
    * `data/processed/detection_events.json` (conforms to `detection_event.schema.yaml`)  
  - **Verification**:  
    1. Parquet contains a row per sliding window; `converged` matches ADVI convergence.  
    2. Detection events include at least one non‑null `time_to_detection`.  
    3. Log `run_metadata` (peak RAM, runtime) in `data/processed/results/first_run_metadata.json`.  

---

## Phase 1 – Setup, compliance, and preparatory studies  

- [ ] **T001** [P2] [US4] Enforce `code/config.yaml` size < 2 KB and contain **only** hyper‑parameters required by `anomaly_detector.schema.yaml` (seeds, model, thresholds, baselines, paths).  
  - **Steps**:  
    1. Strip derived statistics, checksums, and any runtime‑generated fields.  
    2. Validate size with `os.path.getsize()` < 2048 bytes.  
    3. Run `code/scripts/validate_config_schema.py` – must exit 0 with “Validation passed”.  
    4. Record byte count in `data/processed/results/config_compliance.txt`.  

- [ ] **T002** [P2] [US1] Restructure all Python source files under the canonical package layout `code/src/`.  
  - **Files moved**: any `.py` in `code/` root or stray sub‑folders (`baselines/`, `models/`, `evaluation/`, `services/`, `data/`) → `code/src/<module>/`.  
  - **Steps**:  
    1. Physically move files, update import statements (`from ... import ...`).  
    2. Adjust `PYTHONPATH` in `quickstart.md` to `code/src`.  
    3. Verify no empty legacy directories remain (`find code/ -type d -empty`).  
    4. Run full test suite (`pytest code/tests/`) – must pass.  
    5. Capture the directory‑tree diff in `data/processed/results/src_structure_report.txt`.  

- [ ] **T022** [P2] [US1] Perform the **signal‑to‑noise ratio (SNR) simulation study** for the $\dot{\\alpha}$ estimator under the null hypothesis (no anomaly).  
  - **Script**: `code/src/evaluation/simulation.py`  
  - **Outputs**: `data/processed/results/snr_report.json` (contains SNR value, confidence interval).  
  - **Verification**: Pipeline proceeds only if `SNR > 1`; otherwise abort with clear message.  

- [ ] **T024** [P2] [US1] Conduct **prior‑sensitivity analysis** on the Dirichlet‑process concentration hyper‑parameter (`alpha_prior_sigma`).  
  - **Method**: Run DP‑GMM on a subset of windows with three different prior sigmas (0.05, 0.1, 0.2) and record impact on $\dot{\\alpha}$ variance, detection performance, and statistical power.  
  - **Outputs**: `data/processed/results/prior_sensitivity.csv` (columns `alpha_prior_sigma`, `snr`, `wilcoxon_p`, `cohen_d`).  
  - **Verification**: CSV includes required columns and at least one configuration achieving `SNR > 1`.  

---

## Phase 2 – Full study, comparisons, and statistical validation  

- [ ] **T006** [P2] [US2] Execute the **full DP‑GMM pipeline** on all verified real datasets *and* the synthetic dataset.  
  - **Inputs**: `data/processed/normalized/*` + `data/processed/synthetic_generator_output.parquet`.  
  - **Outputs**:  
    * `data/processed/posterior_trajectory.parquet` (full trajectory)  
    * `data/processed/detection_events.json` (all methods)  
  - **Verification**:  
    1. All windows processed; non‑convergent windows flagged `converged=False`.  
    2. ADVI iteration count ≤ `config.yaml` `advi_max_iter`.  
    3. Record runtime and peak RAM in `data/processed/results/full_run_metadata.json`.  

- [ ] **T007** [P2] [US2] Fit **baseline models** (fixed‑component GMMs with k = 3, 5, 10 and ARIMA) on the same sliding windows and compute reconstruction‑error scores.  
  - **Script**: `code/src/models/baselines.py`  
  - **Outputs**: `data/processed/baseline_errors.parquet` (columns: `window_id`, `gmm_k`, `arima_error`, `mse`).  
  - **Verification**:  
    1. Each window has at least one baseline score.  
    2. Schema validated against `output.schema.yaml` (baseline part).  

- [ ] **T026** [P3] [US3] Calibrate **anomaly‑detection thresholds** on the **validation split** (produced by T021). Use the 95th percentile of the validation‑set score distribution as the default, then store the calibrated thresholds.  
  - **Script**: `code/src/services/threshold_calibrator.py`  
  - **Outputs**: `data/processed/results/calibrated_thresholds.json` (fields `threshold`, `percentile`, `adaptive`).  

- [ ] **T019** [P2] [US3] If the **anomaly count** in the current run is **< 10**, execute **bootstrap resampling** for inferential testing and record bootstrap p‑values and confidence intervals (FR‑011, FR‑012).  
  - **Script**: `code/src/evaluation/bootstrap.py`  
  - **Outputs**: `data/processed/results/bootstrap_report.json` (`used`, `p_value`, `ci_lower`, `ci_upper`).  
  - **Verification**: `used` is true only when count < 10; report is incorporated into the final statistical report.  

- [ ] **T008** [P2] [US2] Calculate **time‑to‑detection** for DP‑GMM signatures and each baseline, then perform the required statistical tests (Wilcoxon, paired t‑test if normality holds, Cohen’s d, KS tests FR‑010, FR‑014, FR‑015). Incorporate bootstrap results from T019 when applicable.  
  - **Metrics**: Wilcoxon signed‑rank (primary), paired t‑test (secondary), Cohen’s d, KS statistics.  
  - **Output**: `data/processed/results/statistical_report.json` (matches `output.schema.yaml`).  
  - **Verification**:  
    1. JSON contains `wilcoxon`, optional `t_test`, `cohen_d`, and a list `ks_tests` with three comparisons.  
    2. Script aborts if Wilcoxon p‑value ≥ 0.05 or Cohen’s d < 0.5 (per SC‑001).  

- [ ] **T010** [P3] [US3] Perform **window‑size & derivative‑method sensitivity** (FR‑016). Sweep `window_size` ∈ {20, 30, 40} and derivative smoothing ∈ {none, moving‑average‑3}. Record impact on SNR (from T022) and detection performance.  
  - **Outputs**: `data/processed/results/window_derivative_sensitivity.csv` (`window_size`, `derivative_method`, `snr`, `wilcoxon_p`, `cohen_d`).  
  - **Verification**: CSV includes at least one configuration achieving `SNR > 1`.  

- [ ] **T011** [P4] [US4] Validate **resource constraints** for the complete pipeline (FR‑008).  
  - **Script**: `code/src/scripts/verify_resource_compliance.py` (runs after T006–T008).  
  - **Outputs**: `data/processed/results/resource_validation_report.md` containing peak RAM (MB) and total runtime (seconds).  
  - **Verification**:  
    1. Peak RAM < 7168 MB.  
    2. Runtime < 21600 seconds.  
    3. Script exits 0; otherwise the run is marked failed.  

- [ ] **T012** [P4] [US1] Execute the **MCMC robustness check** (FR‑018) on a representative subset of windows (e.g., the top 5 % with highest `alpha_deriv` variance).  
  - **Method**: NUTS sampling via PyMC; compare ADVI‑derived `alpha_deriv` to MCMC posterior mean.  
  - **Outputs**: `data/processed/results/mcmc_validation.csv` (`window_id`, `advi_alpha_deriv`, `mcmc_alpha_deriv`).  
  - **Verification**: Pearson correlation ≥ 0.9; if lower, set `validation_flag: false` and propagate to final report.  

---

## Phase 3 – Threshold calibration and sensitivity  

- [ ] **T009** [P3] [US3] Perform **threshold sensitivity analysis** on the normalized reconstruction‑error scores using the calibrated thresholds from T026.  
  - **Thresholds**: values defined in `config.yaml` → `[0.01, 0.05, 0.1]`.  
  - **Outputs**: `data/processed/results/sensitivity_report.parquet` (conforms to `sensitivity_report.schema.yaml`).  
  - **Verification**:  
    1. Exactly three rows (one per threshold).  
    2. `stability_flag` = True if any FP/FN rate spikes > 0.2 relative to the previous threshold.  

---

## Phase 4 – Reporting, figures, and finalisation  

- [ ] **T013** [P5] [US5] Generate **all study figures** directly from validated result artefacts.  
  - **Figures** (saved under `data/processed/results/figures/`):  
    1. Posterior α trajectory with injected‑anomaly timestamps.  
    2. Detection‑latency box‑plots for DP‑GMM vs baselines.  
    3. FP/FN vs threshold plot.  
    4. (Optional) Window‑size sensitivity heatmap.  
  - **Verification**: Each PNG exists, script `code/src/visualization/plot_all.py` runs without error, and the figure files are listed in `data/processed/results/figure_manifest.txt`.  

- [ ] **T015** [P7] [US4] Update the **project state hash** whenever the synthetic generator or sliding‑window logic changes (FR‑023).  
  - **Trigger**: Detect file modification timestamps of `code/src/data/synthetic_generator.py` and `code/src/data/windowing.py`.  
  - **Action**: Compute SHA‑256 of each file and write to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` under `artifact_hashes`.  
  - **Verification**: Script exits 0 and the YAML entries match the computed hashes.  

- [ ] **T016** [P6] [US4] Write the **final results report** (`data/processed/results/final_report.md`).  
  - **Content**:  
    1. Brief methods summary linking to `quickstart.md`.  
    2. SNR gate outcome (pass/fail).  
    3. All statistical test results (Wilcoxon, KS, Cohen’s d, bootstrap usage flag).  
    4. Threshold‑sensitivity findings (include FP‑rate range).  
    5. Resource‑validation summary.  
    6. Limitation notes (e.g., if SNR ≤ 1 or MCMC correlation < 0.9).  
    7. Community‑standard threshold justification (Cohen 1988) and observed FP‑rate range.  
    8. “Validation Deferred” statement if T020 produced a deferred‑by‑design report.  
  - **Verification**: Every numeric claim is traced to a file under `data/processed/results/` (checked via a grep‑cross‑reference script).  

- [ ] **T017** [P7] Create a **reproducible workflow document** (`quickstart.md`) **and** an orchestrating shell script `run_all.sh`.  
  - **`run_all.sh`** runs tasks in the exact required order, respecting all producer‑consumer dependencies:  

    ```bash
    #!/usr/bin/env bash
    set -euo pipefail

    # Phase 0
    python -m code.src.data.search_datasets          # T020
    python -m code.src.data.download_datasets         # T003
    python -m code.src.data.preprocessing             # T018
    python -m code.src.data.synthetic_generator        # T025
    python -m code.src.data.verify_synthetic          # T023
    python -m code.src.data.split                     # T021
    python -m code.src.scripts.run_pipeline           # T005 (minimal sanity run)

    # Phase 1
    python -m code.src.scripts.validate_config_schema # T001
    python -m code.src.scripts.restructure_code       # T002
    python -m code.src.evaluation.simulation          # T022
    python -m code.src.evaluation.prior_sensitivity   # T024

    # Phase 2
    python -m code.src.scripts.run_full_dp_gmm        # T006
    python -m code.src.models.baselines               # T007
    python -m code.src.services.threshold_calibrator   # T026
    python -m code.src.evaluation.bootstrap           # T019
    python -m code.src.scripts.statistical_tests      # T008
    python -m code.src.sensitivity.window_derivative  # T010
    python -m code.src.scripts.verify_resource        # T011
    python -m code.src.evaluation.mcmc_check          # T012

    # Phase 3
    python -m code.src.scripts.threshold_sensitivity  # T009

    # Phase 4
    python -m code.src.visualization.plot_all          # T013
    python -m code.src.scripts.update_state_hash      # T015
    python -m code.src.scripts.generate_final_report  # T016
    ```

  - **Verification**: Executing `./run_all.sh` on a fresh runner reproduces all artefacts listed in `final_report.md` and passes the test suite (`pytest`).  

---

## Dependency & Requirement Coverage  

| Spec/FR ID | Covered by Task(s) |
|------------|--------------------|
| FR‑001 – FR‑004 | T006, T007 |
| FR‑005 – FR‑006 | T008 |
| FR‑007 – FR‑009 | T001, T009, T010, T021, T026 |
| FR‑010 – FR‑015 | T008, T009, T010 |
| FR‑016 | T010 |
| FR‑017 / FR‑017b | T020 (search) → if none, deferred report |
| FR‑018 | T012 |
| FR‑019 | T021 (split) → T026 (calibration) |
| FR‑020 | T022 |
| FR‑021 – FR‑022 | T025 (generation) + T023 (verification) |
| FR‑023 | T015 |
| FR‑024 | T001 |
| FR‑008 – FR‑009 | T011, T001 |
| FR‑011 – FR‑012 | T019 (bootstrap) |
| FR‑014 – FR‑015 | T008 (KS tests) |
| FR‑016 | T010 |
| FR‑017 / FR‑017b | T020 |
| FR‑018 | T012 |
| FR‑019 | T021, T026 |
| FR‑020 | T022 |
| SC‑001 – SC‑008 | T008 (Cohen’s d, Wilcoxon), T009 (threshold stability), T011 (resource), T019 (bootstrap), T012 (MCMC correlation) |

All scientific requirements are now represented, and the pipeline can be executed end‑to‑end on real inputs before any paper‑stage handoff.  

---  

*All unchecked tasks are pending; checking a box will be done automatically by the CI verification step once the corresponding artefact passes its verification script.*  
