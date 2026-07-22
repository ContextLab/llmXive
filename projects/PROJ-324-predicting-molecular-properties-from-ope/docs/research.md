# Research Documentation

## Objective

Predict molecular properties (logP, solubility, boiling point) using Open Babel fingerprints and Random Forest models.

## Methodology

1. **Data Collection**: Fetch data from PubChem.
2. **Preprocessing**: Filter high-confidence measurements and apply MaxMin sampling.
3. **Baseline**: Compute Crippen's additive fragment model predictions.
4. **Model Training**: Train Random Forests with nested cross-validation.
5. **Explainability**: Use SHAP to identify contributing substructures.

## Limitations

- Fingerprints are topological abstractions.
- 2D fingerprints cannot capture 3D conformational ensembles.
- Measurement uncertainty data may be absent from sources.

## Validation

- Paired Wilcoxon signed-rank test for model comparison.
- Explicit reporting of data provenance and uncertainty status.