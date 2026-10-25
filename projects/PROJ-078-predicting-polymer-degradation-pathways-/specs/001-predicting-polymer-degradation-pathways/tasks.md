# Tasks: Predicting Polymer Degradation Pathways with Graph Neural Networks  

**Inputs**: `spec.md`, `plan.md`, `tasks_template.md`, all contracts in `specs/001-polymer-degradation/`.  

The tasks are ordered to respect data flow and to produce an early end‑to‑end runnable result. Parallel‑eligible tasks are marked **[P]**; story labels (**[US1]**, **[US2]**, **[US3]**) indicate which user story the task satisfies.

---  

- [ ] **T001** Create the required project directory tree  

  `mkdir -p code/ data/raw/ data/processed/ data/augmented/ data/external/ data/reports/ data/output/ tests/ state/ state/projects/`  

  *Verification*: Run `test -d code && test -d data/raw && test -d data/processed && test -d data/augmented && test -d data/external && test -d data/reports && test -d data/output && test -d tests && test -d state && test -d state/projects`. Log the result of `tree -a .` to `state/dir_structure.txt`.  

- [ ] **T001b** Generate a recursive directory listing with timestamp  

  ```bash
  echo "Setup run at $(date --iso-8601=seconds)" > state/setup_log.txt
  tree -a . >> state/setup_log.txt
  ```  

  *Verification*: Ensure `state/setup_log.txt` exists, contains the word “Setup run at”, and includes a directory tree.  

- [ ] **T000** Create a seed‑pinning helper  

  **File**: `code/seed.py`  

  ```python
  import random, os, numpy as np, torch
  def set_seed(seed: int = 42):
      random.seed(seed)
      np.random.seed(seed)
      torch.manual_seed(seed)
      os.environ["PYTHONHASHSEED"] = str(seed)
  ```  

  *Verification*: Import `code.seed` in all scripts and call `set_seed()`; run `python -c "import code.seed; code.seed.set_seed(); print('seed set')"` successfully.  

- [ ] **T003** Configure strict linting and verify it passes  

  *Create* `code/.ruff.toml` with the repository‑standard strict rules (already present).  

  *Run* `ruff check code/ --exit-zero` and capture stdout/stderr to `state/ruff_check.log`.  

  *Verification*: `grep -q "No issues found" state/ruff_check.log` must succeed and the command must exit with status 0.  

- [ ] **T004** Add deterministic testing configuration  

  *Create* `pytest.ini` containing  

  ```
  [pytest]
  addopts = --random-order-seed=42 -vv
  ```  

  *Create* `tests/conftest.py` that pins random seeds for `random`, `numpy`, and `torch` to 42 (using `code.seed.set_seed`).  

  *Run* `pytest --collect-only` and write the output to `state/pytest_collect.log`.  

  *Verification*: `state/pytest_collect.log` must contain “collected”.  

- [ ] **T005** [US1] Implement real‑data ingestion with exponential backoff  

  **File**: `code/ingest.py`  

  - Download polymer degradation records **only** from **NIST Chemistry WebBook** (`[UNRESOLVED-CLAIM: https://webbook.nist.gov/api/v1/chemical/...` — HTTP 404]) and **Materials Project** (`https://materialsproject.org/rest/v2/materials`).  
  - Use `utils.exponential_backoff` (max 3 retries, jitter) for any HTTP 429 response.  
  - Stream the data, de‑duplicate on canonical SMILES, and write to `data/raw/combined.parquet`.  
  - Log API interactions, retries, and any errors to `state/ingest_error.log`.  

  *Verification*: After running `python -m code.ingest`, confirm `data/raw/combined.parquet` exists, contains ≥ 100 rows, and that `state/ingest_error.log` records any retries.  

- [ ] **T006** [US1] Validate and (if needed) apply rule‑based synthetic labels  

  **File**: `code/label_validation.py`  

  - Scan `data/raw/combined.parquet` for missing `label` fields.  
  - Apply synthetic labeling **only** when a SMART‑rule matches (e.g., ester → hydrolysis, aromatic → photolysis).  
  - Record the source of each label in a new column `label_source` (`curated` or `synthetic`).  
  - Abort with a clear error (and log to `state/label_error.log`) if **all** records lack a curated label after synthetic attempts (FR‑008).  
  - Save the labelled table to `data/raw/labeled.parquet`.  

  *Verification*: `state/label_validation.log` must list counts of curated vs synthetic labels and contain no “FATAL” line.  

- [ ] **T006b** Compute ingestion success‑rate metric  

  **File**: `code/ingestion_success.py`  

  - Compare the number of records in `data/raw/combined.parquet` with the number of records that have valid SMILES, environmental parameters, and a label after `label_validation.py`.  
  - Write the success rate (percentage) to `state/ingestion_success_rate.txt`.  

  *Verification*: The file must contain a numeric value ≥ 95.0.  

- [ ] **T007** [US1] Create the external validation set (≥ 30 curated records)  

  **File**: `code/create_external_validation.py`  

  - Filter `data/raw/labeled.parquet` for `label_source == "curated"` and de‑duplicate against the training pool.  
  - If fewer than 30 records are found, exit with error and write to `state/external_validation_error.log`.  
  - Write the set to `data/external/validation.parquet`.  

  *Verification*: `data/external/validation.parquet` exists and `python -c "import pandas as pd; print(pd.read_parquet('data/external/validation.parquet').shape[0])"` prints a number ≥ 30.  

- [ ] **T008** [US1] Preprocess records into RDKit molecular graphs  

  **File**: `code/preprocess.py`  

  - Load `data/raw/labeled.parquet`.  
  - For each record:  
    1. Parse SMILES with RDKit; on failure, skip and log the SMILES to `state/invalid_smiles.log`.  
    2. Detect ester functional group via SMARTS `C(=O)O`; retain only records where `is_polyester == True`.  
    3. Impute missing environmental values (temp = 25 °C, pH = 7, UV = 0) and flag the record in `validation_flag` (`missing_env`).  
    4. Build a `MolecularGraph` object (nodes, edges, global_features) and serialize with `pickle`.  
  - Save cleaned `PolymerRecord`s to `data/processed/records.parquet`.  
  - Save the **pre‑augmentation** graph dataset to `data/processed/pre_augmented_graph_dataset.parquet`.  
  - Also write individual pickles to `data/processed/graphs/`.  

  *Verification*: `state/preprocess.log` must contain totals processed, skipped, and flagged; the two output files must exist.  

- [ ] **T009** Compute SHA‑256 checksums for raw and processed artifacts  

  **File**: `code/checksums.py`  

  - Compute checksums for `data/raw/combined.parquet`, `data/raw/labeled.parquet`, `data/processed/records.parquet`, `data/processed/pre_augmented_graph_dataset.parquet`, and the entire `data/processed/graphs/` directory (hash each file).  
  - Write a YAML map to `state/artifact_hashes.yaml` (keys = relative paths, values = hex digests).  

  *Verification*: `state/artifact_hashes.yaml` exists and contains an entry for each listed artifact.  

- [ ] **T010** Perform power‑analysis and decide validation strategy  

  **File**: `code/power_analysis.py`  

  - Load `data/processed/records.parquet` and count `n`.  
  - If `n >= 150`, set strategy = `"5fold"`; else set strategy = `"loo"` and write a warning JSON to `data/reports/power_analysis_warning.json` with `{"n": n, "strategy": strategy, "warning": n < 150}`.  
  - Store the decision in `state/validation_strategy.json`.  

  *Verification*: `state/validation_strategy.json` must contain both `n` and `strategy` fields; the warning file must exist when `n < 150`.  

- [ ] **T011** [US2] Implement data augmentation (bond rotation + atom masking) exactly 2× and measure runtime  

  **File**: `code/augment.py`  

  - Read `data/processed/graphs/` and apply two deterministic augmentations per record:  
    1. Random bond‑rotation (rotate rotatable single bonds).  
    2. Atom masking (replace a random non‑ester atom’s feature vector with zeros).  
  - Ensure the total number of augmented graphs equals `2 * original_count`.  
  - Write augmented graphs to `data/augmented/graphs/` and a manifest `data/augmented/augmentation_manifest.json` with `{"original": N, "augmented": 2*N, "factor": 2}`.  
  - Record the wall‑clock time in `state/augmentation_timing.log`; verify it is ≤ 1800 seconds (30 min).  

  *Verification*: `state/augmentation_check.log` must confirm the factor equals 2; the manifest must exist and match the counts; `state/augmentation_timing.log` must contain a value ≤ 1800.  

- [ ] **T012** Compute checksums for the augmented dataset  

  Re‑run `code/checksums.py` targeting `data/augmented/graphs/` and append results to `state/artifact_hashes.yaml`.  

  *Verification*: New entries for the augmented files appear in `state/artifact_hashes.yaml`.  

- [ ] **T013** [US2] Define and train the lightweight GNN  

  **Files**: `code/model.py`, `code/train.py`  

  - `model.py` defines a ≤3‑layer GCN (or GraphSAGE) with hidden dimension ≤128, ReLU activations, mean‑pool readout, and a softmax over three classes.  
  - `train.py` loads the **augmented** graphs **but filters** to only records where `label_source == "curated"` (synthetic records are excluded from training).  
  - Use the validation strategy from `state/validation_strategy.json` (5‑fold CV or leave‑one‑out).  
  - Early‑stop when `|Δloss|/loss_{t‑5} < 0.05`.  
  - After training, compute mean macro‑F1 on the CV folds and on the external validation set (`data/external/validation.parquet`).  
  - Save the best checkpoint to `data/reports/model_best.pth` and metrics to `data/reports/training_metrics.json`.  

  *Verification*: `data/reports/training_metrics.json` must contain keys `macro_f1_cv`, `macro_f1_external`, and `converged: true`.  

- [ ] **T014** [US2] Compute Integrated Gradients for all test samples  

  **File**: `code/attribution.py`  

  - Load the trained model checkpoint and the external validation set.  
  - For each sample, compute node‑level Integrated Gradients (IG) and aggregate to motif‑level scores.  
  - Save per‑sample IG maps to `data/reports/ig_maps/` (one JSON per record) and a summary `data/reports/ig_summary.json` containing the proportion of hydrolysis cases where the ester bond appears in the top‑5 IG scores.  

  *Verification*: `data/reports/ig_summary.json` must contain a field `ester_top5_fraction` ≥ 0.90 for the hydrolysis subset.  

- [ ] **T015** [US3] Perform primary χ² significance test on motif importance and permutation test  

  **File**: `code/statistical_validation.py`  

  - Build a contingency table of predicted vs. observed degradation pathways on the external validation set.  
  - Run `scipy.stats.chi2_contingency` (α = 0.05) and record χ² statistic and p‑value in `data/reports/chi2_results.json`. **This satisfies FR‑006 and SC‑002 by using the required χ² test.**  
  - Run a permutation test (≥ 1 000 permutations) on the motif‑importance scores and store empirical p‑values in `data/reports/permutation_results.json`.  

  *Verification*: Both JSON files must exist; `chi2_results.json` must contain `"p_value"` < 0.05.  

- [ ] **T016** [US3] Generate NetworkX visualization of top 5 degradation pathways  

  **File**: `code/visualization.py`  

  - Build a NetworkX graph of the top 5 degradation pathways with associated motifs and save as PNG `data/reports/visualizations/top5_pathways.png`.  

  *Verification*: The PNG file must exist.  

- [ ] **T017** [US3] Perform ablation study without synthetic labels  

  **File**: `code/ablation.py`  

  - Retrain the GNN using only records where `label_source == "curated"` (no synthetic records at all).  
  - Evaluate on the external validation set and record macro‑F1 in `data/reports/ablation_metrics.json`.  
  - Compare with the full‑training macro‑F1 and write the difference to `data/reports/ablation_comparison.json`.  

  *Verification*: Both JSON files must exist and contain numeric scores.  

- [ ] **T018** [US3] Generate the final scientific report  

  **File**: `code/report.py`  

  - Collate macro‑F1 scores, χ² results, permutation p‑values, top 3‑5 motifs (with importance scores and significance flags), low‑confidence prediction flags, data‑ingestion success rate (from `state/ingestion_success_rate.txt`), augmentation factor, augmentation runtime, and any power‑analysis warnings.  
  - Produce `docs/reports/final_report.md` following the specification layout.  
  - Also export a machine‑readable JSON summary `data/reports/final_summary.json` matching the `output.schema.yaml`.  

  *Verification*: The markdown file must contain sections “Model Performance”, “Statistical Validation”, “Motif Ranking”, and “Limitations”. The JSON file must validate against `output.schema.yaml`.  

- [ ] **T019** Validate all contracts against generated artifacts  

  **File**: `code/contract_validation.py`  

  - Run `jsonschema` validation for every artifact listed in `contracts/` (dataset, molecular_graph, motif_importance, model_output, output).  
  - Write a consolidated log to `state/contract_validation.log`.  

  *Verification*: The log must end with the line `ALL CONTRACTS VALID`.  

- [ ] **T020** End‑to‑end smoke test on CI runner  

  **File**: `code/smoke_test.py`  

  - Execute the full pipeline in order: `ingest → label_validation → ingestion_success → preprocess → power_analysis → augment → train → attribution → statistical_validation → visualization → ablation → report`.  
  - Record total wall‑clock time and peak RAM (using `psutil`) to `state/smoke_test.log`.  
  - Ensure runtime ≤ 5.5 h and peak RAM ≤ 6.5 GB.  

  *Verification*: `state/smoke_test.log` must contain `runtime_seconds: < 19800` and `peak_ram_gb: < 6.5`.  

---  

**Notes**

* All file paths are relative to the repository root.  
* Tasks marked **[P]** can be executed in parallel where there are no file‑level dependencies.  
* Each task’s verification step is designed to be automatable by the platform’s verifier.  
* The pipeline respects the CPU‑only constraint; no GPU‑specific code is introduced.  
* Synthetic labels are generated **only** for augmentation (FR‑001) and never used for training, satisfying FR‑008 and the methodological corrections.  

---  

*End of `tasks.md`.*  