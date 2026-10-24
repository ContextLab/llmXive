# Tasks: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, verifier rejections, reviewer feedback.

The checklist implements **FR‑001 – FR‑014** and **SC‑001 – SC‑005**. All tasks respect data‑flow ordering, write only to project‑owned paths, and avoid any synthetic fallback for real‑data fetches.

---

## Phase 1 – Environment, data acquisition, and validation inputs

- [ ] T001 **Establish a reproducible environment and global configuration**  
  *Files*: `code/src/env_check.py`, `code/src/config.py`, `code/tests/test_env_check.py`  
  *Actions*  
  1. Write `env_check.py` that imports the full scientific stack (`pandas`, `numpy`, `scikit‑learn`, `torch` CPU‑only, `statsmodels`, `pyyaml`, `pytest`, `jsonschema`, `psutil`, `openml`, `ucimlrepo`) and exits 0 only if all imports succeed.  
  2. Create `config.py` defining `SEED = 42`, proxy coefficients `K_STEEL = 0.8`, `K_ALUMINUM = 0.6`, psi‑to‑MPa factor `PSI_TO_MPA = 0.00689476`, and all path constants used downstream.  
  *Verification*: `pytest code/tests/test_env_check.py` asserts exit 0 and presence of `SEED` in `config.py`.

- [ ] T001-1 **Pin dependencies, implement timing, and document quickstart**  
  *Files*: `requirements.txt`, `code/src/timing.py`, `quickstart.md`, `data/raw/checksums.json`  
  *Actions*  
  1. Pin every dependency in `requirements.txt` (e.g., `pandas==2.2.*`, `torch==2.3.*+cpu`, `openml==0.14.*`, etc.).  
  2. Provide a `phase_timer` context manager in `code/src/timing.py` that records wall‑clock seconds and peak RSS (via `psutil`) to `data/results/runtime_summary.csv`.  
  3. Document the single command `python -m code.src.run_e2e` in `quickstart.md`.  
  4. Initialize `data/raw/checksums.json` as an empty JSON object to be populated by acquisition tasks.  
  *Verification*: Verify `requirements.txt` is non-empty and `quickstart.md` contains the e2e command.

- [ ] T014 **Acquire external datasets from OpenML and UCI (fail‑loud, no synthetic fallback)**  
  *Files*: `code/src/acquire_external.py`, `data/external/acquisition_log.json`, `code/tests/test_acquire.py`  
  *Actions*  
  1. Use the `openml` Python client to list and download datasets with tags `fatigue`, `residual stress`, `steel`, `aluminum`. Use `ucimlrepo` similarly.  
  2. For each candidate, flatten structures and validate against `contracts/dataset_schema.yaml`.  
  3. Write matching datasets to `data/raw/external_<name>.csv`, add a `source` column, compute SHA‑256 checksums, and update `data/raw/checksums.json`.  
  4. Record the full query trail in `acquisition_log.json`. The script must raise an exception on any network or parsing error; it must **not** fall back to synthetic data.  
  *Verification*: `pytest code/tests/test_acquire.py` checks that `acquisition_log.json` exists and that any acquired files match their checksums in `checksums.json`.

- [ ] T015 **Generate a deterministic synthetic dataset for pipeline validation only**  
  *Files*: `code/src/data/gen_synthetic.py`, `data/raw/synthetic_fatigue.csv`, `code/tests/test_gen_synthetic.py`  
  *Actions*  
  1. Implement `gen_synthetic.py` using `numpy.random.default_rng(42)`. Produce **10 000** rows conforming to `contracts/dataset_schema.yaml`.  
  2. Set `source="synthetic"` for every row.  
  3. Compute SHA‑256 checksum of the resulting file and update `data/raw/checksums.json`.  
  *Verification*: `pytest code/tests/test_gen_synthetic.py` asserts file existence, row count = 10 000, and byte‑reproducibility.

---

## Phase 2 – Ingestion, preprocessing, and thin end‑to‑end run

- [ ] T002 **Ingest all raw files, harmonise units, median‑impute, compute proxy, and validate schema**  
  *Files*: `code/src/ingest.py`, `data/processed/unified_fatigue.csv`, `data/processed/missing_flags.json`, `logs/proxy_clamp.log`, `code/tests/test_ingest.py`  
  *Actions*  
  1. Load the bundled verification CSV, the synthetic CSV, and all external CSVs produced by T014. Verify each file’s SHA‑256 against `checksums.json`; raise on mismatch.  
  2. Convert residual‑stress units using the `stress_unit` column (psi → MPa using `config.PSI_TO_MPA`).  
  3. Median‑impute missing numeric columns; record original missingness in `missing_flags.json`.  
  4. Compute the **linear proxy** for **all rows** as required by FR-003:  
     `σ_res = k · heat_input · cooling_rate`  
     (k = 0.8 for steel, 0.6 for aluminum).  
     Populate `residual_stress_proxy`. Set `is_proxy = True` only when `residual_stress_measured` is missing.  
  5. Clamp negative proxy values to `0.01 MPa` and log the count to `logs/proxy_clamp.log`.  
  6. Add a per‑row SHA‑256 checksum column. Validate the full dataframe against `contracts/dataset_schema.yaml`; abort on failure.  
  7. Write `data/processed/unified_fatigue.csv`.  
  *Verification*: `pytest code/tests/test_ingest.py` asserts: (a) checksum verification, (b) correct MPa conversion, (c) linear proxy values match formula, (d) schema validation passes.

- [ ] T003 **Compute proxy‑measured agreement and run a thin end‑to‑end pipeline**  
  *Files*: `code/src/proxy_agreement.py`, `code/src/run_e2e.py`, `data/results/proxy_agreement.csv`, `data/results/e2e_summary.json`, `code/tests/test_e2e.py`  
  *Actions*  
  1. In `proxy_agreement.py`, compute Pearson *r* and *R²* between `residual_stress_measured` and `residual_stress_proxy` for overlapping rows. Write to `proxy_agreement.csv` with the caveat `"deterministic (linear) proxy – descriptive only"`.  
  2. `run_e2e.py` orchestrates: **Env → Acquire → Synthetic → Ingest → Proxy‑agreement**. Wrap each phase in `timing.phase_timer`.  
  3. Script exits 0 only if all phases succeed and unit tests pass.  
  *Verification*: `pytest code/tests/test_e2e.py` checks that `e2e_summary.json` is produced and `runtime_summary.csv` is populated.

---

## Phase 3 – Feature construction, model training, and predictive comparison

- [ ] T004 [P] **Construct balanced Feature Set A & B (identical rows), B‑full, and Feature Set C**  
  *Files*: `code/src/build_features.py`, `data/processed/balanced_measured.csv`, `data/processed/feature_set_A.csv`, `data/processed/feature_set_B.csv`, `data/processed/feature_set_B_full.csv`, `data/processed/feature_set_C.csv`, `code/tests/test_features.py`  
  *Actions*  
  1. Filter `unified_fatigue.csv` for `is_proxy == False` and down‑sample to balance steel and aluminum counts (`SEED=42`) → `balanced_measured.csv`.  
  2. **Feature Set A**: Process parameters only from balanced subset.  
  3. **Feature Set B**: Process parameters + measured stress from the same balanced subset (identical rows/order as Set A).  
  4. **Feature Set B‑full**: Full dataset; use measured stress if available, otherwise proxy.  
  5. **Feature Set C**: Full dataset; process parameters + material properties + stress (measured or proxy).  
  6. Standardise numeric features and persist scalers under `code/models/scalers/`.  
  *Verification*: `pytest code/tests/test_features.py` asserts identical row counts for A and B, and that B contains no proxy rows.

- [ ] T005 [P] **Train RF, GBM, and shallow NN with 5‑fold CV and held‑out test evaluation**  
  *Files*: `code/src/train.py`, `data/results/model_performance.csv`, `code/models/<feature_set>/<algorithm>/`, `code/tests/test_train.py`  
  *Actions*  
  1. Define a 10‑combination hyper‑parameter grid for RF, GBM, and NN (1 hidden layer, ≤500 epochs).  
  2. Perform 5‑fold CV stratified by `material_class` on balanced subset (Sets A, B) and full dataset (B-full, C).  
  3. Select best combo by mean CV‑MAPE, retrain, and save models to `code/models/<feature_set>/<algorithm>/model.pt`.  
  4. Split balanced measured subset into train (80%) / test (20%) (seed 42). Compute test MAPE & R²; write to `model_performance.csv`.  
  5. Enforce hard limit of 3600 s for NN training.  
  *Verification*: `pytest code/tests/test_train.py` checks for model existence and that NN training time ≤ 3600s.

- [ ] T006 [P] **Statistical comparison of Set A vs Set B per material class (Constitution‑VII)**  
  *Files*: `code/src/wilcoxon_compare.py`, `data/results/wilcoxon_results.csv`, `code/tests/test_wilcoxon.py`  
  *Actions*  
  1. Compute absolute errors for Models A vs B on identical test rows (measured stress only).  
  2. Run Wilcoxon signed‑rank test and paired t‑test per material class/algorithm. Apply Bonferroni correction (α = 0.05/3).  
  3. Implement improvement‑claim gate: `improvement_claim_supported = True` only if (i) MAPE reduction ≥ 10% AND (ii) both Wilcoxon and t-test p‑values < 0.05.  
  4. Write results to `wilcoxon_results.csv`.  
  *Verification*: `pytest code/tests/test_wilcoxon.py` validates the boolean flag logic using a known-error fixture.

- [ ] T007 [P] **Cross‑material transfer evaluation with permutation testing (FR‑009, FR‑011)**  
  *Files*: `code/src/cross_material.py`, `data/results/cross_material.csv`, `code/tests/test_cross_material.py`  
  *Actions*  
  1. Train on steel, test on aluminum (and vice-versa) using best hyper-parameters.  
  2. Compute `delta_mape = MAPE_other - MAPE_same`.  
  3. Perform 10,000‑permutation test for `delta_mape` significance. Apply Holm‑Bonferroni correction.  
  4. Write to `cross_material.csv`.  
  *Verification*: `pytest code/tests/test_cross_material.py` checks for finite delta_mape and p-values in [0,1].

---

## Phase 4 – Mediation analysis

- [ ] T008 **Power‑analysis validation and sample size check**  
  *Files*: `code/src/power_analysis.py`, `data/results/mediation_validation.json`, `code/tests/test_power.py`  
  *Actions*  
  1. Compute required sample size for mediation (f² = 0.15, α = 0.05, power = 0.80) → ≈ 45.  
  2. Count rows with `is_proxy == False` from real external sources.  
  3. Produce `mediation_validation.json` recording `n_measured` and whether the sample size meets the ≥ 45 requirement.  
  4. If `n_measured < 45`, the script must raise a `ValueError` indicating insufficient power for mediation, causing the pipeline to fail (fail-loud).  
  *Verification*: `pytest code/tests/test_power.py` confirms that a fixture with < 45 measured rows raises a ValueError.

- [ ] T009 **Bootstrap mediation analysis on the measured‑stress subset (FR‑006, FR‑007)**  
  *Files*: `code/src/boot_mediation.py`, `data/results/mediation_summary.csv`, `figures/mediation_forest.png`, `code/tests/test_mediation.py`  
  *Actions*  
  1. Restrict to rows where `is_proxy == False` and `source` is a real external dataset.  
  2. Define exposure `P = z(heat_input)·z(cooling_rate)`.  
  3. Fit a‑path (P + controls → stress) and b‑path (stress + P + controls → fatigue life). Controls include elastic modulus, yield strength, and material class.  
  4. Perform 10,000 bootstrap resamples (seed 42) to estimate indirect effect, direct effect, and proportion mediated. Compute 95% bias‑corrected CIs.  
  5. Compute VIF for predictors; flag any VIF > 5 in `mediation_summary.csv`.  
  6. Produce forest‑plot PNG (`figures/mediation_forest.png`) with the caption `"associational – no causal identification"`.  
  *Verification*: `pytest code/tests/test_mediation.py` checks that the CSV contains finite CI bounds and the forest plot exists.

---

## Phase 5 – Reporting, reproducibility, and handoff

- [ ] T010 **Generate all research figures**  
  *Files*: `code/src/generate_figures.py`, `figures/mape_bar.png`, `figures/proxy_scatter.png`, `figures/cross_material.png`, `code/tests/test_figures.py`  
  *Actions*  
  1. Generate MAPE per feature set bar chart (`figures/mape_bar.png`).  
  2. Generate proxy‑measured scatter plot with regression line (`figures/proxy_scatter.png`).  
  3. Generate cross‑material ΔMAPE bar chart (`figures/cross_material.png`).  
  *Verification*: `pytest code/tests/test_figures.py` asserts that all three PNG files exist and have non-zero size.

- [ ] T010-1 **Synthesize consolidated results report**  
  *Files*: `code/src/generate_report.py`, `paper/results_report.md`, `code/tests/test_report.py`  
  *Actions*  
  1. Aggregate all CSV/JSON artifacts into `paper/results_report.md`.  
  2. Interpret SC‑001 – SC‑004 results, report the improvement‑claim gate result from T006, and discuss the linear proxy circularity caveat.  
  3. Reference all figures from T010 and the mediation plot from T009.  
  *Verification*: `pytest code/tests/test_report.py` asserts the markdown file exists and contains references to all generated figures.

- [ ] T011 **End‑to‑end reproducibility verification (FR‑010, SC‑005)**  
  *Files*: `code/src/repro_check.py`, `data/results/reproducibility_report.txt`, `code/tests/test_repro.py`  
  *Actions*  
  1. Re‑compute SHA‑256 checksums for all raw files and compare against `checksums.json`.  
  2. Re‑run deterministic synthetic generator and confirm checksum match.  
  3. Verify `config.SEED` is used in all stochastic steps.  
  4. Confirm total wall‑clock ≤ 6 h and peak RAM ≤ 7 GB via `runtime_summary.csv`.  
  5. Re‑execute `python -m code.src.run_e2e` and verify final artifacts are byte‑identical to originals.  
  6. Write `reproducibility_report.txt` ending with `ALL CHECKS PASSED`.  
  *Verification*: `pytest code/tests/test_repro.py` checks that the report contains `ALL CHECKS PASSED`.

- [ ] T012 **Create paper‑stage handoff documentation**  
  *Files*: `paper/paper_handoff.md`, `code/tests/test_handoff.py`  
  *Actions*  
  1. List every artifact required for manuscript preparation (CSVs, JSONs, figures, report).  
  2. Provide the exact command to regenerate the full analysis and the location of `requirements.txt`.  
  *Verification*: `pytest code/tests/test_handoff.py` asserts the file exists and all listed paths resolve.