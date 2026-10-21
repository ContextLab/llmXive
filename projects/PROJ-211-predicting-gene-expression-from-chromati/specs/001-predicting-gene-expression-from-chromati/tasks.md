# Tasks: Predicting Gene Expression from Chromatin Accessibility in Human Cells  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-predicting-gene-expression-from-chromati/contracts/`, and any existing artifacts.  
All tasks write to project‑owned directories (`code/`, `data/`, `interpretation/`, `figures/`, `docs/`, `logs/`).  
Tasks are ordered to respect data flow; each task lists its verification criteria in indented continuation lines.

---

## Phase 1 – Setup and early end‑to‑end analysis  

- [ ] T002 [US1] Implement a robust ENCODE download script `code/download_encode.py` that streams real resources for each of the five cell lines and writes:   <!-- FAILED-IN-EXECUTION: code/download_encode.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_download_encode.sh exit=1 -->
  – `data/raw/encode_counts_{cell_line}.csv` (RNA‑seq gene‑quantification TSV),  
  – `data/raw/encode_peaks_{cell_line}.bed` (narrowPeak BED),  
  – `data/raw/gene_coords.bed` (TSS BED derived from GENCODE hg38).  
  The script records SHA‑256 checksums in `data/raw/checksums.csv`, aborts on any HTTP error, empty response, or checksum mismatch, and never falls back to synthetic data.  
  **Verification**: After execution, all listed files exist, are non‑empty, match recorded checksums, and `pytest tests/integration/test_download.py` validates column headers and schema compliance.

- [ ] T003 [US1] Implement the preprocessing pipeline `code/preprocess.py` that, for each cell line, performs:  
  1. **Bin aggregation** (FR‑002): split the ±50 kb window around each gene’s TSS into 200 equal‑width bins, exclude the promoter region (±2 kb), sum peak scores per bin → `data/processed/{cell_line}_binned_features.csv` (columns `bin_1` … `bin_200`).  
  2. **Gene filtering** (FR‑003): remove genes with zero expression across *all* cell lines → `data/processed/filtered_expression.csv`.  
  3. **Log‑pseudocount** (FR‑004): compute `log(count + 1)` → `data/processed/log_expression.csv`.  
  4. **Median imputation** (FR‑005): per‑bin median across genes → `data/processed/imputed_binned_features.csv`.  
  5. **Merging**: combine the 200‑bin feature matrix with the log‑expression target → `data/processed/merged_matrix_{cell_line}.csv`.  
  All produced CSVs must conform to `dataset.schema.yaml` and contain no NaNs.  
  **Verification**: Running `python -m code.preprocess` exits 0, each output file exists, has exactly 200 bin columns plus identifiers, passes JSON‑Schema validation (`pytest tests/unit/test_preprocess.py`), and checksum entries are added to `data/raw/checksums.csv`.

- [ ] T004 [US1] Compute gene‑category metrics (`code/compute_gene_categories.py`):  
  – Calculate coefficient of variation (CV) of log‑expression across the five cell lines → `data/processed/gene_cv.csv`.  
  – Derive housekeeping genes (CV < 0.2) → `data/processed/housekeeping_genes.csv`.  
  – Derive cell‑type‑specific genes (CV > 0.5) → `data/processed/cell_type_specific_genes.csv`.  
  – Subset the merged matrix to housekeeping genes → `data/processed/housekeeping_matrix.csv`.  
  All CSVs must obey the schema and be checksum‑recorded.  
  **Verification**: Files exist, CV thresholds are respected, gene lists are disjoint, and `pytest tests/unit/test_gene_categories.py` succeeds.

---

## Phase 2 – Complete study and validation  

- [ ] T005 [US2] Train Elastic Net models per cell line (`code/train.py`) with the following constraints:  
  – Use Elastic Net (`alpha = 0.5` fixed, `l1_ratio` tuned via leave‑one‑out cross‑validation on the full 200‑bin feature set).  
  – **Reproducibility**: set `random_state=42` and record the seed in the model metadata JSON (`data/models/elastic_net_{cell_line}_metadata.json`).  
  – **CPU‑only enforcement**: assert `OMP_NUM_THREADS=1` before training and check that no GPU‑specific libraries are imported.  
  – Serialize the final model to `data/models/elastic_net_{cell_line}.pkl`.  
  – Save optimal hyperparameters (`l1_ratio`) to `data/models/hyperparams_{cell_line}.json`.  
  – Record per‑fold metrics (`fold`, `r2`, `pearson_r`, `p_value`) in `data/processed/cv_scores_{cell_line}.json`.  
  – Log wall‑time, CPU usage, and peak RAM to `logs/profiling_{cell_line}.log` (enforce `OMP_NUM_THREADS=1`).  
  **Verification**: All model files and JSON score files exist, conform to `model_output.schema.yaml`, profiling logs are present, `pytest tests/integration/test_training.py` passes, and the script asserts the seed and CPU constraints.

- [ ] T006 [US2] Evaluate model performance (`code/evaluate.py`):  
  1. Aggregate CV scores across folds to produce `data/processed/correlations_{cell_line}.csv` containing Pearson r, raw p‑value, and **Bonferroni‑corrected p‑value using m = 5** (FR‑006).  
  2. Compute R² for housekeeping genes → `data/processed/housekeeping_r2.csv` (FR‑009).  
  3. Compute R² for cell‑type‑specific genes → `data/processed/celltype_r2.csv` (FR‑010).  
  4. Calculate performance gap ΔR² = R²_housekeeping − R²_celltype for each cell line → `data/processed/performance_gap.csv`.  
  5. Perform cross‑cell‑line external validation (train on four lines, test on the held‑out fifth) → `data/processed/external_validation_r2.csv`.  
  **Verification**: All CSVs exist, contain finite numeric values, match the schemas, the Bonferroni correction uses the correct `m=5`, and `pytest tests/integration/test_evaluation.py` succeeds.

- [ ] T007 [US3] Perform feature‑importance and proximity analysis (`code/analyze.py`):  
  – Extract non‑zero Elastic Net coefficients, rank by absolute magnitude, and write `interpretation/feature_importance.csv` (fields: `gene_id`, `bin_id`, `coefficient`, `distance_to_tss`, `within_10kb`).  
  – Compute the proportion of the top‑100 bins that lie within ±10 kb of the TSS; write the statistic to `interpretation/tss_proximity_stats.json`.  
  – Run a **deterministic** permutation‑based enrichment test (1 000 permutations, `np.random.seed(42)`) to generate an empirical p‑value → `interpretation/sc003_enrichment.json`.  
  – **Enforce SC‑003**: abort with a non‑zero exit code if the observed proportion is < 80 % (hard failure).  
  – Log the random seed used for the permutation test in the output JSON for reproducibility.  
  **Verification**: Files exist, schema‑validated, permutation test output present, the task exits 0 only when the ≥ 80 % rule holds, and `pytest tests/unit/test_feature_importance.py` checks both the proportion and the failure condition.

- [ ] T008 [US3] Generate final figures and summary table (`code/visualize.py`):  
  – Bar plot of R² per cell line → `figures/r2_by_cell_line.png`.  
  – Scatter plots of predicted vs. observed expression for each cell line (identity line included) → `figures/predicted_vs_observed_{cell_line}.png`.  
  – Consolidated results table → `data/results/summary_table.csv` (columns: `cell_line`, `R2`, `Pearson_r`, `p_value_corrected`, `external_R2`, `ΔR2`).  
  **Verification**: All PNG files are non‑empty, the CSV matches the source metrics, and `pytest tests/integration/test_visualization.py` confirms reproducibility.

- [ ] T009 [US3] Execute a full end‑to‑end run on **real ENCODE inputs** (no synthetic data) using the documented pipeline order (`download_encode → preprocess → train → evaluate → analyze → visualize`). Capture a combined profiling log `logs/full_pipeline.log`. Ensure **total wall‑time ≤ 6 h** and **peak RAM ≤ 7 GB**, and **per‑cell‑line runtime ≤ 2 h** (checked by parsing the log).  
  **Verification**: After the run, `logs/full_pipeline.log` reports runtime and memory within limits for each cell line and overall, all intermediate and final artifacts are present, and the complete test suite (`pytest -q`) exits with 0.

- [ ] T014 [US2] Verify per‑cell‑line runtime limits (`code/verify_runtime.py`): parse `logs/profiling_*.log` for each cell line, assert wall‑time ≤ 2 h and peak RAM ≤ 7 GB, exit non‑zero otherwise.  
  **Verification**: Integrated into T009; the pipeline fails if any cell line exceeds the bound.

---

## Phase 3 – Reproducible results and paper handoff  

- [ ] T010 [US3] Draft the regulatory‑insights report `interpretation/regulatory_insights_report.md` that for each cell line includes: overall R², Pearson r, external‑validation R², top‑10 features (bin ID, coefficient, distance to TSS, within‑10kb flag), and the performance‑gap ΔR². Every numeric value must be programmatically linked to its source CSV/JSON artifact. Append a caveat paragraph explicitly stating: (a) the analysis captures statistical association, not causation; (b) bulk profiles average over cellular heterogeneity; (c) the ±50 kb window excludes distal enhancers; (d) the modest sample size limits statistical power.  
  **Verification**: `pytest tests/integration/test_report_consistency.py` confirms that each number in the markdown matches the corresponding artifact and that the caveat paragraph is present.

- [ ] T011 [US3] Consolidate all limitation statements into a single master file `docs/LIMITATIONS_MASTER.md`. Include the four points from the caveat above plus any additional reviewer‑raised concerns (e.g., variance‑filter effect, promoter exclusion). Update any legacy “Limitations” references in the repository to point to this file.  
  **Verification**: Added script `code/verify_limitations.py` that checks (a) the file exists, (b) it contains all required sections, and (c) a repository‑wide grep for “Limitations” returns only this path. The task runs the script and expects exit code 0.

- [ ] T012 [US3] Write a reproducible workflow guide `quickstart.md` that:  
  – Lists exact commands to run each stage (`python -m code.download_encode`, `python -m code.preprocess`, `python -m code.train`, `python -m code.evaluate`, `python -m code.analyze`, `python -m code.visualize`).  
  – Specifies the Python version (3.11) and that the environment should be created from `requirements.txt`.  
  – Provides a clean‑run command that removes `data/processed/*`, `data/models/*`, `interpretation/*`, and `logs/*` before re‑execution.  
  – Mentions the need for at least 2 CPU cores, < 7 GB RAM, and < 6 h wall‑time.  
  **Verification**: Added `tests/integration/test_quickstart.py` that clones the repo in a temporary directory, follows the guide, and asserts that all expected artifacts appear and that the full test suite passes. The task runs this test and expects exit code 0; also linted with `markdownlint`.

- [ ] T013 [US3] Create the paper‑stage handoff manifest `docs/paper_handoff.yaml` enumerating versioned data files (paths and SHA‑256 checksums) for: processed matrices, model artifacts, evaluation results, figures, and tables. Include a concise “Methods” block that references the task IDs that generated each artifact. Validate the manifest against `docs/paper_handoff_schema.yaml` (provided by the platform) and ensure `python -m code.verify_handoff` exits 0.  
  **Verification**: Manifest file exists, passes schema validation, and the verification script succeeds.

---  

*All tasks above are unchecked; they will be marked complete by the execution stage when their respective verification suites pass.*  