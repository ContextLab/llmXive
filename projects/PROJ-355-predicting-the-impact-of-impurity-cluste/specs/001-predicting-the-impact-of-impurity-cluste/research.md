# Research: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## 1. Problem Statement & Hypothesis

**Hypothesis**: The degree of impurity clustering at grain boundaries (quantified by RDF peaks, pair correlation, and Voronoi neighbor counts) is a statistically significant predictor of segregation energy.
**Null Hypothesis**: Clustering descriptors have no predictive power for segregation energy (R² ≈ 0).

**Context**: Grain boundary segregation is a critical phenomenon in materials science, influencing properties like embrittlement and corrosion. While individual impurity segregation is well-studied, the thermodynamic impact of *clustering* (spatial arrangement) remains less understood. This project aims to quantify this relationship using atomistic simulation data.

## 2. Dataset Strategy

**Critical Scientific Constraint**:
- **Circularity Prevention**: If segregation energy labels are generated via simulation (Potential A), the clustering descriptors MUST be computed from a structurally perturbed representation (e.g., different cutoff radius, distinct relaxation potential) OR the study must explicitly frame conclusions as "relative to Potential A" to avoid tautological validation.
- **No Heuristics**: Under no circumstances will heuristics (e.g., electronegativity rules) or surrogate models (e.g., GNNs) be used to generate target labels for the primary hypothesis test. If simulation is too slow, the sample size (N) will be reduced to a feasible number (N=20-50) rather than compromising scientific validity.

### Verified Sources & Usage Plan

| Dataset Name | Verified URL | Usage in Plan | Status |
|:--- |:--- |:--- |:--- |
| **OQMD Bulk Configs** | ` | Source of bulk crystal structures and compositions to initialize GB simulations. | **Used** (Source of bulk inputs) |
| **OQMD Bulk (Parquet)** | ` | Alternative source for bulk configuration metadata. | **Used** (Fallback) |
| **Unit Test Generator** | `code/tests/unit/generate_synthetic.py` | **Not a dataset**. A local script generates known atomic configurations with analytically calculable energies solely to verify the *code logic* of descriptor calculation and RMSE metric. | **Internal Tool** |
| **Literature DFT** | NO verified source found | **Not Used** as a primary source. If no verified DFT dataset exists for specific GB systems, the project proceeds with Potential A only, explicitly noting the limitation. | **Gap Acknowledged** |

**Gap Analysis & Mitigation**:
- **Missing Target Data**: The spec requires segregation energy labels which are absent from public repositories.
 - *Mitigation*: The pipeline (`code/data/gb_builder.py` and `code/data/simulate_energy.py`) will generate these labels using a lightweight atomistic simulation engine (e.g., LAMMPS via `ase` or a pre-trained potential if available in `pymatgen`).
 - *Fallback*: If the full simulation is too slow for the 6h CI limit, the plan will **reduce the sample size** to N=20-50 configurations. **NO surrogate models or heuristics will be used.** The study will proceed with a smaller dataset to maintain scientific validity.
- **Variable Fit**: We must ensure the bulk configurations from OQMD contain the necessary elements to form the impurities of interest.
 - *Action*: Filter OQMD entries to only those containing the specific alloy systems (e.g., Fe-C, Ni-S) required by the study.

## 3. Methodology

### 3.1 Data Pipeline (FR-001, FR-002, FR-003)
1. **Download**: Fetch bulk structures from OQMD via `wget`/`curl` with 3-retry logic (FR-001).
2. **GB Construction**: Use `pymatgen` to generate symmetric tilt GB supercells. Insert impurities at the interface.
3. **Simulation & Label Generation**:
 - Run energy minimization to relax the structure. Calculate segregation energy ($E_{seg} = E_{GB+imp} - E_{GB} - E_{imp} + E_{bulk}$).
 - **Independence Check**: To avoid circularity, if Potential A is used for energy, descriptors will be computed from a structure relaxed with a *different* potential (Potential B) or with a perturbed atomic configuration. If distinct potentials are unavailable, the study will explicitly limit claims to "Potential A internal consistency."
4. **Descriptor Computation**:
 - **RDF Peaks**: Compute Radial Distribution Function for impurity species within the interface region (defined as ±5Å from the GB plane).
 - **Pair Correlation**: Calculate $g(r)$ statistics.
 - **Voronoi Counts**: Count neighbors within the first coordination shell for each impurity.

### 3.2 Modeling & Validation (FR-004, FR-007)
- **Model**: Random Forest Regressor (preferred for non-linearity) or Linear Regression (for interpretability).
- **Confounding Control (Stratified Residualization)**:
 - GB geometry (plane orientation, misorientation angle) acts as a confounder.
 - **Mechanism**: First, fit a null model using only GB geometry features to predict segregation energy. Extract the **residuals** (observed - predicted) from this null model.
 - Train the primary clustering model on these **residuals**. This isolates the clustering effect from geometric variations.
- **Cross-Validation**: 5-fold if $N \ge 5$, else LOOCV.
- **Collinearity Check**: Compute Variance Inflation Factor (VIF). If VIF $\ge 10$, report joint relationship descriptively (FR-007).
- **Metrics**: R², RMSE, 95% Confidence Intervals.

### 3.3 Statistical Rigor (FR-005, FR-006, SC-001..005)
- **Hypothesis Testing**: Test significance of coefficients. Apply **Bonferroni correction** for multiple comparisons (number of predictors).
- **Sensitivity Analysis**: Sweep regularization strength ($\lambda$) or descriptor perturbation magnitude over 3 values (e.g., 0.01, 0.1, 1.0). Report RMSE variance and R² stability.
- **Power Limitation**: Acknowledge if sample size ($N$) is small.

#### 3.3.1 Power Analysis & Sample Size Justification
- **Minimum Sample Size**: A minimum of **N=30** is required.
- **Rationale**:
 - To perform 5-fold cross-validation with at least 6 samples per fold.
 - To detect an effect size (Cohen's f²) of 0.15 (medium) with 80% power at $\alpha=0.05$ for a regression with ~5 predictors.
 - This sample size is feasible within a defined computational time limit using classical potentials.
 - If N < 30 is forced by data availability, the study will explicitly state it is "underpowered to detect medium effects" and limit claims to exploratory trends.

## 4. Compute Feasibility Plan

The implementation targets a GitHub Actions free-tier runner (2 CPU, 7 GB RAM).
- **Data Sampling**: Limit the dataset to ~500-1000 configurations, with a hard minimum of N=30 for statistical validity.
- **Simulation Strategy**: Use classical potentials (EAM/MEAM) instead of DFT for energy calculation to ensure runtime < 6h. If DFT is mandatory by the spec, the plan will run on a **tiny subset** (e.g., 10-20 samples) and extrapolate, explicitly noting the limitation.
- **Model Training**: `scikit-learn` RandomForest with `n_estimators=100` is CPU-tractable for $N=1000$.
- **Memory Management**: Process data in chunks; do not load all raw structures into memory simultaneously.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Segregation Energy Generation** | High (Blocking) | Use classical potentials (EAM) as primary. If too slow, reduce N to 20-50. **NO heuristics/surrogates.** |
| **Dataset Availability** | Medium | Implement retry logic (3 attempts) and graceful degradation to `[DATA_UNAVAILABLE]` error. |
| **Collinearity** | Medium | Detect VIF; switch to descriptive reporting or PCA if predictors are linearly dependent. |
| **Runtime Exceeds 6h** | High | Pre-filter dataset to a manageable subset of samples; use single-threaded simulation if parallel overhead is too high. |
| **Circular Validity** | High (Fatal) | Enforce "Independence Check" (different potential/perturbation) or limit claims to "potential-dependent trends." |