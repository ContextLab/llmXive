# Tasks: Predicting Material Properties from Compositional Data with Graph Neural Networks  

**Inputs**: `specs/001-predicting-material-properties-from-comp/spec.md`, `plan.md`, `data-model.md`, `contracts/`, reviewer feedback (2026‑10‑14).

The goal is a reproducible, CPU‑only research pipeline that satisfies every functional requirement (FR‑001 – FR‑011) and success criterion (SC‑001 – SC‑006) while respecting the current data‑availability constraints. All tasks are unchecked; each will be marked complete automatically when its verification steps pass.

---

- [ ] **T001** [P] [US‑1] **Create contracts, pin dependencies, and seed utility**  
  - Add `contracts/materials_dataset.schema.yaml` and `contracts/model_metrics.schema.yaml` exactly as defined in the active data model.  
  - Add `requirements.txt` with pinned versions: `torch==2.3.0`, `torch-geometric==2.5.3`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `pymatgen==2024.7.0`, `matplotlib==3.9.0`, `psutil==5.9.8`, `pytest==8.3.2`.  
  - Add `src/utils/seeds.py` that sets `torch.manual_seed(42)`, `np.random.seed(42)`, and `random.seed(42)`.  
  - Create `specs/001-predicting-material-properties-from-comp/quickstart.md` documenting the entry‑point commands referenced by later tasks.  
  - **Verification**: `pytest tests/contract/` passes; `quickstart.md` lists every command referenced by subsequent tasks.

- [ ] **T002** [P] [US‑1] **Acquire a verified open dataset containing all required columns**  
  - Identify a publicly licensed dataset (CC‑BY‑4.0 or similar) that provides `material_id`, `formula`, `band_gap`, **hardness**, and `crystal_system`.  
  - Download the CSV to `data/raw/materials_open_dataset.csv`.  
  - Record the SHA‑256 checksum in `data/raw/README.md` and update the loader to verify the checksum before processing.  
  - **Verification**: checksum validation script succeeds; schema validation (`pytest tests/contract/test_dataset_schema.py`) passes on the downloaded file.

- [ ] **T003** [P] [US‑1] **Implement robust chunked dataset loader** (`src/data/loader.py`)  
  - Load the CSV in chunks of ≤ 5 000 rows using `pandas.read_csv(..., chunksize=5000)`.  
  - For each chunk: validate rows against `contracts/materials_dataset.schema.yaml`; drop rows with missing required fields, duplicate `material_id` (keep first), and rows outside the 1.5 × IQR rule for **band_gap** or **hardness** (log drop count).  
  - Skip materials containing elements absent from the periodic‑table lookup, logging a warning; retain zero‑band‑gap metals.  
  - Raise a `ValueError` if required columns are missing (e.g., no hardness column). No synthetic imputation.  
  - Write the cleaned data to `data/processed/materials_processed.csv`.  
  - Monitor peak RAM via `psutil` and assert ≤ 6 GB (FR‑001).  
  - **Verification**: `pytest tests/unit/test_loader.py` passes, including outlier‑removal logging and RAM‑limit assertion.

- [ ] **T004** [P] [US‑1] **Build composition‑only graph constructor** (`src/graphs/composition.py`)  
  - Parse formulas with `pymatgen.Composition`.  
  - Create node feature matrix **[element_fraction, atomic_number, electronegativity, valence_electrons, atomic_radius]** (5 features; element_fraction added as a spec amendment).  
  - Build a fully‑connected clique including self‑loops; compute edge weights as Euclidean distance in the 4‑D periodic‑property space (excluding fraction).  
  - Return a PyG `Data` object with `x`, `edge_index`, `edge_weight`, and target `y = [band_gap, hardness]`.  
  - Optionally cache each graph under `data/processed/graphs/{material_id}.pt`.  
  - **Verification**: `pytest tests/unit/test_graph_builder.py` confirms distinct graphs for FeO vs Fe₂O₃, correct self‑loops, symmetric edge weights, and warning on unknown elements.

- [ ] **T005** [P] [US‑1] **Implement crystal‑system‑stratified split and 5‑fold CV** (`src/training/split.py`)  
  - Perform an 80/10/10 train/val/test split stratified by `crystal_system`; ensure no `material_id` appears in more than one split.  
  - Generate 5 CV folds on the training split, also stratified by `crystal_system`.  
  - Export split indices to `data/processed/splits/*.json`.  
  - **Verification**: `pytest tests/unit/test_split.py` validates stratification, disjointness, and reproducibility with the seeded RNG.

- [ ] **T006** [P] [US‑1] **Implement lightweight GNN, Random Forest baseline, and runtime guards**  
  - **GNN** (`src/models/gnn.py`): ≤ 3 `GCNConv` layers, hidden dimension ≤ 128, ReLU, global mean pooling, two linear heads for band gap and hardness.  
  - **Optimizer**: Adam, lr = 1e‑3, early‑stopping patience = 10, max 200 epochs, batch size ≤ 32, CPU‑only execution.  
  - **RF baseline** (`src/models/rf_baseline.py`): `RandomForestRegressor` trained on composition‑weighted elemental aggregates (including element_fraction).  
  - **Runtime guard** (`src/utils/runtime_guard.py`): warn and continue if any epoch > 30 min; log warning and halt if total runtime > 6 h; log peak RAM (≤ 6 GB).  
  - **Verification**: `pytest tests/unit/test_runtime_guard.py` passes (mocked timers); a short fixture training run completes without error on CPU.

- [ ] **T007** [P] [US‑1] **Execute fixture end‑to‑end validation run** (`tests/fixtures/tiny_materials.csv`)  
  - Run the full pipeline on the tiny fixture: loader → graph builder → split → train GNN & RF for a few epochs → evaluate → produce `data/results/fixture_run.json`.  
  - The JSON must conform to `contracts/model_metrics.schema.yaml` and be clearly marked “fixture‑only”.  
  - Ensure the pipeline respects all guards and exits gracefully if the main dataset is absent (log “no verified dataset”).  
  - **Verification**: quickstart command completes; `data/results/fixture_run.json` validates against the schema; CI logs indicate gated status when appropriate.

- [ ] **T008** [P] [US‑1] **Run full scientific study on the verified dataset**  
  - Execute the complete pipeline: loader → composition‑graph builder → stratified split → 5‑fold CV training of GNN and RF → evaluation on the shared test set.  
  - Emit `data/results/composition_only.json` conforming to `contracts/model_metrics.schema.yaml` (including `rf_baseline` and `delta_vs_rf` blocks).  
  - Save per‑fold checkpoints to `outputs/gnn_checkpoint_<fold>_<hash>.pt`.  
  - Produce `data/metrics_by_system.csv` (per‑crystal‑system R², MAE, RMSE).  
  - Write `data/results/runtime_report.json` summarising peak RAM, total wall‑time, and any guard warnings (must be ≤ 6 h and ≤ 6 GB).  
  - **Verification**: schema validation passes; `dataset_checksum` matches the SHA‑256 of `data/raw/materials_open_dataset.csv`; runtime limits respected as recorded.

- [ ] **T009** [P] [US‑1] **Implement formula inference entry point** (`src/inference/predict.py`)  
  - Accept `--formula "Fe2O3"`; build the composition graph on‑the‑fly; load the five fold checkpoints; compute predictions for band gap and hardness.  
  - Return mean prediction ± 1.96 × std across folds (fold‑disagreement band) with an ISO‑8601 timestamp.  
  - Write `data/predictions.json` containing `formula`, `timestamp`, `band_gap_pred`, `hardness_pred`, and the two confidence‑interval fields.  
  - **Verification**: `pytest tests/unit/test_inference.py` passes on fixture checkpoints; running the command on a real formula produces a valid JSON file.

- [ ] **T010** [P] [US‑3] **(gated) Perform interpretability analysis on learned embeddings**  
  - Extract node embeddings from the final GNN checkpoint to `outputs/node_embeddings.npy`.  
  - Run PCA on the embeddings; compute Pearson correlations (two‑tailed) between each principal component and external properties **thermal conductivity** and **first ionization energy** (both not used as inputs nor targets).  
  - Apply Bonferroni correction; flag significance at p < 0.05.  
  - Generate `interpretability_report.md` with a table of PC, property, r, raw p, adjusted p, and a “Low Interpretability” banner if no correlation meets significance.  
  - **Verification**: report exists; all p‑values are computed from real embeddings; `tests/unit/test_interpretability.py` checks the low‑interpretability branch with a null‑correlation fixture.

- [ ] **T011** [P] [US‑2] **(gated) Implement CIF fetch stub and crystal‑graph builder**  
  - `src/data/cif_fetch.py`: attempt download from `https://materialsproject.org/rest/v2/materials/{mpid}/cif`; verify SHA‑256 checksum; on failure, log a warning and skip the material (FR‑010, FR‑011).  
  - `src/graphs/structure.py`: build a crystal graph from CIF atom positions and coordination; unit‑tested on `tests/fixtures/tiny.cif`.  
  - Cache successful structure graphs under `data/processed/structure_graphs/`.  
  - No `results_structure_aware.json` or `comparison_summary.csv` are emitted until an open CIF source is attached.  
  - **Verification**: `pytest tests/unit/test_structure_graph.py` passes, including the missing‑CIF skip case.

- [ ] **T012** [P] **Amend the specification to record documented deviations and resolve hardness provenance**  
  - Update **FR‑002** in `specs/001-predicting-material-properties-from-comp/spec.md` to explicitly include **element_fraction** as a required node feature.  
  - Clarify **FR‑007** wording to describe the “calibrated 95 % confidence interval (mean ± 1.96 × std across folds)”.  
  - Add a note acknowledging the hardness‑target provenance issue and cite the dataset added in **T002** as the verified source.  
  - **Verification**: the revised `spec.md` passes a lint check (`specs/001-predicting-material-properties-from-comp/spec.md` contains the revised clauses) and all contract tests remain satisfied.

- [ ] **T013** [P] **Write methods & results narrative and perform full workflow handoff** (`specs/001-predicting-material-properties-from-comp/research.md`)  
  - Describe data acquisition (including checksum), loader provenance checks, composition‑graph construction (with element_fraction amendment), model architecture, training regime, runtime guards, and the RF baseline gap (`delta_vs_rf`).  
  - Summarise per‑system results, interpretability findings, and explicitly discuss limitations: (a) dataset provenance now satisfied, (b) inability to compute structure‑aware ΔR² until an open CIF source is attached, (c) low statistical power of 5‑fold paired comparison, (d) spec deviations noted in **T012**.  
  - Cite every numeric claim to the exact artifact path.  
  - Append a “Paper‑stage handoff” section listing artifacts the paper pipeline must consume (`data/results/composition_only.json`, `data/metrics_by_system.csv`, `figures/…`, `interpretability_report.md`).  
  - **Verification**: `src/utils/verify_research.py` checks that every number in the markdown matches a value in the referenced JSON/CSV files; the script exits with status 0.

- [ ] **T014** [P] **Re‑run the documented workflow from scratch and record successful handoff**  
  - Using only the commands listed in `quickstart.md`, execute the entire pipeline end‑to‑end (including gated steps if the verified dataset and CIF source are present).  
  - Confirm all tests (`pytest tests/`) pass, all schema validations succeed, and all result artifacts are byte‑identical across runs given the pinned seed.  
  - Record the final SHA‑256 hashes of all primary result files in `data/results/handoff_manifest.yaml`.  
  - **Verification**: a CI job that runs `src/utils/handshake.py` reports “handshake successful” and the manifest matches expected hashes.

---  

*All tasks respect the data‑flow ordering: T001 → T002 → T003 → T004 → T005 → T006 → (T007 fixture validation) → T008 full run → T009 inference → T010 interpretability → T011 CIF stub → T012 spec amendment → T013 narrative → T014 handoff.*
