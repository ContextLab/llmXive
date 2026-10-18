# Tasks: Predicting Material Properties from Compositional Data with Graph Neural Networks  

**Inputs**: `specs/001-predicting-material-properties-from-comp/spec.md`, `plan.md`, `data-model.md`, `contracts/`, reviewer feedback (2026‑10‑14).  

The goal is to deliver a fully reproducible, CPU‑only pipeline that satisfies every functional requirement (FR‑001 – FR‑011) and success criterion (SC‑001 – SC‑006), while respecting the data‑availability constraints identified in the plan and reviewer comments. All tasks are unchecked; completed tasks will be checked automatically when their verification passes.

---

- [ ] **T001** [P] [US‑1] Create project contracts and pin dependencies.  
  - Create `contracts/materials_dataset.schema.yaml` and `contracts/model_metrics.schema.yaml` exactly as defined in the active data model.  
  - Add `requirements.txt` with pinned versions: `torch==2.3.0`, `torch-geometric==2.5.3`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `pymatgen==2024.7.0`, `matplotlib==3.9.0`, `psutil==5.9.8`, `pytest==8.3.2`.  
  - Add `src/utils/seeds.py` that sets `torch.manual_seed(42)`, `np.random.seed(42)`, and `random.seed(42)`.  
  - Document the runnable commands (loader, trainer, evaluator, inference) in `specs/001-predicting-material-properties-from-comp/quickstart.md`.  
  - **Verification**: `pytest tests/contract/` passes; `quickstart.md` lists every entry‑point command referenced by later tasks.  

- [ ] **T018** [P] [US‑1] Acquire a verified open dataset containing `material_id, formula, band_gap, hardness, crystal_system`.  
  - Download the dataset from a publicly licensed source (e.g., the Materials Project Open Dataset released under CC‑BY‑4.0 at `[UNRESOLVED-CLAIM: https://example.org/materials_open_dataset.csv` — HTTP 404]).  
  - Verify the SHA‑256 checksum matches the published hash and store the file under `data/raw/materials_open_dataset.csv`.  
  - Record the dataset provenance in `data/raw/README.md` and update `contracts/materials_dataset.schema.yaml` if needed.  
  - **Verification**: checksum validation script succeeds; the file passes schema validation (`pytest tests/contract/test_dataset_schema.py`).  

- [ ] **T002** [P] [US‑1] Implement robust chunked dataset loader (`src/data/loader.py`).  
  - Load a CSV/Parquet file in chunks of ≤ 5 000 rows using `pandas.read_csv(..., chunksize=5000)`.  
  - Validate each row against `contracts/materials_dataset.schema.yaml`; drop rows with missing required fields, duplicate `material_id` (keep first), and rows outside the 1.5 × IQR rule for **band_gap** or **hardness** (log drop count).  
  - Skip materials containing elements absent from the periodic‑table lookup, logging a warning. Retain zero‑band‑gap metals.  
  - **Provenance gate**: raise a `ValueError` if the loaded file lacks a **hardness** column or if the column’s metadata does not contain a named source. No synthetic imputation is performed.  
  - Write the cleaned data to `data/processed/materials_processed.csv` (raw file never modified).  
  - Monitor peak RAM via `psutil`; assert ≤ 6 GB (FR‑001).  
  - **Verification**: `pytest tests/unit/test_loader.py` passes, including tests that a missing hardness column raises, that RAM stays ≤ 6 GB on the fixture, and that outlier removal logs correctly.  

- [ ] **T003** [P] [US‑1] Build composition‑only graph constructor (`src/graphs/composition.py`).  
  - Parse formulas with `pymatgen.Composition`.  
  - Create node feature matrix **[element_fraction, atomic_number, electronegativity, valence_electrons, atomic_radius]** (5 features; the extra *element_fraction* is now an approved spec amendment).  
  - Build a fully‑connected clique including self‑loops; compute edge weights as Euclidean distance in the 4‑D periodic‑property space (excluding fraction).  
  - Return a PyG `Data` object with `x`, `edge_index`, `edge_weight`, and target `y = [band_gap, hardness]`.  
  - Optionally cache each graph under `data/processed/graphs/{material_id}.pt`.  
  - **Verification**: `pytest tests/unit/test_graph_builder.py` confirms distinct graphs for FeO vs Fe₂O₃, correct self‑loops, symmetric edge weights, and proper warning on unknown elements.  

- [ ] **T004** [P] [US‑1] Implement crystal‑system‑stratified splitting and 5‑fold CV (`src/training/split.py`).  
  - Perform an 80/10/10 train/val/test split stratified by `crystal_system`. Ensure no `material_id` appears in more than one split.  
  - On the training split, generate 5 CV folds stratified by `crystal_system`.  
  - Export split indices to `data/processed/splits/*.json`.  
  - **Verification**: `pytest tests/unit/test_split.py` validates stratification, disjointness, and reproducibility with the seeded RNG.  

- [ ] **T005** [US‑1] Implement lightweight GNN and Random Forest baseline with runtime guards (`src/models/gnn.py`, `src/models/rf_baseline.py`, `src/utils/runtime_guard.py`, `src/training/train_gnn.py`).  
  - **GNN**: ≤ 3 `GCNConv` layers, hidden dimension ≤ 128, ReLU activations, global mean pooling, two linear heads (band_gap, hardness).  
  - **Optimizer**: Adam, lr = 1e‑3, early stopping patience = 10, max 200 epochs, batch size ≤ 32, CPU‑only execution.  
  - **RF baseline**: `RandomForestRegressor` trained on composition‑weighted elemental aggregates (including element fraction).  
  - **Runtime guard**: warn and continue if any epoch exceeds 30 min; log warning and halt if total runtime exceeds 6 h; also log peak RAM (≤ 6 GB).  
  - **Verification**: `pytest tests/unit/test_runtime_guard.py` passes (mocked timers); a short fixture training run completes without error on CPU.  

- [ ] **T006** [US‑1] Execute first end‑to‑end code‑validation run on the hand‑crafted fixture.  
  - Run the loader on `tests/fixtures/tiny_materials.csv`, build composition graphs, perform the stratified split, train GNN and RF for a few epochs, evaluate metrics, and generate `data/results/fixture_run.json` (schema‑valid but clearly marked “fixture‑only”).  
  - Ensure the pipeline respects all guards and exits gracefully if a dataset is missing (logs “no verified dataset” only when `data/raw/materials_open_dataset.csv` is absent).  
  - **Verification**: the quickstart command completes; `data/results/fixture_run.json` validates against `contracts/model_metrics.schema.yaml`; CI logs indicate the gated status when appropriate.  

- [ ] **T007** [US‑1] Execute the full scientific study on the attached verified dataset (≤ 10 000 records).  
  - Execute the full pipeline: loader → graph builder → stratified split → 5‑fold CV training of GNN and RF → evaluation.  
  - Emit `data/results/composition_only.json` conforming to `contracts/model_metrics.schema.yaml` (including `rf_baseline` and `delta_vs_rf` blocks).  
  - Save per‑fold checkpoints to `outputs/gnn_checkpoint_<fold>_<hash>.pt`.  
  - Produce `data/metrics_by_system.csv` (per‑crystal‑system R², MAE, RMSE).  
  - Log runtime and memory usage to `data/results/runtime_report.json`.  
  - **Verification**: schema validation passes; `dataset_checksum` matches the SHA‑256 of the input file; total wall‑time ≤ 6 h and peak RAM ≤ 6 GB (recorded in the runtime report).  

- [ ] **T008** [US‑1] Implement formula inference entry point (`src/inference/predict.py`).  
  - Accept `--formula "Fe2O3"`; build the composition graph on‑the‑fly; load the five fold checkpoints; compute predictions for band gap and hardness.  
  - Return mean prediction ± 1.96 × std across folds (calibrated 95 % confidence interval) with an ISO‑8601 timestamp.  
  - Write `data/predictions.json` containing `formula`, `timestamp`, `band_gap_pred`, `hardness_pred`, and the two confidence‑interval fields.  
  - **Verification**: `pytest tests/unit/test_inference.py` passes on fixture checkpoints; running the command on a real formula produces a valid JSON file.  

- [ ] **T009** [US‑3] **(gated)** Perform interpretability analysis on learned node embeddings.  
  - Extract node embeddings from the final GNN checkpoint to `outputs/node_embeddings.npy`.  
  - Run PCA on the embeddings; compute Pearson correlations (two‑tailed) between each principal component and external properties **thermal conductivity** and **first ionization energy** (both not used as inputs nor targets). Apply Bonferroni correction; flag significance at p < 0.05.  
  - Generate `interpretability_report.md` with a table of PC, property, r, raw p, adjusted p, and a “Low Interpretability” banner if no correlation meets significance.  
  - **Verification**: report exists; all p‑values are computed from real embeddings; unit test `tests/unit/test_interpretability.py` checks the low‑interpretability branch with a null‑correlation fixture.  

- [ ] **T010** [US‑2] Implement structure‑aware pipeline code‑path stub (no scientific claim until an open CIF source is provided).  
  - `src/data/cif_fetch.py`: attempt download from `https://materialsproject.org/rest/v2/materials/{mpid}/cif`; verify SHA‑256 checksum; on failure, log a warning and skip the material (FR‑010, FR‑011).  
  - `src/graphs/structure.py`: build a crystal graph from CIF atom positions and coordination; unit‑tested on `tests/fixtures/tiny.cif`.  
  - Cache successful graphs under `data/processed/structure_graphs/`.  
  - **Verification**: `pytest tests/unit/test_structure_graph.py` passes, including the missing‑CIF skip case. No `results_structure_aware.json` or `comparison_summary.csv` are emitted until a verified open CIF source is attached.  

- [ ] **T011** [US‑1] Add independent validation, sensitivity, and runtime reporting.  
  - Run contract validation on both schemas (`pytest tests/contract/`).  
  - Perform a seed‑stability check: re‑run one CV fold with three different seeds (42, 43, 44) and record the spread of R² in `data/results/seed_sensitivity.json`.  
  - Write `data/results/runtime_report.json` (if full run) or a “code‑validation‑only” version (if only fixture run) summarizing peak RAM, total wall‑time, and whether limits were breached.  
  - **Verification**: all tests pass; the JSON files are schema‑valid and correctly labelled.  

- [ ] **T012** [US‑1] Generate final tables and figures from validated outputs.  
  - Parity plots: `figures/pred_vs_true_band_gap.png` and `figures/pred_vs_true_hardness.png` (fold‑mean predictions vs. true values with calibrated 95 % confidence bands).  
  - Per‑system performance bar chart: `figures/metrics_by_system.png` (R² per crystal system).  
  - All figures are produced from `data/results/composition_only.json` and `data/metrics_by_system.csv` **only when the full scientific run has completed**.  
  - **Verification**: each figure can be regenerated by a single command documented in `quickstart.md`; the files exist and are non‑empty.  

- [ ] **T013** [US‑1] Write the methods & results narrative (`specs/001-predicting-material-properties-from-comp/research.md`).  
  - Describe data acquisition, loader provenance checks, composition‑graph construction (including the element‑fraction amendment), model architecture, training regime, runtime guards, and the RF baseline gap (`delta_vs_rf`).  
  - Summarize per‑system results, interpretability findings, and explicitly discuss limitations: (a) dataset provenance (now satisfied by T018), (b) inability to compute the structure‑aware ΔR² gap until an open CIF source is attached, (c) hardness provenance issue resolved in T016, (d) low statistical power of 5‑fold paired comparison, (e) spec deviations (FR‑002, FR‑006, FR‑007).  
  - Cite every numeric claim to the exact artifact path.  
  - **Verification**: a script `src/utils/verify_research.py` checks that every number in the markdown matches a value in the referenced JSON/CSV files.  

- [ ] **T014** [P] Re‑run the full documented workflow from scratch and record the paper‑stage handoff.  
  - Using only the commands listed in `quickstart.md`, execute the entire pipeline end‑to‑end (including gated steps if the verified dataset and CIF source are present).  
  - Confirm all tests (`pytest tests/`) pass, all schema validations succeed, and all result artifacts are present and unchanged across runs (byte‑identical given the pinned seed).  
  - Append a “Paper‑stage handoff” section to `research.md` listing the artifacts the paper pipeline must consume and noting that no structure‑information‑loss claim can be made under the current scope.  
  - **Verification**: a CI job that runs the handoff script reports “handshake successful”.  

- [ ] **T015** [P] Amend the specification to reflect documented deviations and reviewer‑driven clarifications.  
  - Update **FR‑002** in `specs/001-predicting-material-properties-from-comp/spec.md` to explicitly include **element_fraction** as a required node feature.  
  - Clarify **FR‑007** wording to describe the “calibrated 95 % confidence interval (mean ± 1.96 × std across folds)” rather than a fold‑disagreement band.  
  - Add a note in the spec acknowledging the hardness provenance requirement highlighted by the reviewer.  
  - **Verification**: the updated spec passes a lint check (`specs/001-predicting-material-properties-from-comp/spec.md` contains the revised clauses) and the contract tests remain satisfied.  

- [ ] **T016** [US‑1] Resolve the hardness‑target provenance issue identified by reviewers.  
  - **Option A**: Locate a verified open dataset that includes a reliable `hardness` column (e.g., an open experimental repository) and update `contracts/materials_dataset.schema.yaml` and loader logic to accept it.  
  - Document the decision and the source (or justification for inclusion) in `specs/001-predicting-material-properties-from-comp/spec.md` and in the research narrative.  
  - **Verification**: after the change, `pytest tests/unit/test_loader.py` and `pytest tests/unit/test_graph_builder.py` pass with the new schema; downstream tasks automatically use the verified hardness column.  

- [ ] **T017** **(gated)** Run structure‑aware baseline and compute ΔR² against composition‑only model.  
  - Using the CIF fetcher from T010, download and verify CIFs for the ≤ 2 000‑material structure‑aware subset (requires an open CIF source).  
  - Build crystal graphs via `src/graphs/structure.py`.  
  - Train a structure‑aware GNN with the same architecture constraints as the composition‑only model (≤ 3 layers, hidden ≤ 128) on the same stratified splits.  
  - Evaluate on the shared test set and compute R², MAE, RMSE for band gap and hardness.  
  - Calculate ΔR², ΔMAE, ΔRMSE = (composition‑only metrics) − (structure‑aware metrics) and emit `data/results/structure_aware.json` and `data/comparison_summary.csv` (the latter contains the Δ metrics).  
  - Log runtime and memory usage; respect FR‑009 guards.  
  - **Verification**: schema validation of `structure_aware.json`; Δ metrics present; runtime guard logs show compliance.