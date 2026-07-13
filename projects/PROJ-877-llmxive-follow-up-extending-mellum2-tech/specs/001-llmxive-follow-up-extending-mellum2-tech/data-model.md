# Data Model: llmXive follow-up: extending "Mellum2 Technical Report"

## 1. Entities & Relationships

### 1.1 CodeChunk
A segment of source code with associated static analysis labels and LLM inference metrics.
- **ID**: Unique string (hash of content + repo ID).
- **RepositoryID**: String (e.g., `username/repo-name`).
- **Language**: Enum (`python`, `java`, `other`).
- **StaticLabels**:
  - `cyclomatic_complexity`: Integer.
  - `nesting_depth`: Integer.
  - `repetition_ratio`: Float.
- **InferenceMetrics**:
  - `per_token_loss`: Float (log loss).
  - `prediction_entropy`: Float.
  - `normalized_loss`: Float (loss adjusted by 5-gram baseline).
- **Metadata**:
  - `token_count`: Integer.
  - `parse_success`: Boolean.
  - `baseline_model`: String (e.g., "5gram_kneser_ney_disjoint").

### 1.2 RepositoryAggregate
Aggregated metrics per repository (primary unit for correlation analysis).
- **RepositoryID**: String.
- **Language**: String.
- **MeanComplexity**: Float (average of chunk complexities).
- **MeanLoss**: Float (average of chunk losses).
- **MeanNormalizedLoss**: Float.
- **N_Chunks**: Integer (number of chunks in repo).

### 1.3 CorrelationResult
Statistical output describing the relationship between a complexity metric and prediction difficulty.
- **Metric**: String (e.g., `cyclomatic_complexity`).
- **Language**: String.
- **Coefficient**: Float (Pearson/Spearman).
- **PValue**: Float.
- **AdjustedPValue**: Float (after FDR correction).
- **N**: Integer (number of repositories, not chunks).
- **Method**: String (`pearson`, `spearman`).

### 1.4 ThresholdResult
Output of piecewise regression/change-point detection.
- **Metric**: String.
- **Language**: String.
- **ThresholdValue**: Float.
- **SlopeBefore**: Float.
- **SlopeAfter**: Float.
- **ModelFit**: String (e.g., `piecewise`, `linear`).
- **AICDifference**: Float.
- **SensitivityRange**: List of Floats (sweep results).
- **BootstrapStability**: Float (max shift across bootstrap samples).

## 2. Data Flow

1.  **Raw Data**: Parquet files from `codeparrot/github-code`.
2.  **Processed Data**: `data/processed/chunks_annotated.parquet` (CodeChunk entity).
3.  **Aggregation**: `data/processed/repo_aggregates.parquet` (RepositoryAggregate entity).
4.  **Results**: `data/results/correlation_stats.json`, `data/results/threshold_analysis.json`.
5.  **Artifacts**: `data/results/plots/correlation_scatter.png`, `data/results/plots/threshold_sensitivity.png`.

## 3. Constraints & Validation

- **Integrity**: `CodeChunk.ID` must be unique.
- **Range**: `cyclomatic_complexity` >= 0; `nesting_depth` >= 0.
- **Missing Data**: If `parse_success` is False, `InferenceMetrics` are NULL.
- **Normalization**: `normalized_loss` must be computed only if `ngram_prob` > 0.
- **Unit of Analysis**: Correlation results must be based on `RepositoryAggregate`, not raw `CodeChunk` rows, to avoid pseudoreplication.