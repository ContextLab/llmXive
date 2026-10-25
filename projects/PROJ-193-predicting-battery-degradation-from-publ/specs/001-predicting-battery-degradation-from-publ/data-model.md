# Data Model: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

## Overview
The pipeline produces two core artefacts:

1. **Processed Dataset** – ready‑to‑train tensors and metadata (`data/processed/processed_v1.npz`).  
2. **Model Output** – predictions, uncertainty intervals, and interpretability scores (`results/predictions.json`).

Both are validated against JSON‑Schema contracts in `contracts/`.

## Entities

| Entity | Description | Fields |
|--------|-------------|--------|
| **BatteryCell** | Raw per‑cell record parsed from source CSVs. | `cell_id: str`, `protocol_type: str`, `cycle_numbers: List[int]`, `voltage_trace`, `current_trace`, `temperature_trace` (per‑cycle time‑series), `per_cycle_capacity: List[float]` |
| **SequenceWindow** | Processed model input (initial set of cycles). | `cell_id: str`, `input_sequence: ndarray (N, 100, 3)`, `target_fade: float` (computed as described below) |
| **AggregatedFeatureImportance** | Summarized attribution scores. | `cell_id: str`, `per_cycle_importance: List[float]` (length 50), `per_channel_importance: Dict[str, float]` (`voltage`, `current`, `temperature`), `derived_signatures: Dict[str, float]` (e.g., voltage variance, current slope, temperature fluctuation) |
| **ModelPrediction** | Model output per test cell. | `cell_id: str`, `protocol: str`, `predicted_fade: float`, `true_fade: float`, `ci_lower: float`, `ci_upper: float`, `feature_importance_scores: AggregatedFeatureImportance` |
| **BaselineFeatureSet** | Hand‑crafted incremental‑capacity features (early cycles ‑ 50). | `cell_id: str`, `features: Dict[str, float]`, `target_fade: float` |

## Target Definition (Addressing Reviewer Feedback)
For each cell:

```
fade = (Q_initial - Q_final) / Q_initial
```

- `Q_initial` = capacity at **cycle 1**.  
- `Q_final` = capacity at **cycle 150** if the cell reaches at least 150 cycles; otherwise the capacity at the **first cycle > 100**.  
- This ensures `Q_final` lies **outside** the predictor window (cycles 1‑50) and removes label leakage.

## Splits
- **Train / Validation**: [deferred] / [deferred] stratified by `protocol_type`. Seed fixed (`seed=42`).
- **Test (held‑out protocol)**: Entire protocol families not present in training, guaranteeing **≥ 10 cells** and **≥ 2 distinct protocols** (FR‑011).
- **Calibration**: A small, stratified subset ([deferred] of training data) reserved **solely** for split‑conformal calibration of prediction intervals (ensures independence from test set).  
- **Causal‑analysis**: Separate hold‑out partition ([deferred] of cells) used **exclusively** for propensity‑score matching; not used in any other training or evaluation step.

## Provenance
All processed files record:

- `source_urls`: list of URLs used for download.  
- `raw_checksums`: SHA‑256 checksums of each raw CSV.  
- `pipeline_version`: semantic version of the preprocessing code.  
- `generated_at`: ISO‑8601 UTC timestamp.  

## Covariates for Propensity‑Score Matching (Causal‑Inference Support)

The following observed cell‑level attributes are included in the processed dataset to support propensity‑score matching and satisfy the strong ignorability assumption as best as possible:

- `chemistry` (e.g., NMC, LFP)  
- `manufacturer`  
- `initial_capacity` (Q at cycle 1)  
- `protocol_type` (categorical description of charging/discharging regime)  
- `cell_dimensions` (length, width, thickness)  
- `electrode_composition_percent` (active material fraction)  
- `ambient_temperature` (recorded during early cycles)

These covariates are stored alongside each `BatteryCell` record and are used by `src/interpret/causal_analysis.py`.

## Contracts Mapping
- `contracts/processed_dataset.schema.yaml` validates the NPZ structure, split indices, and provenance.  
- `contracts/model_output.schema.yaml` validates the JSON predictions, metrics, and optional attribution.
