---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Conductivity from Graph-Based Features

**Field**: chemistry

## Research question

To what extent does molecular graph topology predict electrical conductivity in organic molecules, and which topological features most strongly correlate with conductive behavior?

## Motivation

Organic electronics require rapid screening of molecular candidates, yet traditional density functional theory (DFT) and experimental synthesis are slow and resource-intensive. Understanding the structural determinants of conductivity would enable computational pre-screening before costly synthesis. This work addresses whether graph-based molecular descriptors capture sufficient information to explain conductivity variance across known organic molecules.

## Literature gap analysis

### What we searched

Searched Semantic Scholar and arXiv using queries: "molecular conductivity prediction graph neural network", "organic molecule electrical conductivity machine learning", and "graph-based molecular property prediction". Two results returned from arXiv, with limited direct coverage of conductivity-specific prediction tasks.

### What is known

- [Dynamic Molecular Graph-based Implementation for Biophysical Properties Prediction (2022)](http://arxiv.org/abs/2212.09991v1) — Establishes that graph neural networks can predict molecular biophysical properties, providing methodological precedent for graph-based molecular property prediction, though focused on biophysical rather than electronic properties.
- [Aromatics and Cyclic Molecules in Molecular Clouds: A New Dimension of Interstellar Organic Chemistry (2021)](http://arxiv.org/abs/2103.09608v1) — Documents aromatic and cyclic molecular structures in organic chemistry contexts, establishing structural classification frameworks but not conductivity relationships.

### What is NOT known

No published work has systematically evaluated whether simple graph-based molecular descriptors (degree distribution, path lengths, ring counts) can predict electrical conductivity in organic molecules. The specific relationship between topological features and conductive behavior remains unquantified, and no benchmark dataset exists for this prediction task.

### Why this gap matters

Organic semiconductor discovery would benefit from rapid computational screening that avoids expensive DFT calculations. If graph topology correlates with conductivity, this could enable pre-filtering of molecular candidates before synthesis, reducing experimental costs and accelerating materials discovery pipelines.

### How this project addresses the gap

The methodology will construct graph-based molecular descriptors from publicly available molecular structure data, train regression models to predict conductivity, and quantify which topological features most strongly correlate with conductive behavior. This directly measures the previously unquantified structure-conductivity relationship.

## Expected results

We expect to identify a subset of graph-based features (e.g., conjugation path length, aromatic ring count) that show moderate correlation (R² > 0.3) with experimental conductivity values. If no significant correlation is found, this would indicate that electronic properties require quantum mechanical descriptors beyond topological information. Either outcome provides publishable insight into structure-property relationships in organic conductors.

## Methodology sketch

- Download molecular structure data (SMILES format) and conductivity measurements from Materials Project (https://materialsproject.org) or PubChem (https://pubchem.ncbi.nlm.nih.gov)
- Parse SMILES strings to molecular graphs using RDKit (lightweight Python library)
- Compute graph-based descriptors: degree distribution, average path length, ring counts, conjugation length, aromaticity indices
- Split dataset into 80/20 train/test split with molecular scaffold splitting to avoid data leakage
- Train Random Forest and Gradient Boosting regressors (scikit-learn) to predict log-transformed conductivity values
- Evaluate performance using R², mean absolute error, and cross-validation on test set
- Perform feature importance analysis to identify topological features most predictive of conductivity
- Generate correlation plots between key descriptors and conductivity with 95% confidence intervals

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first flesh-out for this field).
- Closest match: None identified.
- Verdict: NOT a duplicate
