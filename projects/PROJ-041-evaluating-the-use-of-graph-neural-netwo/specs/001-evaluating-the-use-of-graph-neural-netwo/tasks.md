# Tasks: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic  

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, JSON‑Schema contracts, and any reviewer feedback.  
All paths are relative to the repository root.

---

## Phase 1 – Project bootstrap (already completed)

- [ ] T001 **Create project layout & basic utilities**  
  *Creates* `code/`, `data/`, `tests/`, `docs/` directories, adds placeholder `__init__.py` files, writes `requirements.txt` (pinned Python 3.11, `torch`‑CPU, `networkx`, `scikit‑learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `captum`, `pytest`, `pytest‑memprof`), configures `pyproject.toml` for `ruff` & `black`, implements deterministic seed handling (`code/utils/seed.py`), implements a RAM‑limit wrapper (`code/utils/memory_monitor.py`), and adds the canonical JSON‑Schema contracts (`contracts/dataset.schema.yaml`, `contracts/graph.schema.yaml`).  
  *Verification*: `tree` shows all directories; `pip install -r requirements.txt` succeeds; `seed.set_seed(42)` yields reproducible RNG state; `memory_monitor.run_with_limit` raises `MemoryLimitError` when a dummy allocation exceeds 7 GB; `jsonschema.validate` passes on sample files.

---

## Phase 2 – Data acquisition & preprocessing  

- [ ] T002 **Download and register the active NetFlow dataset**  
  *Action*:  
  1. Attempt to download **CTU‑13 Scenario 1** NetFlow CSV from `https://www.stratosphereips.org/datasets-ctu13/CTU-13-Dataset/Scenario1/Scenario1-1.csv` into `data/raw/ctu13_scenario1.csv`.  
  2. If the download fails, fall back to the verified **NF‑BoT‑IoT‑v3** Parquet dataset via `datasets.load_dataset("nfdatasets/bot_iot_v3", split="train")` and store as `data/raw/bot_iot_v3.parquet`.  
  3. Compute SHA‑256 checksums and write side‑car files (`*.sha256`).  
  4. Record the chosen dataset name in `code/config.yaml` under `active_dataset`.  
  *Verification*: The chosen file exists, its checksum matches the published value, and `config.yaml` contains `active_dataset: ctu13` or `bot_iot`.

- [ ] T003 **Ingest NetFlow records and build the raw directed graph (memory‑bounded)**  
  *Sub‑steps*:  
  1. **Ingestion** – `code/data/ingest_netflow.py` reads the active raw file (CSV or Parquet), validates each row against `contracts/dataset.schema.yaml` using `jsonschema`, hashes IP addresses with SHA‑256, and writes a cleaned Parquet file `data/processed/raw_flows.parquet` plus its checksum `raw_flows.parquet.sha256`.  
  2. **Graph construction** – `code/data/build_graph.py` loads `raw_flows.parquet`, creates a `networkx.DiGraph` where node IDs are the hashed IPs, edge attribute `weight` equals the packet count, and timestamps are preserved. The construction is wrapped by `memory_monitor.run_with_limit(limit_gb=7)`. On success the graph is serialized to compressed GraphML `data/processed/graph_raw.graphml.gz` with checksum `graph_raw.graphml.gz.sha256`.  
  *Verification*:  
  - The Parquet file can be read without schema violations.  
  - The GraphML file loads via `nx.readwrite.graphml.read_graphml` and reports `G.number_of_nodes() <= 10 000` (raw size).  
  - `data/results/memory_usage.json` records `"peak_memory_gb"` ≤ 7.0.  
  - Side‑car checksum files match the actual file hashes.

- [ ] T004 **Validate graph size and perform deterministic subsampling**  
  *Action*: `code/data/subsample_graph.py` reads `graph_raw.graphml.gz` and:  
  1. Extracts the **largest weakly connected component (LCC)** and writes it to `data/processed/graph_lcc.graphml.gz` (+ checksum).  
  2. If the LCC node count > 5 000, selects the top 5 000 nodes by degree (preserving all anomalous nodes) to create a deterministic induced subgraph `data/processed/graph_subsampled.graphml.gz` (+ checksum).  
  3. Updates `code/config.yaml` with `final_graph_path` pointing to the resulting graph (either LCC or subsampled).  
  *Verification*:  
  - `G = nx.readwrite.graphml.read_graphml(... )` reports `G.number_of_nodes() == 5 000` (or ≤ 5 000 if the original graph was already smaller).  
  - Both GraphML files exist and their `.sha256` files verify.  
  - `config.yaml` contains the correct `final_graph_path`.

- [ ] T005 **Temporal hold‑out split & feature engineering**  
  *Action*: `code/data/split_and_features.py` performs:  
  1. Loads `raw_flows.parquet`, sorts by `start_time`, splits 80 % earliest records to `data/processed/train_flows.parquet` and the remaining 20 % to `data/processed/test_flows.parquet` (both with checksums).  
  2. Builds **training** and **test** graphs *only* from their respective flow files using the same graph builder logic, producing `graph_train.graphml.gz` and `graph_test.graphml.gz`.  
  3. Computes node‑level structural features (degree, in/out degree, betweenness centrality, clustering coefficient, edge‑weight variance, temporal activity span) for each graph and writes Parquet feature tables `features_train.parquet` and `features_test.parquet` (with checksums).  
  *Verification*:  
  - Split files exist, contain the expected number of rows, and timestamps respect the 80/20 split.  
  - Both graph files load and have ≤ 5 000 nodes.  
  - Feature tables contain columns `node_id, degree, in_degree, out_degree, betweenness_centrality, clustering_coeff, edge_weight_variance, temporal_span, label`.  
  - All checksum side‑cars validate.

---

## Phase 3 – Model training, evaluation & statistical analysis  

- [ ] T006 **Define models & train across five random seeds**  
  *Sub‑tasks*:  
  1. **GCN** – `code/models/gcn.py` implements a 2‑layer Graph Convolutional Network (CPU‑only) using `torch` + `torch_geometric.nn.GCNConv` with early stopping (max 30 epochs, patience 5, `min_delta=1e‑4`).  
  2. **Baselines** – `code/models/baselines.py` wraps `sklearn.ensemble.RandomForestClassifier` and `xgboost.XGBClassifier` (CPU).  
  3. For each seed in `[0,1,2,3,4]`, set RNG via `utils.seed.set_seed`, load `features_train.parquet`, train the GCN (saving checkpoint `data/models/gcn_seed{seed}.pt`) and the two baselines (saving `rf_seed{seed}.pkl`, `xgb_seed{seed}.pkl`).  
  *Verification*: All five checkpoint/pickle files exist, can be deserialized, and training logs contain a line indicating early‑stopping or max‑epoch termination.

- [ ] T007 **Evaluate all models on the held‑out test set and aggregate results**  
  *Action*: `code/models/evaluate.py` loads each trained model, the test feature table, generates predictions, and computes **Precision, Recall, F1‑Score, AUC‑ROC** (using `sklearn.metrics`). For every `(model, seed)` combination it writes a JSON record `data/results/metrics_{model}_seed{seed}.json`.  
  *Aggregation*: `code/analysis/aggregate.py` reads the six JSON files per model, calculates mean ± std for each metric across seeds, and writes `data/results/aggregate_{model}.csv`.  
  *Verification*: Each JSON contains keys `precision`, `recall`, `f1_score`, `auc_roc` with values in `[0,1]`; the CSV has columns `metric,mean,std` for the four metrics.

- [ ] T008 **Statistical significance testing with multiple‑comparison correction**  
  *Action*: `code/analysis/significance.py` performs:  
  1. **Permutation tests** for the seven hypotheses (GCN vs RF, GCN vs XGB, and the top‑5 structural features vs. a null baseline). Uses 10 000 label permutations per hypothesis, computes the difference in mean F1‑score, and stores raw p‑values in `data/results/pvalues.json`.  
  2. **Benjamini‑Hochberg (BH) correction** on the seven p‑values, producing adjusted q‑values in `data/results/bh_corrected.json` and a summary flag `significant: true` for any hypothesis with `q < 0.05`.  
  *Verification*: `pvalues.json` holds seven entries with numeric p‑values; `bh_corrected.json` holds matching `q_value` fields and at least one entry where `significant` is `true`.

- [ ] T009 **Model attribution & pattern‑level analysis**  
  *Action*:  
  1. **Integrated Gradients** – `code/analysis/attribution.py` runs Captum’s `IntegratedGradients` on the trained GCN (using the best‑seed checkpoint) to obtain attribution scores for each structural feature; results are written to `data/results/gcn_attributions.json`.  
  2. **Random Forest feature importance** – `code/models/baselines.py` averages `feature_importances_` across the five RF seeds and writes `data/results/rf_importances.json`.  
  3. **Bootstrap ranking comparison** – `code/analysis/patterns.py` resamples test predictions 1 000 times, computes rank differences between GCN attribution and RF importance for each feature, derives 95 % confidence intervals, and writes `data/results/distinct_patterns.json` (features whose CI excludes zero are marked `distinct: true`).  
  *Verification*: All three JSON files exist; `distinct_patterns.json` contains at least one feature with `distinct: true`.

- [ ] T010 **Assess predictive power of distinct patterns and enforce target AUC**  
  *Action*:  
  1. Build a reduced feature matrix containing only the `distinct` structural features identified in T009. Train a simple Logistic Regression (CPU) on the training split (seed 0) and evaluate AUC‑ROC on the test split, writing `data/results/distinct_pattern_auc.json`.  
  2. Load `target_auc` from `code/config.yaml` (populated from `research.md`) and compare it to the observed AUC; write a pass/fail flag to `data/results/target_auc_check.json`.  
  *Verification*: `distinct_pattern_auc.json` contains `auc_roc` ≥ 0.0; `target_auc_check.json` contains fields `target_auc`, `observed_auc`, `meets_target` (`true` or `false`).

---

## Phase 4 – Documentation, integrity checks & runtime reporting  

- [ ] T011 **Create user‑facing documentation**  
  *Quick‑start* – `docs/quickstart.md` with step‑by‑step commands to (1) install dependencies, (2) download the dataset, (3) run the graph pipeline (`python code/data/run_graph_pipeline.py`), (4) train all models (`python code/main.py`), and (5) generate the statistical report (`python code/analysis/run_full_report.py`).  
  *Data‑model description* – `docs/data_model.md` summarising `dataset.schema.yaml` and `graph.schema.yaml` with short example snippets.  
  *Verification*: Both Markdown files render without broken links; they reference requirement IDs `FR‑001`, `FR‑003`, `SC‑001`, `SC‑004`.

- [ ] T012 **Verify artifact integrity and record total runtime**  
  *Hash verification* – `code/utils/verify_hashes.py` scans all `*.sha256` side‑cars under `data/processed/` and `data/results/`, recomputes file hashes, and exits with status 0 only if every checksum matches.  
  *Runtime measurement* – `code/utils/measure_runtime.py` wraps the full end‑to‑end pipeline (from dataset download to final statistical report) and writes `data/results/runtime.json` containing `{ "total_seconds": <float>, "within_limit": true/false }` where `within_limit` is `true` if the total ≤ 21 600 s (6 h).  
  *Verification*: `runtime.json` exists and `within_limit` is `true`; `verify_hashes.py` exits with code 0 on a clean run.

---  

### Execution order summary  

1. **T001** (bootstrap) → 2. **T002** (download) → 3. **T003** (ingest + raw graph) → 4. **T004** (validation + subsampling) → 5. **T005** (temporal split + features) → 6. **T006** (model definition + training) → 7. **T007** (evaluation + aggregation) → 8. **T008** (significance testing) → 9. **T009** (attribution + pattern analysis) → 10. **T010** (distinct‑pattern AUC + target check) → 11. **T011** (documentation) → 12. **T012** (hash verification + runtime).  

All tasks respect the data‑flow constraints, enforce the 7 GB RAM limit, use only real CTU‑13 (or verified fallback) data, and produce concrete, verifiable artifacts required by the specification.
