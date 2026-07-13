# Research: Statistical Analysis of Urban Noise Pollution (Prototype Validation)

## 1. Overview
This research phase validates the data sources and methodological approach for analyzing urban noise pollution.
**Critical Scope Note**: The "Verified datasets" block provided in the prompt contains **no geospatial noise, traffic, or population data**. The listed datasets are text-based LLM corpora.
Therefore, this project **cannot** perform an empirical analysis of real-world urban noise. The scope is narrowed to **Methodological Validation**: validating the statistical pipeline (ingestion, spatial modeling, cross-validation) using a **synthetic data proxy**.
The primary objective is to confirm that the proposed statistical methods (OLS, Spatial Lag/Error) are feasible within the CPU-only, time-constrained environment. and that the code correctly detects spatial dependence *if* it exists in the data. The pipeline is designed as a hypothesis test: if the synthetic data lacks spatial dependence, the pipeline must correctly report that OLS is the preferred model.

## 2. Dataset Strategy

### 2.1 Verified Datasets
Per the project constraints, we must cite ONLY verified sources. The following datasets are available and verified for this project:

| Dataset Name | Description | Verified URL | Usage in Project |
|:--- |:--- |:--- |:--- |
| **OLScience Guanaco Format** | Synthetic/Processed dataset for NLP/Science tasks. | ` | **NOT SUITABLE** for this specific spatial analysis. This dataset is text-based and lacks geospatial variables. |
| **OLScience Guanaco Format (8.5k)** | Larger version of the above. | ` | **NOT SUITABLE**. Same limitation as above. |

### 2.2 Critical Gap Analysis
**Status**: **BLOCKING GAP IDENTIFIED**
The "Verified datasets" block provided in the prompt **does not contain any urban noise, traffic, or geospatial covariate data**.

**Action Required**:
1. **Synthetic Data Generation**: Since no verified geospatial noise dataset is provided, the implementation **must** generate a synthetic but statistically valid dataset that mimics the required structure (noise levels, traffic, land use, population) to satisfy the pipeline logic and unit tests.
2. **Scope Definition**: The project is explicitly re-scoped as a **Pipeline Prototype**. The scientific conclusion regarding "urban noise" is **deferred** until verified real-world data is available. The Success Criteria (SC-001 to SC-005) are treated as **Validation Checks** for the pipeline's correctness, not as empirical scientific findings.
3. **Documentation**: The `research.md` and `plan.md` will explicitly state that the analysis runs on a **synthetic proxy dataset** generated to match the schema, as the real-world data sources (NoiseTube, OSM, WorldPop) are not present in the verified list.

### 2.3 Synthetic Data Generation Strategy
To satisfy the "Reproducibility" and "Data Hygiene" principles without external network dependencies for large geospatial files:
* **Generator**: A Python script (`code/synthetic_data.py`) will generate a GeoDataFrame with [deferred] grid cells.
* **Variables**:
 * `noise_db`: Simulated decibel levels with spatial autocorrelation (using a Gaussian Random Field). **Crucially**, the spatial parameter (Moran's I) is drawn from a distribution (e.g., Uniform(0, 0.8)) **without pre-selecting for a specific outcome**. This ensures the analysis is a true hypothesis test: if the generated data has low spatial dependence, the pipeline will correctly report that OLS is sufficient.
 * `traffic_vol`: Simulated traffic counts correlated with `noise_db`.
 * `land_use`: Categorical (Residential, Commercial, Industrial).
 * `pop_density`: Simulated population density.
 * `date`: Random dates to satisfy FR-002 (Daily Aggregation).
* **Validation**: The synthetic data will be constructed to ensure the *pipeline logic* (e.g., detection of spatial dependence, calculation of robust SEs) is functional. It is **not** designed to "ensure" the Success Criteria are met; rather, it tests whether the code *correctly reports* the results (whether positive or negative).

## 3. Methodological Rationale

### 3.1 Spatial Autocorrelation
Urban noise is inherently spatial; measurements in adjacent grid cells are correlated. Standard OLS assumes independence of errors, which is violated here.
* **Method**: We will use **Spatial Lag (SAR)** and **Spatial Error (SEM)** models from `PySAL` to explicitly model this dependence.
* **Validation**: Moran's I will be calculated for residuals. A successful model *should* reduce Moran's I by >10% relative to OLS and achieve residual I ≤ 0.1. If the synthetic data has low spatial dependence, OLS may perform equally well; this is a valid outcome.

### 3.2 Spatial Cross-Validation
Standard K-Fold CV leaks information in spatial data.
* **Method**: **Spatial Block Cross-Validation** (5-fold). The study area will be partitioned into contiguous blocks to ensure training and test sets are spatially disjoint.
* **Significance Testing**: A **spatial block permutation test** (10,000 permutations) will be used to determine if the RMSE reduction of spatial models over OLS is statistically significant (p < 0.05). **Note**: On synthetic data, this validates the *permutation test logic*, not the scientific superiority of the model. If p > 0.05, the pipeline correctly reports no significant difference.

### 3.3 Multiple Comparison Correction
* **Method**: **Benjamini-Hochberg (BH) FDR** correction at α = 0.05 for the three primary covariates (traffic, land use, population) across all models.
* **Robust SEs**: Standard errors will be adjusted using **Cluster-Robust** or **Conley** standard errors (via `linearmodels`) to account for spatial correlation in the error term, ensuring valid p-values.
* **Distinction**: Robust SEs address the validity of individual p-values in the presence of spatial correlation. BH-FDR addresses the family-wise error rate when testing multiple hypotheses (three covariates). Both steps are necessary: Robust SEs ensure the p-values are correct; FDR ensures the set of significant findings is controlled. This two-step process is methodologically sound and distinct.

### 3.4 Spatial Weight Matrix Fallback
* **Primary**: Queen contiguity (shared edge).
* **Fallback 1**: K-Nearest Neighbor (K=8) if the primary matrix fails (e.g., disconnected components).
* **Fallback 2**: **HALT**. If both methods fail, log a CRITICAL error and stop execution. This directly addresses the Spec Edge Case requirement.

### 3.5 Computational Feasibility
* **Library Choice**: `PySAL` (v2.4+), `scikit-learn`, `statsmodels`, and `linearmodels` are CPU-native and efficient.
* **Memory Management**: Data will be processed in chunks if necessary, but the cell limit fits comfortably in available RAM.
* **No GPU**: All operations are matrix-based and linear algebraic, requiring no CUDA.

## 4. Decision Log

| Decision | Rationale | Alternative Rejected |
|:--- |:--- |:--- |
| **Synthetic Data** | No verified geospatial dataset available in the prompt's "Verified datasets" block. | Using real data would require external URLs not verified, violating the "Verified Accuracy" gate. |
| **Pipeline Prototype Scope** | The project cannot fulfill the "Real-world Analysis" requirement. | Proceeding as a "Real-world Study" would be scientifically invalid. |
| **Spatial Block CV** | Standard K-Fold invalid for spatial data due to leakage. | Random K-Fold would yield overly optimistic and invalid performance metrics. |
| **BH-FDR Correction** | Spec requires correction for several primary covariates. | Bonferroni is too conservative for exploratory spatial analysis; BH is preferred. |
| **Cluster-Robust SEs** | Required by FR-009 to handle spatial correlation in errors. | Standard OLS SEs would be biased and lead to incorrect p-values. |
| **Daily Aggregation** | Required by FR-002 to calculate metrics "per day". | Aggregating all time into a single value ignores the temporal dimension required by the spec. |
| **Stochastic Parameter Generation** | To avoid tautological validation, spatial parameters are sampled from a distribution, not pre-biased. | Pre-biasing parameters to guarantee success would invalidate the hypothesis test. |
