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
| **SequenceWindow** | Processed model input (initial set of cycles). | `cell_id: str`, `input_sequence: ndarray (50, 100, 3)`, `target_fade: float` (computed as described below) |
| **AggregatedFeatureImportance** | Summarized attribution scores. | `cell_id: str`, `per_cycle_importance: List[float]` (length 50), `per_channel_importance: Dict[str, float]` (`voltage`, `current`, `temperature`), `derived_signatures: Dict[str, float]` (e.g., voltage variance, current slope, temperature fluctuation) |
| **ModelPrediction** | Model output per test cell. | `cell_id: str`, `protocol: str`, `predicted_fade: float`, `true_fade: float`, `ci_lower: float`, `ci_upper: float`, `feature_importance_scores: AggregatedFeatureImportance` |
| **BaselineFeatureSet** | Hand‑crafted incremental‑capacity features (cycles 1‑50). | `cell_id: str`, `features: Dict[str, float]`, `target_fade: float` |

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

## Provenance
All processed files record:

- `source_urls`: list of URLs used for download.  
- `raw_checksums`: SHA‑256 checksums of each raw CSV.  
- `pipeline_version`: semantic version of the preprocessing code.  
- `generated_at`: ISO‑8601 UTC timestamp.  

## Contracts Mapping
- `contracts/processed_dataset.schema.yaml` validates the NPZ structure, split indices, and provenance.  
- `contracts/model_output.schema.yaml` validates the JSON predictions, metrics, and optional attribution fields.

---

