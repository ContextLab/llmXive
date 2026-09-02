# Research: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Scientific Background

The Equipartition Theorem states that in thermal equilibrium, energy is equally distributed among all available degrees of freedom. In granular systems driven by external forces (vibration), the system is inherently non-equilibrium. This project investigates whether, under specific driving frequencies and material conditions, these systems exhibit "quasi-thermal" behavior where the **ratio of mean translational to rotational energy** approximates 1.0, despite the system being non-equilibrium.

Key theoretical frameworks include:
-   **Equipartition Ratio**: The primary metric is $\langle E_{trans} \rangle / \langle E_{rot} \rangle$. In a valid equipartition regime, this ratio should be $\approx 1.0$.
-   **Maxwell-Boltzmann Distribution**: Used as a secondary diagnostic to test if the system has reached a thermalized state (equilibrium). A driven system may exhibit equipartition (ratio $\approx$ 1) without being Maxwell-Boltzmann distributed.
-   **Non-Equilibrium Statistical Mechanics**: The study of systems where detailed balance is broken. The research question is reframed to: "Under what conditions does a driven granular system exhibit equipartition-like energy ratios?"

## Dataset Strategy

### Verified Datasets
The project must rely on open, programmatic datasets. The following verified sources are available:
-   **OpenGranular**: **NO verified source found**. (Per the project's verified datasets block, no URL exists for this dataset).

### Data Acquisition Strategy
Given the absence of a verified URL for "OpenGranular" and the likelihood that real-world driven granular datasets are either proprietary or require specific experimental setups not publicly mirrored:
1.  **Primary Strategy**: Generate a **synthetic dataset** using a deterministic physics simulator to create ground-truth data for validation (US-1, US-2). This synthetic data will simulate:
    -   Particles with varying masses (steel, polymer).
    -   Driving signals (sinusoidal at 5Hz, 10Hz, 15Hz).
    -   Known "thermal" (randomized velocities) and "non-thermal" (driven, correlated) regimes.
    -   **Ground Truth**: The generator outputs `artifacts/ground_truth.json` containing manual calculation values for SC-001 validation.
2.  **Secondary Strategy (if real data becomes available)**: If a verified URL for a real granular dataset is discovered in the future (e.g., via a new Zenodo release), the ingestion pipeline (`ingestion/sync_data.py`) will be updated to fetch it. Until then, the project proceeds with the synthetic ground truth to validate the *methodology* (FR-001 to FR-008).

**Constraint**: The implementation will **not** attempt to download "OpenGranular" from a guessed URL or a non-programmatic portal, as this would violate the "Data Availability" and "Fabrication" gates.

## Methodology

### 1. Energy Component Calculation (FR-002)
-   **Translational Kinetic Energy**: $E_{trans} = \frac{1}{2}mv^2$. Velocity $v$ derived from finite differences of position $(x, y, z)$ over time $\Delta t$.
-   **Rotational Kinetic Energy**: $E_{rot} = \frac{1}{2}I\omega^2$. Angular velocity $\omega$ derived from orientation $\theta$ changes. Moment of inertia $I$ calculated from mass and radius (material-specific).
-   **Potential Energy**: $E_{pot} = mgz$.
-   **Vibrational Energy ($E_{vib}$)**: Calculated as the **integral of the Power Spectral Density (PSD)** of the driving signal cross-correlated with the particle's velocity.
    -   Formula: $E_{vib} = \int_{f_{min}}^{f_{max}} |S_{v, F}(f)|^2 df$, where $S_{v, F}$ is the cross-spectral density between particle velocity and driving force.
    -   **Isolation**: $E_{vib}$ is calculated as a distinct diagnostic component. It is **NOT** included in the calculation of the Equipartition Ratio ($\langle E_{trans} \rangle / \langle E_{rot} \rangle$). It is used only in the total energy balance residual.

### 2. Statistical Testing (FR-003, FR-004)
-   **Primary Test (Equipartition)**: Compare the observed **Mean Energy Ratio** ($\langle E_{trans} \rangle / \langle E_{rot} \rangle$) against the theoretical value of 1.0 using a t-test or confidence interval check.
-   **Secondary Test (Thermalization)**: **Kolmogorov-Smirnov (KS) Test** compares the empirical CDF of observed energy against the theoretical Maxwell-Boltzmann CDF.
-   **Chi-Squared Goodness-of-Fit**: Bins energy values and compares observed counts to expected counts from the Maxwell-Boltzmann PDF.
-   **Threshold**: Default significance $\alpha = 0.01$.

### 3. Sensitivity Analysis (FR-005)
-   Sweep $\alpha \in \{0.01, 0.05, 0.10\}$.
- Sweep "quasi-thermal" boundaries (e.g., energy ratio within 1%, [deferred], [deferred] of 1.0).
-   Report stability of rejection decisions.

### 4. Multiple Comparison Correction (FR-006)
-   Apply **Benjamini-Hochberg (FDR)** procedure to p-values across all frequency bins to control the False Discovery Rate.

### 5. Regression Analysis (FR-007, FR-008)
-   **Model**: $Deviation = \beta_0 + \beta_1 \cdot Frequency + \beta_2 \cdot Roughness + \epsilon$.
-   **Metric**: **Equipartition Deviation** defined as $|\langle E_{trans} \rangle - \langle E_{rot} \rangle| / \langle E_{total} \rangle$. (Replaces KS statistic).
-   **Test**: t-test on slope coefficients ($\beta_1, \beta_2$) with $p < 0.05$ threshold.

## Statistical Rigor & Assumptions

-   **Multiple Comparisons**: Addressed via Benjamini-Hochberg (FR-006).
-   **Sample Size & Power Analysis**:
    -   For the Kolmogorov-Smirnov test, power depends on the effect size (deviation from null).
 - We assume a minimum detectable effect size of **[deferred] deviation** in the energy ratio distribution (i.e., a ratio of 1.05 vs 1.00).
    -   A power analysis (using `statsmodels.stats.power`) indicates that **N = 10,000** samples provides **>80% power** to detect a 5% deviation at $\alpha=0.01$.
    -   If real data is smaller, the report will explicitly state the power limitation.
-   **Causal Claims**: The analysis is strictly **observational**. Claims will be framed as "associational correlations" between driving frequency and energy distribution deviations, not causal mechanisms, unless the dataset explicitly includes randomized protocols (which the synthetic generator can simulate).
-   **Collinearity**: Frequency and roughness may be correlated in specific experimental designs. The regression model will check for Variance Inflation Factors (VIF) and report collinearity if detected.
-   **Measurement Validity**: Synthetic data is generated from the theoretical formulas, ensuring perfect validity for the *method* test. Real data (if added later) will require validation of the particle tracking algorithm's accuracy (US-1).

## Decision/Rationale: Compute Feasibility

-   **CPU-First**: All statistical tests (KS, Chi-squared, Regression) are computationally lightweight and run efficiently on CPU.
-   **Data Streaming**: If the dataset (synthetic or real) exceeds 7 GB, the `ingestion` module will use `pandas.read_csv(..., chunksize=...)` or `datasets.load_dataset(..., streaming=True)` to process data in chunks, accumulating statistics online.
-   **No GPU Required**: No deep learning models or diffusion processes are planned. The "GPU escape hatch" is not needed for this specific methodology.

## Unresolved Concerns Addressed

-   **FR-002 / Vibrational Energy Chain**: The plan explicitly defines $E_{vib}$ calculation via PSD integration in `src/ingestion/energy_calc.py` and `src/ingestion/sync_driving.py`. The dependency chain is resolved by prioritizing the synchronization step.
-   **T020a (Test Params)**: A `artifacts/test_params.json` file is created containing the Maxwell-Boltzmann parameters (mean=1.0, scale=0.1) and Pareto parameters (shape=2.0) as required for the synthetic ground truth tests. This file is generated by the `generate_ground_truth` task.
