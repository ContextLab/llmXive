# Data Model: Predicting Coating Adhesion Strength

This document defines the data entities, schemas, and relationships used in the
`llmXive` pipeline for predicting coating adhesion strength.

## Core Entities

### 1. CoatingSample

Represents a single coating-substrate pair with measured adhesion strength.

**Schema**:
```yaml
sample_id: string # Unique identifier (verified from source)
coating_composition: dict # Chemical composition (e.g., {"C": 0.6, "H": 0.3, "O": 0.1})
substrate_type: string # e.g., "Steel", "Aluminum", "Polymer"
surface_roughness: dict # Surface metrics (RMS, skewness, kurtosis)
adhesion_strength: float # Target variable (MPa), from ASTM D4541 test
test_date: date # Date of measurement
source: string # Origin (Materials Project, NIST, Literature)
```

**Constraints**:
- `sample_id` must be unique and verified (no heuristic mapping).
- `adhesion_strength` must be present; records with missing targets are excluded.
- `surface_roughness` must include at least RMS; if missing, record is excluded.

### 2. DerivedFeatures

Features engineered from raw composition and surface data.

**Schema**:
```yaml
feature_name: string # e.g., "atomic_radius_variance", "crosslinker_density"
feature_value: float # Computed value
feature_category: string # "compositional" or "surface"
validity_check: bool # Passes construct validity (|r| > 0.3, R² > 0.05)
```

**Derived Features**:
- **Atomic Radius Variance**: Standard deviation of atomic radii in composition.
- **Crosslinker Density Proxy**: Estimated from functional group counts (validated for construct validity).
- **Surface Skewness/Kurtosis**: Statistical moments of roughness profile.

**Construct Validity Check**:
- Proxies are excluded if correlation with target |r| < 0.3 or R² < 0.05.
- Results logged in `state/construct_validity_report.json`.

### 3. ModelOutput

Results from predictive modeling and evaluation.

**Schema**:
```yaml
model_type: string # "GradientBoosting", "RandomForest", "Baseline_Composition", "Baseline_Surface"
mean_r2: float # Mean R² from nested CV
mean_rmse: float # Mean RMSE
mean_mae: float # Mean MAE
shap_rankings: list # Top 10 features by SHAP value
permutation_importance: list # Top 10 features by permutation importance
```

**Statistical Comparison**:
- **Nadeau & Bengio Corrected t-test**: Compares full model vs. baselines.
- **Bonferroni Correction**: Applied to p-values for multiple comparisons.
- **Informative Null Flag**: Set if full model does not outperform baselines (p > 0.05).

## Data Flow

1. **Raw Data**: Fetched from Materials Project, NIST, and literature.
2. **Ingestion**: Filtered by ASTM D4541, validated by unique ID, duplicates resolved.
3. **Preprocessing**: One-hot encoding, standardization, construct validity checks.
4. **Modeling**: Nested CV, SHAP analysis, feature ranking.
5. **Evaluation**: Baseline comparison, statistical testing, final report.

## Output Files

- `data/processed/coating_adhesion_dataset.csv`: Unified dataset (max 5,000 rows).
- `state/validation_report.json`: Exclusion ratio, success rate, construct validity.
- `state/model_report.json`: Model performance and feature importance.
- `state/evaluation_report.json`: Statistical comparison results.

## Safety Gates

- **Power Analysis**: N ≥ 1,000 required.
- **Exclusion Ratio**: < 10% missing targets.
- **Success Rate**: ≥ 95% processing success.
- **Construct Validity**: Derived proxies must pass |r| > 0.3 and R² > 0.05.

## Versioning

- **Data Model Version**: 1.0
- **Last Updated**: 2023-10
- **Corresponds to**: PROJ-419, Task T053