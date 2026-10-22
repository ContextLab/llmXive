# Tasks: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Input**: `spec.md`, `plan.md`, `data-model.md`, contracts, and any existing artifacts.  
All tasks follow the canonical format `- [ ] T### [P?] [USx?] description …` with exact artifact paths.  
Indented continuation lines list the concrete output, verification steps, and any required dependencies.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, fully‑real pipeline on a small but genuine subset of the public EDS + performance data, producing a verifiable end‑to‑end result. |

- [ ] T001 [P] [US1] **Data‑availability feasibility check** – implement `code/data/feasibility.py` that programmatically probes the verified “Doe et al., 2023, Open Perovskite EDS Repository” (HuggingFace dataset `doe2023/perovskite-eds`) and the NREL Perovskite Database for linked performance metrics.  
  - **Outputs**: `data/results/feasibility_report.json` containing for each source: URL, HTTP status, number of records found, count of samples with both EDS map and performance record, and a boolean `has_linked_eds`.  
  - **Verification**:  
    1. File exists and is valid JSON.  
    2. All `url` fields point to reachable HTTPS resources (no `synthetic`/`mock` strings).  
    3. `grep -r "synthetic\|mock\|random.rand" code/data/feasibility.py` returns no matches.  

- [ ] T002 [P] [US1] **Real‑data ingestion & unified dataset creation** – complete `code/data/download.py` and `code/data/ingest.py` to (a) download every EDS map referenced in the feasibility report, (b) download the matching device‑performance CSV/JSON, (c) align each map to a common 512 × 512 pixel grid (`code/data/align.py`), (d) mask defective pixels (`code/data/preprocess.py`), and (e) write a schema‑validated CSV.  
  - **Outputs**:  
    - `data/processed/unified_dataset.csv` (columns: `sample_id, pce, j_sc, v_oc, mask_percentage, eds_status`).  
    - `data/results/ingestion_stats.json` with `ingestion_success_rate`, per‑sample exclusion reasons, and total counts.  
  - **Verification**:  
    1. CSV validates against `specs/001-quantifying-the-impact-of-spatial-correl/contracts/dataset.schema.yaml`.  
    2. No `null` values in `pce`, `j_sc`, `v_oc`.  
    3. `eds_status` is `"complete"` for samples with a map, `"incomplete"` otherwise.  

- [ ] T003 [P] [US2] **Spatial‑metric extraction (autocorrelation, FFT, model fitting)** – finish `code/analysis/spatial_metrics.py` to load each aligned Pb, I, MA map from `data/processed/`, compute:  
    1. 2‑D autocorrelation (FFT‑based).  
    2. Fit exponential, Gaussian, and power‑law decay models, select best via AIC.  
    3. Extract the 1/e correlation length (or flag `is_undefined`).  
    4. Compute low‑frequency spectral power (0 – 0.1 cycles/pixel) from the 2‑D FFT.  
  - **Outputs**: `data/processed/spatial_metrics.csv` with columns  
    `sample_id, element, correlation_length, best_fit_model, aic_score, low_freq_spectral_power, is_undefined, is_censored, censored_value, mask_percentage`.  
  - **Tests**: add `code/tests/test_spatial_metrics.py` that generates synthetic Gaussian‑correlated images with known correlation lengths and asserts extracted lengths are within ±5 % (SC‑001).  
  - **Verification**:  
    1. CSV exists and contains a row for each element of every sample that has a map.  
    2. `pytest -q code/tests/test_spatial_metrics.py` passes.  

- [ ] T004 [P] [US2] **Composite spatial metric & merged dataset** – extend the metric script to (a) normalise each element’s correlation length by the maximum observed length for that element, (b) compute the primary composite metric as the arithmetic mean of the three normalised lengths, (c) append a row with `element="composite"` and a column `composite_spatial_metric`. Then join the unified performance CSV with the spatial‑metrics CSV on `sample_id` to produce a single, schema‑conformant file.  
  - **Outputs**: `data/processed/merged_dataset.csv` (covers every required field from `dataset.schema.yaml`, including `composite_spatial_metric`).  
  - **Verification**:  
    1. File validates against the dataset schema.  
    2. A row with `element="composite"` is present and `composite_spatial_metric` is non‑null for samples with at least one complete map.  

- [ ] T005 [P] [US3] **Thin end‑to‑end pipeline & first‑pass correlations** – wire `code/main_pipeline.py` to execute the ordered steps: feasibility → ingestion → validation (co‑location & depth checks already present) → spatial‑metric extraction → a minimal correlation step that computes Pearson and Spearman r and p‑values between each element’s correlation length (and the composite metric) and PCE.  
  - **Outputs**: `data/results/first_pass_correlations.json` (array of objects with `element, metric_type, pearson_r, pearson_p, spearman_r, spearman_p, n_samples`).  
  - **Documentation**: add the runnable command (`python -m code.main_pipeline`) to `quickstart.md`.  
  - **Verification**:  
    1. Command runs to completion on the CI runner (≤ 6 h).  
    2. JSON file exists and contains numeric fields for every element/composite pair.  

---

## Phase 2 – Complete study, validation, and handoff  

| Goal | Produce the full statistical evidence set, robustness checks, power analysis, and reproducible reports. |

- [ ] T006 [P] [US3] **Full statistical modeling with multiple‑comparison correction & GAM** – expand `code/modeling/correlation.py` to (a) evaluate all element × metric combinations (Pb, I, MA, composite × `correlation_length` and `low_freq_spectral_power`), (b) apply Benjamini‑Hochberg correction across the family of tests, (c) compute 95 % confidence intervals for each coefficient, and (d) store results in `data/results/analysis_results.json` following `results.schema.yaml`. Run `code/modeling/gam.py` to obtain `gam_deviance_explained` for each pair and merge into the same JSON.  
  - **Verification**:  
    1. All p‑values match `scipy.stats` outputs within ±0.001 (SC‑002).  
    2. Adjusted p‑values are present and BH‑corrected.  
    3. JSON validates against the results schema.  

- [ ] T007 [P] [US3] **Robustness (LOO‑CV) and sensitivity to depth‑confounded samples** – implement `code/analysis/robustness.py` to perform leave‑one‑out cross‑validation on the merged dataset, recording Δr for each removed sample and the maximum Δr (`robustness_delta_r_max`). Implement `code/modeling/sensitivity.py` to (a) compute the bulk‑surface discrepancy metric, (b) flag samples where the discrepancy correlates with PCE (Pearson r ≥ 0.30, p < 0.05), and (c) optionally exclude those samples per FR‑008.  
  - **Outputs**: `data/results/loo_robustness.json`, `data/results/sensitivity_analysis.json`, and a filtered dataset `data/processed/filtered_dataset.csv`. Also write `data/results/conditional_exclusion_log.txt`.  
  - **Verification**:  
    1. Both JSON files contain the expected fields (`delta_r`, `max_delta_r`, `sensitivity_excluded`).  
    2. The filtered CSV omits only the samples flagged by the sensitivity rule.  

- [ ] T008 [P] [US3] **Power analysis & configuration** – create `code/config.yaml` with keys `sensitivity_threshold: 0.2`, `min_sample_count: 30`, `alpha: 0.05`. Implement `code/modeling/power.py` that (a) reads the final sample count from the filtered dataset, (b) computes the minimum detectable effect size (MDES) for a two‑tailed Pearson test at 80 % power using `statsmodels.stats.power.NormalIndPower`, (c) compares MDES to the observed absolute correlation, and (d) writes `data/results/power_analysis.json` containing `n_samples`, `mdes`, `observed_r`, `definitive` (true only if power ≥ 0.8 and MDES ≤ |observed_r|), plus a human‑readable `limitation_text` when exploratory.  
  - **Verification**: JSON exists, MDES matches the analytical formula (checked against `statsmodels` within tolerance).  

- [ ] T009 [P] [US3] **Summary report generation (CSV + PDF)** – finish `code/report/generate.py` to ingest `analysis_results.json`, `loo_robustness.json`, `power_analysis.json`, and `ingestion_stats.json`, then produce:  
    - `data/report/summary.csv` with columns `element, metric_type, r_value, p_value, p_value_adj, ci_lower, ci_upper, sample_count, best_fit_model, aic_score, robustness_delta_r_max, ingestion_success_rate, power_definitive`.  
    - `data/report/summary.pdf` that tabulates the same information and includes a one‑page methods sketch.  
  - **Verification**: Both files exist; each row in the CSV can be traced back to a value in one of the upstream JSON artifacts.  

- [ ] T010 [P] **Project documentation & paper‑stage handoff** – write and commit:  
    1. `README.md` with full installation instructions, data‑source provenance (cite the Doe et al. dataset), and a quick‑start command list.  
    2. Update `quickstart.md` to reflect the final end‑to‑end command (`python -m code.main_pipeline`).  
    3. `data/results/paper_handoff.md` enumerating the required figures (e.g., exemplar autocorrelation decay plots, scatter plots of composite metric vs PCE), tables (the CSV summary), and explicit limitation statements (sample‑size, bulk‑surface confounding, depth‑resolution).  
  - **Verification**: All three markdown files exist; every command mentioned is present in the repository and runs without error.  

- [ ] T011 [P] **Methods & results narrative linked to artifacts** – author `data/results/methods_summary.md` that (a) describes the data‑acquisition pipeline, (b) details the spatial‑metric calculations (including model‑selection criteria), (c) outlines the statistical workflow (correlation, BH correction, GAM, linearity diagnostics), (d) reports the actual numeric findings (coefficients, CIs, p‑values, robustness Δr, power status), and (e) explicitly cites the originating artifact for each number (e.g., “Pearson r = ‑0.42 (95 % CI [‑0.58, ‑0.24]) from `analysis_results.json`”).  
  - **Verification**: Every numeric claim matches the corresponding value in the linked JSON/CSV file (checked by a simple script or manual spot‑check).  

---

## Dependencies

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T002 |
| T004 | T002, T003 |
| T005 | T001, T002, T003, T004 |
| T006 | T005 |
| T007 | T006 |
| T008 | T007 |
| T009 | T006, T007, T008 |
| T010 | T009 |
| T011 | T006, T007, T008, T009 |

--- 

*All tasks write only under `data/`, `code/`, or `results/` as required by the platform constitution. No task creates or modifies platform‑owned state files.*
