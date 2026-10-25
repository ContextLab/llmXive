# Tasks: Predicting Polymer Degradation Pathways with Graph Neural Networks  

**Inputs**: `spec.md`, `plan.md`, original research idea, all contracts in `specs/001-polymer-degradation/`.  

The tasks respect data flow, provide an early end‑to‑end runnable result, and cover every mandatory functional and success‑criteria requirement. Parallel‑eligible tasks are marked **[P]**; story labels (**[US1]**, **[US2]**, **[US3]**) indicate which user story the task satisfies.

---  

- [ ] **T001** [P] Create project directory tree and record its structure  

  **File(s)**: *none (shell command)*  

  ```bash
  mkdir -p code/ data/raw/ data/processed/ data/augmented/ data/external/ \
           data/reports/ data/output/ tests/ state/ state/projects/
  # Record directory tree for reproducibility
  tree -a . > state/dir_structure.txt
  ```  

  *Verification*:  
  - Run `test -d code && test -d data/raw && test -d data/processed && test -d data/augmented && test -d data/external && test -d data/reports && test -d data/output && test -d tests && test -d state && test -d state/projects && test -f state/dir_structure.txt`.  
  - The file `state/dir_structure.txt` must contain a non‑empty listing of the top‑level directories.

- [ ] **T002** Create a timestamped recursive directory listing  

  **File**: `state/setup_log.txt`  

  ```bash
  echo "Setup run at $(date --iso-8601=seconds)" > state/setup_log.txt
  ls -R . >> state/setup_log.txt
  ```  

  *Verification*:  
  - `state/setup_log.txt` exists.  
  - First line matches regex `^Setup run at \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*$`.  
  - The file contains at least one line beginning with `./`.

- [ ] **T003** Configure strict linting and capture a successful run  

  **File**: `code/.ruff.toml` (strict rules are already present)  

  *Run*: `ruff check code/ --exit-zero > state/ruff_check.log 2>&1 && echo $? > state/ruff_exit_code.txt`.  

  *Verification*:  
  - `state/ruff_check.log` exists and contains the exact phrase `No issues found`.  
  - `state/ruff_exit_code.txt` exists and its content is `0`.  

- [ ] **T004** Add deterministic testing configuration  

  **Files**: `pytest.ini`, `tests/conftest.py`  

  `pytest.ini`  

  ```
  [pytest]
  addopts = --random-order-seed=42 -vv
  ```  

  `tests/conftest.py`  

  ```python
  import random, os
  import numpy as np
  import torch
  from code.seed import set_seed

  set_seed(42)

  def pytest_configure(config):
      os.environ["PYTHONHASHSEED"] = "42"
  ```  

  *Run*: `pytest --collect-only > state/pytest_collect.log 2>&1`.  

  *Verification*:  
  - `state/pytest_collect.log` exists and contains the word `collected`.  
  - The environment variable `PYTHONHASHSEED` is set to `42` during the run (checked via the log).  

- [ ] **T005** [US1] Implement real‑data ingestion with exponential backoff  

  **File**: `code/ingest.py`  

  - Stream the **Polymer Genome** dataset from HuggingFace (`https://huggingface.co/datasets/PolymerGenome/polymer_degradation/resolve/main/data.parquet`) using `datasets.load_dataset(..., streaming=True)`.  
  - Query the **Materials Project** API (`https://materialsproject.org/rest/v2/materials`) with a helper that retries on HTTP 429 up to 3 times using exponential backoff (`utils.exponential_backoff`).  
  - De‑duplicate records on canonical SMILES, keep only entries that contain a polymer structure, and write the merged table to `data/raw/combined.parquet`.  
  - Log every API request, retry count, and any error to `state/ingest_error.log`; also write a short summary (rows downloaded, rows after de‑duplication) to `state/ingest.log`.  

  *Verification*:  
  - After `python -m code.ingest` finishes, `data/raw/combined.parquet` exists, contains ≥ 100 rows, and `state/ingest_error.log` only contains entries for retries (no fatal errors).  

- [ ] **T007** [US1] Validate / synthesize missing degradation labels  

  **File**: `code/label_validation.py`  

  - Scan `data/raw/combined.parquet` for rows where `label` is missing.  
  - Apply rule‑based synthetic labeling **only** when a SMARTS rule matches:  
    * Ester pattern `C(=O)O` → `hydrolysis`  
    * Aromatic pattern `a` → `photolysis`  
    * Nitro pattern `[N+](=O)[O-]` → `oxidation`  
  - After labeling, compute class frequencies and assert each is within ±10 % of the literature proportions reported in Bergman 2022; abort with error if tolerance is violated.  
  - Add a new column `label_source` set to `"curated"` or `"synthetic"` accordingly.  
  - If **all** records lack a curated label after this step, abort with a clear error and write to `state/label_validation_error.log`.  
  - Write the enriched table to `data/raw/labeled.parquet` and a brief summary (curated vs synthetic counts, frequency check result) to `state/label_validation.log`.  

  *Verification*:  
  - `state/label_validation.log` lists both counts, reports `FREQUENCY_TOLERANCE_OK`, and contains no line starting with `FATAL`.  

- [ ] **T006** [US1] Compute ingestion success‑rate metric (after label validation)  

  **File**: `code/ingestion_success.py`  

  - Load `data/raw/labeled.parquet`.  
  - Count records that have a parsable SMILES (RDKit can convert), non‑missing temperature, pH, UV fields, and a non‑null `label`.  
  - Write the percentage `(valid / total * 100)` as a plain number with two decimal places to `state/ingestion_success_rate.txt`.  

  *Verification*:  
  - The file exists and contains a numeric value ≥ 95.00.

- [ ] **T008** [US1] Create external validation set (≥ 30 curated records)  

  **File**: `code/create_external_validation.py`  

  - Load `data/raw/labeled.parquet` and filter for `label_source == "curated"`.  
  - Remove any record whose SMILES appears in the training pool (i.e., any record in `data/raw/labeled.parquet`).  
  - The curated external records are expected to be supplied in `data/external/literature_curated.parquet`; if that file is missing or yields fewer than 30 records, abort and write the reason to `state/external_validation_error.log`.  
  - Write the final set to `data/external/validation.parquet`.  

  *Verification*:  
  - `data/external/validation.parquet` exists and contains ≥ 30 rows (checked via a one‑liner Python command).

- [ ] **T009** [US1] Preprocess records into RDKit molecular graphs  

  **File**: `code/preprocess.py`  

  - Load `data/raw/labeled.parquet`.  
  - For each record:  
    1. Parse the SMILES with RDKit; on failure, skip and log the SMILES to `state/invalid_smiles.log`.  
    2. Detect the ester functional group via SMARTS `C(=O)O`; keep only records where `is_polyester == True`.  
    3. Impute missing environmental values (`temp_c = 25`, `ph = 7`, `uv_exposure = 0`) and set `validation_flag` to `"missing_env"` when imputation occurs; otherwise `"valid"`.  
    4. Build a `MolecularGraph` object conforming to `molecular_graph.schema.yaml` and serialize each to `data/processed/graphs/graph_{record_id}.pkl`.  
  - Write the cleaned `PolymerRecord`s to `data/processed/records.parquet`.  
  - Write a short processing summary (total, skipped, flagged) to `state/preprocess.log`.  

  *Verification*:  
  - `state/preprocess.log` reports that ≥ 95 % of input rows were kept.  
  - Both `data/processed/records.parquet` and the `graph_*.pkl` files exist.

- [ ] **T011** Perform power‑analysis and decide validation strategy  

  **File**: `code/power_analysis.py`  

  - Load `data/processed/records.parquet` and count `n`.  
  - Compute statistical power for detecting a macro‑F1 of 0.70 with α = 0.05 using `statsmodels.stats.power.NormalIndPower`.  
  - Write a JSON `state/power_analysis.json` containing `{ "n": n, "power": power, "strategy": "5fold" or "loo" }`.  
  - If `power < 0.8`, abort with error and write a warning to `state/power_analysis_warning.json`.  
  - Write the chosen validation strategy to `state/validation_strategy.json`.  

  *Verification*:  
  - `state/power_analysis.json` includes a `power` field ≥ 0.8.  
  - If `n < 150`, `state/power_analysis_warning.json` exists and contains the correct fields.

- [ ] **T012** [US2] Data augmentation (bond rotation + atom masking) to exactly 2× size  

  **File**: `code/augment.py`  

  - Load graphs from `data/processed/graphs/`.  
  - Apply **two deterministic augmentations** **only to records whose `label_source == "synthetic"`**:  
    1. Rotate a randomly chosen rotatable single bond (max 180°) – randomness seeded with `numpy.random.seed(42)`.  
    2. Atom masking – replace the feature vector of a randomly chosen non‑ester atom with zeros (same seed).  
  - Ensure the total number of augmented graphs equals `2 * original_count`; assert this condition and abort on mismatch, logging to `state/augmentation_error.log`.  
  - Write the augmented graphs to `data/augmented/graphs/graph_{record_id}_aug{idx}.pkl`.  
  - Write a manifest `data/augmented/augmentation_manifest.json` containing `{ "original": N, "augmented": 2*N, "factor": 2 }`.  
  - Record wall‑clock time in `state/augmentation_timing.log` and assert it is ≤ 1800 seconds.  

  *Verification*:  
  - `state/augmentation_timing.log` contains a numeric seconds value ≤ 1800.  
  - `state/augmentation_check.log` confirms the factor equals 2.  
  - The manifest matches the counts.

- [ ] **T010** Compute SHA‑256 checksums for all major artifacts (after augmentation)  

  **File**: `code/checksums.py`  

  - Compute SHA‑256 for `data/raw/combined.parquet`, `data/raw/labeled.parquet`, `data/processed/records.parquet`, every file under `data/processed/graphs/`, and every file under `data/augmented/graphs/`.  
  - Write a YAML mapping with **relative POSIX paths sorted alphabetically** to `state/artifact_hashes.yaml`.  

  *Verification*:  
  - `state/artifact_hashes.yaml` exists, contains a key for each listed artifact, and each key follows the relative‑path format.

- [ ] **T013** [US2] Define lightweight GNN architecture (≤ 3 layers, hidden ≤ 128)  

  **File**: `code/model.py`  

  - Implement a PyTorch Geometric GCN (or GraphSAGE) with exactly 3 graph convolutional layers, hidden dimension 128, ReLU activations, mean‑pool readout, and a final linear layer producing logits for the three pathways.  
  - Include a `forward` method that accepts a `MolecularGraph` batch and returns class probabilities via `softmax`.  

  *Verification*:  
  - The file exists and can be imported (`python -c "import code.model; print('ok')"`).  
  - A unit test `tests/unit/test_model_architecture.py` checks that the model has 3 layers and hidden dim ≤ 128 (see T013b).

- [ ] **T013b** Unit test for model architecture  

  **File**: `tests/unit/test_model_architecture.py`  

  ```python
  from code.model import GNNModel
  def test_layer_count_and_dim():
      model = GNNModel()
      assert len(model.convs) == 3
      assert model.convs[0].out_channels == 128
  ```  

  *Verification*: `pytest tests/unit/test_model_architecture.py` passes.

- [ ] **T014** [US2] Train the GNN, evaluate on external validation, and record metrics  

  **File**: `code/train.py`  

  - Load **augmented** graphs from `data/augmented/graphs/` **but filter to only records where `label_source == "curated"`** for the training set.  
  - Use the validation strategy from `state/validation_strategy.json` (5‑fold CV or leave‑one‑out).  
  - Early‑stop when `|Δloss| / loss_{t‑5} < 0.05`.  
  - After training, compute mean macro‑F1 across CV folds and macro‑F1 on the external validation set (`data/external/validation.parquet`).  
  - Assert both macro‑F1 scores are **≥ 0.70**; abort otherwise.  
  - Save the best checkpoint to `data/reports/model_best.pth` and metrics to `data/reports/training_metrics.json` (keys: `macro_f1_cv`, `macro_f1_external`, `converged`).  

  *Verification*:  
  - `data/reports/training_metrics.json` exists, contains the three keys, `macro_f1_cv` ≥ 0.70, `macro_f1_external` ≥ 0.70, and `converged` is `true`.

- [ ] **T015** Compute Integrated Gradients for external validation set  

  **File**: `code/attribution.py`  

  - Load the checkpoint from `data/reports/model_best.pth` and the external validation records.  
  - For each record, compute node‑level Integrated Gradients (IG) using Captum (CPU‑only).  
  - Aggregate IG scores to motif‑level (by matching subgraph patterns).  
  - Write per‑record IG maps as JSON files to `data/reports/ig_maps/` and a summary `data/reports/ig_summary.json` containing at least the field `ester_top5_fraction`, defined as the proportion of hydrolysis records where the ester bond appears among the top‑5 IG scores.  
  - Assert `ester_top5_fraction` ≥ 0.90.  

  *Verification*: `data/reports/ig_summary.json` exists and `ester_top5_fraction` ≥ 0.90.

- [ ] **T016** Perform χ² significance test on external predictions  

  **File**: `code/chi2_test.py`  

  - Build a contingency table of predicted vs. observed degradation pathways on the external validation set.  
  - Run `scipy.stats.chi2_contingency` with α = 0.05 and write the statistic and p‑value to `data/reports/chi2_results.json`.  

  *Verification*: `data/reports/chi2_results.json` exists and the stored `"p_value"` < 0.05.

- [ ] **T017** Run permutation test for motif importance  

  **File**: `code/permutation_test.py`  

  - Shuffle IG‑derived motif importance scores ≥ 1 000 times, compute empirical p‑values for each motif, and write results to `data/reports/permutation_results.json` conforming to `motif_importance.schema.yaml`.  

  *Verification*: The JSON file exists, contains at least one motif entry with `"p_value"` ≤ 0.05, and validates against the schema.

- [ ] **T018** Generate NetworkX visualization of the top 5 degradation pathways  

  **File**: `code/visualization.py`  

  - Using the motif importance results, construct a NetworkX graph linking the five most frequent pathways to their top motifs.  
  - Save the figure as PNG `data/reports/visualizations/top5_pathways.png` with dimensions 800 × 600 pixels.  

  *Verification*: The PNG file exists, is non‑empty, and its dimensions are exactly 800 × 600 (checked via `Pillow`).

- [ ] **T019** Ablation study (training without any synthetic labels)  

  **File**: `code/ablation.py`  

  - Retrain the GNN using **only** records where `label_source == "curated"` (no synthetic records, no augmentation).  
  - Evaluate on the external validation set and write macro‑F1 to `data/reports/ablation_metrics.json`.  
  - Compare to the full‑training macro‑F1 (from `training_metrics.json`) and write the difference (rounded to two decimals) to `data/reports/ablation_comparison.json`.  

  *Verification*: Both JSON files exist, contain numeric scores, and the difference field is present with two‑decimal precision.

- [ ] **T020** Assemble the final scientific report  

  **Files**: `code/report.py`, `docs/reports/final_report.md`, `data/reports/final_summary.json`  

  - Collate: ingestion success rate, power‑analysis warning (if any), CV and external macro‑F1, χ² statistic & p‑value, permutation p‑values, top 3‑5 motifs with importance scores and significance flags, low‑confidence prediction flag statistics, augmentation factor & runtime, ablation results, and any limitation notes.  
  - Ensure the markdown contains the exact section headings:  
    1. `## Model Performance`  
    2. `## Statistical Validation`  
    3. `## Motif Ranking`  
    4. `## Ablation Study`  
    5. `## Limitations`  
  - Verify that at least **three distinct motifs** are listed in the Motif Ranking section and that the low‑confidence flag count (confidence < 0.6) is reported.  
  - Produce a machine‑readable summary JSON `data/reports/final_summary.json` that conforms to `output.schema.yaml`.  

  *Verification*: The markdown file contains all required headings, lists ≥ 3 motifs, includes a low‑confidence count, and `final_summary.json` validates against `output.schema.yaml`.

- [ ] **T021** Validate all JSON‑Schema contracts against generated artifacts  

  **File**: `code/contract_validation.py`  

  - Iterate over every artifact listed in `specs/001-predicting-polymer-degradation-pathways/contracts/` and validate it with `jsonschema`.  
  - Log a consolidated report to `state/contract_validation.log`. The last line of the log must be `ALL CONTRACTS VALID`.  
  - Additionally, ensure that **every** artifact produced by the pipeline appears in at least one contract; missing contracts are reported as warnings.  

  *Verification*: `state/contract_validation.log` exists, ends with `ALL CONTRACTS VALID`, and contains no warnings about unvalidated artifacts.

- [ ] **T022** [US3] Compute low‑confidence prediction flags and summary  

  **File**: `code/low_confidence.py`  

  - Load `data/output/predictions.json` (generated by inference).  
  - For each record, add a boolean field `is_low_confidence` set to `true` if `confidence < 0.6`, otherwise `false`.  
  - Write the enriched predictions to `data/output/predictions_with_flags.json`.  
  - Compute total number and percentage of low‑confidence predictions; write these metrics to `state/low_confidence_summary.txt` (format: `count: X\npercentage: Y.YY`).  
  - *Verification*: `state/low_confidence_summary.txt` exists, contains a numeric percentage between 0 and 100, and `data/output/predictions_with_flags.json` includes the `is_low_confidence` field for every entry.

- [ ] **T023** [US3] Verify that ≥ 3 distinct significant motifs are reported  

  **File**: `code/motif_verification.py`  

  - Load `data/reports/permutation_results.json` (output of the permutation test).  
  - Count unique `motif_id` entries where `significant` is `true`.  
  - Assert the count is at least 3; write the result to `state/motif_count_check.log` (line `MOTIF_COUNT_OK` followed by the numeric count).  
  - *Verification*: `state/motif_count_check.log` exists and contains the line `MOTIF_COUNT_OK` with a count ≥ 3.

- [ ] **T024** End‑to‑end smoke test on the CI runner  

  **File**: `code/smoke_test.py`  

  - Execute the full pipeline in order: `ingest → label_validation → ingestion_success → preprocess → power_analysis → augment → train → attribution → chi2_test → permutation_test → visualization → ablation → report → contract_validation`.  
  - Measure total wall‑clock time and peak RAM using `psutil`; enforce a hard timeout of 5.5 h via `signal.alarm`.  
  - Write JSON results to `state/smoke_test.log` with keys `runtime_seconds` and `peak_ram_gb`.  

  *Verification*: `state/smoke_test.log` exists, `runtime_seconds` < 19800, and `peak_ram_gb` < 6.5.

---  

**Notes**

* All file paths are relative to the repository root.  
* Tasks marked **[P]** can be run in parallel where there are no file‑level dependencies.  
* Verification steps are designed to be automatable by the platform’s verifier.  
* The pipeline respects the CPU‑only constraint; no GPU‑specific code is introduced.  
* Synthetic labels are generated **only for augmentation** and are never used for training, satisfying FR‑008.  

---  

*End of `tasks.md`*.  