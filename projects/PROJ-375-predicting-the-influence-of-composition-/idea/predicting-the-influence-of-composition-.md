---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Field**: materials science

## Research question

How does alloy composition determine the coefficient of thermal expansion (CTE) in metallic glasses?

## Motivation

Metallic glasses require precise CTE control for applications in aerospace, precision optics, and biomedical devices where dimensional stability is critical. Existing empirical rules of mixtures fail to capture the complex, non-linear relationships between elemental composition and CTE in amorphous alloys. This project addresses the gap by establishing a data-driven mapping from composition to CTE that can guide alloy design.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using search terms including: "metallic glass thermal expansion coefficient," "CTE prediction metallic glass composition," "amorphous alloy thermal expansion modeling," and "composition-CTE relationship metallic glasses." The literature search returned sparse results on this specific topic, with only tangentially related work on metallic glass thermal behavior.

### What is known

- [Rejuvenation of metallic glasses by non-affine thermal strain (2015)](https://doi.org/10.1038/nature14674) — This work establishes that thermal strain can modify the structural state of metallic glasses, demonstrating that thermal history affects their properties, but does not predict CTE from composition.

### What is NOT known

No published work has systematically quantified the relationship between elemental composition and CTE across diverse metallic glass families. Existing studies focus on specific alloy systems or thermal treatment effects rather than establishing a generalizable composition-CTE mapping. There is no validated predictive model that can estimate CTE from compositional features alone.

### Why this gap matters

Materials designers need to screen candidate compositions before costly synthesis and characterization. A validated composition-CTE predictor would accelerate development of metallic glasses for applications requiring thermal stability, such as precision instrument components and biomedical implants where differential expansion causes failure.

### How this project addresses the gap

Our methodology compiles public CTE measurements from Materials Project and AFLOWlib, extracts compositional descriptors (atomic radius, electronegativity, valence electron concentration), and trains regression models to establish the composition-CTE mapping. The cross-validation framework quantifies predictive accuracy, directly providing the previously unavailable evidence on compositional control of thermal expansion.

## Expected results

We expect to identify compositional descriptors that correlate significantly with CTE (p < 0.05) across multiple metallic glass families. A regression model achieving R² > 0.6 on held-out test data would demonstrate predictive utility beyond empirical rules of mixtures. Null results (R² < 0.3) would indicate that CTE is governed by structural factors beyond composition alone.

## Methodology sketch

- Download metallic glass CTE measurements and compositions from Materials Project (https://materialsproject.org) and AFLOWlib (http://aflowlib.org) using REST API
- Extract compositional features: weighted mean atomic radius, electronegativity variance, valence electron concentration, and atomic size mismatch for each alloy
- Split dataset into 80/20 train-test stratified by alloy family (Zr-based, Pd-based, Fe-based, etc.)
- Train baseline linear regression and random forest models using scikit-learn on CPU (≤2 cores, ≤7 GB RAM)
- Perform 5-fold cross-validation on training set to tune hyperparameters (grid search over 10 parameter combinations)
- Evaluate final models on held-out test set using R², MAE, and RMSE metrics
- Apply statistical significance testing (permutation test, 1000 iterations) to assess whether model performance exceeds random chance
- Generate feature importance rankings to identify which compositional descriptors most influence CTE
- Compare model predictions against empirical rules of mixtures on a subset of known alloys

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
