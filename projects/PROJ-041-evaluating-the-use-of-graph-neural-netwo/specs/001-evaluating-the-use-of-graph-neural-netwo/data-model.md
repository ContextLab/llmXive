# Data Model: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Entity‑Relationship Overview

| Layer | Description |
|-------|-------------|
| **Raw NetFlow Records** | Parquet rows from the chosen dataset (CTU‑13 if available, otherwise `keys-i/netFlow`). Fields: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `start_time`, `end_time`, `packets`, `bytes`, `label` (0 = normal, 1 = anomaly). |
| **Network Graph (Directed)** | `networkx.DiGraph` where nodes are hashed IPs, edges are directed flows with attributes `weight` (packet count) and `timestamp_range`. Subsampled to ≤5 000 nodes per scenario (deterministic, stratified). |
| **Node Feature Table** | Parquet file (`features_{scenario}.parquet`) with one row per node and columns: `degree`, `in_degree`, `out_degree`, `betweenness_centrality`, `clustering_coeff`, `edge_weight_variance`, `temporal_span`, `label` (aggregated training‑set node‑level anomaly). |
| **Evaluation Metrics** | CSV (`metrics_{scenario}.csv`) containing `scenario_id`, `model_type`, `seed`, `precision`, `recall`, `f1_score`, `auc_roc`, `t_test_p`, `bh_adj_p`, `significant`. |
| **Aggregate Results** | `final_aggregate.csv` merges all scenario‑level CSVs, adds overall means, SDs, and a summary of the BH‑adjusted significance outcomes. |
| **Attribution Output** | CSV (`gcn_attribution_{scenario}.csv`) mapping node IDs to Integrated‑Gradients scores for each structural proxy. |
| **Pattern‑Based Classifier Results** | CSV (`pattern_classifier_{scenario}.csv`) with AUC on the independent held‑out set. |

## Data Flow Diagram

1. **Download** → `data/raw/netflow.parquet` (checksum recorded; fallback dataset).  
2. **Ingest & Graph Build** → `data/processed/graph_{scenario}_subsampled.graphml.gz`.  
3. **Feature Extraction** → `data/processed/features_{scenario}.parquet`.  
4. **Temporal Hold‑out Split** → training and test node sets (test set includes isolated nodes for unseen IPs).  
5. **Model Training** → metrics only (no persistent model files stored).  
6. **Statistical Testing** → `data/results/metrics_{scenario}.csv`.  
7. **Attribution & Pattern Ranking** → `data/results/gcn_attribution_{scenario}.csv`.  
8. **Pattern‑Based Classification** → `data/results/pattern_classifier_{scenario}.csv`.  
9. **Aggregation** → `data/results/final_aggregate.csv`.  

## Storage & Optimization

* **Graphs** stored compressed (`.graphml.gz`) – typical size < 50 MB after subsampling.  
* **Feature tables** use columnar Parquet; ≤ 5 000 rows → < 5 MB each.  
* **Memory** – Only one scenario is loaded at a time; `tracemalloc` ensures peak RAM stays < 7 GB.  
* **Disk** – All intermediate files are deleted after aggregation to keep total usage < 14 GB.  

## Data Hygiene Guarantees

* **Checksums** – SHA‑256 recorded for every raw and processed file in `state/projects/…yaml`.  
* **PII Protection** – IP strings are hashed before any persistent storage; hash collisions are negligible for ≤ 5 000 nodes.  
* **Immutability** – Raw NetFlow file never altered; each transformation writes a new file with a timestamped name.  
* **Deterministic Subsampling** – Fixed seed guarantees reproducible graph topology across runs.  
* **Label Construction** – Node‑level anomaly labels are derived **exclusively from training‑set flows**; test‑set flows never influence label assignment, preventing leakage.  
* **Schema Validation** – Raw NetFlow rows validated against `contracts/dataset.schema.yaml`; final graph validated against `contracts/graph.schema.yaml`.  

---
