---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Elastic Anisotropy of FCC Metals from Composition

**Field**: materials science

## Research question

How does elemental composition influence the elastic anisotropy factor (A₁) in face-centered cubic (FCC) metals and alloys, and can compositional descriptors predict this mechanical property across different alloy systems?

## Motivation

Elastic anisotropy governs plastic deformation behavior and texture evolution in FCC metals, which are critical for structural applications in aerospace and automotive industries. Experimental determination of anisotropy requires single-crystal measurements of elastic constants, which are time-consuming and costly. Establishing a composition-to-anisotropy relationship would enable rapid screening of alloy compositions during materials design without requiring full experimental characterization.

## Literature gap analysis

### What we searched

Search queries included "elastic anisotropy FCC metals composition prediction" and "machine learning elastic constants metallic alloys" across Semantic Scholar and arXiv. The search returned limited direct matches: one review on elastic anisotropy in heterogeneous materials (2022) and sparse results on composition-property relationships in metallic systems. No papers directly addressed ML-based prediction of FCC elastic anisotropy from elemental composition alone.

### What is known

- [Elastic anisotropy in heterogeneous materials (2022)](http://arxiv.org/abs/2212.13503v4) — Establishes that anisotropy depends on phase properties and microstructural configuration, though focused on composite/heterogeneous systems rather than single-phase FCC metals.

### What is NOT known

No published work has systematically quantified the relationship between elemental composition descriptors (e.g., atomic radius, electronegativity, valence electron concentration) and elastic anisotropy in single-phase FCC metals. Existing ML-for-materials studies focus on bulk properties (formation energy, band gap) rather than anisotropic elastic constants, and no benchmark exists for validating composition-to-anisotropy predictions.

### Why this gap matters

Filling this gap would enable early-stage materials screening for alloys requiring specific deformation characteristics, reducing experimental cycles in alloy development. A validated composition-anisotropy model could guide targeted synthesis toward compositions with desired mechanical anisotropy for applications like turbine blades or automotive structural components.

### How this project addresses the gap

The methodology extracts compositional descriptors from public elastic constant databases (Materials Project, AFLOW) and trains regression models to predict anisotropy factor A₁. Cross-validation against held-out compositions and comparison to physical bounds on A₁ will establish whether compositional features contain sufficient information to predict anisotropy, directly testing the unknown relationship identified above.

## Expected results

We expect to find that compositional descriptors (atomic size mismatch, electronegativity variance, valence electron concentration) explain at least 50% of the variance in A₁ across FCC metals. A null result (R² < 0.2) would indicate that microstructure or processing history dominates anisotropy, not composition alone. Either outcome provides publishable insight into the determinants of elastic anisotropy.

## Methodology sketch

- Download elastic constants (C₁₁, C₁₂, C₄₄) for FCC metals from Materials Project (mp.org) and AFLOWlib (aflowlib.org) via their public APIs using `requests` or `wget`.
- Filter dataset to single-phase FCC entries with complete elastic tensor data (approximately 50-100 entries expected).
- Compute anisotropy factor A₁ = 2C₄₄/(C₁₁−C₁₂) for each entry.
- Generate compositional descriptors: atomic radius variance, electronegativity standard deviation, valence electron concentration, and mixing enthalpy using elemental properties from the Periodic Table.
- Split data into 80/20 train/test stratified by element type to avoid data leakage.
- Train three regression models: Random Forest (scikit-learn), Gradient Boosting (XGBoost), and simple linear regression as baseline.
- Perform 5-fold cross-validation on training set; report R², MAE, and RMSE on test set.
- Apply permutation importance to identify which compositional descriptors most influence predictions.
- Visualize predicted vs. actual A₁ with 95% confidence intervals using matplotlib.
- Test physical consistency: verify all predictions fall within theoretical bounds (0 < A₁ < 3 for FCC).

## Duplicate-check

- Reviewed existing ideas: [None provided in input; verification pending project corpus access].
- Closest match: [Unable to compute similarity without existing_idea_paths].
- Verdict: NOT a duplicate (pending corpus check)
