---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Volatile Organic Compound Emission Profiles from Publicly Available Genomic and Environmental Data

**Field**: biology

## Research question

How do genomic features and environmental conditions jointly explain variation in plant volatile organic compound (VOC) emission profiles?

## Motivation

VOCs mediate critical plant-insect interactions and stress signaling, yet the quantitative drivers of their emission remain partially understood. While individual genomic or environmental factors are often studied in isolation, a unified predictive framework is lacking. This project addresses the gap by integrating public multi-omics data to determine the relative contribution of genetics versus environment to VOC variability.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms such as "plant volatile organic compound prediction," "genomic determinants of VOC emission," and "machine learning plant volatiles environment." We retrieved general reviews on plant VOC ecology and atmospheric aerosols, but found no studies explicitly modeling emission profiles as a function of paired genomic and environmental inputs.

### What is known

- [Beyond the network of plants volatile organic compounds (2017)](http://arxiv.org/abs/1704.08062v1) — Establishes that VOC emission is involved in a wide class of ecological functions and plays a crucial role in plant interactions with biotic and abiotic factors.
- [Primary biological aerosol particles in the atmosphere: a review (2012)](https://doi.org/10.3402/tellusb.v64i0.15598) — Confirms that biological materials, including plant-derived excretions and fragments, contribute to atmospheric aerosol diversity, contextualizing VOCs in a broader environmental system.

### What is NOT known

No published work has quantitatively mapped specific genomic features (e.g., transcript abundance of terpene synthases) combined with environmental metadata to predict VOC emission profiles using machine learning. Existing literature describes the *function* of VOCs but not the *predictive determinants* of their abundance across conditions.

### Why this gap matters

Filling this gap would enable the identification of key genomic targets for breeding stress-resistant crops without requiring new wet-lab experiments. It also provides a benchmark for understanding how climate variables modulate chemical signaling in ecosystems.

### How this project addresses the gap

This project curates paired transcriptomic and VOC datasets from public repositories to train a regression model. The methodology specifically tests whether genomic markers improve prediction accuracy beyond environmental variables alone, directly quantifying the previously unknown relationship.

## Expected results

We expect environmental factors to explain the majority of variance in VOC profiles, with specific gene families (e.g., terpene synthases) providing significant marginal predictive power. Model performance (R² > 0.5) would confirm that public data integration is sufficient to capture these dynamics, while feature importance scores will highlight candidate genes for further validation.

## Methodology sketch

- Download paired RNA-seq and VOC metabolomics data from NCBI GEO and the Metabolomics Workbench (filtering for *Arabidopsis thaliana* and stress conditions).
- Preprocess data: normalize transcript counts (TPM) and VOC concentrations, handling missing values via imputation.
- Merge datasets using shared experimental metadata (treatment type, time point, tissue).
- Construct feature matrix combining environmental variables (temperature, light) and selected genomic features (pathway-specific gene expression).
- Train a Random Forest Regressor using scikit-learn (CPU-only) to predict VOC emission levels.
- Perform 5-fold cross-validation to estimate generalization performance (R² and RMSE).
- Calculate permutation feature importance to identify top genomic and environmental predictors.
- Visualize results using SHAP values to interpret feature contributions to specific VOC classes.
- Validate findings against known biological pathways (e.g., jasmonic acid signaling) for biological plausibility.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None identified.
- Verdict: NOT a duplicate
