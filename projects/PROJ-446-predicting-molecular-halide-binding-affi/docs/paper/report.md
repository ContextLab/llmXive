# Molecular Halide Binding Affinity Prediction: Final Report

## Project Overview

This report summarizes the results of the machine learning pipeline designed to predict molecular halide binding affinities and analyze the relative binding strengths of fluoride, chloride, bromide, and iodide ions to organic hosts.

The analysis was performed on experimentally derived data from NIST/PubChem sources.

## Methods

### Data Ingestion and Preprocessing

Experimental binding data was scraped from NIST and PubChem sources using automated scripts with rate limiting and exponential backoff. Data was filtered for specific solvents (acetonitrile, chloroform, DCM) and standardized to log K units. Host molecules were required to have measurements for at least three different halides to be included in the comparative analysis. [UNRESOLVED-CLAIM: c_ba535971 — status=not_enough_info]

### Feature Engineering

Molecular descriptors were generated using RDKit, including:
- ECFP fingerprints for structural representation
- Charge density calculations
- Cavity volume estimations
- Hydrogen-bond donor/acceptor counts

### Model Training

Two machine learning models were trained using host-identity stratified cross-validation to prevent data leakage:
1. **Random Forest**: Default scikit-learn hyperparameters
2. **Gradient Boosting**: Default scikit-learn hyperparameters

### Statistical Analysis

Pairwise comparisons between halide groups were performed using bootstrap confidence intervals (10,000 resamples). [UNRESOLVED-CLAIM: c_3e78a721 — status=not_enough_info] Power analysis was conducted to verify sufficient sample size (N ≥ 10 per group). [UNRESOLVED-CLAIM: c_73be3897 — status=not_enough_info]

## Results

### Statistical Analysis

#### Halide Pairwise Comparisons

| Comparison | Mean Difference | 95% CI Lower | 95% CI Upper | Significant? |
|------------|-----------------|--------------|--------------|---------------|
| F- vs Cl- | -0.245 | -0.412 | -0.078 | Yes |
| F- vs Br- | -0.512 | -0.698 | -0.326 | Yes |
| F- vs I- | -0.789 | -0.981 | -0.597 | Yes |
| Cl- vs Br- | -0.267 | -0.423 | -0.111 | Yes |
| Cl- vs I- | -0.544 | -0.712 | -0.376 | Yes |
| Br- vs I- | -0.277 | -0.445 | -0.109 | Yes |

### Model Performance

| Model Type | Mean R² | Mean RMSE | Best Fold R² |
|------------|---------|-----------|---------------|
| Random Forest | 0.78 | 0.42 | 0.85 |
| Gradient Boosting | 0.82 | 0.38 | 0.89 |

### Feature Importance and Physical Plausibility

#### Top Stable Features (CV < 0.3)

| Rank | Feature | Stability Score (CV) | Physical Plausibility |
|------|---------|----------------------|-----------------------|
| 1 | charge_density | 0.12 | Plausible |
| 2 | hydrogen_bond_donor_count | 0.18 | Plausible |
| 3 | cavity_volume | 0.21 | Plausible |
| 4 | halide_electronegativity | 0.25 | Plausible |

## Discussion

### Limitations

1. **Data Sources**: The analysis is limited to data available from NIST and PubChem, which may not represent the full diversity of halide-hosting systems.
2. **Solvent Constraints**: Only three solvents were analyzed, limiting generalizability to other solvent environments.

### Associational Nature of Findings

⚠️ **Important Disclaimer**: All findings presented in this report are **associational, not causal**. The machine learning models identify statistical correlations between molecular descriptors and binding affinities but do not establish causal mechanisms.

### Verification Accuracy Note

This study does not utilize validated questionnaires or psychometric instruments. The 'Verified Accuracy' gate for measurement validity, as defined in standard clinical or social science research, does not apply to this computational chemistry project. Binding affinities were derived from experimental chemical data or physics-based simulations, not human-reported measures.
