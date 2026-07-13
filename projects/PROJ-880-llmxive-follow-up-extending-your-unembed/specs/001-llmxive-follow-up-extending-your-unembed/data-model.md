# Data Model: llmXive Follow-up: Extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Overview

This document defines the data structures, file formats, and schema contracts for the llmXive follow-up project. All data is stored in `data/` and validated against `contracts/*.schema.yaml`.

## 2. Data Flow

1.  **Raw Frequency Data**: Downloaded from Hugging Face (RedPajama, CC100).
2.  **Model Weights**: Loaded from Hugging Face Hub (Llama-3, BLOOM, Qwen).
3.  **Edge Spectrum**: SVD output (singular values, vectors) saved as CSV.
4.  **Average Vectors**: Frequency-weighted sums saved as CSV.
5.  **Alignment Results**: Procrustes rotation matrices and aligned vectors.
6.  **Statistical Results**: Cosine similarities, p-values, and sensitivity analysis.

## 3. File Specifications

### 3.1 Frequency Lists
*   **Path**: `data/raw/freq_{lang}.csv`
*   **Format**: CSV with headers `token_id`, `token_str`, `frequency`.
*   **Encoding**: UTF-8.
*   **Checksum**: SHA-256 stored in `state/...yaml`.

### 3.2 Edge Spectrum (SVD Output)
*   **Path**: `data/processed/svd_{model}.csv`
*   **Format**: CSV.
*   **Columns**: `component_id`, `singular_value`, `vector_{d}` (flattened vector of dimension D).
*   **Note**: Only top 50 components are stored.

### 3.3 Average Token Vectors
*   **Path**: `data/processed/avg_vec_{lang}_{model}.csv`
*   **Format**: CSV.
*   **Columns**: `vector_{d}` (flattened vector).
*   **Metadata**: JSON sidecar `data/processed/avg_vec_{lang}_{model}.meta.json` containing `language`, `model`, `frequency_source`, `checksum`.

### 3.4 Alignment Results
*   **Path**: `data/processed/alignment_{src}_{tgt}.json`
*   **Format**: JSON.
*   **Fields**: `rotation_matrix` (flattened), `translation_vector` (flattened), `cost`, `source_lang`, `target_lang`.

### 3.5 Statistical Results
*   **Path**: `data/results/stats_{pair}.csv`
*   **Format**: CSV.
*   **Columns**: `pair`, `observed_sim`, `p_value_n100`, `p_value_n1000`, `p_value_n10000`, `convergence_status`.

## 4. Data Hygiene Rules

*   **Immutability**: Raw files in `data/raw/` are never modified.
*   **Derivation**: All derived files (SVD, averages) must include a `derived_from` field in their metadata pointing to the source file hash.
*   **PII**: No personal data is expected in frequency lists or model weights. If detected, the pipeline halts.

## 5. Schema Contracts

The following schemas are defined in `contracts/` and enforced by the `data_ingestion.py` and `report.py` scripts.

*   `contracts/frequency_list.schema.yaml`: Validates raw frequency data.
*   `contracts/svd_output.schema.yaml`: Validates SVD results.
*   `contracts/statistical_results.schema.yaml`: Validates final p-values and similarities.
