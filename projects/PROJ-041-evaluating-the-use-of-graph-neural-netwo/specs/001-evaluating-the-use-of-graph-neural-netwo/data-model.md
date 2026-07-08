# Data Model: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Entity-Relationship Overview

The data model consists of three primary layers: **Raw Ingestion**, **Graph Representation**, and **Derived Features/Metrics**.

### 1. Raw NetFlow Records
Source data containing flow-level details.
*   **Fields**: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `start_time`, `end_time`, `packets`, `bytes`, `label` (if available).
*   **Source**: CTU-13 (CSV) or NF-BoT-IoT-v3 (Parquet).

### 2. Network Graph (Directed)
A directed graph $G = (V, E)$ where:
*   $V$: Unique IP addresses (hashed for PII).
*   $E$: Directed edges $(u, v)$ representing flows from $u$ to $v$.
*   **Edge Attributes**: `weight` (packet count), `timestamp_range` (start, end).
*   **Node Attributes**: `is_anomaly` (binary, **aggregated** from flow labels: 1 if IP participated in ANY anomalous flow), `degree`, `in_degree`, `out_degree`.
*   **Subsampled Graph**: If nodes > 5,000, the graph is subsampled using the **Anomaly-Preserving Subsampling** strategy (retaining anomalous nodes and high-degree hubs). The result is saved as `graph_{scenario}_subsampled.graphml`.

### 3. Feature Matrix (Node-Level)
A table where rows are nodes (IPs) and columns are structural features.
*   **Features**:
    *   `degree`: Total degree.
    *   `in_degree`: In-degree.
    *   `out_degree`: Out-degree.
    *   `betweenness_centrality`: Normalized betweenness.
    *   `clustering_coeff`: Local clustering coefficient.
    *   `edge_weight_variance`: Variance of outgoing edge weights.
    *   `temporal_span`: Duration of activity.
*   **Target**: `label` (0=Normal, 1=Anomaly, **aggregated** from flow labels).

### 4. Evaluation Metrics
Aggregated results per scenario and per model.
*   **Fields**: `scenario_id`, `model_type`, `seed`, `precision`, `recall`, `f1_score`, `auc_roc`, `p_value`, `is_significant`, `null_distribution_mean`.

## Data Flow

1.  **Ingest**: `raw_netflow.csv` -> `data/raw/`
2.  **Construct**: `raw_netflow.csv` -> `data/processed/graph_{scenario}.graphml` (with node/edge attributes).
3.  **Subsample**: If nodes > 5,000 -> `data/processed/graph_{scenario}_subsampled.graphml` (Anomaly-Preserving Subsampling, deterministic seed 42).
4.  **Feature Extract**: `graph_{scenario}_subsampled.graphml` -> `data/processed/features_{scenario}.csv`.
5.  **Train/Eval**: `features_{scenario}.csv` -> `data/results/metrics_{scenario}.csv`.
6.  **Aggregate**: All `metrics_{scenario}.csv` -> `data/results/final_aggregate.csv`.

## Storage Constraints & Optimization

*   **Graph Storage**: Use `GraphML` (XML-based) for interoperability, but ensure it is compressed (`.graphml.gz`) if size exceeds 50MB.
*   **Feature Storage**: Use `Parquet` for efficient columnar storage and faster I/O during training.
*   **Memory Management**:
    *   Graphs are loaded one scenario at a time.
 * Feature matrices are streamed to the model in batches if necessary (though [deferred] nodes fit in RAM easily).
    *   Intermediate files are cleaned up after processing to stay within the 14GB disk limit.

## Data Integrity & Hygiene

*   **Checksums**: All files in `data/raw/` and `data/processed/` will be checksummed (SHA-256) and recorded in `state/...yaml`.
* **PII**: IP addresses in `data/` will be hashed (e.g., `SHA256(ip)`) to prevent direct PII exposure, while maintaining graph topology integrity (hash collisions are negligible for [deferred] nodes).
*   **Immutability**: Raw data is never modified. All transformations create new files.
*   **Fallback Hygiene**: If NF-BoT-IoT-v3 is used, its checksum and URL will be recorded as the "Single Source of Truth" in `state/...yaml`.
