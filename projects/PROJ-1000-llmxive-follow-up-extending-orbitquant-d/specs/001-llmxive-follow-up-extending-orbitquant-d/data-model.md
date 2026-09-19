# Data Model: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

## Overview

This document defines the data structures, schemas, and storage formats for the project. All data is stored in `data/` with checksums recorded in `state/`.

## Data Flows

1.  **Raw Ingestion**: MS-COCO parquet files downloaded from Hugging Face.
2.  **Prompt Extraction**: Captions extracted from MS-COCO parquet to serve as prompts.
3.  **Generation & Activation Extraction**: **Generative** forward passes (conditioned on caption only) generate activation histograms (saved as `.npy` or `.parquet`).
4.  **Entropy Calculation**: Captions processed via generative proxy to generate entropy scores (saved as `.json` or `.csv`).
5.  **Model Artifacts**: 16 Rotation matrices saved as `.pt` or `.npy`.
6.  **Results**: Metrics (FID, CLIP, Time) aggregated into a final results CSV.
7.  **Validation**: `clustering_report.json` generated for Phase 2 gating.

## Entity Definitions

### 1. Prompt Metadata
- **Source**: MS-COCO Captions.
- **Fields**: `prompt_id` (image_id), `text` (caption), `semantic_entropy`.

### 2. Activation Statistics
- **Source**: DiT **generative** pass (conditioned on prompt).
- **Fields**: `prompt_id`, `image_id`, `layer_name`, `variance`, `histogram_bins`, `generation_seed`.

### 3. Rotation Matrices
- **Source**: K-Means clustering on **Entropy** (bins) -> Activation histograms (centroids) of **generated** trajectories.
- **Fields**: `cluster_id` (0-15), `matrix_data` (tensor), `entropy_range_min`, `entropy_range_max`.

### 4. Evaluation Results
- **Source**: Generation & Metrics.
- **Fields**: `prompt_id`, `method` (static/dynamic), `fid`, `clip_score`, `mse`, `inference_time`.

### 5. Clustering Report (Validation Artifact)
- **Source**: Clustering phase.
- **Fields**: `layers_used`, `dataset_split` (train/test counts), `bin_boundaries`, `matrix_indices`.

## Storage Formats

- **Raw Data**: Parquet (compressed).
- **Intermediate Stats**: NumPy (`.npy`) for arrays, JSON for metadata.
- **Final Results**: CSV for easy statistical analysis.
- **Validation Report**: `data/processed/clustering_report.json` (JSON) documenting layers and subsets.

## Data Hygiene Rules

- **Immutability**: Raw files in `data/raw/` are never modified.
- **Checksums**: SHA-256 hashes of all raw files recorded in `state/.../artifact_hashes`.
- **PII**: No personally identifiable information in prompts (filtered during download if necessary).
- **Versioning**: `state/artifact_hashes.json` updated after every run to track all output artifacts.