# Data Model: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Entities

### CodeSnippet
Represents a single unit of source code.
- `id`: string (UUID or hash of code + source)
- `language`: enum['python', 'c', 'javascript']
- `source_code`: string (raw code, truncated if necessary)
- `ground_truth_label`: enum['vulnerable', 'safe', 'unknown']
- `ground_truth_category`: string (e.g., 'CWE-89', 'CWE-119') or null
- `source_dataset`: string (e.g., 'vuldeepecker', 'bigvul')
- `truncated`: boolean (true if code was truncated for LLM context)

### FeatureVector
Extracted properties of a CodeSnippet.
- `snippet_id`: string (FK to CodeSnippet.id)
- `ast_depth`: integer (max depth of AST)
- `node_count`: integer (total AST nodes)
- `cyclomatic_complexity`: float (McCabe complexity)
- `taint_api_count`: integer (frequency of taint-source APIs)
- `sanitization_present`: boolean (true if sanitization found)
- `embedding_similarity_score`: float (cosine similarity to vulnerable pattern)
- `parse_error`: boolean (true if parsing failed)

### PredictionResult
Output of LLM or Static Analyzer.
- `snippet_id`: string (FK to CodeSnippet.id)
- `model_name`: string (e.g., 'phi-3', 'bandit')
- `predicted_label`: enum['vulnerable', 'safe']
- `predicted_category`: string (or null)
- `confidence_score`: float (0.0 to 1.0)
- `is_correct`: boolean (matches ground_truth_label)
- `inference_time_ms`: float (MANDATORY for FR-007)
- `truncation_event`: boolean (true if input was truncated)
- `timeout_risk`: boolean (true if processed after circuit breaker trigger)

### AnalysisMetric
Statistical results.
- `metric_name`: string (e.g., 'Point-Biserial_r', 'McNemar_chi2')
- `feature_name`: string (or 'model_comparison')
- `value`: float
- `p_value`: float
- `adjusted_p_value`: float (if corrected)
- `significance`: enum['significant', 'not_significant']
- `vif`: float (Variance Inflation Factor, if applicable)

## Data Flow

1.  **Download**: Raw datasets downloaded to `data/raw/`. Checksums computed.
2. **Preprocess**: Datasets merged, filtered (max [deferred]), stratified. Output: `data/processed/samples.csv` (CodeSnippet).
3.  **Feature Extraction**: `samples.csv` → `data/processed/features.csv` (FeatureVector).
4.  **Inference**: `samples.csv` → `data/processed/predictions_llm.csv` + `data/processed/predictions_static.csv` (PredictionResult). **Logging `inference_time_ms` is mandatory.**
5.  **Analysis**: `features.csv` + `predictions_*.csv` → `data/processed/metrics.json` (AnalysisMetric).
6.  **Versioning**: `src/utils/hash_artifacts.py` computes content hashes and records them in `state.yaml` after each stage.

## Storage Format

- **Raw Data**: Parquet (preserved as-is).
- **Processed Data**: CSV (for readability and ease of statistical import) with UTF-8 encoding.
- **Metrics**: JSON (structured for programmatic access).
- **Logs**: JSONL (structured logs).