# Data Model: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Feature**: `001-auto-icwm-latent-dynamics`  
**Date**: 2026‑10‑19  

## Overview
The project manipulates four primary data artifacts:

1. **Interaction Clip** – raw simulation episode (`.npz` containing `states`, `actions`, `observations`).  
2. **Latent Descriptor** – per‑clip statistical summary (variance, autocorr_lag1, spectral_density).  
3. **Hyperparameter Label** – optimal `(tau, k)` pair obtained from grid search (training clips only).  
4. **Task‑Complexity Record** – number of distinct sub‑goals for the clip’s environment.  

Derived artifacts (validation results, correlation reports) are also modeled.

## Schemas (validated by CI)
All schemas reside under `specs/001-auto-icwm-latent-dynamics/contracts/`:

- `descriptor.schema.yaml` – records per‑clip descriptors.  
- `label.schema.yaml` – records optimal hyperparameters and success rate.  
- `complexity.schema.yaml` – records the independent task‑complexity metric.  
- `validation_results.schema.yaml` – records zero‑shot validation outcomes, including **auto_success_rate**, **baseline_success_rate**, and the derived **success_diff** binary indicator.

## Data Flow Diagram
```
generate_clips.py
   └─> data/raw/clip_<id>.npz
        |
        v
icwm_encoder.py  (CPU‑only)
        |
        v
extract_descriptors.py
   └─> data/processed/descriptors.csv   (descriptor.schema.yaml)

grid_search_labels.py
   └─> data/processed/labels.csv        (label.schema.yaml)

compute_complexity.py
   └─> data/processed/task_complexity.csv (complexity.schema.yaml)

train_regressor.py
   └─> model/regressor.pt

validate_autocwm.py
   └─> results/validation_results.csv (validation_results.schema.yaml)

correlation_analysis (part of validate_autocwm.py)
   └─> results/correlation_report.md
```

All CSV files are UTF‑8, comma‑separated, with headers matching the schema field names. Files are checksum‑recorded (`sha256`) under `data/checksums.json` for data‑hygiene compliance.

---  

## Consistency Note
The validation results schema now explicitly captures **aggregated success rates** (`auto_success_rate`, `baseline_success_rate`) as required by the revised statistical analysis in the implementation plan.
