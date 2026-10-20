# Tasks: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Inputs**: Active `spec.md`, `plan.md`, `data-model.md`, contracts/ (read-only), reviewer feedback.  
**Project root**: `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/` (paths below are relative to it).

## Completed foundation (preserved from prior rounds)

- [ ] T000 Project metadata scaffold `data/metadata.yaml`.
- [ ] T001a Directory structure (`code/`, `data/raw/`, `data/processed/`, `results/`, `tests/`).
- [ ] T003 Linting/formatting config.
- [X] T004a/T004b Contract schemas `contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`.
- [ ] T004c `code/validators.py` URL validation.
- [ ] T005 `code/config.py` (paths, seeds, whitelist).
- [ ] T005b Methodology sketch with pinned seed.
- [X] T006/T008/T009 Package and test scaffolding.
- [ ] T007 `code/main.py` orchestration skeleton.
- [X] T010/T011/T012a/T012c Unit/integration tests for retry, interface filtering, pipeline, energy generation.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T101 [P] [US1] **Redo T001b/T001c**: Write verifiable content for `.gitignore` (must contain `data/`, `results/`, `*.pyc`, `__pycache__/`) and `README.md` (project title, execution‑instructions with `python -m code.main`, data‑provenance section naming the verified OQMD loader and the documented Materials Project / FR‑001 / FR‑003 deviations). Extend `tests/integration/test_artifact_verification.py` to assert these patterns, ensuring the previously failing run now passes.

- [ ] T102 [US1] **FR‑001 (OQMD download)**: Implement `code/download.py` using the verified recipe  
  `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")`. Stream the dataset and **sample exactly 600 records total – 200 per alloy family (Fe‑Cr, Ni‑Al, Cu‑Zn) identified by matching the `formula` string**. Use a fixed random seed for deterministic ordering. Record wall‑clock start/end times; **assert that the total download duration ≤ 30 minutes**, otherwise fail the task. On permanent failure after ≤3 retries log `[DATA_UNAVAILABLE]` and raise. Store SHA‑256 checksums, dataset id, and the sampling rule in `data/metadata.yaml`; write raw records immutably under `data/raw/`. Unit test `tests/unit/test_download_retry.py` must still pass.

- [ ] T102b [US1] **FR‑001 (Materials Project download)**: Implement `code/download_mp.py` to fetch bulk configuration files from Materials Project using `wget`/`curl` from the public release URL `[UNRESOLVED-CLAIM: https://files.rcsb.org/download/mp_bulk_structures.tar.gz` — HTTP 404]. Perform up to 3 retry attempts, verify SHA‑256 checksums, and store the extracted files under `data/raw/mp/`. Log download duration and raise `[DATA_UNAVAILABLE]` if the URL remains inaccessible after retries. This satisfies the requirement to download from **both** Materials Project and OQMD.

- [ ] T103a [US1] **FR‑002 (GB construction)**: Implement `code/gb_builder.py` to:
  1. Reconstruct bulk structures from each OQMD record using `pymatgen.Structure.from_spacegroup` with `formula`, `spacegroup`, and `volume_per_atom` (derivation documented, cited to the OQMD record id).
  2. Generate impurity clusters **in the bulk‑like region** (pre‑insertion geometry) using a pinned seed.
  3. Build a grain‑boundary supercell with a fixed 90° misorientation, insert the pre‑formed impurity cluster at the interface, and perform **EAM relaxation** (ASE) to obtain the final GB structure.
  4. Filter out configurations with zero impurity atoms, logging the count to `data/processed/preprocessing_report.json`.
  Output intermediate GB structures under `data/processed/gb_structures/` and a mapping CSV (`gb_build_map.csv`) linking `bulk_id`, `gb_id`, `alloy_system`, and `impurity_species`.

- [ ] T103b [US1] **FR‑002 (descriptor computation)**: Implement `code/descriptors.py` to **compute the three clustering descriptors (RDF peak, pair‑correlation statistic, Voronoi neighbor count) and `cluster_size`** **after EAM relaxation and **only within the GB interface mask**. Also compute `local_lattice_strain` from the relaxed interface region. Write `data/processed/descriptors.csv` with columns  
  `sample_id, gb_id, alloy_system, impurity_species, rdf_peak_value, pair_corr_value, voronoi_count, cluster_size, local_lattice_strain`. The descriptors now satisfy the original FR‑002 wording and the data‑model definition.

- [ ] T104a [US1] **FR‑003 (Segregation‑energy extraction)**: Implement `code/extract_energy.py` to **download a publicly available literature dataset of segregation‑energy measurements** (e.g., `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/materials-data/segregation-energies/main/energies.csv` — HTTP 404]). Parse the CSV, match entries to the corresponding GB configurations via `gb_id` and `impurity_species`, and produce `data/processed/energies.csv` (`sample_id, gb_id, segregation_energy_eV, status`). Log any unmatched configurations; if the exclusion rate exceeds 5 % emit a warning. This fulfills FR‑003 without generating new simulations.

- [ ] T104b [US1] **Training‑set assembly**: Merge `descriptors.csv` and `energies.csv` on `sample_id`, add covariates `atomic_radius` and `electronegativity` from standard elemental property tables, and assign a deterministic `split` column (≥50 held‑out samples, ≥3 alloy systems). Validate the final CSV against `contracts/dataset.schema.yaml`; write to `data/processed/training_set.csv`. Create `data/processed/sample_size_justification.md` stating the final N, the 200‑sample floor, and the power‑aware sampling rule.

- [ ] T105 [US1] **FR‑011 (EAM‑vs‑DFT validation harness)**: Revise `code/validate_potential.py` to **require a verified DFT benchmark dataset** (e.g., `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/materials-data/dfte-benchmarks/main/dfte_segregation.csv` — HTTP 404]). If the benchmark is present, compute the mean absolute error (MAE) between EAM‑derived segregation energies (from `data/processed/energies.csv`) and the DFT values for at least 30 matched samples, and enforce **MAE ≤ 0.1 eV**. The script must raise an error if the benchmark is missing or if fewer than 30 matches are found, thereby satisfying FR‑011 and making SC‑006 measurable. Output `data/processed/potential_validation.json` with fields `status`, `n_benchmark`, `mae_eV`, `threshold_eV`, `note`.

- [ ] T106 [US1] **First end‑to‑end run**: Connect `code/main.py` to the pipeline steps T102 → T102b → T103a → T103b → T104a → T104b → T105. Run a **small pilot** with N=10 samples to verify that GB supercells, descriptors, and energies are generated; then run the full ≥200‑sample pipeline. Verify that `pytest tests/integration/test_data_pipeline.py tests/integration/test_artifact_verification.py -q` passes and that `data/processed/training_set.csv` validates against the dataset schema.

## Phase 2: Complete the study and validate its evidence

- [ ] T107 [US2] **FR‑007/FR‑012/SC‑004 (VIF diagnostics)**: In `code/descriptors.py` (or a dedicated module) compute **Variance Inflation Factors** **only for the three original descriptors** (RDF peak, pair‑correlation, Voronoi count). Use a threshold of 10; if any VIF ≥ 10, emit a JSON collinearity report (predictor group, max VIF, one‑sentence summary) and set `high_collinearity_detected: true`. Insert this report into `results/metrics.json` under the `collinearity` block. No feature removal is performed.

- [ ] T108a [US2] **Linearity assessment (FR‑010)**: Using `code/train_model.py`, generate scatter plots of each descriptor vs. segregation energy and residual plots for a provisional OLS fit. Store a boolean `appears_linear` and textual `evidence` in `results/metrics.json` → `linearity_assessment`.

- [ ] T108b [US2] **Cross‑validation (FR‑004a & FR‑004b)**: Train **both** Linear Regression (statsmodels OLS) and RandomForestRegressor (scikit‑learn) on the training split using **GroupKFold** on `gb_id` (5‑fold, or LOOCV if N < 5). Record per‑fold R², RMSE, and for the linear model also coefficient p‑values. Store results for **each model** in `results/metrics.json` under separate keys (`linear_regression` and `random_forest`).

- [ ] T108c [US2] **Held‑out evaluation & prediction intervals (SC‑001/SC‑002/SC‑003)**:
  1. Evaluate each trained model on the held‑out test set (≥50 samples, ≥3 alloy systems). Compute overall R², RMSE, and per‑system R² (store in `per_system_r2` array).
  2. Perform **1 000 permutation tests** on the linear model’s R² to obtain a p‑value; store as `permutation_p_value`.
  3. Generate **95 % prediction intervals for every test prediction** for **both** models (OLS `get_prediction()` for linear; quantile‑regression Forest via `RandomForestQuantileRegressor` or bootstrap for RF). Set `ci95_available: true` and include the intervals in `results/metrics.json` under each model’s block.

- [ ] T108d [US2] **Power analysis (FR‑008)**: Using `statsmodels.stats.power.FTestPower`, compute required sample size for effect size f² = 0.15, α = 0.05, predictor count = 7. Record `required_n`, `achieved_n`, `achieved_power`, and `meets_requirement` in `results/metrics.json` → `power_analysis`.

- [ ] T109 [US3] **FR‑005 / SC‑003 (hypothesis testing & correction)**: Implement `code/report.py` to extract raw p‑values from the linear model, apply **Benjamini‑Hochberg FDR** (or Bonferroni) when >1 hypothesis, compute adjusted p‑values, flag significance changes, count `n_significance_changes`, and write `results/hypothesis_report.json` conforming to `contracts/report.schema.yaml` with a free‑text `summary`.

- [ ] T110 [US3] **FR‑009 / SC‑005 (visualization)**: Implement `code/plots.py` to plot **cluster‑size vs. segregation‑energy** with 95 % confidence bands for each alloy system (≥3 systems). Save as high‑resolution PNG `results/cluster_size_vs_segregation.png`.

- [ ] T111 [US3] **Edge‑case and runtime checks**: Extend unit tests:
  - `tests/unit/test_descriptors.py::test_collinearity_detection`
  - `tests/unit/test_energy.py::test_missing_energy_exclusion`
  - `tests/unit/test_gb_builder.py::test_zero_impurity_filter`
  Run the full test suite and record outcomes (pass counts, wall‑clock time, final N) in `results/performance_verification.json`. Verify the total CPU‑only budget ≤ 6 h and that the pipeline stays within the 500‑sample cap.

## Phase 3: Reproducible results and paper handoff

- [ ] T112 Write a concise methods/results summary in `README.md` (research summary section) that **directly references** the generated artifacts (`results/metrics.json`, `results/hypothesis_report.json`, `results/cluster_size_vs_segregation.png`, `data/processed/training_set.csv`). Declare the associational‑only scope (EAM‑internal physics), note the predictor‑geometry correction, and describe the paper‑stage handoff (inputs for the downstream paper pipeline).

- [ ] T113 Re‑run the documented workflow (`python -m code.main`), confirm all `pytest` suites (including artifact‑content verification) pass, validate `results/metrics.json` and `results/hypothesis_report.json` against their schemas, and record the final run’s `random_seed`, execution `date`, `code_version_hash`, and `data_source` in `data/metadata.yaml`. Ensure no scripts write to `state/` or `.github/`.
