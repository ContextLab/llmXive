---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Computational Screening of Deep Eutectic Solvent Mixtures for CO2 Capture

**Field**: chemistry

## Research question

Can quantitative structure-property relationship (QSPR) models trained on publicly available DES component data predict CO2 solubility and viscosity for untested DES mixtures, enabling computational prioritization of candidates for experimental validation?

## Motivation

The compositional space of deep eutectic solvents (DESs) is too large for exhaustive experimental screening, making computational pre-screening essential for efficient discovery. This project addresses the gap between available single-component DES property data and the need to predict performance of mixtures for CO2 capture applications. A validated in-silico screening pipeline would reduce experimental costs and accelerate development of sustainable carbon capture solvents.

## Related work

- [Development of Quantitative Structure-Property Relationship to Predict the Viscosity of Deep Eutectic Solvent for CO2 Capture using Molecular Descriptor](https://www.semanticscholar.org/paper/cf44b0ec00b9570d6e02d9f92a0e9062203744b6) — Demonstrates QSPR modeling for DES viscosity prediction, establishing feasibility of computational property estimation for CO2 capture applications.
- [Generative Discovery of Novel Chemical Designs using Diffusion Modeling and Transformer Deep Neural Networks with Application to Deep Eutectic Solvents](http://arxiv.org/abs/2304.12400v1) — Shows deep learning approaches for molecular design, though GPU-intensive methods will be simplified for this project's computational constraints.
- [Modeling the Physicochemical Properties of Natural Deep Eutectic Solvents](https://doi.org/10.1002/cssc.202000286) — Provides baseline property data for natural DES components that can inform QSPR feature selection and validation datasets.
- [Crystallisation From Volatile Deep Eutectic Solvents](http://arxiv.org/abs/1902.08376v3) — Illustrates DES characterization methodologies that inform data quality requirements for computational screening.

## Expected results

The QSPR models should predict CO2 solubility within ±15% of experimental values and viscosity within ±20% for mixtures containing known DES components. Performance will be validated using k-fold cross-validation on held-out experimental data from public repositories. Top-ranked DES formulations will be identified based on a composite score balancing solubility, viscosity, and component availability.

## Methodology sketch

- Download DES property datasets from UCI Machine Learning Repository, HuggingFace Datasets, and Zenodo (target: ≤5000 records total, ~50MB)
- Extract molecular descriptors using RDKit (open-source Python library, CPU-only, <1GB RAM) for all DES components
- Train linear regression and random forest QSPR models for CO2 solubility and viscosity prediction using scikit-learn
- Implement mixing rules based on mole-fraction weighted averaging validated against literature data
- Apply models to screen 500-1000 virtual DES mixtures from component combinatorics
- Perform 5-fold cross-validation to assess model generalization (R² ≥ 0.7 threshold for acceptance)
- Generate ranked candidate list with uncertainty estimates using prediction interval methods
- Produce summary figures (solubility vs. viscosity scatter plot, top-10 candidates table) for reporting

## Duplicate-check

- Reviewed existing ideas: None in current corpus (initial flesh-out).
- Closest match: None identified.
- Verdict: NOT a duplicate
