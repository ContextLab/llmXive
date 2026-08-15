# Research Documentation: Predicting Molecular Dipole Moments with Graph Neural Networks

## Overview
This project implements a Graph Neural Network (GNN) pipeline to predict molecular dipole moments using the QM9 dataset. The model architecture leverages a SchNet-style approach to process 3D molecular geometries, complemented by a Random Forest baseline using 2D descriptors.

## Methodology
The core methodology involves extracting 3D coordinates and atom types from the QM9 dataset to construct molecular graphs. A SchNet-style GNN is trained to regress the dipole moment vector magnitude. A Random Forest baseline is trained on Morgan fingerprints and Coulomb matrices for comparison.

## Results
The model achieves competitive Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) scores on the held-out test set. Statistical significance testing (paired t-tests) confirms the performance delta between the GNN and baseline. Feature attribution analysis highlights the contribution of electronegative atom placement and local bond angles to the predicted dipole moments.

## Limitations and Scope Boundaries
This study is strictly computational and operates under specific scope boundaries defined by the project specification and data availability:

1. **Reference Data Ground Truth**: The sole ground truth for training and evaluation is Quantum Mechanical (QM) Density Functional Theory (DFT) data calculated at the BLYP/6-31G(2df,p) level of theory.
2. **Out-of-Scope: Physical Measurement Validation**: Experimental validation via physical measurement techniques (e.g., Stark-effect spectroscopy, dielectric spectroscopy, or microwave spectroscopy) is explicitly **out-of-scope**. While such measurements are the gold standard for experimental verification, this project does not perform or incorporate experimental dipole moment data. The validity of the model is assessed solely against the provided DFT reference values.
3. **Out-of-Scope: Conformational Ensembles**: The dataset provides a single, static 3D geometry per molecule (typically the lowest energy conformer identified in the QM9 generation process). This project does not sample, generate, or average over conformational ensembles. The model predicts the dipole moment for the specific static geometry provided.
4. **Out-of-Scope: Hydration State Sampling**: All calculations and predictions assume gas-phase conditions. The effects of solvent interactions, hydration shells, or explicit water molecules are **out-of-scope**. The dipole moments are derived from isolated molecules in a vacuum as per the QM9 dataset generation protocol.

## Data Sources
- **Primary Dataset**: QM9 (133,885 small organic molecules).
- **DOI**: 10.1038/sdata.2014.22 (Verified via reference-validator).
- **Reference Level**: BLYP/6-31G(2df,p).

## Reproducibility
All experiments use fixed random seeds (seed=42 for data splitting, varying seeds for model training to estimate variance). Code, configuration, and state tracking are maintained to ensure full reproducibility of the reported metrics.

## Future Work
Future iterations could address the scope boundaries identified above by incorporating experimental benchmark sets (e.g., from the NIST Computational Chemistry Comparison and Benchmark Database) to validate against physical reality, or by integrating conformer generation tools to account for thermal fluctuations in dipole moments.