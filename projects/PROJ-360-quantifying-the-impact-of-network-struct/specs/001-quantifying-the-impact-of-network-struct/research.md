# Research: Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids

## 1. Dataset Strategy

### Verified Datasets
The primary data source is the **Materials Project** database.
*   **Access Method**: Programmatic access via the `pymatgen` library (`MPRester`), which handles authentication, rate limiting, and data retrieval.
*   **Verified Source**: The `pymatgen` library interfaces with the official Materials Project API. Direct static URL access to the API endpoint is restricted without valid API keys.; therefore, the research plan relies on the library's authenticated session, which is the verified method for accessing this data in a reproducible research context.
*   **Dataset Content**: Crystallographic Information Files (CIF) and associated metadata including thermal conductivity tensors ($k_x, k_y, k_z$).

### Variable Fit Verification
*   **Required Variables**:
    1.  Crystal structure (atomic positions, unit cell) -> **Available** in CIF.
    2.  Thermal conductivity tensor -> **Available** in Materials Project metadata (experimental or DFT-calculated).
    3.  Covalent radii -> **Available** in `pymatgen` periodic table data.
    4.  Physical Descriptors (Volume, Mass) -> **Available** via `pymatgen` structure analysis.
*   **Fit Assessment**: The dataset contains all necessary variables for constructing atomic networks and performing the required correlation analysis, including controls for confounding physical factors. No missing variable gaps identified.

## 2. Methodology

### Phase 1: Network Construction
1.  **Download**: Query Materials Project for materials with thermal conductivity data. Apply retry logic (exponential backoff) for rate limits.
2.  **Bond Detection**: Use `pymatgen`'s covalent radius summation ($r_i + r_j + 0.4\text{\AA}$) to define edges.
3.  **Fallback**: If no bonds found, increase cutoff to 4.0\AA, then 4.5\AA. Skip if still disconnected.
4.  **Graph Creation**: Construct `networkx.Graph` objects.

### Phase 2: Metric Computation & Confounder Control
Compute for each graph:
*   **Network Metrics**:
    *   **Average Degree**: $\frac{2 \times |E|}{|V|}$.
    *   **Average Shortest Path Length**: Computed on the **Largest Connected Component (LCC)**. If graph is disconnected, report `NaN` (see Missing Data Strategy).
    *   **Clustering Coefficient**: Global average clustering.
*   **Physical Descriptors (Confounding Controls)**:
    *   **Unit Cell Volume**: Calculated from lattice parameters.
    *   **Total Atom Count**: Number of nodes in the graph.
    *   **Mean Atomic Mass**: Average atomic mass of constituent elements.
*   **Missing Data Strategy**:
    *   For disconnected graphs where path length is `NaN`:
        *   If $n_{connected} > 5$, impute with the median path length of connected materials.
        *   If $n_{connected} \le 5$, exclude the material from the specific correlation analysis for this metric, but retain it for others.

### Phase 3: Statistical Analysis
*   **Scalarization**: Thermal conductivity $\kappa = \frac{k_x + k_y + k_z}{3}$.
*   **Distribution Check**: Perform Shapiro-Wilk test. If $p < 0.05$, apply log-transformation to $\kappa$ and metrics.
*   **Correlation**: Compute Pearson and Spearman coefficients between each metric (and physical descriptors) and $\kappa$.
*   **Multiplicity Control**: Apply Bonferroni correction ($\alpha_{adj} = 0.05 / 3$) to control family-wise error rate.
*   **Collinearity Check**: Calculate Variance Inflation Factor (VIF) for all predictors. Exclude features with VIF $\ge 5$.
    *   *Note on Metric Coupling*: Acknowledged that degree, path length, and clustering are topologically coupled in lattices. These are analyzed as a correlated set; VIF filtering is a diagnostic, not a guarantee of independence.
*   **Regression**: Train Linear Regression on filtered features (network metrics + physical descriptors).
*   **Validation**: 5-fold Cross-Validation (stratified by material class if possible, otherwise random) on CPU.

## 3. Power & Sample Size Considerations

*   **Target Sample**: $n \ge 50$.
*   **Power Limitation**: With $n=50$ and 3-5 predictors, the study has limited power to detect small effect sizes ($R^2 < 0.15$).
*   **Protocol**:
    *   If $n < 50$, a warning is logged in `results/power_analysis.log` acknowledging reduced power.
    *   If observed $R^2 < 0.30$, the result is interpreted as "weak predictive power, consistent with null hypothesis or insufficient sample size," rather than a robust finding.
    *   Effect sizes are reported with 95% confidence intervals.

## 4. Statistical Rigor & Limitations

*   **Multiple Comparisons**: Bonferroni correction applied to the 3 correlation tests.
*   **Causal Claims**: The study is observational. All conclusions are framed as associations.
*   **Measurement Validity**: Thermal conductivity values are taken directly from the database; network metrics are standard graph-theoretic definitions.
*   **Confounding**: Physical descriptors (volume, mass, atom count) are included as controls to prevent topology metrics from acting as proxies for size effects.
*   **Limitations Section**: The final report will explicitly state: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects."

## 5. Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (limited CPU, constrained RAM).
*   **Strategy**:
    *   Data is processed in a streaming manner (one CIF at a time) to minimize RAM.
    *   No GPU required; `networkx` and `scikit-learn` are CPU-optimized.
    *   Dataset size (a limited number of materials) is trivial for memory.
    *   Estimated runtime: < 1 hour.

## 6. Decision Log

| Decision | Rationale |
|----------|-----------|
| Use `pymatgen` for API access | Direct URL access returns 403; library handles auth and rate limits correctly. |
| Scalarize thermal conductivity | Required by spec (FR-004) to enable univariate correlation. |
| Bonferroni correction | Required by spec (FR-005) for 3 tests. |
| VIF threshold 5 | Standard threshold for multicollinearity (FR-009). |
| CPU-only execution | Constraint of the execution environment (SC-005). |
| Impute NaN for path length | Preserves sample size for other metrics while acknowledging missingness. |
| Include physical descriptors | Controls for confounding size/mass effects (Scientific Soundness). |
| Log-transform if non-normal | Ensures validity of Pearson correlation and regression assumptions. |