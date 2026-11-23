# Data Model: Counterfactual Inspector Agent

## Overview

This document defines the data structures, schemas, and flow for the Counterfactual Inspector Agent. All data artifacts are versioned and checksummed.

## Input Data Model

### Raw Dataset
- **Source**: Verified public datasets (UCI HAR, etc.).
- **Format**: CSV, Parquet, or JSON.
- **Constraints**: Must contain at least 5 numeric variables and 30 rows (for statistical power).
- **Handling**: Missing values are imputed (mean/median) or excluded per `llmXive` protocol.

### Configuration
- **File**: `code/config.py`
- **Fields**:
    - `RANDOM_SEED`: int (pinned)
    - `P_THRESHOLD`: float (0.05)
    - `R_THRESHOLD`: float (0.15)
    - `MAX_LLM_TIMEOUT`: int (900 seconds)
    - `LLM_FALLBACK_MODEL`: string ("phi-3-mini")

## Output Data Models

### 1. Baseline Narrative (JSON)
```json
{
  "primary_narrative": "string",
  "primary_correlation": {
    "var_a": "string",
    "var_b": "string",
    "r_value": float,
    "p_value": float
  },
  "dataset_id": "string",
  "row_count": int
}
```

### 2. Counterfactual Report (JSON)
- **Schema**: `contracts/counterfactual_report.schema.yaml`
- **Fields**:
    - `threshold_config`: string (e.g., "p<0.05, |r|>0.15")
    - `claim`: string OR "NO_SIGNIFICANT_COUNTERFACTUAL"
    - `p_value`: float
    - `partial_r`: float
    - `stability_score`: float (optional, for future robustness checks)
    - `validity_status`: string ("verified", "low_power", "failed")
    - `query_executed`: string (the SQL/Python query)
    - `low_power_flag`: boolean

### 3. Integrated Story (JSON)
- **Schema**: `contracts/story_output.schema.yaml`
- **Fields**:
    - `title`: string
    - `baseline_section`: string
    - `counterfactual_section`: string (or "None found")
    - `citations`: array of strings (e.g., "Data query: ... returned r=...")
    - `caution_flags`: array of strings (e.g., "Low Power - Interpret with Caution")
    - `neutrality_score`: float (internal metric)

## Data Flow

1.  **Ingest**: `data_loader.py` fetches raw data -> `data/raw/`.
2.  **Preprocess**: `data_loader.py` cleans/imputes -> `data/processed/`.
3.  **Baseline**: `stats_engine.py` computes correlations -> `output/baseline_stories/`.
4.  **Counterfactual**: `query_generator.py` + `stats_engine.py` (partial corr) -> `output/counterfactual_reports/`.
5.  **Synthesis**: `synthesizer.py` merges -> `output/integrated_stories/`.
6.  **Metrics**: `main.py` aggregates -> `output/metrics_report.json`.
