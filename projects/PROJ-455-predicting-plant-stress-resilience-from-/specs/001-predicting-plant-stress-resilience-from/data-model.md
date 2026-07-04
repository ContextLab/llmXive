# Data Model: Predicting Plant Stress Resilience

## 1. Entity Definitions

### MetabolomicProfile
Represents a single sample's pre-stress state.
- **SampleID**: Unique identifier (string).
- **Species**: Plant species name (string).
- **StressType**: Type of stress applied (e.g., "drought", "salinity", "heat").
- **TimePoint**: Time relative to stress (e.g., "t=0" for pre-stress).
- **Metabolites**: Dictionary of {metabolite_name: concentration}.
- **Metadata**: Additional context (e.g., temperature, light).

### RecoveryMetric
Represents the outcome variable.
- **SampleID**: Links to `MetabolomicProfile`.
- **RecoveryType**: Original metric type (e.g., "biomass", "survival").
- **RawValue**: The measured value.
- **ControlValue**: The value of the control group for normalization.
- **RecoveryIndex**: Normalized value (0-1 scale).
- **TimePostStress**: Days post-stress (must be $\ge 7$).

### ModelResult
Output of the predictive modeling phase.
- **ModelType**: "RandomForest" or "SVM".
- **StressType**: Training stress type.
- **Metrics**: Dictionary of performance scores ($R^2$, $r$, RMSE).
- **FeatureImportance**: List of {metabolite: score}.
- **PValue**: Result of permutation test.
- **GeneralizabilityScore**: $R^2_{drop}$ or $r_{drop}$ for cross-stress.

## 2. Data Flow

1.  **Raw Ingestion**: Downloaded files (CSV/Parquet) $\rightarrow$ `data/raw/`.
2.  **Preprocessing**:
    - Filter: `TimePostStress` $\ge 7$.
    - Normalize: `RecoveryIndex` = `RawValue` / `ControlValue`.
    - Impute: Missing < 10% $\rightarrow$ Half-minimum.
    - Transform: $\ln(x)$.
    - Output: `data/processed/cleaned_dataset.parquet`.
3.  **Modeling**:
    - Split: Train/Test (5-fold CV).
    - Train: RF/SVM.
    - Validate: Permutation test, Cross-stress evaluation.
    - Output: `data/results/model_metrics.json`.
4.  **Biological Validation**:
    - Map: Metabolite Name $\rightarrow$ KEGG ID.
    - Enrich: Compare with pathways.
    - Output: `data/results/pathway_validation.json`.

## 3. Constraints & Rules

- **Missing Data**: If missing > 10% in any column, the sample/dataset is rejected (FR-003).
- **Normalization**: All recovery metrics must be converted to 0-1 scale before analysis (FR-002.1).
- **Pairing**: Only samples with both `t=0` and `t>=7d` data are used for individual-level models.
- **Fallback**: If no individual pairs exist, aggregate to population means and use Pearson $r$.
