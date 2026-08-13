# Data Model: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

## Entity Definitions

### CodeSnippet
Represents a single unit of source code with attributes.
- `id`: Unique string identifier (e.g., `py_001_vuln`).
- `language`: Enum (`C`, `Python`, `JavaScript`).
- `source_code`: String (raw code snippet).
- `ground_truth_label`: Enum (`Vulnerable`, `Safe`).
- `ground_truth_category`: String (e.g., `CWE-89` for SQLi).
- `source_dataset`: String (e.g., `VulDeePecker`, `JSVulnDB`, `NIST_Juliet`).
- `truncated`: Boolean (true if code was truncated for context window).

### FeatureVector
Represents the extracted properties of a snippet.
- `snippet_id`: Foreign key to `CodeSnippet.id`.
- `ast_depth`: Integer (max depth of AST).
- `node_count`: Integer (total nodes in AST).
- `cyclomatic_complexity`: Float (McCabe complexity).
- `taint_api_count`: Integer (frequency of taint-source APIs).
- `sanitization_present`: Boolean (presence of known sanitizers).
- `parse_error`: Boolean (true if parsing failed).
- `language`: Enum (`C`, `Python`, `JavaScript`).
- `embedding_similarity_score`: Float (Optional/Nullable; excluded from primary regression).

### PredictionResult
Represents the LLM or Analyzer's output.
- `snippet_id`: Foreign key to `CodeSnippet.id`.
- `model_type`: Enum (`LLM_ZeroShot`, `Bandit`, `Cppcheck`).
- `predicted_label`: Enum (`Vulnerable`, `Safe`, `Uncertain`).
- `predicted_category`: String (e.g., `SQLi`, `BufferOverflow`).
- `confidence_score`: Float (0.0 to 1.0).
- `is_correct`: Boolean (matches `ground_truth_label`).
- `inference_time_ms`: Float (execution time).
- `truncation_event`: Boolean (true if input was truncated).

### AnalysisMetric
Represents a statistical result.
- `metric_name`: String (e.g., `Pearson_r`, `McFadden_R2`).
- `feature_name`: String (e.g., `ast_depth`).
- `model_type`: String (e.g., `LLM_ZeroShot`).
- `value`: Float.
- `p_value`: Float.
- `adjusted_p_value`: Float (Bonferroni corrected).
- `significance`: Enum (`Significant`, `Not_Significant`).

## Data Flow

1. **Ingestion**: Raw datasets (`data/raw`) → `CodeSnippet` records (`data/processed/raw_snippets.parquet`).
2. **Feature Extraction**: `CodeSnippet` → `FeatureVector` (stored in `data/processed/features.parquet`).
3. **Inference**: `CodeSnippet` + `FeatureVector` → `PredictionResult` (LLM & Static Analyzers).
4. **Analysis**: `PredictionResult` + `FeatureVector` → `AnalysisMetric` (stored in `data/results/analysis_metrics.csv`).

## Storage Schema

- **Raw Data**: Parquet/JSONL in `data/raw/`.
- **Processed Data**: Parquet in `data/processed/` (merged features + snippets).
- **Results**: CSV/JSON in `data/results/` (predictions, metrics).
- **Logs**: JSON in `data/logs/` (errors, stratification verification, dataset substitution justification).
  - `data/logs/stratification_verification.json`: Logs the stratification process and sample counts per category.
  - `data/logs/dataset_substitution_justification.json`: Logs the justification for using JSVulnDB over BigVul and NIST Juliet via git clone.