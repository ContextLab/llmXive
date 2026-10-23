# Tasks: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The following checklist implements the complete end‑to‑end study required by FR‑001 … FR‑018 and SC‑001 … SC‑005.  Tasks are ordered to respect data flow; every producer precedes its consumers.  All verification steps are described in the indented continuation lines.

---

## Phase 1 – Data acquisition, preprocessing, and split

- [ ] T001 [US1] **Download verified FluorDB v1.0**  
  *Script*: `code/data/download_fluordb.py` → stores files under `data/raw/`.  
  *Actions*:  
  • Use `datasets.load_dataset("fluordb/v1")` to fetch the joint SMILES + FQY dataset.  
  • Verify SHA‑256 checksums listed in `data/raw/checksums.txt`; abort loudly on mismatch.  
  • Fail with an explicit error if fewer than **500** valid molecules are present.  
  • Write the global random‑seed configuration to `code/config/seeds.yaml` and export it before any shuffling.  
  *Verification*: script exits 0, `data/raw/` contains the parquet/JSON files, checksum log matches, `seeds.yaml` exists, and the molecule count is logged ≥ 500.

- [ ] T002 [US1] **Preprocess raw data** – parse, clean, clip, add metadata, compute scaffolds, and validate schema.  
  *Script*: `code/preprocessing/preprocess.py` → output `data/processed/processed.csv`.  
  *Steps performed internally*:  
  1. Parse each SMILES with RDKit; exclude invalid entries, logging to `data/processed/invalid_smiles.log`.  
  2. Apply ε‑clipping `[1e‑6, 1‑1e‑6]` to exact 0/1 FQY values; log each clipping event to `data/processed/epsilon_clipping.log`.  
  3. Capture optional metadata (solvent, temperature, measurement method) and store in a `metadata` column.  
  4. Compute Murcko scaffold identifiers for every molecule.  
  5. Merge all columns into a single table that conforms to `specs/001-predicting-molecular-fluorescence-quantu/contracts/processed_dataset.schema.yaml`.  
  *Verification*: `processed.csv` passes JSON‑schema validation, `invalid_smiles.log` and `epsilon_clipping.log` are non‑empty if applicable, and the file contains the required columns (`smiles`, `fqy_raw`, `fqy_norm`, `scaffold_id`, `split`, `metadata`).

- [ ] T003 [US1] **Scaffold‑based 80/10/10 split** (zero scaffold overlap).  
  *Script*: `code/preprocessing/scaffold_split.py` → outputs `data/splits/train.csv`, `validation.csv`, `test.csv`.  
  *Actions*:  
  • Use the deterministic seeds from `seeds.yaml`.  
  • Allocate 80 % of molecules to training, 10 % each to validation and test based on scaffold IDs.  
  • Verify that `train` and `test` share **no** scaffold identifiers (SC‑004).  
  • Log absolute counts per split and scaffold‑overlap statistics to `data/splits/split_report.txt`.  
  • If the test set contains fewer than 20 molecules, emit a warning in the report but **do not** alter the split ratios (FR‑013).  
  *Verification*: split files exist, `split_report.txt` shows zero overlap, molecule counts are logged, and a warning line appears only when test < 20.

- [ ] T004 [US1] **Resource‑limits module**  
  *File*: `code/utils/resource_limits.py`.  
  *Features*:  
  • `torch.set_num_threads(2)` to cap CPU parallelism.  
  • A memory‑guard that raises a `RuntimeError` if RAM usage exceeds 7 GB.  
  • A watchdog that terminates the process after 6 hours.  
  • Exported constant `RESOURCE_LIMITS_ENABLED = True`.  
  *Verification*: module imports without error; a quick sanity run prints the configured limits.

- [ ] T005 [US1] **Pinned requirements file**  
  *File*: `requirements.txt` (placed in project root).  
  *Contents*: exact version pins for `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `shap==0.45.0`, `matplotlib==3.9.0`, `numpy==2.0.0`, `tqdm==4.66.5`, plus any transitive pins required by `torch_geometric`.  
  *Verification*: CI step `pip install -r requirements.txt` reproduces the environment without version conflicts.

---

## Phase 2 – Feature engineering, model implementation, training, and evaluation

- [ ] T006 [US2] **Feature extraction**  
  *Script*: `code/features/extract.py` → outputs:  
  • Graph objects (`data/features/gnn_{train,val,test}.pt`) containing node features (atom type, hybridization, formal charge) and edge features (bond type, conjugation).  
  • ECFP4 fingerprint arrays (`data/features/ecfp4_{train,val,test}.npy`).  
  *Verification*: unit tests confirm that a sample molecule yields the required node/edge fields; the shapes of the `.pt` and `.npy` files match the split sizes.

- [ ] T007 [US2] **Model definition**  
  *Files*: `code/models/gnn.py` (PyTorch Geometric GNN, ≤ 5 M parameters) and `code/models/baseline_lr.py` (scikit‑learn `LinearRegression`).  
  *Config*: `code/config/gnn_config.yaml` (layer sizes, dropout, etc.) and `code/config/baseline_config.yaml`.  
  *Verification*: a quick import prints the total parameter count (≤ 5 M) and the baseline model can be instantiated.

- [ ] T008 [US2] **Training both models**  
  *Script*: `code/training/train_all.py`.  
  *Actions*:  
  • Train the GNN on the training split for ≤ 50 epochs with early stopping (patience = 10) on validation loss; save the checkpoint with the lowest validation loss to `models/gnn_best.pt`.  
  • Train the linear‑regression baseline on the training ECFP4 fingerprints; save to `models/baseline_lr.pkl`.  
  • Record per‑epoch loss curves to `data/results/training_log.csv`.  
  *Verification*: training finishes within the 6‑hour wall‑clock limit, `gnn_best.pt` and `baseline_lr.pkl` exist, and `training_log.csv` contains columns `epoch`, `train_loss`, `val_loss`.

- [ ] T009 [US2] **Evaluation, metrics, and predictions**  
  *Script*: `code/evaluation/evaluate.py`.  
  *Outputs*:  
  • `data/results/metrics.json` (overall R², RMSE, MAE for GNN and baseline, plus condition‑wise metrics per solvent/temperature/method).  
  • `data/results/unseen_types_report.txt` summarizing any test‑set molecules that contain atom or bond types unseen during training (FR‑012).  
  • `data/results/resource_usage.json` (wall‑clock time and peak RAM).  
  • `data/results/test_predictions.csv` (SMILES, true `fqy_norm`, GNN prediction, baseline prediction).  
  *Verification*: JSON contains the required fields; the condition‑stratified section lists metrics for each solvent/temperature category; the unseen‑type report is non‑empty only when applicable; resource usage stays ≤ 7 GB and ≤ 6 h.

---

## Phase 3 – Interpretability, validation, and handoff

- [ ] T010 [US3] **Curated fluorophore‑motif reference set**  
  *Files*: `data/reference/fluorophore_motifs.csv` (columns `smarts`, `name`, `citation`) and `docs/reference_set_readme.md` documenting provenance (literature sources, DOI list).  
  *Verification*: CSV contains ≥ 30 distinct motifs, README lists at least five peer‑reviewed articles, and a script confirms that none of the motifs were derived from the training molecules.

- [ ] T011 [US3] **Attribution generation & sanity check**  
  *Script*: `code/interpretability/attribute.py`.  
  *Steps*:  
  1. Compute Integrated Gradients for every test molecule; aggregate atom‑level scores into contiguous aromatic or conjugated fragments.  
  2. Rank fragments and output the top 20 (SMARTS + summed absolute attribution) to `data/results/attributions/top20_substructures.json`.  
  3. Run SHAP `DeepExplainer` on a random subset of 10 test molecules; compute Pearson correlation between IG and SHAP scores and write to `data/results/attrib_sanity_check.txt`.  
  *Verification*: JSON has exactly 20 entries; sanity‑check file contains a numeric correlation (any real value).

- [ ] T012 [US3] **Attribution validation against reference set**  
  *Script*: `code/interpretability/validate_attributions.py`.  
  *Checks*:  
  1. **Overlap count** – number of top‑20 fragments that appear in `fluorophore_motifs.csv` (must be ≥ 12).  
  2. **Enrichment** – seeded permutation test (100 random draws of 20 fragments) computing mean random overlap; require observed overlap ≥ 1.5 × mean.  
  3. **Spot‑check** – identify the test molecule with the highest experimental FQY; require ≥ 3 of its top‑5 fragments to match the reference set.  
  *Output*: `data/results/attrib_validation.txt` with three lines reporting `PASS`/`FAIL` as described in the spec.  
  *Verification*: file exists and the three lines follow the exact schema; values reflect real calculations.

- [ ] T013 [US3] **Figures and methods‑results write‑up**  
  *Outputs*:  
  • Figures under `figures/`: `train_curve.png`, `parity_plot.png`, `substructure_importance.png`.  
  • Narrative markdown `paper/methods_results.md` linking to `metrics.json`, `top20_substructures.json`, `attrib_validation.txt`, and the three figures; it explicitly states that SC‑001 (R² ≥ 0.7) is a hypothesis to be tested, not a hard gate.  
  *Verification*: each PNG loads without error; the markdown contains hyperlinks to the exact artifact paths and no invented numbers.

- [ ] T014 [US2] **End‑to‑end reproducibility run**  
  *Command*: `python -m code.run_pipeline`.  
  *Actions*:  
  • Executes tasks T001–T013 from a clean checkout.  
  • Writes `data/results/rerun_log.txt` listing SHA‑256 hashes of all primary output files (`processed.csv`, model checkpoints, metrics.json, top20 JSON, figures, etc.).  
  • Compares these hashes to those from the original run and reports any mismatches (should be none).  
  *Verification*: command completes within the resource limits; `rerun_log.txt` shows matching hashes for every artifact.

- [ ] T015 [US3] **Inference‑time handling for unseen atom/bond types**  
  *File*: `code/inference/predict.py`.  
  *Behavior*: when presented with a new SMILES, the script checks whether any atom or bond type was absent from the training set; if so, it logs a warning to `data/inference/unseen_warning.log` and **skips** the molecule (no crash).  
  *Unit test*: `tests/unit/test_inference_unseen.py` feeds a synthetic molecule containing a novel atom (e.g., a lanthanide) and asserts that the warning is written and the returned prediction list is empty.  
  *Verification*: unit test passes; running the script on a mixed input file produces a warning line for the unseen molecule and predictions for the rest.

--- 

**All tasks are unchecked (`- [ ]`) to indicate they still need execution.**  Once a task is completed and its verification passes, the CI system will automatically check the box.  This checklist satisfies every functional requirement (FR‑001 … FR‑018) and success criterion (SC‑001 … SC‑005) while respecting the platform’s compute limits and the reviewers’ comments.
