# Research: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Dataset Strategy

| Dataset | Source / URL | Format | Usage | Verification Status |
|:---|:---|:---|:---|:---|
| **NetFlow (keys‑i)** | https://huggingface.co/datasets/keys-i/netFlow/resolve/main/data/NF-BoT-IoT-v3.parquet | Parquet (NetFlow records) | Primary source for all flow records, node/edge construction, and ground‑truth anomaly labels. | **Verified** (reachable, format‑checked) |

**Rationale**  
The original specification required CTU‑13, but no open, programmatically downloadable mirror exists. To satisfy the platform’s data‑availability rule we use the verified NetFlow dataset from HuggingFace, which provides the same essential fields (source/destination IP, packet count, timestamps, label) needed for graph construction and anomaly labeling. All downstream claims are explicitly scoped to this dataset.

## Graph Construction & Memory Strategy

1. **Streaming Ingestion** – `datasets.load_dataset("keys-i/netFlow", split="train", streaming=True)` reads the Parquet file in 1 M‑row chunks, avoiding full‑dataset loading into RAM.  
2. **Edge Aggregation** – For each chunk, update a `networkx.DiGraph`:
   * Nodes: hashed IP strings (`sha256(ip)`) to satisfy PII hygiene (Principle III).  
   * Edges: directed (src → dst) with `weight = sum(packets)`; store `timestamp_start` / `timestamp_end` per edge as the min/max timestamps observed.  
3. **Memory Guard** – After each chunk, `tracemalloc` records current and peak memory. If peak > 6.8 GB, the script aborts with a clear error (fulfilling **FR‑002**).  
4. **Unbiased Stratified Subsampling** – If `G.number_of_nodes() > 5,000`:
   * Compute the overall anomaly proportion in the full graph.  
   * Perform stratified random sampling that preserves this proportion while selecting exactly 5 000 nodes, using the deterministic seed manager (`code/utils/seed.py`).  
   * Save the resulting subgraph as `graph_{scenario}_subsampled.graphml.gz`.  
5. **Determinism** – All random operations are seeded via `code/utils/seed.py`; the same seed produces identical graphs across runs.  

## Model Strategy

| Model | Architecture / Settings | Input Features | Training Details |
|-------|------------------------|----------------|------------------|
| **GCN** | 2‑layer Graph Convolutional Network (hidden dim = 64, ReLU, dropout = 0.5) | Node‑level structural features (degree, in/out degree, betweenness, clustering, edge‑weight variance, temporal span) | PyTorch CPU backend; max 30 epochs; early stopping (patience = 5, Δ = 1e‑4); Adam lr = 0.01; **5 seeds** (42, 123, 456, 789, 101112) |
| **Random Forest** | `sklearn.ensemble.RandomForestClassifier` (n_estimators = 200, max_depth = None) | Same structural features | CPU; deterministic via `random_state` |
| **XGBoost** | `xgboost.XGBClassifier` (max_depth = 6, n_estimators = 200, learning_rate = 0.1, tree_method = `hist`, `use_gpu=False`) | Same structural features | CPU‑only |

All models are trained **node‑wise**: each node’s label (`is_anomaly`) is derived **exclusively from training‑set flows**; test‑set flows are never used to set node labels, preventing leakage.

### Temporal Hold‑out (FR‑008)

* **Training Window** – First 70 % of timestamps per scenario (chronological).  
* **Test Window** – Remaining 30 % (no overlap).  
* Graph construction for training uses only the training flows; the test graph is the training graph plus isolated nodes for any IPs that appear exclusively in the test window (these nodes receive label 0 and are excluded from metric aggregation).  

## Statistical Rigor & Methodology

* **Primary Metric** – F1‑Score (reported mean ± SD across the 5 seeds). AUC‑ROC reported as secondary.  
* **Wilcoxon Signed‑Rank Tests** (FR‑006) – Paired comparisons of F1 scores across the 5 seeds for:  
  1. GCN vs. Random Forest  
  2. GCN vs. XGBoost  
  3‑7. Each of the top‑5 structural features (identified by Random Forest importance) vs. a null baseline (labels permuted 1 000 times, model trained on a single feature).  
* **Multiple‑Comparison Correction** – Benjamini‑Hochberg applied to the seven p‑values; significance declared if BH‑adjusted p < 0.05 (SC‑003). Because only 5 paired observations are available, the smallest attainable two‑sided p‑value is ≈0.0625; we therefore report that no comparison can survive the FDR < 0.05 threshold and discuss this limitation transparently.  
* **Power & Limitations** – The 5‑seed design follows the specification; we note the limited statistical power and treat results as exploratory.  
* **Collinearity Disclosure** – A correlation matrix of structural features will be printed; any pair with |ρ| > 0.8 will be flagged, and we will avoid claiming independent effects for highly collinear features.  
* **Target AUC Threshold** – SC‑005 references a pre‑defined benchmark AUC ≥ 0.75; the final report will state whether each model meets this target.  

## Decision Rationale: CPU‑Only Constraint

All chosen libraries have stable CPU wheels; the GCN on ≤5 000 nodes converges within minutes on the 2‑vCPU runner. No GPU‑only features are required, satisfying the compute‑feasibility rule. If any step threatens the 6‑hour wall‑clock, the pipeline will automatically reduce `n_estimators` for baselines or hidden dimension for the GCN and log the adjustment.

## Limitations

* **Dataset Substitution** – Analyses are confined to the verified NetFlow dataset; we do **not** claim that findings generalize to CTU‑13 or other traffic corpora.  
* **Causal Claims** – The study is observational; any inference that graph structure *causes* improved detection is unwarranted. Results reflect association within the chosen dataset.  
* **Statistical Power** – Using only 5 random seeds restricts the granularity of the Wilcoxon test; the smallest achievable two‑sided p‑value (≈0.0625) may prevent any comparison from achieving the FDR < 0.05 threshold after BH correction. This limitation is reported in the final results section.  

---
