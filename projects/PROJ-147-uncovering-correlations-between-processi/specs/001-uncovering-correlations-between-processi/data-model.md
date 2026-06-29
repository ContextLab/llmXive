# Data Model: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Entity Definitions

### ProcessingRecord

Represents a single rolling experiment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sample_id` | string | Yes | Unique identifier |
| `alloy_id` | string | Yes | Alloy identifier |
| `alloy_family` | string | Yes | Classification (e.g., "FCC_Al", "FCC_Cu", "BCC_steel") |
| `rolling_speed` | float | Yes | Rolling speed (m s⁻¹) |
| `temperature` | float | Yes | Rolling temperature (°C) |
| `reduction_ratio` | float | Yes | Thickness reduction (%) |
| `composition` | array[float] | No | Optional composition vector |
| `source` | string | Yes | Dataset source (e.g., "OMDB", "NIST", "synthetic") |
| `checksum` | string | Yes | SHA256 of raw data row |

### TextureDescriptor

Quantitative representation of crystallographic texture.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sample_id` | string | Yes | Links to ProcessingRecord |
| `odf_100` | float | Yes | Peak ODF intensity for {100} plane (MRD) |
| `odf_110` | float | Yes | Peak ODF intensity for {110} plane (MRD) |
| `odf_111` | float | Yes | Peak ODF intensity for {111} plane (MRD) |
| `raw_diffraction_file` | string | No | Path to raw diffraction data (optional for synthetic data) |
| `computation_script` | string | Yes | Path to ODF computation script |

### AlloyFamily

Classification of alloys by composition and crystal structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `family_id` | string | Yes | Unique identifier (e.g., "FCC_Al") |
| `crystal_structure` | string | Yes | "FCC", "BCC", "HCP" |
| `composition_range` | object | Yes | Min/max for each element |
| `sample_count` | integer | Yes | Number of samples in family |

### TrainedModel

Serialized multi-output RandomForest model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_id` | string | Yes | Unique identifier for the model |
| `model_file` | string | Yes | Path to serialized model (joblib) |
| `hyperparameters` | object | Yes | n_estimators, max_depth, etc. |
| `training_checksum` | string | Yes | SHA256 of training data |
| `validation_metrics` | object | Yes | R², MAE, RMSE per coefficient |
| `created_at` | string | Yes | ISO timestamp |

## Derived Features

| Feature | Formula | Description |
|---------|---------|-------------|
| `strain_rate` | rolling_speed / (initial_thickness - final_thickness) | Deformation rate |
| `zener_hollomon` | strain_rate * exp(Q / (R * temperature_K)) | Temperature‑compensated strain rate (Q: activation energy, R: gas constant) |
| `normalized_speed` | (rolling_speed - mean) / std | Standardized rolling speed |
| `normalized_temp` | (temperature - mean) / std | Standardized temperature |

## Synthetic Data Generation (New)

To satisfy **FR‑008** (≥ 50 paired samples per alloy family), a synthetic generator (`code/pipeline/synthetic_data.py`) creates **60 samples per alloy family** (Al, Cu, steel). Parameters are sampled from realistic bounded ranges:

- `rolling_speed`: Uniform [0.1, 5.0] m s⁻¹  
- `temperature`: Uniform [200, 1200] °C  
- `reduction_ratio`: Uniform [10, 80] %  

Each synthetic record receives a SHA‑256 checksum and a `source` value of `"synthetic"`.

## Synthetic Texture Computation (New)

For each synthetic sample, a parametric ODF model with Gaussian peaks on the {100}, {110}, and {111} crystallographic planes is generated. The ODF is then processed by **pymtex** (or a spherical‑harmonic fallback) to extract the peak MRD intensities (`odf_100`, `odf_110`, `odf_111`). This procedure satisfies **FR‑003** with an equivalence tolerance of ±5 % MRD relative to a reference implementation.

## Data Flow

```
raw_data/
  ├── omdb_co_0.parquet    # Downloaded from verified URL
  �├── nist_800_53.jsonl    # Downloaded from verified URL
  └── synthetic_data.json  # Generated if no paired data is available
processed_data/
  ├── processed_records.csv      # Ingested + validated ProcessingRecords
  ├── texture_descriptors.csv    # Computed TextureDescriptors
  ├── derived_features.csv       # Physics‑based features
  └── train_test_split.csv       # Final training/test split
artifacts/
  ├── trained_model.joblib       # TrainedModel
  ├── predictions.csv            # Output predictions
  ├── evaluation_report.json     # Metrics
  └── importance_plot.png        # Feature importance visualization
```

## Validation Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Sample count per family | ≥50 per alloy_family | Abort if not met (FR‑008) |
| Missing numeric values | >20 % NaN for any parameter | Abort with "Data quality insufficient" (Edge Case) |
| Outlier removal | >3σ from mean | Remove and log |
| Unit standardization | °C, m s⁻¹, % reduction | Convert if needed |
| ODF equivalence | ±5 % MRD of pymtex | Document alternative tool |

---



