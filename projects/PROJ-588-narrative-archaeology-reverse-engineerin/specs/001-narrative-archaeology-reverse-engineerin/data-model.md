# Data Model: Narrative Archaeology

## 1. Overview

This document defines the data structures, schemas, and flow for the Narrative Archaeology project. The data model supports the ingestion of raw fMRI data, the preprocessing into clean timecourses, the segmentation of events, and the storage of model outputs.

## 2. Data Flow

1.  **Raw Data**: Downloaded from OpenNeuro ds000234 (BIDS format).
2.  **Preprocessed Data**: fMRIPrep outputs (NIfTI, confounds JSON).
3.  **Segmented Data**: Timecourses aligned with event labels (CSV/Parquet).
4.  **Semantic Features**: Text embeddings (Parquet).
5.  **Model Outputs**: Weights, predictions, and metrics (JSON/Parquet).

## 3. Entity Definitions

### 3.1 Subject
- **ID**: Unique identifier (e.g., `sub-01`).
- **Metadata**: Age, sex, handedness (from BIDS participants.tsv).

### 3.2 Session
- **Type**: `encoding` (listening) or `recognition` (delayed task).
- **Duration**: Length of the fMRI run in seconds.

### 3.3 Event
- **ID**: Unique event identifier.
- **Type**: `plot`, `character`, `theme`, `misc`.
- **Onset**: Start time in seconds (relative to scan start).
- **Duration**: Duration in seconds.
- **Text**: The specific story segment text.

### 3.4 NeuralPattern
- **SubjectID**: Reference to Subject.
- **SessionID**: Reference to Session.
- **EventID**: Reference to Event.
- **ROI**: Region of Interest (e.g., `hippocampus`).
- **Vector**: Array of voxel values (flattened).

### 3.5 DecodingModel
- **Type**: `ridge`, `svm`.
- **Target**: `plot`, `character`, `theme`.
- **Weights**: Model coefficients.
- **Metrics**: Accuracy, F1, Permutation p-value.

## 4. File Formats

- **Raw**: BIDS (NIfTI, JSON).
- **Processed**: NIfTI (MNI space), JSON (confounds).
- **Derived**: Parquet (high-performance, columnar storage for timecourses and labels).
- **Models**: JSON (weights) or Pickle (serialized sklearn models).

## 5. Constraints

- **PII**: No raw demographic data with names/IDs stored. Only anonymized subject IDs.
- **Checksums**: All files in `data/` must have a corresponding `.sha256` file.
- **Versioning**: All derived data files must include a `version` field in their metadata.
