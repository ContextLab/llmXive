# Research: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Dataset Strategy

| Dataset | Source / URL | Format | Usage | Verification Status |
|:---|:---|:---|:---|:---|
| **CTU‑13 NetFlow** | *Pending specification amendment – no open source currently available* | Parquet (NetFlow records) | Required for graph construction, node/edge creation, and ground‑truth anomaly labeling. | **Not Available** (requires spec change) |

**Rationale**  
The original specification (FR‑001) mandates the CTU‑13 dataset. Since an open, programmatically downloadable mirror is not presently available, the research plan cannot proceed until the specification is amended to either accept an alternative open dataset that provides equivalent NetFlow fields or a verified CTU‑13 source is supplied. No substitution is made in this plan.

## Graph Construction & Memory Strategy

1. **Streaming Ingestion** – `datasets.load_dataset("<CTU13_IDENTIFIER>", split="train", streaming=True)` will read the CTU‑13 Parquet file in 1 M‑row chunks, avoiding full‑dataset loading into RAM. (Implementation placeholder until a valid identifier is supplied.)  
2. **Record Validation** – Each raw NetFlow row is validated against `contracts/dataset.schema.yaml` using `utils/schema_validator.py`. Invalid rows generate a logged warning and are skipped.  
3. **Edge Aggregation** – For each chunk, update a `networkx.DiGraph`:
   * Nodes: hashed IP strings (`sha256(ip)`) to satisfy PII hygiene (Principle III).  
   * Edges: directed (src → dst) with `weight = sum(packets)`; store `timestamp_start` / `timestamp_end` per edge as the min/max timestamps observed.  
4. **Memory Guard** – After each chunk, `tracemalloc` records current and peak memory. If peak > 6.8 GB, the script aborts with a clear error (fulfilling **FR‑002**).  
5. **Unbiased Stratified Subsampling** – If `G.number_of_nodes() > 5,000`:
   * Compute the overall anomaly proportion in the full graph.  
   * Perform stratified random sampling that preserves this proportion while selecting exactly 5 000 nodes, using the deterministic seed manager (`code/utils/seed.py`).  
   * Save the resulting subgraph as `graph_{scenario}_subsampled.graphml.gz`.  
6. **Determinism** – All random operations are seeded via `code/utils/seed.py`; the same seed yields identical graphs across runs.  
7. **Schema Validation** – The final graph is validated against `contracts/graph.schema.yaml` using `utils/schema_validator.py`.

## Model Strategy

| Model | Architecture / Settings | Input Features | Training Details |
|-------|------------------------|----------------|------------------|
| **GCN** | 2‑layer Graph Convolutional Network (hidden dim = 64, ReLU, dropout = 0.5) | Node‑level structural features (degree, in/out degree, betweenness, clustering, edge‑weight variance, temporal span) | PyTorch CPU backend; max 30 epochs; early stopping (patience = 5, Δ = 1e‑4); Adam lr = 0.01; **10 seeds** (42, 123, 456, 789, 101112, 131415, 161718, 192021, 222324, 252627) |
| **Random Forest** | `sklearn.ensemble.RandomForestClassifier` (n_estimators = 200, max_depth = None) | Same structural features | CPU; deterministic via `random_state` |
| **XGBoost** | `xgboost.XGBClassifier` (max_depth = 6, n_estimators = 200, learning_rate = 0.1, tree_method = `hist`, `use_gpu=False`) | Same structural features | CPU‑only |

All models are trained **node‑wise**: each node’s label (`is_anomaly`) is derived **exclusively from training‑set flows**; test‑set flows never influence label assignment, preventing leakage.

### Temporal Hold‑out (FR‑008)

* **Training Window** – First [deferred] of timestamps per scenario (chronological).  
* **Test Window** – Remaining [deferred] (no overlap).  
* Graph construction for training uses only the training flows; the test graph includes the training graph plus isolated nodes for any IPs that appear exclusively in the test window (these nodes receive label 0 and are excluded from metric aggregation).

## Statistical Rigor & Methodology

* **Primary Metric** – F1‑Score (reported mean ± SD across the 10 seeds). AUC‑ROC reported as secondary.  
* **Wilcoxon Signed‑Rank Tests** (FR‑006) – Paired comparisons of F1 scores across the **10 seeds** for:  
  1. GCN vs. Random Forest  
  2. GCN vs. XGBoost  
  3‑7. Each of the top‑5 structural features (identified by Random Forest importance) vs. a null baseline (labels permuted 1 000 times, model trained on a single feature).  
* **Multiple‑Comparison Correction** – Benjamini‑Hochberg applied to the seven p‑values; significance declared if BH‑adjusted p < 0.05 (SC‑003). With 10 seeds the smallest attainable two‑sided p‑value is sufficiently low, allowing at least one comparison to survive correction.  
* **Power & Limitations** – Using 10 seeds satisfies the FR‑006 requirement (≥5 seeds) while providing sufficient granularity for the BH threshold. The modest replication is reported transparently.  
* **Collinearity Disclosure** – A correlation matrix of structural features will be printed; any pair with |ρ| > 0.8 will be flagged, and we will avoid claiming independent effects for highly collinear features.  
* **Target AUC Threshold** – SC‑005 references a benchmark AUC ≥ 0.75; the final report will state whether each model meets this target.

## Decision Rationale: CPU‑Only Constraint

All chosen libraries have stable CPU wheels; the GCN on ≤5 000 nodes converges within minutes on the 2‑vCPU runner. No GPU‑only features are required, satisfying the compute‑feasibility rule. If any step threatens the 214‑minute wall‑clock, the pipeline will automatically reduce `n_estimators` for baselines or hidden dimension for the GCN and log the adjustment.

## Limitations

* **Dataset Availability** – CTU‑13 is not currently open; the analysis cannot be executed until a verified open source is provided or the spec is amended.  
* **Causal Claims** – The study is observational; any claim that graph structure *causes* improved detection is avoided.  
* **Statistical Power** – Although 10 seeds improve feasibility, the analysis remains exploratory; this limitation is reported.  

---



