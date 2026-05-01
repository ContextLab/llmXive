---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

**Field**: chemistry

## Research question

Can classical machine learning models (e.g., Random Forests, SVMs) trained on molecular fingerprints accurately predict organic reaction yields and selectivity without requiring deep learning infrastructure?

## Motivation

Experimental screening of reaction conditions is resource-intensive and slow. Establishing a robust baseline using low-resource classical ML models can provide a computationally efficient screening tool for chemists, particularly in environments lacking GPU access or large-scale compute clusters.

## Related work

- [Universal Chemical Synthesis and Discovery with 'The Chemputer' (2019)](https://doi.org/10.1016/j.trechm.2019.07.004) — Discusses the integration of AI with automated chemical synthesis, highlighting the need for predictive models to guide robotic experimentation.
- [QSAR without borders (2020)](https://doi.org/10.1039/d0cs00098a) — Reviews the application of machine learning and AI methods for predicting chemical properties and bioactivity, establishing context for yield prediction tasks.
- [Linking the Neural Machine Translation and the Prediction of Organic Chemistry Reactions (2016)](http://arxiv.org/abs/1612.09529v1) — Demonstrates early success in applying sequence-to-sequence models to reaction prediction, providing a benchmark for comparing classical ML approaches.

## Expected results

We expect Random Forest models to achieve moderate predictive accuracy (R² > 0.6) on yield prediction tasks, confirming that simple fingerprint-based features capture significant variance. The results will identify specific reaction conditions and structural motifs that most strongly correlate with high yields, validated via cross-validation on a held-out test set.

## Methodology sketch

- Download the USPTO reaction yield dataset from the Scientific Data repository (`https://doi.org/10.1038/s41597-020-00636-9`) using `wget`.
- Preprocess SMILES strings using RDKit to sanitize molecules and remove salts/inorganic byproducts.
- Generate ECFP4 (Extended Connectivity Fingerprints) for all reactants and reaction conditions using `rdkit.Chem.AllChem`.
- Split the dataset into training (80%), validation (10%), and test (10%) sets using stratified sampling on yield bins.
- Train Random Forest and Support Vector Machine regressors using `scikit-learn` on the fingerprint vectors.
- Tune hyperparameters (e.g., number of trees, C parameter) using grid search on the validation set.
- Evaluate model performance on the test set using Root Mean Squared Error (RMSE) and R-squared metrics.
- Extract feature importance scores to determine which molecular substructures or conditions drive yield predictions.
- Visualize prediction errors and feature importance using `matplotlib` to generate publication-ready figures.
- Ensure all steps run within 7GB RAM by limiting dataset size to 10,000 reactions if necessary.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: None.
- Verdict: NOT a duplicate
