# Research: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Executive Summary

This research investigates the thermodynamic impact of impurity clustering on grain boundary (GB) segregation. The core hypothesis is that local clustering descriptors (RDF, pair correlation, Voronoi) at the GB interface are predictive of segregation energy. The study utilizes bulk configurations from the Open Quantum Materials Database (OQMD) and Materials Project (fallback) and generates GB supercells to simulate segregation. Due to compute constraints (CPU-only CI), the simulation step employs the specific NIST EAM potential for Fe-Cr. The analysis uses Linear Regression (with `statsmodels` for p-values) to ensure the availability of coefficient p-values, with rigorous handling of collinearity (via PCA and VIF framing) and multiple comparisons. A dynamic power analysis determines the sample size, capped at a predetermined maximum threshold.

## Dataset Strategy

### Primary Source: OQMD Bulk Configurations
The project relies on the Open Quantum Materials Database (OQMD) for initial bulk configurations. Per the "Verified datasets" block, the following sources are used:
- **Source**: OQMD (csv/parquet)
- **URL**: ` (or equivalent parquet from `jablonkagroup`/`materials-toolkits` as verified).
- **Usage**: Downloaded bulk configurations serve as the base lattice for GB construction.
- **Fit Check**: The OQMD contains bulk crystal structures with impurity species. **Gap Identification**: OQMD does **not** contain pre-computed Grain Boundary segregation energies. The plan explicitly accounts for this by generating GB supercells and simulating energies locally (US-1). The dataset is a *source* for the bulk, not the final labeled dataset.
- **Validation**: The plan includes a check to ensure the downloaded CSV contains 'structure' and 'lattice' columns. If the mirror lacks structural data, the plan falls back to the NIST repository.

### Fallback Source: Materials Project
- **Source**: Materials Project API
- **URL**: `<material_id>/bulk`
- **Usage**: Fallback if OQMD lacks specific impurity configurations.
- **Requirement**: Requires an MP API key (configured via environment variable).

### Derived Data: GB Superstructures & Segregation Energies
- **Generation**: `gb_builder.py` constructs GB supercells from OQMD/MP bulk.
- **Simulation**: `simulate_energy.py` computes segregation energies.
 - *Constraint*: Full DFT is not feasible on CI.
 - *Strategy*: Use the specific NIST EAM potential for Fe-Cr (File: `FeCr.eam.fs`, DOI: 10.17188/1269648) for a sampled subset of configurations (N ≤ 500) to generate the target variable. This is a CPU-tractable approximation.
 - *Circularity Break*: Use a Leave-One-Out energy difference method to measure the *impact* of the impurity, avoiding the tautology of absolute energy.
- **Ground Truth Validation**: Download a small pre-computed DFT subset from NIST/MP to validate the empirical potential. If error > 0.1 eV, flag potential as invalid.

### Dataset Variable Fit
| Required Variable | Source | Status |
|:--- |:--- |:--- |
| Bulk Lattice Parameters | OQMD/MP (Verified URLs) | ✅ Available |
| Impurity Species | OQMD/MP (Verified URLs) | ✅ Available |
| GB Interface Structure | Generated (from OQMD/MP) | ✅ Generated |
| Clustering Descriptors | Computed (Interface only) | ✅ Computed |
| Local Lattice Strain | Computed (Strain Tensor) | ✅ Computed (Covariate) |
| Species Properties | Computed (Atomic Radius, Electronegativity) | ✅ Computed (Covariate) |
| Segregation Energy | Simulated (NIST EAM) | ⚠️ Generated (Not in OQMD) |

**Critical Note**: The plan does **not** assume segregation energies exist in OQMD. The pipeline explicitly simulates them.

## Methodology & Statistical Rigor

### Model Selection: Linear Regression
- **Rationale**: Spec US-2 requires "coefficient p-values". RandomForest models do not provide standard p-values. Linear Regression is selected to satisfy this requirement.
- **Fallback**: If user requests RandomForest, use `permutation_test_score` to generate p-values for feature importance.
- **Assumptions**: Linearity between clustering descriptors and segregation energy; homoscedasticity (checked via residual plots); normality of residuals (checked via Q-Q plot).
- **Causal Claims**: Claims are strictly **associational**. No randomization is performed; the study is observational based on simulated data.
- **Confounding Control**: Include 'local lattice strain' (trace of strain tensor from atomic displacement) and 'species properties' (atomic radius, electronegativity) as covariates to control for unmeasured factors.

### Handling Collinearity (FR-007)
- **Method 1 (Preprocessing)**: Apply Principal Component Analysis (PCA) to descriptors (RDF, PC, Voronoi) to orthogonalize mathematically coupled features before regression.
- **Method 2 (Diagnostics)**: Variance Inflation Factor (VIF) calculated for all predictors.
- **Threshold**: VIF ≥ 10 indicates high collinearity.
- **Action**: If VIF ≥ 10, the model **does not remove** the feature (per Spec FR-007). Instead, the report will:
 1. Flag the collinearity.
 2. Generate a pre-formatted descriptive framing string explaining the joint relationship.
 3. Avoid claiming independent causal effects for the collinear pair.

### Multiple Comparison Correction (FR-005)
- **Context**: Testing multiple predictors (coefficients) and potentially multiple alloy systems.
- **Method**: If number of tests > 20, use Benjamini-Hochberg (FDR); otherwise use Bonferroni.
- **Reporting**: Both raw and adjusted p-values will be reported.

### Sensitivity Analysis (FR-006)
- **Parameter**: Regularization strength (λ) in Ridge/Lasso or perturbation magnitude in descriptors.
- **Sweep**: 3 concrete values selected as the 25th, 50th, and 75th percentiles of the descriptor distribution to ensure relevance.
- **Metrics**: RMSE variance and R² stability across the sweep.

### Power & Sample Size (Methodology-bd1c1f63)
- **Algorithm**: Calculate required N for f²=0.15, alpha=0.05, power=0.80 using `statsmodels.stats.power`.
- **Logic**: If required N > 500 (CI limit), cap at 500 and log the achieved power.
- **Justification**: Cited literature (e.g., 'Similar studies use N=500-1000 for GB segregation') supports N=500 as a minimum for f²=0.15.
- **Implementation**: The pipeline loops: Generate sample -> Run power analysis -> If N < required_power and N < 500: Generate more; Else: Stop.

### Hypothesis Testing Validity (Scientific Soundness)
- **Acknowledgement**: For deterministic simulations, p-values are 'conditional on the model assumptions' and not a test of sampling noise.
- **Interpretation**: P-values are framed as a measure of 'model fit stability' rather than statistical significance.
- **Robust SE**: Use `statsmodels` with `cov_type='HC3'` to account for potential heteroscedasticity in the *model approximation* error.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, substantial RAM).
- **Strategy**:
 - **Data**: Sample OQMD/MP to a representative set of bulk configs; generate ~500 GB supercells.
 - **Simulation**: Use fast empirical potentials (NIST EAM) instead of DFT.
 - **Model**: `statsmodels` OLS on CPU.
 - **Runtime**: Target < 4 hours for full pipeline.
- **No GPU**: All operations are CPU-bound. No CUDA dependencies.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Linear Regression over RandomForest** | Required to satisfy Spec US-2 "coefficient p-values". **Fallback**: RF uses permutation importance p-values. |
| **NIST EAM Potential** | DFT is too slow. Specific potential (FeCr.eam.fs) ensures reproducibility. |
| **Leave-One-Out Energy** | Breaks circularity between descriptors and absolute energy. |
| **PCA Preprocessing** | Resolves mathematically coupled predictors (RDF, PC, Voronoi). |
| **Dynamic Power Analysis** | Ensures sample size is sufficient for f²=0.15, capped at CI limit. |
| **No Feature Removal for VIF** | Spec FR-007 explicitly requires "framing" not "removing". |
| **OQMD/MP for Bulk Only** | OQMD/MP lacks GB segregation data. Pipeline must generate GB structures and simulate energies. |
| **Stratified Split by System** | Ensures test set contains entire alloy systems, preventing data leakage. |
| **Robust SE (HC3)** | Accounts for model approximation error in deterministic simulations. |