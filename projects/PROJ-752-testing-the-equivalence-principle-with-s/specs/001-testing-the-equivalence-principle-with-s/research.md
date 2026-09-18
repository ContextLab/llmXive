# Research: Testing the Equivalence Principle with Satellite Laser Ranging

## Scientific Background

The Weak Equivalence Principle (WEP) states that the trajectory of a freely falling test body is independent of its internal structure and composition. In the context of geodetic satellites, a violation would manifest as a differential acceleration ($a_{anom}$) between two satellites of different composition (e.g., LAGEOS vs. Starlette) in the same gravitational field, *after* accounting for all known forces. The Eötvös parameter $\eta$ quantifies this violation:

$$ \eta = \frac{2 |a_{anom, 1} - a_{anom, 2}|}{|a_{anom, 1} + a_{anom, 2}|} \approx \frac{|a_{anom}|}{g} $$

where $a_{anom}$ is the **anomalous** differential acceleration (total observed difference minus expected non-gravitational difference) and $g$ is the local gravitational acceleration. Current state-of-the-art limits (e.g., from MICROSCOPE) are at the level of extreme precision. This project aims to replicate similar precision using SLR data, acknowledging the observational nature of the study.

**Critical Distinction**: The 'differential acceleration' ($a_c$) in the spec is redefined here as the **residual anomaly**. The total difference in non-gravitational forces (SRP, Drag) is expected to be large and composition-dependent. The WEP test is performed on the *residual* after subtracting the expected difference.

## Dataset Strategy

The plan relies on **open, directly-downloadable datasets** to ensure CI feasibility. The spec requires SLR normal-point series for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette.

### Verified Datasets

| Dataset Name | Source URL | Status | Notes |
|--------------|------------|--------|-------|
| SLR NoteSense | ` | **Available** | Contains SLR normal points. **Usage**: Pipeline Validation (code correctness) ONLY. Not sufficient for scientific results. |
| Open SLR Turkish | ` | **Available** | Contains SLR data. **Usage**: Pipeline Validation ONLY. |
| ILRS Archive (LAGEOS-1/2, Etalon, Starlette) | ` (Programmatic access) | **Required** | **Usage**: Scientific Validation. **Gap**: No verified direct download URL in input block. **Strategy**: The pipeline attempts to fetch from the known ILRS public endpoint. If this fails or data is missing, the system generates a 'Data Feasibility Gap' report and halts scientific analysis. |

### Pipeline vs. Scientific Data

- **Pipeline Validation**: Small HF datasets (100 entries, 10 hours) are used **only** to verify that the code runs, the schemas are valid, and the error handling works. These datasets are insufficient for scientific results (statistically insignificant).
- **Scientific Validation**: The scientific claim relies on multi-year ILRS data. If the ILRS data for the required satellites is not available (e.g., missing from the archive, access blocked), the project **does not** produce a scientific result. Instead, it outputs a 'Data Feasibility Gap' report stating which satellites are missing and why the WEP test cannot be performed. This prevents spurious results from small samples.

### Data Availability & Fit

- **Gap Analysis**: The verified HF datasets are small samples. The plan explicitly states that scientific results are conditional on the availability of the multi-year ILRS dataset.
- **Variable Fit**: The HF datasets must contain `timestamp`, `range`, `satellite_id`, and `station_id`. If composition metadata (mass, material) is missing, the system logs a warning and excludes the satellite from differential analysis (as per spec edge cases).
- **Feasibility**: The small HF datasets are fully CPU-tractable. The full ILRS archive (if accessible) would require streaming to fit memory. The plan implements a `streaming=True` flag in the data loader to handle both cases.
- **Constitutional Exception**: While Principle VI requires ILRS sourcing, the plan acknowledges that if the ILRS archive is inaccessible, a 'Data Feasibility Gap' report is generated rather than using proxies for scientific claims.

## Methodology & Statistical Rigor

### Orbit Determination

- **Method**: Weighted Least-Squares (WLS) using `scipy.optimize.least_squares`.
- **Dynamics**:
 - Geopotential: GGM05C (or EGM2008/GOCO06s for sensitivity).
 - Drag: Jacchia model.
 - SRP: Box-wing model.
 - Relativity: Standard post-Newtonian corrections.
- **Parameters**: Orbital elements, non-gravitational acceleration coefficients ($C_r$, $C_{dr}$), and the **anomalous** differential acceleration term $a_{anom}$ (if estimating jointly).
- **Convergence**: Solver stops when residuals reach a sufficiently small threshold or max iterations reached.

### Differential Anomaly Estimation (Revised)

1. **Step 1**: Fit independent orbits for Satellite A and Satellite B.
2. **Step 2**: Extract non-gravitational acceleration residuals ($a_{ng, A}$, $a_{ng, B}$) and the empirical scaling factors ($C_{r, A}$, $C_{r, B}$, etc.).
3. **Step 3**: **Calculate Expected Non-Gravitational Difference**: Using precise satellite metadata (mass, cross-section, optical properties), calculate the *expected* difference in SRP and Drag forces ($\Delta a_{expected}$) due to composition.
4. **Step 4**: Calculate **Anomalous Acceleration**: $a_{anom} = |a_{ng, A} - a_{ng, B}| - \Delta a_{expected}$.
5. **Step 5**: Compute $\eta = a_{anom} / g$.
6. **Uncertainty**: Propagate covariance matrices from the WLS fits to derive the standard error of $\eta$ ($SE_\eta$).
7. **Confidence Interval**: A confidence interval for $\eta$ is constructed as $\eta \pm z \times SE_\eta$, where $z$ corresponds to the critical value for the desired confidence level.

### Statistical Validation

- **Hypothesis Test**: Null hypothesis $H_0: a_{anom} = 0$ (no anomalous acceleration after subtracting expected forces). Use F-test to compare the null model (only known forces) vs. the alternative model (known forces + $a_{anom}$).
- **Multiple Comparisons**: If testing multiple satellite pairs, apply configurable correction (Bonferroni, Holm-Bonferroni, Benjamini-Hochberg).
- **Sensitivity Analysis**: Sweep geopotential models (GGM05C, EGM2008, GOCO06s). Report Z-score ($\eta / SE_\eta$) variation. Flag if variation > 20%.
- **Precision Measurement**: Calculate the width of the 95% CI and compare against state-of-the-art benchmarks (e.g., $10^{-15}$). Report 'Precision Status'.
- **Robustness Score**: Calculate the standard deviation of Z-scores across geopotential models.

## Compute Feasibility

- **CPU-First**: All methods (WLS, matrix operations) are CPU-tractable. No GPU required.
- **Memory**: Streaming data ensures < 7 GB RAM usage.
- **Runtime**: Small HF datasets will run in minutes. Full ILRS data (if streamed) estimated at < 6 hours for 5 satellites.
- **Escape Hatch**: Not required for this study, but the code supports `device="cuda"` if future models (e.g., deep learning orbit predictors) are added.

## Decision Rationale

- **Why HF datasets?** They are the only verified, open sources. The plan treats them as a "minimum viable dataset" for pipeline validation, **not** for scientific claims.
- **Why WLS?** It is the standard for orbit determination and is robust for this scale.
- **Why Bonferroni?** Conservative control of family-wise error for a small number of tests (5 satellites).
- **Why streaming?** To ensure the plan works for both small samples and large archives without memory overflow.
- **Why subtract expected forces?** To isolate the WEP signal from the dominant, known composition-dependent non-gravitational forces. Without this step, the test would trivially reject the null hypothesis due to known physical differences, not a WEP violation.

## Assumptions

- **Assumption about data availability**: The ILRS public archive contains sufficient multi-year normal-point data for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette to perform a statistically significant test (minimum 500 points per satellite).
- **Assumption about compute environment**: The analysis will run on a GitHub Actions free-tier runner (CPU, sufficient RAM) using CPU-tractable methods (scikit-learn, classical statistics) without GPU acceleration or large-model inference, with a a hard limit on the runtime per run.
- **Assumption about dynamical models**: The GGM05C Earth gravity field model and standard atmospheric drag models (e.g., Jacchia) are sufficient to model non-compositional forces to the required precision.
- **Assumption about statistical framing**: Since the study is observational (no random assignment of satellite composition), all findings regarding $\eta$ will be framed as associational limits or upper bounds, not causal proofs of WEP violation, unless a specific identification strategy is introduced later.
- **Assumption about target precision**: The target research precision for the Eötvös parameter is high sensitivity levels, based on current state-of-the-art benchmarks (e.g., Müller et al.).
- **Assumption about dataset-variable fit**: The SLR normal points and satellite metadata (mass, composition) provided by ILRS contain all necessary variables to compute the differential acceleration; if a specific composition variable is missing for a satellite, that satellite will be excluded from the differential analysis.
