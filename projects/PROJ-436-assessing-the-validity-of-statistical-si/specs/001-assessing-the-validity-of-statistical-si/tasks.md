# Tasks: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Inputs**: `specs/001-assessing-the-validity-of-statistical-si/spec.md`, `specs/001-assessing-the-validity-of-statistical-si/plan.md`, existing code base, and the contracts directory.

The following checklist implements the complete, reproducible study while satisfying every functional and success‑criteria requirement.  Tasks are ordered to respect data flow; each item lists the concrete artifact path, the specification/user‑story it fulfills, and an observable verification step.

---

- [ ] **T001** [P] **[US-1]** *Download and verify real RCT/observational datasets*  
  **File**: `code/data_loader.py`  
  *Implementation*: Use `datasets.load_dataset` (HuggingFace) or direct HTTPS URLs to fetch three verified datasets (one genuine RCT, two observational). Compute SHA‑256 checksums, compare against `data/checksums/manifest.json`, abort on mismatch, and **skip** any dataset with N < 100 (log a warning). No synthetic fallback; failures raise exceptions.  
  *Verification*:  
   · Unit test `tests/unit/test_data_loader.py` asserts that each file is downloaded, checksum matches, and that a dataset with N < 100 is recorded as `FLAGGED` in the manifest.  
   · Running `python -c "from code.data_loader import load_all"` completes without error on the CI runner.

- [ ] **T002** [P] **[US-1]** *Prepare data: synthesize treatment/outcome where absent and enforce a true null hypothesis*  
  **File**: `code/preparation.py`  
  *Implementation*:  
   · Detect missing `treatment` column → create binary `treatment` ~ Bernoulli(0.5).  
   · Detect missing `outcome` column → generate continuous `outcome` ~ N(0,1) or binary via median split, preserving a correlation of r ≈ 0.3 ± 0.05 with covariates if required.  
   · **Permute** `treatment` (and `outcome` for MNAR) using a fixed seed to guarantee zero average effect before any missingness injection.  
  *Verification*:  
   · Unit test `tests/unit/test_preparation.py` checks that after preparation the treatment column is present, has mean ≈ 0.5, and that the correlation between outcome and covariates lies within the prescribed band.  
   · A sanity t‑test / logistic regression on the permuted data returns a p‑value > 0.5, confirming the null.

- [ ] **T003** [P] **[US-1]** *Generate exhaustive SimulationConfig objects*  
  **File**: `code/config.py`  
  *Implementation*:  
   · For each verified dataset, create configs for the three missingness mechanisms (MCAR, MAR, MNAR), eight missingness rates `{0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40}`, both outcome types (`continuous`, `binary`), and the three analysis methods (`CC`, `MI`, `IPW`).  
   · Set `seed` (incremental per config), `n_iterations = 15000`, `analysis_methods = ["CC","MI","IPW"]`.  
   · Validate each config against `contracts/simulation_config.schema.yaml`.  
  *Verification*:  
   · Test `tests/unit/test_config.py` confirms that the total number of generated configs equals `datasets × 3 × 8 × 2 = 48 × #datasets` and that every JSON file loads without schema errors.  

- [ ] **T004** [P] **[US-1]** *Simulate missing data according to MCAR, MAR, and MNAR*  
  **File**: `code/simulation.py`  
  *Implementation*:  
   · **MCAR** – mask entries uniformly at random to achieve the target rate.  
   · **MAR** – compute missingness probability as a logistic function of a selected observed covariate (e.g., `age`).  
   · **MNAR** – after permutation (see T002), compute missingness probability as a logistic function of the **permuted outcome** *and* the **permuted treatment** (joint dependence).  
   · Ensure the actual proportion of missing values per variable deviates ≤ 0.5 % from the target.  
  *Verification*:  
   · Unit test `tests/unit/test_simulation.py` verifies (i) the missingness proportion, (ii) that MCAR missingness is independent of covariates (using a chi‑square test), and (iii) that MAR/MNAR probabilities correlate with the designated predictor(s) (Spearman ρ > 0.4).  

- [ ] **T005** [P] **[US-3]** *Implement analysis methods (CC, MI, IPW) with correct test selection*  
  **File**: `code/analysis.py`  
  *Implementation*:  
   · **Complete‑Case (CC)** – drop rows with any missing value; for continuous outcomes run a two‑sample *t*‑test, for binary outcomes run **logistic regression** (fallback to chi‑square/Fisher when cell counts < 5).  
   · **Multiple Imputation (MI)** – use `miceforest` with `m=5` imputations, pool estimates via Rubin’s Rules, then apply the same test as CC.  
   · **Inverse Probability Weighting (IPW)** – fit a logistic missingness model on observed covariates, compute inverse‑probability weights, and perform weighted *t*‑test or weighted logistic regression accordingly.  
  *Verification*:  
   · Integration test `tests/integration/test_analysis_pipeline.py` runs each method on a tiny synthetic dataset with known null effect; asserts that CC produces an inflated error (≥ 0.12) under MNAR, while MI and IPW remain ≤ 0.06.  

- [ ] **T006** [P] **[US-1]** *Monte‑Carlo engine: run ≥ 15 000 iterations per condition and persist iteration‑level artifacts*  
  **File**: `code/main.py`  
  *Implementation*:  
   · Iterate over every `SimulationConfig`. For each, execute the following pipeline **(a)** load prepared data, **(b)** apply missingness (T004), **(c)** run each analysis method (T005).  
   · Record per‑iteration results as `ErrorMetric` (to `data/processed/error_metrics.parquet`) and `PValueDistribution` (to `data/processed/p_value_distribution.parquet`).  
   · Process iterations in batches of 1 000 to keep RAM < 2 GB; after each batch, write to Parquet and update a checkpoint file `data/checkpoints/{config_hash}.ckpt` so the job can resume if the CI wall‑time is reached.  
   · Use `joblib.Parallel(n_jobs=2)` to parallelise batches across the two free‑tier CPU cores.  
  *Verification*:  
   · After a test run with `n_iterations=1000`, confirm that both Parquet files contain exactly 1 000 rows and that each row validates against its respective schema (`error_metric.schema.yaml`, `p_value_distribution.schema.yaml`).  

- [ ] **T007** [P] **[US-2]** *Aggregate metrics and produce SimulationOutput records*  
  **File**: `code/metrics.py`  
  *Implementation*:  
   · Load the iteration‑level Parquet files, group by `config_id` and `method`.  
   · Compute **empirical Type I error** = proportion of `rejected` flags.  
   · Perform **Kolmogorov‑Smirnov (KS) test** of the p‑value distribution against Uniform(0,1) (α = 0.05) and record the p‑value.  
   · Set `tipping_point_flag = (empirical_type1_error > 0.055)`.  
   · For each config, compute `cc_mi_ratio = error_CC / error_MI` and `error_rate_IPW`.  
   · Conduct **McNemar’s test** comparing per‑iteration rejection outcomes of CC vs. MI and CC vs. IPW; store `mcnemar_p_value`.  
   · Generate a **paired bootstrap** (2 000 resamples) of the error‑rate ratio to obtain a 95 % confidence interval (`ratio_bootstrap_ci`).  
   · Set `validated_tipping_point = (ratio_bootstrap_ci[0] > 2) and (mcnemar_p_value < 0.05)`.  
   · **Verification of Success Criteria**:  
   - Assert SC‑001: for MCAR configurations, `empirical_type1_error ≤ 0.06`.  
   - Assert SC‑003: KS p‑value > 0.05 (uniformity not rejected).  
   - Assert SC‑005: `ratio_bootstrap_ci[0] > 2` and `mcnemar_p_value < 0.05`.  
   · Write a JSON array `data/processed/simulation_outputs.json` conforming to `simulation_output.schema.yaml`.  
  *Verification*: Unit test `tests/unit/test_metrics.py` validates all computed fields and confirms that the three success‑criterion checks pass (or appropriately flag failures).

- [ ] **T008** [P] **[US-2]** *Generate summary CSV and report files*  
  **File**: `code/report.py`  
  *Implementation*:  
   · Load `simulation_outputs.json`.  
   · Create a human‑readable CSV `data/processed/tipping_points.csv` summarising `dataset_id`, `mechanism`, `missing_rate`, all three error rates, `ks_p_value_CC`, `tipping_point_flag`, `validated_tipping_point`, and `validation_status`.  
   · Produce a concise markdown summary `data/processed/summary.md` that lists identified tipping points per mechanism and highlights any flagged conditions.  
  *Verification*: Integration test `tests/integration/test_report.py` asserts that the CSV contains rows for every mechanism, that at least one MNAR row has `tipping_point_flag = true`, and that the markdown file is non‑empty.

- [ ] **T009** [P] **[US-3]** *Generate figures and tables for the manuscript*  
  **File**: `code/visualize.py`  
  *Implementation*:  
   · Plot **Type I error vs. missingness rate** curves for each mechanism, overlaying CC, MI, and IPW lines; mark identified tipping points with a red triangle.  
   · Plot **error‑rate ratio bootstrap CI** as a shaded region for CC vs. MI.  
   · Export figures to `figures/error_rate_curves.png`, `figures/ratio_bootstrap.png`.  
   · Create a summary table `figures/tipping_points_table.png` (rendered from `tipping_points.csv`).  
  *Verification*: Test script `tests/unit/test_visualize.py` runs the module on a subset of `simulation_outputs.json` and checks that the PNG files exist and have size > 10 KB.  

- [ ] **T010** [P] **[Documentation]** *Add automated reproducible workflow verification*  
  **Files**: `README.md`, `specs/001-assessing-the-validity-of-statistical-si/quickstart.md`, `tests/integration/test_quickstart.py`  
  *Implementation*:  
   · Quick‑Start commands are scripted; `test_quickstart.py` executes the full pipeline (`data_loader → preparation → config → main → report → visualize`) and asserts that the expected artifact files (`simulation_outputs.json`, `tipping_points.csv`, PNG figures) exist and have non‑zero size.  
   · The README/quickstart now reference this automated test as the verification step.  
  *Verification*: CI runs `pytest -q tests/integration/test_quickstart.py`; a zero exit code indicates successful end‑to‑end execution.

- [ ] **T011** [P] **[US-1]** *Reproducibility check* *Validate that a fresh execution reproduces results within tolerance*  
  **File**: `code/reproducibility_check.py`  
  *Implementation*:  
   · Delete `data/processed/` and `data/checkpoints/` directories, then invoke the full pipeline (`data_loader → preparation → config → main → report → visualize`).  
   · Load the newly generated `simulation_outputs.json` and compare each numeric field to the reference version stored in `reference/simulation_outputs.json` using absolute tolerance 0.005.  
   · Exit with status 0 if all comparisons pass; otherwise raise an AssertionError listing mismatched fields.  
  *Verification*: CI step runs `python -m code.reproducibility_check` and expects a zero exit code; any deviation fails the pipeline.  

- [ ] **T012** [P] **[US-2]** *Estimate statistical power under alternative effect*  
  **File**: `code/power.py`  
  *Implementation*:  
   · For each `SimulationConfig`, generate an alternative dataset with a predefined effect size (Cohen's d = 0.5 for continuous outcomes, odds ratio = 1.5 for binary outcomes).  
   · Run the same missingness mechanisms and analysis methods (using a reduced iteration count of 2 000 for speed).  
   · Compute empirical power as the proportion of iterations where the null hypothesis is correctly rejected (p < 0.05).  
   · Verify that power ≥ 0.80 for every condition; if a condition falls below, add a `power_flag = false` entry in the corresponding `SimulationOutput` record.  
  *Verification*: Unit test `tests/unit/test_power.py` validates power calculation on a known scenario where the true effect is strong enough to yield > 0.90 power.  

--- 

**Dependency Mapping**

| Spec / FR / SC | Satisfying Task(s) |
|----------------|--------------------|
| FR‑001 (real datasets) | T001 |
| FR‑002 (missingness mechanisms) | T004 |
| FR‑003 (≥ 15000 iterations) | T006 |
| FR‑004 (tipping‑point rule) | T008 |
| FR‑005 / FR‑007 (CC, MI, IPW, correct test selection) | T005 |
| FR‑010 (p‑value distribution artifact) | T006 |
| FR‑011 (SimulationOutput artifact only) | T007, T008, T012 |
| SC‑001 (CC error ≤ 0.06 under MCAR) | T007 (verification) |
| SC‑002 (tipping point detection) | T008 |
| SC‑003 (KS uniformity test) | T007 (verification) |
| SC‑004 (statistical power ≥ 0.80) | T012 |
| SC‑005 (ratio > 2, McNemar significance) | T007 (verification) |
| US‑1 (simulate missing data & compute empirical Type I error) | T001‑T006 |
| US‑2 (sensitivity analysis & tipping points) | T006‑T008 |
| US‑3 (compare CC vs. MI & IPW) | T005‑T009 |
| Documentation & CI automation | T010 |
| Reproducibility assurance | T011 |

The ordering respects data flow: **T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012**. All tasks are unchecked and ready for implementation and verification.  
