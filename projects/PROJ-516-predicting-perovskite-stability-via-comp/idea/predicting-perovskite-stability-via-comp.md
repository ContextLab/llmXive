---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Perovskite Stability via Compositional Fingerprints

**Field**: materials science

## Research question

How does elemental composition determine the thermal decomposition temperature of metal halide perovskites, and can compositional descriptors alone predict stability across diverse perovskite families?

## Motivation

Perovskite solar cells face a critical barrier: compositional tuning for long-term stability requires costly experimental validation. A predictive model linking composition to stability would accelerate materials discovery and reduce reliance on trial-and-error synthesis. This work addresses the gap between high-throughput computational screening and experimental verification.

## Related work

- [Analogical discovery of disordered perovskite oxides by crystal structure information hidden in unsupervised material fingerprints](http://arxiv.org/abs/2105.11877v1) — Demonstrates that unsupervised material fingerprints can capture compositional disorder patterns in perovskites, establishing a precedent for fingerprint-based discovery.
- [Efficient and Accurate Prediction of Double Perovskite Quasiparticle Band Gaps via Machine Learning and a Descriptor](https://www.semanticscholar.org/paper/b75a5a9cb4dc2518b49b29b8196d7b90a882858f) — Shows ML-based descriptor prediction is feasible for perovskite properties, though focused on band gaps rather than stability.
- [Data-Driven Optimization and Mechanical Assessment of Perovskite Solar Cells via Stacking Ensemble and SHAP Interpretability](https://www.semanticscholar.org/paper/e72e104c3d9fa2d8991a998a715d28569fca7127) — Applies ensemble ML with interpretability to perovskite solar cell optimization, validating the methodology for PSC-related prediction tasks.
- [Boosting Efficiency and Stability of Planar Inverted (FAPbI3)x(MAPbBr3)1−x Solar Cells via FAPbI3 and MAPbBr3 Crystal Powders](https://www.semanticscholar.org/paper/a1576dc2031290feffcc977f6842689a302158cb) — Provides experimental stability data for mixed-cation perovskite compositions, offering ground-truth measurements for model validation.

## Expected results

A regression model achieving R² ≥ 0.6 on held-out perovskite compositions will indicate compositional fingerprints carry predictive signal for thermal stability. Feature importance analysis (e.g., SHAP values) should reveal which elemental properties (ionic radii, electronegativity, formation enthalpy) most strongly correlate with decomposition temperature. A null result (R² < 0.3) would suggest stability depends on factors beyond composition alone (e.g., microstructure, defects).

## Methodology sketch

- **Data acquisition**: Download perovskite composition and thermal stability datasets from Materials Project (https://materialsproject.org) and NREL's perovskite database; filter for entries with experimentally measured decomposition temperatures.
- **Feature engineering**: Compute compositional descriptors for each perovskite formula: atomic fractions, weighted averages of elemental properties (ionic radius, electronegativity, first ionization energy, formation enthalpy), and variance metrics across A/B/X site elements.
- **Train/test split**: Stratify by perovskite family (e.g., lead-halide, tin-halide, double perovskites) to ensure independent test sets; reserve 20% for final evaluation.
- **Model selection**: Implement three baseline regressors (Random Forest, Gradient Boosting, Elastic Net) using scikit-learn; limit grid search to ≤10 hyperparameter combinations per model to stay within 6h runtime.
- **Cross-validation**: Perform 5-fold cross-validation on training data; track RMSE, R², and MAE as primary metrics.
- **Feature importance**: Extract SHAP values from best-performing model to identify which compositional descriptors drive stability predictions.
- **External validation**: Test on held-out experimental data from the literature (e.g., FAPbI3-MAPbBr3 mixed systems) to assess generalizability beyond training distribution.
- **Statistical test**: Apply permutation importance testing (1000 permutations) to confirm feature contributions exceed random baseline at p < 0.05.

## Duplicate-check

- Reviewed existing ideas: None in current corpus (this is a new brainstormed idea).
- Closest match: N/A (no prior fleshed-out ideas in materials science perovskite stability domain).
- Verdict: NOT a duplicate
