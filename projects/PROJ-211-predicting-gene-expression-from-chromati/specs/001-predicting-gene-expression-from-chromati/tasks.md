# Tasks: Predicting Gene Expression from Chromatin Accessibility in Human Cells

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-predicting-gene-expression-from-chromati/contracts/`, and existing verified artifacts.

The pipeline must use **real ENCODE data** for scientific results; synthetic data is generated **only** for CI validation and never substitutes for real results. All artifacts are written under project‑owned directories (`code/`, `data/`, `interpretation/`, `figures/`, `docs/`, `logs/`). Tasks are ordered to respect data flow.

---

## Phase 1 – Setup and first end‑to‑end analysis

| Goal | Run an executable analysis on a small real (or CI‑synthetic) input set early. |
|------|--------------------------------------------------------------------------------|

- [ ] T001 [US1] Implement a deterministic synthetic data generator `code/generate_data.py` that
  – seeds NumPy with `42`;  
  – writes `data/raw/synthetic_counts.csv` (RNA‑seq counts) and `data/raw/synthetic_peaks.bed` (peak calls) for the five cell lines (GM12878, K562, HMEC, IMR90, HepG2);  
  – validates both outputs against the YAML schema `specs/001-predicting-gene-expression-from-chromati/contracts/dataset_schema.schema.yaml` using `jsonschema`;  
  – records SHA‑256 checksums in `data/raw/checksums.csv`;  
  – raises on any mismatch (no silent fallback).  
  **Verification**: Run the generator with `python -m code.generate_data` **or** `python code/generate_data.py`; it must exit 0, both files exist, are non‑empty, and `pytest tests/unit/test_generate_data.py` passes.

- [ ] T002 [US1] Implement a robust ENCODE download script `code/download_encode.py` that streams real resources and records SHA‑256 checksums in `data/raw/checksums.csv`. For each of the five cell lines it must download: <!-- FAILED: unspecified --> <!-- FAILED-IN-EXECUTION: code/download_encode.py exit=1 -->
  – RNA‑seq gene‑quantification TSV → `data/raw/encode_counts_{cell_line}.csv`  
  – DNase‑seq/ATAC‑seq narrowPeak BED → `data/raw/encode_peaks_{cell_line}.bed`  
  – GENCODE hg38 gene‑coordinates GTF (reduced to TSS BED) → `data/raw/gene_coords.bed`  
  The script aborts on any HTTP error or empty response.  
  **Verification**: All files exist, are non‑empty, checksums match those recorded, and `pytest tests/integration/test_download.py` validates column headers and schema compliance.

- [ ] T003 [US1] Implement preprocessing `code/preprocess.py` that, for each cell line, performs the following steps and writes the indicated artifacts:   <!-- FAILED-IN-EXECUTION: code/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/preprocess.py exit=1 -->
  1. **Bin aggregation** (FR‑002): split the ±50 kb window around each TSS into 200 fixed‑width bins, exclude the promoter region (TSS ± 2 kb), sum peak scores per bin → `data/processed/{cell_line}_binned_features.csv` (200 columns `bin_1` … `bin_200`).  
  2. **Gene filtering** (FR‑003): remove genes with zero expression across all five cell lines → `data/processed/filtered_expression.csv`.  
  3. **Log‑pseudocount** (FR‑004): compute `log(count + 1)` → `data/processed/log_expression.csv`.  
  4. **Median imputation** (FR‑005): per‑bin median across genes → `data/processed/imputed_binned_features.csv`.  
  5. **Merge**: combine the 200‑bin feature matrix with the log‑expression target → `data/processed/merged_matrix_{cell_line}.csv`.  
  **Verification**: Each CSV has exactly 200 bin columns plus identifiers, contains no NaNs, validates against `specs/001-predicting-gene-expression-from-chromati/contracts/dataset.schema.yaml`, **and** the merged matrix file exists, is non‑empty, and passes the same schema validation.

- [ ] T004 [US1] Extend `code/preprocess.py` (or a companion script) to compute gene‑category metrics and write:  
  – Coefficient of variation (CV) of log‑expression across cell lines → `data/processed/gene_cv.csv`.  
  – Housekeeping genes (CV < 0.2) → `data/processed/housekeeping_genes.csv`.  
  – Cell‑type‑specific genes (CV > 0.5) → `data/processed/cell_type_specific_genes.csv`.  
  – Housekeeping‑only merged matrix → `data/processed/housekeeping_matrix.csv`.  
  **Verification**: Category files respect the CV thresholds, are disjoint, and the matrix contains exactly the rows listed in `housekeeping_genes.csv`; `pytest tests/unit/test_gene_categorization.py` passes.

- [ ] T015 [US1] Create a consolidated binned‑feature file `data/processed/tss_binned_features.csv` that aggregates the per‑cell‑line bin matrices into a single feature matrix (genes × 200 bins) for downstream analyses.  
  **Verification**: File exists, has 200 bin columns, passes schema validation, and checksum is recorded.

---

## Phase 2 – Complete the study and validate its evidence

| Goal | Run the full specified analysis, preserve every population, baseline and scientific constraint. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T005 [US2] Implement Elastic Net training `code/train.py` that, for **each of the five cell lines**, performs LOOCV over the 200‑bin features:  
  – Elastic Net with `l1_ratio=0.5`, `alpha` selected by LOOCV;  
  – Serialize the final model → `data/models/elastic_net_{cell_line}.pkl`;  
  – Save optimal `alpha` → `data/models/lambda_optimal_{cell_line}.json`;  
  – Record per‑fold metrics (`fold`, `r2`, `pearson_r`, `p_value`) → `data/processed/cv_scores_{cell_line}.json`.  
  – Enforce **serial execution** on the runner (`OMP_NUM_THREADS=1` or equivalent) and write a profiling log entry for each cell line (wall‑time, CPU usage, peak RAM).  
  **Verification**: Model files exist, `cv_scores_*.json` conforms to `model_output.schema.yaml`, profiling entries are present in `logs/profiling.log`, and `pytest tests/integration/test_training_loop.py` passes.

- [ ] T006 [US2] Implement evaluation `code/evaluate.py` that consumes the CV scores and model predictions to produce:  
  1. Pearson correlations and raw p‑values per cell line → `data/processed/correlations.csv`.  
  2. Bonferroni‑corrected p‑values (m = 5 cell lines) → added column `p_value_corrected` in the same CSV (FR‑006).  
  3. Housekeeping‑gene R² → `data/processed/housekeeping_r2.csv` (FR‑009).  
  4. Cell‑type‑specific‑gene R² → `data/processed/cell_type_specific_r2.csv` (FR‑010).  
  5. External validation (SC‑006): LOOCV across cell lines (train on four, test on held‑out) → `data/processed/external_validation_r2.csv` (`held_out_cell_line`, `r2`).  
  **Verification**: All CSVs exist, contain finite numeric values, adhere to the respective schemas, and `pytest tests/integration/test_evaluation.py` succeeds.

- [ ] T007 [US3] Implement interpretation `code/analyze.py` that generates:  
  1. Feature‑importance report (non‑zero coefficients ranked by absolute magnitude) → `interpretation/feature_importance.csv` (matches `model_output.schema.yaml` fields).  
  2. TSS‑proximity statistics: percentage of top‑100 coefficients within ±10 kb → `interpretation/tss_proximity_stats.json`. **If the percentage is < 80 % the task must fail** (hard enforcement of SC‑003).  
  3. Performance‑gap report ΔR² = R²(housekeeping) − R²(cell‑type‑specific) per cell line → `interpretation/performance_gap.csv`.  
  **Verification**: Files exist, schema‑validated, and the test suite asserts the ≥ 80 % rule; failure aborts the task.

- [ ] T008 [US3] Generate figures and a summary table programmatically from validated outputs:  
  – `figures/r2_by_cell_line.png` (bar plot of R² for each cell line).  
  – `figures/predicted_vs_observed_{cell_line}.png` (scatter with identity line for each cell line).  
  – `data/results/summary_table.csv` (columns: cell_line, R², Pearson r, corrected p‑value, external‑validation R², ΔR²).  
  **Verification**: Each figure file is non‑empty PNG, the CSV rows exactly match source metrics, and `pytest tests/integration/test_figures_and_table.py` confirms reproducibility.

- [ ] T009 [US3] Perform a **full end‑to‑end re‑run** on the real ENCODE inputs (no synthetic data) using the documented workflow (`code/download_encode.py → code/preprocess.py → code/train.py → code/evaluate.py → code/analyze.py`). Capture a fresh `logs/profiling.log` and verify that total runtime ≤ 6 h and peak RAM ≤ 7 GB.  
  **Verification**: The profiling log reflects the constraints, all artifacts from Phases 1‑2 are regenerated, and the full test suite (`pytest -q`) exits with 0.

---

## Phase 3 – Reproducible results and paper handoff

| Goal | Deliver a concise methods/results account linked to actual outputs; provide a clean handoff to the downstream paper pipeline. |
|------|-------------------------------------------------------------------------------------------------------------------------------|

- [ ] T010 [US3] Draft the regulatory‑insights report `interpretation/regulatory_insights_report.md` that for each cell line includes: overall R², Pearson r, external‑validation R², top‑10 features (with bin ID, coefficient, distance to TSS, within‑10 kb flag), and the performance‑gap ΔR². Every numeric token must be traceable to a row in a CSV/JSON artifact. Append a caveat paragraph that explicitly states: (a) models capture statistical association, not causation; (b) bulk profiles average over single‑cell heterogeneity; (c) the ±50 kb window excludes distal enhancers; (d) small‑N limits statistical power.  
  **Verification**: `pytest tests/integration/test_report_consistency.py` asserts that each number in the markdown matches its source artifact and that the caveat paragraph is present.

- [ ] T011 [US3] Consolidate all limitation statements into a single master file `docs/LIMITATIONS_MASTER.md` covering: bulk‑profile averaging, correlation ≠ causation, ±50 kb window, promoter‑exclusion design, small‑N statistical validity, and any other reviewer‑raised concerns. Update any legacy limitation references to point to this file.  
  **Verification**: The file exists, contains all required sections, and a repository search for “Limitations” returns only this file as the canonical source.

- [ ] T012 [US3] Write a reproducible workflow guide `quickstart.md` that lists exact commands for the full pipeline (download → preprocess → train → evaluate → interpret), specifies Python 3.11 and the `requirements.txt` environment, and provides a clean‑run command that removes `data/processed/*`, `data/models/*`, `interpretation/*`, and `logs/*` before re‑execution.  
  **Verification**: Following the guide in a fresh clone reproduces all artifacts; running `pytest` after the guide’s commands exits 0.

- [ ] T013 [US3] Create the paper‑stage handoff manifest `docs/paper_handoff.yaml` enumerating versioned data files (paths and SHA‑256 checksums) for processed matrices, model artifacts, evaluation results, figures, and tables; include a brief “Methods” block referencing the relevant task IDs.  
  **Verification**: The YAML validates against `docs/paper_handoff_schema.yaml` and `python -m code.verify_handoff` exits 0.
