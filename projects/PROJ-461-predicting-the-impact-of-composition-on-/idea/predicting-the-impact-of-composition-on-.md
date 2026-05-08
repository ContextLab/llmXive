---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Impact of Composition on the Density of Metallic Glasses

**Field**: Materials Science

## Research question

How do constituent elemental mass fractions and atomic radii correlate with bulk density across experimentally validated metallic glass systems?

## Motivation

Density is a fundamental physical property that dictates the mechanical behavior and application suitability of metallic glasses, yet it is typically measured post-synthesis. Establishing a predictive link between composition and density would enable rapid computational screening of alloy candidates for lightweight or high-density structural applications without requiring physical fabrication. This addresses the gap between theoretical alloy design and practical property estimation in amorphous materials.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "metallic glass density prediction," "amorphous alloy composition density machine learning," and "metallic glass physical properties dataset." The search returned a single result in the verified literature block that touches on machine learning in complex alloys but does not specifically address metallic glass density.

### What is known

- [High-entropy high-hardness metal carbides discovered by entropy descriptors (2018)](https://doi.org/10.1038/s41467-018-07160-7) — This work demonstrates the utility of entropy descriptors and machine learning for predicting formation and properties in high-entropy materials, establishing a methodological precedent for data-driven alloy design.

### What is NOT known

There is no published work that specifically quantifies the relationship between elemental composition and bulk density for metallic glasses using standardized public datasets. While high-entropy alloy studies exist, the amorphous structure of metallic glasses introduces distinct packing efficiency variables that are not captured by crystalline carbide models.

### Why this gap matters

Filling this gap would provide a baseline estimator for density that alloy designers can use before committing to expensive melting and casting processes. It would clarify whether density in amorphous phases is primarily governed by atomic mass (simple mixing rule) or if amorphous packing constraints introduce non-linear deviations.

### How this project addresses the gap

This project compiles public metallic glass composition and density records to train a regression model that explicitly tests the composition-density relationship. By isolating amorphous systems, the methodology produces the specific evidence needed to determine if standard mixing rules suffice or if amorphous-specific descriptors are required.

## Expected results

We expect to find a strong positive correlation between mean atomic mass and density, but with significant variance explained by atomic radius mismatch and packing efficiency. A regression model achieving a mean absolute error below 0.1 g/cm³ would confirm that composition is a dominant predictor, while higher error would suggest structural factors play a larger role.

## Methodology sketch

- **Data acquisition**: Download curated metallic glass composition and density datasets from public repositories (e.g., Zenodo or GitHub repositories hosting MGDB compilations) using `wget`.
- **Feature engineering**: Compute compositional descriptors including mean atomic mass, mean atomic radius, and electronegativity variance for each alloy.
- **Data splitting**: Partition the dataset into training (80%) and test (20%) sets using stratified sampling to ensure coverage of different alloy families.
- **Model training**: Fit a Gradient Boosting Regressor (e.g., LightGBM or XGBoost CPU version) to map compositional features to density values.
- **Hyperparameter tuning**: Perform a coarse grid search on learning rate and tree depth within the 6-hour runtime limit.
- **Evaluation**: Calculate R-squared and Mean Absolute Error (MAE) on the held-out test set to assess predictive power.
- **Feature importance**: Extract SHAP values or permutation importance to identify which elemental properties most influence density predictions.
- **Visualization**: Generate scatter plots of predicted vs. actual density and partial dependence plots for top features.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A.
- Verdict: NOT a duplicate
