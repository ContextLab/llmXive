# Data Model: Predicting Battery Degradation from Public Cycling Data

## Overview
The data model defines the canonical representations used throughout the pipeline. All artifacts are stored under `data/` with explicit versioned filenames (e.g., `processed_v1.npz`). Schemas are provided as JSON‑compatible YAML contracts in `contracts/`.

> **Note:** The current implementation uses a synthetic placeholder dataset because no open battery cycling dataset with the required variables (voltage, current, temperature, final capacity fade) is available. The schemas below are defined for the intended real data; when a suitable dataset is obtained, the same schemas will apply without modification. The placeholder data will still conform to these schemas (with dummy values) to keep the pipeline runnable.

## Entities

| Entity | Description | Fields |
|--------|-------------|--------|
| **BatteryCell** | Raw representation of a single cell as read from the source CSVs. | `cell_id: string`<br>`protocol_type: string`<br>`voltage_trace: list[float]` (flattened across cycles)<br>`current_trace: list[float]`<br>`temperature_trace: list[float]`<br>`initial_capacity: float`<br>`final_capacity: float` |
| **SequenceWindow** | Processed input sequence for model consumption. | `cell_id: string`<br>`input_sequence: ndarray[float]` shape `(50, 100, 3)` (cycles, timesteps, channels)<br>`target_fade: float` (computed per spec) |
| **ModelPrediction** | Output of the trained Bi‑LSTM for a given cell. | `cell_id: string`<br>`predicted_fade: float`<br>`confidence_interval: tuple[float, float]` (lower, upper, 90 % CI)<br>`shap_scores: list[float]` length `50*100*3` (optional) |
| **BaselineFeatureSet** | Hand‑crafted incremental‑capacity features used for the baseline linear model. | `cell_id: string`<br>`features: dict[string, float]` (e.g., `ic_10`, `ic_20`, …)<br>`target_fade: float` |

## Contracts

### `contracts/processed_dataset.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Processed Battery Sequence Dataset"
description: "Tensor dataset produced after ingestion and preprocessing, ready for model training."
type: object
required:
  - version
  - generated_at
  - sequences
  - targets
properties:
  version:
    type: string
    description: "Semantic version of the processing pipeline (e.g., 'v1.0.0')."
  generated_at:
    type: string
    format: date-time
    description: "UTC timestamp when the file is created."
  sequences:
    type: array
    description: "List of input tensors, each of shape (50, 100, 3) representing 50 cycles, 100 timesteps per cycle, and 3 channels."
    items:
      type: array
      items:
        type: array
        items:
          type: array
          items:
            type: number
  targets:
    type: array
    description: "Corresponding scalar capacity‑fade targets."
    items:
      type: number
  cell_ids:
    type: array
    description: "Original cell identifiers aligned with sequences/targets."
    items:
      type: string
```

### `contracts/model_output.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Prediction Output"
description: "Predictions and uncertainty intervals for each test cell."
type: object
required:
  - predictions
  - ci_coverage
properties:
  predictions:
    type: array
    description: "List of prediction records."
    items:
      type: object
      required:
        - cell_id
        - predicted_fade
        - ci_lower
        - ci_upper
      properties:
        cell_id:
          type: string
        predicted_fade:
          type: number
        ci_lower:
          type: number
        ci_upper:
          type: number
        shap_scores:
          type: array
          description: "Optional SHAP values aligned with input features."
          items:
            type: number
  ci_coverage:
    type: number
    description: "Proportion of true targets falling within the 90 % confidence intervals."
```

These schemas are used by `tests/contract/` to validate that generated artifacts conform to the expected structure.
