# Data Model: Evaluating the Statistical Validity of Common Ranking Metrics

## Entities

### Collection
Represents a specific TREC dataset track.
- `collection_id`: Unique identifier (e.g., "trec-robust04", "trec-web-2009").
- `source_name`: Human-readable name.
- `year`: Year of the track.

### Query
Represents a single search topic from a TREC collection.
- `query_id`: Unique identifier (integer or string).
- `collection_id`: Foreign key to Collection.
- `doc_count`: Number of documents in the query's ranking.
- `relevant_count`: Number of documents with relevance > 0.

### Relevance Judgment (QREL)
Represents a single relevance label for a document in a query.
- `query_id`: Foreign key to Query.
- `doc_id`: Document identifier.
- `relevance`: Relevance score (integer, typically 0-3 or 0-4).
- `iteration`: Iteration identifier (usually '0').

### Metric Score
Represents a computed ranking metric value.
- `query_id`: Foreign key to Query.
- `metric_name`: Name of the metric (e.g., "NDCG@10", "MAP").
- `score`: Computed value (float).
- `source`: "original" or "permuted".
- `permutation_id`: ID of the permutation (null if original).
- `permutation_count`: Total number of permutations executed for this query (for FR-004 verification).

### Null Distribution
Aggregated null distribution for a query and metric.
- `query_id`: Foreign key to Query.
- `metric_name`: Metric name.
- `observed_score`: Original metric score.
- `null_scores`: List of permuted scores (stored as separate rows in CSV).
- `p_value`: Permutation p-value.
- `is_significant`: Boolean (after BH correction).
- `permutation_count`: Exact count of permutations executed (N).

### MDES Result
Minimum Detectable Effect Size analysis result.
- `metric_name`: Metric name.
- `alpha`: Significance threshold (e.g., 0.05).
- `power_target`: Target power (0.80).
- `mdes_value`: Minimum detectable effect size (float).
- `ci_lower`: Lower bound of 95% CI.
- `ci_upper`: Upper bound of 95% CI.
- `method_used`: Method used for alternative hypothesis (e.g., "top_k_swap").
- `tolerance`: Binary search tolerance used.

### Sensitivity Result
Sensitivity analysis result for alpha sweep.
- `alpha`: Significance threshold.
- `significant_count`: Number of queries significant at this alpha.
- `status_change_count`: Number of queries that changed significance status from previous alpha.

### Subsample Log
Records queries dropped due to runtime/memory limits.
- `query_id`: The dropped query identifier.
- `trigger_reason`: "runtime" or "memory".
- `timestamp`: ISO timestamp of the drop.
- `collection_id`: Collection from which the query was dropped.

## Data Flow

1. **Raw Data**: TREC qrels (immutable) → `data/raw/`.
2. **Processed Data**:
   - `query_metrics.csv`: Original scores per query/metric.
   - `null_distributions.csv`: Permuted scores per query/metric/permutation.
   - `p_values.csv`: P-values per query/metric.
   - `bh_corrected.csv`: BH-corrected p-values and significance flags.
   - `mdes_results.csv`: MDES estimates.
   - `alpha_sweep.csv`: Sensitivity analysis results.
   - `subsample_log.csv`: Dropped queries (if any).
3. **Artifacts**: PNG plots, summary tables (with explicit associational framing).

## Constraints

- **Immutability**: Raw data files are never modified.
- **Checksums**: All raw files checksummed; hashes stored in `state/`.
- **Subsampling**: If triggered, subsample index logged in `data/processed/subsample_log.csv` (satisfies FR-011 and Constitution Principle III).
- **Reproducibility**: All random seeds pinned in `config.py`.
