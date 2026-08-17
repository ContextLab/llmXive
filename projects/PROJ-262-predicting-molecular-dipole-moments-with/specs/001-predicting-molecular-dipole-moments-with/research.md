# Research Documentation: Predicting Molecular Dipole Moments with Graph Neural Networks

## Overview
This project implements a Graph Neural Network (GNN) pipeline to predict molecular dipole moments using the QM9 dataset. The approach leverages 3D molecular geometries and 2D topological descriptors to train a SchNet-style architecture, comparing it against a Random Forest baseline.

## Ground Truth and Reference Data
The sole source of ground truth for this study is the QM9 dataset, specifically the dipole moments calculated via Density Functional Theory (DFT) at the BLYP/6-31G(2df,p) level of theory.

**Important**: All model evaluation and training are strictly based on these quantum mechanical reference values. No experimental physical measurements are used as ground truth in this pipeline.

## Scope Boundaries and Limitations

### Out-of-Scope: Physical Measurement Validation
This project explicitly **excludes** physical measurement validation against experimental data.

- **Stark-effect spectroscopy**, dielectric spectroscopy, and other experimental techniques for measuring dipole moments are **not** performed or utilized in this study.
- While experimental validation is a critical step in broader chemical research (as noted in reviewer feedback regarding physical reality benchmarks), it falls outside the defined scope of this specific computational pipeline (FR-011).
- The project assumes the QM9 DFT values are the authoritative reference for the purpose of training and evaluating the GNN architecture.

### Out-of-Scope: Hydration and Solvation Effects
- The dataset consists of gas-phase molecules.
- Hydration states, solvent effects, and conformational ensembles in solution are **not** modeled.
- The input features are derived from single, static 3D conformers provided in the QM9 dataset.

### Out-of-Scope: Conformational Sampling
- The pipeline uses a single conformer per molecule as provided in the dataset.
- No dynamic conformational sampling or ensemble averaging is performed.

## Methodology
1. **Data Source**: QM9 dataset (DOI: 10.1038/sdata.2014.22).
2. **Preprocessing**: Extraction of 3D coordinates, atom types, and 2D Morgan fingerprints.
3. **Models**:
 - **SchNet-style GNN**: Processes 3D atomic environments.
 - **Random Forest Baseline**: Processes 2D descriptors.
4. **Evaluation**: Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) against DFT dipole moments.

## Reproducibility
- Random seeds are fixed (seed=42) for data splitting and model initialization.
- All dependencies are pinned in `requirements.txt`.
- Execution is constrained by time (6h), memory (8GB), and CPU core limits to ensure feasibility.

## References
1. Ramakrishnan, R., Dral, P. O., Rupp, M., & von Lilienfeld, O. A. (2014). Quantum chemistry structures and properties of 134 kilo molecules. *Scientific Data*, 1, 140022. https://doi.org/10.1038/sdata.2014.22
2. Schütt, K. T., Sauceda, H. E., Arbabzadah, P., Chmiela, S., Müller, K. R., & Tkatchenko, A. (2017). SchNet – A deep learning architecture for molecules and materials. *The Journal of Chemical Physics*, 148(24), 241722.