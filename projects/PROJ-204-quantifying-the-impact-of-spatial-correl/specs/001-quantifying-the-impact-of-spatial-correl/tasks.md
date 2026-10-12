# Tasks: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Input**: Design documents from `specs/001-quantify-spatial-correlations/`  
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/

## Task format and paths

- `- [ ] T### [P?] [USx?] description with exact artifact paths`
- Paths are relative to the project directory (`code/`, `code/tests/`, `data/`).
- All result artifacts go under `data/` (e.g., `data/processed/`, `data/results/`, `data/report/`). Scripts must NOT write to `state/` — the platform's `llmxive_toolkit.paths` creates output folders on demand.

- Directory creation, logging setup, and installing common scientific packages (numpy, pandas, scipy, matplotlib, pytest) are never tasks: the platform's `llmxive_toolkit.paths` creates output folders on demand.

## Phase 1: Setup and first end-to-end analysis

- [ ] T100 [US1] **Data feasibility check with real, reachable sources.** Implement `code/data/feasibility.py` that programmatically probes candidate sources for EDS elemental maps paired with device performance metrics: (a) the NREL Perovskite Database (perovskitedatabase.com API export), (b) Zenodo records via the Zenodo REST API (`https://zenodo.org/api/records/?q=perovskite+EDS`), and (c) Materials Project API via `mp_api` for metadata fallback (FR-001). The script MUST attempt each real fetch (no try/except that silently substitutes data), record per-source HTTP status, record count, and whether EDS image files are programmatically linked to performance metrics, and write `data/results/data_feasibility_report.json` (source URL, reachable: true/false, n_records, eds_linked: true/false, evidence sample IDs). If no verified source with linked EDS maps is found, the script MUST write the report with `verdict: "halt"` and exit nonzero — no synthetic fallback; the plan's Data Availability Report path then applies. Document the runnable command (`python -m code.data.feasibility`) in the active feature's `quickstart.md`.
    - Verification: `data/results/data_feasibility_report.json` exists, contains real probed URLs and measured record counts, and no fallback-to-synthetic code path (`grep -r "synthetic\|mock\|random.rand" code/data/feasibility.py` returns nothing).

- [ ] T101 [US1] **Real data ingestion and unified dataset.** Implement `code/data/download.py` + `code/data/ingest.py` (completing the truncated file) that uses the verified source(s) from T100's report: download real EDS map files and performance metric records (PCE, J_sc, V_oc) to `data/raw/` (unchanged), align maps to a common pixel grid via the existing `code/data/align.py`, mask defects via the existing `code/preprocess/calibrate.py`, exclude samples with missing performance metrics (logging the specific excluded sample IDs and a warning per sample to `data/results/ingestion_log.txt`), and write the pre-filter unified dataset to `data/processed/unified_dataset.csv` with columns: `sample_id, Pb_map_path, I_map_path, MA_map_path, pce, j_sc, v_oc, mask_percentage, co_location_status, depth_validation_status, eds_status`. The `eds_status` column records `"complete"` for samples with successfully linked EDS maps and `"incomplete"` for samples where the fallback metadata was found but no EDS image could be retrieved (FR-001). Compute `ingestion_success_rate = n_processed / n_requested` and write it with per-sample exclusion reasons to `data/results/ingestion_stats.json`. The loader MUST raise on failed real fetches; never fall back to generated data. If the verified source yields fewer than 30 matched samples, proceed honestly and record the count — the power limitation is reported by T106, never compensated with fabricated samples.
    - Verification: `data/processed/unified_dataset.csv` exists with the exact column set, non-null `pce/j_sc/v_oc` for every row, and `eds_status` column populated; `data/results/ingestion_stats.json` contains the measured rate and excluded sample IDs.

- [ ] T101a [US1] **Flag incomplete EDS samples.** Extend the ingestion pipeline to write the `eds_status` column (see T101) and additionally generate `data/results/eds_flag_summary.json` summarizing counts of `"complete"` vs `"incomplete"` samples. This artifact directly satisfies the fallback‑flagging clause of FR‑001.
    - Verification: `data/results/eds_flag_summary.json` exists and correctly reflects the status distribution.

- [ ] T102 [P] [US2] **Spatial metric extraction module with correctness tests.** Complete `code/analysis/spatial_metrics.py` (currently truncated): load each aligned Pb/I/MA map from `data/processed/`, compute the 2‑D autocorrelation (`scipy.signal.correlate2d` or FFT‑based), fit exponential, Gaussian, and power‑law decay models with AIC‑based best‑fit selection (existing fit code may be reused), extract the 1/e correlation length, compute the 2‑D FFT integrated spectral power in the 0–0.1 cycles/pixel low‑frequency band, and flag "undefined" correlation lengths (decay not reached within image bounds) with `is_undefined=true` **and** `is_censored=false`. If the correlation length exceeds the image dimension, set `is_censored=true` and `is_undefined=false`, recording the image dimension as `censored_value`. Write per‑sample metrics to `data/processed/spatial_metrics.csv` with columns: `sample_id, element, correlation_length, best_fit_model, aic_score, low_freq_spectral_power, is_undefined, is_censored, censored_value`. Include focused unit tests in `code/tests/test_spatial_metrics.py` using synthetic Gaussian‑correlated test images with known ground‑truth correlation lengths, asserting deviation ≤ 5 % (SC‑001); synthetic images are permitted here only as test fixtures for the metric‑extraction code, never as analysis inputs.
    - Verification: `data/processed/spatial_metrics.csv` exists with all required columns populated from real maps; `pytest code/tests/test_spatial_metrics.py` passes.

- [ ] T102b [US2] **Composite spatial metric computation.** Extend the spatial‑metric extraction to compute a composite metric (average of normalized `correlation_length` and `low_freq_spectral_power` across the three elements) and append a row with `element="composite"` to `data/processed/spatial_metrics.csv`. Also add a column `composite_metric` for the composite rows.
    - Verification: `data/processed/spatial_metrics.csv` contains a row where `element="composite"` and the new `composite_metric` column is populated.

- [ ] T102c [US2] **Separate undefined/censored flagging.** Ensure the CSV from T102 includes distinct boolean columns `is_undefined` and `is_censored` as described above, matching the spec and data‑model distinction.
    - Verification: Columns `is_undefined` and `is_censored` are present and correctly populated.

- [ ] T102d [US2] **Merge unified dataset and spatial metrics into schema‑conformant dataset.** Join `data/processed/unified_dataset.csv` with `data/processed/spatial_metrics.csv` on `sample_id` and `element` to produce `data/processed/merged_dataset.csv` that contains **all** fields required by `specs/001-quantifying-the-impact-of-spatial-correl/contracts/dataset.schema.yaml` (including `pce`, `j_sc`, `v_oc`, `mask_percentage`, `co_location_status`, `depth_validation_status`, `eds_status`, `correlation_length`, `best_fit_model`, `low_freq_spectral_power`, `is_undefined`, `is_censored`, `censored_value`). This merged file will be the primary input for downstream statistical modeling.
    - Verification: `data/processed/merged_dataset.csv` validates against the dataset schema (all required properties present, no additional properties).

- [ ] T103 [US3] **First end-to-end thin analysis on real inputs.** Wire `code/main_pipeline.py` (existing entry point) to run feasibility → ingestion → validation filtering (existing `code/validation/co_location.py` and `code/validation/depth_check.py`, via the existing `code/modeling/filter.py`) → spatial metrics → a minimal Pearson/Spearman correlation between each element's correlation length and PCE using the existing `code/modeling/correlation.py`. Run it on the real dataset and write first‑pass results to `data/results/first_pass_correlations.json` with fields: `element, metric_type, pearson_r, pearson_p, spearman_r, spearman_p, n_samples`. Document the runnable command in `quickstart.md`.
    - Verification: the documented command executes end‑to‑end on real data and `data/results/first_pass_correlations.json` contains measured coefficients computed from `data/processed/merged_dataset.csv`.

- [ ] T104 [US3] **Full statistical modeling with multiple‑comparison correction and GAM.** Extend `code/modeling/correlation.py` runs to cover all element × metric combinations (Pb, I, MA, composite × correlation_length, spectral_power), applying Benjamini‑Hochberg correction across the family of tests and reporting raw and adjusted p‑values (FR‑004). Run the existing `code/modeling/gam.py` to record `gam_deviance_explained` per combination. Write results conforming to `specs/001-quantifying-the-impact-of-spatial-correl/contracts/results.schema.yaml` to `data/results/analysis_results.json` (element, metric_type, pearson_r, pearson_p, pearson_p_adj, spearman_r, spearman_p, spearman_p_adj, gam_deviance_explained, robustness_delta_r_max, n_samples, sensitivity_excluded). Verify p‑values against `scipy.stats` reference within ±0.001 (SC‑002).

- [ ] T104b [US3] **Correlation confidence‑interval generation.** Compute 95 % confidence intervals for Pearson and Spearman correlations for each element × metric pair and write them to `data/results/correlation_ci.json` (fields: `element`, `metric_type`, `pearson_ci_lower`, `pearson_ci_upper`, `spearman_ci_lower`, `spearman_ci_upper`). This satisfies Constitution VII without altering the immutable `results.schema.yaml`.
    - Verification: JSON file exists and CI values are consistent with the correlation coefficients.

- [ ] T104e [US3] **Merge analysis artifacts.** After T104, T105, and T104b have produced their respective JSON outputs, run a small merging script that combines `analysis_results.json`, `loo_robustness.json`, `sensitivity_analysis.json`, and `correlation_ci.json` into a final `data/results/analysis_results_complete.json` matching the schema (the schema already includes `robustness_delta_r_max` and `sensitivity_excluded`; CI fields are stored separately as per Constitution VII). Verification ensures the merged file validates against the results schema.
    - Verification: `data/results/analysis_results_complete.json` passes schema validation.

- [ ] T105 [US3] **Robustness: LOO‑CV and sensitivity analysis.** Run the existing `code/analysis/robustness.py` leave‑one‑out cross‑validation over the primary analysis dataset, recording Δr per removed sample and the max Δr per test (FR‑005, SC‑003), writing `data/results/loo_robustness.json`. Complete `code/modeling/sensitivity.py` (currently truncated): read the sensitivity threshold from a project‑level `config.yaml` under `code/` (not `state/`), compute correlation coefficients on both the pre‑filter dataset (T101) and the primary filtered dataset, report Δr and whether excluding depth‑confounded samples (FR‑008) alters the conclusion, writing `data/results/sensitivity_analysis.json`. Fix the missing `Tuple/Dict/Any` imports and implement the real `main()` CLI.
    - Verification: both JSON artifacts exist with measured Δr values; `python -m code.modeling.sensitivity` runs without import errors.

- [ ] T105a [US3] **Conditional exclusion based on sensitivity.** Using the `sensitivity_threshold` from `config.yaml`, generate `data/processed/filtered_dataset.csv` that excludes depth‑confounded samples when the sensitivity analysis indicates high sensitivity (as defined in FR‑008). Record the exclusion decision in `data/results/conditional_exclusion_log.txt`.
    - Verification: The filtered dataset is produced and the log reflects the applied rule.

- [ ] T106 [US3] **Statistical power assessment.** Implement `code/modeling/power.py` that computes the minimum detectable effect size for the achieved N (80 % power, α = 0.05 from `config.yaml`), flags results as `non‑definitive` when N < `config.min_sample_count` or when MDES exceeds the observed |r|, and records the power‑limitation statement required by the spec's edge‑case handling (<30 samples). Write `data/results/power_analysis.json` (n_samples, mdes, observed_r, definitive: true/false, limitation_text).
    - Verification: artifact exists with computed MDES matching the standard formula (verifiable against `statsmodels.stats.power` reference within tolerance).

- [ ] T106a [US3] **Create project configuration file.** Write `code/config.yaml` containing keys: `sensitivity_threshold: 0.2`, `min_sample_count: 30`, `alpha: 0.05`. Document the defaults in `quickstart.md`.
    - Verification: `code/config.yaml` exists and is readable by downstream tasks.

- [ ] T107 [US3] **Summary report generation.** Complete `code/report/generate.py` (currently truncated) to read the validated outputs above and generate `data/report/summary.csv` and `data/report/summary.pdf` with fields: correlation coefficient, p‑value (raw and BH‑adjusted), sample count, best‑fit decay model, AIC score, Δr max, ingestion_success_rate (from `data/results/ingestion_stats.json`), and sensitivity_delta_r (from T105). The report must be generated directly from the result artifacts — no manual transcription.
    - Verification: both report files exist, every row traces to a value in `data/results/analysis_results_complete.json` and the other result artifacts.

- [ ] T108 [P] **Project documentation.** Write `README.md` with usage instructions, example commands for each pipeline stage, dependency installation, and the data‑source provenance from T100; update the feature's `quickstart.md` to reflect the final runnable workflow.
    - Verification: `README.md` exists and its documented commands match the actual entry points.

## Phase 2: Complete the study and validate its evidence

- [ ] T109 **Methods/results account.** Write `data/results/methods_summary.md` describing the data source and sample counts, preprocessing and masking, metric extraction with best‑fit model distribution, statistical methods (correlation, BH correction, GAM, LOO‑CV, sensitivity, partial correlation), and the actual measured findings — including negative findings, undefined/censored correlation lengths, and power limitations — each linked to a specific output file under `data/results/` and `data/report/`.
    - Verification: every numeric claim in the summary cites an existing result artifact and matches its content.

- [ ] T110 **Full re‑run and paper‑stage handoff.** Re‑run the documented workflow from `data/raw/` inputs through `code/main_pipeline.py`, confirm all focused tests (`pytest code/tests/`) and artifact checks pass, and record the paper‑stage handoff in `data/results/paper_handoff.md`: required figures (autocorrelation decay examples, correlation scatter plots), tables (summary.csv contents), and the open limitations (EDS depth‑resolution confounding, sample count, chemical coupling of Pb/I/MA) that the paper must state.
    - Verification: a clean end‑to‑end re‑run reproduces identical result files (pinned seeds) and the handoff document names each required paper artifact.

## Dependencies

| Task | Depends on |
|------|-------------|
| T101 | T100 |
| T101a | T101 |
| T102 | T101 |
| T102b | T102 |
| T102c | T102 |
| T102d | T101, T102, T102b |
| T103 | T100, T101, T102d |
| T104 | T103 |
| T104b | T104 |
| T104e | T104, T105, T104b |
| T105 | T104 |
| T105a | T105, T106a |
| T106 | T105a |
| T106a | — (initial config creation) |
| T107 | T104e, T106, T108 |
| T108 | — |
| T109 | T107, T104e, T105a |
| T110 | T109, T108 |
