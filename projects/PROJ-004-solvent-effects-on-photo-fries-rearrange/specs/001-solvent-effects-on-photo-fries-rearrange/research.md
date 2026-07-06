# Research: Solvent Effects on Photo-Fries Rearrangement Kinetics

## Executive Summary

This research phase validates the dataset strategy, statistical methodology, and computational feasibility for investigating solvent effects on Photo-Fries rearrangement kinetics. The study aims to correlate solvent polarity (dielectric constant, $\epsilon$) and computed solvation free energy ($\Delta G_{solv}$) with the experimentally derived lifetime ($\tau$) of the singlet-radical-pair intermediate.

**Key Finding**: The study is **observational** (no random assignment of solvents to conditions in a causal trial sense; solvents are intrinsic properties). Therefore, all claims will be framed as **associational**. Causal inference (e.g., "Solvent X *causes* lifetime Y") is explicitly avoided unless a randomized experimental design is introduced (which is not the case here).

## Dataset Strategy

The project relies on a hybrid dataset: **Simulated Experimental Data** (for kinetic traces) and **Computed DFT Data** (for solvation energies).

### 1. Simulated Transient-Absorption Data (Kinetic Traces)
*   **Source**: Generated programmatically via `code/data/loaders.py` using a deterministic random seed to mimic laser flash photolysis outputs.
*   **Rationale**: Real experimental data is not available in the "Verified datasets" block for this specific project. The spec requires a pipeline that *would* process such data. We generate synthetic traces with known parameters ($\tau_{true}$) to validate the fitting algorithms.
*   **Validation Strategy (Null Hypothesis)**: To avoid circular validation where the synthetic data embeds the hypothesis, the primary synthetic dataset is generated with **no correlation** between solvent properties and lifetime. Lifetimes are drawn from a broad uniform distribution independent of solvent polarity. This allows the pipeline to be tested for its ability to correctly report "no correlation" (validating the absence of false positives). A separate "positive" test case is used only for unit testing the regression code, not for the main research output.
*   **Variables**: Time (ns), Absorbance (AU), Wavelength (nm), Solvent ID, Temperature, Humidity.
*   **Coverage**: 5-10 solvents, 3 replicates each (n=3).
*   **Verification**: The "Verified datasets" block in the user message contains **no** URL for a real-world Photo-Fries kinetic dataset. Therefore, we rely on the **synthetic generation** strategy, which is standard for pipeline validation in the absence of public benchmarks for this specific reaction.

### 2. Computed Solvation Energies (DFT)
*   **Source**: `code/data/compute/` (simulated output of B3LYP/6-31G* SMD/PCM calculations).
*   **Rationale**: The spec (FR-005) requires implicit (SMD/PCM) models for $\le 80\%$ and explicit for $\ge 20\%$. We generate these values programmatically to simulate the output of a quantum chemistry package (e.g., Gaussian or ORCA).
*   **Variables**: Solvent ID, $\Delta G_{solv}$ (kcal/mol), Dielectric Constant ($\epsilon$), Method (SMD/PCM).
*   **Verification**: No external dataset URL exists for pre-computed DFT solvation energies for this specific set of solvents in the "Verified datasets" block. We simulate the *process* of obtaining these values.

### Dataset Fit Check
*   **Required Variables**: $\tau$ (lifetime), $\epsilon$ (dielectric), $\Delta G_{solv}$, Temperature, Humidity.
*   **Availability**: All variables are present in the synthetic/computed datasets.
*   **Mismatch**: None. The synthetic generator is configured to include all required fields.

## Statistical Methodology

### 1. Global Kinetic Analysis (FR-004)
*   **Method**: Multi-exponential fitting ($A(t) = \sum A_i e^{-t/\tau_i} + C$) using `scipy.optimize.curve_fit`.
*   **Constraint**: CPU-tractable. `scipy` is fully supported on GitHub Actions free-tier.
*   **Calibration**: Fitted $\tau$ values are adjusted by a calibration factor derived from a reference standard (simulated in `data/raw/calibration.csv`).

### 2. Correlation & Significance Testing (FR-006, SC-001, SC-003)
*   **Primary Test**: Linear regression ($\tau = \beta_0 + \beta_1 \cdot \Delta G_{solv} + \epsilon$) and ($\tau = \beta_0 + \beta_1 \cdot \epsilon + \epsilon$).
*   **Methodology Revision**: Due to the small sample size (N=5-10 solvents), standard p-value significance testing is unreliable. The plan now prioritizes **effect size estimation** with **bootstrapped 95% confidence intervals**.
*   **Multiple Comparison Correction**: Since we test two alternative models (Lifetime vs. Solvation, Lifetime vs. Dielectric), we apply the **Bonferroni** correction to the set of models if both are reported. However, given the structural collinearity, we primarily report the effect size and CI for the primary descriptor (Solvation Energy) and note the collinearity.
*   **Power Analysis**: Sample size $n=3$ per solvent is low. Power is acknowledged as limited. Effect sizes will be reported with confidence intervals (95% CI) rather than just p-values. A formal power analysis is documented in `docs/power_analysis.md`.

### 3. Collinearity Diagnostics (SC-009)
*   **Method**: Variance Inflation Factor (VIF) analysis.
*   **Rationale**: Dielectric constant ($\epsilon$) and solvation energy ($\Delta G_{solv}$) are often highly correlated (structurally collinear in SMD/PCM models). VIF > 5 indicates severe collinearity. The plan acknowledges that they are not independent predictors and will not be used in a multiple regression simultaneously. Instead, they are analyzed as separate univariate models.

## Computational Feasibility

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
*   **Workload**:
    *   Kinetic fitting: < 1 second per trace. Total < 1 minute.
    *   DFT simulation: Simulated (no actual DFT calculation performed in CI to save time). Real DFT would be too heavy for CI; the plan is to *process* DFT results, not *run* DFT.
    *   Statistics: Instant.
*   **Conclusion**: The pipeline is fully CPU-tractable and will complete well within the designated time limit.

## Reviewer Feedback Integration

*   **rosalind-franklin-simulated**: Highlighted the need for strict humidity/temperature control.
    *   *Action*: The `data-model.md` includes `temperature` and `humidity` as mandatory fields in `SolventCondition`. The `kinetic_fit.py` script will flag any run where `abs(temp - 25) > 0.5` or `abs(humidity - target) > 2`.
*   **marie-curie-simulated**: Demanded instrument calibration details.
    *   *Action*: `CalibrationRecord` entity added to data model. `kinetic_fit.py` applies calibration factors before reporting $\tau$.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Data for Kinetics** | No verified public dataset exists for this specific reaction kinetics in the provided list. Synthetic data allows pipeline validation without violating "No Fabricated URLs" rule. |
| **Null Hypothesis Generation** | Synthetic data is generated with no inherent correlation between solvent properties and lifetime to avoid circular validation. |
| **Associational Framing** | The design is observational (solvents are not randomly assigned to "treatment" groups in a way that isolates causality). Claims are limited to correlation. |
| **Bootstrapped CIs** | Preferred over p-values for small N to provide robust effect size estimates. |
| **VIF Analysis** | Required by SC-009 to address the inherent correlation between $\epsilon$ and $\Delta G_{solv}$. |
| **Separate Univariate Models** | Due to structural collinearity, $\epsilon$ and $\Delta G_{solv}$ are analyzed as alternative descriptors, not independent variables in a multiple regression. |