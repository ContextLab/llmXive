# Data Model: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The project manipulates three primary data artefacts:

1. **Raw Dataset** – original HEA yield‑strength CSV (composition, measured yield strength, phase, testing temperature).  
2. **Descriptor Table** – deterministic compositional descriptors derived from the raw dataset, plus covariates `phase` and `testing_temperature`.  
3. **Model Output** – predictions, residuals, and performance metrics.

All artefacts are version‑controlled, checksum‑recorded, and validated against JSON‑Schema contracts located in `contracts/`.

## Schema: `contracts/descriptor.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Descriptor Table"
description: "Row‑wise deterministic descriptors for each alloy composition."
type: object
properties:
  composition:
    type: string
    description: "Alloy composition formula (e.g., 'CoCrFeMnNi')."
  mixing_entropy:
    type: number
    description: "Configurational mixing entropy (J mol⁻¹ K⁻¹)."
  atomic_size_mismatch:
    type: number
    description: "δ, atomic size mismatch (dimensionless)."
  electronegativity_variance:
    type: number
    description: "Δχ, variance of Pauling electronegativities."
  vec:
    type: number
    description: "Valence electron concentration (electrons per atom)."
  tm_variance:
    type: number
    description: "Variance of melting temperatures of constituent elements."
  phase:
    type: string
    description: "Phase structure (e.g., 'Single‑phase', 'BCC')."
  testing_temperature:
    type: number
    description: "Testing temperature in Celsius."
required:
  - composition
  - mixing_entropy
  - atomic_size_mismatch
  - electronegativity_variance
  - vec
  - tm_variance
  - phase
  - testing_temperature
additionalProperties: false
```

## Schema: `contracts/model_output.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Output"
description: "Predictions, residuals, and performance metrics for the HEA yield‑strength model."
type: object
properties:
  predictions:
    type: array
    items:
      type: number
    description: "Predicted yield strength values (same order as input)."
  actual:
    type: array
    items:
      type: number
    description: "Measured yield strength values."
  residuals:
    type: array
    items:
      type: number
    description: "Actual minus predicted."
  r2_score:
    type: number
    description: "Mean cross‑validated R²."
  r2_ci_95:
    type: array
    items:
      type: number
    minItems: 2
    maxItems: 2
    description: "Lower and upper bounds of the 95 % bootstrap confidence interval for R² at a conventional confidence level."
  permutation_importance:
    type: object
    description: "Feature importance values and p‑values."
    additionalProperties:
      type: object
      properties:
        importance:
          type: number
        p_value:
          type: number
      required:
        - importance
        - p_value
required:
  - predictions
  - actual
  - residuals
  - r2_score
  - r2_ci_95
  - permutation_importance
additionalProperties: false
```

## Checksum Recording
Every artefact stored under `data/` will have its SHA‑256 checksum recorded in `state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml` under the `artifact_hashes` map. The `code/utils/checksums.py` module provides `record_checksum(path)` and `verify_checksum(path, expected)` utilities used throughout the pipeline.

## Derivation Traceability
- **Raw → Descriptor**: `compute_descriptors.py` reads `data/raw/hea_yield_strength.csv` and writes `data/derived/descriptors.csv`. The output checksum is stored and linked to the input checksum.
- **Descriptor → Model**: `train_model.py` consumes `descriptors.csv` and writes `data/derived/model_artifact.pkl`. Both input and output checksums are recorded.
- **Model → Report**: `generate_report.py` pulls `model_artifact.pkl` and `descriptors.csv` to compute metrics and embed figures; the final `reports/report.md` checksum is also stored.

## Contract Validation Steps (added)
- **Raw Dataset Validation**: After download, `code/download_data.py` validates the raw CSV against `contracts/dataset.schema.yaml`.  
- **Elemental Property Table Validation**: `code/compute_descriptors.py` validates `data/element_properties.csv` against `contracts/elemental_properties.schema.yaml`.  
- **HEA Composition Validation**: The merged composition object is validated against `contracts/hea_composition.schema.yaml`.  
- **Processed Data Validation**: The final processed dataset (including descriptors and covariates) is validated against `contracts/processed_data.schema.yaml`.  
- **Model Output Validation**: After training and evaluation, `code/generate_report.py` validates the JSON output against `contracts/model_output.schema.yaml`.  
- **Metrics Validation**: Bootstrap CI, permutation importance, and VIF results are validated against `contracts/metrics.schema.yaml` and `contracts/model_metrics.schema.yaml`.  

All validations are performed before any downstream analysis, satisfying **Principle III (Data Hygiene)** and **Principle IV (Single Source of Truth)**.

## Data Hygiene & Single Source of Truth
- No in‑place modifications; each transformation writes a new file with a documented derivation step.  
- Every figure, statistic, or interpretation in the paper traces back to a single row in `data/` and a single block in `code/`.

---


