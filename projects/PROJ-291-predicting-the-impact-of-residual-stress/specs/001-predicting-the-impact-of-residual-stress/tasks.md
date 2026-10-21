# Tasks: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The checklist implements the technical schema requirements of FR‑001 – FR‑014 and SC‑001 – SC‑005 under the verified scope (bundled verification CSV + deterministic synthetic dataset). It explicitly flags the unavailability of external repositories for formal spec revision in T014. All tasks respect data‑flow ordering, use only project‑owned paths, and avoid any fabricated data sources.

---

## Phase 1 – Environment, data ingestion, and early end‑to‑end run  

- [ ] T001 **[P] [US1] Establish runnable environment, global config, and pin dependencies**  
  *Files*: `quickstart.md`, `code/src/env_check.py`, `code/src/config.py`, `requirements.txt`, `data/raw/checksums.json`  
  *Actions*  
  – Implement `code/src/env_check.py` that imports the full scientific stack (`pandas`, `numpy`, `scikit‑learn`, `torch` CPU‑only, `statsmodels`, `pyyaml`, `pytest`, `jsonschema`) and exits with code 0 only if all imports succeed.  
  – Create `code/src/config.py` to centrally define `SEED = 42` and other global constants to ensure reproducibility (Constitution I).  
  – Write `requirements.txt` that pins **all** packages used downstream (e.g., `pandas==2.2.*`, `numpy==1.26.*`, `scikit‑learn==1.5.*`, `torch==2.3.*+cpu`, `statsmodels==0.14.*`, `pyyaml==6.0.*`, `pytest==8.2.*`, `jsonschema==4.23.*`).  
  – Compute SHA‑256 checksums of the two bundled raw inputs (`data/raw/pipeline_verification.csv`, `data/raw/synthetic_fatigue.csv`) and store them in `data/raw/checksums.json`. The loader in T002 must verify these hashes and **raise** on mismatch (no synthetic fallback).  
  – Add a single‑command usage example to `quickstart.md` (e.g., `python -m code.src.run_e2e`).  
  *Verification*: `pytest code/tests/test_env_check.py` asserts that the script exits 0, that `config.py` defines `SEED`, and that recorded checksums match files on disk.

- [ ] T002 **[P] [US1] Implement technical data ingestion, harmonisation, and proxy computation**  
  *File*: `code/src/ingest.py`  
  *Actions*  
  – Load **only** the two bundled raw files; on any read error raise immediately. This implements the schema-unification, CSV + nested‑JSON parsing, unit standardisation, and median imputation requirements of FR‑001. (External repository ingestion is flagged as unavailable and handled in T014).  
  – Parse CSV rows and flatten any nested JSON structures (fixture `code/tests/fixtures/openml_style_nested.json`) into the unified schema defined in `contracts/dataset_schema.yaml`.  
  – Convert all stress units to MPa (`1 psi = 0.00689476 MPa`).  
  – Median‑impute missing numeric values; record original missingness in `data/processed/missing_flags.json`.  
  – Compute the residual‑stress proxy for **all** rows: `σ_res = k·heat_input·cooling_rate` with `k=0.8` for steel and `k=0.6` for aluminium. Populate columns `residual_stress_proxy` and `is_proxy` (true only when a measured value is missing). Clamp any negative proxy to `0.01 MPa` and log the adjustment count.  
  – Write `data/processed/unified_fatigue.csv` and validate it against `contracts/dataset_schema.yaml` using the pinned `jsonschema`; abort on validation failure.  
  *Verification*: `pytest code/tests/test_ingest.py` runs on a slice of the bundled CSV and on the nested‑JSON fixture, asserting presence of the checksum column, MPa‑standardised stress, correct proxy values & flags, and successful schema validation.

- [ ] T003 **[P] [US1] Compute proxy‑measured agreement (FR‑014) and instrument runtime**  
  *Files*: `code/src/proxy_agreement.py`, `code/src/run_e2e.py`, `code/src/timing.py`, `data/results/proxy_agreement.csv`, `data/results/e2e_summary.json`, `data/results/runtime_summary.csv`  
  *Actions*  
  – For rows where both `residual_stress_measured` and `residual_stress_proxy` are present, compute Pearson r and R²; write results (including a column `caveat="descriptive – proxy is deterministic function of predictors"`) to `proxy_agreement.csv`.  
  – Provide a `phase_timer` context manager (wall‑clock via `time.perf_counter` and peak‑RSS via `psutil`) in `timing.py`. Wrap each pipeline phase in `run_e2e.py` with this timer and append a row to `runtime_summary.csv` (`phase`, `wall_clock_s`, `peak_rss_mb`).  
  – Execute the full end‑to‑end pipeline (ingest → proxy agreement) and emit `e2e_summary.json` summarising row counts, % of proxy rows, and the agreement metrics.  
  *Verification*: `pytest code/tests/test_e2e.py` checks that `e2e_summary.json` exists, contains finite agreement metrics when applicable, and that `runtime_summary.csv` has at least one row with non‑null timing values for each phase.

---

## Phase 2 – Feature construction, model training, and predictive comparison  

- [ ] T004 **[P] [US2] Build feature sets A, B (balanced), B‑full, and C**  
  *File*: `code/src/build_features.py`  
  *Actions*  
  – Load `unified_fatigue.csv`.  
  – **Feature Set A**: process‑parameter columns only.  
  – **Feature Set B (balanced)**: process + measured residual stress, limited to the identical balanced subset where `is_proxy=False`.  
  – **Feature Set B‑full**: process + stress (measured where available, proxy otherwise) on the **full** dataset (satisfying “process + measured or estimated stress”).  
  – **Feature Set C**: process + material‑property attributes + proxy (full dataset).  
  – Standardise all numeric features (zero mean, unit variance) and persist the scalers for later use.  
  *Verification*: `pytest code/tests/test_features.py` confirms (i) A and balanced B share identical row indices, (ii) B contains no proxy rows, (iii) B‑full and C span the full dataset and correctly use proxy where measured is missing.

- [ ] T005 **[P] [US2] Train RF, GBM, and shallow NN with 5‑fold CV, hyper‑parameter search, and timing**  
  *File*: `code/src/train.py`  
  *Actions*  
  – Define a fixed grid of **10** hyper‑parameter combinations per algorithm (as described in the plan).  
  – Perform 5-fold CV stratified by `material_class` on the balanced subset for A and B, and on the full dataset for B-full and C. Record per-fold MAPE & R².  
  – Use `config.SEED` for all random state initializations.  
  – Select the combo with lowest mean CV-MAPE, retrain on the full training split, and save the best model under `code/models/`.  
  – Use an 80/20 stratified train-test split (seed `config.SEED`) for the balanced subset; compute test-set MAPE & R² per model and per material class; write `data/results/model_performance.csv`.  
  – Record wall-clock training time for each model via `timing.py`; enforce that shallow-NN training completes ≤ 60 min (raise a clear error otherwise).  
  *Verification*: `pytest code/tests/test_train.py` asserts model files exist, CV-MAPE values are finite, NN `train_time_s` ≤ 3600 s, and that test-set metrics are written.

- [ ] T006 **[P] [US2] [US3] Statistical comparison of Set A vs Set B (Per-Material Class Wilcoxon + paired-t & ≥10 % MAPE improvement)**  
  *File*: `code/src/wilcoxon_compare.py`  
  *Actions*  
  – Compute absolute errors for each algorithm’s A-model and B-model on the **same measured-stress test rows**, stratified by `material_class`.  
  – For **each material class** (steel, aluminum):  
    – Run a **Wilcoxon signed-rank test** (primary test, Bonferroni-corrected α = 0.05/3).  
    – Run a **paired t-test** (Constitution VII).  
    – Calculate MAPE reduction: Only if MAPE_B is **≥ 10% lower** than MAPE_A for that specific material class is the improvement deemed "meaningful".  
  – Write `data/results/wilcoxon_results.csv` with columns: `material_class`, `algorithm`, `statistic`, `p_uncorrected`, `p_corrected`, `ttest_statistic`, `ttest_p`, `mape_reduction_pct`, `meets_threshold`.  
  *Verification*: `pytest code/tests/test_wilcoxon.py` checks that results are reported per material class, that p-values lie in [0,1], and that a fixture with material-specific errors yields the expected significance and threshold outcomes.

- [ ] T007 **[P] [US3] Cross‑material transfer evaluation with permutation testing (FR‑009, FR‑011)**  
  *File*: `code/src/cross_material.py`  
  *Actions*  
  – For each algorithm/feature set, train on steel‑only data, test on aluminium‑only data, and vice‑versa.  
  – Compute ΔMAPE relative to the within‑material baseline.  
  – Perform a permutation test (10 000 permutations, α = 0.05) and apply Holm‑Bonferroni correction across the two material‑pair comparisons.  
  – Write `data/results/cross_material.csv` with `train_material`, `test_material`, `mape_same`, `mape_other`, `delta_mape`, `perm_p`, `p_corrected`.  
  *Verification*: `pytest code/tests/test_cross_material.py` asserts both direction rows exist, ΔMAPE is finite, and permutation p‑values are within [0,1].

---

## Phase 3 – Conditional mediation analysis  

- [ ] T008 **[P] [US3] Power‑analysis eligibility gate and proxy‑dependency flag (FR‑013)**  
  *File*: `code/src/power_analysis.py`  
  *Actions*  
  – Conduct the a‑priori power analysis for mediation (medium effect f² = 0.15, α = 0.05, power = 0.80) and record the required sample size (≈ 45).  
  – Count rows with `is_proxy=False` (measured stress) overall and per material class; produce `data/results/mediation_eligibility.json` containing `n_measured`, `eligible` (≥ 50), `under_power_band` (50 – 63), `skip_mediation` (< 50), and `proxy_dependent` (true when `n_measured==0`).  
  *Verification*: `pytest code/tests/test_power.py` confirms the JSON matches recomputed counts and that a zero‑measured‑row fixture yields `proxy_dependent:true` and `skip_mediation:true`.

- [ ] T009 **[P] [US3] Bootstrap mediation analysis on measured‑stress subset (FR‑006, FR‑007, FR‑012)**  
  *File*: `code/src/boot_mediation.py`  
  *Actions*  
  – Proceed only if `eligible==true`; if `under_power_band` is true, add a warning flag in the output; if `skip_mediation` or `proxy_dependent` is true, log and write a “skipped” row.  
  – Exclude all proxy‑only rows.  
  – Define exposure `P = z(heat_input)·z(cooling_rate)` (standardised product).  
  – **a‑path** OLS: `residual_stress_measured ~ P + elastic_modulus + yield_strength + C(material_class)`.  
  – **b‑path** OLS: `fatigue_life_cycles ~ residual_stress_measured + P + elastic_modulus + yield_strength + C(material_class)`.  
  – Compute indirect effect = a·b, direct effect = c′, proportion mediated, and VIFs (flag > 5).  
  – Bootstrap 10 000 resamples using `config.SEED`; report indirect effect, 95 % CI, proportion mediated; apply Holm‑Bonferroni across material classes.  
  – Label results with “associational — no causal identification” and, because inputs are synthetic, also “pipeline validation only — synthetic data, not an external scientific claim”.  
  – Write `data/results/mediation_summary.csv` and save a PNG forest‑plot under `figures/`.  
  *Verification*: `pytest code/tests/test_mediation.py` checks that when eligibility is met the CSV contains non‑null CI bounds and required labels, and that when eligibility is not met a skip row is written.

---

## Phase 4 – Spec maintenance and final reporting  

- [ ] T013 **[P] Add literature citation for the residual‑stress proxy formula and discuss deterministic overlap**  
  *File*: `specs/001-predicting-the-impact-of-residual-stress/spec.md`  
  *Actions*  
  – Locate a peer‑reviewed source that justifies the empirical proxy `σ_res ≈ k·heat_input·cooling_rate` (e.g., a welding‑stress study) and insert a proper citation (e.g., `@cite{smith2020weldstress}`).  
  – Add a short discussion under FR‑003 acknowledging that the proxy is a deterministic linear combination of process parameters already present in Feature Set A, and therefore its predictive gain must be interpreted with caution.  
  *Verification*: `pytest code/tests/test_spec_update.py` checks that the spec contains a `@cite` entry for the proxy and that the new discussion paragraph is present.

- [ ] T014 **[P] Revise FR‑001 to reflect the verified unavailability of suitable public datasets**  
  *File*: `specs/001-predicting-the-impact-of-residual-stress/spec.md`  
  *Actions*  
  – Amend FR‑001 wording to state that, **as of the current verification date**, no publicly available NIST, UCI, or OpenML dataset satisfies the full schema (process parameters + measured residual stress + fatigue life + material class).  
  – Record this limitation as a formal “Spec Gap” and reference the plan’s summary section.  
  – Keep the remainder of FR‑001 (CSV/JSON parsing, unit standardisation, imputation) unchanged.  
  *Verification*: `pytest code/tests/test_spec_update.py` confirms the updated FR‑001 clause mentions the dataset‑availability gap and that the spec still validates against `contracts/dataset_schema.yaml`.

- [ ] T010 **[P] [US3] Generate complete results report and figures**  
  *File*: `code/src/generate_report.py`  
  *Actions*  
  – Aggregate all result CSV/JSON artifacts (model performance, Wilcoxon, cross‑material, proxy agreement, mediation summary/eligibility).  
  – Produce PNG figures: (i) MAPE per feature set & algorithm, (ii) mediation indirect‑effect forest plot (if present), (iii) cross‑material ΔMAPE bar chart, (iv) proxy‑agreement scatter. Save under `figures/`.  
  – Write `paper/results_report.md` that (a) links each table/figure, (b) interprets SC‑001 – SC‑004, (c) explicitly notes the deterministic nature of the proxy and the circularity caveat, (d) flags that mediation results are associational and based on synthetic validation, (e) records the FR‑001 repository‑ingestion gap as formally updated in the spec (T014), and (f) reports any under‑power warnings.  
  – Append the consolidated runtime summary (`runtime_summary.csv`) to the report.  
  *Verification*: `pytest code/tests/test_report.py` asserts the markdown file exists, references at least three figures, all referenced artifact paths exist, and that a `proxy_dependent:true` eligibility case produces the corresponding statement in the report.

- [ ] T011 **[P] [US2] End‑to‑end reproducibility verification**  
  *File*: `code/src/repro_check.py`  
  *Actions*  
  – Re‑compute SHA‑256 checksums of the raw files and compare to `checksums.json` and the `checksum` column in `unified_fatigue.csv`.  
  – Confirm that `config.SEED` is used consistently across splits, model initialisation, and bootstrap.  
  – Validate that total wall‑clock time ≤ 6 h and peak RAM ≤ 7 GB from `runtime_summary.csv` (SC‑005).  
  – Ensure every shallow‑NN entry in `model_performance.csv` has `train_time_s` ≤ 3600 s.  
  – Re‑run the workflow exactly as described in `quickstart.md`; verify that all final artefacts are byte‑stable (identical hashes).  
  – Write `data/results/reproducibility_report.txt` summarising pass/fail for each check.  
  *Verification*: `pytest code/tests/test_repro.py` checks that the report contains “ALL CHECKS PASSED” when constraints are met and that the NN training‑time check is enforced.

- [ ] T012 **[P] Paper‑stage handoff documentation**  
  *File*: `paper/paper_handoff.md`  
  *Actions*  
  – List exact locations of every artefact required for manuscript preparation (model performance, Wilcoxon, cross‑material, proxy agreement, mediation files, figures, reproducibility report, results markdown).  
  – State the scope limitation: measured‑stress results are synthetic validation only; no verified public dataset currently supplies the full required schema, so FR‑001 remains partially unmet pending a real source.  
  – Preserve any manuscript‑specific notes (layout, PDF compilation) as handoff items only.  
  *Verification*: `pytest code/tests/test_handoff.py` asserts the file exists and that each listed path resolves to an actual file in the repository.

---

### Dependency & requirement coverage

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| FR‑001 (partial) | T002, T013, T014 |
| FR‑002 | T002 |
| FR‑003 | T002, T004, T013 |
| FR‑004 | T005 |
| FR‑005 | T005 |
| FR‑006 / FR‑007 | T009 |
| FR‑008 | T006 |
| FR‑009 / FR‑011 | T007 |
| FR‑010 | T001, T005, T009, T011 |
| FR‑012 | T004, T009 |
| FR‑013 | T008 |
| FR‑014 | T003 |
| SC‑001 – SC‑005 | T005–T011 |
| Constitution VII (≥10 % MAPE & paired t‑test per class) | T006 |
| Reviewer‑identified deterministic proxy issue | T013 |

**Execution order** (respecting data flow):  
T001 → T002 → T003 → T004 → T005 → (parallel) T006 & T007 → T008 → T009 → T013 → T014 → T010 → T011 → T012.  

All tasks are presently unchecked; they will be marked ✔︎ only after the corresponding verification scripts pass.