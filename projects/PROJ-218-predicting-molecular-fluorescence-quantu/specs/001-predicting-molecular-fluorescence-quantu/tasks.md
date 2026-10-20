# Tasks: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The goal is a fully reproducible end-to-end study satisfying FR-001 … FR-018 and SC-001 … SC-005. Tasks follow the three research phases and respect data flow: every producer task precedes its consumers. Key corrections from prior reviews are integrated: **no min-max scaling** (FQY is already a dimensionless ratio in [0, 1]; only ε-clipping is applied — FR-010), the dataset is the **verified joint FluorDB v1.0** source (no separate SMILES/FQY join — FR-018), and previously rejected download/preprocessing work (old T001–T003) is redone within T001–T003 above. The plan maintains the 80/10/10 split mandated by FR-013 and Constitution Principle VI without auto-rebalance; tasks strictly enforce this split as specified.

---

## Phase 1: Data acquisition and first end-to-end preprocessing

- [ ] T001 [US1] Fetch the verified joint dataset **FluorDB v1.0** from `https://huggingface.co/datasets/fluordb/v1` using `datasets.load_dataset`. Verify SHA‑256 checksums of every downloaded file against `data/raw/checksums.txt`; on mismatch or failed fetch, **raise and fail loudly**. Store raw files under `data/raw/`. Abort with a clear error if the dataset contains fewer than **500** valid molecules with both SMILES and experimental FQY (aligns with spec assumption). Pin and record all random seeds in `code/config/seeds.yaml` and write them to `data/results/seeds.json`.  
  *Verification*: download script exits 0; `data/raw/` contains the real dataset files; checksum log matches; `seeds.json` exists with fixed seeds; molecule count ≥ 500 is logged.

- [ ] T002 [US1] **Orchestrator** that runs the newly added preprocessing subtasks (T014‑T016) in sequence and validates their outputs against the data contract schema at `specs/001-predicting-molecular-fluorescence-quantu/contracts/processed_dataset.schema.yaml`.  
  *Verification*: Calls each subtask; exits 0 only if all subtasks succeed and schema validation passes.

- [ ] T014 [US1] Parse each SMILES with RDKit; **exclude** invalid SMILES, logging the SMILES and reason to `data/processed/invalid_smiles.log` without crashing. Output a temporary CSV `data/processed/parsed.csv`.  
  *Verification*: script exits 0; `invalid_smiles.log` lists all exclusions; `parsed.csv` contains only valid SMILES.

- [ ] T015 [US1] Apply **ε‑clipping** to the raw experimental FQY values (clip exact 0/1 to `[1e-6, 1‑1e-6]`), log each clipped occurrence to `data/processed/epsilon_clipping.log`. Add a column `fqy_norm`. No other scaling is performed. Output `data/processed/clipped.csv`.  
  *Verification*: clipping log exists; `fqy_norm` equals `fqy_raw` except at clipped boundaries.

- [ ] T016 [US1] Capture optional metadata (solvent, temperature, measurement method), compute Murcko scaffold IDs, and merge the outputs of T014 and T015 into the final processed table `data/processed/processed.csv` conforming to `specs/001-predicting-molecular-fluorescence-quantu/contracts/processed_dataset.schema.yaml`. Validate against the schema.  
  *Verification*: `processed.csv` passes schema validation; scaffold IDs present; metadata columns included when available.

- [ ] T003 [US1] Perform the scaffold‑based 80/10/10 split on `processed.csv` using the pinned seeds, guaranteeing **zero scaffold overlap** between train and test (FR‑002, SC‑004). Log absolute molecule counts per split and scaffold‑overlap statistics (FR‑014). If the test set contains fewer than 20 molecules, log a limited‑statistical‑power warning **without altering** the split ratios (FR‑013). Save `data/splits/train.csv`, `validation.csv`, `test.csv` and validate them against the data contract.  
  *Verification*: overlap report shows `train‑test scaffold overlap: 0`; counts logged; contract validation passes.

- [ ] T020 [US1] Initialise resource limits **before any heavy compute**: set `torch.set_num_threads(2)`, install a memory guard aborting > 7 GB RAM, and start a 6‑hour wall‑clock watchdog. Export a module `code/utils/resource_limits.py` that is imported by all subsequent compute tasks (including T004).  
  *Verification*: module logs the enforced limits; downstream tasks import it without error.

- [ ] T019 [US1] Create a pinned `requirements.txt` (or `pyproject.toml`) under `code/` listing exact versions of all dependencies (torch, torch_geometric, rdkit, pandas, scikit‑learn, shap, matplotlib, numpy, tqdm, etc.). Verify that the file is non‑empty and matches the environment used in CI.  
  *Verification*: `requirements.txt` exists; a CI step checks that `pip install -r requirements.txt` reproduces the environment.

## Phase 2: Features, models, training, and evaluation

- [ ] T004 [US1] Implement graph feature extraction: for every molecule, generate node features (atom type, hybridization, formal charge) and edge features (bond type, conjugation status) via RDKit, serialising as PyTorch Geometric `Data` objects. Also compute ECFP4 fingerprints (radius 2, 2048 bits) for the baseline, saving `data/features/ecfp4_{train,val,test}.npy`. Import `code/utils/resource_limits.py` to respect limits.  
  *Verification*: unit tests confirm required node/edge features on sample molecules; `.npy` shapes match split sizes.

- [ ] T005 [US2] Implement the message‑passing GNN (< 5 M parameters, CPU‑only) in `code/models/gnn.py` with config in `code/config/gnn_config.yaml` (FR‑003). Also implement the linear‑regression baseline on ECFP4 fingerprints. Ensure the resource‑limits module is imported.  
  *Verification*: parameter count ≤ 5 M; `torch.get_num_threads()` ≤ 2; resource‑limits logs present.

- [ ] T006 [US2] Train the GNN on the training split for ≤ 50 epochs with early stopping (patience = 10) on validation loss, Adam optimiser, MSE loss, seeded reproducibly, saving the checkpoint from the epoch with the **lowest** validation loss to `models/gnn_best.pt` and the per‑epoch log to `data/results/gnn_training_log.csv`. Fit the linear‑regression baseline on ECFP4 training fingerprints, saving to `models/baseline_lr.pkl`.  
  *Verification*: training exits 0; log contains `epoch`, `train_loss`, `val_loss`; checkpoint corresponds to minimum validation loss; same seeds reproduce identical trajectories.

- [ ] T007 [US2] Evaluate both models on the scaffold‑disjoint test set: compute overall R², RMSE, MAE, and condition‑stratified metrics (solvent/temperature/method) (FR‑005, FR‑017). For molecules with unseen atom/bond types during test-set evaluation, **retain them in the evaluation**, logging a transparency summary to `data/results/unseen_types_report.txt` that details how many test molecules had unseen types and their impact on metrics (FR‑012 test-set branch). Write `data/results/metrics.json`. Record wall‑clock time and peak RAM to `data/results/resource_usage.json`.  
  *Verification*: `metrics.json` contains overall and per‑condition metrics; GNN vs baseline comparison (SC‑001) is computed and reported honestly; `resource_usage.json` within limits; `unseen_types_report.txt` exists with transparency summary of test-set unseen types.

- [ ] T021 [US2] Save per‑molecule test predictions (`data/results/test_predictions.csv`) containing SMILES, true `fqy_norm`, and predicted values for both GNN and baseline. This file will be used for parity‑plot verification.  
  *Verification*: CSV exists with correct columns; number of rows matches test set size.

## Phase 3: Interpretability, validation, and handoff

- [ ] T008 [US3] Create the curated fluorophore‑motif reference set from peer‑reviewed literature independent of the training data: each entry (SMARTS, name, citation/DOI) stored in `data/reference/fluorophore_motifs.csv`, with provenance documented in `docs/reference_set_readme.md` (FR‑016). Do **not** prune motifs that appear in training or test; optionally flag training‑only motifs.  
  *Verification*: CSV has columns `smarts`, `name`, `citation`; README lists sources; independence check reports overlap statistics.

- [ ] T009 [US3] Apply **Integrated Gradients** to the trained GNN for every test molecule, aggregate atom‑level attributions into contiguous aromatic or conjugated fragments (detected via RDKit), and rank the **top 20** substructures by summed absolute attribution (FR‑006). Save `data/results/attributions/top20_substructures.json`. Additionally, compute a **SHAP** sanity check on a random subset of 10 test molecules using `shap.DeepExplainer` on flattened node embeddings; log the Pearson correlation between IG and SHAP scores to `data/results/attrib_sanity_check.txt` (optional, no pass/fail gate).  
  *Verification*: JSON contains exactly 20 entries with SMARTS and scores; sanity‑check file records a correlation value (may be any real number).

- [ ] T010 [US3] Validate attributions against the reference set (SC‑005):  
  1. Count matches between the top‑20 substructures and the full reference set (threshold ≥ 12).  
  2. Run a **seeded permutation test** with **100 random draws** of 20 substructures from the full fragment pool; compute the mean random overlap and require the observed overlap to be **≥ 1.5×** this mean (enrichment criterion).  
  3. Perform the spot‑check on **a single highest‑FQY test molecule** (the molecule with the highest experimental FQY value in the test set) and require ≥ 3 of its top‑5 substructures to match the reference set (US‑3 Scenario 3).  
  Write `data/results/attrib_validation.txt` with three lines:  
  `CHECK1 overlap_count: <int> threshold: 12 result: PASS|FAIL`  
  `CHECK2 enrichment_ratio: <float> threshold: 1.5 result: PASS|FAIL`  
  `CHECK3 spotcheck_matches: <int> threshold: 3 result: PASS|FAIL`.  
  Pass/fail rules: CHECK1 PASS if overlap_count ≥ 12; CHECK2 PASS if enrichment_ratio ≥ 1.5; CHECK3 PASS if spotcheck_matches ≥ 3.  
  *Verification*: file exists with exact schema; values reflect real calculations; PASS/FAIL reported honestly.

- [ ] T011 [US3] Generate required figures under `figures/`: `train_curve.png` (training vs. validation loss), `parity_plot.png` (predicted vs. experimental FQY for both models using `data/results/test_predictions.csv`), and `substructure_importance.png` (bar chart of top‑20 substructure attributions).  
  *Verification*: each PNG is non‑empty, loads as a valid image, and matches the underlying data.

- [ ] T012 [US3] Write a concise methods/results account in `paper/methods_results.md` linking to the actual output files (`data/results/metrics.json`, `data/results/attributions/*`, `figures/*`). Describe model comparison, attribution validation outcomes, boundary‑value clipping summary (FR‑011), unseen‑type summary (FR‑012), condition heterogeneity (FR‑017), and any negative findings, framing all structure‑property findings as associational correlations.  
  *Verification*: every numeric claim references a specific artifact; no invented results appear.

- [ ] T013 [US2] Re‑run the documented workflow end‑to‑end from its declared inputs using a single command (`python -m code.run_pipeline`). Record a rerun log `data/results/rerun_log.txt` that lists all authoritative artifact paths and their content hashes, then compare to the hashes from the original run, confirming reproducibility.  
  *Verification*: executing the command on a fresh runner reproduces all listed artifacts; `rerun_log.txt` contains matching hashes.

- [ ] T018 [US1] **Inference‑time handling** (FR‑012 branch a): for any new inference input (outside the curated test set), the system must detect molecules with atom types or bond configurations not present in the training set, log a warning to the inference log, and **skip** the molecule rather than processing it or crashing. Implement this logic in `code/inference/predict.py` and unit‑test it with a synthetic unseen‑type molecule.  
  *Verification*: inference script logs warning and returns no prediction for unseen‑type input; unit test passes; behavior is distinct from test-set evaluation (T007).
