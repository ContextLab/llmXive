# Tasks: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Input**: Design documents from `specs/001-quantify-spatial-correlations/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/

## Task format and paths

- `- [ ] T### [P?] [USx?] description with exact artifact paths`
- Paths are relative to the project directory (`code/`, `code/tests/`, `data/`).
- All result artifacts go under `data/` (e.g., `data/processed/`, `data/results/`, `data/report/`). Scripts must NOT write to `state/` — the platform owns project state and derives artifact hashes at verification time.

## Phase 1: Setup and first end-to-end analysis

- [ ] T100 [US1] **Data feasibility check with real, reachable sources.** Implement `code/data/feasibility.py` that programmatically probes candidate sources for EDS elemental maps paired with device performance metrics: (a) the NREL Perovskite Database (perovskitedatabase.com API export), (b) Zenodo records via the `zenodo` REST API (`https://zenodo.org/api/records/?q=perovskite+EDS`), and (c) Materials Project API via `mp_api` for metadata fallback (FR-001). The script MUST attempt each real fetch, record per-source HTTP status, record count, and whether EDS image files are programmatically linked to performance metrics, and write `data/results/data_feasibility_report.json` (source URL, reachable: true/false, n_records, eds_linked: true/false, evidence sample IDs). If no verified source with linked EDS maps is found, the script MUST write the report with `verdict: "halt"` and exit nonzero — no synthetic fallback. Document the runnable command (`python -m code.data.feasibility`) in the active feature's `quickstart.md`.
    - Verification: `data/results/data_feasibility_report.json` exists, contains real probed URLs and measured record counts, and no fallback-to-synthetic code path (`grep -r "synthetic\|mock\|random.rand" code/data/feasibility.py` returns nothing).

- [ ] T101 [US1] **Real data ingestion and unified dataset.** Implement `code/data/download.py` + `code/data/ingest.py` (completing the truncated file) that uses the verified source(s) from T100's report: download real EDS map files and performance metric records (PCE, J_sc, V_oc) to `data/raw/` (unchanged), align maps to a common pixel grid via the existing `code/data/align.py`, mask defects via the existing `code/preprocess/calibrate.py`, exclude samples with missing performance metrics (logging the specific excluded sample IDs to `data/results/ingestion_log.txt`), and write the pre-filter unified dataset to `data/processed/unified_dataset.csv` with columns: sample_id, Pb_map_path, I_map_path, MA_map_path, pce, j_sc, v_oc, mask_percentage, co_location_status, depth_validation_status (FR-001, US-1 Scenarios 1–3). Compute `ingestion_success_rate = n_processed / n_requested` and write it with per-sample exclusion reasons to `data/results/ingestion_stats.json` (NOT `state/` — the platform owns state paths). The loader MUST raise on failed real fetches; never fall back to generated data.
    - Verification: `data/processed/unified_dataset.csv` exists with the exact column set, non-null pce/j_sc/v_oc for every row, and `data/results/ingestion_stats.json` contains the measured rate and excluded sample IDs.

- [ ] T102 [P] [US2] **Spatial metric extraction module with correctness tests.** Complete `code/analysis/spatial_metrics.py` (currently truncated): load each aligned Pb/I/MA map from `data/processed/`, compute the 2-D autocorrelation (`scipy.signal.correlate2d` or FFT-based), fit exponential, Gaussian, and power-law decay models with AIC-based best-fit selection (existing fit code may be reused), extract the 1/e correlation length, compute the 2-D FFT integrated spectral power in the 0–0.1 cycles/pixel low-frequency band, and flag "undefined" correlation lengths (decay not reached within image bounds) with `is_censored=true` and the image dimension as `censored_value` lower bound (FR-002, FR-003, US-2 Scenario 3). Write per-sample metrics to `data/processed/spatial_metrics.csv` with columns: sample_id, element, correlation_length, best_fit_model, aic_score, low_freq_spectral_power, is_censored, censored_value. Include focused unit tests in `code/tests/test_spatial_metrics.py` using synthetic Gaussian-correlated test images with known ground-truth correlation lengths, asserting deviation ≤ 5% (SC-001).
    - Verification: `data/processed/spatial_metrics.csv` exists with all required columns populated from real maps; `pytest code/tests/test_spatial_metrics.py` passes.

- [ ] T103 [US3] **First end-to-end thin analysis on real inputs.** Wire `code/main_pipeline.py` (existing entry point) to run feasibility → ingestion → validation filtering (existing `code/validation/co_location.py` and `code/validation/depth_check.py`, via the existing `code/modeling/filter.py`) → spatial metrics → a minimal Pearson/Spearman correlation between each element's correlation length and PCE using the existing `code/modeling/correlation.py`. Run it on the real dataset and write first-pass results to `data/results/first_pass_correlations.json` with fields: element, metric_type, pearson_r, pearson_p, spearman_r, spearman_p, n_samples. Document the runnable command in `quickstart.md`.
    - Verification: the documented command executes end-to-end on real data and `data/results/first_pass_correlations.json` contains measured coefficients computed from `data/processed/spatial_metrics.csv` joined to `data/processed/unified_dataset.csv`.

**Checkpoint**: The documented pipeline command executes on real inputs and its numerical outputs can be checked. No result may be written from expected or invented values.

## Phase 2: Complete the study and validate its evidence

- [ ] T104 [US3] **Full statistical modeling with multiple-comparison correction and GAM.** Extend `code/modeling/correlation.py` runs to cover all element × metric combinations (Pb, I, MA, composite × correlation_length, spectral_power), applying Benjamini-Hochberg correction across the family of tests and reporting raw and adjusted p-values (FR-004), and run the existing `code/modeling/gam.py` to record `gam_deviance_explained` per combination. Write results conforming to `specs/.../contracts/results.schema.yaml` to `data/results/analysis_results.json` (element, metric_type, pearson_r/p/p_adj, spearman_r/p/p_adj, gam_deviance_explained, n_samples). Verify p-values against `scipy.stats` reference within ±0.001 (SC-002).
    - Verification: `data/results/analysis_results.json` validates against the results schema and contains every element × metric combination with measured values.

- [ ] T105 [US3] **Robustness: LOO-CV and sensitivity analysis.** Run the existing `code/analysis/robustness.py` leave-one-out cross-validation over the primary analysis dataset, recording Δr per removed sample and the max Δr per test (FR-005, SC-003), writing `data/results/loo_robustness.json`. Complete `code/modeling/sensitivity.py` (currently truncated): read the sensitivity threshold from a project-level `config.yaml` under `code/` (not `state/`), compute correlation coefficients on both the pre-filter dataset (T101) and the primary filtered dataset, report Δr and whether excluding depth-confounded samples (FR-008) alters the conclusion, writing `data/results/sensitivity_analysis.json`. Fix the missing `Tuple/Dict/Any` imports and implement the real `main()` CLI.
    - Verification: both JSON artifacts exist with measured Δr values; `python -m code.modeling.sensitivity` runs without import errors.

- [ ] T106 [US3] **Statistical power assessment.** Implement `code/modeling/power.py` that computes the minimum detectable effect size for the achieved N (80% power, α = 0.05 from `config.yaml`), flags results as `non-definitive` when N < `config.min_sample_count` or when MDES exceeds the observed |r|, and records the power-limitation statement required by the spec's edge-case handling (<30 samples). Write `data/results/power_analysis.json` (n_samples, mdes, observed_r, definitive: true/false, limitation_text).
    - Verification: artifact exists with computed MDES matching the standard formula (verifiable against `statsmodels.stats.power` reference within tolerance).

- [ ] T107 [US3] **Summary report generation.** Complete `code/report/generate.py` (currently truncated) to read the validated outputs above and generate `data/report/summary.csv` and `data/report/summary.pdf` with fields: correlation coefficient, p-value (raw and BH-adjusted), sample count, best-fit decay model, AIC score, Δr max, ingestion_success_rate (from `data/results/ingestion_stats.json`), and sensitivity_delta_r (from T105) (FR-006). The report must be generated directly from the result artifacts — no manual transcription.
    - Verification: both report files exist, every row traces to a value in `data/results/analysis_results.json` and the other result artifacts.

- [ ] T108 [P] **Project documentation.** Write `README.md` with usage instructions, example commands for each pipeline stage, dependency installation, and the data-source provenance from T100; update the feature's `quickstart.md` to reflect the final runnable workflow.
    - Verification: `README.md` exists and its documented commands match the actual entry points.

## Phase 3: Reproducible results and paper handoff

- [ ] T109 **Methods/results account.** Write `data/results/methods_summary.md` describing the data source and sample counts, preprocessing and masking, metric extraction with best-fit model distribution, statistical methods (correlation, BH correction, GAM, LOO-CV, sensitivity), and the actual measured findings — including negative findings, undefined/censored correlation lengths, and power limitations — each linked to the specific output files under `data/results/` and `data/report/`.
    - Verification: every numeric claim in the summary cites an existing result artifact and matches its content.

- [ ] T110 **Full re-run and paper-stage handoff.** Re-run the documented workflow from `data/raw/` inputs through `code/main_pipeline.py`, confirm all focused tests (`pytest code/tests/`) and artifact checks pass, and record the paper-stage handoff in `data/results/paper_handoff.md`: required figures (autocorrelation decay examples, correlation scatter plots), tables (summary.csv contents), and the open limitations (EDS depth-resolution confounding, sample count, chemical coupling of Pb/I/MA) that the paper must state.
    - Verification: a clean end-to-end re-run reproduces identical result files (pinned seeds) and the handoff document names each required paper artifact.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstration |
|---|---|---|
| FR-001 (ingestion, alignment, fallback flagging) | T100, T101 | `data/results/data_feasibility_report.json`, `data/processed/unified_dataset.csv` |
| FR-002 (autocorrelation, decay fits, AIC) | T102 | `data/processed/spatial_metrics.csv`, `pytest code/tests/test_spatial_metrics.py` |
| FR-003 (low-frequency spectral power) | T102 | same CSV, `low_freq_spectral_power` column |
| FR-004 (Pearson/Spearman, BH, GAM) | T103, T104 | `data/results/analysis_results.json` |
| FR-005 (LOO-CV, Δr) | T105 | `data/results/loo_robustness.json` |
| FR-006 (CSV/PDF report) | T107 | `data/report/summary.csv`, `summary.pdf` |
| FR-007 (co-location validation) | T101, T103 (existing `code/validation/co_location.py`) | `co_location_status` column |
| FR-008 (depth flagging, sensitivity) | T101, T105 | `depth_validation_status` column, `data/results/sensitivity_analysis.json` |
| SC-001–SC-004 | T102, T104, T105, T101 | test pass, ±0.001 p-value match, Δr report, ingestion rate |

Execution order: T100 → T101 → T102 → T103 → (T104, T105 can follow T103; T105 needs T101's pre-filter dataset) → T106 → T107 → T109 → T110. T108 is parallel. Previously verified modules (`align.py`, `calibrate.py`, `co_location.py`, `depth_check.py`, `filter.py`, `correlation.py`, `gam.py`, `robustness.py`, `config.py`, `main_pipeline.py`, `models.py`) are preserved and consumed as-is; the rejected tasks were consolidated into T100–T107, each producing a deterministically verifiable file artifact. No task writes to `state/` or `.github/`; ingestion statistics moved to `data/results/ingestion_stats.json`.

## Revision behavior

Verified work (checked tasks in the prior list) is preserved. Rejected tasks were re-planned as consolidated, artifact-producing steps: directory-scaffolding tasks (T001/T005) are dropped (the platform's `llmxive_toolkit.paths` creates output folders on demand); linting setup (T003) is dropped as non-scientific; the failed data tasks (T010/T011/T014c/T015/T010b) are replaced by T100/T101 with real, named, reachable sources and fail-loudly loaders; truncated analysis/report code (T019/T021/T024/T031c/T032/T033) is completed within T102/T105/T106/T107 with concrete output files as the verification evidence.
