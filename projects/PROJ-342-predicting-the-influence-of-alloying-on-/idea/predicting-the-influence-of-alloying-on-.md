---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Field**: materials science

## Research question

How do compositional descriptors (atomic radius mismatch, electronegativity difference, and valence electron concentration) systematically influence the glass transition temperature (Tg) in metallic glasses across different alloy families?

## Motivation

The glass transition temperature determines the usable temperature range and thermal stability of metallic glasses for structural and functional applications. Experimental Tg measurement is time-consuming and expensive, requiring dedicated thermal analysis equipment for each new composition. A quantitative mapping between compositional features and Tg would accelerate the discovery of metallic glasses with tailored thermal properties and provide mechanistic insight into the atomic-scale drivers of glass stability.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using the following search terms: "metallic glass glass transition temperature prediction," "Tg composition relationship metallic glasses," "machine learning glass transition temperature," and "alloying effect glass transition temperature." The searches returned 6 papers total, but only 1-2 were directly relevant to Tg prediction in metallic glasses specifically.

### What is known

- [Theory of the Structural Glass Transition: A Pedagogical Review](http://arxiv.org/abs/1511.05998v1) — Establishes the theoretical framework for understanding glass transitions but does not provide quantitative composition-to-Tg mappings for metallic glasses.
- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems](http://arxiv.org/abs/2512.05895v2) — Demonstrates ML approaches for glass-forming ability prediction in oxide glasses, but does not address Tg specifically or metallic glass systems.

### What is NOT known

No published work has systematically quantified how specific compositional descriptors (atomic radius mismatch, electronegativity difference, valence electron concentration) correlate with Tg values across diverse metallic glass families using publicly available datasets. The existing literature focuses on glass-forming ability or theoretical frameworks rather than predictive models for Tg from composition alone.

### Why this gap matters

Materials scientists designing new metallic glasses for aerospace, energy, or biomedical applications need rapid screening tools to identify compositions with suitable thermal stability before experimental synthesis. Filling this gap would enable data-driven alloy design, reduce experimental iteration cycles, and potentially reveal which atomic-scale features most strongly govern glass stability.

### How this project addresses the gap

This project will compile public metallic glass composition-Tg datasets, engineer compositional descriptors, and train interpretable regression models to quantify feature-Tg relationships. The feature importance analysis will directly identify which compositional factors most strongly influence Tg, providing the previously unavailable quantitative mapping.

## Expected results

We expect to identify 2-3 compositional descriptors that show statistically significant correlation with Tg (R² > 0.5 on held-out test data). A null result (R² < 0.3) would indicate that Tg depends on factors beyond simple compositional descriptors (e.g., processing history, cooling rate). Either outcome would be informative: positive results enable accelerated alloy design, while null results would guide future work toward additional feature engineering or alternative data sources.

## Methodology sketch

- **Data acquisition**: Download metallic glass composition and Tg datasets from Materials Project (https://materialsproject.org) and/or published compilations (e.g., Inorganic Glass Database via Zenodo DOI: 10.5281/zenodo.XXXXXX); verify data completeness (composition + Tg pairs only).
- **Data preprocessing**: Filter for metallic glasses only (exclude crystalline alloys), remove duplicates, handle missing values via listwise deletion, split into 80/20 train/test stratified by alloy family.
- **Feature engineering**: Compute atomic-scale descriptors for each composition: weighted mean atomic radius, atomic radius mismatch (standard deviation of radii), electronegativity difference (Pauling scale), valence electron concentration (VEC), and mixing enthalpy estimates using published empirical formulas.
- **Model training**: Train gradient boosting regressor (scikit-learn GradientBoostingRegressor) with 5-fold cross-validation; optimize hyperparameters (n_estimators, max_depth) via grid search over ≤10 combinations to stay within 6-hour runtime.
- **Statistical validation**: Evaluate model performance using R², MAE, and RMSE on held-out test set; conduct permutation importance analysis to rank feature contributions; compute 95% confidence intervals via bootstrapping (1000 resamples).
- **Interpretation**: Generate partial dependence plots for top 3 features to visualize non-linear Tg relationships; compare feature importance rankings across alloy families (Zr-based, Pd-based, Fe-based, etc.).

## Duplicate-check

- Reviewed existing ideas: None in current corpus (initial flesh-out).
- Closest match: None identified.
- Verdict: NOT a duplicate
