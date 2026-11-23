# Data Model: Evaluating the Effectiveness of LLMs for Detecting Code Smells

## 1. Entity Definitions

### 1.1. CodeFunction
- `id`: **string** – unique identifier (e.g., SHA‑256 of source code).  
- `source_code`: **string** – raw Python function.  
- `structural_metrics`: **object**  
  - `loc`: **integer** (≥ 1).  
  - `cyclomatic_complexity`: **integer** (≥ 1).  
  - `nesting_depth`: **integer** (≥ 0).  
- `static_labels`: **array[string]** – raw Pylint error codes.  
- `normalized_static_labels`: **array[string]** – canonical smell names mapped from `static_labels`.  
- `semantic_vector`: **array[number]** – MiniLM embedding with a suitable dimensionality..  
- `semantic_complexity_score`: **number** – simple aggregate (e.g., variance) of `semantic_vector`.  
- `llm_labels`: **array[string]** – smell categories returned by CodeLlama (canonical names).  
- `llm_raw_output`: **string** – raw LLM response (for debugging).  
- `parse_status`: **enum** – `SUCCESS`, `PARSE_ERROR`, `CONTEXT_OVERFLOW`.

### 1.2. DetectionResult
- `smell_category`: **string** – canonical smell name.  
- `detected_by_static`: **boolean**.  
- `detected_by_llm`: **boolean**.  
- `features_at_detection`: **object** – snapshot of `structural_metrics` and `semantic_complexity_score`.

### 1.3. StatisticalReport
- `mcnemar_pvalues`: **object** – keys = smell categories, values = p‑value (0 – 1).  
- `logistic_regression_static_only`: **object** – predictor → coefficient.  
- `logistic_regression_llm_only`: **object** – predictor → coefficient.  
- `multinomial_regression_coefficients`: **object** – predictor → list of three coefficients (static‑only, LLM‑only, both).  
- `complementarity_summary`: **string** – narrative of overlap / exclusive detections.  
- `sensitivity_analysis`: **object** – keys = LOC threshold (integer), values = `{static_only_proportion: number (0‑1)}`.  
- `vif_scores`: **object** – predictor → VIF value.  
- `resource_usage`: **object** – `peak_ram_gb` (≥ 0), `total_time_hours` (≥ 0).  
- `power_analysis`: **object** – `m_des` (minimum detectable effect size), `estimated_discordance_rate`.

## 2. File Formats

### 2.1. `data/static_baseline.csv`
| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Unique identifier. |
| `source_code` | string | Raw code (escaped newlines). |
| `loc` | integer | Lines of Code. |
| `cyclomatic_complexity` | integer | Radon CC metric. |
| `nesting_depth` | integer | Max nesting depth. |
| `static_labels` | string (JSON array) | Raw Pylint codes. |
| `normalized_static_labels` | string (JSON array) | Canonical smell names. |

### 2.2. `data/semantic_analysis.json`
- **Format**: JSON Lines (`.jsonl`).  
- **Each line**: a `CodeFunction` object (including all fields above).

### 2.3. `results/statistical_significance.json`
- **Format**: JSON.  
- **Schema**: `contracts/statistical_report.schema.yaml`.

## 3. Data Flow
1. **Raw download** → `data/raw/code-search-net.parquet` (checksumed).  
2. **Sampling & static analysis** → `data/processed/static_baseline.csv`.  
3. **Embedding + LLM** → `data/processed/semantic_analysis.json`.  
4. **Statistical pipeline** → `results/statistical_significance.json` + `results/sensitivity_report.md`.

## 4. Constraints & Validation
- **Completeness**: ≥ 95 % of sampled functions must have non‑null `structural_metrics`, `semantic_vector`, and at least one label set.  
- **Validity**: `loc`, `cyclomatic_complexity` ≥ 1; `nesting_depth` ≥ 0.  
- **Uniqueness**: `id` must be unique across all files.  
- **Immutability**: Raw files (`data/raw/*`) are never overwritten; all derived artifacts receive new filenames.

---


