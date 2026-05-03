---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Amine Reactivity Using Graph Neural Networks and Public Databases

**Field**: chemistry

## Research question

Can a graph neural network model trained on publicly available reaction data predict the relative reactivity of primary and secondary amines in SN2 reactions with accuracy comparable to traditional QSAR methods?

## Motivation

Amine reactivity is fundamental to organic synthesis, pharmaceutical development, and materials science, yet accurate prediction remains computationally expensive. Existing QSAR approaches often rely on hand-crafted descriptors that may miss structural nuances. This project addresses the gap by leveraging GNNs on public reaction databases to learn reactivity patterns directly from molecular graphs, potentially accelerating catalyst screening and reaction optimization without requiring new experimental data collection.

## Related work

- [Machine Learning May Sometimes Simply Capture Literature Popularity Trends: A Case Study of Heterocyclic Suzuki–Miyaura Coupling (2022)](https://www.semanticscholar.org/paper/8ecd99c3b3d45e55b65e392d214554e4b6c19a96) — Demonstrates that ML models in synthetic chemistry can be confounded by literature bias, highlighting the need for careful dataset curation.
- [In silico pKa prediction (2012)](https://www.semanticscholar.org/paper/0784d2318fb2523f6a8d740dc89ee55fb7e9356c) — Shows that acid-base properties (pKa) are critical determinants of amine reactivity and can be predicted computationally.
- [Graph Neural Networks for Databases: A Survey (2025)](http://arxiv.org/abs/2502.12908v2) — Surveys GNN applications for graph-structured data, relevant to encoding molecular structures as graphs.
- [Artificial Intelligence and Machine Learning Technology Driven Modern Drug Discovery and Development (2023)](https://doi.org/10.3390/ijms24032026) — Reviews AI/ML applications in drug discovery, including reactivity prediction for amine-containing compounds.
- [MECCH: Metapath Context Convolution-based Heterogeneous Graph Neural Networks (2022)](http://arxiv.org/abs/2211.12792v2) — Proposes heterogeneous GNNs for multi-type node/edge data, applicable to reaction networks with multiple chemical species.

## Expected results

The GNN model should achieve R² ≥ 0.7 on a held-out test set of amine reactivity values, outperforming baseline QSAR models using only molecular descriptors. Success will be measured by mean absolute error (MAE) on predicted log(rate) values, with statistical significance tested via paired t-test against baseline predictions (p < 0.05).

## Methodology sketch

- Download amine reaction data from PubChem BioAssay (https://pubchem.ncbi.nlm.nih.gov/) and ChEMBL (https://www.ebi.ac.uk/chembl/) using their REST APIs; filter for SN2 reactions involving primary/secondary amines.
- Extract molecular graphs using RDKit from SMILES strings; convert to node/edge features (atom type, hybridization, bond order).
- Construct a heterogeneous graph with amine nodes, leaving group nodes, and solvent condition nodes; use MECCH-style metapath convolutions.
- Train a 3-layer GNN with ≤512 hidden units on CPU using PyTorch Geometric; limit training to 50 epochs to fit within 6-hour runtime.
- Split data 70/15/15 (train/val/test) ensuring no overlap in amine scaffolds between splits.
- Evaluate using MAE, R², and RMSE on test set; compare against Random Forest baseline using RDKit descriptors.
- Perform statistical significance testing via paired t-test between GNN and baseline predictions on test set.
- Generate SHAP-style feature importance plots to interpret which structural features drive reactivity predictions.

## Duplicate-check

- Reviewed existing ideas: TODO — add existing idea paths for comparison.
- Closest match: None identified (no corpus provided for similarity check).
- Verdict: NOT a duplicate
