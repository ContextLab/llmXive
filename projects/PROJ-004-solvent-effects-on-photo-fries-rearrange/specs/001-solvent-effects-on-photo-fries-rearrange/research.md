# Research: Solvent Effects on Photo-Fries Rearrangement Kinetics

## Problem Statement & Hypothesis

**Hypothesis**: There is an **associational relationship** between solvent polarity and the lifetime of the singlet-radical-pair intermediate in the Photo-Fries rearrangement of phenyl benzoate. Higher solvent polarity is *associated* with changes in the intermediate lifetime.

**Research Question**: How do solvent properties (dielectric constant, solvation free energy) quantitatively correlate with the experimentally derived lifetime of the radical-pair intermediate?

**Note on Causality**: This study design is observational (solvent choice is not randomized in the chemical sense). Therefore, **no causal claims** (e.g., "solvents stabilize radicals") are made. The analysis cannot distinguish direct solvent effects from confounding variables (e.g., viscosity, specific solute-solvent interactions). All findings are framed strictly as *associational*.

**Exploratory Nature**: Due to the low sample size (n=3 replicates per solvent), this study is explicitly framed as **exploratory** and **hypothesis-generating**. The statistical tests are not intended to provide definitive proof but to estimate effect sizes and generate hypotheses for future validation with larger sample sizes.

## Verified Datasets

The project utilizes **simulated** data for CI reproducibility, modeled after real transient-absorption spectroscopy protocols. No external real-world dataset URL is used for the primary execution, as real instrument data requires physical access. However, the simulation parameters are derived from established literature on Photo-Fries kinetics.

**Simulated Data Source**:
-   **Generator**: `code/simulate_data.py`
-   **Basis**: Kinetic parameters derived from general photochemistry principles and specific literature on aryl ester rearrangements.
-   **Reference**: [Learning Continuous Solvent Effects from Transient Flow Data: A Graph Neural Network Benchmark on Catechol Rearrangement (2025)](http://arxiv.org/abs/2512.19530v1) (Used for conceptual modeling of solvent-dependent kinetics).
-   **Independence Check**: The simulation generator uses an **empirical kinetic model based on the Arrhenius equation with randomized activation energy**. This is mathematically independent of the DFT solvation energy calculation (which uses the Born equation). The correlation test is **not circular** because the two models use distinct physical parameters and functional forms.

**Real Data Ingestion**:
-   The system supports ingesting real transient-absorption data by placing CSV files in `data/raw/` with the naming convention `trace_<solvent>_<replicate>.csv`.
-   The system validates these files against the `dataset.schema.yaml` before processing.
-   This mechanism allows the pipeline to be used with real instrument data if available, while defaulting to simulation for CI.

## Dataset Strategy

| Data Type | Source/Method | Variables Included | Usage |
| :--- | :--- | :--- | :--- |
| **Transient Absorption Traces** | Simulated (`simulate_data.py`) or Uploaded Real Data | `time` (ns), `absorbance` (mOD), `solvent_id`, `replicate_id` | Kinetic fitting to extract lifetime (US-2). |
| **Solvent Properties** | Versioned Lookup (`data/chemicals/solvents.csv`) | `solvent_name`, `dielectric_constant`, `viscosity` | Environmental logging (US-1), Predictor variable. |
| **Solvation Free Energy** | DFT Computation (`compute_solvation.py` or pre-computed) | `solvation_energy` (kcal/mol), `method` (SMD/PCM) | Predictor variable for correlation (US-3). |
| **Product Distribution** | Simulated Proxy (Derived) | `ortho_ratio`, `para_ratio` | Secondary consistency check only (not independent validation). |

**Data Integrity**: All generated data is checksummed. The lookup table for solvents is version-controlled to ensure dielectric constants match the reference (SC-010).

## Statistical Methodology

### 1. Kinetic Analysis (US-2) - Joint Modeling
-   **Method**: **Joint Non-Linear Mixed-Effects (NLME) Modeling** using `pymc` (CPU-tractable).
-   **Model**: $A(t) = A_0 \exp(-t/\tau) + C$, where $\tau$ is modeled as a function of solvent properties.
-   **Output**: Lifetime $\tau$ (ns) with 95% credible intervals, *simultaneously* fitted with the regression model.
-   **Advantage**: Avoids the bias of treating point estimates as fixed inputs (two-stage flaw). Propagates uncertainty from kinetic fitting directly into the regression.
-   **Validation**: Residual analysis to ensure goodness-of-fit (R² > 0.95).

### 2. Correlation & Regression (US-3) - Bayesian Hierarchical Model
-   **Primary Model**: **Bayesian Hierarchical Model** of $\tau$ vs. **Solvent Polarity Index** (derived via PCA from dielectric constant and solvation energy).
-   **Associational Framing**: All claims explicitly state "association" not "causation" (SC-006).
-   **Collinearity**: **PCA** is used to derive a single "Solvent Polarity Index" to avoid tautology between dielectric constant and solvation energy. Separate univariate models for these variables are **forbidden** for hypothesis testing.
-   **Multiple Comparisons**: If comparing multiple solvent groups, ANOVA with Bonferroni correction is applied (SC-003).
-   **P-Values**: Exact p-values (or Bayesian posterior probabilities) are calculated and reported with multiple-comparison correction. The study acknowledges low power but reports these values as part of the exploratory analysis.

### 3. Power & Sensitivity (SC-007, SC-008)
-   **Power Analysis**: Documented for $n=3$ replicates. Effect size estimation deferred to implementation; low power acknowledged as a limitation. The study is explicitly framed as **exploratory** and **hypothesis-generating**.
-   **Sensitivity Analysis**: Thresholds for lifetime discrepancy (e.g., 0.05 ns) are varied to assess false-positive rates.

### 4. Confounding Variables
-   **Acknowledgement**: The study design cannot control for confounders such as viscosity or specific solute-solvent interactions.
-   **Framing**: All results are interpreted as *associational* only. No causal mechanisms are inferred.

## Computational Feasibility

-   **Hardware**: CPU-only (2 cores, 7 GB RAM).
-   **Libraries**: `pymc`, `scipy`, `statsmodels`, `numpy`. No GPU dependencies.
-   **Runtime**: Estimated < 30 minutes for full pipeline on CI.
-   **Data Size**: < 10 MB total.

## Limitations & Assumptions

-   **Simulation Fidelity**: Simulated data assumes ideal instrument behavior; real data may have higher noise.
-   **Sample Size**: $n=3$ is low for robust statistical inference; results are preliminary and exploratory. The study is not powered to detect small effect sizes with high confidence.
-   **DFT Accuracy**: Solvation energies are approximated; explicit solvent models are not fully simulated due to compute constraints.
-   **Instrument Calibration**: Simulated calibration metadata is assumed perfect; real experiments require rigorous calibration.
-   **Product Distribution**: Product distribution is a **derived artifact** of the lifetime model (via cage effect) and **cannot serve as an independent validation target** for the lifetime hypothesis. It is retained only as a secondary consistency check. **No NMR analysis is performed; HPLC-UV is the sole method for product distribution.**

## References

1.  [Learning Continuous Solvent Effects from Transient Flow Data: A Graph Neural Network Benchmark on Catechol Rearrangement (2025)](http://arxiv.org/abs/2512.19530v1)
2.  [Fluctuations and correlations in chemical reaction kinetics and population dynamics (2018)](http://arxiv.org/abs/1807.01248v1)
3.  [Erratum to the article: Charge transfer to solvent identified using dark channel fluorescence-yield L-edge spectroscopy, NATURE CHEMISTRY 2 (2010) 853 (2017)](http://arxiv.org/abs/1705.03941v2)
