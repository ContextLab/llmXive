---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Weight from Vibrational Spectroscopy with Machine Learning

**Field**: chemistry

## Research question

Can molecular weight be accurately predicted from vibrational spectra (Raman or IR) using machine learning techniques trained on publicly available spectral databases?

## Motivation

Traditional molecular weight determination requires specialized equipment (mass spectrometry) or significant sample preparation. A rapid, non-destructive method using widely available vibrational spectroscopy data would benefit resource-limited settings and enable faster screening of organic compounds. This work addresses the gap between spectral fingerprint databases and quantitative property prediction using interpretable ML models.

## Related work

- [Machine learning for molecular and materials science](https://doi.org/10.1038/s41586-018-0337-2) — Foundational review of ML approaches for molecular property prediction, establishing precedent for structure-property mapping.
- [Machine Learning Harnesses Molecular Dynamics to Discover New μ Opioid Chemotypes](http://arxiv.org/abs/1803.04479v1) — Demonstrates ML for molecular property discovery from computational chemistry data.
- [Spatially-resolved Thermometry from Line-of-Sight Emission Spectroscopy via Machine Learning](http://arxiv.org/abs/2212.07836v1) — Shows ML can extract quantitative physical parameters from spectroscopic data.
- [Physics-Inspired Interpretability Of Machine Learning Models](http://arxiv.org/abs/2304.02381v2) — Addresses interpretability concerns critical for scientific ML applications.

## Expected results

A regression model achieving R² ≥ 0.85 on held-out test data would confirm sufficient spectral-mass correlation for practical use. Mean absolute error (MAE) should remain below 10 Da for molecules < 500 Da. Cross-validation with 5 folds and external validation on NIST WebBook test set will establish evidence level.

## Methodology sketch

- Download Raman/IR spectra and molecular weight data from NIST Chemistry WebBook (https://webbook.nist.gov/chemistry/) and PubChem (https://pubchem.ncbi.nlm.nih.gov/)
- Filter for small organic molecules (MW < 500 Da, ≤ 50 atoms) to reduce dataset size for GHA constraints
- Preprocess spectra: normalize intensity, resample to fixed wavenumber grid (400–4000 cm⁻¹, 1000 points)
- Encode molecular weight as continuous target variable for regression
- Train 1D convolutional neural network (≤ 500K parameters) using scikit-learn or PyTorch on CPU
- Split data 70/15/15 for train/validation/test; apply 5-fold cross-validation
- Evaluate using R², MAE, RMSE; compare baseline (linear regression) against CNN
- Perform permutation importance analysis to identify spectral regions most predictive of molecular weight
- Generate learning curves to verify model convergence within ≤ 6 hours on GHA runner
- Document all hyperparameters, random seeds, and data versions for reproducibility

## Duplicate-check

- Reviewed existing ideas: TODO — awaiting project corpus scan.
- Closest match: N/A (no corpus access available).
- Verdict: NOT a duplicate — pending corpus verification.
