# Data Model: llmXive follow-up: extending "Qwen-Image-Agent"

## Overview

This document defines the data structures used to represent prompts, complexity scores, routing decisions, generated images, and fidelity metrics. All data is stored in `data/` as JSON/Parquet/CSV with checksums.

## Entity Definitions

### 1. Prompt (Input)
Represents a raw text prompt from IA-Bench or LAION-CC.
-   `prompt_id`: Unique identifier (UUID).
-   `source`: "IA-Bench" or "LAION-CC".
-   `raw_text`: The original prompt string.
-   `domain_label`: (Optional) Initial domain guess (if available in source).
-   `timestamp`: ISO 8601 creation time.

### 2. ComplexityScore (Derived)
Result of the syntactic analysis.
-   `prompt_id`: FK to Prompt.
-   `parse_depth`: Float (max depth of dependency tree).
-   `clause_count`: Integer.
-   `mtld`: Float (Mean Length of T-Units).
-   `complexity_score`: Float (0.0–1.0).
-   `routing_category`: "low", "medium", or "high".
-   `features_vector`: Dictionary of normalized metrics.

### 3. RoutingDecision (Derived)
Log of the routing logic.
-   `prompt_id`: FK to Prompt.
-   `category`: "low", "medium", "high".
-   `target_path`: "lightweight" or "agent".
-   `threshold_applied`: The specific threshold value used (e.g., 0.2, 0.6).
-   `latency_ms`: Execution time of routing logic.
-   `token_count`: (Nullable) Actual tokens for LLM paths. For diffusion, this is null.
-   `inference_steps`: (Nullable) Steps for diffusion paths.

### 4. GeneratedImage (Output)
Result of the generation step.
-   `prompt_id`: FK to Prompt.
-   `generation_method`: "lightweight" or "agent".
-   `image_path`: Relative path to the generated image file.
-   `image_hash`: SHA256 of the image file.
-   `domain_classified`: "photorealistic", "abstract", "illustration" (from ResNet-50).
-   `generation_latency_ms`: Time taken to generate.
-   `agent_token_count`: (Nullable) Tokens used if agent path. Null for diffusion.
-   `inference_steps`: (Nullable) Steps used if diffusion model.

### 5. FidelityMetric (Derived)
Result of the CLIP evaluation.
-   `prompt_id`: FK to Prompt.
-   `reference_text`: The generated gold-standard reference description.
-   `clip_score_baseline`: Float (Full Agent/Proxy path).
-   `clip_score_hybrid`: Float (Hybrid path).
-   `fidelity_delta`: Float (Baseline - Hybrid).
-   `structural_detail_score`: Float (Secondary metric for construct validity).
-   `domain_stratum`: "photorealistic", "abstract", "illustration".

### 6. RegressionResult (Final Output)
Aggregated statistical findings.
-   `model_type`: "piecewise" or "linear".
-   `knee_point`: Float (complexity score).
-   `slope_change`: Float.
-   `p_value_f_test`: Float.
-   `p_value_lrt`: Float (Likelihood Ratio Test).
-   `p_value_permutation`: Float.
-   `r_squared`: Float.
-   `domain_stratum`: "overall" or specific domain.
-   `confidence_interval`: [lower, upper].
-   `model_comparison`: "piecewise_superior", "linear_sufficient", "no_threshold_found".

## Storage Layout

```text
data/
├── raw/
│   ├── ia_bench_prompts.parquet
│   └── laion_cc_prompts.parquet
├── processed/
│   ├── complexity_scores.csv
│   ├── routing_logs.json
│   ├── reference_texts.json
│   └── generated_images/
│       ├── img_001_baseline.png
│       ├── img_001_hybrid.png
│       └── ...
├── results/
│   ├── pilot_correlation.json  # Gate for Phase 1
│   ├── fidelity_metrics.csv
│   ├── regression_stats.json
│   └── plots/
│       └── fidelity_delta_curve.png
```

## Data Flow

1.  **Ingestion**: `IA-Bench`/`LAION-CC` → `Prompt` entities.
2.  **Scoring**: `Prompt` → `ComplexityScore` (via `scoring` module).
3.  **Sampling**: Select 600 prompts (stratified by domain) → `PairedSample`.
4.  **Reference Gen**: `PairedSample` → `ReferenceText` (via LLM).
5.  **Routing**: `ComplexityScore` → `RoutingDecision` (via `router` module).
6.  **Generation**: `RoutingDecision` → `GeneratedImage` (via `pipeline` module, **Paired Execution**).
7.  **Evaluation**: `GeneratedImage` + `ReferenceText` → `FidelityMetric` (via `fidelity` module).
8.  **Analysis**: `FidelityMetric` → `RegressionResult` (via `regression_analysis` module).