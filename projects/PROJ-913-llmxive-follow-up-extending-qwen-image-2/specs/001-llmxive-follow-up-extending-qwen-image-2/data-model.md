# Data Model: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## Overview

This document defines the data structures used to store prompts, generated images, evaluation scores, and human‑rating artifacts. All data is stored under `data/` with checksums.

## Entities

### 1. PromptSet
Represents the curated list of text prompts.
- **id**: Unique identifier (UUID).
- **text**: The prompt string.
- **category**: `id` (In‑Distribution) or `ood` (Out‑of‑Distribution).
- **embedding**: Optional 1D float32 array (for validation).

### 2. GeneratedImage
Represents an image artifact produced by the model.
- **image_id**: Unique identifier (UUID).
- **prompt_id**: Foreign key to `PromptSet`.
- **model_version**: `base` or `rl_unified`.
- **path**: Relative path to the image file (`outputs/…`).
- **checksum**: SHA‑256 of the image file.
- **seed**: Random seed used for generation.

### 3. EvaluationScore
Represents a score assigned by a VLM reward model.
- **id**: Unique identifier (UUID).
- **image_id**: Foreign key to `GeneratedImage`.
- **metric**: `aesthetics` | `prompt_adherence` | `identity_preservation`.
- **model**: Name of the VLM model used.
- **value**: Float (0.0 – 1.0).
- **timestamp**: ISO‑8601 datetime string.

### 4. HumanRating
**New** – captures **human‑derived** evaluation scores for FR‑008 validation.
- **id**: Unique identifier (UUID).
- **image_id**: Foreign key to `GeneratedImage`.
- **metric**: `aesthetics` | `prompt_adherence` | `identity_preservation`.
- **score**: Float (0.0 – 1.0) representing the human rating.
- **timestamp**: ISO‑8601 datetime string.
- **source**: URL or identifier of the crowdsourcing platform.

### 5. StatisticalResult
Aggregated results for the study.
- **metric**: `generalization_gap` | `human_gap` | `concordance`.
- **value**: Float (mean or statistic).
- **p_value**: Float.
- **ci_lower**: Float (95% CI lower bound).
- **ci_upper**: Float (95% CI upper bound).
- **test_type**: `paired_t` | `wilcoxon` | `bootstrap` | `permutation`.

### 6. PowerAnalysisReport
**New** – captures the pilot power analysis outcomes.
- **mdes**: Minimum Detectable Effect Size (float) for the target N = 500.
- **achieved_power**: Power (float) estimated for N = 500.
- **variance_inflation_factor**: Float (set to 1.2).
- **pilot_sample_size**: Integer (20).
- **notes**: String describing any limitations.

## File Formats
- **Prompts**: JSONL (one JSON object per line).
- **Scores**: Parquet (for efficient storage.
- **Human Ratings**: Parquet.
- **Results**: JSON.
- **Power Analysis**: JSON.

## Schema Definitions
See **`contracts/`** directory for detailed YAML schemas for each entity.
- **`dataset.schema.yaml`** – for dataset manifests.
- **`generated_image.schema.yaml`** **​**​ ​  ​  ​ ​  ​ ​ ​  ​  ​ ​  ​  ​ ​** (Note: unchanged) **​**​ ​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​** (no change)
- **`prompt.schema.yaml`** – for prompt sets.
- **`score.schema.yaml`** **​**​ ​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​** (no change)
- **`human_rating.schema.yaml`** – for human‑rating.