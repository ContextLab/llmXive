# Tasks: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Inputs**: `spec.md`, `plan.md`, the current repository state, and the reviewer comments listed above.  
All tasks respect the data‑flow order required by the functional requirements (FR‑001 … FR‑018) and success criteria (SC‑001 … SC‑005).  Verification steps are described in the indented continuation lines.  Boxes are left unchecked because the pipeline has not yet been executed; a CI run will automatically check a box when its verification passes.

---

## Phase 1 – Data acquisition, cleaning, and scaffold‑based split  

- [ ] T001 **US‑1** Implement download script for verified FluorDB v1.0 → `code/data/download_fluordb.py` → `data/raw/fluordb/`   <!-- FAILED-IN-EXECUTION: code/data/download_fluordb.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download_fluordb.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_fluordb.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download_fluordb.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download_fluordb.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_fluordb.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download_fluordb.py exit=1 -->
  *Actions*  
  • Use `datasets.load_dataset("fluordb/v1", split="train", streaming=False)` to fetch the joint SMILES + FQY parquet file.  
  • Write the file `fluordb.parquet` into `data/raw/fluordb/`.  
  • Store the SHA‑256 checksum of the downloaded file in `data/raw/fluordb/checksums.txt`.  
  • Abort with a clear error if the file is missing, the checksum does not match, or fewer than 500 valid rows remain after download.  
  *Verification*  
  – Script exits 0.  
  – `data/raw/fluordb/fluordb.parquet` exists, checksum file is present, and a log `download.log` records “SUCCESS” and the molecule count (≥ 500).

- [ ] T002 **US‑1** Preprocess raw data → `code/preprocessing/clean.py` → `data/processed/processed.csv`  
  *Steps* (performed inside the script)  
  1. Load `data/raw/fluordb/fluordb.parquet`.  
  2. Parse each SMILES with RDKit; **exclude** invalid entries and write their SMILES and the error reason to `data/processed/invalid_smiles.log`.  
  3. Apply ε‑clipping `[1e‑6, 1‑1e‑6]` to any FQY value that is exactly 0 or 1; log each clipping event to `data/processed/epsilon_clipping.log`.  
  4. Preserve optional metadata (solvent, temperature, measurement method) in a `metadata` column.  
  5. Compute Murcko scaffold identifiers for every molecule.  
  6. Assemble a table with columns `smiles`, `fqy_raw`, `fqy_norm`, `scaffold_id`, `metadata` that conforms to `specs/001-predicting-molecular-fluorescence-quantu/contracts/processed_dataset.schema.yaml`.  
  7. **No additional scaling** is performed (FR‑010).  
  8. Write the table to `data/processed/processed.csv`.  
  *Verification*  
  – The CSV passes the JSON‑schema test (`tests/contract/test_processed_schema.py`).  
  – Log files exist (may be empty).  
  – All required columns are present.

- [ ] T003 **US‑1** Scaffold‑based 80/10/10 split → `code/preprocessing/scaffold_split.py` → `data/splits/train.csv`, `validation.csv`, `test.csv`  
  *Actions*  
  • Load `data/processed/processed.csv`.  
  • Use the deterministic seed defined in `code/config/seeds.yaml` (`seed: 20231022`).  
  • Allocate molecules to training (≈ 80 %), validation (≈ 10 %), and test (≈ 10 %) **by scaffold ID**; enforce **zero scaffold overlap** between training and test (SC‑004).  
  • **Enforce a minimum of 50 test molecules**; abort with an error if the test split contains fewer than 50 entries (FR‑013).  
  • Write the three CSV files under `data/splits/`.  
  • Generate `data/splits/split_report.txt` containing:  
    – absolute counts per split,  
    – list of overlapping scaffold IDs (must be empty),  
    – a warning line if the test set contains fewer than 20 molecules (still logged per FR‑013).  
  *Verification*  
  – All three split files exist and contain a `split` column with the correct label.  
  – `split_report.txt` shows “Overlap: 0” and reports an error if test‑size < 50.  

---

## Phase 2 – Feature engineering, model definition, training, and evaluation  

- [ ] T004 **US‑2** Extract graph tensors & ECFP4 fingerprints → `code/features/extract.py` → `data/features/`  
  *Outputs*  
  • `gnn_train.pt`, `gnn_val.pt`, `gnn_test.pt` (PyTorch Geometric `Data` objects with node features: atom type, hybridization, formal charge; edge features: bond type, conjugation).  
  • `ecfp4_train.npy`, `ecfp4_val.npy`, `ecfp4_test.npy` (NumPy arrays of 2048‑bit ECFP4 fingerprints).  
  *Verification*  
  – Unit test confirms that a randomly selected molecule yields the required node/edge fields.  
  – Shapes of the `.pt` and `.npy` files match the number of rows in the corresponding split CSVs.

- [ ] T005 **US‑2** Define GNN (< 5 M parameters) & linear‑regression baseline → `code/models/gnn.py`, `code/models/baseline_lr.py` → `code/config/gnn_config.yaml`, `baseline_config.yaml`  
  *Details*  
  • GNN: 3 GraphConv layers + global mean‑pool readout; total trainable parameters ≤ 5 M (checked at import).  
  • Baseline: `Ridge(alpha=1.0)` fitted on ECFP4 fingerprints only (no covariates).  
  *Verification*  
  – Importing `gnn.py` prints the parameter count (≤ 5 M).  
  – Instantiating the baseline class succeeds without error.

- [ ] T006 **US‑2** Train models → `code/training/train.py` → `models/gnn_best.pt`, `models/baseline_lr.pkl`, `data/results/training_log.csv`  
  *Actions*  
  • Train the GNN on the training split for **≤ 50 epochs** with early stopping (patience = 10) on validation loss; save the checkpoint with lowest validation loss to `models/gnn_best.pt`.  
  • Train the linear‑regression baseline on the training ECFP4 fingerprints; save the model to `models/baseline_lr.pkl`.  
  • Record per‑epoch `epoch`, `train_loss`, `val_loss` in `training_log.csv`.  
  *Verification*  
  – Training completes within the 6‑hour wall‑clock limit.  
  – Checkpoint and baseline files exist.  
  – `training_log.csv` contains the three columns and at least one epoch row.

- [ ] T007 **US‑2** Evaluate on test set → `code/evaluation/evaluate.py` → `data/results/metrics.json`, `test_predictions.csv`, `unseen_types_report.txt`, `resource_usage.json`  
  *Outputs*  
  • `metrics.json` with R², RMSE, MAE for the GNN and the baseline (overall) and a `condition_metrics` sub‑object (solvent/temperature/method breakdown).  
  • `test_predictions.csv` (SMILES, `fqy_norm`, `gnn_pred`, `baseline_pred`).  
  • `unseen_types_report.txt` summarising any test‑set molecules that contain atom or bond types not observed during training (FR‑012).  
  • `resource_usage.json` reporting wall‑clock time and peak RAM (must be ≤ 6 h, ≤ 7 GB).  
  *Verification*  
  – JSON conforms to the `metrics.json` schema test.  
  – Resource usage respects limits.  
  – Unseen‑type report is non‑empty only when applicable.

---

## Phase 3 – Interpretability, attribution validation, and inference robustness  

- [ ] T008 **US‑3** Curate fluorophore‑motif reference set → `data/reference/fluorophore_motifs.csv` & `docs/reference_set_readme.md`  
  *Contents*  
  • CSV columns: `smarts`, `name`, `citation`; ≥ 30 distinct motifs, none derived from the training molecules.  
  • README documents provenance (≥ 5 peer‑reviewed articles with DOIs) and selection criteria.  
  *Verification*  
  – CSV loads without error and contains ≥ 30 rows.  
  – README lists at least five citations.

- [ ] T009 **US‑3** Integrated Gradients attribution → `code/interpretability/attribute_ig.py` → `data/results/top20_substructures.json`  
  *Steps*  
  1. Load `models/gnn_best.pt` and the test split graphs.  
  2. Compute Integrated Gradients for each test molecule.  
  3. Aggregate atom‑level IG scores into chemically meaningful fragments (contiguous aromatic or conjugated substructures detected via RDKit).  
  4. Sum absolute attributions per fragment, rank, and write the top 20 fragments (SMARTS + summed score) to the JSON file.  
  *Verification*  
  – JSON contains exactly 20 entries, each with fields `smarts`, `score`.  
  – A quick script prints the highest‑scoring fragment.

- [ ] T010 **US‑3** SHAP sanity‑check → `code/interpretability/attribute_shap.py` → `data/results/shap_correlation.txt`  
  *Actions*  
  • Run `shap.DeepExplainer` on a random subset of **at least 30** test molecules.  
  • For each molecule compute Pearson correlation between IG and SHAP scores.  
  • Write the **average correlation** (single floating‑point number) to `shap_correlation.txt`.  
  *Verification*  
  – File exists and contains a numeric value; no pass/fail threshold is imposed.

- [ ] T011 **US‑3** Validate attributions against reference set → `code/interpretability/validate_attributions.py` → `data/results/attrib_validation.txt`  
  *Checks*  
  1. **Overlap count** – number of top‑20 fragments that match any `smarts` pattern in `fluorophore_motifs.csv`.  
  2. **Enrichment** – permutation test (100 random draws of 20 fragments) to obtain mean random overlap; require observed overlap ≥ 1.5 × mean.  
  3. **Spot‑check** – for the test molecule with the highest experimental FQY, require at least 3 of its top‑5 fragments to be present in the reference set.  
  *Output* – three lines exactly: `OVERLAP_PASS` / `OVERLAP_FAIL`, `ENRICHMENT_PASS` / `ENRICHMENT_FAIL`, `SPOT_CHECK_PASS` / `SPOT_CHECK_FAIL`.  
  *Verification*  
  – File exists and follows the three‑line schema.

- [ ] T012 **US‑3** Inference‑time handling of unseen atom/bond types → `code/inference/predict.py` & `tests/unit/test_inference_unseen.py` → `data/inference/unseen_warning.log`  
  *Behavior*  
  • Load `models/gnn_best.pt` and the set of atom/bond types observed during training.  
  • For each input SMILES, if a novel atom or bond type is detected, log a warning to `unseen_warning.log` and **skip** that molecule (no crash).  
  • Return predictions for all valid molecules.  
  *Verification*  
  – Unit test feeds a SMILES containing a lanthanide atom, asserts that a warning line is written and that the returned list is empty for that entry.  
  – Running the script on a mixed input file produces the expected warning.

---

## Phase 4 – Visualization, reporting, and reproducible hand‑off  

- [ ] T013 **US‑3** Generate figures → `code/visualization/plot_results.py` → `figures/train_curve.png`, `parity_plot.png`, `substructure_importance.png`, `figures/figures_sha256.txt`  
  *Produces*  
  • Training‑loss vs. epoch curve (both train and validation).  
  • Parity plot (predicted vs. experimental FQY) with R² annotation.  
  • Bar chart of the top‑20 substructure importance scores.  
  • SHA‑256 checksum file recording hashes of the three PNGs.  
  *Verification*  
  – Each PNG opens without error.  
  – Checksum file exists and contains three lines of the form `<sha256>  <filename>`.

- [ ] T014 **US‑3** End‑to‑end reproducibility run → `code/run_pipeline.py` (`python -m code.run_pipeline`) → `data/results/rerun_log.txt`  
  *Behavior*  
  • Executes tasks T001–T013 sequentially from a clean checkout.  
  • After completion, computes SHA‑256 hashes of all major output artifacts (`processed.csv`, split CSVs, feature tensors, model checkpoints, `metrics.json`, attribution files, figures) and writes them to `rerun_log.txt`.  
  • Compares these hashes to the originals (if present) and reports “ALL MATCH” when they agree.  
  *Verification*  
  – Command finishes within the resource limits.  
  – `rerun_log.txt` lists a hash line for every artifact and ends with the line `ALL MATCH` when reproducibility is confirmed.

---

## Dependency & Requirement Coverage

| Specification | Covered by task(s) |
|---------------|-------------------|
| FR‑001 – RDKit graph parsing | T002 |
| FR‑002 – Scaffold‑based split (80/10/10, zero overlap) | T003 |
| FR‑003 – < 5 M‑param GNN (CPU) | T005 |
| FR‑004 – ≤ 50 epochs, early stopping | T006 |
| FR‑005 – Baseline regression & metric reporting | T006, T007 |
| FR‑006 – Integrated Gradients & substructure aggregation | T009 |
| FR‑007 – Visualizations (training curve, parity plot, importance chart) | T013 |
| FR‑008 – Resource limits (≤ 7 GB RAM, ≤ 6 h) | T007 (resource_usage.json), T014 (watchdog) |
| FR‑009 – Invalid SMILES exclusion & logging | T002 |
| FR‑010 – ε‑clipping only (no min‑max scaling) | T002 |
| FR‑011 – Log clipped boundary values | T002 |
| FR‑012 – Unseen atom/bond handling (log & skip) | T007 (report), T012 (inference) |
| FR‑013 – Test‑set size warning | T003 |
| FR‑014 – Log split counts & scaffold overlap | T003 |
| FR‑015 – Preserve solvent/temperature/method metadata | T002, T007 |
| FR‑016 – Curated fluorophore‑motif reference set | T008 |
| FR‑018 – Verified FluorDB download & checksum | T001 |
| SC‑001 – Report GNN vs. baseline R², RMSE, MAE (no hard pass/fail) | T007 |
| SC‑002 – Measure total wall‑clock time | T007 (resource_usage.json) |
| SC‑003 – Measure peak RAM usage | T007 (resource_usage.json) |
| SC‑004 – Verify zero scaffold overlap | T003 |
| SC‑005 – Attribution overlap, enrichment, spot‑check | T011 |
| SC‑006 – IG vs. SHAP correlation (≥ 30 molecules, report only) | T010 |

All scientific requirements from the specification are represented, and the pipeline can be executed end‑to‑end starting from T001.  