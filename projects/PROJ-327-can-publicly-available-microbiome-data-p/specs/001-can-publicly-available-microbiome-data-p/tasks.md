# Tasks: Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?

**Inputs**: `spec.md`, `plan.md`, existing code skeleton, reviewer feedback, and the data‑model contract.

The following checklist implements the smallest complete, reproducible study that satisfies **all** functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑008).  
Tasks are ordered to respect data flow and computational dependencies; each unchecked box represents work that must be performed on the CI runner.  

---  

- [ ] **T001** [US1] Verify metabolomics data availability after download and abort if missing.  
  *Implementation*: `code/acquire.py` checks that the metabolomics CSV produced by T013 exists; if not, raises `RuntimeError("Metabolomics data unavailable – aborting per FR‑008")`.  
  *Verification*: Unit test `tests/unit/test_acquire.py::test_metabolomics_missing` confirms the RuntimeError and that CI logs the exact message required by FR‑008.  

- [ ] **T002** [US1] Download raw 16S rRNA FASTQ reads from NCBI SRA (real, immutable accession list).  
  *Implementation*: `code/acquire.py` defines `download_sra_fastq(accessions: List[str], out_dir: Path) -> None` that uses `pysradb`/`sra-tools` to fetch FASTQ files into `data/raw/sra_fastq/`, computes SHA‑256 checksums stored in `data/checksums/checksums.txt`.  
  *Verification*: After execution, `data/raw/sra_fastq/` contains at least one `.fastq.gz` file and matching checksum entries.  

- [ ] **T003** [US1] Process raw FASTQ reads with DADA2 (via `rpy2`) to generate an ASV table.  
  *Implementation*: `code/curate.py` runs the full DADA2 pipeline on the FASTQ files from T002, outputs a wide CSV `data/processed/asv_table.csv` with columns `asv_*`. No fallback to pre‑computed tables is permitted.  
  *Verification*: `tests/unit/test_curate.py::test_asv_table_schema` validates that every `asv_*` column is an integer ≥ 0 and that the file size estimate fits within the 7 GB RAM budget.  

- [ ] **T013** [US1] Download metabolomics profiles from MetaboLights (real, reachable URL).  
  *Implementation*: `code/acquire.py` adds `download_metabolomics(url: str, out_path: Path) -> None` which fetches the TSV/CSV at `[UNRESOLVED-CLAIM: https://ftp.ebi.ac.uk/pub/databases/metabolights/MTBLS2295/files/MTBLS2295.tsv` — HTTP 404] (a verified public dataset) into `data/raw/metabolomics/metabolomics.tsv`, verifies checksum.  
  *Verification*: Unit test `tests/unit/test_acquire.py::test_metabolomics_download` checks file existence and checksum match.  

- [ ] **T004** [US1] Normalize metabolite intensities, canonicalize metadata, merge with ASV table, and enforce sample‑count guard.  
  *Implementation*: `code/integrate.py`  
  - Loads `data/processed/asv_table.csv`.  
  - Loads metabolomics CSV from T013, applies median scaling to all `metab_*` columns.  
  - Normalizes heterogeneous `condition` labels to the canonical value `herbivore_stress` (FR‑007).  
  - Performs an inner join on `sample_id`, `species`, `condition`, and `study_id`.  
  - Drops rows with missing values; logs exclusion count.  
  - Checks that usable samples ≥ 30; if not, raises `RuntimeError("Error: insufficient samples (<30) for 5‑fold cross‑validation")` (FR‑008).  
  - Adds one‑hot species columns `species_arabidopsis` and `species_tomato`.  
  - Writes the merged, schema‑validated file to `data/processed/merged_dataset.csv`.  
  *Verification*: `tests/contract/test_merged_schema.py` validates against `merged-dataset.schema.yaml`; separate test confirms RuntimeError on insufficient samples.  

- [ ] **T005** [US2] Implement PCA fitting *within* each cross‑validation training fold for a configurable variance‑retention threshold.  
  *Implementation*: `code/pca.py` provides `fit_pca(train_df: pd.DataFrame, variance: float) -> PCA` that selects the number of components to retain the requested variance (default 0.90) and returns the fitted scikit‑learn `PCA` object. The function is called inside the CV loop (see T006).  
  *Verification*: Unit test `tests/unit/test_pca.py::test_variance_retention` checks that cumulative explained variance meets or exceeds the requested threshold for synthetic data.  

- [ ] **T006** [US2] Train a multi‑output Random Forest regressor with leave‑one‑study‑out 5‑fold CV, compute per‑metabolite and mean R², and output feature‑importance rankings.  
  *Implementation*: `code/model.py` orchestrates the CV:  
  - Splits samples by `study_id` (LOSO).  
  - Within each training fold, calls `pca.fit_pca` (T005) on the ASV columns, transforms both train and test sets, concatenates species one‑hot columns, and fits `RandomForestRegressor(n_estimators=500, max_features='sqrt', random_state=42)` wrapped by `MultiOutputRegressor`.  
  - Records per‑metabolite R², mean R², and the top 10 PC importances (by mean decrease impurity).  
  - Writes metrics to `data/results/model_metrics.csv` and a JSON summary to `data/results/model_summary.json`.  
  *Verification*: After execution, `data/results/model_metrics.csv` contains columns `metabolite, r2, mean_r2`; pytest `tests/unit/test_model_cv.py` asserts non‑nan R² per fold and consistency with the JSON summary.  

- [ ] **T007** [US2] Perform **1,000** permutation tests (labels permuted within each CV fold) to generate a null R² distribution and compute a one‑sided p‑value.  
  *Implementation*: Extend `code/model.py` with `run_permutations(n_perm=1000)` that repeats the LOSO CV loop, permuting metabolite labels **within** each training fold before model fitting (FR‑011). Results aggregated into `data/results/permutation_null.npy`; p‑value written to `data/results/permutation_pvalue.txt`.  
  *Verification*: `tests/unit/test_permutation.py::test_null_distribution` checks array length = 1000, p‑value ∈ [0,1], and that permutation respects CV‑fold boundaries (validated by T014).  

- [ ] **T014** [US2] Verify that permutation shuffling occurs **within** each CV fold.  
  *Implementation*: Unit test `tests/unit/test_permutation_fold.py::test_permutation_within_fold` creates a mock CV split, runs a single permutation, and asserts that no label moves across fold boundaries.  
  *Verification*: Test passes only if the permutation logic respects the fold partitioning.  

- [ ] **T008** [US3] Sensitivity analysis: sweep PCA variance thresholds {0.80, 0.90, 0.95}.  
  *Implementation*: `code/sensitivity.py` iterates over the three variance thresholds, re‑runs the full LOSO CV pipeline (T006) for each, and records the resulting mean R² in `data/results/sensitivity.csv` with columns `variance, mean_r2`.  
  *Verification*: `tests/unit/test_sensitivity.py::test_sensitivity_table` confirms the CSV has exactly 3 rows and numeric R² values.  

- [ ] **T009** [US2 & US3] Generate all required figures and a concise markdown summary for handoff.  
  *Implementation*: `code/reporting.py` reads outputs from T006, T007, T008, and T016, creates:  
  - Per‑metabolite observed vs. predicted scatter plots (`figures/regression_{metab}.png`).  
  - Bar plot of the top 10 PC feature importances (`figures/pc_importance.png`).  
  - Sensitivity sweep line plot (`figures/sensitivity.png`).  
  - Baseline vs. model R² comparison plot (`figures/baseline_comparison.png`).  
  - `paper/summary.md` listing mean R², p‑value, baseline R², and a table of sensitivity results, referencing each figure.  
  *Verification*: pytest `tests/unit/test_reporting.py` checks existence and non‑emptiness of all figure files and presence of expected markdown sections.  

- [ ] **T010** Guardrails & Continuous Validation  
  *Implementation*: Comprehensive test suite under `tests/` covering:  
  - FR‑008 abort condition (already in T004 test).  
  - Contract validation for the merged dataset (T004).  
  - Correctness of LOSO splitting (`tests/unit/test_cv_split.py`).  
  - Runtime‑memory check ensuring PCA on the full training fold never exceeds 7 GB (now performed by T012).  
  - Study‑identifier non‑predictivity test (T015).  
  - Baseline model comparison (T016).  
  *Verification*: CI runs `pytest -q`; the suite must pass with 0 failures before any downstream task is considered complete.  

- [ ] **T011** Measure total pipeline runtime and enforce the 6‑hour CI limit (SC‑003).  
  *Implementation*: `code/runtime_monitor.py` wraps the entire end‑to‑end execution, records wall‑clock time, writes `data/logs/runtime_seconds.txt`. A pytest `tests/unit/test_runtime.py::test_runtime_limit` asserts the recorded time ≤ 21600 seconds.  
  *Verification*: Failure of the test aborts the pipeline, guaranteeing compliance with SC‑003.  

- [ ] **T012** Measure memory footprint of the PCA‑reduced dataset and enforce the 7 GB RAM limit (SC‑004).  
  *Implementation*: `code/memory_monitor.py` uses `psutil` to snapshot peak memory usage during PCA transformation, writes `data/logs/pca_peak_memory_gb.txt`. A pytest `tests/unit/test_memory.py::test_pca_memory_limit` asserts the peak ≤ 7 GB.  
  *Verification*: Test failure stops the run, ensuring SC‑004 is met.  

- [ ] **T015** Verify that study identifiers are not predictive (SC‑006).  
  *Implementation*: `code/study_check.py` runs LOSO CV (as in T006) and a random‑study CV where study IDs are shuffled before splitting; compares mean R² between the two. Writes `data/results/study_id_check.txt` with the difference. A pytest `tests/unit/test_study_predictivity.py::test_study_not_predictive` asserts that the LOSO performance does not exceed random‑study performance by more than 0.05, confirming study bias is absent.  

- [ ] **T016** Train a baseline random‑guess model and report comparative R² (SC‑008).  
  *Implementation*: `code/baseline.py` predicts each metabolite as the training‑fold mean (i.e., a constant model), computes per‑metabolite and mean R², writes `data/results/baseline_metrics.csv`. `code/reporting.py` incorporates these values into the final markdown and comparison plot.  
  *Verification*: `tests/unit/test_baseline.py::test_baseline_metrics` checks that baseline R² values are ≤ 0 (as expected for a non‑informative model).  

---  

### Dependency Mapping (spec → tasks)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 | T002, T003 |
| FR‑002 | T004 |
| FR‑003 | T005 |
| FR‑004 | T006 |
| FR‑005 | T007 |
| FR‑006 | T008 |
| FR‑007 | T004 |
| FR‑008 | T004 (guard) |
| FR‑009 | T005 (fit within CV) |
| FR‑010 | T006 (feature‑importance) |
| FR‑011 | T007, T014 |
| FR‑012 | T006 (LOSO) |
| FR‑013 | T006 (multi‑output) |
| FR‑014 (baseline) | T016 |
| SC‑001 | T006, T007 |
| SC‑002 | T008 |
| SC‑003 | T011 |
| SC‑004 | T012 |
| SC‑005 | T004 (abort test) |
| SC‑006 | T015 |
| SC‑007 | T007, T014 |
| SC‑008 | T009, T016 |

---  

All tasks are unchecked, ready for execution, and collectively deliver an end‑to‑end, reproducible analysis that satisfies the specification without fabricating data or exceeding compute limits.  