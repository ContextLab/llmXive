---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Reactivity Using Machine Learning and Public Reaction Databases

**Field**: chemistry

## Research question

How do structural features encoded in molecular SMILES representations predict relative reactivity patterns across SN1, SN2, and Diels-Alder organic reactions in publicly available reaction databases?

## Motivation

Organic synthesis planning requires accurate prediction of how molecular structure influences reaction outcomes. Existing retrosynthesis tools struggle to generalize across reaction classes because they lack systematic quantitative models of structure-reactivity relationships. Establishing whether graph-based molecular representations can capture these relationships would inform both computational chemistry workflows and fundamental understanding of reactivity determinants.

## Related work

- [Prediction of Organic Reaction Outcomes Using Machine Learning (2017)](https://doi.org/10.1021/acscentsci.7b00064) — Establishes that ML models can predict reaction outcomes from molecular inputs, providing methodological precedent for structure-reactivity modeling.
- [Machine learning for molecular and materials science (2018)](https://doi.org/10.1038/s41586-018-0337-2) — Reviews ML approaches for molecular property prediction, including graph representations relevant to reactivity modeling.
- [Recent advances and applications of deep learning methods in materials science (2022)](https://doi.org/10.1038/s41524-022-00734-6) — Documents deep learning applications in materials chemistry, though focused on atomistic properties rather than reaction outcomes.

## Expected results

The project will produce a quantitative ranking of how well different molecular representations (SMILES-based vs. graph-based) predict relative reactivity within each reaction class. A positive result would show statistically significant correlation between predicted and observed reactivity rankings (Spearman ρ > 0.5, p < 0.01); a null result would indicate that current public reaction databases lack sufficient signal for this prediction task. Either outcome provides actionable information for computational chemistry pipeline design.

## Methodology sketch

- Download USPTO reaction dataset subset (100k reactions, ~5GB) from public repository (e.g., GitHub: rsc-ai/USPTO)
- Filter reactions to SN1, SN2, and Diels-Alder classes using reaction template matching
- Convert molecular reactants to SMILES and molecular graphs (RDKit)
- Extract structural features: molecular weight, atom counts, bond types, topological indices
- Train lightweight gradient-boosting model (XGBoost) on CPU with 30-minute training budget
- Evaluate using 5-fold cross-validation with reactivity ranking as target
- Compute Spearman correlation and permutation test significance
- Compare performance across reaction classes to identify which mechanisms are most predictable

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: N/A
- Verdict: NOT a duplicate
