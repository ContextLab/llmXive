# Tasks: Predicting Material Properties from Compositional Data with Graph Neural Networks  

**Inputs**: `specs/001-predict-material-properties-from-comp/spec.md`, `plan.md`, `data-model.md`, contract schemas, and reviewer feedback (2026‑10‑14).  

The aim is a reproducible, CPU‑only research pipeline that satisfies every functional requirement (FR‑001 – FR‑011) and success criterion (SC‑001 – SC‑006). Tasks are ordered to respect data flow; each includes an observable verification step. Checked tasks have already passed their verification; unchecked tasks must be completed and re‑run the verifier.

---  

- [ ] **T001** [P] **Create contracts, pin dependencies, and seed utility**  
  - Add `contracts/materials_dataset.schema.yaml` and `contracts/model_metrics.schema.yaml` exactly as defined in the active data model.  
  - Create `requirements.txt` with pinned versions: `torch==2.3.0`, `torch-geometric==2.5.3`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `pymatgen==2024.7.0`, `matplotlib==3.9.0`, `psutil==5.9.8`, `pytest==8.3.2`, `jsonschema==4.23.0`.  
  - Add `src/utils/seeds.py` that sets `torch.manual_seed(42)`, `np.random.seed(42)`, and `random.seed(42)`.  
  - Write `specs/001-predict-material-properties-from-comp/quickstart.md` documenting the exact CLI commands used by later tasks.  
  - **Verification**:  
    1. Run `pytest tests/contract/ -q --junitxml=outputs/test_logs/contract.xml 2>&1 | tee outputs/test_logs/contract.log`.  
    2. Confirm `quickstart.md` exists and contains the expected command strings (`python -m src.training.train_gnn ...`).  
    3. Both the JUnit XML and the log must end with `=== 0 passed in ...s ===`.  

- [ ] **T002** [P] **Validate presence and integrity of the open Materials dataset (including hardness column)**  
  - Ensure `data/raw/materials.csv` exists and contains the required columns `material_id, formula, band_gap, hardness, crystal_system`.  
  - Compute SHA‑256 checksum of the file and record it in `data/raw/README.md`.  
  - Execute schema validation: `pytest tests/contract/test_dataset_schema.py -q --junitxml=outputs/test_logs/dataset_schema.xml 2>&1 | tee outputs/test_logs/dataset_schema.log`.  
  - **Verification**:  
    1. The pytest command exits with code 0 and the log contains `0 passed`.  
    2. Verify that `data/raw/README.md` now contains a line `checksum: <sha256>` matching the computed value.  

- [ ] **T003** [P] **Implement robust chunked loader that satisfies unit tests**  
  - Create `src/data/loader.py` that reads `data/raw/materials.csv` in chunks of ≤ 5 000 rows (`pandas.read_csv(..., chunksize=5000)`).  
  - For each chunk:  
    1. Validate rows against `contracts/materials_dataset.schema.yaml`.  
    2. Drop duplicate `material_id` (keep first).  
    3. Apply 1.5 × IQR outlier removal **separately** for `band_gap` and `hardness`; log exact drop counts.  
    4. Skip rows whose formula contains an element missing from the periodic‑table lookup, logging a warning.  
    5. **Retain** zero‑band‑gap metals (do not drop them).  
  - After processing all chunks, concatenate kept rows and write to `data/processed/materials_processed.csv`.  
  - Use `psutil` to assert peak RAM ≤ 6 GB; raise `MemoryError` otherwise.  
  - **Verification**: `pytest tests/unit/test_loader.py -q --junitxml=outputs/test_logs/loader.xml 2>&1 | tee outputs/test_logs/loader.log` must pass, confirming (a) metals are kept, (b) exactly one outlier is removed, (c) **9** valid rows remain for the tiny fixture, and (d) RAM limit is respected.  

- [ ] **T004** [P] **Build composition‑only graph constructor** (`src/graphs/composition.py`)  
  - Parse formulas with `pymatgen.Composition`.  
  - Node features **exactly**: `[atomic_number, electronegativity, valence_electrons, atomic_radius]` (four features as required by FR‑002).  
  - Construct a fully‑connected clique (including self‑loops); edge weight = Euclidean distance in the 4‑D periodic‑property space.  
  - Return a PyG `Data` object with `x`, `edge_index`, `edge_weight`, and target `y = [band_gap, hardness]`.  
  - Cache each graph under `data/processed/graphs/{material_id}.pt`.  
  - **Verification**: `pytest tests/unit/test_graph_builder.py -q --junitxml=outputs/test_logs/graph_builder.xml 2>&1 | tee outputs/test_logs/graph_builder.log` must pass, checking distinct graphs for different stoichiometries, correct self‑loops, symmetric edge weights, and warning on unknown elements.  

- [ ] **T005** [P] **Implement crystal‑system‑stratified split and 5‑fold CV** (`src/training/split.py`)  
  - Perform an 80/10/10 train/val/test split stratified by `crystal_system`; ensure no `material_id` appears in more than one split.  
  - Generate 5 CV folds on the training portion, also stratified by `crystal_system`.  
  - Export split indices to `data/processed/splits/train.json`, `val.json`, `test.json`, and `fold_{i}.json` (i = 0‑4).  
  - **Verification**: `pytest tests/unit/test_split.py -q --junitxml=outputs/test_logs/split.xml 2>&1 | tee outputs/test_logs/split.log` must pass, confirming stratification, disjointness, and reproducibility with the seeded RNG.  

- [ ] **T006** [P] **Implement lightweight GNN, Random Forest baseline, and runtime‑guard utilities**  
  - **GNN** (`src/models/gnn.py`): ≤ 3 `GCNConv` layers, hidden dim ≤ 128, ReLU, global mean pooling, two linear heads (band gap & hardness).  
  - **RF baseline** (`src/models/rf_baseline.py`): `RandomForestRegressor` (200 trees, seed = 42) trained on composition‑weighted elemental aggregates (including the four mandated features).  
  - **Runtime guard** (`src/utils/runtime_guard.py`):  
    * Warn if any epoch exceeds 30 min (continues).  
    * Halt the job if total wall‑time exceeds 6 h (logs warning and exits with code 1).  
    * Log peak RAM usage; assert ≤ 6 GB.  
  - Include deterministic seeding via `src/utils/seeds.py`.  
  - **Verification**:  
    1. `pytest tests/unit/test_runtime_guard.py -q --junitxml=outputs/test_logs/runtime_guard.xml 2>&1 | tee outputs/test_logs/runtime_guard.log` must pass (uses mocked timers).  

- [ ] **T006a** [P] **Debug and fix GNN training/evaluation scripts**  
  - Run the full training script on the tiny fixture and capture exit codes.  
  - Fix any exceptions so that `src/training/train_gnn.py` and `src/training/evaluate.py` exit with status 0.  
  - Add unit tests `tests/unit/test_train_gnn_exit.py` and `tests/unit/test_evaluate_exit.py` that assert a zero exit code on the fixture.  
  - **Verification**: Both new tests must pass, confirming the scripts now satisfy FR‑003 and FR‑006.  

- [ ] **T007** [P] **Run fixture end‑to‑end validation (tiny_materials.csv)**  
  - Execute the full pipeline on the fixture: loader → composition graph builder → split → train GNN & RF for 2 epochs → evaluate → produce `data/results/fixture_run.json`.  
  - The JSON must conform to `contracts/model_metrics.schema.yaml` and include a `"fixture": true` flag.  
  - Log all commands in `outputs/test_logs/fixture_end_to_end.log`.  
  - **Verification**:  
    * `pytest tests/fixture_end_to_end.py -q --junitxml=outputs/test_logs/fixture_end_to_end.xml 2>&1 | tee outputs/test_logs/fixture_end_to_end.log` passes.  
    * Schema validation (`jsonschema.validate`) succeeds for `fixture_run.json`.  

- [ ] **T008** [P] **Execute full composition‑only study on the verified dataset**  
  - Prerequisite: `T002` succeeded and dataset checksum recorded.  
  - Run the complete pipeline: loader → composition‑only graph builder → stratified split → 5‑fold CV training of GNN and RF → evaluation on the shared test set.  
  - Emit:  
    * `data/results/composition_only.json` (conforms to `model_metrics.schema.yaml`, includes `rf_baseline` and `delta_vs_rf`).  
    * Per‑fold checkpoints `outputs/gnn_checkpoint_fold{i}_{hash}.pt`.  
    * `data/metrics_by_system.csv` (per crystal‑system R², MAE, RMSE).  
    * `data/results/runtime_report.json` (peak RAM, total wall‑time, any guard warnings).  
  - **Verification**:  
    * `pytest tests/integration/test_full_composition.py -q --junitxml=outputs/test_logs/full_composition.xml 2>&1 | tee outputs/test_logs/full_composition.log` passes.  
    * SHA‑256 of the source CSV matches `dataset_checksum` stored in `composition_only.json`.  
    * `pytest tests/integration/test_metrics_by_system.py -q --junitxml=outputs/test_logs/metrics_by_system.xml 2>&1 | tee outputs/test_logs/metrics_by_system.log` confirms the CSV exists and contains the required columns.  

- [ ] **T009** [P] **Provide formula inference entry point** (`src/inference/predict.py`)  
  - CLI: `python -m src.inference.predict --formula "Fe2O3"`.  
  - Build the composition graph on‑the‑fly, load the five fold checkpoints, compute predictions for band gap and hardness, and aggregate across folds to produce mean ± 1.96 × std (fold‑disagreement band).  
  - Output `data/predictions.json` with fields: `formula`, `timestamp` (ISO‑8601), `band_gap_pred`, `hardness_pred`, `band_gap_band_disagreement`, `hardness_band_disagreement`.  
  - **Verification**: `pytest tests/unit/test_inference.py -q --junitxml=outputs/test_logs/inference.xml 2>&1 | tee outputs/test_logs/inference.log` passes; manual run of the CLI creates a valid JSON file validated against a small schema.  

- [ ] **T010** [P] **Interpretability & embedding analysis**  
  - Extract node embeddings from the final GNN checkpoint (`outputs/node_embeddings.npy`).  
  - Perform PCA on the embeddings.  
  - Compute Pearson correlation (two‑tailed) between each principal component and external properties **thermal conductivity** and **first ionization energy** (both not used as inputs nor targets).  
  - Apply Bonferroni correction; flag significance at p < 0.05.  
  - Generate `interpretability_report.md` containing a table of PC, property, r, raw p, adjusted p, and a “Low Interpretability” banner if no entry meets significance.  
  - **Verification**: `pytest tests/unit/test_interpretability.py -q --junitxml=outputs/test_logs/interpretability.xml 2>&1 | tee outputs/test_logs/interpretability.log` passes; the report file exists and contains at least one row.  

- [ ] **T011** [P] **Acquire and cache verified open CIF files per material via Materials Project API**  
  - For each `material_id` in the structure‑aware subset (≤ 2 000 materials), download the CIF from `https://materialsproject.org/rest/v2/materials/{mpid}/cif`.  
  - Verify each file’s SHA‑256 checksum against the `Content-MD5` header (or a manifest generated on first successful download).  
  - Store verified CIFs under `data/raw/cifs/{material_id}.cif`.  
  - Log download progress, any missing files, and checksum mismatches; missing CIFs are handled downstream as per FR‑010.  
  - **Verification**: `python scripts/verify_cif_manifest.py` exits with code 0 and produces `outputs/test_logs/cif_manifest.log` showing successful verification of all retrieved files.  

- [ ] **T012** [P] **Build and evaluate structure‑aware GNN, compute performance gap**  
  - Using CIFs from `T011`, construct crystal graphs via `src/graphs/structure.py` (caches under `data/processed/structure_graphs/{material_id}.pt`).  
  - Re‑use the split indices from `T005` (same train/val/test splits).  
  - Train a GNN with identical architecture/hyper‑parameters as in `T006` on the structure graphs (5‑fold CV).  
  - Evaluate on the shared test set; emit:  
    * `data/results/structure_aware.json` (same schema as composition results; hardness may be null).  
    * `data/comparison_summary.csv` containing ΔR², ΔMAE, ΔRMSE (composition − structure) for band gap (hardness may be null).  
  - **Verification**: `pytest tests/integration/test_structure_aware.py -q --junitxml=outputs/test_logs/structure_aware.xml 2>&1 | tee outputs/test_logs/structure_aware.log` passes; both JSON and CSV conform to their schemas and Δ calculations match manual recomputation.  

- [ ] **T012a** [P] **Verify performance‑gap CSV**  
  - Run `pytest tests/integration/test_comparison_summary.py -q --junitxml=outputs/test_logs/comparison_summary.xml 2>&1 | tee outputs/test_logs/comparison_summary.log`.  
  - The test asserts that `comparison_summary.csv` exists, contains columns `delta_r2`, `delta_mae`, `delta_rmse` for each target, and that values are numeric.  
  - **Verification**: Test must pass, confirming SC‑002 is covered.  

- [ ] **T013** [P] **Compute true 95 % confidence intervals for predictions (FR‑007)**  
  - After training, generate predictions on the test set for each of the 5 CV folds.  
  - For each target, compute the standard error of the mean across folds and construct intervals: `mean ± 1.96 × standard_error`.  
  - Add a top‑level field `confidence_interval` to `data/results/composition_only.json` and, if present, to `structure_aware.json`.  
  - **Verification**: `pytest tests/unit/test_confidence_interval.py -q --junitxml=outputs/test_logs/confidence_interval.xml 2>&1 | tee outputs/test_logs/confidence_interval.log` passes; intervals are numeric and correctly derived from the fold predictions.  

- [ ] **T014** [P] **Write methods & results narrative and perform full workflow handoff** (`specs/001-predict-material-properties-from-comp/research.md`)  
  - When `composition_only.json` (and, if available, `structure_aware.json`) exist, draft a markdown methods & results section that cites each numeric claim to its exact artifact path.  
  - Include a “Paper‑stage handoff” subsection listing required artifacts: `data/results/composition_only.json`, `data/results/structure_aware.json` (optional), `data/metrics_by_system.csv`, `interpretability_report.md`, `data/predictions.json`, and the manifest `data/results/handoff_manifest.yaml`.  
  - If result files are missing, write a placeholder narrative explaining the missing inputs and next steps.  
  - **Verification**: `src/utils/verify_research.py` checks that every number in the markdown matches the corresponding value in the referenced JSON/CSV files; exits with status 0 when all present, otherwise reports mismatches.  

- [ ] **T015** [P] **Re‑run the documented workflow from scratch and record handoff manifest** (`src/utils/handshake.py`)  
  - Using only the commands listed in `quickstart.md`, execute the entire pipeline end‑to‑end (including structure‑aware steps `T011`‑`T012` and confidence‑interval computation `T013`).  
  - After successful completion, compute SHA‑256 hashes of all primary result files and write them to `data/results/handoff_manifest.yaml`.  
  - Log the full run in `outputs/test_logs/full_handshake.log`.  
  - If required inputs are absent, the script logs “handshake skipped – missing inputs” and exits with code 0.  
  - **Verification**: Running `python -m src.utils.handshake` prints “handshake successful” and the manifest file exists with matching hashes; `pytest tests/integration/test_handshake.py -q --junitxml=outputs/test_logs/handshake.xml 2>&1 | tee outputs/test_logs/handshake.log` passes.  

- [ ] **T016** [P] **Amend model metrics schema to capture structure‑aware performance gap**  
  - Draft an updated `contracts/model_metrics.schema.yaml` that adds a required `delta_vs_structure` block mirroring `delta_vs_rf` (fields: `delta_r2`, `delta_mae`, `delta_rmse` for each target).  
  - Submit the schema change as a pull‑request to the repository and record the PR identifier in `data/results/schema_amendment_log.txt`.  
  - **Verification**: The PR is open and passes CI validation of the updated schema (no test failures).  

- [ ] **T017** [P] **Amend materials dataset schema to require non‑null hardness**  
  - Edit `contracts/materials_dataset.schema.yaml` to change the `hardness` property definition from `type: [number, "null"]` to `type: number` and remove the `null` option.  
  - Update any downstream code that previously allowed `null` hardness to raise a validation error if missing.  
  - Add a unit test `tests/contract/test_hardness_nonnull.py` that validates a sample dataset containing a `null` hardness value fails schema validation.  
  - Submit the schema change as a pull‑request and record the PR identifier in `data/results/schema_amendment_log.txt`.  
  - **Verification**: The PR is open, CI runs the new test, and the schema validation now enforces non‑null hardness.  

---  

**Ordering summary**:  
T001 → T002 → T003 → T004 → T005 → T006 → T006a → T007 → T008 → T009 → T010 → T011 → T012 → T012a → T013 → T014 → T015 → T016 → T017.  

All tasks respect the data‑flow constraints, use only project‑owned paths, and avoid any fabricated data or synthetic stand‑ins. Completion of the unchecked tasks will allow the verifier to run cleanly on the next analysis pass.  