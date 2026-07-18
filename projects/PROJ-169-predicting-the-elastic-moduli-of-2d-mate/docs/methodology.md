# Methodology: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## Overview

This project implements a **Structure-Only Surrogate Model** designed to predict the elastic moduli of two-dimensional (2D) materials. The model utilizes Graph Neural Networks (GNNs) to learn statistical mappings between material crystal structures and their pre-computed elastic properties.

## Data Sources

The training data for this surrogate model consists of crystal structures and corresponding elastic tensors derived from Density Functional Theory (DFT) calculations found in public repositories, specifically:
- **Materials Project**: A comprehensive database of computed materials properties.
- **AFLOW**: The Automatic-Fast Library for Approximate Materials Design.

All data used in this pipeline is fetched from these existing, pre-computed sources. No new DFT calculations are performed within this project.

## Model Architecture

The core of the system is a lightweight GNN architecture (`LightweightGNN`) implemented using `torch_geometric`. The model operates on `MaterialGraph` objects, where:
- **Nodes** represent atoms, encoded with composition-based features (e.g., atomic number, electronegativity).
- **Edges** represent chemical bonds or spatial proximity, encoded with distance-based features.
- **Targets** are the Young's Modulus, Shear Modulus, and Poisson's Ratio derived from the elastic tensor.

The model is trained via supervised learning to minimize the error between predicted and DFT-derived moduli. It functions as a non-linear regressor, interpolating within the manifold of the training data.

## What This Is Not

It is critical to distinguish the methodology of this project from "First-Principles" calculations.

**This project does NOT solve the Schrödinger equation.**
**This project does NOT calculate electron density from the Hamiltonian.**
**This project does NOT perform ab initio physics simulations.**

Instead, this system is a **statistical interpolator** trained on pre-computed DFT data. It learns the correlation between structural descriptors and elastic properties as encoded in the training set. While the underlying data originates from first-principles calculations (DFT), the model itself is a machine learning surrogate. It cannot predict properties for materials significantly outside the distribution of its training data (extrapolation failure) and does not discover new physical laws or fundamental quantum mechanical variables.

The term "First-Principles" is reserved for methods that explicitly solve the many-body quantum mechanical equations (e.g., DFT, Hartree-Fock). In contrast, this project implements a **curve-fitting** approach that approximates the results of such calculations with significantly lower computational cost.

## Reproducibility and Bias Control

To ensure reproducibility (Constitution Principle I), all random seeds for `torch`, `numpy`, and `random` are pinned globally via `code/utils/config.py`. Data loading enforces a single canonical source per run to prevent mixing incompatible datasets. Bias checks are performed on excluded entries to ensure no systematic filtering of specific material families skews the training distribution.

## Limitations

- **Extrapolation**: The model is not reliable for predicting properties of materials with chemical or structural compositions absent from the training data.
- **Physics Discovery**: The model identifies statistical correlations, not causal physical mechanisms. It cannot be used to derive fundamental equations of state.
- **Data Dependency**: The accuracy of the surrogate is strictly bounded by the accuracy and coverage of the source DFT datasets.