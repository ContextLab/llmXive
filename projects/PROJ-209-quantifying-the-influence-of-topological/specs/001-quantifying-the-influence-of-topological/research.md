# Research: Quantifying the Influence of Topological Defects on 2D Material Properties

## Executive Summary

This research plan details the methodology for **predictive modeling** of how topological defects in graphene and MoS₂ correlate with changes in electronic conductivity, Young's modulus, and fracture strength. **All inferences are explicitly framed as associational, not causal**, due to the observational nature of the data. The study relies on the "2022 supplementary CSV/JSON" as the sole source for scientific analysis. If this dataset is unavailable, the project halts scientific analysis and runs a "Pipeline Validation" mode using a strictly synthetic dataset.

## Dataset Strategy

### Primary Data Sources

**Strict Requirement**: The study requires the "2022 supplementary CSV/JSON" (Constitution Principle VI) containing defect type, density, and fracture energy for graphene/MoS₂.

**Strategy**:
1. **Pristine Structures**: Downloaded from the Materials Project REST API (FR-001).
2. **Defect Properties**:
 * **If 2022 CSV exists**: Load and validate. Proceed to scientific analysis.
 * **If 2022 CSV missing**: Log `ERROR: 2022 CSV missing`, generate `Validation_Report.json` with `status: NO_EXTERNAL_DATA`, and **HALT** scientific modeling.
 * **Pipeline Test Mode**: If explicitly flagged for testing, generate a synthetic dataset (`data/raw/synthetic_train.csv`) using stochastic physical models. This data is **never** used for scientific conclusions.

### Verified Datasets (Cited Sources)

The following datasets are verified and reachable. They will be used to derive pristine reference values if the MP API fails.

| Dataset Name | Source URL | Usage in Plan |
|:--- |:--- |:--- |
| DFT (test) | ` | Potential source for pristine reference values (elastic tensor, band gap) if MP API fails. |
| DFT (train) | ` | Potential source for pristine reference values. |

**Note on Defect Dataset**: The "2022 supplementary CSV/JSON" is **not** in the verified URL list. It must be provided in the repository. If missing, the project cannot proceed with scientific analysis.

### Data Availability & Feasibility

* **Compute**: The datasets are small (<100MB for CSV/Parquet). They fit easily within the available RAM limit.
* **Streaming**: Not required for the expected dataset size (<10k rows). Full load into memory is feasible.
* **Access**: All verified HF datasets are public. Materials Project API is public (requires API key, handled via env var).

## Statistical Methodology

### Model Selection
* **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
* **Justification**: Handles non-linear relationships between defect geometry and properties; robust to outliers; provides feature importance.
* **Constraints**: CPU-optimized; no GPU required.

### Validation Strategy
* **Train/Test Split**: 80/20 (Train/Validation+Test) with a further split of the [deferred] into [deferred] Validation and [deferred] **Independent Hold-Out Test** (FR-012).
* **Cross-Validation**: 5-fold CV on the Train set.
* **Metrics**: R² and MAPE (FR-002, SC-002).
* **Null Baseline**: Mean prediction model (FR-002).

### Inference & Multiple Testing
* **Permutation Testing**: N=1000 permutations (FR-011) to generate p-values for feature importance.
* **FDR Control**: Benjamini-Hochberg procedure (FR-005, SC-004) to control FDR at q ≤ 0.05 across all tests.
* **Collinearity**: Variance Inflation Factor (VIF) computed. If VIF > 5, sensitivity analysis compares models with/without correlated features (FR-008, Edge Cases).

### Causal Limitations
* **Framing**: All inferences are **associational**. The data is observational (defects are not randomly assigned).
* **Confounding Control (FR-013)**: Attempt stratification by 'synthesis_method' or 'grain_size'. If unavailable, include as covariates. If neither is possible, log a warning and proceed with a `covariate_skipped` flag.
* **Propensity Score Matching**: As a sensitivity analysis, we will attempt to match samples with similar confounding characteristics to reduce bias, though this does not establish causality.

## Synthetic Data Generator Logic

If the project runs in "Pipeline Test Mode" (synthetic data only):
* **Stochasticity**: The generator will use theoretical scaling laws (e.g., linear or power-law relationships between density and property change) **plus** significant Gaussian noise and random feature interactions.
* **Non-Tautology**: This ensures the Random Forest model is not simply learning a deterministic formula but is tested on its ability to recover signal from noise.
* **Uncorrelated Features**: The generator will include uncorrelated "dummy" features to test the specificity of the feature importance ranking.

## Compute Feasibility

* **CPU-First**: Random Forest and permutation testing are CPU-tractable.
 * *Estimate*: A moderate number of permutations on a representative set of samples with a standard number of features takes approximately 5-10 minutes on 2 cores.
 * *Memory*: < 1GB.
* **GPU Escape Hatch**: Not required. No deep learning or large matrix factorization is planned.

## Ethical & Reproducibility Considerations

* **Synthetic Data**: Strictly flagged. Not used for final conclusions if real data is missing.
* **Missing Data**: Entries with missing fracture energy or undefined density are excluded and logged with `[MISSING: requires exclusion]` (FR-002, Edge Cases).
* **Reproducibility**: All seeds pinned; `model_config.yaml` generated.
* **Validation Report**: If no external dataset exists, `Validation_Report.json` is generated with `status: NO_EXTERNAL_DATA` and `method: internal_only` (FR-009).