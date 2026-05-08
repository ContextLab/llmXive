---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Glass Forming Region of Metallic Glass Alloys Using Machine Learning

**Field**: materials science

## Research question

How do atomic-scale compositional descriptors (e.g., atomic size mismatch, electronegativity difference) delineate the boundary between crystalline and amorphous phases in ternary metallic alloy systems?

## Motivation

Identifying the glass-forming region (GFR) is essential for designing metallic glasses with tailored mechanical and magnetic properties, but experimental screening is costly and slow. Current theoretical rules (e.g., atomic size criteria) capture only linear trends and often fail in complex multicomponent systems. A data-driven mapping of compositional space to phase stability would accelerate the discovery of new amorphous alloys by prioritizing synthesis targets.

## Related work

- [Accelerated discovery of metallic glasses through iteration of machine learning and high-throughput experiments](https://doi.org/10.1126/sciadv.aaq1566) — Demonstrates an active learning loop where ML guides experimental validation of GFR boundaries in ternary systems.
- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems](http://arxiv.org/abs/2512.05895v2) — Proposes a specific ML architecture for classifying glass-forming ability based on compositional features.
- [A general-purpose machine learning framework for predicting properties of inorganic materials](https://doi.org/10.1038/npjcompumats.2016.28) — Establishes the methodological baseline for using descriptor-based models on inorganic material property prediction.
- [Which glass stability parameters can assess the glass-forming ability of oxide systems?](http://arxiv.org/abs/2001.01113v1) — Provides statistical methods (bootstrap/Wilcoxon) for evaluating the significance of glass stability parameters, applicable to GFR feature selection.

## Expected results

We expect to identify a subset of non-linear interaction descriptors that outperform traditional atomic size rules in predicting the GFR boundary. A Random Forest or Gradient Boosting model achieving >85% balanced accuracy on held-out alloy compositions would confirm that compositional descriptors encode sufficient physics to distinguish amorphous from crystalline phases. Conversely, a null result (performance near random) would suggest that thermodynamic history or processing conditions dominate over composition alone.

## Methodology sketch

- **Data acquisition**: Download alloy composition and phase label datasets from the supplementary materials of [2] (DOI: 10.1126/sciadv.aaq1566) and the Materials Project (via API) to ensure public reproducibility.
- **Feature engineering**: Compute standard atomic descriptors (atomic radius, valence electron concentration, electronegativity) and interaction terms (mismatch, mixing enthalpy) for each composition.
- **Dataset split**: Partition data into 80% training and 20% test sets, stratified by alloy system (e.g., Zr-Cu-Al vs. Mg-Cu-Y) to test generalization across chemistry.
- **Model training**: Train Random Forest and XGBoost classifiers using `scikit-learn` and `xgboost` on the training set, optimizing hyperparameters via 5-fold cross-validation.
- **Feature importance**: Extract permutation importance scores to rank which compositional descriptors most strongly influence the GFR boundary prediction.
- **Statistical validation**: Apply the Wilcoxon signed-rank test (as suggested in [7]) to compare the performance of the ML model against a baseline linear logistic regression model.
- **Visualization**: Generate SHAP (SHapley Additive exPlanations) plots to visualize how specific descriptor values shift the predicted probability of glass formation.
- **Resource check**: Ensure all steps run within 6 hours on a 2-core CPU runner with <7GB RAM by limiting the dataset to <10,000 compositions and avoiding deep learning architectures.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A (no corpus provided).
- Verdict: NOT a duplicate
