# Research: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Dataset Strategy

The project relies on two primary data sources: eBird for bird observations and NOAA/PRISM for climate data.

**Data Gap Status**: The "Verified Datasets" block provided in the source spec contains **no** verified URLs for the full eBird Basic Dataset (EBD) or NOAA/PRISM gridded climate data for 2020–2024.
- **eBird**: No verified URL for the full EBD.
- **NOAA/PRISM**: No verified URL for gridded PRISM data. The available "NOAA-Buoy" dataset is point-source marine data, which is **not** a valid proxy for the gridded terrestrial climate data required by FR-001 and US-1.

**Action**: The implementation will proceed with a **Synthetic Data Generation** strategy for code validation. The synthetic data will strictly conform to the `dataset.schema.yaml` contract and mimic the statistical properties (spatial resolution, temporal range, observation density) of the target datasets. This ensures the pipeline logic (ingestion, grid mapping, GAMM fitting, Riemannian analysis) is validated against the correct data structure, unlike the previous attempt to use buoy data which had a fundamentally different spatial structure.

| Data Source | Verified URL | Usage | Notes on Fit |
|:--- |:--- |:--- |:--- |
| **eBird (Full)** | *None Verified* | **Blocked**. Requires external acquisition. | No verified URL available. |
| **NOAA/PRISM (Full)** | *None Verified* | **Blocked**. Requires external acquisition. | No verified URL available. |
| **NOAA-Buoy (Proxy)** | ` | **NOT USED**. | **Mismatch**: Point-source marine data. Cannot validate 0.5° gridded spatial logic. |
| **Synthetic Data** | *Generated Locally* | **Active**. Used for code validation. | Generated to match `dataset.schema.yaml` and target statistical properties. |

**Blocking Note**: The final statistical results **cannot** be generated until the full, verified eBird and PRISM datasets are sourced and integrated. The plan explicitly states that the "Dataset Strategy" in the final report will depend on acquiring the real data. The code will be written to accept the full data format once available.

## Statistical Rigor & Methodology

### 1. Multiple Comparison Correction
* **Requirement**: FR-005 mandates Benjamini–Hochberg (BH) FDR correction.
* **Method**: All p-values from the GAMM coefficients (species-climate pairs) will be collected into a single vector. The BH procedure will be applied to control the False Discovery Rate at $\alpha = 0.05$.
* **Justification**: With thousands of species-grid combinations, uncorrected p-values would yield massive false positives.

### 2. Power & Sample Size
* **Acknowledgement**: The spec does not define a power target.
* **Limitation**: On the synthetic dataset, sample size is controlled. The plan will compute post-hoc power estimates for the subset.
* **Strategy**: The code will include a check: if the number of observations per grid cell < 30, the cell is marked "insufficient data" (US-1, Edge Case 1).

### 3. Causal Inference & Assumptions
* **Observational Nature**: The study is purely observational.
* **Claim Framing**: Results will be framed as "associations" or "correlations," not causal effects.
* **Confounding**: The GAMM includes **observer effort covariates** (`checklist_duration`, `distance_traveled`, `num_observers`) as fixed effects to control for sampling bias (methodology-26c416ac). "Species-year" is included as a random effect to control for unobserved temporal trends. Spatial autocorrelation is modeled via a default spatial smooth term (Unified Spatial Model).

### 4. Measurement Validity
* **Instruments**: eBird checklists are the standard for citizen science phenology.
* **Validation**: The plan assumes the Cornell Lab of Ornithology's species list is the ground truth for "migratory" status.
* **Collinearity**: Temperature and precipitation are often correlated. The plan will check Variance Inflation Factors (VIF) for fixed effects. If VIF > 5, the model will be refitted with one variable or using a dimension reduction technique (PCA) if necessary, though this is deferred to the implementation phase.

### 5. Spatial Autocorrelation
* **Method**: **Unified Spatial Model**. Instead of a two-step check (fit GAMM → check Moran's I → refit with GP), which invalidates p-values (scientific_soundness-9fdb232e), the plan mandates fitting a GAMM with a spatial smooth term `s(latitude, longitude)` by default for all species. This treats spatial structure as a prior assumption.
* **Implementation**: `statsmodels` with custom covariance or `rpy2` (if feasible) to support Matérn structures. If `rpy2` is too heavy for CI, `statsmodels` with a P-spline spatial term will be used as a CPU-feasible approximation, explicitly noting the trade-off.

### 6. Permutation Testing
* **Requirement**: FR-005 mandates [deferred] shuffles.
* **Adaptation**: To meet CI runtime limits (SC-005), the plan uses **[deferred] shuffles with early stopping** (sequential testing). This achieves the same statistical power with fewer iterations, ensuring the pipeline completes within 6 hours.

## Compute Feasibility & CPU Constraints

* **Hardware**: 2 CPU cores, 7 GB RAM, 14 GB disk.
* **Strategy**:
 * **Data Sampling**: Top species, a representative number of grid cells per species (tail-preserving stratified sampling).
 * **Model Choice**: `statsmodels` (preferred for flexibility) or `rpy2` (if feasible). `pygam` is rejected for lack of native Matérn GP support (scientific_soundness-f67c121f).
 * **No GPU**: All operations are CPU-native. No CUDA dependencies.
 * **Time Limit**: The pipeline is capped at a predefined maximum duration. Permutation tests (a sufficient number of shuffles with early stopping) will be parallelized across the 2 cores using `joblib`.
 * **Riemannian Analysis**: `geomstats` library used for manifold calculations.

## Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Synthetic Data for Validation** | No verified full EBD/PRISM URLs exist. Buoy data is a structural mismatch. Synthetic data ensures correct schema and logic validation. |
| **Tail-Preserving Stratified Sampling** | Prevents bias in 'first_arrival_date' caused by random sampling of rare early events (methodology-0002e18c). |
| **Unified Spatial Model** | Avoids data snooping and invalid p-values from two-step model selection (scientific_soundness-9fdb232e). |
| **Observer Effort Covariates** | Controls for sampling bias in eBird data (methodology-26c416ac). |
| **`geomstats` for Trajectories** | Required for Riemannian manifold statistics (spec_coverage-a125686e). |
| **1,000 Permutations + Early Stopping** | Ensures runtime compliance with SC-005 (6 hours) while maintaining statistical power (spec_coverage-37ec8968). |
| **`statsmodels`/`rpy2` over `pygam`** | `pygam` lacks native Matérn GP support; `statsmodels`/`rpy2` provide the necessary flexibility (scientific_soundness-f67c121f). |