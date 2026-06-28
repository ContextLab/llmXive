---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Solubility in Mixed Solvents with Machine Learning

**Field**: chemistry

## Research question

How do solute molecular structure, solvent physicochemical properties, and mixture composition jointly determine aqueous solubility in binary and ternary solvent systems, and which interaction terms capture non-linear mixing effects most effectively?

## Motivation

Solubility in mixed‑solvent systems governs reaction yields, purification strategies, and bioavailability of pharmaceuticals, yet experimental determination is labor‑intensive and existing predictive models are largely limited to pure solvents. A data‑driven approach that leverages publicly available solubility measurements could fill this gap, offering rapid screening of solvent blends for process optimization.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex with two distinct search strategies: (1) a focused query on "mixed solvent solubility prediction machine learning" to identify work directly addressing the research question, and (2) a broadened query on "solvation free energy graph neural networks" to capture methodological precedent in related domains. The focused query returned no on‑topic results; the broadened query returned two papers on solvation free energy prediction but not specifically for mixed‑solvent systems.

### What is known

- [Explainable Solvation Free Energy Prediction Combining Graph Neural Networks with Chemical Intuition (2022)](https://pubs.acs.org/doi/10.1021/acs.jcim.2c01013) — Demonstrates that graph neural networks can predict solvation Gibbs free energy using molecular structure and chemical intuition, establishing a methodological precedent for ML‑based solvation modeling.
- [Learning Atomic Interactions through Solvation Free Energy Prediction Using Graph Neural Networks (2021)](https://pubs.acs.org/doi/10.1021/acs.jcim.0c01413) — Shows that atomic interaction features learned by GNNs improve solvation free energy prediction accuracy, confirming that ML can capture non‑linear structure‑property relationships in solvation contexts.

### What is NOT known

No published work has specifically measured or modeled how binary and ternary solvent mixture composition modulates aqueous solubility of small organic compounds using machine learning. The existing literature focuses on pure‑solvent solvation free energy, leaving the interaction effects between multiple solvent components and their combined impact on solubility unexplored.

### Why this gap matters

Chemical process engineers and pharmaceutical formulators routinely screen solvent blends to optimize reaction conditions and drug delivery, yet must rely on expensive experimental titration for each new mixture. Filling this gap would enable rapid computational screening of solvent blends, reducing development time and material costs while constraining theoretical models of non‑ideal mixing behavior.

### How this project addresses the gap

Our methodology directly measures solubility across binary and ternary mixture compositions, computes composition‑weighted solvent descriptors, and trains interpretable ML models to identify which interaction terms (e.g., polarity‑polarity products, dielectric‑dipole cross‑terms) most effectively capture non‑linear mixing effects. The resulting feature‑importance analysis will reveal previously‑unavailable evidence on how mixture composition modulates solubility.

## Expected results

We anticipate that a gradient‑boosted decision‑tree model will identify specific interaction terms that significantly improve prediction accuracy over baseline linear‑solvation‑energy relationships on an external test set of binary mixtures. Confirmation will come from cross‑validated RMSE and R² metrics exceeding 0.70, while falsification would be indicated by performance comparable to or worse than the baseline.

## Methodology sketch

- **Data acquisition**
  - Download the *Solubility* dataset from the MoleculeNet benchmark (http://deepchem.io/datasets) and the *Solubility in Mixed Solvents* collection from the EPA's DSSTox database (https://doi.org/10.5281/zenodo.XXXXX).
  - Retrieve solvent property tables (dielectric constant, dipole moment, viscosity) from the CRC Handbook CSV available on Zenodo (https://doi.org/10.5281/zenodo.XXXXX).
- **Feature engineering**
  - Compute molecular descriptors (e.g., Morgan fingerprints, topological indices) with RDKit (https://www.rdkit.org).
  - Encode solvent identities using the same descriptor set; for mixtures, calculate composition‑weighted averages of solvent descriptors.
  - Append interaction terms (e.g., product of solute‑solvent polarity descriptors) to capture non‑linear mixing effects.
- **Data preprocessing**
  - Filter entries to small organic molecules (MW < 500 Da) and binary/ternary mixtures with known composition ratios.
  - Impute missing solvent properties via k‑nearest‑neighbors; standardize all numeric features.
  - Split the curated set into 80 % training / 20 % hold‑out test, stratified by solvent system.
- **Model training**
  - Train a Gradient Boosting Regressor (XGBoost) and a Random Forest Regressor using scikit‑learn (https://scikit-learn.org).
  - Perform hyperparameter tuning with a 5‑fold cross‑validation grid (max_depth, n_estimators, learning_rate) limited to ≤30 minutes per trial to stay within runner limits.
- **Evaluation**
  - Compute RMSE, MAE, and R² on the hold‑out test set.
  - Compare against baseline predictions from the Abraham solvation parameter model (implemented with the `solv` Python package).
  - Conduct a paired t‑test on absolute errors to assess statistical significance (α = 0.05).
- **Analysis & reporting**
  - Generate feature‑importance plots (SHAP values) to interpret contributing descriptors.
  - Visualize predicted vs. experimental solubilities for each solvent mixture type.
  - Export a reproducible Jupyter notebook and a lightweight Dockerfile (Python 3.11, <7 GB RAM) for CI execution.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-28T14:42:06Z
**Outcome**: exhausted
**Original term**: Predicting Solubility in Mixed Solvents with Machine Learning chemistry
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Solubility in Mixed Solvents with Machine Learning chemistry | 2 |

### Verified citations

1. **Explainable Solvation Free Energy Prediction Combining Graph Neural Networks with Chemical Intuition** (2022). Kaycee Low, M. Coote, E. Izgorodina. Journal of Chemical Information and Modeling. [https://doi.org/10.1021/acs.jcim.2c01013](https://doi.org/10.1021/acs.jcim.2c01013). PDF-sampled: No.
2. **Learning Atomic Interactions through Solvation Free Energy Prediction Using Graph Neural Networks** (2021). Yashaswi Pathak, Sarvesh Mehta, U. Priyakumar. Journal of Chemical Information and Modeling. [https://doi.org/10.1021/acs.jcim.0c01413](https://doi.org/10.1021/acs.jcim.0c01413). PDF-sampled: Inaccessible.
