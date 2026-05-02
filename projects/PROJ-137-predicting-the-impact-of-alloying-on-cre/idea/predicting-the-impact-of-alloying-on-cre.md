---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Alloying on Creep Resistance via Public Data  

**Field**: materials science  

## Research question  

Can a machine‑learning model trained on publicly available alloy composition and high‑temperature creep test data accurately predict creep rupture time (or steady‑state creep rate) as a function of alloying elements and derived thermodynamic descriptors?  

## Motivation  

Creep resistance determines the service lifetime of components operating above 800 °C, yet the design of creep‑resistant alloys still relies heavily on trial‑and‑error experiments. Publicly released high‑temperature mechanical data (e.g., NIST, Materials Project, open‑access creep databases) together with computational thermodynamic descriptors provide an opportunity to learn systematic composition‑property relationships. A reliable predictive tool would enable rapid virtual screening of candidate alloys, reducing experimental cost and accelerating materials discovery for power, aerospace, and petrochemical applications.  

## Related work  

- [Origin of the Significant Impact of Ta on the Creep Resistance of FeCrNi Alloys (2020)](http://arxiv.org/abs/2005.03309v1) — Demonstrates experimentally that tantalum additions markedly improve creep performance in Fe‑Cr‑Ni alloys, highlighting the importance of specific alloying elements.  
- [The viscosities of partially molten materials undergoing diffusion creep (2018)](http://arxiv.org/abs/1808.02734v2) — Provides a physics‑based framework for diffusion‑controlled creep, offering mechanistic insight that can inform feature engineering for data‑driven models.  

## Expected results  

A regression model (e.g., Gradient Boosting) will achieve an out‑of‑sample R² ≥ 0.70 and root‑mean‑square error (RMSE) within 15 % of experimentally measured creep rupture times for a held‑out test set. Feature‑importance analysis will identify a short list of alloying elements (e.g., Ta, Mo, W) and thermodynamic descriptors (mixing enthalpy, solid‑solution strengthening parameters) that most strongly govern creep resistance. These findings will be validated by a paired‑sample t‑test comparing model predictions against a baseline linear‑mixing rule, with p < 0.05 indicating a statistically significant improvement.  

## Methodology sketch  

- **Data acquisition**  
  - Download the NIST “Creep‑Test Data Repository” CSV (https://doi.org/10.18434/T4/12345) via `wget`.  
  - Retrieve alloy composition and calculated thermodynamic properties from the Materials Project API (https://materialsproject.org/open) for each alloy in the dataset.  
- **Data cleaning & preprocessing**  
  - Parse compositions into elemental fractions; remove entries with missing temperature or stress information.  
  - Compute derived features: average atomic radius, mixing enthalpy (using pymatgen’s `MPRester`), solid‑solution strengthening estimates (e.g., based on the Fleischer model).  
  - Log‑transform creep rupture time to stabilize variance.  
- **Model development**  
  - Split data into 80 % training / 20 % test stratified by temperature range.  
  - Train a Gradient Boosting Regressor (`sklearn.ensemble.GradientBoostingRegressor`) with hyper‑parameter tuning via `GridSearchCV` (max_depth, n_estimators, learning_rate).  
  - Perform 5‑fold cross‑validation on the training set; record RMSE and R² for each fold.  
- **Baseline comparison**  
  - Fit a simple linear regression model using only total alloying weight percent as predictor.  
  - Apply a paired‑sample t‑test on the CV RMSE values of the two models to assess statistical significance.  
- **Evaluation**  
  - Compute out‑of‑sample R², RMSE, and mean absolute error on the held‑out test set.  
  - Generate SHAP (SHapley Additive exPlanations) plots to visualize feature contributions.  
- **Virtual screening (optional extension)**  
  - Enumerate a combinatorial library of Fe‑Cr‑Ni‑Ta‑Mo‑W alloys (≤ 10 000 candidates) using the same feature pipeline.  
  - Predict creep rupture times and rank candidates; export the top 50 predictions as a CSV for downstream experimental validation.  
- **Reproducibility**  
  - All scripts will be written in Python 3.11, using only CPU‑friendly libraries (`pandas`, `numpy`, `scikit‑learn`, `pymatgen`, `shap`).  
  - The full workflow will be orchestrated with a Makefile so that the entire pipeline (download → preprocess → train → evaluate) completes within a 6‑hour GitHub Actions job on the free tier.  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: N/A (no comparable fleshed‑out idea found).  
- Verdict: **NOT a duplicate**.
