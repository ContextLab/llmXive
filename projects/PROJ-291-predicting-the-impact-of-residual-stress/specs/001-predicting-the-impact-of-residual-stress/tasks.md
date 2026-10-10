# Tasks: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The following checklist implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑012) and success criterion (SC‑001 – SC‑005). Tasks are ordered to respect data flow and computational dependencies. All tasks are unchecked; completed work from prior iterations is retained but re‑opened where specification‑driven corrections are needed.

---

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T001 [P] [US1] **Create reproducible environment and quick‑start guide**  
  *Files*: `requirements.txt`, `quickstart.md`, `README.md`  
  *Actions*:  
  – Pin exact package versions (Python 3.11, pandas 2.2.*, scikit‑learn 1.5.*, torch 2.3.*, statsmodels 0.14.*, datasets 2.20.*).  
  – Add a `quickstart.md` section describing the single command to run the full pipeline (`bash run_pipeline.sh`).  
  – Verify that `pip install -r requirements.txt` completes in ≤ 2 min on the GitHub Actions runner.  
  *Verification*: Run `make env-check` (provided in `quickstart.md`) and confirm exit code 0.

- [ ] T002 [P] [US1] **Implement data‑ingestion & provenance pipeline**  
  *File*: `code/ingest/ingest.py`  
  *Actions*:  
  – Download NIST, UCI, and OpenML fatigue datasets from their canonical URLs (hard‑coded, version‑pinned).  
  – Compute a SHA‑256 checksum for each raw row and store it in a new `checksum` column.  
  – Convert all stress units to MPa (`1 psi = 0.00689476 MPE`).  
  – Median‑impute missing numeric values per column.  
  – Apply the proxy formula `σ_res = k·heat_input·cooling_rate` (k = 0.8 for steel, 0.6 for aluminum) when `residual_stress_measured` is missing; set `is_proxy = True`, store result in `residual_stress_proxy`, and clamp negatives to 0.01 MPa.  
  – Write the unified CSV to `data/processed/unified_fatigue.csv` and validate against `specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml` using `jsonschema`.  
  *Verification*: Unit test `tests/test_ingest.py` runs the script on a synthetic 10‑row CSV and asserts (i) checksum column exists, (ii) all stress values are ≤ MPa, (iii) proxy rows are flagged, and (iv) schema validation passes.

- [ ] T003 [P] [US1] **Execute ingestion on a small real subset for early end‑to‑end check**  
  *File*: `scripts/run_small_ingest.sh` (calls `code/ingest/ingest.py --rows 200`).  
  *Actions*:  
  – Process only the first 200 rows of each source dataset to keep RAM < 1 GB.  
  – Produce `data/processed/unified_fatigue_sample.csv`.  
  – Log summary statistics (rows processed, % proxy, unit conversion count).  
  *Verification*: After script finishes, a pytest test `tests/test_small_ingest.py` checks that the output file contains exactly 200 rows and that the `checksum` column matches the recorded SHA‑256 hashes.

---

## Phase 2 – Feature set construction, model training & evaluation

- [ ] T004 [P] [US2] **Build three feature‑set CSVs (A, B, C)**  
  *File*: `code/features/build_features.py`  
  *Actions*:  
  – Read `data/processed/unified_fatigue.csv`.  
  – Create `data/processed/feature_set_A.csv` (process parameters only).  
  – Create `data/processed/feature_set_B.csv` (process + measured residual stress; exclude rows where `is_proxy=True`).  
  – Create `data/processed/feature_set_C.csv` (process + material properties; no stress column).  
  – Standardize each numeric column to zero mean / unit variance.  
  *Verification*: Tests in `tests/test_features.py` assert column presence for each set and that `feature_set_B.csv` contains no `is_proxy=True` rows.

- [ ] T005 [P] [US2] **Implement model‑training pipeline with CV and hyper‑parameter search**  
  *File*: `code/models/train.py`  
  *Actions*:  
  – Accept a feature‑set path argument.  
  – Perform stratified 5‑fold CV (stratify by `material_class`).  
  – For each algorithm (RandomForestRegressor, GradientBoostingRegressor, shallow PyTorch NN) evaluate a grid of 10 hyper‑parameter combos.  
  – Use fixed random seed `SEED=42` for splits, model initialization, and CV shuffling.  
  – Record per‑fold MAPE and R²; select the combo with lowest mean CV‑MAPE.  
  – Save the final model object to `models/{algorithm}_{feature_set}.pt` (or `.pkl` for scikit‑learn).  
  *Verification*: `tests/test_train.py` runs the script on `feature_set_A.csv` truncated to 300 rows and checks that a model file is created and that the returned CV‑MAPE is a finite float.

- [ ] T006 [P] [US2] **Run full training on all feature sets and generate test‑set performance report**  
  *File*: `scripts/run_full_training.sh` (orchestrates `code/models/train.py` for A, B, C).  
  *Actions*:  
  – Split `unified_fatigue.csv` into stratified train (80 %) / held‑out test (20 %) using `SEED=42`.  
  – Train each algorithm/feature‑set combination on the full training data.  
  – Predict fatigue life on the held‑out test set; compute MAPE and R² **overall and per `material_class`**.  
  – Write a consolidated performance table to `results/performance.csv`.  
  – **Verification**: Assert that for every algorithm and for each material class `MAPE_B <= 0.9 * MAPE_A` (≥10 % improvement). If any condition fails, the script exits with a non‑zero status.  
  – Generate `results/runtime_summary.csv` (wall‑clock time, peak memory) and assert limits (≤ 6 h, ≤ 7 GB RAM).  
  *Verification*: `tests/test_full_training.py` parses `performance.csv` and confirms the ≥10 % improvement condition per material class and that runtime limits are respected.

- [ ] T013 [P] [US2] **Explicit verification of ≥10 % MAPE reduction across material classes**  
  *File*: `code/eval/verify_improvement.py`  
  *Actions*:  
  – Load `results/performance.csv`.  
  – For each algorithm, compute the percentage reduction `100 * (MAPE_A - MAPE_B) / MAPE_A` overall and separately for `steel` and `aluminum`.  
  – Fail with a clear error message if any reduction is < 10 %.  
  – Output a concise summary `results/improvement_check.txt`.  
  *Verification*: `tests/test_improvement_check.py` ensures the script returns exit code 0 only when the 10 % threshold is met for all required groups.

- [ ] T007 [P] [US3] **Perform paired t‑tests comparing Feature A vs B errors and enforce 10 % improvement**  
  *File*: `code/eval/pairwise_test.py`  
  *Actions*:  
  – Load test‑set predictions for Model A and Model B (same algorithm).  
  – Compute absolute errors, then run a paired t‑test.  
  – Apply Bonferroni correction for the three algorithm families (α = 0.05/3).  
  – **Additional check**: Verify that the observed MAPE reduction meets the ≥10 % threshold (using the same calculation as T013). If not, emit a warning and set a non‑zero exit status.  
  – Output statistics (t, df, p‑value, corrected p) to `results/paired_t_test.csv`.  
  *Verification*: `tests/test_pairwise.py` verifies that the CSV contains columns `t_stat`, `p_uncorrected`, `p_corrected` and that both the statistical significance and the 10 % improvement condition are satisfied.

- [ ] T008 [P] [US3] **Cross‑material transfer learning evaluation**  
  *File*: `code/eval/cross_material.py`  
  *Actions*:  
  – Train on steel‑only subset, test on aluminum‑only subset; then reverse.  
  – Compute ΔMAPE = MAPE_test_other − MAPE_test_same for each direction.  
  – Record results in `results/cross_material.csv` with columns `train_material`, `test_material`, `delta_mape`.  
  *Verification*: `tests/test_cross_material.py` checks that both directions are present and that `delta_mape` is a non‑negative float.

---

## Phase 3 – Mediation analysis (measured‑stress subset only)

- [ ] T009 [P] [US3] **Bootstrap mediation analysis (10 000 resamples) on measured‑stress data**  
  *File*: `code/mediation/boot_mediation.py`  
  *Actions*:  
  – Filter `unified_fatigue.csv` to rows where `is_proxy=False`.  
  – If filtered rows < 50, emit a warning and skip mediation (record `skip_mediation=True` in `results/mediation_summary.csv`).  
  – For each material class (steel, aluminum) fit a mediation model: process parameters → residual stress (mediator) → fatigue life (outcome), adjusting for other covariates (`elastic_modulus`, `yield_strength`, etc.).  
  – Perform 10 000 bootstrap resamples to estimate indirect effect, 95 % CI, and proportion mediated.  
  – Apply Holm‑Bonferroni correction across material classes.  
  – Save `results/mediation_summary.csv` with columns `material_class`, `indirect_effect`, `ci_lower`, `ci_upper`, `prop_mediated`, `p_corrected`.  
  *Verification*: `tests/test_mediation.py` confirms that when ≥ 50 rows are present the CSV contains non‑null CI bounds and that corrected p‑values are ≤ 1; when < 50 rows, the CSV contains a single row with `skip_mediation=True`.

---

## Phase 4 – Reporting, reproducibility, and handoff

- [ ] T010 [P] [US3] **Generate final results report and figures**  
  *File*: `code/report/generate_report.py`  
  *Actions*:  
  – Read all CSVs in `results/` (performance, paired_t_test, cross_material, mediation_summary).  
  – Produce Matplotlib figures: (i) bar chart of MAPE per feature set, (ii) forest plot of mediation indirect effects, (iii) ΔMAPE cross‑material heatmap.  
  – Save figures to `results/figures/`.  
  – Write a Markdown summary `reports/report.md` that links to each table and figure, includes interpretation of SC‑001 – SC‑004, and notes any skipped mediation due to sample‑size limits.  
  *Verification*: `tests/test_report.py` checks that `reports/report.md` exists, contains at least three figure links, and that each referenced CSV file is present.

- [ ] T011 [P] [US2] **Reproducibility checklist and provenance validation**  
  *File*: `code/utils/repro_check.py`  
  *Actions*:  
  – Verify that `SEED=42` is set in all scripts (`grep` for the constant).  
  – Re‑compute checksums of raw files in `data/raw/` and compare to the `checksum` column in `unified_fatigue.csv`.  
  – Parse `results/runtime_summary.csv` and assert that wall‑clock time ≤ 6 h and peak memory ≤ 7 GB (SC‑005).  
  – Output a human‑readable `results/reproducibility_report.txt` summarizing pass/fail for each check.  
  *Verification*: `tests/test_repro.py` asserts that the report contains the line `All reproducibility checks passed.` when limits are satisfied.

- [ ] T012 [P] [US1] **Document full pipeline usage and paper‑stage handoff**  
  *Files*: `README.md`, `quickstart.md`, `reports/paper_handoff.md`  
  *Actions*:  
  – `README.md` lists project overview, dataset URLs, and how to obtain raw data.  
  – `quickstart.md` gives step‑by‑step commands: `bash run_small_ingest.sh`, `bash run_full_training.sh`, `python -m code.report.generate_report`.  
  – `paper_handoff.md` enumerates the exact artifact locations required for downstream manuscript generation (e.g., `results/performance.csv`, `results/figures/`, `reports/report.md`) and cites the reproducibility report.  
  *Verification*: Manual inspection test `tests/test_docs.py` ensures each of the three files exists and contains the expected section headers.

---

## Dependencies and requirement coverage

| Specification Requirement | Satisfying Task(s) |
|---------------------------|--------------------|
| FR‑001 (ingest public datasets) | T002 |
| FR‑002 (median imputation & unit standardisation) | T002 |
| FR‑003 (proxy calculation & flagging) | T002 |
| FR‑004 (train three feature‑set models) | T005, T006 |
| FR‑005 (5‑fold CV & held‑out test) | T005, T006 |
| FR‑006 (bootstrap mediation, 10 k resamples) | T009 |
| FR‑007 (report proportion mediated & CI) | T009 |
| FR‑008 (paired t‑test on MAPEs) | T007 |
| FR‑009 (stratified analysis by material class) | T009, T008 |
| FR‑010 (fixed seeds) | T001, T005, T009, T011 |
| FR‑011 (cross‑material transfer evaluation) | T008 |
| FR‑012 (exclude proxy rows from mediation) | T009 |
| SC‑001 – SC‑005 (measurable outcomes & compute limits) | T006, T009, T011 |
| Constitution VII (≥10 % MAPE improvement) | T006, T013, T007 |

All tasks are ordered to respect data dependencies: ingestion → feature construction → model training → performance verification → statistical evaluation → mediation → reporting. The early end‑to‑end run is provided by T003 (small‑subset ingestion) followed by T004‑T006 on the full data, guaranteeing an executable pipeline before any downstream statistical work.
