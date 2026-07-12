# Data Model: llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

## Overview

This document defines the data structures used in the research pipeline, focusing on the synthetic image generation, inference results, and regression analysis outputs. All data is stored in JSON or CSV formats for portability and verification.

## Entities

### 1. SyntheticImage
Represents a generated test case with non-overlapping bounding boxes.
*   **Fields**:
    *   `image_id`: Unique string identifier.
    *   `source_image_path`: Path to the base image.
    *   `region_count`: Integer (20, 30, or 50).
    *   `bounding_boxes`: List of objects `{x, y, width, height}`.
    *   `ground_truth_relations`: List of objects `{box_a_id, box_b_id, relation}` (e.g., "left_of").

### 2. InferenceResult
Stores the output of a single inference run (Parallel or Sequential).
*   **Fields**:
    *   `image_id`: Reference to `SyntheticImage`.
    *   `method`: String ("parallel" or "sequential").
    *   `captions`: List of strings (one per region).
    *   `inference_time_ms`: Float.
    *   `geometric_consistency_score`: Float (0.0 - 1.0).
    *   `bleu4_score`: Float.

### 3. RegressionRecord
Aggregated data point for the degradation curve.
*   **Fields**:
    *   `region_count`: Integer.
    *   `method`: String.
    *   `mean_geometric_consistency`: Float.
    *   `std_geometric_consistency`: Float.
    *   `mean_time_ms`: Float.

## Storage Locations

*   `data/synthetic/`: Contains `synthetic_image_{id}.png` and `annotation_{id}.json`.
*   `data/processed/inference_results.json`: Aggregated results from Phase 2.
*   `data/processed/regression_data.csv`: Final data for plotting.