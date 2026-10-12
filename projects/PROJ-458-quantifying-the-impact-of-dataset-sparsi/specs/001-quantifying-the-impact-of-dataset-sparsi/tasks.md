# Tasks: Quantify Dataset Sparsity Impact  

**Input**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  
**Goal**: Implement a reproducible end‑to‑end pipeline that (1) downloads real Materials Project data, (2) builds a Representative Stratified Sample (RSS), (3) creates strictly nested sparsity subsets, (4) trains Gaussian Process Regression (FITC) and Random Forest models on CPU, (5) evaluates performance, (6) analyses results with Linear Mixed‑Effects Modeling (LMM) and Tukey post‑hoc, (7) conducts a sensitivity analysis on slope variance, and (8) produces a final associational report.  

All tasks follow the canonical checklist format `- [ ] T### [P?] [USx?] description …`.  Checked boxes indicate completed work that already satisfies verification; unchecked boxes are pending and have been revised to guarantee deterministic, real‑data artefacts.

---

## Phase 0 – Project scaffolding (completed)

- [X] T001 **[FR-001]** Establish project layout (`code/`, `data/raw`, `data/processed`, `data/results`, `data/metadata`, `tests/unit`, `tests/integration`, `docs`).  
  **Verification**: `project_structure.txt` lists all created directories.

- [X] T002 **[FR-001]** Pin reproducible dependencies in `code/requirements.txt` (e.g., `pymatgen==2024.2.21`, `matminer==0.9.2`, `scikit‑learn==1.3.0`, `gpytorch==2.0.1`, …).  
  **Verification**: `pip install -r code/requirements.txt` succeeds without version conflicts.

- [ ] T003 **[FR-001]** Add pre‑commit configuration (`code/.pre‑commit-config.yaml`) with `ruff` and `black`.  
  **Verification**: `pre‑commit run --all-files` passes.

- [ ] T004 **[FR-001]** Create `code/config.py` exposing pipeline constants (e.g., `SEED_LIST`, `SPARSITY_LEVELS`) and a helper `load_env()` that raises `RuntimeError` if `MP_API_KEY` is missing.  
  **Verification**: Importing `config` without `MP_API_KEY` raises the expected error.

- [X] T005 **[FR-001]** Define RSS size dynamically: `code/define_rss_size.py` writes an integer `rss_size` to `data/metadata/rss_config.json` after a lightweight memory‑budget check.  
  **Verification**: `rss_config.json` exists and contains a positive integer ≤ 150 000.

- [X] T015 **[FR-001]** Implement JSON‑logging utility `code/utils/logging.py` (`get_logger()` writes to `data/results/`).  
  **Verification**: Sample log file is created under `data/results/`.

- [X] T016 **[FR-001]** Provide memory‑constraint helper `code/utils/cpu_constraints.py` (`enforce_memory_limit(max_gb)`) and a safe `chunked_iterator(iterable, chunk_size)`.  
  **Verification**: Functions import without error; a test script runs without exceeding 7 GB.

- [~] T017 **[FR-001]** Add schema validator `code/utils/contract_validator.py` (`validate_schema(data, schema_path)`).  
  **Verification**: Validation against `contracts/dataset.schema.yaml` and `contracts/metrics.schema.yaml` succeeds for known‑good files.

- [~] T018 **[FR-001]** Define dataclasses `MaterialEntry` and `SparsitySubset` in `code/utils/data_models.py`.  
  **Verification**: Instances can be created and serialized to JSON.

- [~] T019 **[FR-001]** Provide `.env.example` with placeholder `MP_API_KEY` and `config.load_env()` that aborts if the variable is absent.  
  **Verification**: Running any pipeline script without `MP_API_KEY` raises `RuntimeError`.

---

## Phase 1 – Data acquisition & preprocessing (pending)

- [ ] T020 **[US1]** Download the full Materials Project corpus (≥ 150 000 entries) via the REST API using the environment variable `MP_API_KEY`.   <!-- FAILED-IN-EXECUTION: code/data_ingestion.py exit=1 -->
  *Implementation*: `code/data_ingestion.py` streams JSON responses, writes `data/raw/raw_pool.csv` with columns `material_id`, `composition`, `formation_energy_per_atom`, `dft_computed`.  
  *Verification*: File exists, row count ≥ 150 000, and a checksum is recorded in `data/metadata/raw_pool_checksum.json`.  

- [ ] T021 **[US1]** Split a **fixed test set** (20 % of the *entire* raw pool) using stratified sampling on `formation_energy_per_atom` (quantile bins).  
  *Implementation*: `code/test_split.py` reads `raw_pool.csv`, writes `data/processed/test_set.csv` and `data/processed/test_set_indices.csv`.  
  *Verification*: `test_set.csv` contains exactly 20 % of rows, indices file matches rows, and a SHA‑256 hash is stored in `data/metadata/test_set_hash.json`.  

- [ ] T022 **[US1]** Filter the remaining raw pool to keep only rows where `formation_energy_per_atom` is not null **and** `dft_computed` is `True`.  
  *Implementation*: Extend `code/data_ingestion.py` to read `raw_pool.csv`, apply the filter, and write `data/processed/filtered_pool.csv`.  
  *Verification*: No nulls in `formation_energy_per_atom`, `dft_computed` column is all `True`, and row count is logged in `data/metadata/filtered_counts.json`.  

- [ ] T023 **[US1]** Generate elemental‑property descriptors (average atomic number, electronegativity, atomic radius) using `matminer`’s `ElementProperty` transformer, **excluding** any rows belonging to the test set.  
  *Implementation*: `code/data_ingestion.py` loads `filtered_pool.csv`, drops test‑set indices, applies the transformer, and writes `data/processed/descriptors_pool.csv`.  
  *Verification*: Output CSV contains the three descriptor columns with no missing values; a schema check against `contracts/dataset.schema.yaml` passes.  

- [ ] T024 **[US1]** Impute any remaining missing descriptor values (mean imputation), drop rows with > 50 % missing descriptors, and produce the final training pool `data/processed/full_pool_final.csv`.  
  *Implementation*: `code/data_ingestion.py` reads `descriptors_pool.csv`, computes column means, fills missing entries, removes overly incomplete rows, and writes the final file. It also creates `data/results/ingestion_log.json` summarising dropped rows and imputation statistics.  
  *Verification*: `full_pool_final.csv` exists, contains the three descriptor columns, and the log file reports < 1 % rows dropped.  

---

## Phase 2 – Representative Stratified Sample (RSS) (pending)

- [ ] T025 **[US1]** Build a **Representative Stratified Sample** (`rss_pool.csv`) of size `rss_size` (from `rss_config.json`) by stratified random sampling on `formation_energy_per_atom` (same bins as the test split).  
  *Implementation*: `code/rss_generation.py` reads `full_pool_final.csv`, performs the stratified draw, and writes `data/processed/rss_pool.csv`.  
  *Verification*: The distribution of `formation_energy_per_atom` in `rss_pool.csv` matches that of `full_pool_final.csv` within a Jensen‑Shannon divergence ≤ 0.02; the divergence value is recorded in `data/metadata/rss_stratification.json`.  

---

## Phase 3 – Nested sparsity subsets (pending)

- [ ] T026 **[US2]** Generate strictly **nested** sparsity subsets for the seven levels defined in `config.SPATIALITY_LEVELS` (e.g., 5 %, 10 %, 20 %, 40 %, 60 %, 80 %, 100 %).  
  *Implementation*: `code/sparsity_generation.py` reads `rss_pool.csv` and, for each seed in `config.SEED_LIST`, samples the required percentage **from the immediate larger parent subset** to guarantee nesting. Files are written as `data/processed/sparsity_<level>pct_seed<seed>.csv`.  
  *Verification*: For each seed, a script verifies that `sparsity_Apct_seedX.csv` ⊂ `sparsity_Bpct_seedX.csv` whenever A < B, and writes a boolean report `data/metadata/nesting_verification_seed<seed>.json`.  

- [ ] T027 **[US2]** Record metadata for every generated subset (seed, percentage, checksum, row indices) in JSON files `data/metadata/sparsity_<level>_<seed>.json`.  
  *Implementation*: Integrated in `code/sparsity_generation.py`.  
  *Verification*: All expected JSON files exist; each contains keys `seed`, `percentage`, `checksum`, and `row_indices`.  

---

## Phase 4 – Model training & metric collection (pending)

- [ ] T028 **[US2]** Train **Gaussian Process Regression (FITC)** models on each sparsity subset (CPU‑only) and evaluate on the fixed test set.  
  *Implementation*: `code/model_training.py` loops over all `sparsity_*.csv` files, fits a FITC‑approximated GPR (using `gpytorch` with 500 inducing points), computes RMSE, MAE, predictive variance, and calibration slope, appending rows to `data/results/metrics.csv`.  
  *Verification*: `metrics.csv` conforms to `contracts/metrics.schema.yaml`; a summary `data/results/training_log.json` records training time per run and confirms no CUDA usage.  

- [ ] T037 **[US2]** Train **Random Forest** models on each sparsity subset (CPU‑only) and evaluate on the fixed test set.  
  *Implementation*: `code/model_training.py` (RF branch) loops over the same subset files, fits an RF (`n_estimators=500`), computes RMSE, MAE, predictive variance, and calibration slope, appending rows to `data/results/metrics.csv`.  
  *Verification*: Same as T028; RF results are distinguished by `model_type = "RF"` in `metrics.csv`.  

- [ ] T028b **[US2]** Ensure chunked processing to stay within the 7 GB RAM limit for the largest subset (≈ 150 k rows).  
  *Implementation*: `model_training.py` uses `chunked_iterator()` from T016 when loading feature matrices.  
  *Verification*: Peak memory usage (captured via `psutil`) stays below 6.5 GB; the log `data/results/memory_usage.json` records the peak for each run.  

- [ ] T035a **[US3]** Generate **uncertainty calibration report** for GPR models and validate it.  
  *Implementation*: `code/calibration.py` reads GPR predictions on the test set, computes calibration slope and plots predicted variance vs. squared residuals, writes `data/results/calibration_report.json` containing fields `calibration_slope`, `r2`, `details`. The task also runs `code/utils/contract_validator.py` against a calibration schema (included in `contracts/`).  
  *Verification*: The JSON file exists, passes schema validation, and the slope is logged in `data/results/training_log.json`.  

---

## Phase 5 – Statistical analysis & visualization (pending)

- [ ] T030 **[US3]** Produce **learning‑curve plots** (`data/results/plots/learning_curve.png`) showing RMSE vs. dataset size with error bars representing the standard deviation across seeds for each model type.  
  *Implementation*: `code/statistical_analysis.py` reads `metrics.csv`, aggregates per level/seed/model, and uses `matplotlib`/`seaborn` to create the plot.  
  *Verification*: Plot file exists, PNG is non‑empty, and a checksum is stored in `data/metadata/learning_curve_hash.json`.  

- [ ] T031 **[US3]** Fit a **Linear Mixed‑Effects Model** (`error ~ sparsity_level + (1|seed)`) using `statsmodels.MixedLM` on the RMSE values, saving fixed‑effect estimates and random‑effect variances to `data/results/lmm_fixed_effects.json`.  
  *Implementation*: `code/statistical_analysis.py` performs the fit, extracts the predicted mean error per sparsity level, and writes the JSON.  
  *Verification*: The JSON contains keys `fixed_effects`, `random_effects`, and `model_summary`; a schema check passes.  

- [ ] T032 **[US3]** Conduct **Tukey‑adjusted pairwise contrasts** on the LMM results, storing p‑values in `data/results/tukey_contrasts.json` and flagging any comparisons with `p < 0.05`.  
  *Implementation*: Uses `statsmodels.stats.multicomp.pairwise_tukeyhsd`.  
  *Verification*: JSON includes a list of contrast objects with fields `level_a`, `level_b`, `p_adj`; at least one entry is present.  

- [ ] T033 **[US3]** Perform the **sensitivity analysis** required by FR‑007: compute consecutive‑level slope variance, compare to the 10 % threshold, and write the boolean result plus the numeric variance to `data/results/slope_variance.json`.  
  *Implementation*: Reads `lmm_fixed_effects.json`, calculates finite‑difference slopes, computes variance, and writes the JSON with fields `slope_variance`, `threshold_met`.  
  *Verification*: The JSON file exists and `threshold_met` is either `true` or `false`.  

- [ ] T034 **[US3]** Assemble a **final markdown report** (`data/results/final_report.md`) summarising all findings (learning curves, statistical significance, slope‑variance outcome) while explicitly avoiding causal language.  
  *Implementation*: `code/report_generator.py` templates the markdown, inserts figures and tables, and writes the file.  
  *Verification*: Report renders without markdown errors; it references all required artefacts and includes a “Results Hand‑off” section for downstream paper generation.  

- [ ] T035 **[ ]** Validate the complete pipeline end‑to‑end: run the top‑level command `python -m src.run_pipeline` (or the equivalent entry point defined in `quickstart.md`).  
  *Verification*: The command finishes within the 6‑hour CI window, exits with status 0, and all files listed in the “Artifacts” section of `quickstart.md` are present and pass their respective schema checks.  

- [ ] T036 **[ ]** Update `docs/quickstart.md` with a reproducible command‑line snippet, environment‑setup instructions, and a note that the pipeline requires a valid `MP_API_KEY`.  
  *Verification*: The documentation builds without broken links, and a fresh CI run that follows the snippet reproduces the full artefact set.  

---

### Dependency graph (high‑level)

```
T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027
                                            ↓
                                         T028 → T028b → T037 → T035a
                                            ↓
                                         T030 → T031 → T032 → T033 → T034
                                            ↓
                                         T035 (end‑to‑end)
```

All tasks respect strict data‑flow ordering; no task that consumes a file runs before the task that produces it.  

---  

*All unchecked tasks above are ready to be implemented; each includes a concrete verification step that the automated analyser can evaluate.*  