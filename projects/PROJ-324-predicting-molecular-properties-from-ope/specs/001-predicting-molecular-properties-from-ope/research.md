# Research Context: Molecular Property Prediction

## Background
Molecular properties like logP (partition coefficient), aqueous solubility, and boiling point are critical in drug discovery. Traditional methods rely on additive fragment models (e.g., Crippen's), which assume properties are the sum of atomic contributions. However, non-linear interactions and steric effects often cause deviations.

## Research Question
Which structural substructures, as captured by Open Babel fingerprints, are most predictive of deviations from the additive baseline for logP, solubility, and boiling point?

## Hypothesis
Random Forest models trained on topological fingerprints will capture non-linear interactions missed by additive models, particularly for molecules with complex steric environments. SHAP analysis will identify specific fingerprint bits (substructures) responsible for these improvements.

## Methodology
1. **Data Collection**: Acquire diverse dataset of molecules with experimental properties.
2. **Baseline**: Calculate Crippen's predictions.
3. **Modeling**: Train RF models on Open Babel fingerprints.
4. **Analysis**: Compare errors and use SHAP to interpret feature importance and interactions.

## Limitations
- Fingerprints are 2D topological representations and may not capture 3D conformational effects.
- Experimental data may have varying measurement conditions (temperature, pH).
