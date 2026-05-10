---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning

**Field**: materials science

## Research question

How do atomic size mismatch and mixing enthalpy descriptors determine the boundaries of the glass-forming region in multi-component metallic systems?

## Motivation

Experimentally mapping the glass-forming region (GFR) for multi-component alloys requires extensive trial-and-error synthesis, which is resource-intensive and slow. While machine learning has been applied to glass-forming ability in oxide systems, its application to metallic multi-component alloys remains under-explored. This project addresses the gap by quantifying the relationship between compositional descriptors and glass stability to accelerate materials discovery.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms including "machine learning glass forming ability," "alloy composition descriptors," and "active learning materials discovery." We examined the returned literature for specific applicability to *metallic multi-component* systems versus oxide glasses or generic materials science frameworks.

### What is known

- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025)](http://arxiv.org/abs/2512.05895v2) — Establishes an ML framework for predicting glass-forming ability, though focused primarily on oxide glasses and ternary systems.
- [DScribe: Library of descriptors for machine learning in materials science (2019)](https://doi.org/10.1016/j.cpc.2019.106949) — Provides standard software for computing atomistic descriptors (e.g., SOAP, ACSF) required for feature engineering in alloy models.
- [Active learning in materials science with emphasis on adaptive sampling using uncertainties for targeted design (2019)](https://doi.org/10.1038/s41524-019-0153-8) — Reviews active learning strategies for efficient materials discovery, relevant for optimizing the search of the compositional space.

### What is NOT known

No published work in the provided literature explicitly validates the predictive power of standard thermodynamic descriptors for the glass-forming region specifically within *metallic* multi-component systems (e.g., high-entropy alloys). The existing ML frameworks are either domain-specific to oxides or lack the compositional complexity of multi-component metallics.

### Why this gap matters

Metallic glasses offer superior mechanical properties (strength, elasticity) compared to crystalline alloys, but their discovery is bottlenecked by the difficulty of identifying stable glass-forming compositions. Filling this gap would enable computational screening of vast compositional spaces, reducing experimental costs and time-to-material.

### How this project addresses the gap

This project adapts the descriptor-based ML approach from the existing literature to a curated dataset of metallic alloy compositions. By training models specifically on metallic systems and evaluating feature importance, we directly test whether standard thermodynamic descriptors generalize to the metallic multi-component GFR.

## Expected results

We expect to identify a subset of compositional descriptors (e.g., atomic size mismatch, electronegativity difference) that significantly correlate with glass formation. We anticipate a classification model achieving >80% accuracy in distinguishing glass-forming from crystalline regions on held-out test data, with feature importance scores revealing the dominant physical drivers.

## Methodology sketch

- **Data Acquisition**: Download alloy composition and phase data from the Materials Project (https://materialsproject.org) and NIST Alloy Database (https://www.nist.gov/pml/alloy-database) using `wget` scripts.
- **Data Filtering**: Filter the dataset to retain only multi-component metallic systems (≥3 elements) and label samples as "glass-forming" or "crystalline" based on reported phase diagrams.
- **Feature Engineering**: Compute atomic size mismatch, mixing enthalpy, and electronegativity variance for each composition using Python libraries (e.g., `pymatgen` or `DScribe`).
- **Model Training**: Train Random Forest and Gradient Boosting classifiers using `scikit-learn` on CPU (no GPU required) with hyperparameter tuning via 5-fold cross-validation.
- **Evaluation**: Assess model performance using ROC-AUC and precision-recall metrics on a held-out test set (20% of data).
- **Statistical Analysis**: Apply permutation importance tests to determine which descriptors most strongly influence the predicted glass-forming boundary.
- **Visualization**: Generate SHAP summary plots to visualize the relationship between descriptor values and the probability of glass formation.
- **Reproducibility**: Package the code and data processing scripts into a GitHub repository compatible with GitHub Actions runners (≤7GB RAM, 2 CPU).

## Duplicate-check

- Reviewed existing ideas: None provided in current session.
- Closest match: None identified.
- Verdict: NOT a duplicate.
