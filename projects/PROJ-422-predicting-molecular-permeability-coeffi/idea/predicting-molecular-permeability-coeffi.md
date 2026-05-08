---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Field**: Chemistry

## Research question

How does molecular topology influence permeability coefficients across common polymeric separation membranes?

## Motivation

Screening membrane materials for industrial separation currently relies on computationally expensive molecular dynamics simulations or slow experimental measurements. Establishing a data-driven relationship between molecular structure and permeability could enable rapid virtual screening of candidate molecules for specific separation tasks without requiring new wet-lab experiments.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms including "polymeric membrane permeability machine learning," "molecular permeability graph neural network," and "QSPR membrane separation." We reviewed the provided literature block for direct matches on industrial membrane permeability prediction using deep learning.

### What is known

- [Could graph neural networks learn better molecular representation for drug discovery? A comparison study of descriptor-based and graph-based models (2021)](https://doi.org/10.1186/s13321-020-00479-8) — Establishes that GNNs generally outperform traditional descriptor-based models for molecular property prediction tasks.
- [ADMETlab 3.0: an updated comprehensive online ADMET prediction platform enhanced with broader coverage, improved performance, API functionality and decision support (2024)](https://doi.org/10.1093/nar/gkae236) — Demonstrates the viability of automated permeability prediction, though focused on biological absorption rather than polymeric membranes.
- [OPERA models for predicting physicochemical properties and environmental fate endpoints (2018)](https://doi.org/10.1186/s13321-018-0263-1) — Provides validated QSAR baselines for physicochemical properties that can serve as methodological precedents for regression tasks.

### What is NOT known

No published work in the provided search results specifically applies graph neural networks to predict permeability coefficients across *polymeric* membranes for separation applications using publicly available datasets. Existing platforms like ADMETlab focus on biological membranes (e.g., Caco-2), leaving a gap in industrial separation modeling.

### Why this gap matters

Filling this gap would enable chemical engineers to prioritize membrane-material pairings for gas separation or liquid filtration without running full molecular dynamics simulations, significantly reducing development time for sustainable separation technologies.

### How this project addresses the gap

This project will train a graph-based regression model specifically on public polymeric permeability data (e.g., from NIST repositories) to quantify the structure-permeability relationship, directly addressing the lack of deep learning benchmarks in this subdomain.

## Expected results

The GNN model will achieve a lower root-mean-square error (RMSE) on the test set compared to a baseline Random Forest model using standard descriptors. A statistically significant improvement (p < 0.05) will confirm that topological features capture variance in permeability that standard descriptors miss.

## Methodology sketch

- Download public permeability datasets (SMILES + coefficient values) from NIST or Zenodo repositories using `wget`.
- Parse SMILES strings into molecular graphs using RDKit (CPU-only).
- Construct a Message Passing Neural Network (MPNN) using PyTorch Geometric with 2 layers.
- Split data into 80% training / 20% test sets with stratified sampling by polymer type.
- Train the model on CPU for 50 epochs with early stopping based on validation loss.
- Evaluate performance using RMSE and R² metrics on the held-out test set.
- Train a baseline Random Forest regressor using OPERA-style molecular descriptors for comparison.
- Perform a paired t-test on prediction errors between GNN and baseline to assess statistical significance.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: N/A (no existing ideas provided).
- Verdict: NOT a duplicate
