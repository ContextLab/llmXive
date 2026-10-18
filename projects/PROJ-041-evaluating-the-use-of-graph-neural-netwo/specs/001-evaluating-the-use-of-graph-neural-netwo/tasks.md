# Tasks: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic  

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, JSON‑Schema contracts, and reviewer feedback.  
All paths are relative to the repository root.

---

## Phase 1 – Project bootstrap  

- [ ] T001 **Create project layout & core utilities**  
  *Creates* `code/`, `data/`, `docs/`, `tests/`, writes `requirements.txt` (pinning Python 3.11 and all scientific libraries), adds a minimal `pyproject.toml`, implements deterministic seed handling (`code/utils/seed.py`) and a RAM‑limit wrapper (`code/utils/memory_monitor.py`).  
  **Verification**: `tree` shows the directories; `pip install -r requirements.txt` succeeds; `seed.set_seed(42)` yields reproducible RNG state; `memory_monitor.run_with_limit` raises `MemoryLimitError` when a dummy allocation exceeds 7 GB; a sample JSON validates against `contracts/*.schema.yaml` without error.

---

## Phase 2 – Data acquisition & preprocessing  

- [ ] T002 **Download CTU‑13 Scenario 1 NetFlow CSV (real, verified URL)**   <!-- FAILED-IN-EXECUTION: code/data/download_ctu13.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_ctu13.py exit=1 -->
  *Script*: `code/data/download_ctu13.py`  
  1. Downloads `Scenario1/CTU-13-Dataset-1.csv` from the official repository  
     `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/CTU-AI-Lab/CTU-13-Dataset/master/Scenario1/CTU-13-Dataset-1.csv` — HTTP 404].  
  2. Saves to `data/raw/ctu13_scenario1.csv`.  
  3. Computes SHA‑256 checksum and writes `data/raw/ctu13_scenario1.csv.sha256`.  
  4. Updates `code/config.yaml` with `active_dataset: ctu13_scenario1`.  
  **Verification**: Script exits with status 0; file exists; checksum matches; any HTTP error raises `RuntimeError` (no silent fallback).

- [ ] T003 **Ingest NetFlow records, validate against `dataset.schema.yaml`, and write cleaned Parquet**  
  *Script*: `code/data/ingest_netflow.py`  
  1. Reads `data/raw/ctu13_scenario1.csv`, validates each row with `jsonschema` against `contracts/dataset.schema.yaml`.  
  2. Hashes IP addresses (SHA‑256) and writes `data/processed/raw_flows_scenario1.parquet`.  
  3. Writes checksum `data/processed/raw_flows_scenario1.parquet.sha256`.  
  **Verification**: Loading the Parquet with `pandas.read_parquet` succeeds; no schema violations; checksum matches.

- [ ] T004 **Build directed communication graph, enforce 7 GB RAM limit, and serialise**  
  *Script*: `code/data/build_graph.py`  
  1. Streams `raw_flows_scenario1.parquet`, creates a `networkx.DiGraph` where nodes are hashed IPs and edge attribute `weight` = packet count; timestamps preserved.  
  2. Wraps construction with `memory_monitor.run_with_limit(limit_gb=7)`.  
  3. **Verification**: After construction the script checks that `graph.number_of_nodes() ≤ 5_000`. If the limit is exceeded, a `MemoryLimitError` (or custom `GraphSizeError`) is raised before any further processing.  
  4. Saves compressed GraphML to `data/processed/graph_scenario1_raw.graphml.gz`.  
  5. Writes checksum `data/processed/graph_scenario1_raw.graphml.gz.sha256`.  
  **Verification**: Peak memory recorded ≤ 7 GB; graph loads via `nx.readwrite.graphml.read_graphml`; node count ≤ 5 000; checksum matches.

- [ ] T005 **Validate graph size and perform unbiased stratified subsampling to ≤5 000 nodes**  
  *Script*: `code/data/subsample_graph.py`  
  1. Loads `graph_scenario1_raw.graphml.gz`.  
  2. If node count ≤ 5 000, the graph is accepted unchanged as `graph_scenario1_final.graphml.gz`.  
  3. If node count > 5 000, performs **unbiased stratified random sampling**:  
     - Computes the proportion of anomalous nodes (`is_anomaly=True`) in the full graph.  
     - Samples nodes without replacement using a fixed seed (42) such that the sampled set preserves this anomaly proportion and totals ≤ 5 000 nodes.  
     - Constructs the induced subgraph and saves it as `graph_scenario1_subsampled.graphml.gz`.  
  4. Updates `code/config.yaml` with `final_graph_path` pointing to the accepted graph (raw or subsampled).  
  5. Writes checksums for all output graphs.  
  **Verification**: Final graph has ≤ 5 000 nodes, anomaly proportion matches that of the original graph within a tolerance of ±1 %; checksum files validate; `config.yaml` correctly references the chosen graph.

- [ ] T006 **Temporal hold‑out split & node‑level feature engineering**  
  *Script*: `code/data/split_and_features.py`  
  1. Sorts `raw_flows_scenario1.parquet` by `start_time`; splits 80 % earliest rows → `data/processed/train_flows.parquet`, 20 % latest → `data/processed/test_flows.parquet`.  
  2. Builds training and test graphs from the respective flow files using the same graph‑builder logic, producing `graph_scenario1_train.graphml.gz` and `graph_scenario1_test.graphml.gz`.  
  3. Computes structural features (degree, in/out degree, betweenness centrality, clustering coefficient, edge‑weight variance, temporal span) for every node; writes `data/processed/features_scenario1_train.parquet` and `features_scenario1_test.parquet`.  
  4. Adds a boolean `label` column derived **only from training‑set flows** (no leakage).  
  5. Writes SHA‑256 side‑cars for all new files.  
  **Verification**: Split files respect the 80/20 temporal split; both graphs ≤ 5 000 nodes; feature tables contain all required columns with correct dtypes; checksums validate.

---

## Phase 3 – Model training, evaluation & statistical analysis  

- [ ] T007 **Train GCN (CPU‑only) and baseline models across 20 random seeds**  
  *Modules*: `code/models/gcn.py`, `code/models/baselines.py`  
  For each seed in `[0,1,2,…,19]`:  
  1. `utils.seed.set_seed(seed)` ensures reproducibility.  
  2. Loads `features_scenario1_train.parquet`.  
  3. Trains a 2‑layer GCN (max 30 epochs, early stopping patience 5, `min_delta=1e‑4`) on the training graph; saves checkpoint `data/models/gcn_seed{seed}.pt`.  
  4. Trains `RandomForestClassifier` (200 trees) and `XGBClassifier` (max_depth 6, 200 estimators, `tree_method='hist'`) on the same feature table; saves `rf_seed{seed}.pkl` and `xgb_seed{seed}.pkl`.  
  **Verification**: All model files exist, can be deserialized, and training logs contain a line indicating early‑stopping or reaching epoch 30 without CUDA errors.

- [ ] T008 **Evaluate models on the held‑out test set and aggregate metrics**  
  *Script*: `code/evaluation/evaluate.py`  
  1. Loads each trained model and `features_scenario1_test.parquet`, generates predictions, computes Precision, Recall, F1‑Score, and AUC‑ROC (`sklearn.metrics`).  
  2. Writes per‑run JSON `data/results/metrics_{model}_seed{seed}.json`.  
  3. `aggregate_metrics.py` reads all JSONs for a given model, calculates mean ± std for each metric across the twenty seeds, and writes `data/results/aggregate_{model}.csv`.  
  4. Computes the delta AUC‑ROC between GCN and Random Forest (`delta_auc = gcn_mean_auc - rf_mean_auc`) and stores `data/results/auc_comparison.json`.  
  **Verification**: Every metrics JSON contains keys `precision`, `recall`, `f1_score`, `auc_roc` with values in `[0,1]`; aggregate CSVs contain `metric,mean,std`; `auc_comparison.json` includes numeric `delta_auc` and boolean `gcn_outperforms_rf`.

- [ ] T009 **Wilcoxon signed‑rank tests (20 seeds) & Benjamini‑Hochberg correction**  
  *Script*: `code/analysis/significance.py`  
  1. Extracts paired F1‑scores across the twenty seeds for the seven hypotheses defined in **FR‑006** (GCN vs RF, GCN vs XGB, and top‑5 structural features vs null baseline).  
  2. Runs `scipy.stats.wilcoxon` (two‑sided) for each hypothesis; stores raw p‑values in `data/results/pvalues_wilcoxon.json`.  
  3. Applies Benjamini‑Hochberg (BH) to the seven p‑values, producing adjusted q‑values in `data/results/bh_corrected.json`.  
  4. **Verification**: The script flags a hypothesis as `significant:true` **only** when the BH‑adjusted q‑value `< 0.05`. Raw p‑values are recorded but never used for significance decisions.  
  5. Adds a `statistical_power_limited` flag set to `false` (now sufficient seeds).  
  **Verification**: Both JSON files contain seven entries with numeric `p_value` / `q_value`; no `significant:true` entry appears unless `q_value < 0.05`.

- [ ] T010 **Model attribution & identification of distinct predictive patterns**  
  *Scripts*: `code/analysis/attribution.py`, `code/analysis/patterns.py`  
  1. **Integrated Gradients** – runs Captum’s `IntegratedGradients` on the best‑seed GCN checkpoint, producing per‑feature attribution scores; writes `data/results/gcn_attributions.json`.  
  2. **Random Forest importance** – averages `feature_importances_` across the twenty RF seeds; writes `data/results/rf_importances.json`.  
  3. **Pattern ranking** – compares GCN attributions to RF importances, bootstraps 1 000 resamples to obtain 95 % confidence intervals for the difference of each structural feature; writes `data/results/distinct_patterns.json` where each feature has `distinct: true/false`.  
  **Verification**: All three JSON files exist; `distinct_patterns.json` lists at least one feature with `distinct:true`.

- [ ] T015 **Define the pre‑defined target AUC value**  
  *File*: `data/targets/target_auc.json`  
  1. Writes `{ "target_auc": 0.85 }` (based on prior CTU‑13 literature).  
  2. Generates checksum `data/targets/target_auc.json.sha256`.  
  **Verification**: JSON parses; checksum matches; downstream tasks (T011) read the value successfully.

- [ ] T011 **Assess predictive power of the distinct patterns (logistic regression) vs. target AUC**  
  *Script*: `code/analysis/pattern_auc.py`  
  1. Constructs a reduced feature matrix containing only the `distinct:true` structural features identified in T010.  
  2. Trains a `LogisticRegression(max_iter=1000)` on the training split (seed 0) and evaluates AUC‑ROC on the test split; writes `data/results/distinct_pattern_auc.json`.  
  3. Reads the pre‑defined target AUC from `data/targets/target_auc.json` (produced by T015) and writes `data/results/target_auc_check.json` containing `target_auc`, `observed_auc`, and `meets_target` (`true`/`false`).  
  **Verification**: `distinct_pattern_auc.json` contains a numeric `auc_roc`; `target_auc_check.json` correctly reflects whether the observed AUC meets or exceeds the target.

- [ ] T012 **Document statistical‑power limitation and contextualize significance results**  
  *Script*: `code/analysis/report_power.py` reads `pvalues_wilcoxon.json` and the `statistical_power_limited` flag, then appends a clearly marked “Statistical Power Note” paragraph to `docs/report.md` explaining why the FDR < 0.05 threshold may be unattainable with fewer seeds and how the increased seed count resolves this.  
  **Verification**: `docs/report.md` contains the paragraph; CI test that searches for the heading “## Statistical Power Note” passes.

---

## Phase 4 – Documentation, integrity checks & runtime reporting  

- [ ] T013 **Create user‑facing documentation**  
  *Files*: `docs/quickstart.md`, `docs/data_model.md`  
  - `quickstart.md` lists step‑by‑step commands to (1) install dependencies, (2) download the dataset, (3) run the graph pipeline (`python code/data/run_graph_pipeline.py`), (4) train all models (`python code/main.py`), and (5) generate the full statistical report (`python code/analysis/run_full_report.py`).  
  - `data_model.md` summarises `dataset.schema.yaml` and `graph.schema.yaml` with short example snippets.  
  **Verification**: Both Markdown files render without broken links; they reference requirement IDs `FR‑001`, `FR‑003`, `SC‑001`, `SC‑004`.

- [ ] T014 **Verify artifact integrity and record total runtime**  
  *Scripts*: `code/utils/verify_hashes.py`, `code/utils/measure_runtime.py`  
  1. `verify_hashes.py` scans every `*.sha256` side‑car under `data/processed/` and `data/results/`, recomputes hashes, and exits with status 0 only if all match.  
  2. `measure_runtime.py` wraps the full end‑to‑end pipeline (from dataset download to final report) and writes `data/results/runtime.json` containing `{ "total_seconds": <float>, "within_limit": true/false }` where `within_limit` is `true` if total ≤ 21 600 s (6 h). The script aborts the pipeline if `within_limit` is `false`.  
  **Verification**: `runtime.json` exists and reports `within_limit: true`; `verify_hashes.py` exits with code 0 on a clean run.

- [ ] T016 **Write final methods & results report**  
  *File*: `docs/report.md` (updated by previous analysis tasks).  
  - Summarises dataset provenance, graph construction statistics, model performance tables, statistical test outcomes (including the power limitation note), attribution findings, and the target‑AUC check.  
  - Includes all generated figures (ROC curves, feature‑importance bar plots, attribution heatmaps) referenced from `figures/`.  
  **Verification**: Report contains sections for each FR/SC, all tables match the CSV/JSON artifacts, and the CI test that parses the report for required sections passes.

---

### Execution order summary  

1. **T001** → 2. **T002** → 3. **T003** → 4. **T004** → 5. **T005** → 6. **T006** → 7. **T007** → 8. **T008** → 9. **T009** → 10. **T010** → 11. **T015** → 12. **T011** → 13. **T012** → 14. **T013** → 15. **T014** → 16. **T016**.  

All tasks respect data‑flow constraints, enforce the 7 GB RAM limit, use only the verified CTU‑13 dataset, and produce a complete, reproducible end‑to‑end analysis that satisfies every functional requirement and success‑criterion in the specification while transparently handling the statistical‑power limitation highlighted by reviewers.  
