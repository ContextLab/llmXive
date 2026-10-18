# Tasks: Predicting Gene Expression from Chromatin Accessibility in Human Cells

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-predicting-gene-expression-from-chromati/contracts/`, and any existing verified artifacts.

The pipeline must use **real ENCODE data** for the scientific results; synthetic data is only for CI validation. All artifacts are written under project‑owned directories (`code/`, `data/`, `interpretation/`, `docs/`, `logs/`).  
Each task lists its verification criteria in the indented lines that follow.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T001 [US1] Implement deterministic synthetic data generator `code/generate_data.py` that (a) seeds `numpy.random` with `42`, (b) writes `data/raw/synthetic_counts.csv` and `data/raw/synthetic_peaks.bed` conforming to `specs/001-predicting‑gene‑expression‑from‑chromati/contracts/dataset.schema.yaml`, and (c) validates the outputs against that schema, raising an exception on any mismatch.  
  - **Verification**: `python -m code.generate_data` exits 0, both files exist, are non‑empty, and `pytest tests/unit/test_generate_data.py` (which loads the schema and checks conformity) passes.

- [ ] T002 [US1] Implement robust ENCODE download script `code/download_encode.py` that streams the following real resources (SHA‑256 checksums recorded in `state/projects/PROJ-211-predicting-gene-expression-from-chromati.yaml`):  
  - RNA‑seq count matrix for each of the five cell lines (GM12878, K562, HMEC, IMR90, HepG2) → `data/raw/encode_counts_{cell_line}.csv`  
  - DNase/ATAC‑seq narrowPeak files for the same cell lines → `data/raw/encode_peaks_{cell_line}.bed`  
  - GENCODE hg38 TSS coordinates → `data/raw/gene_coords.bed`  
  The script must raise on any HTTP error; no synthetic fallback is permitted.  
  - **Verification**: After execution, each file exists, checksum matches the recorded value, and `pytest tests/integration/test_download.py` (which checks file headers and schema compliance) passes.

- [ ] T003 [US1] Implement preprocessing script `code/preprocess.py` that performs the following steps for each cell line:  
  1. **Bin aggregation** – split the ±50 kb window around each TSS into 200 fixed‑width bins (100 bins covering ±10 kb, 100 bins covering the remaining ±40 kb) and compute the sum of peak scores per bin, storing results in `data/processed/{cell_line}_binned_features.csv`.  
  2. **Gene filtering** – remove genes with zero expression across all five cell lines, producing `data/processed/filtered_expression.csv`.  
  3. **Log‑pseudocount** – transform raw counts to `log(count + 1)` and write `data/processed/log_expression.csv`.  
  4. **Median imputation** – impute missing bin values per bin with the median across genes, outputting `data/processed/imputed_expression.csv`.  
  5. **Merge** – create a joint matrix `data/processed/merged_matrix_{cell_line}.csv` that concatenates the 200‑bin feature matrix with the corresponding log‑expression vector.  
  - **Verification**: Each CSV has the expected number of columns (200 bin columns + identifiers), contains no `NaN`s, passes schema validation (`dataset.schema.yaml`), and unit tests in `tests/unit/test_preprocess.py` succeed.

- [ ] T004 [US1] Extend `code/preprocess.py` to compute gene‑category metrics: calculate the coefficient of variation (CV) of log‑expression across cell lines, then write:  
  - `data/processed/housekeeping_genes.csv` (genes with CV < 0.2)  
  - `data/processed/cell_type_specific_genes.csv` (genes with CV > 0.5)  
  - `data/processed/housekeeping_matrix.csv` (merged feature+target matrix restricted to housekeeping genes)  
  - **Verification**: Both category files obey their respective CV bounds, are disjoint, and the matrix file contains exactly the rows listed in `housekeeping_genes.csv`. Tests in `tests/unit/test_gene_categorization.py` pass.

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] T005 [US2] Implement Elastic Net training script `code/train.py` that, for each cell line, trains a single Elastic Net model (`l1_ratio=0.5`) with the regularization strength `alpha` selected by **Leave‑One‑Out Cross‑Validation (LOOCV)** on the 200‑bin features. The script must:  
  1. Serialize the optimal model to `data/models/elastic_net_{cell_line}.pkl`.  
  2. Record the chosen `alpha` in `data/models/lambda_optimal_{cell_line}.json`.  
  3. Produce per‑fold CV metrics (`fold`, `r2`, `pearson_r`, `p_value`) in `data/processed/cv_scores_{cell_line}.json`.  
  4. Log wall‑time and peak RAM usage per cell line to `logs/profiling.log` and enforce **≤ 2 h runtime and ≤ 7 GB RAM** per model.  
  - **Verification**: All model files exist, `cv_scores_*.json` conforms to `model_output.schema.yaml`, profiling log shows limits respected, and integration test `tests/integration/test_training_loop.py` passes.

- [ ] T006 [US2] Implement evaluation script `code/evaluate.py` that consumes the CV scores and model predictions to compute:  
  1. Pearson correlations and raw p‑values for each cell line, writing `data/processed/correlations.csv`.  
  2. Bonferroni‑corrected p‑values (m = 5 cell lines) and adds a column `p_value_corrected`.  
  3. R² for housekeeping genes → `data/processed/housekeeping_r2.csv`.  
  4. R² for cell‑type‑specific genes → `data/processed/cell_type_specific_r2.csv`.  
  5. External validation: train on four cell lines, test on the held‑out fifth (rotating), and write `data/processed/external_validation_r2.csv` (columns: `held_out_cell_line`, `r2`).  
  - **Verification**: All CSVs exist, contain finite numeric values, adhere to the schema, and `pytest tests/integration/test_evaluation.py` succeeds.

- [ ] T007 [US3] Implement interpretation script `code/analyze.py` that produces:  
  1. **Feature importance** – extract non‑zero Elastic Net coefficients, rank by absolute magnitude, and write `interpretation/feature_importance.csv` (columns: `gene_id`, `bin_id`, `coefficient`, `distance_to_tss`, `within_10kb`).  
  2. **TSS proximity stats** – compute the percentage of the top‑100 coefficients that lie within ±10 kb of the TSS; enforce **≥ 80 %** (task fails otherwise) and store the statistic in `interpretation/tss_proximity_stats.json`.  
  3. **Performance gap** – calculate ΔR² = R²(housekeeping) − R²(cell‑type‑specific) for each cell line and write `interpretation/performance_gap.csv`.  
  - **Verification**: Files exist, `feature_importance.csv` matches `model_output.schema.yaml` fields, `tss_proximity_stats.json` parses and meets the 80 % threshold, and unit tests `tests/unit/test_interpretation.py` pass.

- [ ] T008 [US3] Draft the regulatory‑insights summary `interpretation/regulatory_insights_report.md` that includes, for every cell line:  
  - Overall R² and Pearson r (from `correlations.csv`)  
  - External‑validation R² (from `external_validation_r2.csv`)  
  - Top‑10 features with distances and within‑10 kb flag  
  - Performance gap values (from `performance_gap.csv`)  
  - A prefixed caveat paragraph referencing `docs/LIMITATIONS_MASTER.md`.  
  - **Verification**: Every numeric token in the report can be traced back to a row in the corresponding CSV/JSON file; a test `tests/integration/test_report_consistency.py` asserts the presence of the caveat header.

- [ ] T009 [US3] Consolidate all limitation statements into a single source file `docs/LIMITATIONS_MASTER.md` (including bulk‑profile averaging, correlation ≠ causation, ±50 kb window limitation, and any reviewer‑suggested caveats). Update any legacy limitation references (e.g., `docs/regulatory_context.md`) to point to this master file.  
  - **Verification**: The master file exists, contains all required limitation sections, and a search for the phrase “Limitations” in the repository returns only this file.

- [ ] T010 [US3] Write a reproducible workflow guide `quickstart.md` that lists the exact commands to run the full pipeline on real ENCODE data from start to finish (download → preprocess → train → evaluate → interpret). The guide must:  
  1. Invoke each script with explicit paths.  
  2. State the required Python version and that all dependencies are listed in `requirements.txt`.  
  3. Include a “clean‑run” command that deletes `data/processed/*`, `data/models/*`, and `interpretation/*` before re‑execution.  
  - **Verification**: Executing the commands in a fresh clone reproduces all artifacts listed in the verification steps above; a CI job using this guide exits 0.

- [ ] T011 [US3] Perform a **full end‑to‑end re‑run** using the workflow in `quickstart.md` on the real ENCODE inputs (no synthetic data). Capture the final profiling log (`logs/profiling.log`) and confirm that all runtime and memory constraints are satisfied. Commit the regenerated artifacts to the repository (they will be hashed by the platform).  
  - **Verification**: The log file shows ≤ 2 h and ≤ 7 GB per cell line, all previous verification tests still pass, and the platform’s artifact hash table updates without errors.

---

## Phase 3 – Reproducible results and handoff to the paper pipeline  

- [ ] T012 [US3] Create the handoff manifest `docs/paper_handoff.yaml` that enumerates:  
  - Versioned data files (paths and SHA‑256 checksums) for all processed matrices, model artifacts, and evaluation results.  
  - Locations of figures/tables to be generated by the downstream paper pipeline (e.g., `figures/r2_by_cell_line.png` will be produced later).  
  - A brief “Methods” block summarizing the computational steps (referencing the task IDs).  
  - **Verification**: The YAML file validates against a minimal schema (`docs/paper_handoff_schema.yaml`) and a sanity‑check script `code/verify_handoff.py` runs without error.

--- 

### Dependency & Requirement Mapping

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| **FR‑001** | T002 |
| **FR‑002‑005** | T003 |
| **FR‑006** | T006 |
| **FR‑007‑010** | T005, T006, T007 |
| **FR‑011** | T008 |
| **SC‑001** | T005 |
| **SC‑002** | T002, T003, T005 (CPU‑only) |
| **SC‑003** | T007 (≥ 80 % within 10 kb) |
| **SC‑004** | T008 (traceable report) |
| **SC‑005** | T002, T003 (memory‑friendly streaming) |
| **SC‑006** | T006 (external validation) |
| **US‑1‑3** | T001‑T008 (full end‑to‑end) |
| **External validation** | T006 |
| **Reproducibility** | T010‑T012 |

All tasks are ordered to respect data flow: download → preprocess → categorization → training → evaluation → interpretation → documentation → final handoff.
