# Research: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Problem Statement
Diffusion in metals is a critical process in materials science, governing phenomena like creep, sintering, and phase transformations. In FCC alloys, the presence of solute atoms alters the activation energy ($E_a$) required for diffusion. This project investigates whether atomic size mismatch (a geometric descriptor) is a statistically significant predictor of this shift, using **observational data from verified public repositories**.

## Dataset Strategy

### Verified Data Sources
The project relies on **verified** public repositories for diffusion data. Synthetic or mock data is **NOT** used for hypothesis validation.
1.  **NIST Standard Reference Database 168 (Diffusion in Metals)**: Contains experimental diffusion coefficients and activation energies for various alloys.
    *   *Access Strategy*: The pipeline will attempt to fetch data via the `diffusion` Python package (if available) or scrape the verified CSV mirror provided in the project's `data/raw/` directory (checksummed).
    *   *Verification*: The dataset is verified to contain `crystal_structure`, `diffusion_mode`, `activation_energy`, and elemental identifiers.
2.  **Materials Project (API)**: Provides calculated and experimental diffusion barriers.
    *   *Access Strategy*: Use the `pymatgen` library to query for FCC self-diffusion events.
    *   *Verification*: Confirmed to contain `solute_radius` and `host_radius` via periodic table integration in `pymatgen`.
3.  **Literature Compilations**: If NIST/Materials Project data is insufficient, the pipeline will attempt to ingest specific, verified datasets from literature (e.g., "Diffusion in FCC Alloys" compilations from *Acta Materialia* or *Journal of Alloys and Compounds*).

**Critical Decision**: The plan **NO LONGER** relies on synthetic or mock data. If the verified NIST/Materials Project data cannot be fetched or lacks sufficient rows (N < 50), the pipeline will halt and flag a "Data Insufficiency" error, rather than proceeding with invalid synthetic data. This ensures the hypothesis is tested against real physical observations.

### Data Schema Requirements
To satisfy **FR-001** and **FR-002**, the input data must contain:
- `crystal_structure`: String (must include "FCC")
- `diffusion_mode`: String (must include "self")
- `activation_energy_eV`: Float (Target variable)
- `solute_element`: String
- `host_element`: String
- `solute_concentration`: Float (at.%)
- `solute_radius_pm`: Float (Metallic radius)
- `host_radius_pm`: Float (Metallic radius)

### Data Handling Strategy
1.  **Ingestion**: Load CSV/JSONL from verified sources. Filter rows where `crystal_structure == "FCC"` and `diffusion_mode == "self"`.
2.  **Cleaning**: Exclude rows with missing `solute_concentration` (log as `MISSING_CONCENTRATION`).
3.  **Descriptor Lookup**: If atomic radii are missing, merge with the `utils/constants.py` file which contains **Metallic Radii (Pauling/Wiberg)** specifically for FCC coordination. If still missing, exclude and log to `errors/missing_atomic_data.csv`.

## Feature Engineering & Model Selection

### Features
- **Primary Feature**: `size_mismatch` = $(r_{solute} - r_{host}) / r_{host}$, using **Metallic Radii**.
  *   *Descriptor Consistency*: Atomic radii vary with coordination. We explicitly use **Metallic Radii** for FCC metals. A sensitivity check will be performed: if the model performance varies significantly when using Covalent Radii, the "size_mismatch" hypothesis is flagged as sensitive to descriptor choice.
- **Secondary Features** (if data permits): Electronegativity difference (Pauling scale), valence electron count.
- **Target**: $\Delta E_a = E_{alloy\_measured} - E_{pure\_host\_measured}$.
  *   *Ground Truth Definition*: Both $E_{alloy}$ and $E_{pure\_host}$ are **experimentally measured** values from the dataset. This ensures the target is an independent ground truth, avoiding circular validation.

### Model Justification
1.  **Random Forest (RF)**: Selected for robustness to non-linearities and outliers. It handles the small dataset size well and provides feature importance.
2.  **Gradient Boosting (GB)**: Selected for potential higher accuracy on structured tabular data.
3.  **Linear Regression**: Selected **solely for statistical inference** (FR-005).
    *   *Confounding Control*: To address the observational nature of the data, the Linear Regression model will include **Host Metal** as a categorical fixed effect (One-Hot Encoding). This controls for the intrinsic properties of the host metal, isolating the effect of `size_mismatch`. The p-value will reflect the significance of size mismatch *conditional* on the host metal.

### Hyperparameter Tuning
- **Method**: Grid Search with 5-fold Cross-Validation.
- **Ranges**: `max_depth` [3, 10], `n_estimators` [50, 200].
- **Metric**: R² (maximized).
- **Constraint**: Must run on CPU within 15 minutes (US-2).

## Statistical Validation Strategy

### Statistical Power & Sample Size
- **Power Analysis**: With an estimated sample size of N=50-200, the study is likely underpowered to detect small effect sizes (e.g., $R^2 < 0.1$).
- **Mitigation**: The pipeline will calculate the **Minimum Detectable Effect (MDE)** for the `size_mismatch` coefficient given the sample size and variance.
- **Reporting**: The final report will explicitly state the achieved power and MDE. If power < 0.8, results will be framed as "exploratory" and "inconclusive" rather than definitive, preventing Type II error misinterpretation.

### Significance Testing (FR-005, SC-002)
- **Hypothesis**: The `size_mismatch` coefficient in the Linear Regression model (with Host Metal fixed effects) is non-zero.
- **Method**: Standard OLS t-test for p-value.
- **Robustness**: 95% Confidence Interval calculated via **Bootstrap Resampling** (1000 iterations) to account for small sample size and non-normality of residuals.
- **Correction**: If multiple predictors were tested, Bonferroni correction would be applied. Here, we focus on the primary hypothesis of size mismatch.

### Sensitivity Analysis (FR-005, SC-003)
- **Threshold Sweep**: Evaluate classification of "significant shift" ($\Delta E_a > T$) for $T \in \{0.45, 0.46, \dots, 0.55\}$.
- **Metric**: **Standard Deviation of the Classification Rate** across the threshold sweep.
  *   *Correction*: The previous definition involving "relative to RMSE" was dimensionally inconsistent. The new metric measures the absolute variation in classification stability (probability) across the sweep, independent of the RMSE.
- **Goal**: Confirm that the conclusion (e.g., "alloying slows diffusion") does not flip arbitrarily with small threshold changes.

## Computational Feasibility
- **Hardware**: GitHub Actions Free Tier (limited CPU, 7 GB RAM).
- **Dataset Size**: Verified datasets (NIST/Materials Project) are typically < 10 MB for this scope.
- **Model Complexity**: RF/GB with `n_estimators=200` on < 200 rows is trivial for CPU. No GPU required.
- **Runtime**: Estimated < 30 minutes for full pipeline (ingestion, tuning, training, validation).

## Limitations & Assumptions
- **Data Availability**: The plan assumes the verified NIST/Materials Project data is accessible. If not, the pipeline halts.
- **Causality**: Data is observational. Results will be framed as **associational**, not causal. The inclusion of Host Metal fixed effects mitigates confounding but does not eliminate it.
- **Linearity**: The Linear model is a proxy; the true physics may be non-linear, but RF/GB will capture that.
- **Descriptor Choice**: The use of a single "Metallic Radius" is a simplification. The sensitivity check for descriptor choice addresses this limitation.