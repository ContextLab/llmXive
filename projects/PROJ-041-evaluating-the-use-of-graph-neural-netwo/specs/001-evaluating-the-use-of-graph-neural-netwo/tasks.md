# Tasks: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic  

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, JSON‑Schema contracts, and reviewer feedback.  
All paths are relative to the repository root.

---

## Phase 1 – Project bootstrap  

- [X] **T001** **Create project layout & core utilities**  
  *Creates* the top‑level directories `code/`, `data/`, `docs/`, `tests/`, adds minimal `__init__.py` files, writes `requirements.txt` (pinning Python 3.11, `torch`‑CPU, `torch‑geometric`, `networkx`, `scikit‑learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `captum`, `pytest`, `pytest‑memprof`), adds `pyproject.toml` for `ruff`/`black`, implements deterministic seed handling (`code/utils/seed.py`) and a RAM‑limit wrapper (`code/utils/memory_monitor.py`).  
  **Verification**: `tree` shows the directories; `pip install -r requirements.txt` succeeds; `seed.set_seed(42)` yields reproducible RNG state; `memory_monitor.run_with_limit` raises `MemoryLimitError` when a dummy allocation exceeds 7 GB; `jsonschema.validate` passes on sample files.

---

## Phase 2 – Data acquisition & preprocessing  

- [ ] **T002** **Download and register the CTU‑13 NetFlow dataset (mandatory)**   <!-- FAILED-IN-EXECUTION: code/data/download_ctu13.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_ctu13.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_ctu13.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_ctu13.py exit=1 -->
  1. Download **CTU‑13 Scenario 1** NetFlow CSV from  
     `[UNRESOLVED-CLAIM: https://www.stratosphereips.org/datasets-ctu13/CTU-13-Dataset/Scenario1/Scenario1-1.csv` — HTTP 404] into `data/raw/ctu13_scenario1.csv`.  
  2. **No fallback**: if the download fails, the task aborts with a clear error message and the pipeline stops (ensuring FR‑001 is not weakened).  
  3. Compute SHA‑256 checksum and write side‑car file `ctu13_scenario1.csv.sha256`.  
  4. Record the dataset name in `code/config.yaml` under `active_dataset: ctu13`.  
  **Verification**: The CSV file exists, its checksum matches the published value, and `config.yaml` contains `active_dataset: ctu13`; failure to download raises an exception that halts execution.

- [ ] **T003** **Ingest NetFlow records, produce cleaned Parquet, and build the raw directed graph**  
  *Sub‑steps* (all scripts placed under `code/data/`):  
  1. **Ingestion** – `ingest_netflow.py` reads the active raw file (CSV), validates each row against `contracts/dataset.schema.yaml` using `jsonschema`, hashes IP addresses with SHA‑256, and writes a cleaned Parquet file `data/processed/raw_flows_{scenario}.parquet` plus its checksum `raw_flows_{scenario}.parquet.sha256`.  
  2. **Raw graph construction** – `build_graph.py` loads `raw_flows_{scenario}.parquet`, creates a `networkx.DiGraph` where node IDs are the hashed IPs, edge attribute `weight` equals the packet count, and timestamps are preserved. The construction is wrapped by `memory_monitor.run_with_limit(limit_gb=7)`. On success the graph is serialized to compressed GraphML `data/processed/graph_{scenario}_raw.graphml.gz` with checksum `graph_{scenario}_raw.graphml.gz.sha256`.  
  **Verification**:  
  - `raw_flows_{scenario}.parquet` can be read without schema violations.  
  - `graph_{scenario}_raw.graphml.gz` loads via `nx.readwrite.graphml.read_graphml` and reports `G.number_of_nodes() <= 10 000`.  
  - `data/results/memory_usage.json` records `"peak_memory_gb" ≤ 7.0`.  
  - All checksum side‑cars validate.

- [ ] **T004** **Validate graph size, extract the Largest Weakly Connected Component (LCC), and perform deterministic subsampling**  
  *Script*: `subsample_graph.py` reads `graph_{scenario}_raw.graphml.gz` and:  
  1. Extracts the **largest weakly connected component** and writes it to `data/processed/graph_{scenario}_lcc.graphml.gz` (+ checksum).  
  2. If the LCC node count > 5 000, selects the top 5 000 nodes by degree **while preserving every anomalous node** (identified from `label` aggregation) to create a deterministic induced subgraph `data/processed/graph_{scenario}_subsampled.graphml.gz` (+ checksum).  
  3. Updates `code/config.yaml` with `final_graph_path` pointing to the LCC graph if size ≤ 5 000, otherwise to the subsampled graph.  
  **Verification**:  
  - `graph_{scenario}_lcc.graphml.gz` loads and its node count equals the LCC size.  
  - `graph_{scenario}_subsampled.graphml.gz` (when created) has exactly 5 000 nodes and includes all nodes with `is_anomaly = True`.  
  - All checksum files match.  
  - `config.yaml` correctly references the chosen final graph.

- [ ] **T005** **Temporal hold‑out split & node‑level feature engineering**  
  *Script*: `split_and_features.py` performs:  
  1. Loads `raw_flows_{scenario}.parquet`, sorts by `start_time`, and splits 80 % earliest records to `data/processed/train_flows.parquet` and the remaining 20 % to `data/processed/test_flows.parquet` (both with checksums).  
  2. Builds **training** and **test** graphs *only* from their respective flow files using the same graph‑builder logic, producing `graph_{scenario}_train.graphml.gz` and `graph_{scenario}_test.graphml.gz`.  
  3. Computes node‑level structural features (degree, in/out degree, betweenness centrality, clustering coefficient, edge‑weight variance, temporal activity span) for each graph and writes Parquet feature tables `features_{scenario}_train.parquet` and `features_{scenario}_test.parquet` (with checksums). Each table contains columns `node_id, degree, in_degree, out_degree, betweenness_centrality, clustering_coeff, edge_weight_variance, temporal_span, label`.  
  **Verification**:  
  - Split files exist, contain the expected row counts, and timestamps respect the 80/20 split.  
  - Both graph files load and have ≤ 5 000 nodes.  
  - Feature tables contain all required columns and pass a schema sanity check (`pandas.api.types.is_numeric_dtype` for numeric fields, boolean for `label`).  
  - All checksum side‑cars validate.

---

## Phase 3 – Model training, evaluation & statistical analysis  

- [ ] **T006** **Define models & train across five random seeds**  
  *Modules*: `code/models/gcn.py` (2‑layer GCN, CPU‑only, early stopping: max 30 epochs, patience 5, `min_delta=1e‑4`), `code/models/baselines.py` (wrappers for `RandomForestClassifier` and `XGBClassifier`).  
  For each seed in `[0,1,2,3,4]`:  
  1. Set RNG via `utils.seed.set_seed`.  
  2. Load `features_{scenario}_train.parquet`.  
  3. Train the GCN (saving checkpoint `data/models/gcn_seed{seed}.pt`) and the two baselines (saving `rf_seed{seed}.pkl`, `xgb_seed{seed}.pkl`).  
  **Verification**: All six model files exist, can be deserialized, and training logs contain a line indicating early‑stopping or max‑epoch termination.

- [ ] **T007** **Evaluate all models on the held‑out test set, aggregate results, and perform explicit GCN vs. RF AUC‑ROC comparison**  
  *Script*: `evaluate.py` loads each trained model, the test feature table, generates predictions, and computes **Precision, Recall, F1‑Score, AUC‑ROC** (using `sklearn.metrics`). For every `(model, seed)` combination it writes a JSON record `data/results/metrics_{model}_seed{seed}.json`.  
  *Aggregation*: `aggregate.py` reads the six JSON files per model, calculates mean ± std for each metric across seeds, and writes `data/results/aggregate_{model}.csv`.  
  *Comparative assessment*: After aggregation, a new step computes the delta AUC‑ROC between GCN and Random Forest (`delta_auc = gcn_mean_auc - rf_mean_auc`). It writes `data/results/auc_comparison.json` containing `{ "gcn_mean_auc": ..., "rf_mean_auc": ..., "delta_auc": ..., "gcn_outperforms_rf": <true if delta_auc > 0 else false> }`. This satisfies SC‑002 by providing a clear pass/fail indicator of added predictive value.  
  **Verification**:  
  - Each metrics JSON contains keys `precision`, `recall`, `f1_score`, `auc_roc` with values in `[0,1]`.  
  - Each aggregate CSV has columns `metric,mean,std` for the four metrics.  
  - `auc_comparison.json` exists, `delta_auc` is numeric, and `gcn_outperforms_rf` is a boolean reflecting whether GCN’s AUC‑ROC exceeds the RF baseline.

- [ ] **T008** **Statistical significance testing (Wilcoxon + supplemental permutation) and multiple‑comparison correction**  
  *Script*: `significance.py` performs the following for the seven hypotheses defined in **FR‑006** (GCN vs RF, GCN vs XGB, and the top‑5 structural features vs. a null baseline):  
  1. **Wilcoxon signed‑rank test** on the paired F1‑scores across the five seeds (`scipy.stats.wilcoxon`). Stores raw two‑sided p‑values in `data/results/pvalues_wilcoxon.json`.  
  2. **Permutation test** (10 000 label permutations) as a robustness check; results saved in `data/results/pvalues_permutation.json`.  
  3. **Benjamini‑Hochberg (BH) correction** applied to the seven Wilcoxon p‑values, producing adjusted q‑values in `data/results/bh_corrected.json` and a summary flag `significant: true` for any hypothesis with `q < 0.05`.  
  **Verification**: Both JSON files contain seven entries with numeric p‑values; `bh_corrected.json` contains matching `q_value` fields and at least one entry where `significant` is `true`.

- [ ] **T009** **Model attribution & pattern‑level analysis**  
  1. **Integrated Gradients** – `attribution.py` runs Captum’s `IntegratedGradients` on the best‑seed GCN checkpoint, yielding attribution scores per structural feature; writes `data/results/gcn_attributions.json`.  
  2. **Random Forest feature importance** – averaged `feature_importances_` across the five RF seeds; writes `data/results/rf_importances.json`.  
  3. **Bootstrap ranking comparison** – `patterns.py` resamples test predictions 1 000 times, computes rank differences between GCN attribution and RF importance for each feature, derives 95 % confidence intervals, and writes `data/results/distinct_patterns.json` (features whose CI excludes zero are marked `distinct: true`).  
  **Verification**: All three JSON files exist; `distinct_patterns.json` lists at least one feature with `distinct: true`.

- [ ] **T010** **Assess predictive power of distinct patterns and enforce target AUC**  
  1. Build a reduced feature matrix containing only the `distinct` structural features identified in T009.  
  2. Train a Logistic Regression (CPU) on the training split (seed 0) and evaluate AUC‑ROC on the test split; write `data/results/distinct_pattern_auc.json`.  
  3. Load `target_auc` from `code/config.yaml` (populated from the research plan) and compare it to the observed AUC; write a pass/fail flag to `data/results/target_auc_check.json`.  
  **Verification**: `distinct_pattern_auc.json` contains `auc_roc` (float); `target_auc_check.json` contains fields `target_auc`, `observed_auc`, `meets_target` (`true`/`false`).

---

## Phase 4 – Documentation, integrity checks & runtime reporting  

- [ ] **T011** **Create user‑facing documentation**  
  *Quick‑start* – `docs/quickstart.md` with step‑by‑step commands to (1) install dependencies, (2) download the dataset, (3) run the graph pipeline (`python code/data/run_graph_pipeline.py`), (4) train all models (`python code/main.py`), and (5) generate the statistical report (`python code/analysis/run_full_report.py`).  
  *Data‑model description* – `docs/data_model.md` summarising `dataset.schema.yaml` and `graph.schema.yaml` with short example snippets.  
  **Verification**: Both Markdown files render without broken links; they reference requirement IDs `FR‑001`, `FR‑003`, `SC‑001`, `SC‑004`.

- [ ] **T012** **Verify artifact integrity and record total runtime**  
  1. **Hash verification** – `verify_hashes.py` scans all `*.sha256` side‑cars under `data/processed/` and `data/results/`, recomputes file hashes, and exits with status 0 only if every checksum matches.  
  2. **Runtime measurement** – `measure_runtime.py` wraps the full end‑to‑end pipeline (from dataset download to final statistical report) and writes `data/results/runtime.json` containing `{ "total_seconds": <float>, "within_limit": true/false }` where `within_limit` is `true` if the total ≤ 21 600 s (6 h). The script aborts the pipeline if `within_limit` is `false`, ensuring SC‑004 is enforced.  
  **Verification**: `runtime.json` exists and `within_limit` is `true`; `verify_hashes.py` exits with code 0 on a clean run.

---

### Execution order summary  

1. **T001** → 2. **T002** → 3. **T003** → 4. **T004** → 5. **T005** → 6. **T006** → 7. **T007** → 8. **T008** → 9. **T009** → 10. **T010** → 11. **T011** → 12. **T012**.  

All tasks respect data‑flow constraints, enforce the 7 GB RAM limit, use only the mandatory CTU‑13 dataset, and now include explicit comparative evaluation and statistical testing that fully satisfy the specification’s functional and success‑criterion requirements.  