---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Field**: chemistry

## Research question

Can supervised machine learning models trained on DFT‑derived electronic‑structure descriptors and computed reaction‑path features reliably predict experimental turnover frequencies of heterogeneous metal catalysts?

## Motivation

High‑throughput screening of catalyst candidates is limited by the computational expense of full reaction‑path calculations and by the scarcity of experimentally measured activity data. Demonstrating that a compact set of quantum‑chemical descriptors can accurately predict catalytic performance would enable rapid, inexpensive virtual screening and focus experimental effort on the most promising materials.

## Related work

- [AARON: An Automated Reaction Optimizer for New Catalysts. (2018)](https://www.semanticscholar.org/paper/2a2b7ca70967ba94116f1397ed78ef710061c87c) — Presents an open‑source workflow that automates QM geometry optimizations and reaction‑coordinate characterizations, providing a practical source of standardized DFT data for model training.  
- [Catalytic Activity of an Ensemble of Sites for CO₂ Hydrogenation to Methanol on a ZrO₂‑on‑Cu Inverse Catalyst. (2025)](https://www.semanticscholar.org/paper/36ecbb2698fe2d12ae531a295c1cb615b7f942df) — Reports experimentally measured turnover frequencies together with site‑specific DFT energetics, offering a real‑world dataset linking reaction‑path energetics to activity.  
- [Assessing correlations of perovskite catalytic performance with electronic structure descriptors (2019)](http://arxiv.org/abs/1902.05867v1) — Shows how simple electronic‑structure descriptors (e.g., O p‑band center, d‑band center) correlate with oxygen‑evolution activity, establishing a precedent for descriptor‑based activity prediction.  
- [Exploring the Synergistic Ni‑Fe‑W Interplay in Double Perovskites to Understand the Operando Electronic Transformations Driving High Oxygen Evolution Reaction Activity and Stability (2024)](https://www.semanticscholar.org/paper/6e6b944ee7dbf0e18e0e4099eb32b55d309fa029) — Provides a dataset of experimentally measured OER activities together with DFT‑derived electronic descriptors for a family of perovskites, useful for benchmarking regression models.  

## Expected results

A regression model (e.g., Gradient Boosted Trees) trained on ≤30 DFT descriptors and ≤10 reaction‑path features will achieve a cross‑validated Pearson R ≥ 0.80 and mean absolute error ≤ 20 % of the experimental turnover frequency range. Performance will be statistically superior to a baseline linear‑descriptor model (paired t‑test, p < 0.01). The model will also identify the most informative descriptors via SHAP analysis.

## Methodology sketch

- **Data acquisition**  
  - Download publicly available catalyst datasets:  
    - Open Catalyst Project (OC20) reaction energetics (`wget https://dl.fbaipublicfiles.com/oc20/...`).  
    - Materials Project bulk electronic descriptors (`wget https://materialsproject.org/downloads/...`).  
    - Experimental turnover frequencies from the 2025 CO₂ hydrogenation study (supplementary CSV linked in the paper).  
- **Feature extraction**  
  - Compute d‑band center, p‑band center, frontier orbital energies, and Bader charges using pre‑computed density of states from Materials Project.  
  - Extract reaction‑path features: activation barrier, reaction energy, transition‑state geometry RMSD (provided in OC20).  
- **Data preprocessing**  
  - Align DFT descriptors with experimental entries via catalyst composition and surface facet identifiers.  
  - Impute missing values with k‑nearest‑neighbors (k=5).  
  - Standardize all numeric features (zero mean, unit variance).  
- **Model training & validation**  
  - Split data into 80 % training / 20 % hold‑out test (stratified by catalyst family).  
  - Train Gradient Boosted Regression Trees (XGBoost) with hyper‑parameter grid (max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, n_estimators ≤ 200).  
  - Perform 5‑fold cross‑validation on the training set; select hyper‑parameters by maximizing R².  
- **Baseline comparison**  
  - Fit a simple linear regression using only the d‑band center and activation barrier.  
  - Compare test‑set MAE and R² between the baseline and the tuned XGBoost model.  
- **Statistical assessment**  
  - Conduct a paired t‑test on the absolute errors of the two models across the test set to evaluate significance (α = 0.05).  
- **Interpretability**  
  - Compute SHAP values for the final model; rank descriptors by mean absolute SHAP impact.  
  - Visualize the top five features in a bar plot (Matplotlib).  
- **Reproducibility**  
  - All scripts will be written in Python 3.11, using `pandas`, `numpy`, `scikit‑learn`, `xgboost`, and `shap`.  
  - The entire pipeline (download → preprocess → train → evaluate) will be orchestrated by a single `make` target, runnable on a GitHub Actions runner within a 6‑hour wall‑clock limit.  

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A
- Verdict: **NOT a duplicate**
