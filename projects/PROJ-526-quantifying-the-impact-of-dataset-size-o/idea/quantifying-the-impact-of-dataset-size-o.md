---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Dataset Size on the Accuracy of Machine Learning Models for Predicting Material Properties

**Field**: physics

## Research question

How does the prediction error of machine learning models for material properties (e.g., band gap, bulk modulus) scale as a function of training dataset size in materials informatics?

## Motivation

Materials discovery efforts increasingly rely on machine learning to predict properties from composition or structure, but the data requirements for achieving target accuracy remain poorly quantified. Establishing scaling laws between dataset size and prediction error would guide resource allocation for future data generation and help researchers determine whether collecting additional experimental or DFT-computed data is cost-effective for their specific prediction task.

## Literature gap analysis

### What we searched

We queried Semantic Scholar / arXiv / OpenAlex using two distinct queries: (1) "dataset size scaling machine learning materials properties" and (2) "learning curves materials informatics dataset size". The search returned 8 results from the literature block, of which 4 were directly on-topic for materials science ML applications and 1 specifically addressed learning curves in supervised ML.

### What is known

- [Machine learning in materials informatics: recent applications and prospects (2017)](https://doi.org/10.1038/s41524-017-0056-5) — This review establishes the breadth of ML applications in materials science but does not quantify dataset size requirements for specific property predictions.
- [Recent advances and applications of deep learning methods in materials science (2022)](https://doi.org/10.1038/s41524-022-00734-6) — Documents growing use of deep learning in materials data science but focuses on architectural advances rather than data quantity scaling.
- [Recent advances and applications of machine learning in solid-state materials science (2019)](https://doi.org/10.1038/s41524-019-0221-0) — Surveys ML methods in solid-state materials science but provides no systematic analysis of dataset size versus prediction accuracy.
- [Learning Curves for Decision Making in Supervised Machine Learning: A Survey (2022)](http://arxiv.org/abs/2201.12150v2) — This survey establishes learning curves as a concept for assessing ML performance with respect to resource constraints, but does not apply it to materials property prediction datasets.

### What is NOT known

No published work has systematically measured how prediction error scales with training set size across multiple material properties (band gap, formation energy, bulk modulus) using standard regression algorithms on public materials databases. The learning curve behavior for materials informatics datasets remains uncharacterized, and there is no consensus on whether materials property prediction follows the same power-law scaling observed in other domains.

### Why this gap matters

Materials researchers designing data collection campaigns need evidence-based guidance on whether additional DFT calculations or experimental measurements will meaningfully improve model accuracy. Filling this gap would enable more efficient allocation of computational resources in the Materials Genome Initiative and similar data-driven materials discovery efforts, potentially accelerating the identification of promising candidate materials.

### How this project addresses the gap

This project will construct learning curves by training standard regression models (Random Forest, Gradient Boosting) on systematically subsampled Materials Project and AFLOW datasets, measuring prediction error at multiple training set sizes. The resulting scaling laws directly quantify the relationship between dataset size and prediction accuracy for materials properties, providing the first empirical evidence for data requirements in this domain.

## Expected results

We expect to observe a power-law relationship between training set size and prediction error, with the exponent varying by property and model complexity. Confirmation would be demonstrated by consistent scaling across multiple material properties and datasets, while a null result (no systematic scaling) would indicate that factors other than data quantity (e.g., feature quality, physics constraints) dominate prediction accuracy.

## Methodology sketch

- Download Materials Project band gap and formation energy datasets via the public API (https://materialsproject.org) and AFLOW via direct HTTPS download; limit to ≤50,000 entries to fit within 7GB RAM.
- Extract composition-based features using standard descriptors (e.g., Magpie, elemental property vectors) and split into train/test sets with 20% held out for final evaluation.
- Generate 8-10 training set sizes ranging from 1,000 to 40,000 samples by random subsampling; ensure each size is repeated 3 times with different random seeds for variance estimation.
- Train Random Forest and Gradient Boosting regressors (scikit-learn) on each subsampled training set; use default hyperparameters to avoid tuning overhead.
- Measure mean absolute error (MAE) on the held-out test set for each training size; record computation time and memory usage per model.
- Fit power-law scaling models (error = a × N^b) to the learning curves using linear regression on log-transformed data; compute 95% confidence intervals on the exponent b.
- Compare scaling exponents across properties (band gap vs. formation energy) and models (Random Forest vs. Gradient Boosting) using t-tests on the fitted exponents.
- Produce figures showing learning curves with confidence bands and a summary table of scaling exponents for each property-model combination.

## Duplicate-check

- Reviewed existing ideas: None (no existing_idea_paths provided).
- Closest match: None identified.
- Verdict: NOT a duplicate
