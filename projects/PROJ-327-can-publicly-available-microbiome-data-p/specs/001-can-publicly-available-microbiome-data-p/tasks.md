# Tasks: Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?

**Inputs**: `spec.md`, `plan.md`, existing code skeleton, reviewer feedback, and the data‑model contract.

The checklist implements the smallest complete, reproducible study that satisfies **all** functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑008).  
Tasks are ordered to respect data flow and computational dependencies; each unchecked box represents work that must be performed on the CI runner.

---

- [X] **T001** [US1] **Download metabolomics profiles and verify checksum**  
  *Implementation*: `code/acquire.py` adds `download_metabolomics(url: str, out_path: Path) -> None`. The function fetches a verified MetaboLights TSV/CSV (e.g., `[UNRESOLVED-CLAIM: https://ftp.ebi.ac.uk/pub/databases/metabolights/MTBLS1234/files/MTBLS1234.tsv` — HTTP 404]), writes it to `data/raw/metabolomics/`, and verifies the SHA‑256 checksum recorded in `data/checksums/checksums.txt`. If the HTTP request fails or the checksum entry is missing, the function raises `RuntimeError("Metabolomics data unavailable – aborting per FR‑008")`.  
  *Verification*: Unit test `tests/unit/test_acquire.py::test_metabolomics_missing_file` checks missing file abort, and `tests/unit/test_acquire.py::test_metabolomics_missing_checksum` checks missing checksum abort; both assert the exact RuntimeError message.

- [ ] **T002** [US1] **Download raw 16S rRNA FASTQ reads from NCBI SRA**  
  *Implementation*: `code/acquire.py` defines `download_sra_fastq(accessions: List[str], out_dir: Path) -> None` which uses `pysradb`/`sra-tools` to fetch FASTQ.gz files into `data/raw/sra_fastq/`. SHA‑256 checksums are written to `data/checksums/checksums.txt`.  
  *Verification*: After execution, `data/raw/sra_fastq/` contains at least one `.fastq.gz` file and matching checksum entries; test `tests/unit/test_acquire.py::test_sra_download` validates existence and checksum correctness.

- [ ] **T003** [US1] **Process raw FASTQ reads with DADA2 (via `rpy2`) to generate an ASV table**   <!-- FAILED-IN-EXECUTION: code/curate.py exit=1 -->
  *Implementation*: `code/curate.py` runs the full DADA2 pipeline on the FASTQ files from T002, outputs a wide CSV `data/processed/asv_table.csv` with columns `asv_*`. No fallback to pre‑computed tables is permitted.  
  *Verification*: `tests/unit/test_curate.py::test_asv_table_schema` validates that every `asv_*` column is an integer ≥ 0 and that the file size estimate fits within the 7 GB RAM budget.

- [ ] **T004** [US1] **Normalize metabolite intensities, canonicalize metadata, merge with ASV table, and enforce sample‑count guard**  
  *Implementation*: `code/integrate.py`  
  - Loads `data/processed/asv_table.csv`.  
  - Loads metabolomics CSV from T001, applies median scaling to all `metab_*` columns.  
  - Normalizes heterogeneous `condition` labels to the canonical value `herbivore_stress` (FR‑007).  
  - Performs an inner join on `sample_id`, `species`, `condition`, and `study_id`.  
  - Drops rows with missing values; logs the exclusion count.  
  - Checks that usable samples ≥ 30; if not, raises `RuntimeError("Error: insufficient samples (<30) for 5‑fold cross‑validation")` (FR‑008).  
  - Adds one‑hot species columns `species_arabidopsis` and `species_tomato`.  
  - Writes the merged, schema‑validated file to `data/processed/merged_dataset.csv`.  
  *Verification*: `tests/contract/test_merged_schema.py` validates the file against `merged-dataset.schema.yaml`; `tests/unit/test_integrate.py::test_insufficient_samples` confirms the RuntimeError is raised when < 30 samples remain.

- [ ] **T005** [US2] **Fit PCA within each cross‑validation training fold for a configurable variance‑retention threshold**  
  *Implementation*: `code/pca.py` provides `fit_pca(train_df: pd.DataFrame, variance: float) -> PCA` that selects the smallest number of components whose cumulative explained variance meets or exceeds `variance` (default 0.90) and returns the fitted scikit‑learn `PCA` object. This function is called inside the CV loop (see T006).  
  *Verification*: Unit test `tests/unit/test_pca.py::test_variance_retention` checks that cumulative explained variance meets the requested threshold on synthetic data.

- [ ] **T006** [US2] **Train a multi‑output Random Forest regressor with leave‑one‑study‑out 5‑fold CV; compute per‑metabolite & mean R²; output top‑10 PC feature‑importance ranking**  
  *Implementation*: `code/model.py` orchestrates the CV:  
  - Splits samples by `study_id` (LOSO).  
  - Within each training fold, calls `pca.fit_pca` (T005) on the ASV columns, transforms both train and test sets, concatenates species one‑hot columns, and fits `RandomForestRegressor(n_estimators=500, max_features='sqrt', random_state=42)` wrapped by `MultiOutputRegressor`.  
  - Records per‑metabolite R², mean R², and the top 10 PC importances (by mean decrease impurity) which are written to `data/results/pc_importance.csv`.  
  - Writes metrics to `data/results/model_metrics.csv` and a JSON summary to `data/results/model_summary.json`.  
  *Verification*: After execution, `data/results/model_metrics.csv` contains columns `metabolite,r2,mean_r2`; `data/results/pc_importance.csv` contains the top 10 PCs; pytest `tests/unit/test_model_cv.py` asserts non‑NaN R² per fold and consistency with the JSON summary.

- [ ] **T007** [US2] **Perform 1,000 permutation tests (labels permuted within each CV fold) to generate a null R² distribution and compute a one‑sided p‑value**  
  *Implementation*: Extend `code/model.py` with `run_permutations(n_perm: int = 1000)` that repeats the LOSO CV loop, permuting metabolite labels **within** each training fold before model fitting (FR‑011). Results are aggregated into `data/results/permutation_null.npy`; the one‑sided p‑value is written to `data/results/permutation_pvalue.txt`.  
  *Verification*: `tests/unit/test_permutation.py::test_null_distribution` checks that the array length equals 1000, that the p‑value lies in [0,1], and that permutation respects CV‑fold boundaries (validated by T008).

- [ ] **T008** [US2] **Verify that permutation shuffling occurs within each CV fold**  
  *Implementation*: Unit test `tests/unit/test_permutation_fold.py::test_permutation_within_fold` creates a mock CV split, runs a single permutation, and asserts that no label moves across fold boundaries.  
  *Verification*: Test passes only if the permutation logic respects the fold partitioning.

- [ ] **T009** [US3] **Sensitivity analysis: sweep PCA variance thresholds {0.80, 0.90, 0.95} and record performance**  
  *Implementation*: `code/sensitivity.py` iterates over the three variance thresholds, re‑runs the full LOSO CV pipeline (T006) for each, and records the resulting mean R² in `data/results/sensitivity.csv` with columns `variance,mean_r2`.  
  *Verification*: `tests/unit/test_sensitivity.py::test_sensitivity_table` confirms the CSV has exactly three rows and numeric R² values.

- [ ] **T010** [US2] **Train a baseline random‑guess model and report comparative R²**  
  *Implementation*: `code/baseline.py` predicts each metabolite as the training‑fold mean (constant model), computes per‑metabolite and mean R², writes `data/results/baseline_metrics.csv`. `code/reporting.py` incorporates these values into the final markdown and a baseline‑vs‑model comparison plot.  
  *Verification*: `tests/unit/test_baseline.py::test_baseline_metrics` checks that baseline R² values are ≤ 0 (as expected for a non‑informative model).

- [ ] **T011** [US2] **Check that study identifiers are not predictive (SC‑006)**  
  *Implementation*: `code/study_check.py` runs LOSO CV (as in T006) and a random‑study CV where study IDs are shuffled before splitting; compares mean R² between the two. Writes `data/results/study_id_check.txt` with the difference.  
  *Verification*: `tests/unit/test_study_predictivity.py::test_study_not_predictive` asserts that the LOSO performance does not exceed random‑study performance by more than 0.05, confirming study bias is absent.

- [ ] **T012** [US3] **Generate all required figures and a concise markdown summary for handoff**  
  *Implementation*: `code/reporting.py` reads outputs from T006, T007, T009, T010, and T011, creates:  
  - Per‑metabolite observed‑vs‑predicted scatter plots (`figures/regression_{metab}.png`).  
  - Bar plot of the top 10 PC feature importances (`figures/pc_importance.png`).  
  - Sensitivity sweep line plot (`figures/sensitivity.png`).  
  - Baseline vs. model R² comparison plot (`figures/baseline_comparison.png`).  
  - Study‑bias check plot (`figures/study_bias.png`).  
  - `paper/summary.md` listing mean R², p‑value, baseline R², sensitivity table, and references to each figure.  
  *Verification*: pytest `tests/unit/test_reporting.py` checks existence and non‑emptiness of all figure files and the presence of expected markdown sections.

- [ ] **T014** [US3] **Measure total pipeline runtime and enforce the 6‑hour CI limit (SC‑003)**  
  *Implementation*: `code/runtime_monitor.py` wraps the entire end‑to‑end execution, records wall‑clock time, writes `data/logs/runtime_seconds.txt`. A pytest `tests/unit/test_runtime.py::test_runtime_limit` asserts the recorded time ≤ 21600 seconds.  
  *Verification*: Failure of the test aborts the pipeline, guaranteeing compliance with SC‑003.

- [ ] **T015** [US3] **Measure peak memory footprint of the PCA‑reduced dataset and enforce the 7 GB RAM limit (SC‑004)**  
  *Implementation*: `code/memory_monitor.py` uses `psutil` to snapshot peak memory usage during PCA transformation, writes `data/logs/pca_peak_memory_gb.txt`. A pytest `tests/unit/test_memory.py::test_pca_memory_limit` asserts the peak ≤ 7 GB.  
  *Verification*: Test failure stops the run, ensuring SC‑004 is met.

- [ ] **T016** [US3] **Power‑analysis sanity check**  
  *Implementation*: `code/power_analysis.py` computes post‑hoc statistical power based on the observed effect size (mean R²), sample size, and desired alpha = 0.05 using `statsmodels.stats.power.FTestPower`. Results (estimated power, required sample size for 0.8 power) are written to `data/results/power_analysis.txt` and summarized in `paper/summary.md`.  
  *Verification*: `tests/unit/test_power_analysis.py::test_power_output` checks that the file contains a numeric power value between 0 and 1 and that required sample size is reported.

- [ ] **T017** [US3] **Random Forest hyper‑parameter sweep**  
  *Implementation*: `code/hyperparameter_sweep.py` iterates over `n_estimators ∈ {200, 500}` and `max_features ∈ {'sqrt', 0.5}` (in addition to the variance thresholds already covered by T009). For each configuration it runs the full LOSO CV pipeline (T006) and records mean R² in `data/results/hyperparameter_sweep.csv` with columns `n_estimators,max_features,mean_r2`.  
  *Verification*: `tests/unit/test_hyperparameter_sweep.py::test_sweep_table` confirms the CSV contains 4 rows (all combos) and numeric R² entries.

- [ ] **T018** [US1] **Unit test for missing checksum abort in metabolomics download (T001)**  
  *Implementation*: `tests/unit/test_acquire.py::test_metabolomics_missing_checksum` creates a dummy checksum file without an entry for the metabolomics URL, runs `download_metabolomics`, and asserts that `RuntimeError("Metabolomics data unavailable – aborting per FR-008")` is raised.  
  *Verification*: Test passes only when the missing‑checksum guard is correctly implemented.

- [ ] **T019** [US2] **Unit test for existence and correctness of top‑10 PC importance ranking**  
  *Implementation*: `tests/unit/test_model_importance.py::test_top10_importance_file` runs the model pipeline (T006) on a small synthetic dataset, checks that `data/results/pc_importance.csv` exists, contains exactly 10 rows, and that the `importance` column values are non‑negative and sum to a positive number.  
  *Verification*: Test fails if the file is missing, has incorrect row count, or contains invalid values.

- [ ] **T020** [US2] **Guardrail test that mean R² exceeds the constitution threshold (R² > 0.3)**  
  *Implementation*: `tests/unit/test_mean_r2_threshold.py::test_mean_r2_above_threshold` runs the full modeling pipeline (T006) and asserts that the reported mean R² in `data/results/model_metrics.csv` is greater than 0.3.  
  *Verification*: Failure aborts the run, ensuring compliance with Constitution VII.
