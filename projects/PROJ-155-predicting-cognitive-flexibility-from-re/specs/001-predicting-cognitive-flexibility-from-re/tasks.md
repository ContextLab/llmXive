# Tasks: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, original research idea, any existing code artifacts.

## Phase 1 – Setup and first end‑to‑end analysis  

The goal of this phase is to obtain a runnable pipeline on a tiny real‑data subset (e.g., 5 HCP subjects) that produces all required intermediate files and a preliminary regression result.

- [ ] T001 [US1] **Create project skeleton, pin dependencies, and verify linting**   <!-- FAILED-IN-EXECUTION: code/lint_setup.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/lint_setup.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/lint_setup.py exit=1 -->
  *Create directories* `code/`, `data/raw/`, `data/processed/`, `data/results/`, `figures/`, `docs/`, `tests/`.  
  *Write* `requirements.txt` (numpy, pandas, scipy, statsmodels, nibabel, nilearn, scikit‑learn, tqdm, pyyaml, nitime, pytest, ruff).  
  *Add* `.ruff.toml` with the project‑wide linting configuration.  
  *Implement* `code/config.py` containing:  
  ```python
  SEED = 42
  WINDOW_SEC = 60          # seconds, per spec
  STEP_SEC = 1
  FD_THRESHOLD = 0.2
  BATCH_SIZE = 20
  ```  
  *Run* `ruff check . > data/logs/ruff.log` and confirm the log contains “✔ No errors”.  
  **Verification**: `cat data/logs/ruff.log && grep -q "No errors"` succeeds; `test -d code && test -d data/raw && test -d data/processed && test -d data/results && test -d figures && test -d docs && test -d tests` succeeds; directory tree matches the list above.

- [ ] T002 [US1] **Download HCP data, verify integrity, and preprocess**   <!-- FAILED-IN-EXECUTION: code/main.py exit=-1 (TIMEOUT) -->
  *Implement* `code/data/download.py` to fetch the HCP 1200‑subject resting‑state fMRI (4 runs) and the behavioral CSV containing the NIH Toolbox Dimensional Change Card Sort score via the HCP API (authenticated with a token stored in `~/.hcp_token`).  
  *Compute* SHA‑256 checksums for every downloaded file and write them to `data/raw/checksums.json`.  
  *Implement* `code/data/preprocess.py` to:  
  1. Load the Schaefer 200‑region atlas (downloaded from the official GitHub release).  
  2. Apply the atlas to each subject’s minimally preprocessed NIfTI, producing a region‑wise time‑series matrix saved as `data/processed/timeseries/{subj}_ts.npy`.  
  *Implement* `code/data/merge.py` to join the behavioral CSV with the imaging metadata, retaining only subjects that have a non‑null Flexibility_Score.  
  *Implement* `code/utils/motion.py` to compute Mean FD from the motion parameters; subjects with `Mean_FD > FD_THRESHOLD` are excluded and logged to `data/processed/exclusion_log.csv`.  
  **Verification**: Run `python -m code.data.download --subset 5` and `python -m code.data.preprocess --subset 5`; then `head data/processed/exclusion_log.csv` shows at least one row and `ls data/processed/timeseries/*_ts.npy | wc -l` equals the number of retained subjects (≤5).  

- [ ] T003 [US2] **Compute sliding‑window dynamic connectivity, derive single variability predictor, and optional PCA components**  
  *Implement* `code/features/connectivity.py` to:  
  1. Load each subject’s time‑series (`*.npy`).  
  2. Generate sliding windows of length `WINDOW_SEC` (60 s) with step `STEP_SEC` (1 s) and compute Pearson correlation matrices for every window.  
  3. For each edge, calculate the standard deviation across windows (variability) and Shannon entropy of the correlation distribution (using `np.histogram` with 20 equally‑spaced bins).  
  4. **Compute the primary subject‑level predictor** `Variability_MeanSD` as the mean of all edge‑wise standard deviations.  
  5. Assemble an edge‑wise variability matrix and run Incremental PCA, retaining the top 10 components (`PCA_Component_1` … `PCA_Component_10`) for exploratory analysis only.  
  6. Save a CSV `data/processed/variability_metrics.csv` with columns: `Subject_ID, Age, Sex, Mean_FD, Total_Scan_Time, Flexibility_Score, Status, Variability_MeanSD, PCA_Component_1 … PCA_Component_10`.  
  **Verification**: After processing the 5‑subject subset, `head data/processed/variability_metrics.csv` shows 1 header line + 5 data lines; the file validates against `contracts/dataset.schema.yaml`; the header contains exactly the ten PCA columns plus `Variability_MeanSD`; each PCA column contains a float; the `Variability_MeanSD` column contains a float.

- [ ] T004 [US2] **Validate RSFC‑variability metric against a phase‑shuffled surrogate null model**  
  *Implement* `code/features/null_model.py` to:  
  1. For each subject, generate a phase‑shuffled version of the original time‑series (FFT → randomize phase → inverse FFT).  
  2. Re‑run the sliding‑window pipeline on the surrogate and compute the same `Variability_MeanSD` metric.  
  3. Compare the real vs. surrogate distributions across subjects using a paired two‑tailed t‑test; store the resulting p‑value as `Null_Model_P` in `data/processed/variability_metrics.csv`.  
  **Verification**: `grep "Null_Model_P" data/processed/variability_metrics.csv` shows a numeric column for every retained subject; the script asserts `p_value < 0.05` and prints “Null‑model validation passed (p < 0.05)”.

- [ ] T005 [US3] **Run linear regression with covariates and produce a preliminary summary**  
  *Implement* `code/analysis/regression.py` to fit via `statsmodels.api.OLS` the model:  
  `Flexibility_Score ~ Variability_MeanSD + Age + Sex + Mean_FD + Total_Scan_Time`.  
  *Output* a JSON `data/results/regression_summary.json` containing all fields required by `contracts/output.schema.yaml`. For the preliminary run, set `Permutations = 0`, `P_Value = null`, `Significance_Status = "Not Tested"`, `FDR_Appplied = false`.  
  *Also* write `data/processed/final_results.csv` with per‑subject predicted scores and residuals (columns: Subject_ID, Flexibility_Score, Predicted_Score, Residual).  
  **Verification**: `python -m code.analysis.regression` runs without error; `jq .Beta_Variability data/results/regression_summary.json` returns a numeric value; `jq '.Permutations, .Significance_Status, .FDR_Appplied' data/results/regression_summary.json` returns `0`, `"Not Tested"`, `false`; the CSV contains exactly the same number of rows as `variability_metrics.csv` (excluding excluded subjects).

## Phase 2 – Complete the study and validate its evidence  

Now scale to the full HCP cohort, add rigorous permutation testing, and apply FDR correction where needed.

- [ ] T006 [US2] **Scale metric extraction to the full cohort using batch processing**  
  *Modify* `code/features/connectivity.py` to iterate over subjects with a generator that loads at most `BATCH_SIZE` time‑series into memory simultaneously, guaranteeing peak RSS < 7 GB (verified with `memory_profiler`).  
  *Run* the full‑cohort pipeline (`python -m code.features.connectivity --all`).  
  **Verification**: `tail -n 1 data/processed/variability_metrics.csv` shows the last subject ID; `grep -c "Subject_ID" data/processed/variability_metrics.csv` equals the number of included subjects (≥ 800 expected); `memory_profiler -m python -m code.features.connectivity --all | grep "Peak" | awk '{print $NF}'` yields a value < 7GB.

- [ ] T007 [US2] **Re‑run the phase‑shuffled null‑model validation on the full dataset**  
  *Execute* `python -m code.features.null_model --all`.  
  *Confirm* that every row in `variability_metrics.csv` now has a non‑missing `Null_Model_P` and that the overall proportion of subjects with `Null_Model_P < 0.05` is reported.  
  **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/variability_metrics.csv'); print((df['Null_Model_P']<0.05).mean())"` prints a value ≥ 0.5.

- [ ] T008 [US3] **Perform a 10 000‑iteration permutation test for the regression coefficient**  
  *Implement* `code/analysis/permutation.py` to:  
  1. Shuffle `Flexibility_Score` across subjects 10 000 times.  
  2. Re‑fit the same OLS model for each permutation, storing the β for `Variability_MeanSD`.  
  3. Compute the empirical two‑tailed p‑value as the proportion of |β_perm| ≥ |β_obs|.  
  4. If the computed p‑value equals 0.0, replace it with the string “< 0.0001”.  
  *Update* `regression_summary.json` with the final `P_Value`, `Permutations = 10000`, `Significance_Status` (“Significant” if p < 0.05 else “Not Significant”), and add `Timestamp`.  
  **Verification**: `jq .P_Value data/results/regression_summary.json` yields either a float in (0,1] or the string “< 0.0001”; the script asserts that when the raw p‑value is 0.0 the JSON field contains “< 0.0001”.

- [ ] T009 [US3] **Apply FDR correction for any optional post‑hoc network‑specific analyses**  
  *If* additional analyses (e.g., edge‑wise or network‑level β’s) are performed, run `statsmodels.stats.multitest.multipletests` with method=`fdr_bh`.  
  *Store* the adjusted q‑values in `data/results/posthoc_fdr.csv` and set `FDR_Appplied` = true in `regression_summary.json`; otherwise leave `FDR_Appplied` = false.  
  **Verification**: When `FDR_Appplied` is true, `test -f data/results/posthoc_fdr.csv && python -c "import pandas as pd, json, sys; schema=json.load(open('contracts/output.schema.yaml')); df=pd.read_csv('data/results/posthoc_fdr.csv'); assert not df.empty"` succeeds; the script also validates that the CSV conforms to a simple schema (columns: `Test_ID`, `q_value`).

- [ ] T010 [US3] **Generate final visualizations and summary tables**  
  *Implement* `code/utils/plotting.py` to produce:  
  1. `figures/variability_vs_flexibility.png` – scatter of `Variability_MeanSD` vs. Flexibility_Score with regression line and 95 % CI.  
  2. `figures/null_model_distribution.png` – histogram of real vs. surrogate `Variability_MeanSD` values with p‑value annotation.  
  3. `figures/permutation_beta_distribution.png` – histogram of permuted βs with observed β marked.  
  **Verification**: `ls figures/*.png | wc -l` returns 3; each PNG file size > 5 KB.

- [ ] T013 [SC‑001] **Compute and record the proportion of subjects successfully processed**  
  *Implement* `code/analysis/processing_stats.py` to read `data/raw/checksums.json` (total subjects) and `data/processed/exclusion_log.csv` (excluded subjects) and compute the proportion retained.  
  *Write* the metric to `data/processed/processing_proportion.csv` with columns `Total_Subjects, Retained_Subjects, Proportion_Retained`.  
  **Verification**: `cat data/processed/processing_proportion.csv` shows three numeric values; the script asserts `0.0 < Proportion_Retained <= 1.0`.

## Phase 3 – Reproducible results and paper handoff  

All scientific artifacts are now ready; this phase documents them and confirms full reproducibility.

- [ ] T011 **Write the methods and results narrative** (`docs/research.md`)  
  *Describe* data acquisition (HCP URLs, checksum verification), preprocessing (Schaefer atlas, motion exclusion), metric computation (sliding‑window, entropy, single variability metric, optional PCA), null‑model validation, regression, permutation, and any post‑hoc FDR steps.  
  *Link* each statement to the exact artifact (e.g., “see `data/processed/variability_metrics.csv`”, “see `data/results/regression_summary.json`”, “see `figures/variability_vs_flexibility.png`”).  
  **Verification**: A test script parses `docs/research.md`, extracts all file paths ending with `.csv`, `.json`, or `.png`, and asserts each exists in the repository.

- [ ] T012 **Verify end‑to‑end reproducibility and handoff**  
  *Create* `docs/quickstart.md` with the exact command sequence:  
  ```bash
  python -m code.data.download --all
  python -m code.data.preprocess --all
  python -m code.features.connectivity --all
  python -m code.features.null_model --all
  python -m code.analysis.permutation --all
  python -m code.utils.plotting
  ```  
  *Run* the full pipeline from a clean checkout (`git clean -fdx && git checkout .`) and then execute `pytest -q tests/test_contracts.py`.  
  *Record* SHA‑256 hashes of all major outputs (`variability_metrics.csv`, `final_results.csv`, `regression_summary.json`, `figures/*.png`).  
  *Run* the pipeline a second time and assert that the recorded hashes are identical.  
  **Verification**: The test suite includes a hash‑comparison test that fails if any hash differs between runs.

- [ ] T014 **Final hash‑consistency check (redundant safety)**  
  *Re‑run* the hash‑comparison step from T012 as an isolated script to double‑check reproducibility after any future modifications.  
  **Verification**: The script exits with status 0 only if all hashes match; otherwise it prints mismatched files.

---  

## Dependency and requirement coverage  

| Spec Requirement | Task(s) | Verification Command |
|------------------|---------|----------------------|
| FR‑001 (download) | T002 | `python -m code.data.download --verify` |
| FR‑002 (parcellation) | T002 | `ls data/processed/timeseries/*.npy | wc -l` |
| FR‑003 / FR‑004 (dynamic metric) | T003, T006 | `head data/processed/variability_metrics.csv` |
| FR‑005 (regression) | T005, T008 | `cat data/results/regression_summary.json \| jq .Beta_Variability` |
| FR‑006 (permutation) | T008 | `cat data/results/regression_summary.json \| jq .Permutations` |
| FR‑007 (CSV output) | T005, T010 | `csvstat data/processed/final_results.csv` |
| FR‑008 (null model) | T004, T007 | `grep Null_Model_P data/processed/variability_metrics.csv` |
| FR‑009 (FDR) | T009 | `grep FDR_Appplied data/results/regression_summary.json` |
| SC‑001 (processing proportion) | T013 | `cat data/processed/processing_proportion.csv` |
| SC‑003 (empirical p‑value) | T008 | `cat data/results/regression_summary.json \| jq .P_Value` |
| SC‑004 (correlation coefficient) | T005, T008 | `cat data/results/regression_summary.json \| jq .Pearson_R` |

**Execution Order**:  
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T013 → T011 → T012 → T014.  

---  

# End of tasks.md