# Data Model: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## Overview

This document defines the data structures used throughout the pipeline: from raw prompt curation to final statistical results. All data is stored in `data/` and `outputs/` with strict versioning and checksums.

## Entities

### 1. PromptSet

A collection of text prompts categorized by distribution type.

- **id**: Unique identifier (UUID).
- **text**: The prompt string.
- **distribution_type**: Enum (`"in_distribution"`, `"out_of_distribution"`).
- **source**: Origin dataset (e.g., `"Qwen-Image-Bench"`, `"LAION-2B-Physics"`).
- **embedding**: Optional CLIP embedding vector (for leakage check).
- **checksum**: SHA-256 of the prompt text.

### 2. ModelWeights

Metadata for the neural network weights.

- **model_id**: Identifier (e.g., `"Qwen-Image-2.0"`, `"Qwen-Image-2.0-RL"`).
- **path**: Local path to weights.
- **sha256**: Checksum of the downloaded weights.
- **architecture**: Model architecture string.
- **version**: Hugging Face revision.

### 3. GeneratedImage

An image artifact produced by a model.

- **id**: Unique identifier.
- **prompt_id**: FK to `PromptSet.id`.
- **model_id**: FK to `ModelWeights.model_id`.
- **file_path**: Relative path to the image file.
- **seed**: Random seed used.
- **steps**: Number of diffusion steps.
- **checksum**: SHA-256 of the image file.
- **metadata**: JSON blob with generation params.

### 4. EvaluationScore

A numeric value assigned to a generated image.

- **id**: Unique identifier.
- **image_id**: FK to `GeneratedImage.id`.
- **metric_name**: Enum (`"aesthetics"`, `"prompt_adherence"`, `"identity_preservation"`).
- **score**: Float (0-1).
- **scorer_model**: Name of the VLM used (e.g., `"open-clip-vit-b-32"`).
- **timestamp**: UTC timestamp of scoring.

### 5. AnalysisResult

Aggregated statistical results.

- **id**: Unique identifier.
- **experiment_id**: Link to the specific run.
- **metric**: The metric being analyzed (e.g., `"aesthetics"`).
- **mean_base**: Mean score for Base model.
- **mean_rl**: Mean score for RL model.
- **degradation_id**: Mean degradation (Base - RL) for In-Distribution.
- **degradation_ood**: Mean degradation (Base - RL) for Out-of-Distribution.
- **generalization_gap**: `degradation_ood - degradation_id`.
- **p_value**: From Welch’s t-test with bootstrap.
- **confidence_interval**: [lower, upper].
- **power**: Achieved statistical power.
- **mdes**: Minimum Detectable Effect Size.
- **variance_saturation**: Boolean flag.
- **proxy_correlation**: Pearson r with proxy model.

## Data Flow

1. **Ingestion**: `download_models.py` -> `ModelWeights`.
2. **Curation**: `curate_prompts.py` -> `PromptSet` (with leakage check).
3. **Generation**: `engine.py` -> `GeneratedImage`.
4. **Scoring**: `scorer.py` -> `EvaluationScore`.
5. **Analysis**: `stats.py` -> `AnalysisResult`.

## Storage Strategy

- **Raw Data**: `data/raw/prompts.jsonl`, `data/raw/models_manifest.json`.
- **Processed Data**: `data/processed/images/`, `data/processed/scores.jsonl`.
- **Results**: `data/results/stats.json`.
- **Checksums**: `state/artifact_hashes.yaml`.

## Constraints

- **Memory**: All data structures must fit within 7 GB RAM. Large image files are stored on disk, not in memory.
- **Immutability**: Once a file is written to `data/`, it is never modified. Derivations create new files.
- **Schema Validation**: All JSON/JSONL files must conform to the schemas in `contracts/`.
