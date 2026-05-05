---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

**Field**: chemistry

## Research question

Can Random Forest models trained on Open Babel fingerprints accurately predict a range of molecular properties (e.g., logP, solubility, boiling point) available in public databases like PubChem, and how does their performance compare to established quantitative structure-property relationship (QSPR) methods?

## Motivation

This project addresses the need for computationally efficient molecular property prediction methods that can be run on standard hardware without specialized infrastructure. While deep learning approaches dominate the field, Random Forests offer interpretability and lower computational overhead, making them suitable for resource-constrained environments. Understanding the baseline performance of fingerprint-based Random Forest models provides a reference point for more complex methods.

## Related work

- [ADMET property prediction through combinations of molecular fingerprints (2023)](http://arxiv.org/abs/2310.00174v1) — Demonstrates that random forests paired with extended-connectivity fingerprints outperform other methods for small molecule potency prediction.
- [QUBO-inspired Molecular Fingerprint for Chemical Property Prediction (2023)](http://arxiv.org/abs/2303.10179v1) — Investigates molecular fingerprint selection and generation for chemical property prediction tasks.
- [Asymptotic Theory for Random Forests (2014)](http://arxiv.org/abs/1405.0352v2) — Provides statistical foundation for random forests as reliable predictive algorithms, supporting their use in QSPR applications.

## Expected results

Random Forest models using Open Babel fingerprints should achieve competitive prediction accuracy (R² ≥ 0.7) for physicochemical properties like logP and solubility, comparable to or exceeding traditional QSPR baselines. Feature importance analysis will reveal which structural substructures most strongly influence each property, providing interpretable insights into molecular behavior.

## Methodology sketch

- Download molecular data from PubChem BioAssay and ChEMBL (https://pubchem.ncbi.nlm.nih.gov/; https://www.ebi.ac.uk/chembl/) containing SMILES strings and measured properties.
- Filter dataset to 5,000–10,000 molecules with complete property labels (logP, water solubility, boiling point).
- Generate Open Babel fingerprints (MACCS, ECFP4, FP2) using `obabel` command-line tool for each SMILES.
- Split data into 80/10/10 train/validation/test stratified by property value distribution.
- Train Random Forest regressors (scikit-learn) with 100–500 trees, max depth 20, on each fingerprint type.
- Tune hyperparameters via 5-fold cross-validation on training set (grid search: n_estimators, max_depth, min_samples_split).
- Evaluate performance using R², MAE, and RMSE on held-out test set.
- Compare results against baseline linear regression and published QSPR benchmarks from related work.
- Extract and visualize feature importance scores to identify key fingerprint bits.
- Generate summary figures (scatter plots, feature importance bar charts) using matplotlib.

## Duplicate-check

- Reviewed existing ideas: [none provided in context].
- Closest match: [N/A — no existing ideas to compare].
- Verdict: NOT a duplicate
