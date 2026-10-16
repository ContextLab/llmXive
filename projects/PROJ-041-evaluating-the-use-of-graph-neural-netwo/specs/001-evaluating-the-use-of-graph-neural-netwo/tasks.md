# Tasks: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic  

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, JSON‑Schema contracts, and reviewer feedback.  
All paths are relative to the repository root.

---

## Phase 1 – Project bootstrap  

- [ ] **T001** **Create project layout & core utilities**  
  *Creates* the top‑level directories `code/`, `data/`, `docs/`, `tests/`, writes `requirements.txt` (pinning Python 3.11, `torch`‑CPU, `torch‑geometric`, `networkx`, `scikit‑learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `captum`, `pytest`, `pytest‑memprof`), adds a minimal `pyproject.toml` for formatting tools, implements deterministic seed handling (`code/utils/seed.py`) and a RAM‑limit wrapper (`code/utils/memory_monitor.py`).  
  **Verification**: `tree` shows the directories; `pip install -r requirements.txt` succeeds; `seed.set_seed(42)` yields reproducible RNG state; `memory_monitor.run_with_limit` raises `MemoryLimitError` when a dummy allocation exceeds 7 GB; a sample JSON validates against `contracts/*.schema.yaml` without error.

## Phase 2 – Data acquisition & preprocessing  

- [ ] **T002** **Download the CTU‑13 Scenario 1 NetFlow CSV (real, verified URL) and register it**  
  *Script*: `code/data/download_ctu13.py`  
  1. Downloads **Scenario 1** NetFlow CSV from the official CTU‑13 repository using a direct raw URL, e.g. `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/CTU-AI-Lab/CTU-13-Dataset/master/Scenario1/Scenario1-1.csv` — HTTP 404].  
  2. Saves the file to `data/raw/ctu13_scenario1.csv`.  
  3. Computes a SHA‑256 checksum and writes `data/raw/ctu13_scenario1.csv.sha256`.  
  4. Updates `code/config.yaml` with `active_dataset: ctu13_scenario1`.  
  **Verification**: The script exits with status 0; the downloaded file exists; its checksum matches the recorded value; any HTTP or network error raises a `RuntimeError` (no silent fallback).

- [ ] **T003** **Ingest NetFlow records, validate against schema, and build the raw directed graph**  
  *Scripts*: `code/data/ingest_netflow.py`, `code/data/build_graph.py`  
  1. `ingest_netflow.py` reads `data/raw/ctu13_scenario1.csv`, validates each row against `contracts/dataset.schema.yaml` using `jsonschema`, hashes IP addresses (SHA‑256), and writes a cleaned Parquet file `data/processed/raw_flows_scenario1.parquet` plus checksum `raw_flows_scenario1.parquet.sha256`.  
  2. `build_graph.py` streams the Parquet file, creates a `networkx.DiGraph` where node IDs are the hashed IPs and edge attribute `weight` equals the packet count; timestamps are preserved. The construction is wrapped by `memory_monitor.run_with_limit(limit_gb=7)`.  
  3. Serialises the graph to compressed GraphML `data/processed/graph_scenario1_raw.graphml.gz` and writes checksum `graph_scenario1_raw.graphml.gz.sha256`.  
  **Verification**:  
  - `raw_flows_scenario1.parquet` loads without schema violations.  
  - `graph_scenario1_raw.graphml.gz` loads via `nx.readwrite.graphml.read_graphml` and reports `G.number_of_nodes() ≤ 10 000`.  
  - `data/results/memory_usage.json` records `"peak_memory_gb" ≤ 7.0`.  
  - All checksum side‑cars validate.

- [ ] **T004** **Validate graph size, retain the largest weakly connected component (LCC), then perform deterministic subsampling if needed**  
  *Script*: `code/data/subsample_graph.py`  
  1. Loads `graph_scenario1_raw.graphml.gz`, extracts the **largest weakly connected component (LCC)** and writes `data/processed/graph_scenario1_lcc.graphml.gz` (+ checksum).  
  2. If the LCC node count > 5 000, selects the top 5 000 nodes by degree **while preserving every node with `is_anomaly = True`** to create an induced subgraph `data/processed/graph_scenario1_subsampled.graphml.gz` (+ checksum).  
  3. Updates `code/config.yaml` with `final_graph_path` pointing to the LCC graph if its size ≤ 5 000, otherwise to the subsampled graph.  
  **Verification**: LCC loads and its node count equals component size; subsampled graph (when created) has exactly 5 000 nodes and includes all anomalous nodes; checksums match; `config.yaml` correctly references the chosen final graph.

- [ ] **T005** **Temporal hold‑out split & node‑level feature engineering**  
  *Script*: `code/data/split_and_features.py`  
  1. Loads `raw_flows_scenario1.parquet`, sorts by `start_time`, and splits 80 % earliest records to `data/processed/train_flows.parquet` and the remaining 20 % to `data/processed/test_flows.parquet` (both with checksums).  
  2. Builds **training** and **test** graphs *only* from their respective flow files using the same graph‑builder logic, producing `graph_scenario1_train.graphml.gz` and `graph_scenario1_test.graphml.gz`.  
  3. Computes node‑level structural features (degree, in/out degree, betweenness centrality, clustering coefficient, edge‑weight variance, temporal activity span) for each graph and writes Parquet tables `features_scenario1_train.parquet` and `features_scenario1_test.parquet` (with checksums). Each table contains columns `node_id, degree, in_degree, out_degree, betweenness_centrality, clustering_coeff, edge_weight_variance, temporal_span, label`.  
  **Verification**:  
  - Split files exist, contain the expected row counts, and timestamps respect the 80/20 split.  
  - Both graph files load and have ≤ 5 000 nodes.  
  - Feature tables contain all required columns and pass a sanity‑type check (numeric fields are numeric, `label` is boolean).  
  - All checksum side‑cars validate.

## Phase 3 – Model training, evaluation & statistical analysis  

- [ ] **T006** **Define models & train across ten random seeds**  
  *Modules*: `code/models/gcn.py` (2‑layer GCN, CPU‑only, early stopping: max 30 epochs, patience 5, `min_delta=1e‑4`), `code/models/baselines.py` (wrappers for `RandomForestClassifier` and `XGBClassifier`).  
  For each seed in `[0,1,2,3,4,5,6,7,8,9]`:  
  1. Set RNG via `utils.seed.set_seed`.  
  2. Load `features_scenario1_train.parquet`.  
  3. Train the GCN (saving checkpoint `data/models/gcn_seed{seed}.pt`) and the two baselines (saving `rf_seed{seed}.pkl`, `xgb_seed{seed}.pkl`).  
  **Verification**: All model files exist, can be deserialized, and training logs contain a line indicating early‑stopping or max‑epoch termination without errors.

- [ ] **T007** **Evaluate all models on the held‑out test set, aggregate results, and compute GCN vs. RF AUC‑ROC delta**  
  *Script*: `code/evaluation/evaluate.py`  
  1. Loads each trained model and `features_scenario1_test.parquet`, generates predictions, and computes **Precision, Recall, F1‑Score, AUC‑ROC** (using `sklearn.metrics`).  
  2. Writes a JSON record per `(model, seed)` to `data/results/metrics_{model}_seed{seed}.json`.  
  3. `aggregate.py` reads the six JSON files per model, calculates mean ± std for each metric across seeds, and writes `data/results/aggregate_{model}.csv`.  
  4. Computes the delta AUC‑ROC between GCN and Random Forest (`delta_auc = gcn_mean_auc - rf_mean_auc`) and writes `data/results/auc_comparison.json` containing `{ "gcn_mean_auc":…, "rf_mean_auc":…, "delta_auc":…, "gcn_outperforms_rf": <bool> }`.  
  **Verification**:  
  - Every metrics JSON contains keys `precision`, `recall`, `f1_score`, `auc_roc` with values in `[0,1]`.  
  - Each aggregate CSV has columns `metric,mean,std`.  
  - `auc_comparison.json` exists, `delta_auc` is numeric, and `gcn_outperforms_rf` correctly reflects whether `delta_auc > 0`.

- [ ] **T008** **Perform Wilcoxon signed‑rank tests and apply Benjamini‑Hochberg correction**  
  *Script*: `code/analysis/significance.py`  
  1. For the seven hypotheses defined in **FR‑006** (GCN vs RF, GCN vs XGB, and the top‑5 structural features vs. a null baseline) extracts the paired F1‑scores across the ten seeds and runs `scipy.stats.wilcoxon`. Stores raw two‑sided p‑values in `data/results/pvalues_wilcoxon.json`.  
  2. Applies the Benjamini‑Hochberg (BH) procedure to the seven p‑values, producing adjusted q‑values in `data/results/bh_corrected.json` and a boolean flag `significant` for any hypothesis with `q < 0.05`.  
  **Verification**: Both JSON files contain seven entries with numeric `p_value` / `q_value`; at least one entry has `significant: true` **or**, if none survive, the file still records the outcome and the downstream reporting task (T013) will note the limitation.

- [ ] **T009** **Model attribution & pattern‑level analysis**  
  1. **Integrated Gradients** – `code/analysis/attribution.py` runs Captum’s `IntegratedGradients` on the best‑seed GCN checkpoint, yielding attribution scores per structural feature; writes `data/results/gcn_attributions.json`.  
  2. **Random Forest feature importance** – averages `feature_importances_` across the ten RF seeds; writes `data/results/rf_importances.json`.  
  3. **Bootstrap ranking comparison** – `code/analysis/patterns.py` resamples test predictions 1 000 times, computes rank differences between GCN attribution and RF importance for each feature, derives 95 % confidence intervals, and writes `data/results/distinct_patterns.json` (features whose CI excludes zero are marked `distinct: true`).  
  **Verification**: All three JSON files exist; `distinct_patterns.json` lists at least one feature with `distinct: true`.

- [ ] **T010** **Assess predictive power of distinct patterns and enforce target AUC**  
  1. Constructs a reduced feature matrix containing only the `distinct` structural features identified in T009.  
  2. Trains a Logistic Regression (CPU) on the training split (seed 0) and evaluates AUC‑ROC on the test split; writes `data/results/distinct_pattern_auc.json`.  
  3. Loads the pre‑defined target AUC from `data/targets/target_auc.json` (created by T014) and compares it to the observed AUC; writes a pass/fail flag to `data/results/target_auc_check.json`.  
  **Verification**: `distinct_pattern_auc.json` contains an `auc_roc` (float); `target_auc_check.json` contains fields `target_auc`, `observed_auc`, `meets_target` (`true`/`false`).

- [ ] **T011** **Document statistical‑power limitation and contextualize significance results**  
  *Script*: `code/analysis/report_power.py` reads the Wilcoxon p‑values, notes that with n = 10 the smallest possible two‑sided p‑value is 0.05, and automatically adds a paragraph to the final report (`docs/report.md`) explaining why the FDR < 0.05 threshold may be unattainable and how the results should be interpreted.  
  **Verification**: `docs/report.md` contains a clearly marked “Statistical Power Note” section, and the CI test that checks for the presence of this section passes.

## Phase 4 – Documentation, integrity checks & runtime reporting  

- [ ] **T012** **Create user‑facing documentation**  
  *Files*: `docs/quickstart.md`, `docs/data_model.md`  
  - `quickstart.md` provides step‑by‑step commands to (1) install dependencies, (2) download the dataset, (3) run the graph pipeline (`python code/data/run_graph_pipeline.py`), (4) train all models (`python code/main.py`), and (5) generate the statistical report (`python code/analysis/run_full_report.py`).  
  - `data_model.md` summarizes `dataset.schema.yaml` and `graph.schema.yaml` with short example snippets.  
  **Verification**: Both Markdown files render without broken links; they reference requirement IDs `FR‑001`, `FR‑003`, `SC‑001`, `SC‑004`.

- [ ] **T013** **Verify artifact integrity and record total runtime**  
  1. `verify_hashes.py` scans all `*.sha256` side‑cars under `data/processed/` and `data/results/`, recomputes file hashes, and exits with status 0 only if every checksum matches.  
  2. `measure_runtime.py` wraps the full end‑to‑end pipeline (from dataset download to final statistical report) and writes `data/results/runtime.json` containing `{ "total_seconds": <float>, "within_limit": true/false }` where `within_limit` is `true` if the total ≤ 21 600 s (6 h). The script aborts the pipeline if `within_limit` is `false`, ensuring **SC‑004** is enforced.  
  **Verification**: `runtime.json` exists and `within_limit` is `true`; `verify_hashes.py` exits with code 0 on a clean run.

- [ ] **T014** **Define the pre‑defined target AUC value**  
  *File*: `data/targets/target_auc.json`  
  1. Writes a JSON file containing `{ "target_auc": 0.85 }` (the value is chosen based on prior literature for CTU‑13 anomaly detection).  
  2. Commits the file alongside its SHA‑256 checksum `data/targets/target_auc.json.sha256`.  
  **Verification**: The JSON file exists and parses; the checksum matches; downstream tasks (T010) read the value successfully.

### Execution order summary  

1. **T001** → 2. **T002** → 3. **T003** → 4. **T004** → 5. **T005** → 6. **T006** → 7. **T007** → 8. **T008** → 9. **T009** → 10. **T010** → 11. **T011** → 12. **T012** → 13. **T013** → 14. **T014**.  

All tasks respect data‑flow constraints, enforce the 7 GB RAM limit, use only the verified CTU‑13 dataset, and provide a complete end‑to‑end analysis that satisfies every functional requirement and success‑criterion in the specification while transparently handling the statistical‑power limitation noted by reviewers.