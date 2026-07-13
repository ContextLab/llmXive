# Data Model: llmXive follow-up: extending "DomainShuttle"

## 1. Overview

This document defines the data structures, storage formats, and relationships for the research pipeline. All data is stored in the `data/` directory, with raw data preserved and derived data versioned via content hashes.

## 2. Entity Definitions

### 2.1 Subject
A unique entity representing a video clip from WebVid-10M, characterized by a visual representation and computed metadata.

- **Attributes**:
  - `subject_id`: Unique string identifier (e.g., `webvid_001`).
  - `video_url`: Source URL in WebVid.
  - `frame_paths`: List of paths to 5 extracted keyframe images.
  - `complexity_score`: Float (0.0 - 1.0) derived from mean of 5-frame edge density/texture.
  - `raw_embedding_path`: Path to the high-dimensional tensor file.

### 2.2 CompressedVector
A reduced-dimensionality tensor derived from a Subject's embedding.

- **Attributes**:
  - `subject_id`: FK to Subject.
  - `target_dimension`: Integer (16, 24, 32, 40, 48, 64, 80, 96, 112, 128, 160, 192, 256).
  - `reconstruction_loss`: Float (Cosine similarity loss on test set).
  - `vector_path`: Path to the compressed tensor file.
  - `model_checkpoint_path`: Path to the trained Autoencoder weights for this dimension.

### 2.3 GeneratedVideo (Frames)
A set of synthetic frames generated from a CompressedVector and a text prompt.

- **Attributes**:
  - `subject_id`: FK to Subject.
  - `target_dimension`: Integer.
  - `style_domain`: String ('Anime', 'Photorealistic', 'Sketch').
  - `prompt`: Text prompt used.
  - `generated_frame_paths`: List of paths to 5 generated images.
  - `identity_score_mean`: Float (Mean CLIP similarity of 5 frames).
  - `identity_score_std`: Float (Std CLIP similarity of 5 frames).
  - `status`: String ('success', 'timeout', 'failed').

## 3. File Formats & Storage

| File Type | Format | Location | Description |
| :--- | :--- | :--- | :--- |
| **Raw Data** | Parquet | `data/raw/webvid_subset.parquet` | 100-row subset of WebVid. |
| **Keyframes** | PNG | `data/raw/frames/{subject_id}_frame_{i}.png` | Extracted reference images (5 per subject). |
| **Embeddings** | `.pt` (PyTorch) | `data/processed/embeddings/{subject_id}.pt` | High-dimensional tensors. |
| **Complexity CSV** | CSV | `data/processed/complexity_scores.csv` | Subject IDs and scores. |
| **Compressed Vectors** | `.pt` | `data/processed/compressed/{dim}/{subject_id}.pt` | Reduced tensors. |
| **Autoencoder Checkpoints** | `.pt` | `data/processed/models/{dim}.pt` | Trained AE weights. |
| **Fidelity Results** | CSV | `data/results/fidelity_scores.csv` | Aggregated scores for analysis. |
| **Plots** | PNG | `data/results/phase_transition_plot.png` | Visual output of analysis. |

## 4. Data Flow

1. **Ingestion**: `WebVid` -> `data/raw/webvid_subset.parquet`
2. **Extraction**: `webvid_subset.parquet` -> `keyframes` (5 per subject) + `embeddings` + `complexity_scores.csv`
3. **Compression**: `embeddings` + `complexity_scores.csv` -> `compressed_vectors` + `models`
4. **Generation**: `compressed_vectors` + `prompts` -> `generated_frames` (5 per video)
5. **Analysis**: `generated_frames` + `keyframes` -> `fidelity_scores.csv` -> `plots`

## 5. Integrity & Versioning

- **Checksums**: All files in `data/raw` and `data/processed` are checksummed (SHA-256) and recorded in `state/.../artifact_hashes.yaml`.
- **Immutability**: Raw data is never overwritten. Derived data is written to new filenames if the source or algorithm changes.
- **PII**: No PII is expected in WebVid metadata; a scan is run before commit.