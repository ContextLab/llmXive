# Project Plan: Predicting Molecular Properties from Open Babel Fingerprints

## Overview
This project investigates the ability of Random Forest models trained on Open Babel fingerprints to predict molecular properties (logP, solubility, boiling point) compared to baseline additive fragment models (Crippen's).

## Goals
1. Establish a baseline error using Crippen's additive fragment model.
2. Train Random Forest models using Open Babel fingerprints.
3. Quantify the improvement of the non-linear model over the baseline.
4. Identify specific structural substructures (via SHAP) that contribute to prediction errors.

## Constraints
- Runtime: Max 6 hours on CPU-only runner.
- Memory: Max 7GB RAM, 14GB disk.
- Data: Real experimental data only (no synthetic).
- Tooling: Open Babel CLI for fingerprints, RDKit for parsing.

## Execution Strategy
1. **Phase 1 (Setup)**: Initialize directory structure and dependencies.
2. **Phase 2 (Foundational)**: Implement data download, preprocessing, and diversity filtering.
3. **Phase 3 (US1)**: Baseline error quantification.
4. **Phase 4 (US2)**: Non-linear model training and validation.
5. **Phase 5 (US3)**: Interaction zone mapping and explainability.
6. **Phase 6 (Review)**: Address specific reviewer concerns on data integrity and conformational limitations.

## Risk Management
- **Data Availability**: Use verified HuggingFace datasets (ChEMBL, MoleculeNet) to ensure real data.
- **Runtime**: Implement MaxMin sampling to reduce dataset size while maintaining diversity.
- **Conformational Bias**: Acknowledge 2D fingerprint limitations in the final report.
