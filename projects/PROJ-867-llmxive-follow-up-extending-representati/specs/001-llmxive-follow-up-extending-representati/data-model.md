# Data Model: llmXive follow-up: extending Representation Forcing for Structured Text Generation

## 1. Overview

This document defines the data structures, flows, and schemas used in the `llmXive` follow-up project. The data model supports the extraction of RF tokens, training of autoregressive models, and evaluation of structured text generation.

## 2. Data Flow

1.  **Raw Data**: Document images (PNG/JPG) and annotations (JSON/Parquet) from PubLayNet.
2.  **Preprocessing**:
    -   **RF Token Extraction**: Raw images -> Frozen RF Encoder (`layoutlmv3`) -> `rf_token_sequence` (padded/truncated to 512 tokens).
    -   **Pixel Baseline**: Raw images -> Downsampling -> `pixel_matrix`.
    -   **Ground Truth**: Annotations -> Parsed JSON/Markdown (canonical schema) -> `structured_text`.
3.  **Training**: `rf_token_sequence` + `structured_text` -> RF Model -> `predictions`.
4.  **Evaluation**: `predictions` vs. `structured_text` -> `metrics` (validity, AST distance, runtime).

## 3. Entity Definitions

### 3.1 RF Token Sequence
- **Description**: A sequence of continuous vectors representing the structural priors of a document image, extracted by the frozen RF encoder.
- **Dimensions**: `[batch_size, sequence_length, embedding_dim]` (fixed `sequence_length` = 512).
- **Source**: Output of `rf_encoder.forward(image)`.
- **Constraints**: Must be normalized (mean=0, std=1) if required by the downstream model.

### 3.2 Structured Text Output
- **Description**: The generated text (JSON, Markdown, or AST) predicted by the autoregressive model.
- **Format**: String (valid JSON/Markdown).
- **Validation**: Must pass parser acceptance (e.g., `json.loads()`) and match canonical ground truth content.

### 3.3 Pixel Matrix
- **Description**: Downsampled raw image pixels used for the baseline model.
- **Dimensions**: `[batch_size, channels, height, width]` (e.g., 3x224x224).
- **Source**: Raw image resized and normalized.

### 3.4 Evaluation Metrics
- **Description**: Aggregated results from the evaluation phase.
- **Fields**:
    -   `syntactic_validity_rate`: Float (0.0-1.0).
    -   `ast_edit_distance`: Float (average distance).
    -   `complexity_overflow_rate`: Float (0.0-1.0).
    -   `truncation_rate`: Float (0.0-1.0).
    -   `p_value_validity`: Float (from McNemar's test).
    -   `p_value_ast`: Float (from Wilcoxon test).
    -   `total_runtime_seconds`: Float (total time for training and evaluation).

## 4. Data Storage

- **Raw Data**: Stored in `data/raw/` with checksums.
- **Processed Data**: Stored in `data/processed/` (e.g., `rf_tokens.parquet`, `pixel_matrices.npz`).
- **Results**: Stored in `data/results/` (e.g., `metrics.json`, `predictions.jsonl`).

## 5. Schema Contracts

See `contracts/` directory for formal YAML schemas:
- `rf_token_sequence.schema.yaml`
- `structured_text_output.schema.yaml`
- `evaluation_metrics.schema.yaml`