---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks

**Field**: chemistry

## Research question

Which molecular substructures and interaction patterns (electrostatic, hydrophobic, hydrogen bonding) most strongly determine binding affinity in protein-ligand complexes?

## Motivation

Understanding the structural determinants of protein-ligand binding is critical for rational drug design, yet current methods struggle to identify which specific molecular features drive high-affinity binding. This project addresses the gap between black-box affinity prediction and interpretable mechanistic insight, enabling researchers to prioritize drug candidates based on interpretable interaction motifs rather than opaque scores.

## Related work

- [Structure-aware Interactive Graph Neural Networks for the Prediction of Protein-Ligand Binding Affinity (2021)](http://arxiv.org/abs/2107.10670v1) — Directly applies GNNs to protein-ligand binding affinity prediction, establishing baseline performance and interactive graph construction methods.
- [MECCH: Metapath Context Convolution-based Heterogeneous Graph Neural Networks (2022)](http://arxiv.org/abs/2211.12792v2) — Demonstrates heterogeneous GNNs for structural data with multiple node/edge types, relevant for modeling diverse molecular interaction types.
- [From Quantum Chemistry to Networks in Biology: A Graph Spectral Approach to Protein Structure Analyses (2019)](http://arxiv.org/abs/1912.11609v1) — Provides theoretical framework for representing protein structures as networks, supporting graph-based molecular analysis.
- [Graph convolutional networks: a comprehensive review (2019)](https://doi.org/10.1186/s40649-019-0069-y) — Comprehensive GCN methodology review establishing foundational techniques for graph-based molecular representation learning.

## Expected results

We expect to identify 3-5 molecular substructure motifs that consistently correlate with high binding affinity across diverse protein-ligand pairs, with at least one motif showing statistically significant predictive power (p < 0.01) in held-out test data. We will measure this using feature importance scores from trained GNNs and validation against known pharmacophore databases to confirm biological plausibility.

## Methodology sketch

- Download PDBbind v2020 refined set (~5,000 protein-ligand complexes with binding affinity measurements) from http://www.pdbbind.org.cn/ using `wget`
- Construct molecular graphs for each complex using RDKit, encoding atoms as nodes and covalent/non-covalent bonds as edges with feature vectors for atom type, charge, and hydrophobicity
- Train a message-passing GNN (3 layers, 128 hidden units) to predict binding affinity (pKd) using mean-squared error loss, with 80/10/10 train/validation/test split
- Apply gradient-based attribution (Integrated Gradients) to extract feature importance scores for each atom and interaction type in high-affinity vs low-affinity predictions
- Cluster high-importance substructures using DBSCAN and cross-reference against known pharmacophores in the ChEMBL database (https://www.ebi.ac.uk/chembl/) to validate biological relevance
- Perform statistical significance testing (two-sample t-test) comparing feature importance distributions between high-affinity (pKd > 8) and low-affinity (pKd < 6) complexes

## Duplicate-check

- Reviewed existing ideas: N/A (no existing fleshed-out ideas provided in field)
- Closest match: None identified
- Verdict: NOT a duplicate
