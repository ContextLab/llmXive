# Research: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Dataset Strategy

| Dataset | Source / URL | Format | Usage | Verification Status |
|:---|:---|:---|:---|:---|
| **CTU‑13** | https://huggingface.co/datasets/ctu13/ctu13 | CSV/Parquet (NetFlow records) | Primary source for all NetFlow flows, node/edge construction, and ground‑truth anomaly labels. | **Verified** (reachable, format‑checked) |
| **CTU‑13 (metadata)** | https://huggingface.co/datasets/ctu13/ctu13 | CSV (scenario metadata) | Provides scenario‑level labels and timestamps. | **Verified** |

**Rationale**  
The specification mandates ingestion of the CTU‑13 dataset (FR‑001). A verified HuggingFace mirror is available, satisfying the platform’s data‑availability rule. All downstream claims are explicitly scoped to CTU‑13 traffic characteristics.

## Graph Construction & Memory Strategy

1. **Streaming Ingestion** – `datasets.load_dataset("ctu13/ctu13", split="train", streaming=True)` reads the NetFlow file in 1 M‑row chunks, avoiding full‑dataset loading.
2. **Edge Aggregation** – For each chunk, update a `networkx.DiGraph`:
   * Nodes: hashed IP strings (`sha256(ip)`) to satisfy PII hygiene.
   * Edges: directed (src → dst) with `weight = sum(packet_count)` and timestamps stored as min/max per edge.
3. **Memory Guard** – After each chunk, `tracemalloc` records current and peak memory. If peak > 6.8 GB, the script aborts with a clear error (fulfilling FR‑002).
4. **Unbiased Stratified Subsampling** – If `G.number_of_nodes() > 5,000`:
   * Compute the overall anomaly proportion in the full graph.
   * Perform stratified random sampling that preserves this proportion while selecting **5** seeds (deterministic via `code/utils/seed.py`).
   * The resulting subgraph is saved as `graph_{scenario}_subsampled.graphml.gz`.
5. **Determinism** – All random operations use the central seed manager (`code/utils/seed.py`).

## Model Strategy

| Model | Architecture / Settings | Input Features | Training Details |
|-------|------------------------|----------------|------------------|
| **GCN** | 2‑layer Graph Convolutional Network (hidden dim = 64, ReLU, dropout = 0.5) | Node‑level structural features (degree, in/out degree, betweenness, clustering, edge‑weight variance, temporal span) | PyTorch CPU backend; max 30 epochs; early stopping (patience = 5, Δ = 1e‑4); Adam lr = 0.01; **5 seeds** (42, 123, 456, 789, 101112) |
| **Random Forest** | `sklearn.ensemble.RandomForestClassifier` (n_estimators = 200, max_depth = None) | Same structural features | CPU; deterministic via `random_state` |
| **XGBoost** | `xgboost.XGBClassifier` (max_depth = 6, n_estimators = 200, learning_rate = 0.1, tree_method = `hist`, `use_gpu=False`) | Same structural features | CPU‑only |

All models are trained **node‑wise**: each node’s label (`is_anomaly`) is **derived exclusively from training‑set flows** (see Data Model). Nodes that appear only in the test window are added as isolated nodes with label 0; they do not affect training.

### Temporal Hold‑out (FR‑008)

* **Training Window** – First [deferred] of the chronological flow timestamps per scenario.
* **Test Window** – Remaining [deferred] (no overlap).
* Graph construction for training uses only the training flows; the test graph is the training graph plus isolated nodes for any IPs that appear only in the test window (ensuring class distribution is unchanged). Unseen IPs are **not dropped**.

## Statistical Rigor & Methodology

* **Primary Metric** – F1‑Score (reported mean ± SD across 5 seeds). AUC‑ROC reported as secondary.
* **Wilcoxon Signed‑Rank Tests** (FR‑006) – Paired comparisons of F1 scores across the 5 seeds for:
  1. GCN vs. Random Forest  
  2. GCN vs. XGBoost  
  3‑7. Each of the top‑5 structural features (as identified by Random Forest importance) vs. a null baseline (labels permuted 1 000 times, model trained on a single feature).  
* **Multiple‑Comparison Correction** – Benjamini‑Hochberg applied to the seven p‑values; significance declared if BH‑adjusted p < 0.05 (SC‑003). With only a limited number of paired observations, the smallest attainable two‑sided p‑value is relatively high, so we acknowledge that the correction may render all comparisons non‑significant; this limitation is reported transparently.  
* **Power & Limitations** – The 5‑seed design follows the specification; we note the limited statistical power and that results should be interpreted as exploratory within CTU‑13.  
* **Collinearity Disclosure** – Correlation matrix of structural features will be printed; any high (>0.8) correlations will be noted, and independent effect claims will be avoided.  
* **Target AUC Threshold** – SC‑005 specifies a benchmark AUC ≥ 0.75; the final report will state whether each model meets this target.

## Decision Rationale: CPU‑Only Constraint

All libraries have stable CPU wheels; the GCN on ≤5 000 nodes converges within minutes on the 2‑vCPU runner. No GPU‑only features are required, satisfying the compute‑feasibility rule. If any step threatens the 6‑hour wall‑clock, the pipeline automatically reduces `n_estimators` for baselines or hidden dimension for the GCN and logs the adjustment.

## Limitations

* **Dataset Scope** – Analyses are confined to the publicly available CTU‑13 dataset; we do **not** claim that GNNs improve anomaly detection beyond this benchmark. Results are strictly observational within this dataset and should not be interpreted as evidence of generalizable causal improvement.
* **Causal Claims** – The study is observational; any inference that graph structure *causes* improved detection is unwarranted. Results reflect association within the CTU‑13 data.
* **Statistical Power** – Using only 5 random seeds restricts the granularity of the Wilcoxon test; the smallest achievable two‑sided p‑value (≈0.0625) may prevent any comparison from achieving the FDR < 0.05 threshold after BH correction. This limitation is reported in the final results section.

---



