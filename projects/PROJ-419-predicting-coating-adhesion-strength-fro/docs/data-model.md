# Data Model Specification: Coating Adhesion Prediction

This document defines the data structures, schemas, and relationships used in the coating adhesion prediction pipeline.

## Overview

The pipeline integrates data from multiple sources:
- **Materials Project API**: Material composition and properties.
- **NIST Surface Metrology Repository**: Surface roughness and texture metrics.
- **Open-Access Literature**: Additional experimental data.

All data is aligned, cleaned, and transformed into a unified schema before modeling.

## Raw Data Sources

### Materials Project (MP)
- **URL**: `https://materialsproject.org/rest`
- **Schema**:
 - `material_id`: Unique identifier (string).
 - `composition`: Chemical formula (string).
 - `properties`: Dictionary containing mechanical properties.
 - `target_property`: "adhesion_strength" (if available).

### NIST Surface Metrology
- **URL**: `
- **Schema**:
 - `sample_id`: Unique identifier (string).
 - `surface_roughness`: RMS roughness (float).
 - `skewness`: Surface skewness (float).
 - `kurtosis`: Surface kurtosis (float).
 - `coating_type`: Coating material (string).

### Literature Sources
- **Format**: CSV/JSON from open-access journals.
- **Schema**:
 - `study_id`: Unique study identifier.
 - `coating_substrate_pair`: String describing the pair.
 - `adhesion_strength`: Target variable (MPa).
 - `surface_metrics`: Dictionary of surface measurements.

## Unified Processed Dataset

The final dataset (`data/processed/coating_adhesion_dataset.csv`) follows this schema:

| Column Name | Type | Description |
|-------------|------|-------------|
| `unique_id` | str | Composite key: `{mp_id}_{sample_id}` |
| `composition_encoded` | str | One-hot encoded composition features |
| `atomic_radius_variance` | float | Variance of atomic radii in composition |
| `crosslinker_density_proxy` | float | Derived proxy for crosslinker density |
| `rms_roughness` | float | Root mean square roughness (standardized) |
| `skewness` | float | Surface skewness (standardized) |
| `kurtosis` | float | Surface kurtosis (standardized) |
| `adhesion_strength` | float | Target variable (MPa) |
| `test_method` | str | ASTM standard used (e.g., "ASTM_D4541") |
| `source` | str | Data source identifier (MP, NIST, LIT) |

## Derived Features

### Compositional Features
- **One-Hot Encoding**: Categorical elements in the chemical formula.
- **Atomic Radius Variance**: Statistical measure of atomic size diversity.
- **Crosslinker Density Proxy**: Calculated based on functional group counts.

### Surface Features
- **Standardization**: All surface metrics are standardized (mean=0, std=1).
- **RMS Roughness**: Primary surface texture metric.
- **Skewness & Kurtosis**: Higher-order texture descriptors.

## Data Quality Rules

1. **Unique Identifier Enforcement**:
 - Records without a verified unique identifier are **rejected** (T023).
 - Heuristic mapping is **not allowed** (contradicts Spec FR-007).

2. **Target Variable Requirements**:
 - Records with missing `adhesion_strength` are excluded (T024).
 - Exclusion ratio must be < 10% (T011, SC-005).

3. **Surface Data Requirements**:
 - Records missing surface roughness data are excluded or imputed (T027).

4. **ASTM D4541 Filter**:
 - Only records using ASTM D4541 pull-off test are retained (T022).

5. **Construct Validity**:
 - Derived proxies must have |r| > 0.3 and R² > 0.05 against target (T015, T042).

## Data Flow

1. **Ingestion**:
 - Fetch raw data from sources.
 - Filter to ASTM D4541 records.
 - Validate unique identifiers.
 - Exclude missing targets.

2. **Preprocessing**:
 - Encode compositional data.
 - Standardize surface metrics.
 - Perform construct validity checks.

3. **Modeling**:
 - Train Gradient Boosting and Random Forest models.
 - Compute SHAP values and permutation importance.
 - Rank features by category.

4. **Evaluation**:
 - Compare full model against baselines.
 - Apply Nadeau & Bengio corrected t-test.
 - Flag "Informative Null" if no improvement.

## File Locations

- **Raw Data**: `data/raw/`
- **Processed Data**: `data/processed/coating_adhesion_dataset.csv`
- **State Checksums**: `state/checksums.yaml`
- **Results**: `results/`

## Versioning

- **Schema Version**: 1.0
- **Last Updated**: 2023-10-27
- **Maintainer**: llmXive Pipeline Team