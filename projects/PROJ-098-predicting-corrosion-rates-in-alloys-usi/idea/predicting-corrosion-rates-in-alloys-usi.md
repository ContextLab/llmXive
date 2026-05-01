---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Corrosion Rates in Alloys Using Machine Learning on Public Datasets

**Field**: materials science

## Research question

Can supervised machine learning models accurately predict the corrosion rates of common alloys using only their chemical composition and environmental parameters (temperature, pH, chloride concentration) available in public repositories?

## Motivation

Experimental corrosion testing is resource-intensive, time-consuming, and often limits the speed of materials discovery. Developing a data-driven surrogate model would allow for rapid screening of alloy compositions, reducing the need for extensive physical testing. This project addresses the gap between available materials data and the need for predictive tools that operate within standard computational constraints.

## Related work

- [Reviewing machine learning of corrosion prediction in a data-oriented perspective (2022)](https://doi.org/10.1038/s41529-022-00218-4) — Provides a comprehensive overview of data sources and ML approaches specifically for electrochemical corrosion prediction.
- [Data‐Driven Materials Science: Status, Challenges, and Perspectives (2019)](https://doi.org/10.1002/advs.201900808) — Establishes the paradigm of using materials datasets for knowledge extraction and highlights current data scarcity issues.
- [The Open MatSci ML Toolkit: A Flexible Framework for Machine Learning in Materials Science (2022)](http://arxiv.org/abs/2210.17484v1) — Offers a scalable Python framework for applying ML models on scientific materials data, relevant for pipeline implementation.
- [Exploration of data science techniques to predict fatigue strength of steel from composition and processing parameters (2014)](https://doi.org/10.1186/2193-9772-3-8) — Demonstrates successful application of data analytics to predict material properties from composition, supporting methodological feasibility.
- [Physics-Inspired Interpretability Of Machine Learning Models (2023)](http://arxiv.org/abs/2304.02381v2) — Discusses methods for explaining ML decisions, crucial for identifying key compositional features driving corrosion.

## Expected results

We expect to achieve a regression model with an R² > 0.7 on a held-out test set using public corrosion data. The study will identify the top 3 compositional features (e.g., Chromium content, Nickel ratio) most strongly correlated with corrosion resistance. Evidence will be confirmed via k-fold cross-validation and permutation importance metrics.

## Methodology sketch

- **Data Acquisition**: Download tabular corrosion datasets from public repositories (e.g., Zenodo or GitHub) referenced in the supplementary materials of [5] (https://doi.org/10.1038/s41529-022-00218-4) or use sample data from the Open MatSci ML Toolkit [4].
- **Preprocessing**: Clean missing values, normalize environmental features (temperature, pH), and encode alloy compositions using elemental descriptors.
- **Feature Engineering**: Generate interaction terms between alloying elements and environmental factors to capture synergistic effects.
- **Model Training**: Train Random Forest and Gradient Boosting regressors using `scikit-learn` on CPU (no GPU required) to ensure compatibility with GitHub Actions free-tier limits.
- **Validation**: Perform 5-fold cross-validation to estimate generalization error and prevent overfitting on small datasets.
- **Statistical Testing**: Apply ANOVA to determine if differences in model performance (RMSE) between algorithms are statistically significant.
- **Interpretability**: Use SHAP (SHapley Additive exPlanations) values to rank feature importance and validate physical plausibility.
- **Deployment**: Package the final model and data processing scripts into a reproducible Python environment for the 6-hour job window.

## Duplicate-check

- Reviewed existing ideas: None (new corpus).
- Closest match: None found.
- Verdict: NOT a duplicate
