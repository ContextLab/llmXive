# Data Model: llmXive Follow-up: Extending "JoyAI-VL-Interaction"

## Overview
This document defines the data structures for the synthetic video generation, feature extraction, visual baseline, and scheduler training pipeline. All data is stored in JSONL or NumPy formats for efficient streaming and processing.

## Entities

### 1. SyntheticVideoFrame
Represents a single frame from the generated video stream with its ground-truth label.
- **frame_id**: Unique identifier (string).
- **timestamp**: Float (seconds from start).
- **visual_data_path**: Relative path to the image file in `data/raw/`.
- **ground_truth_label**: String (`"critical"` or `"silence"`).
- **event_type**: String (e.g., `"fall"`, `"alarm"`, `"conversation"`).
- **confidence_score**: Float (confidence of the visual detector).
- **source**: String (`"synthetic_generator"`).
- **noise_applied**: Boolean (True if jitter/noise was applied to this frame).

### 2. InternalStateVector
Represents the extracted hidden state and attention map data for a specific frame.
- **frame_id**: String (links to `SyntheticVideoFrame`).
- **hidden_state_embedding**: List of floats (flattened vector).
- **attention_map**: List of floats (flattened attention weights).
- **layer_index**: Integer (which layer of the VLM was extracted).
- **extraction_timestamp**: Float (timestamp of extraction).
- **dimensions**: Object `{ "hidden": int, "heads": int, "seq_len": int }`.

### 3. VisualBaselineDecision
Represents the output of the Noisy Rule-Based Visual Detector.
- **frame_id**: String (links to `SyntheticVideoFrame`).
- **prediction**: String (`"trigger"` or `"suppress"`).
- **probability**: Float (0.0 to 1.0, derived from visual confidence).
- **latency_ms**: Float (inference time).
- **ground_truth_label**: String (for evaluation).
- **metric_contribution**: Object `{ "interruption_reduction": bool, "safety_recall": bool }`.

### 4. SchedulerDecision
The output of the lightweight classifier for a specific time step.
- **frame_id**: String.
- **prediction**: String (`"trigger"` or `"suppress"`).
- **probability**: Float (0.0 to 1.0).
- **latency_ms**: Float (inference time).
- **ground_truth_label**: String (for evaluation).
- **metric_contribution**: Object `{ "interruption_reduction": bool, "safety_recall": bool }`.

### 5. MutualInfoResult
Stores the results of the Mutual Information calculation.
- **feature_source**: String (`"internal_state"` or `"visual_features"`).
- **mi_score**: Float (Mutual Information value).
- **p_value**: Float (significance from permutation test).
- **sample_size**: Integer (number of samples used).

## Data Flow

1.  **Generation**: `generator.py` produces `SyntheticVideoFrame` entries in `data/raw/` and logs them to `data/manifest.jsonl`.
2.  **Labeling**: `visual_labeler.py` updates the manifest with `ground_truth_label` and `event_type`.
3.  **Baseline**: `visual_detector.py` reads `SyntheticVideoFrame` and writes `VisualBaselineDecision` to `data/baseline/`.
4.  **Extraction**: `extractor.py` reads `SyntheticVideoFrame`, queries the VLM (CPU mode), and writes `InternalStateVector` to `data/features/`.
5.  **Training**: `train.py` reads `InternalStateVector` and `ground_truth_label` to train the model.
6.  **Evaluation**: `eval.py` produces `SchedulerDecision` entries, calculates Mutual Information, and computes metrics.

## Storage Schema (JSONL)

### `data/manifest.jsonl`
```json
{
  "frame_id": "vid_001_frame_123",
  "timestamp": 12.3,
  "visual_data_path": "data/raw/vid_001/frame_123.png",
  "ground_truth_label": "critical",
  "event_type": "fall",
  "confidence_score": 0.98,
  "source": "synthetic_generator",
  "noise_applied": true
}
```

### `data/features/vid_001_features.jsonl`
```json
{
  "frame_id": "vid_001_frame_123",
  "hidden_state_embedding": [0.12, -0.45, ...],
  "attention_map": [0.05, 0.92, ...],
  "layer_index": 12,
  "extraction_timestamp": 1689123456.789,
  "dimensions": { "hidden": 768, "heads": 12, "seq_len": 64 }
}
```

### `data/baseline/vid_001_baseline.jsonl`
```json
{
  "frame_id": "vid_001_frame_123",
  "prediction": "trigger",
  "probability": 0.85,
  "latency_ms": 12.5,
  "ground_truth_label": "critical",
  "metric_contribution": { "interruption_reduction": false, "safety_recall": true }
}
```

### `data/evaluation/results.jsonl`
```json
{
  "frame_id": "vid_001_frame_123",
  "prediction": "trigger",
  "probability": 0.92,
  "latency_ms": 45.2,
  "ground_truth_label": "critical",
  "metric_contribution": { "interruption_reduction": false, "safety_recall": true }
}
```

### `data/evaluation/mi_results.jsonl`
```json
{
  "feature_source": "internal_state",
  "mi_score": 0.45,
  "p_value": 0.001,
  "sample_size": 10000
}
```

## Data Hygiene & Versioning
- **Checksums**: All files in `data/raw/`, `data/features/`, `data/baseline/`, and `data/evaluation/` are checksummed (SHA-256) upon generation.
- **Immutability**: Raw data is never modified. If a labeler logic changes, a new manifest is generated with a new suffix (e.g., `manifest_v2.jsonl`).
- **PII**: Synthetic data contains no real PII. All generated identities are random strings.