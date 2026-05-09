---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Field**: materials science

## Research question

To what extent do thermodynamic mixing parameters (enthalpy, atomic size mismatch) correlate with the critical cooling rate for glass formation in ternary metallic systems?

## Motivation

Metallic glasses exhibit superior strength and elasticity, but their synthesis requires identifying compositions within narrow glass-forming regions. Current design relies on empirical rules that often fail for complex multi-component systems. Establishing a quantitative link between thermodynamic descriptors and critical cooling rates would reduce trial-and-error in alloy discovery and validate theoretical models of glass formation.

## Related work

- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025)](http://arxiv.org/abs/2512.05895v2) — Provides a methodological precedent for classifying GFA in ternary systems, though it emphasizes oxide glasses, offering a transferable framework for metallic alloys.
- [A general-purpose machine learning framework for predicting properties of inorganic materials (2016)](https://doi.org/10.1038/npjcompumats.2016.28) — Establishes the viability of extracting predictive models from existing materials data, supporting the use of public databases for GFA training.
- [MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction (2018)](http://arxiv.org/abs/1811.05660v1) — Demonstrates how crystal structure representations can predict material properties, informing feature engineering choices for alloy descriptors.

## Expected results

A significant positive correlation between specific thermodynamic descriptors (e.g., negative mixing enthalpy) and lower critical cooling rates would validate existing empirical rules. Conversely, a weak correlation would indicate that electronic structure or kinetic factors dominate, necessitating more complex feature sets. Either outcome provides actionable evidence for alloy design strategies.

## Methodology sketch

- Download a subset of ternary alloy entries (N ≈ 1000) from the Open Quantum Materials Database (OQMD) via HTTP.
- Filter for entries with reported glass-forming labels or critical cooling rate values from associated literature metadata.
- Compute thermodynamic features (mixing enthalpy, atomic size difference, electronegativity variance) using elemental properties from the Periodic Table.
- Train a Random Forest classifier/regressor using scikit-learn on a 80/20 train-test split.
- Apply 5-fold cross-validation to estimate generalization performance (RMSE or F1-score).
- Perform permutation importance analysis to identify which thermodynamic parameters most influence the prediction.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None (no corpus provided).
- Verdict: NOT a duplicate
