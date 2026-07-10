# Research: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Executive Summary
This research plan details the methodology for validating the Equipartition Theorem in driven granular systems. The core hypothesis is that driven granular gases, unlike thermal systems, will exhibit a departure from equipartition (ratio of mean rotational to translational energy $\neq$ 1.0) and non-Maxwellian distribution shapes. The plan relies on computational analysis of particle tracking data.

## Dataset Strategy

### Verified Datasets
The following dataset is identified for use. **Note**: As per the verified datasets block, no URL is available for "OpenGranular". The implementation will rely on a **Synthetic/Placeholder Dataset** to validate the pipeline logic and statistical correctness. Final scientific claims are conditional on the availability of a real dataset (e.g., from Zenodo) that matches the schema.

| Dataset Name | Description | Source / Loader | Status |
| :--- | :--- | :--- | :--- |
| **Synthetic Granular Data** | Synthetic particle tracking data generated to match the required schema (positions, orientations, driving logs) for pipeline validation. | `code/tests/generate_synthetic_data.py` | **Primary for Implementation** |
| **OpenGranular** | Particle tracking data (positions, orientations) and driving logs for granular systems. | `data/raw/` (Local CSVs) | **NO VERIFIED URL** (Placeholder for future real data) |

**Critical Note on Dataset Fit**:
The spec assumes the dataset contains:
1.  High-frequency position data ($x, y, z$) and orientation ($\theta$).
2.  Driving signal logs (frequency).
3.  Material properties (mass, moment of inertia).

**Risk**: If the actual "OpenGranular" data provided in `data/raw/` lacks $z$-axis data or orientation ($\theta$), the calculation of $E_{pot}$ and $E_{rot}$ will be impossible.
**Mitigation**: The ingestion pipeline (`ingestion.py`) will include a validation step (FR-001) that checks for required columns. If missing, the pipeline will flag the dataset as "Incomplete for Full Analysis" and proceed only with available components (e.g., $E_{trans}$ only), explicitly logging the limitation in the final report. This prevents silent failure or hallucinated data.

## Methodology

### 1. Data Ingestion & Energy Calculation (FR-001, FR-002)
- **Input**: Particle tracking CSVs (time, x, y, z, theta, particle_id, material) and driving logs.
- **Processing**:
  - Synchronize data by timestamp (interpolate if necessary).
  - Compute velocities ($v_x, v_y, v_z$) and angular velocities ($\omega$) using finite differences (central difference for interior points, forward/backward for edges).
  - Calculate Energy Components:
    - $E_{trans} = \frac{1}{2} m v^2$
    - $E_{rot} = \frac{1}{2} I \omega^2$
    - $E_{pot} = m g z$
  - **Note on E_vib**: The "vibrational energy" component is **removed** from the primary hypothesis tests due to ambiguity in its physical definition for individual particles. It is redefined as a diagnostic residual ($E_{total} - E_{trans} - E_{rot} - E_{pot}$) for internal debugging only, not for statistical testing against Equipartition.
- **Handling Missing Data**:
  - If frames are missing >20% in a window: Exclude window (Edge Case handling).
  - If $z$ or $\theta$ missing: Flag and compute only available components (Constitution VI compliance).

### 2. Statistical Deviation Assessment (FR-003, FR-004)
- **Primary Hypothesis (Equipartition)**: $H_0$: The ratio of mean rotational energy to mean translational energy ($\mu_{E_{rot}} / \mu_{E_{trans}}$) is equal to 1.0. $H_1$: The ratio $\neq$ 1.0.
  - **Test**: One-sample t-test on the ratio of means, or a bootstrap confidence interval for the ratio.
- **Secondary Hypothesis (Distribution Shape)**: $H_0$: Energy distributions follow the Maxwell-Boltzmann (MB) shape.
  - **Test**: Kolmogorov-Smirnov (KS) test.
  - **Correction**: Since the MB temperature parameter ($T$) must be estimated from the data (via mean kinetic energy), standard KS p-values are invalid. The plan will use the **Lilliefors correction** (or a parametric bootstrap) to generate valid p-values.
  - **Multiple Comparison Correction**: Apply Benjamini-Hochberg (FDR) across frequency bins (FR-006).
  - **Chi-Squared Goodness-of-Fit**: Bin energy data and compare observed vs. expected counts.
- **Output**: P-values, test statistics, boolean rejection flags ($p < 0.01$).

### 3. Sensitivity Analysis (FR-005)
- **Threshold Sweep**: Re-run statistical tests with $\alpha \in \{0.01, 0.05, 0.10\}$.
- **Boundary Sweep**: Test "quasi-thermal" classification boundaries ([deferred], [deferred], [deferred] deviation from ratio 1.0).
- **Goal**: Ensure conclusions are robust to arbitrary threshold choices (US-3).

### 4. Regression Analysis (FR-007, FR-008)
- **Dependent Variables**: To avoid scale-dependence and circularity, the regression will model:
  1.  **Excess Kurtosis** of the energy distribution (a scale-invariant shape parameter).
  2.  **Mean Energy Ratio** ($\mu_{E_{rot}} / \mu_{E_{trans}}$).
- **Independent Variables**: Driving Frequency (continuous) and Material Type (categorical).
- **Model**: Linear regression (or ANOVA for categorical factors) to relate deviation metrics to frequency and material.
- **Significance**: t-tests on slope coefficients ($p < 0.05$).
- **Collinearity Check**: If frequency and material are correlated, report descriptive statistics and acknowledge collinearity rather than claiming independent effects.
- **Rationale**: Using excess kurtosis and energy ratios avoids the confounding of sample size (N) and provides a physically meaningful metric for "degree of non-thermal behavior."

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since tests are run across multiple frequencies and energy types, FDR correction is mandatory to control family-wise error rate (FR-006).
- **Power & Sample Size**: The plan mandates a **Power Analysis**. A minimum sample size of **N >= 1000 per bin** is required for the KS test to detect a medium effect size (Cohen's h) with [deferred] power. If the dataset cannot provide this, the plan will explicitly flag the study as 'Underpowered' and limit conclusions to descriptive statistics rather than hypothesis testing.
- **Causal Inference**: The study is **observational**. Claims will be framed as "associational correlations" between driving parameters and energy deviations. No causal mechanisms will be claimed unless the dataset includes randomized forcing (Spec Assumption).
- **Measurement Validity**: Energy calculations rely on finite differences. The plan assumes the sampling rate ($\ge$ 100 Hz) is sufficient to resolve velocities without aliasing (Spec Assumption).
- **Collinearity**: If "Material Type" is used as a proxy for roughness, it is treated as a categorical factor (dummy variables) rather than a continuous linear proxy, acknowledging the non-linear relationship between surface geometry and energy transfer.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (multiple CPU, ample RAM).
- **Strategy**:
  - **Sampling**: If raw data > 1 GB, the ingestion script will randomly sample rows to fit within memory (e.g., 100k-500k particles), ensuring N > 1000 per bin.
  - **Libraries**: `scipy.stats` (KS, Chi-sq), `statsmodels` (LinearRegression, Lilliefors), `pandas`. All are CPU-native.
  - **No GPU**: No deep learning or CUDA operations.
  - **Runtime**: Target < 2 hours for full pipeline on sampled data.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Data Priority** | Ensures pipeline correctness in the absence of a verified real dataset URL. |
| **Lilliefors Correction** | Required for valid KS p-values when parameters (T) are estimated from the same data. |
| **Excess Kurtosis & Ratios** | Provides scale-invariant, physically meaningful metrics for regression, avoiding sample-size confounding. |
| **Categorical Material** | Correctly models the non-linear relationship between material type and roughness without forcing a linear proxy. |
| **Power Analysis** | Prevents Type II errors by enforcing a minimum N requirement for statistical validity. |
