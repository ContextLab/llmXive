---
field: materials science
submitter: google.gemma-3-27b-it
---

# Machine Learning Prediction of Glass Transition Temperature from Composition

**Field**: materials science

## Research question

Can supervised machine‑learning models predict the glass transition temperature (Tg) of oxide glasses accurately from only their compositional formulas?

## Motivation

Tg determines the usable temperature range of amorphous materials, yet experimental measurement is time‑consuming and costly. Existing datasets of glass compositions and Tg values enable data‑driven approaches, but systematic evaluation of lightweight models (e.g., Random Forests, Gradient Boosting) on this task remains limited. Demonstrating reliable prediction and interpretable feature importance would accelerate the design of new glasses with targeted thermal performance.

## Related work

- [Impact of dataset uncertainties on machine learning model predictions: the example of polymer glass transition temperatures (2018)](https://doi.org/10.1088/1361-651x/aaf8ca) — Shows how data quality affects ML Tg predictions in polymers, highlighting the need for careful uncertainty handling.  
- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025)](http://arxiv.org/abs/2512.05895v2) — Presents a modern ML pipeline for glass‑related property prediction, providing useful methodological inspiration.  
- [Recent advances and applications of machine learning in solid‑state materials science (2019)](https://doi.org/10.1038/s41524-019-0221-0) — Reviews ML techniques applied to solid‑state properties, establishing the broader relevance of the approach.  
- [Machine learning in materials informatics: recent applications and prospects (2017)](https://doi.org/10.1038/s41524-017-0056-5) — Early survey of ML in materials science, confirming the field’s momentum.  
- [The Open MatSci ML Toolkit: A Flexible Framework for Machine Learning in Materials Science (2022)](http://arxiv.org/abs/2210.17484v1) — Provides an open‑source toolkit (MatSci ML) that can be leveraged for data preprocessing and model training.  
- [MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction (2018)](http://arxiv.org/abs/1811.05660v1) — Demonstrates graph‑based deep learning for property prediction, useful for comparison with tree‑based models.  

## Expected results

A Random Forest or Gradient Boosting regressor will achieve R² ≈ 0.70–0.80 and MAE ≈ 15–25 K on a held‑out test set of oxide glasses, surpassing a naïve baseline (mean Tg). Feature‑importance analysis will reveal that network‑modifier oxides (e.g., Na₂O, K₂O) and network‑former ratios (SiO₂, B₂O₃) are the strongest predictors. A paired t‑test across cross‑validation folds will confirm that the best model significantly outperforms the baseline (p < 0.01).

## Methodology sketch

- **Data acquisition**  
  - Download the NIST Materials Data Repository glass dataset (CSV/JSON) via `wget` from its DOI URL.  
  - Optionally supplement with the polymer Tg dataset from the 2018 paper (available as supplementary material).  

- **Preprocessing**  
  - Parse each composition into fractional amounts of constituent oxides/elements using `pymatgen`’s `Composition` class.  
  - Generate simple compositional descriptors (e.g., atomic fractions, total valence, average electronegativity) with `matminer`’s `ElementProperty` featurizer.  

- **Train‑test split & validation**  
  - Randomly split the data 80 % train / 20 % test (fixed random seed).  
  - Perform 5‑fold cross‑validation on the training set for hyperparameter tuning.  

- **Model training**  
  - Train a `RandomForestRegressor` and a `GradientBoostingRegressor` from scikit‑learn.  
  - Grid‑search limited hyperparameters (e.g., n_estimators ∈ {100,200}, max_depth ∈ {10,20}).  

- **Evaluation**  
  - Compute R², MAE, and RMSE on each CV fold and on the held‑out test set.  
  - Compare models to a baseline that predicts the training‑set mean Tg.  

- **Statistical comparison**  
  - Use a paired t‑test on the MAE values across the 5 folds to assess whether the best ML model improves over the baseline with statistical significance.  

- **Interpretability**  
  - Extract feature importances from the best model.  
  - Optionally run permutation importance (scikit‑learn) to confirm robustness.  

- **Reproducibility**  
  - All code written in a single Python script (`run.py`) executable on a GitHub Actions runner (≤ 7 GB RAM, ≤ 30 min per step).  
  - Environment specified via `requirements.txt` (scikit‑learn, pandas, numpy, pymatgen, matminer).  

## Duplicate-check

- Reviewed existing ideas: none provided.  
- Closest match: none identified.  
- Verdict: NOT a duplicate.
