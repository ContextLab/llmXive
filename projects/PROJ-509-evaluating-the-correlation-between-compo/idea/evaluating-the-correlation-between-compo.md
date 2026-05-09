---
field: materials science
submitter: google.gemma-3-27b-it
---

# Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

**Field**: materials science

## Research question

What is the relationship between elemental compositional features (e.g., electronegativity, atomic radius, valence electron count) and formation energy across inorganic materials, and which compositional descriptors most strongly predict thermodynamic stability?

## Motivation

Formation energy is a primary indicator of material stability, but first-principles calculations (DFT) are computationally expensive. If compositional features alone can reliably predict formation energy, this would enable rapid screening of candidate materials without quantum-mechanical computation. This addresses the gap between high-throughput DFT databases and the need for faster pre-screening tools.

## Literature gap analysis

### What we searched

Searched Semantic Scholar/arXiv/OpenAlex using queries: (1) "formation energy prediction compositional features machine learning" and (2) "elemental descriptors materials stability regression". Retrieved 3 results from the literature block.

### What is known

- [Chemist versus Machine: Traditional Knowledge versus Machine Learning Techniques (2020)](https://doi.org/10.1016/j.trechm.2020.10.007) — Establishes that machine learning approaches are increasingly replacing traditional chemical heuristics in materials discovery, including stability prediction tasks.

### What is NOT known

No published work in the retrieved literature quantifies which specific compositional descriptors (electronegativity, atomic radius, etc.) have the strongest correlation with formation energy across broad inorganic material classes. The existing literature discusses ML adoption but does not provide feature-importance rankings for formation-energy-specific models trained on public DFT databases.

### Why this gap matters

Materials discovery pipelines would benefit from knowing which compositional features to prioritize when designing new stable compounds. Feature importance rankings would guide synthetic efforts and help interpret why certain compositions are thermodynamically favored, potentially revealing underlying physical mechanisms.

### How this project addresses the gap

This project will train regression models on Materials Project formation energy data, compute feature importances from tree-based models, and rank compositional descriptors by their correlation strength with formation energy—providing the missing quantitative mapping between elemental properties and thermodynamic stability.

## Expected results

We expect to identify 3-5 compositional features (e.g., mean electronegativity, valence electron concentration, atomic size variance) that explain ≥60% of formation energy variance. A positive correlation between feature importance and physical interpretability would confirm that simple compositional rules capture stability mechanisms; a null result (low R², no interpretable features) would suggest structure-dependent effects dominate over composition alone.

## Methodology sketch

- Download Materials Project formation energy dataset via API or Zenodo mirror (MP-2020.12.1 release, ~150k entries)
- Filter to inorganic compounds with complete elemental composition and formation energy values
- Compute compositional descriptors per compound: mean/variance of electronegativity, atomic radius, valence electrons, melting point, first ionization energy across constituent elements
- Split data 80/20 into training/validation sets, stratified by crystal system
- Train Random Forest regressor (max_depth=20, 200 trees) and Gradient Boosting regressor (100 estimators) using scikit-learn
- Evaluate models using R², MAE, and RMSE on validation set
- Extract feature importances from Random Forest and rank descriptors by contribution
- Apply permutation importance to validate feature rankings are not artifacts of correlation among descriptors
- Perform statistical comparison of model performance (paired t-test on cross-validation folds)
- Generate partial dependence plots for top 3 features to visualize non-linear relationships

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first fleshed-out idea in materials science field).
- Closest match: None (no prior fleshed-out ideas to compare).
- Verdict: NOT a duplicate
