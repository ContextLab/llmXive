# Data Model: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

## Overview
This document defines the data structures used throughout the pipeline, from raw dataset ingestion to final analysis results. All derived data is immutable and checksummed.

## Raw Data Schemas

### IA-Bench (metadata.jsonl)
- `prompt_id`: string (unique identifier)
- `text`: string (raw prompt)
- `source`: string (dataset origin)
- `task_type`: string (e.g., "image_generation")

### WISE-Verified (cultural_common_sense_verified.json)
- `id`: string
- `prompt`: string
- `reference_description`: string (human-verified, independent of prompt)
- `verified`: boolean
- `domain`: string (e.g., "photorealistic", "abstract")

### Derived: Complexity Scores (complexity_scores.csv)
- `prompt_id`: string
- `prompt_text`: string
- `parse_depth`: float
- `clause_count`: int
- `mtld`: float
- `complexity_score`: float (0.0–1.0)
- `source_dataset`: string

### Derived: Routed Prompts (routed_prompts.csv)
- `prompt_id`: string
- `complexity_score`: float
- `category`: string (low/medium/high)
- `routing_decision`: string (rule_based/qwen_agent)
- `is_counterfactual_sample`: boolean (True if Low/Med prompt selected for Baseline execution)
- `timestamp`: datetime

### Derived: Generated Images (generated_images/)
- Directory structure: `data/derived/generated_images/{prompt_id}.png`
- Metadata: `generation_log.jsonl` with `prompt_id`, `method`, `latency`, `tokens`, `is_baseline`

### Derived: Fidelity Scores (fidelity_scores.csv)
- `prompt_id`: string
- `baseline_clip_score`: float (Nullable for non-counterfactual Low/Med)
- `hybrid_clip_score`: float
- `fidelity_delta`: float (Nullable if baseline is missing)
- `reference_description`: string
- `reference_independence_flag`: string (PASS/FAIL)

### Derived: Domain Labels (domain_labels.csv)
- `prompt_id`: string
- `domain`: string (photorealistic/abstract/illustration)
- `confidence`: float

## Analysis Outputs

### Knee Point Analysis (knee_point_analysis.json)
- `threshold`: float
- `slope_change`: float
- `r_squared_piecewise`: float
- `r_squared_linear`: float
- `f_test_p_value`: float
- `lrt_p_value`: float
- `permutation_p_value`: float
- `model_comparison`: string (piecewise_superior/linear_superior)
- `dataset_scope`: string (description of data used for regression, e.g., "High + Counterfactual Sample")

### Stratified Results (stratified_results.json)
- `domains`: [
    {`domain`: string, `threshold`: float, `slope_change`: float, `p_value`: float},
    ...
  ]

### Efficiency Metrics (efficiency_metrics.csv)
- `prompt_id`: string
- `method`: string
- `latency_seconds`: float
- `tokens_used`: int

## Data Flow
1. Fetch raw datasets → `data/raw/` (checksummed).
2. Validate with Reference-Validator + Reference Independence Check → `data/derived/complexity_scores.csv`.
3. Route prompts + Apply Counterfactual Sampling → `data/derived/routed_prompts.csv`.
4. Generate images (Baseline for High + Counterfactual; Hybrid for all) → `data/derived/generated_images/`.
5. Compute fidelity → `data/derived/fidelity_scores.csv`.
6. Classify domains → `data/derived/domain_labels.csv`.
7. Run regression on High + Counterfactual subset → `data/results/knee_point_analysis.json`.
8. Stratify → `data/results/stratified_results.json`.
9. Efficiency report → `data/results/efficiency_metrics.csv`.