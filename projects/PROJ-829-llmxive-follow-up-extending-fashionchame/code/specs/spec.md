# Specification: llmXive Follow-Up - Extending FashionChame

## 1. Introduction
This document defines the requirements for extending the FashionChame project to support text-driven garment fidelity benchmarking using the DeepFashion2 dataset.

## 2. Functional Requirements

### FR-002: Data Ingestion
The system must ingest the **DeepFashion2** dataset.
- **Input**: DeepFashion2 parquet files via HuggingFace `datasets` library.
- **Constraint**: Must use streaming mode (`streaming=True`) to handle large dataset sizes without full memory loading.
- **Exclusion**: Human3.6M is explicitly excluded; all data processing must target DeepFashion2 schema.

### FR-010: Motion Labeling
The system must derive motion labels for video frames to categorize motion intensity.
- **Method**: Calculate **optical flow magnitude** from consecutive video frames.
- **Logic**:
 - High Motion: Optical flow magnitude > threshold (configurable).
 - Low Motion: Optical flow magnitude <= threshold.
- **Exclusion**: Skeletal joint velocity is explicitly excluded as it is unavailable in DeepFashion2.

### FR-011: Feature Stratification
The system must tag clips by `GarmentFeatureClass` (color, pattern, texture) using **DeepFashion2** metadata fields.
- **Input**: DeepFashion2 annotation files containing garment attributes.
- **Output**: Filtered dataset manifest with feature class tags.

## 3. Non-Functional Requirements

### NFR-001: Performance
- Inference latency per frame must be under 50ms on standard CPU hardware.
- Memory usage must not exceed 6.5 GB during processing (triggers batched streaming).

### NFR-002: Reproducibility
- All experiments must be deterministic given the same seed and configuration.
- Random seeds must be configurable via `settings.yaml`.

## 4. Assumptions
1. The **DeepFashion2** dataset provides sufficient metadata for garment attribute classification (color, pattern, texture).
2. **Optical flow magnitude** is a valid proxy for "motion intensity" in the context of garment deformation, replacing skeletal velocity.
3. The HuggingFace `datasets` library provides a stable streaming interface for DeepFashion2 parquet files.
4. CPU-only execution is the primary target for inference benchmarking.

## 5. Constraints
- No synthetic data generation or fallbacks are permitted.
- All code must run on Python 3.11+.
- No CUDA dependencies for the benchmarking pipeline.
