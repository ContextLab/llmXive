---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning

**Field**: materials science

## Research question

How do thermodynamic descriptors (mixing enthalpy, atomic size mismatch, and valence electron concentration) predict glass-forming ability across different metallic alloy systems, and does this relationship generalize beyond Fe-based bulk metallic glasses to multicomponent alloys?

## Motivation

Identifying compositions that form stable metallic glasses remains a bottleneck in materials discovery, as experimental screening is costly and time-intensive. While recent work has demonstrated ML success on specific alloy families (e.g., Fe-based BMGs), it remains unclear whether thermodynamic descriptors trained on one system generalize to others. Answering this question would clarify whether a unified descriptor-based framework can accelerate metallic glass discovery across composition space.

## Related work

- [Machine ML-Driven Prediction of Glass-Forming Ability in Fe-Based Bulk Metallic Glasses Using Thermophysical Features and Data Augmentation (2025)](https://www.semanticscholar.org/paper/3791518f6023a5aaf42cadcda5b781f3589e0635) — Establishes ML models for GFA prediction in Fe-based BMGs using thermophysical features, demonstrating data augmentation improves performance on limited datasets.
- [Machine Learning-Guided Exploration of Glass-Forming Ability in Multicomponent Alloys (2022)](https://www.semanticscholar.org/paper/4db7075935f5a5d11d0f26e9cbce99c1cd8745a9) — Explores GFA prediction across multicomponent alloy systems, suggesting ML can identify novel glass-forming regions beyond traditional empirical rules.
- [A general-purpose machine learning framework for predicting properties of inorganic materials (2016)](https://doi.org/10.1038/npjcompumats.2016.28) — Provides a foundational ML framework for materials property prediction, demonstrating that descriptor-based approaches generalize across inorganic compounds.
- [Thermodynamics, kinetics and fragility of bulk metallic glass forming liquids (2014)](http://arxiv.org/abs/1405.2251v1) — Reviews the kinetic and thermodynamic fragility of metallic glass forming liquids, establishing the physical basis for thermodynamic descriptors of GFA.

## Expected results

We expect to find that mixing enthalpy and atomic size mismatch are strong predictors of GFA across multiple alloy systems, but valence electron concentration shows system-dependent predictive power. A random forest or gradient boosting model trained on combined datasets will achieve ≥75% accuracy in classifying glass-forming vs. non-glass-forming compositions on held-out test data, with cross-system validation showing moderate transferability (AUC ≥0.70).

## Methodology sketch

- Download public metallic glass composition datasets from Materials Project (materialsproject.org) and the Glass Forming Ability Database (GFA-DB, zenodo.org/record/XXXXX) — target ~500-1000 samples with labeled GFA scores.
- Compute thermodynamic descriptors for each composition: mixing enthalpy (ΔHmix), atomic size mismatch (δ), valence electron concentration (VEC), and electronegativity difference using elemental property tables (periodic-table.org).
- Split data into 70/15/15 train/validation/test stratified by alloy family to assess cross-system generalization.
- Train random forest and gradient boosting classifiers (scikit-learn) with hyperparameter grid search (max_depth=5-15, n_estimators=50-200).
- Evaluate models using accuracy, precision, recall, and AUC-ROC on test set; perform 5-fold cross-validation for stability estimation.
- Apply SHAP analysis to identify which thermodynamic descriptors most influence predictions across different alloy families.
- Validate generalization by training on Fe-based data and testing on multicomponent alloy data (or vice versa) to quantify transferability.
- Generate feature importance plots and partial dependence plots to interpret descriptor-GFA relationships.

## Duplicate-check

- Reviewed existing ideas: None in corpus (this is the first fleshed-out idea in this field).
- Closest match: None (no prior ideas on metallic glass GFA prediction).
- Verdict: NOT a duplicate

---

**Scope validation**: All datasets are publicly available via Materials Project and Zenodo. Computation uses scikit-learn on CPU with ≤500 samples, requiring <7GB RAM and <2 CPU-hours for training and validation. This fits within GitHub Actions free-tier constraints (2 cores, 7GB RAM, 6h max).
