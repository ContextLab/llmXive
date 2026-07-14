# Research: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Scientific Context

The search for Time-Reversal (T) violation in nuclear beta decay is a critical test of the Standard Model and a probe for new physics (e.g., scalar or tensor currents). The D-coefficient represents a T-odd, P-odd correlation in the decay distribution. While the Standard Model predicts a negligible D-coefficient (effectively zero), many Beyond Standard Model (BSM) theories predict non-zero values.

This project does not perform new experiments but instead synthesizes existing archival data to determine if a combined analysis reveals a statistically significant deviation from zero or establishes a tighter upper bound than individual experiments.

## Dataset Strategy

The project relies on the Particle Data Group (PDG) Reviews as the primary source for published D-coefficients.

| Dataset Name | Description | Source / URL | Usage |
|:--- |:--- |:--- |:--- |
| **PDG 2024 Review** | Particle Data Group 2024 Review of Particle Physics. Contains the latest published D-coefficients for 6He, 19Ne, etc. | ` (Official PDF) | Primary source for D-coefficient values, uncertainties, and experiment references. |
| **PDG 2022 Review** | Particle Data Group 2022 Review of Particle Physics. | ` | Reference for validation (comparing derived upper bounds against the *previous* world average to avoid circularity). |
| **NNDC ENSDF** | Evaluated Nuclear Structure Data File. | ` | Used for structural data (mass numbers, decay modes) to validate nucleus identity. **NOT** used for D-coefficients directly, as these are derived parameters found in PDG/arXiv and are not machine-readable in ENSDF. |

**Dataset Fit Assessment**:
- The PDG 2024 Review is the canonical source for *published* D-coefficients. It aggregates the specific values required by the spec.
- The PDG 2022 Review is used for validation to ensure the new meta-analysis (using 2024 data) is not compared to a 2024 average derived from the same data (avoiding circularity).
- The NNDC ENSDF is used only to confirm the existence and properties of the nuclei (e.g., 6He, 19Ne) but does not expose the D-coefficient directly in a machine-readable format.
- *Constraint*: If the PDG 2024 PDF cannot be parsed (e.g., layout changes) or the network is unreachable, the system **MUST NOT** proceed with mock data for scientific results. Instead, it must flag the analysis as "Failed to retrieve primary source" and halt. Mock data in `data/raw/mock_pdg_2024.json` is strictly for **unit testing the pipeline logic** in CI environments where the PDG API is unreachable, ensuring the code runs without crashing, but results derived from mock data are marked as "Test Mode" and excluded from scientific claims.

## Methodology

### 1. Data Retrieval & Harmonization (FR-001)
- **Mechanism**: HTTP GET requests to PDG web pages or parsing of the official PDF (using `pdfplumber` or `tabula-py`).
- **Handling Missing Data**: If a specific nucleus (e.g., 6He) has no D-coefficient data in the 2024 Review, the script flags it as "insufficient data" and excludes it from the meta-analysis (User Story 1, Scenario 3).
- **Range Handling**: If a D-coefficient is reported as a range $[a, b]$, the midpoint $(a+b)/2$ is used as the value, and $(b-a)/2$ is used as the uncertainty.

### 2. Meta-Analysis & Hypothesis Testing (FR-002, FR-003)
- **Method**: Inverse-variance weighting.
 - Weight $w_i = 1 / \sigma_i^2$.
 - Combined value $\bar{D} = \frac{\sum w_i D_i}{\sum w_i}$.
 - Combined uncertainty $\sigma_{\bar{D}} = \sqrt{1 / \sum w_i}$.
- **Formal Hypothesis Test (Z-test)**:
 - **Null Hypothesis ($H_0$)**: The true D-coefficient is zero (Standard Model prediction).
 - **Test Statistic**: $Z = \bar{D} / \sigma_{\bar{D}}$.
 - **Decision Rule**:
 - **If** $|Z| \ge 1.96$ (p < 0.05): The system reports a **non-zero result** (potential T-violation) with the value $\bar{D} \pm \sigma_{\bar{D}}$.
 - **If** $|Z| < 1.96$ (p >= 0.05): The system reports a **null result** (consistent with SM) and calculates the 95% confidence interval upper bound as $|D| < 1.96 \sigma_{\bar{D}}$ (or $|\bar{D}| + 1.96 \sigma_{\bar{D}}$ depending on convention, but explicitly labeled as a limit). This satisfies User Story 2 Scenario 3.
- **Upper Bound**: The 95% confidence interval upper bound is calculated as $|\bar{D}| + 1.96 \sigma_{\bar{D}}$ (assuming a normal approximation). If the mean is consistent with zero, the bound is reported as $|D| < X$.

### 3. Consistency & Sensitivity (FR-004, FR-005)
- **Cochran's Q Test**: Used to detect heterogeneity.
 - **Constraint**: Only performed if all measurements are for the **same nucleus**. If mixing nuclei (e.g., 6He and 19Ne), Q is skipped as the "true effect" is not identical.
 - **Constraint**: Only performed if $n \ge 2$.
 - $Q = \sum w_i (D_i - \bar{D})^2$.
 - P-value derived from $\chi^2$ distribution with $k-1$ degrees of freedom.
 - **Shuffle Fallback**: If $n < 5$ and the p-value is borderline (0.01 < p < 0.1), perform a sufficient number of shuffles of the weights to estimate the p-value empirically (as per FR-004). This is for heterogeneity, not the primary T-violation test.
- **Sensitivity Limit**: Calculated as the inverse-variance weighted average of individual uncertainties.

### 4. Validation (FR-006)
- **PDG Comparison**: The derived upper bound is compared against the **PDG 2022 Review** limit (previous edition). If the new bound is looser (larger) than the 2022 limit, a flag is raised. This avoids circularity by comparing new data against the old world average.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Not applicable in the traditional sense as we are testing a single parameter (D) across multiple experiments. However, if multiple nuclei are tested, a Bonferroni correction will be applied to the significance threshold for the combined result.
- **Power Justification**: The power of the meta-analysis is limited by the precision of the archival data. We acknowledge that if the archival uncertainties are large, the combined bound may not be sensitive to BSM physics. This is explicitly reported as a "sensitivity limit" rather than a discovery.
- **Causal/Associational**: This is a meta-analysis of observational (archival) results. Claims are strictly associational (e.g., "The combined data limits D to..."). No causal inference is made beyond the statistical aggregation.
- **Collinearity**: N/A. Each measurement is from a distinct experiment with distinct systematic uncertainties.

## Compute Feasibility

- **CPU Only**: All operations (HTTP requests, pandas operations, scipy stats) are CPU-bound and lightweight.
- **Memory**: The dataset size is negligible (< 1 MB). The entire pipeline fits easily within 7 GB RAM.
- **Runtime**: Estimated runtime < 5 minutes.
- **Dependencies**: `requests`, `pandas`, `scipy`, `numpy`, `pyyaml` are all available on free-tier runners and do not require GPU.