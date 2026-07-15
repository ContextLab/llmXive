# Data Model: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## 1. Overview

This document defines the data structures used in the project, ensuring reproducibility and traceability. All data is stored in `data/` and processed by `code/`.

## 2. Entities

### 2.1 PromptSet
A collection of text prompts categorized by distribution type.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `prompt_id` | string | Unique identifier for the prompt. | UUID format. |
| `text` | string | The prompt text. | Max 512 characters. |
| `distribution_type` | enum | `in_distribution` or `out_of_distribution`. | Required. |
| `source_dataset` | string | Original dataset name (if applicable). | Optional. |
| `embedding_vector` | array[float] | Latent-space embedding of the prompt. | Dimension: 768 (or model-specific). |
| `cosine_similarity_to_id` | float | Similarity to ID centroids (for OOD only). | Range: [0, 1]. |
| `variance_flag` | boolean | True if score variance (CV) > 0.2. | Default: False. |
| `cv_value` | float | Coefficient of Variation for the prompt. | Range: [0, ∞). |

### 2.2 ModelWeights
Represents the binary state of the neural network.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `model_id` | string | Unique identifier (e.g., `base_qwen_image_2.0`). | Required. |
| `version` | string | Version of the model. | Semver. |
| `checksum_sha256` | string | SHA-256 hash of the weights. | Required. |
| `source_url` | string | Canonical source URL. | Required. |

### 2.3 GeneratedImage
An image artifact produced by a model.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `image_id` | string | Unique identifier. | UUID format. |
| `prompt_id` | string | Reference to the prompt. | Foreign key to PromptSet. |
| `model_id` | string | Reference to the model. | Foreign key to ModelWeights. |
| `seed` | int | Random seed used for generation. | Required. |
| `file_path` | string | Path to the image file. | Relative to `data/outputs/`. |
| `dimensions` | tuple[int, int] | Image dimensions (width, height). | Required. |
| `image_hash` | string | SHA-256 hash of the image bytes. | Optional, for proxy matching. |

### 2.4 EvaluationScore
A numeric value assigned to a generated image.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `score_id` | string | Unique identifier. | UUID format. |
| `image_id` | string | Reference to the image. | Foreign key to GeneratedImage. |
| `metric_name` | enum | `aesthetics`, `prompt_adherence`, `identity_preservation`. | Required. |
| `score_value` | float | Score value (0-1). | Range: [0, 1]. |
| `reward_model_version` | string | Version of the VLM reward model. | Required. |
| `variance_flag` | boolean | Inherited from PromptSet. | Required. |

### 2.5 HumanProxyScore
Human-annotated scores from `HuggingFaceH4/image-reward` used for independent validation.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `prompt_id` | string | Unique identifier for the prompt. | Foreign key to PromptSet. |
| `metric_name` | enum | `aesthetics`, `quality`. | Required. |
| `score_value` | float | Human-annotated score. | Range: [0, 10] or normalized [0, 1]. |
| `source` | string | "HuggingFaceH4/image-reward". | Required. |

## 3. Relationships

- **PromptSet** (1) -> (N) **GeneratedImage**: One prompt generates multiple images.
- **ModelWeights** (1) -> (N) **GeneratedImage**: One model generates multiple images.
- **GeneratedImage** (1) -> (N) **EvaluationScore**: One image is scored on multiple metrics.
- **PromptSet** (1) -> (1) **HumanProxyScore**: One prompt may have one proxy score entry.
- **EvaluationScore** (N) -> (1) **HumanProxyScore**: VLM scores are correlated with proxy scores via `prompt_id`.

## 4. Data Flow

1.  **Ingestion**: `data_acquisition.py` downloads models and curates prompts, populating `ModelWeights` and `PromptSet`.
2.  **Proxy Load**: `human_proxy.py` loads `HuggingFaceH4/image-reward` and joins with `PromptSet` by `prompt_id`.
3.  **Generation**: `inference.py` generates images, creating `GeneratedImage` records.
4.  **Scoring**: `scoring.py` scores images, creating `EvaluationScore` records and calculating `variance_flag`.
5.  **Analysis**: `analysis.py` aggregates scores, excludes high-variance prompts, and performs the Independent T-Test and Human Proxy correlation.

## 5. Storage Format

- **Prompts**: CSV (`data/prompts/in_distribution.csv`, `data/prompts/ood.csv`).
- **Models**: Directory structure with `model.safetensors` and `config.json`.
- **Images**: PNG files in `data/outputs/base/` and `data/outputs/rl_unified/`.
- **Scores**: JSONL (`data/scores/scores.jsonl`).
- **Proxy Scores**: JSONL (`data/proxy/human_proxy_scores.jsonl`).
