# Research: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## 1. Scientific Background & Literature Review

The shape of dark matter haloes is a fundamental prediction of the Cold Dark Matter (CDM) paradigm, typically characterized by triaxiality rather than perfect sphericity. Theoretical models suggest that halo shape influences the accretion of gas and the subsequent formation of central galaxies, potentially affecting Star Formation Rates (SFR) and morphological properties. However, disentangling shape effects from the dominant confounder of halo mass is challenging.

Key literature establishes the methodology for shape measurement via the reduced inertia tensor of dark matter particles within the virial radius (e.g., `arxiv.org/abs/1907.11775v1`). This project adopts this standard method to compute axial ratios ($b/a$, $c/a$) and triaxiality ($T$). **Crucially, all results will be framed as associational evidence; no causal inference is claimed.**

## 2. Dataset Strategy

The analysis relies on two primary cosmological simulation datasets. Per the verified datasets list, we utilize the specific sources below.

**Verified Datasets:**
*   **IllustrisTNG-100**: The primary dataset. We will use the standard `tng` API or direct download from the IllustrisTNG website (`https://www.tng-project.org/data/`) as the canonical source.
*   **Millennium-II**: **CRITICAL GAP**: The provided "Verified datasets" block does not contain a URL for Millennium-II.
    *   **Protocol**: The pipeline will attempt to load Millennium-II via standard loaders (e.g., `datasets.load_dataset("millennium")` if available) or check the standard archive.
    *   **Fallback**: If no verified URL exists in the provided block, the dataset is treated as **unavailable**. The pipeline will **skip** the cross-validation step (FR-007), log a "Data Gap" report, and proceed with TNG-100 only. This prevents silent failure or hallucination.
*   **Warm Dark Matter (WDM) Variants**: The plan will check for WDM snapshots in the TNG-100 or Millennium-II archives. If unavailable, the plan will document the absence as a limitation rather than failing the requirement.

**Dataset Variable Fit Check:**
*   **Required Variables**: Dark matter particle positions (for inertia tensor), Halo mass, Subhalo stellar mass, SFR, Effective radius, Spin vectors.
*   **TNG-100 Availability**: Confirmed to contain all required variables via the public API.
*   **Millennium-II Availability**: Contains halo/subhalo catalogs; spin vectors and SFR may require specific sub-catalogs. We will verify variable presence before full ingestion.

## 3. Methodology

### 3.1 Halo Shape Computation (FR-001, FR-002)
For each FoF halo with $N_{DM} \ge [deferred]$:
1.  Select dark matter particles within the virial radius ($R_{200m}$).
2.  Compute the reduced inertia tensor $I_{ij} = \sum_k \frac{x_{i,k} x_{j,k}}{r_k^2}$ iteratively (3-5 iterations) to converge on the principal axes.
3.  Calculate eigenvalues $\lambda_1 \ge \lambda_2 \ge \lambda_3$.
4.  Derive axial ratios: $b/a = \sqrt{\lambda_2/\lambda_1}$, $c/a = \sqrt{\lambda_3/\lambda_1}$.
5.  Compute triaxiality: $T = \frac{1 - (c/a)^2}{1 - (b/a)^2}$.

### 3.2 Binning and Mass Control (FR-003, FR-012)
*   **Primary Method (Regression)**: To avoid selection bias and power loss from aggressive mass-matching, the primary analysis will use **multivariate linear regression** (FR-011): $Property \sim \beta_0 + \beta_1(c/a) + \beta_2(\log M_{halo}) + \epsilon$. This controls for mass continuously.
*   **Secondary Method (Binning)**: Binning by $c/a$ (Prolate: $c/a < 0.5$, Triaxial: $0.5 \le c/a \le 0.8$, Spherical: $c/a > 0.8$) will be used for visualization and robustness checks.
*   **Low-Power Handling**: If mass-matching (stratification) results in insufficient sample size (<30 per bin), the analysis will fall back to regression-only and flag the bin as "Underpowered" rather than discarding data.

### 3.3 Statistical Analysis (FR-004, FR-005, FR-011)
*   **Family of Hypotheses**: Defined as 2 properties (SFR, Radius) × 3 tests (Kruskal-Wallis, Mann-Whitney, KS) + 1 Regression coefficient test = **7 tests**.
*   **Hypothesis Tests**:
    *   **Kruskal-Wallis H-test**: Compare distributions of SFR/Radius across the three shape bins.
    *   **Mann-Whitney U-tests**: Pairwise comparisons.
    *   **Kolmogorov–Smirnov (KS) Test**: Compare cumulative distributions.
*   **Multiple Comparison Correction**: Apply Bonferroni correction across the **total family (k=7)**. $p_{adj} = p \times 7$.
*   **Regression**: Linear regression with mass as a covariate.
*   **Significance Thresholds**: $p < 0.01$ for primary tests; $p < 0.05$ for misalignment (SC-006).

### 3.4 Sensitivity Analysis (FR-006, SC-003)
*   **Threshold Sweep**: Sweep binning thresholds over $\{0.45, 0.55, 0.75, 0.85\}$.
*   **Robustness Metric**: Instead of arbitrary p-value variance, we measure the **stability of the effect size**.
    *   **Decision Rule**: Findings are robust if the **sign** of the regression coefficient for triaxiality remains consistent across the sweep AND the **95% Confidence Interval** of the coefficient overlaps with the primary analysis CI.
    *   This ensures the physical trend is stable, not just the p-value.

### 3.5 Orientation Misalignment (FR-009, FR-010, SC-006)
*   Compute spin vectors for halo and galaxy.
*   Calculate angle $\theta = \arccos(\vec{S}_{halo} \cdot \vec{S}_{galaxy})$.
*   Correlate $\theta$ with SFR and Radius using Spearman correlation.

### 3.6 Null Simulation Control (Scientific Soundness)
*   **Purpose**: Distinguish physical correlation from simulation artifacts.
*   **Method**: Randomly shuffle galaxy properties (SFR, Radius) relative to halo shapes (keeping the marginal distributions identical).
* **Execution**: Repeat the primary regression analysis on [deferred] shuffled datasets.
*   **Outcome**: If the observed effect size falls outside the confidence interval of the null distribution, the correlation is unlikely to be a simulation artifact.

## 4. Computational Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB Disk).
*   **Strategy**:
    *   **No GPU**: All libraries (numpy, scipy) are CPU-native.
    *   **Chunking**: Data loaded in chunks of haloes to stay under 6 GB RAM.
 * **Sampling**: If full TNG-100 exceeds time limits, a random sample of [deferred] haloes will be used for the primary analysis, with the full set processed if time permits.
    *   **Libraries**: `h5py` for HDF5 reading (TNG format), `pandas` for tabular manipulation, `scipy.stats` for tests. No deep learning frameworks.

## 5. Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Millennium-II Data Unavailable** | Cannot satisfy FR-007 (Cross-validation). | **Data Gap Protocol**: If no verified URL exists, the pipeline skips cross-validation, logs the gap, and proceeds with TNG-100 only. SC-004 marked "Not Measurable". |
| **Memory Overflow** | Pipeline crash on 7GB limit. | Strict chunking; discard intermediate arrays immediately; use `dtype=float32` where precision allows. |
| **Inertia Tensor Singularities** | Numerical errors for low-N haloes. | Exclude haloes with $N < 10,000$ (FR-002); add small regularization term if necessary. |
| **False Positives** | Spurious correlations due to multiple testing. | Strict Bonferroni correction (FR-005) across the defined family of tests; Null Simulation Control. |
| **Binning Bias** | Discretizing continuous variables reduces power. | Primary analysis uses multivariate regression; binning is secondary for visualization only. |

## 6. Decision Log

| Date | Decision | Rationale |
| :--- | :--- | :--- |
| 2026-06-25 | Use `scipy.stats` for all tests | Native CPU support, no external heavy dependencies, meets FR-004. |
| 2026-06-25 | Exclude $N_{DM} < 10,000$ | Ensures resolution validity per FR-002 and Assumptions. |
| 2026-06-25 | Apply Bonferroni Correction (k=7) | Required by FR-005 to control family-wise error rate across the defined family of tests. |
| 2026-06-25 | Chunked Processing | Mandatory for 7GB RAM constraint (Assumptions). |
| 2026-06-25 | Regression-First Mass Control | Avoids selection bias and power loss from aggressive mass-matching. |
| 2026-06-25 | Null Simulation Control | Distinguishes physical correlation from simulation artifacts. |
| 2026-06-25 | Effect Size Stability Metric | Replaces arbitrary p-value variance with a statistically sound robustness metric. |