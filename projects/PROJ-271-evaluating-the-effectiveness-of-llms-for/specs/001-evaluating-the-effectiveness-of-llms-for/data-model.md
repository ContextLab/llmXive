# Data Model: Evaluating the Effectiveness of LLMs for Detecting Code Smells

## 1. Entity Definitions

### 1.1. CodeFunction
Represents a single sampled Python function.
- `id`: Unique string identifier (hash of code or index).
- `source_code`: String (raw code).
- `structural_metrics`: Object
  - `loc`: Integer (Lines of Code).
  - `cyclomatic_complexity`: Integer.
  - `nesting_depth`: Integer.
- `static_labels`: List of strings (Raw Pylint error codes, e.g., `["C0103", "R0913"]`).
- `normalized_static_labels`: List of strings (Canonical smell names, e.g., `["Missing Docstring", "Too Many Arguments"]`).
- `semantic_vector`: Array of floats (dense embedding, e.g., 384-dim).
- `semantic_complexity_score`: Float (Derived metric, e.g., variance of the embedding, to avoid tautology).
- `llm_labels`: List of strings (LLM-detected smell categories, e.g., `["Long Method", "God Class"]`).
- `llm_raw_output`: String (raw LLM response for debugging).
- `parse_status`: Enum (`SUCCESS`, `PARSE_ERROR`, `CONTEXT_OVERFLOW`).

### 1.2. DetectionResult
Represents the outcome of a detection attempt for a specific smell.
- `smell_category`: String (normalized smell name).
- `detected_by_static`: Boolean.
- `detected_by_llm`: Boolean.
- `features_at_detection`: Object (snapshot of `structural_metrics` and `semantic_complexity_score`).

### 1.3. StatisticalReport
Aggregated results.
- `mcnemar_pvalues`: Object (key: smell category, value: float p-value).
- `logistic_regression_static_only`: Object (coefficients for Model 1).
- `logistic_regression_llm_only`: Object (coefficients for Model 2).
- `complementarity_summary`: String (text summary of overlap).
- `sensitivity_analysis`: Object (threshold: false_positive_rate, false_negative_rate).
- `vif_scores`: Object (key: predictor, value: float VIF).
- `resource_usage`: Object (peak_ram_gb, total_time_hours).
- `power_analysis`: Object (m_des, estimated_discordance_rate).

## 2. File Formats

### 2.1. `data/static_baseline.csv`
- **Format**: CSV
- **Columns**: `id`, `source_code`, `loc`, `cyclomatic_complexity`, `nesting_depth`, `static_labels` (JSON string), `normalized_static_labels` (JSON string).
- **Constraint**: `source_code` must be escaped properly (newlines as `\n`).

### 2.2. `data/semantic_embeddings.json`
- **Format**: JSON Lines (`.jsonl`) or JSON Array.
- **Structure**: Array of `CodeFunction` objects (excluding `source_code` if too large, or include if manageable).

### 2.3. `results/statistical_significance.json`
- **Format**: JSON.
- **Structure**: `StatisticalReport` object.

## 3. Data Flow

1. **Raw**: `codeparrot/github-code` (Parquet) -> `data/raw/codeparrot.parquet` (Checksummed).
2. **Processed**: `data/processed/static_baseline.csv` (Structural metrics + Static labels + Normalized labels).
3. **Processed**: `data/processed/semantic_analysis.json` (Embeddings + LLM labels + Complexity Score).
4. **Derived**: `results/statistical_significance.json` (Analysis output).

## 4. Constraints & Validation

- **Completeness**: ≥95% of 800 samples must have valid `source_code` and `structural_metrics`.
- **Validity**: `cyclomatic_complexity` must be ≥1. `loc` must be ≥1.
- **Uniqueness**: `id` must be unique per row.
- **Immutability**: Raw data files must never be overwritten.