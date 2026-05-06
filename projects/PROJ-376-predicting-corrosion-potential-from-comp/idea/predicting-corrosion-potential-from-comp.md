---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Corrosion Potential from Composition and Environment via Public Databases

**Field**: Materials Science

## Research question

How do alloy composition and environmental conditions interact to determine the corrosion potential of metallic alloys?

## Motivation

Corrosion causes significant economic loss and infrastructure failure, yet predictive models remain largely environment-specific. A generalizable model linking composition and environment to corrosion potential would accelerate materials selection and reduce reliance on costly empirical testing.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for "corrosion potential prediction machine learning", "alloy composition corrosion dataset", and "hot corrosion causal discovery". Results included causal mechanism studies, data extraction tools, and nanoparticle synthesis literature, but few integrated predictive modeling studies on public databases.

### What is known

- [Causal Discovery to Understand Hot Corrosion (2024)](http://arxiv.org/abs/2402.07804v1) — This work establishes that hot corrosion in superalloys is driven by specific factors like deposit flux, temperature, and gas composition, clarifying mechanisms but not providing a general predictive model across alloy classes.

### What is NOT known

There is a lack of integrated public datasets combining alloy composition and environmental parameters for broad corrosion potential prediction. Existing literature focuses on specific mechanisms (e.g., hot corrosion in turbines) rather than generalizable regression relationships applicable to diverse metallic systems.

### Why this gap matters

Filling this gap would enable computational screening of alloys for specific environments before physical prototyping, reducing R&D costs and time-to-market for corrosion-resistant materials in infrastructure and energy sectors.

### How this project addresses the gap

This project aggregates public composition data (Materials Project) and corrosion records (NIST) to train and evaluate machine learning models that quantify the interaction effects between alloying elements and environmental variables on corrosion potential.

## Expected results

We expect to identify key alloying elements that consistently reduce corrosion potential across multiple environments, with model performance (R² > 0.6) confirming a learnable relationship. A null result (low predictive power) would indicate that corrosion is dominated by unrecorded microstructural or surface factors rather than bulk composition alone.

## Methodology sketch

- Download alloy composition data from the Materials Project API (`https://next-gen.materialsproject.org/`) for candidate metals (e.g., Fe, Al, Ni, Ti alloys).
- Retrieve corrosion potential measurements from public NIST Standard Reference Data records (`https://www.nist.gov/`) matching the composition and environment metadata.
- Preprocess data by encoding composition as elemental weight fractions and environments as categorical variables (e.g., pH, temperature, saline/acidic).
- Split the dataset into 80% training and 20% testing sets, ensuring no alloy class leakage between splits.
- Train Random Forest and Gradient Boosting regressors (CPU-optimized) to predict corrosion potential from features.
- Evaluate model performance using R² and Root Mean Squared Error (RMSE) on the held-out test set.
- Perform permutation importance analysis to quantify the contribution of specific elements and environmental factors.
- Conduct statistical significance testing (ANOVA) on feature importance scores to verify robustness.
- Generate partial dependence plots to visualize non-linear interactions between composition and environment.
- Document all code and data processing steps in a reproducible GitHub Actions workflow compatible with 2 CPU/7GB RAM limits.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None.
- Verdict: NOT a duplicate
