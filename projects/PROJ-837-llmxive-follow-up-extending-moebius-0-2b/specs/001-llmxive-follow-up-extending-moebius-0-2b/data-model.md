# Data Model: llmXive follow-up: extending "Moebius: 0.2B Lightweight Image Inpainting Framework with 10B-Level Pe"

## 1. Overview

This document defines the data schemas for the `llmXive-moebius-dynamic` project. All data artifacts must adhere to these schemas to ensure reproducibility and data hygiene (Constitution III).

## 2. Core Entities

### 2.1. MaskedRegion
Represents a specific masked area in an image.
- **image_id**: Unique identifier for the source image (string).
- **mask_geometry**: JSON object describing the mask shape (e.g., coordinates of a rectangle or polygon).
- **gradient_variance**: Float, calculated variance of gradients within the masked region.
- **texture_entropy**: Float, calculated entropy of pixel intensities within the masked region.
- **human_complexity_score**: Float (1.0 to 5.0), the average human-rated score (Likert scale).
- **mask_coverage_ratio**: Float (0.0 to 1.0), the ratio of masked pixels to total pixels.
- **krippendorff_alpha**: Float (optional), inter-rater reliability metric (if multiple raters).

### 2.2. InferenceResult
Represents the output of a model run for a specific sample.
- **model_type**: String, either "dynamic" or "static".
- **latency_ms**: Float, wall-clock inference time in milliseconds.
- **fid_score**: Float, Fréchet Inception Distance.
- **lpiPS_score**: Float, Learned Perceptual Image Patch Similarity.
- **complexity_bin**: Integer (1-5), the bin corresponding to the ground truth score.
- **active_matrix_rank**: Integer, the rank used by the dynamic model for this sample.

### 2.3. GatingState
Internal state of the gating mechanism during inference.
- **input_context_features**: Array of floats (flattened feature vector).
- **predicted_complexity**: Float, the output of the gating head.
- **active_matrix_rank**: Integer, the resulting rank after modulation.

## 3. File Schemas

### 3.1. Human Annotations (`data/annotations/human_scores.csv`)
CSV file containing human-rated complexity scores (or decoupled synthetic scores).

| Column | Type | Description |
| :--- | :--- | :--- |
| `image_id` | string | Unique ID for the image. |
| `mask_id` | string | Unique ID for the specific mask. |
| `participant_id` | string | ID of the simulated/real participant. |
| `score` | integer | Likert score (1-5). |
| `timestamp` | string | ISO 8601 timestamp of annotation. |
| `krippendorff_alpha` | float | Inter-rater reliability (if applicable). |

### 3.2. Mask Metrics (`data/processed/mask_metrics.json`)
JSON file containing synthetic metrics for each masked region.

```json
[
  {
    "image_id": "string",
    "mask_id": "string",
    "gradient_variance": 0.123,
    "texture_entropy": 4.56,
    "mask_coverage_ratio": 0.15,
    "mask_geometry": { "type": "rectangle", "x": 10, "y": 20, "w": 50, "h": 50 }
  }
]
```

### 3.3. Evaluation Results (`data/results/evaluation_report.json`)
JSON file containing aggregated evaluation metrics.

```json
{
  "metadata": {
    "model_version": "string",
    "dataset_subset": "string",
    "cpu_cores": 2,
    "timestamp": "ISO 8601",
    "mode": "CI_Simulation" | "Research_Human"
  },
  "latency": {
    "dynamic_low_complexity": { "mean_ms": 0.0, "std_ms": 0.0 },
    "static_baseline": { "mean_ms": 0.0, "std_ms": 0.0 },
    "reduction_percent": 0.0
  },
  "quality": {
    "fid": { "dynamic": 0.0, "static": 0.0, "difference": 0.0 },
    "lpiPS": { "dynamic": 0.0, "static": 0.0, "difference": 0.0 }
  },
  "statistics": {
    "t_test_p_value": 0.0,
    "correlation_proxy_human": 0.0,
    "spearman_rank_correlation": 0.0,
    "statistical_power": 0.0,
    "permutation_test_p_value": 0.0
  },
  "ablation": {
    "dynamic_vs_static_low_rank": { "latency_diff": 0.0, "quality_diff": 0.0 },
    "prediction_overhead": 0.0
  }
}
```

## 4. Data Flow

1.  **Ingestion**: `data/loader.py` reads raw images from `data/raw/`.
2.  **Masking**: `data/mask_generator.py` creates masks and computes synthetic metrics, writing to `data/processed/mask_metrics.json`.
3.  **Annotation**: `data/annotator.py` generates `data/annotations/human_scores.csv` (Decoupled or Human).
4.  **Training**: `code/training/train_gating.py` reads metrics and annotations to train the gating head.
5.  **Evaluation**: `code/eval/metrics.py` runs inference, computes FID/LPIPS/Latency, and writes to `data/results/evaluation_report.json`.
6.  **Reporting**: `code/eval/report.py` reads the JSON report and generates the final paper artifacts.

## 5. Constraints & Hygiene

- **Checksums**: All files in `data/raw/` and `data/processed/` must have a `.sha256` checksum file.
- **PII**: No personally identifiable information (e.g., real participant names) in `data/annotations/`. Use anonymized IDs.
- **Immutability**: Raw data files are never modified. Derivations are written to new files.
- **Versioning**: The `state/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b.yaml` file must be updated with new artifact hashes after each data generation step.
