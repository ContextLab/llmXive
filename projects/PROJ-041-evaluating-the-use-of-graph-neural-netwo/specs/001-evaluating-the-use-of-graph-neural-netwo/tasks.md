# Tasks: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

**Input**: `spec.md`, `plan.md`, `data-model.md`, contracts, and any reviewer feedback.  
All paths are relative to the repository root.

---

## Phase 1 – Project Setup (already completed)

- [ ] T001 Create the standard project layout (`code/`, `data/`, `tests/`, `docs/`) and add placeholder `__init__.py` files.  
  *Verification*: `tree` shows all directories; `git status` reports no missing folders.

- [ ] T002 Initialise `requirements.txt` with pinned versions of Python 3.11, `torch` (CPU), `networkx`, `scikit‑learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `captum`, `pytest`, `pytest‑memprof`.  
  *Verification*: `pip install -r requirements.txt` succeeds without warnings.

- [ ] T003 Configure linting (`ruff`) and formatting (`black`) via `pyproject.toml`.  
  *Verification*: `ruff check .` and `black --check .` both return exit‑code 0.

---

## Phase 2 – Foundational Infrastructure (already completed)

- [ ] T004 Implement deterministic seed handling in `code/utils/seed.py`.  
  *Verification*: `seed.set_seed(42)` produces reproducible NumPy and PyTorch RNG states.

- [ ] T005 Implement `code/utils/memory_monitor.py` that wraps a callable, records peak RAM with `tracemalloc`, and raises `MemoryLimitError` if > 7 GB.  
  *Verification*: Unit test in `tests/test_memory_limits.py` triggers the error when a dummy allocation exceeds the limit.

- [ ] T006 Add the canonical JSON‑Schema contracts `contracts/dataset.schema.yaml` and `contracts/graph.schema.yaml`.  
  *Verification*: `jsonschema.validate` against sample files passes.

- [ ] T007e_gen Generate `research.md` with a placeholder `target_auc` and temporal‑holdout split ratios.  
  *Verification*: File exists and contains the required sections.

- [ ] T007e_cfg Write `code/config.yaml` containing `target_auc: 0.75` (read from `research.md`).  
  *Verification*: `yaml.safe_load` returns a dict with the key `target_auc`.

- [ ] T007d Validate that `research.md` and `code/config.yaml` are present and consistent; abort if missing.  
  *Verification*: Script exits with status 0 when both files are correct; otherwise raises `ConfigurationError`.

---

## Phase 3 – Dataset Acquisition (re‑planned, previously failing)

- [ ] T007a_download_ctu13 **Download CTU‑13 Scenario 1 NetFlow CSV**  
  *Action*: Use `urllib.request` to fetch `[UNRESOLVED-CLAIM: https://www.stratosphereips.org/datasets-ctu13/CTU-13-Dataset/Scenario1/Scenario1-1.csv` — HTTP 404].  
  *Verification*: After download the script computes the SHA‑256 checksum of the file and stores it in `data/raw/ctu13_scenario1.csv.sha256`; the checksum is then compared against the published value (to be filled in after first successful download). If the download fails or checksum mismatches, raise a clear `DatasetDownloadError`.

- [ ] T007b_download_bot_iot **Download NF‑BoT‑IoT‑v3 Parquet dataset** *(optional, requires spec amendment)*  
  *Action*: Use `datasets.load_dataset("nfdatasets/bot_iot_v3", split="train", streaming=False)` (or direct URL `https://huggingface.co/datasets/nfdatasets/bot_iot_v3/resolve/main/bot_iot_v3.parquet`).  
  *Verification*: After download compute the SHA‑256 checksum, store it in `data/raw/bot_iot_v3.parquet.sha256`, and compare to the official checksum. On failure raise `DatasetDownloadError`. Use of this dataset without a formal spec amendment will abort the pipeline.

- [ ] T007c_select_dataset **Select active dataset**  
  *Action*: If `data/raw/ctu13_scenario1.csv` exists and passes checksum → set `ACTIVE_DATASET=ctu13`; else if `data/raw/bot_iot_v3.parquet` is valid → set `ACTIVE_DATASET=bot_iot`. Write the chosen name into `code/config.yaml` under `active_dataset`.  
  *Verification*: `config.yaml` contains the key `active_dataset` with value `ctu13` or `bot_iot`.

---

## Phase 4 – User Story 1: Construct & Validate Network Traffic Graphs (P1)

### 4.1 Interface Definitions

- [ ] T010_define_ingest_interface **Define ingestion API** in `code/data/ingest_netflow.py`  
  ```python
  def ingest_netflow(input_path: str) -> pd.DataFrame:
      """Read a NetFlow CSV or Parquet, validate against dataset.schema.yaml,
      and return a DataFrame with columns {src_ip, dst_ip, packets, start_time, label}."""
  ```  
  *Verification*: `inspect.getsource` contains the docstring and type hints; unit test imports the function and checks its signature.

- [ ] T012_define_graph_builder_interface **Define graph‑builder API** in `code/data/preprocess.py`  
  ```python
  def build_graph(flows_path: str) -> nx.DiGraph:
      """Construct a directed graph from a parquet of flows, hash IPs,
      assign edge weight = packet count, and return a NetworkX DiGraph."""
  ```  
  *Verification*: Presence of function with correct signature; `pytest` test imports and asserts `callable(build_graph)`.

### 4.2 Implementation Steps

- [ ] T011_implement_ingest **Implement NetFlow ingestion**  
  *Action*: Read the file indicated by `ACTIVE_DATASET` (CSV for CTU‑13, Parquet for Bot‑IoT), enforce schema via `jsonschema`, hash IP addresses with SHA‑256, write the processed DataFrame to `data/processed/raw_flows_{scenario}.parquet`. Also write a side‑car hash file `raw_flows_{scenario}.parquet.sha256`.  
  *Verification*: The parquet file exists, can be read without error, and its SHA‑256 matches the side‑car.

- [ ] T013_implement_graph_builder **Build raw directed graph**  
  *Action*: Load `raw_flows_{scenario}.parquet`, create a `networkx.DiGraph` where each node ID is the hashed IP, each edge carries `weight=packets` and timestamps. Serialize to compressed GraphML `data/processed/graph_{scenario}_raw.graphml.gz` and generate a `.sha256` side‑car.  
  *Verification*: `nx.readwrite.graphml.read_graphml` loads the file; node count ≤ 10 000 for the raw graph; side‑car hash matches.

- [ ] T014_memory_guard **Enforce 7 GB RAM limit during graph construction**  
  *Action*: Wrap the body of `build_graph` with `memory_monitor.run_with_limit(limit_gb=7)`. On breach, raise `MemoryLimitError` with a user‑friendly message.  
  *Verification*: Unit test artificially inflates memory usage and confirms the exception is raised.

- [ ] **T014a_log_memory_usage** **Record peak memory usage**  
  *Action*: `memory_monitor.run_with_limit` returns the peak RAM usage; write a JSON file `data/results/memory_usage.json` containing `{ "peak_memory_gb": <float> }`.  
  *Verification*: The JSON file exists and the value is ≤ 7.0; the file is read by the verification script to confirm compliance with SC‑001.

- [ ] T015_largest_connected_component **Extract Largest Weakly Connected Component (LCC)**  
  *Action*: Load `graph_{scenario}_raw.graphml.gz`, compute the LCC using `nx.algorithms.components.weakly_connected_components`, write to `data/processed/graph_{scenario}_lcc.graphml.gz` plus hash file.  
  *Verification*: Node count of LCC ≤ original node count; file exists and hash matches.

- [ ] T016_degree_based_subsampling **Degree‑based fallback subsampling**  
  *Precondition*: LCC node count > 5 000.  
  *Action*: Sort nodes by degree descending, keep top 5 000, induce subgraph, write to `data/processed/graph_{scenario}_subsampled.graphml.gz` with hash.  
  *Verification*: Resulting graph reports `G.number_of_nodes() == 5000`; hash side‑car present.

- [ ] T017_orchestrate_subsampling **Conditional subsampling orchestrator**  
  *Action*: After `build_graph` finishes, check `G.number_of_nodes()`.  
  - If ≤ 5 000 → copy raw graph to `*_subsampled.graphml.gz`.  
  - Else run `T015_largest_connected_component`; if LCC ≤ 5 000 → use LCC; otherwise invoke `T016_degree_based_subsampling`.  
  All paths are logged; final graph path stored in `code/config.yaml` as `final_graph_path`.  
  *Verification*: End‑to‑end script `code/data/run_graph_pipeline.py` exits with status 0 and the config entry points to an existing file whose node count ≤ 5 000 and whose hash matches the side‑car.

---

## Phase 5 – User Story 2: Compare GNN vs. Feature‑Engineered Baselines (P2)

- [ ] T018_define_temporal_split **Temporal hold‑out split** (`code/data/splits.py`)  
  *Action*: Load `raw_flows_{scenario}.parquet`, sort by `start_time`, split 80 % earliest timestamps → `train_split.parquet`, remaining 20 % → `test_split.parquet`. Construct the training graph **only** from `train_split.parquet` (using the same builder as T013) and store as `graph_{scenario}_train.graphml.gz`.  
  *Verification*: Scripts assert `set(test_nodes) - set(train_nodes) == {}` and write both split files plus hashes. Additionally, the task now calls `extract_features` for both splits (see T018a/b) and records the resulting feature CSVs.

- [ ] **T018a_extract_train_features** **Extract structural features for training graph** (`code/analysis/feature_engineering.py`)  
  *Action*: Load `graph_{scenario}_train.graphml.gz`, compute degree, betweenness, clustering, edge‑weight variance, temporal span per node, and write `data/processed/features_{scenario}_train.parquet`.  
  *Verification*: Parquet file exists, can be read, and contains the expected columns.

- [ ] **T018b_extract_test_features** **Extract structural features for test graph** (`code/analysis/feature_engineering.py`)  
  *Action*: Load the test graph derived from `test_split.parquet` (built similarly to training) and write `data/processed/features_{scenario}_test.parquet`.  
  *Verification*: Parquet file exists and matches schema.

- [ ] T019_define_gcn_interface **GCN model definition** (`code/models/gcn.py`)  
  *Action*: Implement a 2‑layer Graph Convolutional Network using `torch.nn` with `torch_geometric.nn.GCNConv` (CPU only). Include early‑stopping logic (max 30 epochs, patience 5, `min_delta=1e-4`). Provide a `train()` method that accepts a seed and returns the best checkpoint path.  
  *Verification*: Unit test constructs the model, runs a single epoch on a tiny synthetic graph, and checks that parameters are on `cpu`.

- [ ] T020_train_gcn **Train GCN for 5 random seeds**  
  *Action*: For each seed in `[0,1,2,3,4]`, set RNG, load `graph_{scenario}_train.graphml.gz`, generate node feature matrix (structural features from `features_{scenario}_train.parquet`), train with early stopping, save checkpoint to `data/models/gcn_{seed}.pt`. Log final epoch, validation loss, and early‑stop trigger.  
  *Verification*: All five checkpoint files exist; each checkpoint can be loaded without error; training logs contain `EarlyStopping triggered` or `Reached max epochs`.

- [ ] **T020c_extract_train_features** *(alias for T018a – kept for backward compatibility)* – *No additional action.*

- [ ] T021_train_baselines **Train Random Forest & XGBoost for 5 seeds**  
  *Action*: Load `data/processed/features_{scenario}_train.parquet`, fit `sklearn.ensemble.RandomForestClassifier` and `xgboost.XGBClassifier` (CPU). Save models to `data/models/rf_{seed}.pkl` and `data/models/xgb_{seed}.pkl`.  
  *Verification*: Pickle files load successfully; `model.feature_importances_` is non‑empty.

- [ ] T022_evaluate_models **Compute evaluation metrics on test split** (`code/models/metrics.py`)  
  *Action*: For each seed and each model, load `features_{scenario}_test.parquet`, generate predictions, compute Precision, Recall, F1‑Score, AUC‑ROC using `sklearn.metrics`. Write a JSON record to `data/results/metrics_{scenario}_{model}_{seed}.json`.  
  *Verification*: JSON file contains keys `precision`, `recall`, `f1_score`, `auc_roc`; values are floats in `[0,1]`.

- [ ] T023_aggregate_metrics **Aggregate per‑model statistics**  
  *Action*: Read all metric JSONs for a given model, compute mean ± std for each metric across seeds, write CSV `data/results/aggregate_{model}.csv`.  
  *Verification*: CSV has header `metric,mean,std` and four rows (precision, recall, f1_score, auc_roc).

- [ ] **T025a_wilcoxon_test** **Wilcoxon signed‑rank test on F1‑scores** (`code/analysis/significance_tests.py`)  
  *Action*: Using the five seed‑wise F1‑scores for GCN vs. RF and GCN vs. XGB, perform Wilcoxon signed‑rank tests (two‑tailed). Store p‑values in `data/results/wilcoxon_pvalues.json`.  
  *Verification*: JSON contains entries `gcn_vs_rf` and `gcn_vs_xgb` with numeric p‑values.

- [ ] T025_permutation_tests **Run permutation tests for every hypothesis** (`code/analysis/significance_tests.py`)  
  *Action*: For each of the seven hypotheses (including top‑5 structural features vs. null), perform 10 000 label permutations, compute the test statistic (difference in mean F1‑score), derive a two‑sided p‑value. Store results in `data/results/pvalues.json`.  
  *Verification*: JSON contains 7 entries; each p‑value is a float in `(0,1)`.

- [ ] T026_bh_correction **Apply Benjamini‑Hochberg correction** (`code/analysis/significance_tests.py`)  
  *Action*: Load `pvalues.json`, sort, compute adjusted q‑values, write `data/results/bh_corrected.json`. Also write a summary flag `significant: true` for any hypothesis with `q < 0.05`.  
  *Verification*: All 7 entries have both `p_value` and `q_value`; at least one entry has `significant: true`.

- [ ] T027_gnn_attribution **Integrated Gradients for GCN** (`code/analysis/attribution.py`)  
  *Action*: Using `captum.attr.IntegratedGradients`, compute attribution scores for each node feature, map scores back to the structural proxy names, write `data/results/gnn_attribution_{scenario}.json`.  
  *Verification*: JSON contains a mapping `{feature_name: attribution_score}`; scores sum to ~1.0 after normalization.

- [ ] T028_rf_feature_importance **Extract Random Forest feature importances** (`code/models/baselines.py`)  
  *Action*: Load each RF model, average importances across seeds, write `data/results/rf_importances.json`.  
  *Verification*: JSON lists the same 5 structural features with non‑negative importance values that sum to 1 after normalization.

- [ ] T029_compare_rankings **Bootstrap confidence intervals & identify distinct patterns** (`code/analysis/patterns.py`)  
  *Action*: Resample test predictions 1 000 times, compute rank of each feature in GNN attribution vs. RF importance, derive 95 % confidence intervals for rank differences. A pattern is “distinct” if the interval excludes 0. Write `data/results/distinct_patterns.json` listing those patterns.  
  *Verification*: Output contains a list; each entry has `feature`, `rank_diff_ci_low`, `rank_diff_ci_high`, and a boolean `distinct`.

- [ ] T030_distinct_pattern_auc **Evaluate predictive power of distinct patterns** (`code/models/evaluation.py`)  
  *Action*: Build a reduced feature matrix containing only the distinct patterns, train a simple Logistic Regression (CPU) on the training split, evaluate AUC‑ROC on the test split, write `data/results/distinct_pattern_auc.json`.  
  *Verification*: JSON contains key `auc_roc` with a float; value ≥ 0.0.

- [ ] T031_enforce_target_auc **Check against target AUC from research.md** (`code/config.yaml` holds `target_auc`)  
  *Action*: Load `target_auc`, compare with `distinct_pattern_auc`. Write a pass/fail flag to `data/results/threshold_enforcement.json`.  
  *Verification*: JSON contains `target_auc`, `observed_auc`, `meets_target: true/false`.

---

## Phase 6 – Documentation, Verification & State Management

- [ ] T032_write_quickstart **Create `docs/quickstart.md`**  
  *Content*: Step‑by‑step commands to (1) install deps, (2) download dataset, (3) run `python code/data/run_graph_pipeline.py`, (4) train models via `python code/main.py`, (5) generate significance report.  
  *Verification*: Markdown renders without broken links; all commands are present; file includes references to requirement IDs `FR-001`, `FR-003`, `SC-001`, `SC-004`.

- [ ] T033_write_data_model_doc **Create `docs/data_model.md`** summarising `dataset.schema.yaml` and `graph.schema.yaml` with example snippets.  
  *Verification*: File exists; schema sections are correctly quoted and the file contains the exact snippets from both schema files.

- [ ] T034_verify_hashes **Run hash verification script** (`code/utils/verify_hashes.py`)  
  *Action*: Scan `data/processed/**/*.sha256`, recompute hashes, report mismatches, and exit with non‑zero status if any checksum differs.  
  *Verification*: Script exits with status 0 when all hashes match; exits with non‑zero status and prints mismatched files when any differ.

- [ ] **T037_update_hashes_state** **Aggregate artifact hashes into project state** (`state/projects/001-evaluating-the-use-of-graph-neural-netwo.yaml`)  
  *Action*: Parse all `.sha256` side‑car files, build a map `artifact_hashes`, and write it into the state YAML under `artifact_hashes`.  
  *Verification*: The state file parses without error and contains entries for every artifact produced in Phases 3‑6.

- [ ] T035_finalize_state_manager **Update project state file** (`state/projects/001-evaluating-the-use-of-graph-neural-netwo.yaml`)  
  *Action*: Insert `last_updated: <ISO‑timestamp>`, include `artifact_hashes` from T037, and list completed task IDs.  
  *Verification*: YAML parses without error; `last_updated` is recent; `artifact_hashes` contains entries for every artifact produced in Phases 3‑6; the file includes a `runtime_seconds` field populated by T036.

- [ ] **T036_measure_runtime** **Measure total pipeline runtime**  
  *Action*: Wrap the full end‑to‑end execution (from dataset download to final statistical report) with a timer, write `data/results/runtime.json` containing `{ "total_seconds": <float>, "within_limit": true/false }` where `within_limit` is true if total_seconds ≤ 21600 (6 hours).  
  *Verification*: JSON file exists; `within_limit` is asserted true by the verification step.

---

### Execution Order Summary

1. **Phase 3** (T007a–T007c) must succeed before any ingestion or graph work.  
2. **Phase 4** (T010–T017) builds and validates the graph, producing `final_graph_path`.  
3. **Phase 5** (T018–T031) consumes the final graph to create train/test splits, extract features, train/evaluate models, and perform statistical analysis.  
4. **Phase 6** (T032–T036) documents the pipeline, verifies data integrity, aggregates hashes, records runtime, and finalises project state.

All tasks respect data‑flow constraints, enforce the 7 GB memory limit with recorded usage, and provide measurable outputs for every success criterion defined in the specification.  

--- 

*Note*: Tasks marked **optional** (e.g., Bot‑IoT fallback) will abort the pipeline unless a formal spec amendment is provided, preserving the original functional requirements.  
