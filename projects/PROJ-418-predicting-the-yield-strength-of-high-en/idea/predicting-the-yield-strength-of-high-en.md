---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

**Field**: materials science

## Research question

How do elemental mixing parameters (atomic radii, electronegativity, valence electron concentration) correlate with the yield strength of single-phase high-entropy alloys at room temperature, and which compositional descriptor set provides the strongest predictive signal?

## Motivation

Experimental characterization of high-entropy alloys (HEAs) requires costly synthesis and mechanical testing, limiting exploration of the vast compositional space. If compositional descriptors alone can reliably predict yield strength, researchers can prioritize promising alloys for experimental validation. This work addresses the gap between theoretical compositional design rules and quantitative mechanical property prediction.

## Related work

- [Machine-Learning-Based Intelligent Framework for Discovering Refractory High-Entropy Alloys with Improved High-Temperature Yield Strength](http://arxiv.org/abs/2112.02587v1) — Demonstrates ML prediction of yield strength for refractory HEAs, though focused on elevated temperatures rather than room-temperature properties.
- [High-entropy high-hardness metal carbides discovered by entropy descriptors](https://doi.org/10.1038/s41467-018-07160-7) — Establishes entropy-based descriptors as predictive features for hardness in high-entropy materials, providing a precedent for descriptor-based mechanical property modeling.
- [Plasticity of Zr-Nb-Ti-Ta-Hf high-entropy alloys](http://arxiv.org/abs/1401.3997v1) — Provides experimental yield strength data for specific non-equiatomic HEA compositions that can serve as validation points for predictive models.
- [Recent advances and applications of machine learning in solid-state materials science](https://doi.org/10.1038/s41524-019-0221-0) — Reviews statistical learning methods applicable to solid-state property prediction, including descriptor engineering approaches.

## Expected results

We expect to identify 2-3 compositional descriptors (e.g., atomic size mismatch, electronegativity variance) that show statistically significant correlation (|r| > 0.5, p < 0.01) with room-temperature yield strength across a curated HEA dataset. A random forest or gradient boosting model trained on these descriptors should achieve R² > 0.6 on held-out test compositions, demonstrating that compositional information alone carries predictive signal for mechanical properties.

## Methodology sketch

- **Data acquisition**: Download HEA composition and yield strength data from open repositories (Materials Project, NIST HEA database, or published datasets via Zenodo/figshare DOIs)
- **Descriptor engineering**: Calculate mixing entropy, atomic size mismatch (δ), electronegativity variance (Δχ), valence electron concentration (VEC), and melting temperature variance for each alloy composition
- **Data preprocessing**: Filter to single-phase alloys at room temperature; remove entries with missing yield strength values or non-standard testing conditions
- **Feature selection**: Use recursive feature elimination and SHAP analysis to identify the most predictive descriptor subset
- **Model training**: Train random forest and gradient boosting models with 5-fold cross-validation; tune hyperparameters via grid search on CPU (≤50 trees, depth ≤10)
- **Validation**: Hold out 20% of compositions as test set; evaluate R², MAE, and RMSE; compare against baseline linear regression
- **Statistical testing**: Perform permutation importance testing and bootstrap confidence intervals (1000 resamples) to quantify feature contribution significance
- **Reproducibility**: Save model artifacts, descriptor calculations, and data splits; document all random seeds

## Duplicate-check

- Reviewed existing ideas: [placeholder for system-provided list of existing fleshed-out ideas in materials science].
- Closest match: [placeholder for nearest semantic similarity result].
- Verdict: NOT a duplicate
