# Data Model: ShutterMuse

## Overview
This document defines the data structures for the ShutterMuse research pipeline. All data is stored in CSV/Parquet formats for compatibility with `pandas` and `scikit-learn`.

## Entities

### 1. Image Sample
Represents a single image unit of analysis.
- **image_id**: Unique identifier (string).
- **source_dataset**: `"AVA"` or `"COCO"` (string).
- **image_path**: Local path to the image file.
- **composition_tags**: JSON string of ground‑truth tags (e.g., `{"lighting": "natural", "angle": "eye-level"}`).
- **face_bbox**: JSON string of primary face bounding box (`{"x":0,"y":0,"w":100,"h":100}`) or `null` if no face detected.
- **demographics**: JSON string of inferred demographics (`{"gender":"male","age":30,"confidence":0.92}`) or `null`.
- **lighting_condition**: Inferred or native lighting category (string).
- **image_quality**: Float representing average brightness (0‑1), used as a covariate in bias analysis.

### 2. Model Output
Stores the raw response from an MLLM in response to a capture‑time guidance prompt.
- **sample_id**: FK to `Image Sample`.
- **model_name**: `"LLaVA-1.6"`, `"Qwen-VL"`, `"GPT-4V"` (string).
- **prompt_type**: `"Standard"` or `"Counterfactual"` (string).
- **raw_output**: The full text response (string).
- **inference_timestamp**: ISO8601 timestamp.
- **status**: `"Success"`, `"Parsing Failure"`, `"Timeout"` (string).

### 3. Error Record
Links a model output to a specific error category.
- **record_id**: Unique identifier.
- **sample_id**: FK to `Image Sample`.
- **model_name**: FK to `Model Output`.
- **error_category**: `"Hallucinated Object"`, `"Incorrect Rule Application"`, `"Missing Advice"`, `"Correct"`, `"Parsing Failure"`, `"Potential Reasoning Error"` (string).
- **confidence_score**: Float (0‑1) if applicable (optional for parsing failures).
- **reasoning_flag**: Boolean (True if the error is identified as a reasoning‑based hypothesis via counterfactual analysis).
- **prompt_type**: `"Standard"` or `"Counterfactual"` (string).

### 4. Analysis Result
Aggregated statistical results.
- **analysis_id**: Unique identifier.
- **test_type**: `"Chi-square"` or `"Fisher's Exact"` (string).
- **variable_x**: e.g., `"Subject Gender"` (string).
- **variable_y**: e.g., `"Error Type"` (string).
- **statistic_value**: Float (Chi‑square value or Fisher statistic).
- **p_value**: Float.
- **significant**: Boolean (p < 0.05).
- **correction_applied**: `"Bonferroni"`, `"Holm"`, or `"None"` (string).
- **effect_size**: Float (Cramér’s V) or `null`.
- **confidence_interval**: JSON string with lower/upper bounds for the effect size or `null`.

## Data Flow
1. **Raw Data** (`data/raw/`) → **Image Sample** (CSV).
2. **Image Sample** + **Inference** → **Model Output** (CSV).
3. **Model Output** + **Ground Truth** → **Error Record** (CSV).
4. **Error Record** + **Demographics** + **Image Quality** → **Analysis Result** (JSON/CSV).

## Storage Constraints
- All CSV files are compressed (`.csv.gz`) to stay within the 14 GB disk limit.
- Large image files remain in `data/raw/images/`; only paths are stored in the tables.