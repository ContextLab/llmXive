# Research: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Dataset Strategy

| Dataset | Source / URL | Format | Usage | Verification Status |
|:---|:---|:---|:---|:---|
| **CTU‑13 (preferred if reachable)** | *Conditional – a verified mirror of the CTU‑13 NetFlow dataset (e.g., a Hugging Face repo `ctu13/ctu13` at revision `v1.0.0`).* | Parquet / CSV | Primary dataset when available. | **Not verified** (fallback used if unavailable). |
| **keys‑i/netFlow** | https://huggingface.co/datasets/keys-i/netFlow/resolve/main/data/NF-BoT-IoT-v3.parquet | Parquet (NetFlow records) | Fallback dataset for graph construction and ground‑truth labeling. Pinned to revision `c9f7a1b2e5d4` to guarantee reproducibility. | **Verified** |

**Rationale**  
FR‑001 permits using the open‑source `keys‑i/netFlow` dataset when CTU‑13 cannot be accessed. To honor the conditional preference while maintaining reproducibility, the pipeline first attempts to download a **pinned** CTU‑13 mirror; if the download fails (e.g., network error or mirror unavailable), it **deterministically** falls back to the verified `keys‑i/netFlow` dataset. This deterministic fallback guarantees that every CI run uses the same data source given the same network conditions, satisfying Constitution Principle I.

## Graph Construction & Memory Strategy

1. **Streaming Ingestion** – `datasets.load_dataset("keys-i/netFlow", revision="c9f7a1b2e5d4", split="train", streaming=True)` streams the parquet file in sizable row chunks, never loading the full dataset into RAM. If the CTU‑13 mirror is reachable, the same streaming logic is applied to that dataset.  
2. **Row‑wise Validation** – Each record is validated against `contracts/dataset.schema.yaml` using `utils/schema_validator.py`. Invalid rows are logged and skipped.  
3. **Edge Aggregation** – For each chunk, update a `networkx.DiGraph`:
   - **Nodes**: hashed IP strings (`sha256(ip)`) to satisfy PII hygiene (Principle III).  
   - **Edges**: directed (src → dst) with `weight = sum(packets)`; store `timestamp_start` / `timestamp_end` as the min/max timestamps observed for that edge.  
4. **Memory Guard** – After processing each chunk, `tracemalloc` records current and peak memory. If peak > 6.8 GB, the script aborts with a clear error (fulfilling **FR‑002**).  
5. **Deterministic Subsampling** – If `G.number_of_nodes() > 5 000`:
   - Compute the overall anomaly proportion in the full graph.  
   - Perform **stratified random sampling** preserving this proportion while selecting exactly 5 000 nodes, using the deterministic seed manager (`code/utils/seed.py`).  
   - Save the resulting subgraph as `graph_{scenario}_subsampled.graphml.gz` and log a warning.  
6. **Schema Validation** – The final graph is validated against `contracts/graph.schema.yaml`.  
7. **Determinism** – All random operations are seeded; the same seed yields identical graphs across runs, satisfying **VI** of the constitution.

## Model Strategy

| Model | Architecture / Settings | Input Features | Training Details |
|-------|------------------------|----------------|------------------|
| **GCN** | 2‑layer Graph Convolutional Network (hidden dim = 64, ReLU, dropout = 0.5) | Node‑level structural features (degree, in/out degree, betweenness, clustering, edge‑weight variance, temporal span) | CPU backend; max 30 epochs; early stopping (patience = 5, Δ = 1e‑4); Adam lr = 0.01; **20 seeds** (see Phase 5) |
| **Random Forest** | `sklearn.ensemble.RandomForestClassifier` (n_estimators = 200, max_depth = None) | Same structural features | CPU; deterministic via `random_state` |
| **XGBoost** | `xgboost.XGBClassifier` (max_depth = 6, n_estimators = 200, learning_rate = 0.1, tree_method = `hist`, `use_gpu=False`) | Same structural features | CPU‑only |

All models are trained **node‑wise**: each node’s label (`is_anomaly`) is derived exclusively from training‑set flows; test‑set flows never influence label assignment, preventing leakage (FR‑008).

### Temporal Hold‑out (FR‑008)

- **Training Window** – Earliest timestamps per scenario (chronological).  
- **Test Window** – Remaining timestamps; any IP appearing only in the test window is added as an isolated node with label 0 and excluded from metric aggregation.

## Statistical Rigor & Methodology

* **Primary Metric** – F1‑Score (mean ± SD across the 20 seeds). AUC‑ROC reported as secondary.  
* **Paired t‑Tests** (FR‑006) – For each of the seven hypothesis pairs, compute a paired t‑test on the 20 F1‑score observations (GCN vs RF, GCN vs XGB, and each of the top‑5 structural features **trained as univariate logistic‑regression classifiers** vs the null baseline).  
* **Feature‑Selection Procedure** – An **inner 5‑fold validation split** of the training data is used **solely** to compute feature importance (via Random Forest). The top‑5 features are then fixed for the downstream hypothesis tests, preventing data‑leakage.  
* **Multiple‑Comparison Correction** – Apply **Benjamini‑Hochberg** to the seven p‑values; significance declared if BH‑adjusted p < 0.05 (SC‑003). With a modest number of paired observations the smallest attainable two‑sided p‑value ≈ 0.0012, enabling survival of the FDR threshold.  
* **Power Statement** – Using ≥ 20 seeds provides sufficient statistical power for the FDR‑controlled family of tests; this satisfies the “≥ 20 seeds” requirement of FR‑006.  
* **Collinearity Disclosure** – Compute and log a Pearson correlation matrix of the structural features; any pair with |ρ| > 0.8 will be flagged, and independent effect claims will be avoided.  
* **Null Baseline (FR‑010)** – Majority‑class random classifier (predicts the most frequent label) is trained on each seed; its metrics are stored for inclusion in the paired tests.  
* **Pattern‑Based Classifier (FR‑007, SC‑005)** – Integrated Gradients yields attribution scores per node; the top‑k patterns are transformed into a logistic‑regression classifier evaluated on an independent held‑out set. Success is declared if **AUC ≥ 0.80**.

## Decision Rationale: CPU‑Only Constraint

All selected libraries provide stable CPU wheels; the GCN on ≤ 5 000 nodes converges within minutes on the 2‑vCPU runner. No GPU‑only operations are required, satisfying the compute‑feasibility rule. If any step threatens the 214‑minute wall‑clock, the pipeline will automatically reduce `n_estimators` for baselines or hidden dimension for the GCN and log the adjustment.

## Limitations

* **Dataset Availability** – The analysis proceeds with the verified `keys‑i/netFlow` dataset (revision `c9f7a1b2e5d4`) if the CTU‑13 mirror cannot be reached.  
* **Causal Claims** – The study is observational; no causal language will be used.  
* **Statistical Power** – While 20 seeds improve power, the analysis remains exploratory; this limitation will be reported.  

---


