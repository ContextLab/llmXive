---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Alloying on Creep Resistance via Public Data

**Field**: materials science

## Research question

How do alloying elements and derived thermodynamic descriptors govern creep resistance in high‑temperature alloys, and to what extent can composition alone predict rupture time compared to microstructure‑dependent factors?

## Motivation

Creep resistance determines the service lifetime of components operating above 800 °C, yet the design of creep‑resistant alloys still relies heavily on trial‑and‑error experiments. While machine learning has been proposed for materials discovery, the specific contribution of composition versus microstructure remains debated. Publicly released high‑temperature mechanical data combined with computational thermodynamic descriptors provide an opportunity to isolate the predictive power of composition. A reliable quantification of this gap would enable rapid virtual screening of candidate alloys, reducing experimental cost and accelerating materials discovery for power, aerospace, and petrochemical applications.

## Literature gap analysis

### What we searched

Queried Semantic Scholar and arXiv for terms including "alloy creep resistance machine learning," "composition‑based creep prediction," and "thermodynamic descriptors high‑temperature alloys." Searched sources included arXiv, Semantic Scholar, and OpenAlex for peer‑reviewed or preprint literature published between 2015–2024. Returned volume was low, with only one directly on‑topic result found regarding data analytics for creep.

### What is known

- [Modern Data Analytics Approach to Predict Creep of High-Temperature Alloys (2018)](https://arxiv.org/abs/1811.01239) — Establishes that modern data analytics workflows can generate novel material hypotheses and predict creep behavior in multi‑component systems, confirming feasibility of data‑driven approaches.

### What is NOT known

No published work has explicitly quantified the variance in creep rupture time explained specifically by thermodynamic descriptors versus raw elemental fractions on public datasets. Furthermore, there is limited evidence on the predictive ceiling of composition‑only models when microstructural data (grain size, precipitate distribution) is absent from the feature set.

### Why this gap matters

Filling this gap would clarify whether expensive microstructural characterization is strictly necessary for initial alloy screening. If composition and thermodynamic descriptors suffice for high‑accuracy prediction, it would drastically reduce the cost of virtual screening for power and aerospace industries. Conversely, identifying the limitation would direct future efforts toward acquiring microstructure‑linked datasets.

### How this project addresses the gap

This project applies a rigorous feature‑importance analysis (SHAP values) to a public creep dataset to rank the contribution of thermodynamic descriptors against elemental fractions. By comparing model performance against a baseline that ignores thermodynamic physics, we quantify the marginal gain of physics‑informed features, directly addressing the unknown predictive ceiling of composition‑only models.

## Expected results

A regression model incorporating thermodynamic descriptors will achieve an out‑of‑sample R² ≥ 0.70, significantly outperforming a composition‑only baseline (p < 0.05 via paired t‑test on CV scores). Feature‑importance analysis will identify specific alloying elements (e.g., Ta, Mo, W) and descriptors (mixing enthalpy, atomic radius mismatch) that govern resistance. These results will demonstrate whether composition alone is sufficient for screening or if microstructure‑dependent factors introduce irreducible uncertainty.

## Methodology sketch

- **Data acquisition**
  - Download the NIMS Creep Data Center dataset (https://www.nims.go.jp/creep/) or equivalent public CSV via `wget`.
  - Retrieve alloy composition and calculated thermodynamic properties from the Materials Project API (https://materialsproject.org/open) for each alloy in the dataset.
- **Data cleaning & preprocessing**
  - Parse compositions into elemental fractions; remove entries with missing temperature, stress, or rupture time.
  - Compute derived features: average atomic radius, mixing enthalpy (using pymatgen’s `MPRester`), solid‑solution strengthening estimates (Fleischer model).
  - Log‑transform creep rupture time to stabilize variance and handle skew.
- **Model development**
  - Split data into 80 % training / 20 % test stratified by temperature range to prevent leakage.
  - Train a Gradient Boosting Regressor (`sklearn.ensemble.GradientBoostingRegressor`) with hyper‑parameter tuning via `GridSearchCV` (max_depth, n_estimators, learning_rate).
  - Perform 5‑fold cross‑validation on the training set; record RMSE and R² for each fold.
- **Baseline comparison**
  - Fit a simple linear regression model using only total alloying weight percent as predictor (composition‑only baseline).
  - Apply a paired‑sample t‑test on the CV RMSE values of the two models to assess statistical significance.
- **Evaluation**
  - Compute out‑of‑sample R², RMSE, and mean absolute error on the held‑out test set.
  - Generate SHAP (SHapley Additive exPlanations) plots to visualize feature contributions and quantify the impact of thermodynamic descriptors.
- **Reproducibility**
  - All scripts will be written in Python 3.11, using only CPU‑friendly libraries (`pandas`, `numpy`, `scikit‑learn`, `pymatgen`, `shap`).
  - The full workflow will be orchestrated with a Makefile so that the entire pipeline (download → preprocess → train → evaluate) completes within a 6‑hour GitHub Actions job on the free tier.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A (no comparable fleshed‑out idea found).
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-28T21:51:15Z
**Outcome**: exhausted
**Original term**: Predicting the Impact of Alloying on Creep Resistance via Public Data materials science
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting the Impact of Alloying on Creep Resistance via Public Data materials science | 0 |
| 1 | Machine learning creep property prediction | 5 |
| 2 | Data-driven alloy creep modeling | 0 |
| 3 | Materials informatics for creep resistance | 0 |
| 4 | Computational prediction of creep strength | 0 |
| 5 | Alloy composition effects on creep | 0 |
| 6 | High-temperature mechanical property prediction | 0 |
| 7 | Nickel-based superalloy creep data | 0 |
| 8 | Public materials databases for creep | 0 |
| 9 | Machine learning assisted alloy design | 0 |
| 10 | Accelerated materials discovery creep | 0 |
| 11 | Creep rupture life prediction models | 0 |
| 12 | Statistical learning for metallurgical properties | 0 |
| 13 | Composition-property relationships in alloys | 0 |
| 14 | Time-dependent deformation prediction | 0 |
| 15 | Integrated computational materials engineering | 0 |
| 16 | Thermodynamic modeling of creep | 0 |
| 17 | Microstructure-property relationships creep | 0 |
| 18 | Open data materials science creep | 0 |
| 19 | Dislocation dynamics creep simulation | 0 |
| 20 | High-throughput experimentation creep | 0 |

### Verified citations

1. **Modern Data Analytics Approach to Predict Creep of High-Temperature Alloys** (2018). Dongwon Shin, Yukinori Yamamoto, Michael P. Brady, Sangkeun Lee, J. Allen Haynes. arXiv. [1811.01239](https://arxiv.org/abs/1811.01239). PDF-sampled: No.
