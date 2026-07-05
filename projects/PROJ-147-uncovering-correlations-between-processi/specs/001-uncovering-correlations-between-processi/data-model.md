# Data Model: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Overview

This document defines the core data entities, relationships, and transformations used throughout the pipeline. It ensures consistency between data ingestion, preprocessing, modeling, and output.

## Core Entities

### ProcessingRecord
Represents a single rolling experiment.
- `sample_id`: str (unique identifier)
- `alloy_id`: str (links to AlloyFamily)
- `rolling_speed`: float (m/s)
- `temperature`: float (°C)
- `reduction_ratio`: float (%)
- `composition_vector`: list[float] (normalized elemental composition)
- `prior_history`: str (categorical: e.g., "annealed", "cold-worked")
- `raw_diffraction_file`: str (path to raw ODF/pole-figure file)
- `source`: str (e.g., "OMDB", "synthetic")

### AlloyFamily
Classification of alloys by composition and crystal structure.
- `family_id`: str (e.g., "FCC_Al", "FCC_Cu", "BCC_Steel")
- `crystal_structure`: str (e.g., "FCC", "BCC")
- `composition_range`: dict (min/max for key elements)

### TextureDescriptor
Quantitative representation of crystallographic texture.
- `sample_id`: str (links to ProcessingRecord)
- `odf_100`: float (MRD)
- `odf_110`: float (MRD)
- `odf_111`: float (MRD)
- `computed_by`: str (e.g., "pymtex", "synthetic_generator")

### TrainedModel
Serialized multi-output RandomForest model.
- `model_id`: str (content hash)
- `hyperparameters`: dict (n_estimators, max_depth, etc.)
- `training_seed`: int
- `feature_names`: list[str]
- `alloy_families`: list[str]
- `created_at`: datetime

### SyntheticDataConfig
Configuration for synthetic data generation.
- `num_samples`: int (≥50 per family)
- `alloy_families`: list[str]
- `noise_level`: float (σ=0.05 MRD)
- `seed`: int

## Relationships

- `ProcessingRecord` ↔ `TextureDescriptor`: One-to-one via `sample_id` and `alloy_id`.
- `ProcessingRecord` ↔ `AlloyFamily`: Many-to-one via `alloy_id`.
- `TrainedModel` → `ProcessingRecord`: Trained on processed `ProcessingRecord` data.
- `SyntheticDataConfig` → `ProcessingRecord` + `TextureDescriptor`: Generates both.

## Data Flow

1. **Ingestion**: Raw files (CSV/JSON) → `ProcessingRecord` + `TextureDescriptor` (via `pymtex`).
2. **Preprocessing**: `ProcessingRecord` → cleaned/derived features (VIF-checked).
3. **Training**: Cleaned features + `TextureDescriptor` → `TrainedModel`.
4. **Prediction**: New `ProcessingRecord` → predicted `TextureDescriptor`.
5. **Evaluation**: Predicted vs. actual `TextureDescriptor` → metrics + importance.

## Transformations

| Step | Input | Output | Transformation |
|------|-------|--------|----------------|
| Unit Standardization | Raw `ProcessingRecord` | Cleaned `ProcessingRecord` | Convert to SI units (°C, m/s, %) |
| Imputation | Cleaned `ProcessingRecord` | Imputed `ProcessingRecord` | Median imputation for missing values |
| Outlier Removal | Imputed `ProcessingRecord` | Filtered `ProcessingRecord` | Remove samples beyond 3σ |
| Feature Engineering | Filtered `ProcessingRecord` | Derived `ProcessingRecord` | Add strain rate, Zener-Hollomon, composition |
| VIF Check | Derived `ProcessingRecord` | Final `ProcessingRecord` | Remove features with VIF ≥ 5 |
| Texture Computation | Raw diffraction files | `TextureDescriptor` | `pymtex` ODF peak extraction |
| Synthetic Generation | `SyntheticDataConfig` | `ProcessingRecord` + `TextureDescriptor` | Physics-informed simulation |

## Constraints & Validations

- **Sample Size**: ≥ 50 per alloy family (abort if not met).
- **Missing Data**: >20% missing in any feature → abort.
- **VIF Threshold**: ≥ 5 → remove feature.
- **ODF Accuracy**: Synthetic descriptors must match generator within ±5% MRD.
- **Seeds**: All random operations use fixed seeds for reproducibility.
