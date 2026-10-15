# Tasks: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The goal is to deliver a fully reproducible end‑to‑end study that satisfies every functional requirement (FR‑001 … FR‑017) and success criterion (SC‑001 … SC‑005) in the specification.  
The tasks are grouped into three research phases and ordered to respect data flow: every producer task precedes its consumers, and all resource-limit enforcement and seed pinning occur before any heavy or stochastic computation.

---

## Phase 1 – Data acquisition, curation & preprocessing  

| Goal | Run a small, real‑data pipeline that produces a validated, scaffold‑split dataset ready for modelling. |
|------|--------------------------------------------------------------------------------------------------------|

- [ ] **T001** [US1] Download the raw molecular dataset (SMILES) and the experimental FQY values, verify checksums, and store them under `data/raw/`. **Before any stochastic operation**, pin and record all random seeds: set `PYTHONHASHSEED`, `random.seed`, `numpy.random.seed`, and `torch.manual_seed` to fixed values defined in `code/config/seeds.yaml`, and write the seed values to `results/seeds.json` (Constitution Principle I). <!-- FAILED-IN-EXECUTION: src/data/download_smiles.py exit=1; src/data/download_fqy.py exit=1 -->
  *Verification*: SHA‑256 checksum matches the values recorded in `data/raw/checksums.txt`; the download script exits with status 0; `results/seeds.json` exists and contains the fixed integer seeds; the seed-configuration module is imported (and asserts equality with `results/seeds.json`) before any shuffle or split call in the pipeline.

- [ ] **T002** [US1] Join the SMILES file and the FQY file on InChIKey (generated with RDKit), requiring **≥ 200** matched molecules. Capture solvent, temperature, and measurement‑method metadata (FR‑015) into a `metadata` column. Write the joined table to `data/processed/joined.csv` and log the match count.   <!-- FAILED-IN-EXECUTION: src/preprocessing/join.py exit=1 -->
  *Verification*: `joined.csv` contains a column `inchi_key`; the log entry `matches: X` shows X ≥ 200; the script aborts with an error if the threshold is not met.

- [ ] **T003** [US1] Parse each SMILES in `joined.csv` to an RDKit `Mol`, extract node features (atom type, hybridization, formal charge) and edge features (bond type, conjugation), and discard invalid SMILES while logging the SMILES string and reason. Output a Parquet file `data/processed/graph_features.parquet`.   <!-- FAILED-IN-EXECUTION: src/preprocessing/graph_features.py exit=1 -->
  *Verification*: The Parquet schema contains the required feature columns; `invalid_smiles.log` lists every excluded entry; the script finishes without raising an exception.

- [ ] **T004** [US1] Perform a scaffold‑based split (Murcko scaffolds) with an 80/10/10 ratio, using the seeds pinned in T001 (`code/config/seeds.yaml`) for any scaffold shuffling, guaranteeing **zero scaffold overlap** between train and test. Save three CSVs under `data/splits/` (`train.csv`, `validation.csv`, `test.csv`). Log the counts per split, the overlap statistics, and emit a warning if the test set contains fewer than 20 molecules (FR‑013).  
  *Verification*: `scaffold_overlap.txt` reports `train‑test overlap: 0`; `split_counts.log` shows the 80/10/10 proportions; a warning line appears only when `len(test) < 20`; the split is bit-identical across two runs with the same seed.

- [ ] **T005** [US1] Compute min‑max scaling **only on the training split** for the raw FQY column, apply ε‑clipping (`ε = 1e‑6`) to boundary values 0 and 1, and add a column `fqy_norm`. Propagate the same scaling parameters to validation and test sets. Overwrite the split CSVs with the new column.  
  *Verification*: All `fqy_norm` values lie in `[0, 1]`; the scaling parameters are saved in `data/splits/scaling_params.json`; the log records any clipped values.

- [ ] **T016** [US1] Validate the three split CSVs against the project data contract `contracts/processed_dataset.schema.yaml`: every row must contain `smiles`, `fqy_raw`, `fqy_norm`, `scaffold_id`, `split` (enum train/validation/test) with correct types and ranges, and optional `metadata` fields. Additionally assert that the FR‑014 scaffold-overlap statistics were logged (train–test overlap exactly 0) and that split counts are recorded.  
  *Verification*: A contract-validation script exits with status 0 on all three split files; any schema violation raises an error naming the offending row and field; the validation log confirms `train‑test scaffold overlap: 0` and per-split molecule counts.

---

## Phase 2 – Modelling, training & evaluation  

| Goal | Train a lightweight GNN, a linear‑regression baseline, and produce quantitative performance metrics, all within enforced resource limits. |
|------|----------------------------------------------------------------------------------------------------|

- [ ] **T018** [US2] **Enforce resource limits before any heavy computation** (FR‑008, SC‑002, SC‑003): configure the pipeline to use at most 2 CPU cores (`torch.set_num_threads(2)`, threadpool limits), install a memory guard that aborts with a clear error if peak RSS exceeds 7 GB (e.g., a monitoring thread checking `psutil`), and start a wall-clock watchdog that fails the run if the pipeline exceeds 6 hours. This configuration module is imported by every subsequent compute task (T006–T014).  
  *Verification*: `code/utils/resource_limits.py` exists and is imported by all pipeline entry points; a unit test confirms `torch.get_num_threads() <= 2`; the watchdog and memory guard are active (verified by a log line `resource limits enforced: cpu=2, ram_gb=7, wall_hours=6`) before T006 runs.

- [ ] **T006** [US3] Compute ECFP4 fingerprints (radius = 2, 2048 bits) for every molecule in the three splits and store them as NumPy arrays under `data/features/ecfp4_train.npy`, `ecfp4_val.npy`, `ecfp4_test.npy`.  
  *Verification*: Each `.npy` file loads without error and has shape `(N, 2048)` where N matches the corresponding split size.

- [ ] **T007** [US2] Implement a message‑passing GNN with < 5 M trainable parameters in `code/models/gnn.py` (e.g., three GraphConv layers + readout). Include a configuration file `code/config/gnn_config.yaml`.  
  *Verification*: `torchsummary` run on the model reports ≤ 5 M parameters; the config file contains all hyper‑parameters used downstream.

- [ ] **T008** [US2] Train the GNN on `train.csv` (using the graph features) for **≤ 50 epochs** with early stopping (patience = 10) based on validation MSE. Use Adam optimizer, default precision on CPU, with the seeds pinned in T001. Save the checkpoint with the lowest validation loss to `models/gnn_best.pt` and write a convergence CSV `results/gnn_training_log.csv`.  
  *Verification*: Training script exits with status 0; `gnn_training_log.csv` contains columns `epoch`, `train_loss`, `val_loss`; the best checkpoint is the one referenced in the log; two runs with the same seed produce identical loss trajectories.

- [ ] **T009** [US2] Fit a linear regression model on the ECFP4 fingerprints of the training split, save the fitted model to `models/baseline_lr.pkl`, and record training RMSE in `results/baseline_training_log.csv`. (The baseline is part of the US-2 model-comparison story; it must be produced before evaluation in T010.)  
  *Verification*: Scikit‑learn `LinearRegression` runs without error; the saved pickle loads and predicts; the log file contains a non‑NaN RMSE entry.

- [ ] **T010** [US2] Evaluate **both** the GNN (from T008) and the baseline (from T009) on the held‑out test set. Compute **R², RMSE, MAE** overall and stratified by any available `solvent`, `temperature`, or `measurement_method` metadata. Store results in `results/metrics.json`.  
  *Verification*: `metrics.json` conforms to the schema `{model: {overall: {...}, by_condition: {...}}}`; the R² for the GNN is ≥ 0.7 and exceeds the baseline by ≥ 0.05 (SC‑001) – this will be asserted by the CI test suite.

---

## Phase 3 – Interpretability, validation & hand‑off  

| Goal | Produce scientifically meaningful attribution, validate it against the curated motif set, and generate all required figures and reproducibility artefacts. |
|------|------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T017** [US3] Create the curated reference set of fluorophore motifs (Supplementary Table S1) **with full provenance documentation**: each motif entry (SMARTS + human-readable name) is drawn from peer‑reviewed literature sources **independent of the training data**, with citation, source, and selection criteria recorded. Write the motif table to `data/reference/fluorophore_motifs.csv` and the provenance/selection-criteria documentation to `docs/reference_set_provenance.md` (FR‑016). Verify independence: no molecule in the reference set's cited sources overlaps the training or test sets (checked via InChIKey where structures are listed).  
  *Verification*: `data/reference/fluorophore_motifs.csv` exists with columns `smarts`, `name`, `citation`; `docs/reference_set_provenance.md` documents provenance and selection criteria for every entry; an independence-check log reports zero overlap with train/test molecules.

- [ ] **T011** [US3] Apply **Integrated Gradients** (or SHAP if preferred) to the trained GNN for every molecule in `test.csv`, using the seeds pinned in T001. Aggregate atom‑level attributions into contiguous aromatic or conjugated fragments (detected via RDKit), sum absolute attributions per fragment, and rank the **top 20** substructures. Save a JSON mapping `substructure → attribution` to `results/attributions/top20_substructures.json`. **FR‑012 semantics**: molecules in the held‑out test set with atom/bond types unseen in training are **RETAINED** for evaluation — the system logs a summary report of such molecules for transparency (`results/unseen_types_report.txt`) but does not drop them. Skipping applies **only** to new inference inputs outside the dataset, which are logged and skipped with a warning.  
  *Verification*: The JSON contains exactly 20 entries; each entry includes a SMARTS string and a numeric score; `results/unseen_types_report.txt` exists and lists any test molecules with unseen atom/bond types, and the count of attributed molecules equals the full test-set size (no test molecules dropped).

- [ ] **T012** [US3] Validate the attribution results against the curated reference set of fluorophore motifs produced in T017 (`data/reference/fluorophore_motifs.csv`), whose provenance is documented in `docs/reference_set_provenance.md`.  
  *Steps*:  
  1. Compute the count of matches between the top 20 substructures and the reference set (must be ≥ 12).  
  2. Generate 100 random draws (seeded from `code/config/seeds.yaml`) of 20 substructures from the full fragment pool, compute the mean overlap, and verify that the observed overlap is **≥ 1.5×** this mean (enrichment).  
  3. Spot‑check the five highest‑FQY test molecules: ensure at least three of their top‑5 substructures appear in the reference set.  
  Save the validation report to `results/attrib_validation.txt` using this exact line-oriented schema (one line per check, parsed by CI):  
  `CHECK1 overlap_count: <int> threshold: 12 result: PASS|FAIL`  
  `CHECK2 enrichment_ratio: <float> threshold: 1.5 result: PASS|FAIL`  
  `CHECK3 spotcheck_matches: <int> threshold: 3 result: PASS|FAIL`  
  *Verification*: `results/attrib_validation.txt` exists at that exact path and contains the three CHECK lines in the exact schema above; CI asserts that all three report `result: PASS` (SC‑005).

- [ ] **T013** [US3] Generate the required visualizations and store them under `figures/`:  
  * `train_curve.png` – training vs. validation loss per epoch.  
  * `parity_plot.png` – predicted vs. experimental FQY for the test set (both models).  
  * `substructure_importance.png` – bar chart of the top 20 substructure attributions.  
  *Verification*: Each PNG file is created, non‑empty, and matches the expected dimensions (≥ 600 px width). The CI test suite loads them to confirm they are valid image files.

- [ ] **T014** [US2] Record resource usage for the entire pipeline: total wall‑clock time, peak RAM usage during training, and GPU usage flag (should be `false`), as **measured compliance evidence** for the limits enforced by T018. Write to `results/resource_usage.json`.  
  *Verification*: The JSON contains keys `wall_time_seconds`, `peak_ram_gb`, `gpu_used`; values are numeric and within the limits (≤ 6 h, ≤ 7 GB RAM); the run fails loudly (via the T018 watchdog) if any limit is exceeded.

- [ ] **T015** [US3] Write a **quickstart** guide (`quickstart.md`) that documents a single reproducible command to run the full pipeline from raw download to final figures, and create a **paper‑stage handoff** (`paper/handoff.md`) that lists the authoritative artefacts (`results/metrics.json`, `figures/*`, `results/attributions/*`) and their provenance.  
  *Verification*: `quickstart.md` contains a runnable one‑liner (e.g., `python -m src.run_pipeline`). Executing it on a fresh runner reproduces all files listed in `paper/handoff.md`. The handoff file includes SHA‑256 hashes of each artefact for traceability.

---

## Dependency & Requirement Mapping  

| Spec ID | Covered by Task(s) |
|---------|--------------------|
| FR‑001 | T001, T002, T003 |
| FR‑002 | T004 |
| FR‑003 | T007 |
| FR‑004 | T008 |
| FR‑005 | T010 |
| FR‑006 | T011 |
| FR‑007 | T013 |
| FR‑008 | T018 (enforcement), T014 (recording) |
| FR‑009 | T003 |
| FR‑010 / FR‑011 | T005 |
| FR‑012 | T011 (retain test molecules; skip only new inference inputs) |
| FR‑013 | T004 (warning) |
| FR‑014 | T004 (log), T016 (contract validation) |
| FR‑015 | T002 (metadata capture) |
| FR‑016 | T017 (reference set + provenance), T012 (validation) |
| FR‑017 | T010 (stratified reporting) |
| SC‑001 | T010 (performance thresholds) |
| SC‑002 | T018 (enforcement), T014 (measurement) |
| SC‑003 | T018 (enforcement), T014 (measurement) |
| SC‑004 | T004, T016 |
| SC‑005 | T012 (overlap & enrichment) & spot‑check |
| Constitution I (seeds) | T001 (pinning), T004, T008, T011, T012 (usage) |
| Data contract | T016 |

---  

*All tasks are unchecked; the CI system will mark them as completed only after the corresponding scripts pass their independent correctness tests.*