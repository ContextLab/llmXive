# Data Model: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Feature**: `001-auto-icwm-latent-dynamics`  
**Date**: 2026‑10‑14  

## Overview
The project manipulates three primary data artifacts:

1. **Interaction Clip** – raw simulation episode (`.npz` with `states`, `actions`, `observations`).  
2. **Latent Descriptor** – per‑clip statistical summary (variance, autocorr_lag1, spectral_density).  
3. **Hyperparameter Label** – optimal `(tau, k)` pair obtained from grid search (training only).  

Derived artifacts (task‑complexity, validation results) are also modeled.

## Schemas
All schemas are stored under `contracts/` and are validated by the CI.

- `contracts/descriptor.schema.yaml` – records per‑clip descriptors.  
- `contracts/label.schema.yaml` – records optimal hyperparameters per training clip.  
- `contracts/complexity.schema.yaml` – records the independent task‑complexity metric.  
- `contracts/validation_results.schema.yaml` – records zero‑shot validation outcomes.

## Data Flow
```
generate_clips.py --> data/raw/*.npz
extract_descriptors.py --> data/processed/descriptors.csv   (descriptor.schema.yaml)
grid_search_labels.py --> data/processed/labels.csv       (label.schema.yaml)
compute_complexity.py --> data/processed/task_complexity.csv (complexity.schema.yaml)
train_regressor.py --> model/regressor.pt
validate_autocwm.py --> results/validation_results.csv   (validation_results.schema.yaml)
```

All CSV files are UTF‑8, comma‑separated, with headers matching schema field names.

---

