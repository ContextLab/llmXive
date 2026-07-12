# Data Model: LLMXive Follow-up: Latent Anomaly Detection

## Overview
This document defines the data structures, schemas, and relationships used in the LLMXive follow-up project. The data flow moves from raw audio files to processed embeddings, then to model artifacts and evaluation metrics.

## Entities

### 1. RawDataset
Represents the raw data downloaded from verified sources.
- **Source**: Verified URLs (LALM Adversarial subsets, Benign TTS).
- **Format**: Parquet files (containing audio bytes or paths, labels, text).
- **Transformation**: Raw audio is decoded and resampled; labels are mapped to binary `0` (benign) / `1` (jailbreak) **only after validation**.

### 2. AudioEmbedding
The core data product: a fixed-dimensional vector representing an audio sample.
- **Input**: Raw audio (16kHz, mono).
- **Output**: Numpy array of shape `(768,)` (for Distil-Whisper Base).
- **Attributes**:
  - `sample_id`: Unique identifier.
  - `embedding`: Vector (768 dimensions).
  - `label`: Binary (0/1).
  - `source`: Dataset name.
  - `error`: If processing failed, stores the error message (FR-005).
  - `split`: "train" or "test" (assigned before statistical calculation).

### 3. AnomalyScore
Derived metric for each sample.
- **Input**: `AudioEmbedding` + Benign Centroid (from Train set) + Covariance (from Train set).
- **Output**: Scalar float (Mahalanobis distance).
- **Attributes**:
  - `sample_id`: Matches `AudioEmbedding`.
  - `distance`: Float.
  - `is_outlier`: Boolean (if distance > threshold).
  - `reference_distribution`: "benign_train" or "random_noise".

### 4. ClassifierModel
The trained Logistic Regression artifact.
- **Input**: `AudioEmbedding` (training set).
- **Output**: `sklearn` pickle file.
- **Attributes**:
  - `weights`: Array.
  - `intercept`: Float.
  - `class_distribution`: Dict (train set class counts).
  - `covariance_regularization`: "LedoitWolf".

### 5. EvaluationReport
The final output containing metrics and logs.
- **Input**: Predictions vs. Ground Truth.
- **Output**: JSON/Markdown report.
- **Attributes**:
  - `precision`, `recall`, `f1`: Floats.
  - `baseline_f1`: Float (stratified random).
  - `correlation_r`: Float (Pearson r for Mahalanobis).
  - `p_value`: Float.
  - `resource_log`: Dict (RAM, Time).
  - `random_noise_baseline`: Dict (distance stats for noise).

## Data Flow Diagram

```mermaid
graph TD
    A[Raw Parquet Datasets] -->|Download & Verify| B(Preprocessing)
    B -->|Decode Audio | C[AudioLoader]
    C -->|Batch Extract | D[Encoder: Distil-Whisper]
    D -->|Embeddings | E[AudioEmbedding Table]
    E -->|Split 80/20 | F[Train Set]
    E -->|Split 20% | G[Test Set]
    F -->|Compute Stats (LedoitWolf)| H[Benign Centroid/Cov]
    F -->|Generate Noise| I[Random Noise Vectors]
    E -->|Calculate (Train Stats)| J[AnomalyScore Table]
    I -->|Calculate (Train Stats)| K[Noise AnomalyScore]
    F -->|Train | L[ClassifierModel]
    L -->|Predict | M[Test Predictions]
    M -->|Compare| N[EvaluationReport]
    K -->|Compare| N
```

## Storage Strategy
- **Raw Data**: `data/raw/` (Parquet). Read-only.
- **Processed Data**: `data/processed/` (Parquet for embeddings, JSON for scores).
- **Models**: `models/` (Pickle/Joblib).
- **Results**: `results/` (JSON, Markdown).
- **State**: `state/` (YAML for versioning/hashes).

## Schema Definitions
See `contracts/` directory for detailed YAML schemas:
- `dataset.schema.yaml`: Validates raw/processed dataset structure.
- `embedding.schema.yaml`: Validates embedding vectors and metadata.