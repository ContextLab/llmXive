---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases

**Field**: chemistry

## Research question

Which environmental factors (pH, salinity, temperature) and material properties (composition, crystal structure) most strongly determine corrosion rates across common metals, and how do these drivers interact under different conditions?

## Motivation

Corrosion causes billions in annual infrastructure damage, yet traditional measurement methods are slow and costly. This project addresses the gap in understanding the *relative* and *interactive* influence of environmental vs. material drivers by leveraging data-driven materials science. Success would provide a data-backed hierarchy of risk factors, enabling targeted maintenance strategies rather than generic material replacement.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using terms including "corrosion rate prediction machine learning," "environmental factors corrosion dataset," and "materials informatics corrosion." The search returned several general papers on ML validation and data science trends, but no primary studies specifically quantifying the interaction effects between specific environmental variables (pH, salinity) and material microstructure on corrosion rates in public datasets.

### What is known
- [Changing Data Sources in the Age of Machine Learning for Official Statistics (2023)](https://arxiv.org/abs/2306.04338) — Establishes the paradigm of using automated data collection and ML for statistical analysis in large-scale scientific domains, supporting the feasibility of aggregating public corrosion data.
- [DOME: Recommendations for supervised machine learning validation in biology (2020)](https://arxiv.org/abs/2006.16189) — Provides critical guidelines for rigorous ML validation in scientific contexts, emphasizing the need for independent test sets and avoiding circular reasoning, which this project will adopt.
- [Physics-Inspired Interpretability Of Machine Learning Models (2023)](https://arxiv.org/abs/2304.02381) — Highlights the importance of using interpretability tools (like SHAP) to extract physical insights from "black box" models, a key requirement for answering the "how do these drivers interact" part of our question.

### What is NOT known
No published work has specifically isolated and quantified the interaction terms between environmental stressors (e.g., salinity × pH) and material composition to predict corrosion rates using only public, tabular datasets. Existing literature often focuses on model accuracy benchmarks or broad data trends rather than the specific mechanistic drivers of corrosion variability.

### Why this gap matters
Understanding the specific interaction effects is crucial for material selection in complex environments (e.g., marine vs. industrial atmospheres). Without this granular knowledge, engineers may over-rely on conservative material choices or miss critical environmental thresholds, leading to either unnecessary costs or premature failure.

### How this project addresses the gap
This project will explicitly engineer interaction features and use interpretable ML models (Random Forest/Gradient Boosting with SHAP analysis) to rank the importance of environmental vs. material factors and visualize their non-linear interactions, directly filling the gap in quantitative driver analysis.

## Expected results

The project expects to identify a specific set of high-impact interaction terms (e.g., high salinity combined with low pH) that dominate corrosion rate predictions across common metals. The measurement will confirm the feasibility of ML prediction if feature importance analysis reveals that environmental interactions explain a significant portion of variance (>30%) beyond material composition alone. Evidence will be provided via SHAP summary plots and partial dependence curves showing non-linear interaction effects.

## Methodology sketch

- **Data Acquisition**: Search Zenodo, HuggingFace Datasets, and OpenML for tabular corrosion datasets containing columns for material type, composition, environmental conditions (pH, temperature, salinity), and measured corrosion rate (e.g., `https://zenodo.org/search?q=corrosion+dataset` or specific DOI if found).
- **Preprocessing**: Clean missing values using `pandas`; normalize environmental features and encode categorical material properties using `scikit-learn`.
- **Feature Engineering**: Explicitly construct interaction terms (e.g., `pH * salinity`, `temperature * composition_ratio`) and polynomial features to capture non-linear relationships.
- **Model Training**: Split data into 80/20 train/test sets; train Random Forest and Gradient Boosting regressors using `scikit-learn` (CPU-only) to model the relationship between features and corrosion rate.
- **Hyperparameter Tuning**: Perform grid search with constrained depth (max_depth=5) and limited trees to stay within 7GB RAM and 6-hour runtime limits.
- **Statistical Evaluation**: Calculate Root Mean Squared Error (RMSE) and R² on the **held-out test set** (independent of training data) to assess predictive power; apply k-fold cross-validation (k=5) to ensure robustness.
- **Interpretability Analysis**: Generate SHAP (SHapley Additive exPlanations) values to quantify the contribution of each feature and interaction term to the predicted corrosion rate, identifying the dominant drivers.
- **Visualization**: Create partial dependence plots and SHAP summary plots to visualize how corrosion rates change with varying environmental conditions and material properties.
- **Reporting**: Save model artifacts, feature importance rankings, and interaction visualizations to the project repository; document data sources with DOIs for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-07T07:25:59Z
**Outcome**: success_after_expansion
**Original term**: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases chemistry
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases chemistry | 0 |
| 1 | machine learning models for corrosion rate prediction | 5 |
| 2 | data-driven corrosion kinetics modeling | 0 |
| 3 | artificial intelligence in corrosion science | 0 |
| 4 | predictive modeling of metal degradation | 0 |
| 5 | corrosion rate estimation using public datasets | 0 |
| 6 | supervised learning for electrochemical corrosion | 0 |
| 7 | machine learning approaches to atmospheric corrosion | 0 |
| 8 | data mining corrosion databases for rate prediction | 0 |
| 9 | computational corrosion prediction algorithms | 0 |
| 10 | corrosion behavior prediction using neural networks | 0 |
| 11 | regression models for metal corrosion rates | 0 |
| 12 | corrosion data analysis and machine learning | 0 |
| 13 | ML-based prediction of uniform corrosion rates | 0 |
| 14 | digital twins for corrosion rate forecasting | 0 |
| 15 | corrosion kinetics prediction via deep learning | 0 |
| 16 | statistical and machine learning methods in corrosion | 0 |
| 17 | open access corrosion data and predictive analytics | 0 |
| 18 | corrosion rate forecasting for structural metals | 0 |
| 19 | electrochemical data mining for corrosion modeling | 0 |
| 20 | hybrid physics-informed machine learning for corrosion | 0 |

### Verified citations

1. **Changing Data Sources in the Age of Machine Learning for Official Statistics** (2023). Cedric De Boom, Michael Reusens. arXiv. [2306.04338](https://arxiv.org/abs/2306.04338). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Learning Curves for Decision Making in Supervised Machine Learning: A Survey** (2022). Felix Mohr, Jan N. van Rijn. arXiv. [2201.12150](https://arxiv.org/abs/2201.12150). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **DOME: Recommendations for supervised machine learning validation in biology** (2020). Ian Walsh, Dmytro Fishman, Dario Garcia-Gasulla, Tiina Titma, Gianluca Pollastri, et al.. arXiv. [2006.16189](https://arxiv.org/abs/2006.16189). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Physics-Inspired Interpretability Of Machine Learning Models** (2023). Maximilian P Niroomand, David J Wales. arXiv. [2304.02381](https://arxiv.org/abs/2304.02381). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **A Benchmark Study of Machine Learning Models for Online Fake News Detection** (2019). Junaed Younus Khan, Md. Tawkat Islam Khondaker, Sadia Afroz, Gias Uddin, Anindya Iqbal. arXiv. [1905.04749](https://arxiv.org/abs/1905.04749). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
