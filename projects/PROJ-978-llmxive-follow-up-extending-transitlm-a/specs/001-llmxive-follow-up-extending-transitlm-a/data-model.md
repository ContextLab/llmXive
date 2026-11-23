# Data Model: llmXive follow-up: extending "TransitLM"

## 1. Entities & Attributes

### 1.1 Route
Represents a single transit path.
*   `route_id`: Unique string identifier.
*   `city`: String (e.g., "Beijing", "Shanghai").
*   `start_station`: String (Station ID or name).
*   `end_station`: String.
*   `station_sequence`: List[String] (Ordered list of station IDs).
*   `stop_count`: Integer (Length of the sequence).
*   `validity`: Boolean (True if the model prediction matches *any* valid path in the ground truth set).
*   `topological_complexity`: Float (Calculated path-level betweenness centrality).
*   `stratum`: String ("short-haul", "medium-haul", "long-haul").
*   `valid_path_set`: List[List[String]] (The set of all geographically valid paths for this start/end pair, generated via BFS on the adjacency graph, independent of dataset ground truth).
*   `hop_validity`: List[Boolean] (Validity status for each hop in the sequence).
*   `failure_hop`: Integer (Index of the first invalid hop, or null).

### 1.2 Station
Represents a transit stop.
*   `station_id`: String (Unique identifier).
*   `city`: String.
*   `frequency`: Integer (Count of occurrences in training data).
*   `vocab_rank`: Integer (Rank in the top-N vocabulary list).
*   `is_unknown`: Boolean (True if mapped to `<UNKNOWN>` token).

### 1.3 AdjacencyGraph
Represents the local connectivity structure.
*   `nodes`: Set[String] (Station IDs).
*   `edges`: List[Tuple[String, String]] (Directed edges).
*   `edge_overlap_pct`: Float (Percentage of edges in the graph that exist in the ground truth).
*   `transition_frequencies`: Dict[Tuple[String, String], Integer] (For the fixed lookup model).

### 1.4 ModelOutput
Represents the prediction result.
*   `route_id`: String.
*   `predicted_sequence`: List[String].
*   `confidence_scores`: List[Float]. (For baseline only; lightweight is deterministic).
*   `failure_hop`: Integer (Index of the first invalid hop, or null).
*   `inference_time_ms`: Float.
*   `peak_memory_mb`: Float.
*   `model_type`: String ("lightweight" or "baseline").
*   `valid_path_match`: Boolean (True if prediction matches any path in valid_path_set).

### 1.5 StatisticalResult
Represents the output of the survival analysis and inflection point detection.
*   `city`: String.
*   `model_type`: String ("lightweight", "baseline").
*   `survival_curve`: Dict (Time vs. Survival Probability).
*   `median_survival_length`: Float.
*   `log_rank_p_value`: Float.
*   `adjusted_p_value`: Float (Benjamini-Hochberg corrected).
*   `inflection_point`: Integer (Route length where divergence occurs, or null).
*   `inflection_confidence_interval`: List[Float] (Confidence interval for the inflection point).
*   `effect_size_cohen_h`: Float (Effect size for the proportion difference at the inflection point).
*   `inference_metrics`: Dict (Performance metrics).
*   `baseline_status`: String ("success", "timeout", "oom", "inconclusive").

## 2. Data Flow

1.  **Raw Data**: `data/raw/transitlm_sft.jsonl` (Downloaded from Hugging Face).
2.  **Processed Data**:
    *   `data/processed/station_vocab.json` (Top-N mapping).
    *   `data/processed/city_mapping.json` (Station to City mapping).
    *   `data/processed/adjacency_graph_{city}.json` (Local graph with transition frequencies).
    *   `data/processed/stratified_routes.parquet` (Stratified test set with valid_path_set and hop_validity).
3.  **Analysis Data**:
    *   `data/analysis/survival_curves.csv` (KM curves).
    *   `data/analysis/inflection_points.json` (Results).
4.  **Artifacts**:
    *   `data/artifacts/model_predictions.jsonl` (Raw predictions).
    *   `data/artifacts/profiling_report.json` (CPU metrics).

## 3. Constraints & Validation

*   **Vocabulary**: Station IDs not in the top-N list MUST be mapped to `<UNKNOWN>`.
*   **Stratification**: Routes MUST be strictly categorized by `stop_count`.
*   **Graph**: The adjacency graph MUST be validated for edge overlap ≥95% before use.
*   **Censoring**: Routes completing without error are censored at `stop_count`.
*   **Validity**: Validity MUST be checked against the `valid_path_set` generated via BFS, not just a single ground truth sequence.
*   **Missing Baseline**: If `baseline_status` is "timeout" or "oom", `inflection_point` MUST be null and `baseline_status` MUST be recorded as "inconclusive" for the divergence claim.