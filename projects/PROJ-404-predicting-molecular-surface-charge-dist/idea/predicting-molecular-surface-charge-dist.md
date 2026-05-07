---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

**Field**: chemistry

## Research question

How does molecular graph structure relate to the electrostatic potential (ESP) derived surface charge distribution across small organic molecules, and can this relationship be captured without explicit quantum chemical computation?

## Motivation

ESP-derived charge distributions govern intermolecular interactions, solvation, and molecular recognition, but computing them requires expensive DFT calculations. Understanding whether structural features alone can predict these charges would enable rapid estimation for large-scale screening, provided the relationship is learnable from existing quantum chemistry data.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex for queries including "electrostatic potential charge prediction machine learning," "ESP charge distribution graph neural network," and "molecular surface charge quantum chemical ML." Retrieved 8 results from the literature block, spanning quantum computing applications in chemistry, molecular simulation software, and general molecular orbital theory.

### What is known

- [Spin-coupled molecular orbitals: chemical intuition meets quantum chemistry (2024)](http://arxiv.org/abs/2402.08858v1) — Establishes molecular orbital theory as a conceptual framework for understanding chemical bonding and electronic structure.
- [CHARMM: The biomolecular simulation program (2009)](https://doi.org/10.1002/jcc.21287) — Widely used molecular simulation program that can compute electrostatic properties but relies on explicit quantum or force-field calculations.
- [Avogadro: an advanced semantic chemical editor, visualization, and analysis platform (2012)](https://doi.org/10.1186/1758-2946-4-17) — Provides tools for visualizing and analyzing molecular structures but does not address ML-based charge prediction.

### What is NOT known

No published work has systematically evaluated whether graph-based machine learning models can predict ESP-derived surface charge distributions directly from molecular structure without performing quantum chemical calculations. The existing literature focuses on either quantum chemistry methods themselves or molecular simulation tools, not on learning the structure-to-charge mapping as a surrogate model.

### Why this gap matters

Filling this gap would enable rapid charge estimation for large molecular libraries where DFT is computationally prohibitive, accelerating drug discovery and materials screening workflows that depend on accurate electrostatic descriptions.

### How this project addresses the gap

The project will train a graph neural network on public quantum chemistry datasets (e.g., QM9, ANI-1) containing both molecular graphs and pre-computed ESP charges, measuring prediction accuracy against held-out DFT calculations to establish whether structure alone suffices for charge estimation.

## Expected results

A graph neural network trained on ESP charge labels from quantum chemistry datasets will achieve mean absolute error below 0.1 e on atom-centered charges for small organic molecules, demonstrating that structural features contain sufficient information for approximate charge prediction. Null results would indicate that electronic structure details beyond graph connectivity are essential for accurate ESP modeling.

## Methodology sketch

- Download QM9 or ANI-1 dataset from OpenML/Zenodo (contains molecular graphs, atomic coordinates, and DFT-computed ESP charges).
- Preprocess molecular graphs: extract atom types, bond orders, and 3D coordinates; compute atomic ESP charges from existing quantum calculations.
- Construct graph neural network architecture (e.g., Message Passing Neural Network) with atom-wise output layer for charge prediction.
- Split data into train/validation/test sets (80/10/10) ensuring no molecular scaffold leakage between splits.
- Train model on CPU for ≤100 epochs with early stopping based on validation MAE; use Adam optimizer, learning rate 1e-3.
- Evaluate test set MAE, RMSE, and Pearson correlation between predicted and DFT ESP charges.
- Perform ablation: compare GNN predictions against simple atom-type averaging baseline to quantify structural information contribution.
- Visualize charge distribution errors on 3D molecular structures using Avogadro or RDKit for qualitative assessment.
- Document runtime and memory usage to confirm feasibility within GitHub Actions 6-hour, 7GB RAM constraints.

## Duplicate-check

- Reviewed existing ideas: None in the corpus for this field.
- Closest match: None identified (no prior fleshed-out ideas in chemistry domain).
- Verdict: NOT a duplicate
