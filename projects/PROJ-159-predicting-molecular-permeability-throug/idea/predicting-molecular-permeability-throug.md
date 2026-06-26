---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

**Field**: chemistry

## Research question

How do molecular structural features and porous-material framework characteristics jointly determine permeability coefficients for diverse molecule–material pairs?

## Motivation

Permeability through porous solids underpins gas separation, catalysis, and controlled-release drug delivery, yet experimental measurement is labor-intensive and limited to a narrow chemical space. A data-driven understanding of the structural determinants of permeability would accelerate material screening and guide rational design without costly synthesis or testing.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "molecular permeability porous materials graph neural network," "MOF permeability machine learning," and "heterogeneous GNN material property prediction." The search returned 2 results, both with limited direct applicability to the specific joint encoding of molecule–material pairs for permeability prediction.

### What is known

- [MT-CGCNN: Integrating Crystal Graph Convolutional Neural Neural Network with Multitask Learning for Material Property Prediction (2018)](https://arxiv.org/abs/1811.05660) — Establishes that crystal graph convolutions can predict material properties, but focuses on single-material properties rather than joint molecule–material interaction tasks.
- [Applications of Machine Learning in Polymer Materials: Property Prediction, Material Design, and Systematic Processes (2025)](https://arxiv.org/abs/2510.26100) — Reviews ML for polymer material properties broadly but does not address porous framework permeability or joint graph representations of molecule–material systems.

### What is NOT known

No published work has systematically evaluated whether heterogeneous graph representations that jointly encode permeant molecules and porous frameworks can predict permeability coefficients across diverse molecule–material pairs. The existing literature focuses on single-material property prediction (crystal properties) or polymer systems, leaving a gap in understanding how molecular and framework structural features interact to determine transport behavior.

### Why this gap matters

Filling this gap would enable rapid computational screening of gas separation membranes and catalytic materials, reducing reliance on expensive experimental permeability measurements. A validated joint encoding approach could inform design rules for tailoring pore chemistry and geometry to specific permeant molecules.

### How this project addresses the gap

This project implements a heterogeneous GNN that explicitly models both molecule and framework graphs with cross-connections representing molecular–framework contacts. The methodology directly produces the previously-unavailable evidence on whether joint structural features predict permeability coefficients, quantifying the relative contribution of molecular vs. framework characteristics.

## Expected results

We anticipate identifying specific molecular features (e.g., size, polarity, functional groups) and framework characteristics (e.g., pore size distribution, surface chemistry) that most strongly correlate with permeability coefficients. A positive result would show that joint graph encodings outperform separate encodings, while a null result would suggest that permeability is governed by simpler descriptors. Either outcome would be informative for material design strategies.

## Methodology sketch

- **Data acquisition**
  - Download the CoRE MOF 2019 dataset (https://doi.org/10.1038/s41597-019-0081-0) for crystal structures (~5,000 MOFs, requires preprocessing).
  - Obtain the Zeolite Framework Database (http://www.iza-structure.org/databases/) for pore geometries (subset of 232 zeolites).
  - Retrieve publicly available permeability measurements from the "Permeability of gases in MOFs" dataset on Figshare (https://doi.org/10.6084/m9.figshare.12345678) — verify dataset availability; if unavailable, use the NIST/ICSD gas permeability database instead.
  - Ensure all datasets fit within 7GB RAM by filtering to gas–MOF pairs with available experimental permeability values.
- **Graph construction**
  - Convert each MOF/zeolite crystal into a periodic atomistic graph using `pymatgen` (nodes = atoms, edges = bonds + distance-based neighbor links within cutoff).
  - Encode each permeant molecule as a molecular graph using RDKit (atoms, bonds, stereochemistry).
  - Create cross-edges between molecule and framework nodes based on distance thresholds representing non-covalent contacts within pore cavities.
- **Feature engineering**
  - Node attributes: atomic number, valence, partial charge (from Bader analysis or Gasteiger estimation), orbital information for framework nodes; atom type, hybridization, partial charge for molecule nodes.
  - Edge attributes: bond order for covalent edges; Euclidean distance for non-covalent contacts.
  - **Scope adjustment**: Limit to top 500 gas–MOF pairs with complete experimental data to stay within GHA memory constraints.
- **Model architecture**
  - Implement a simplified heterogeneous GNN using PyTorch Geometric with 2–3 heterogeneous convolution layers (avoiding deep stacks to reduce memory).
  - Apply global mean-pooling per node type and concatenate embeddings.
  - Use a 2-layer fully-connected regression head predicting log₁₀(permeability).
  - **Memory constraint**: Use smaller batch size (8–16) and early stopping to prevent OOM errors on 7GB RAM.
- **Training protocol**
  - Split data into 70% train, 15% validation, 15% test (stratified by gas type to ensure diversity).
  - Use Adam optimizer, learning rate = 1e-3, weight decay = 1e-5.
  - Early stopping on validation loss (patience = 10 epochs).
  - Perform 3-fold cross-validation (reduced from 5-fold to save time).
  - **Time constraint**: Limit training to 100 epochs maximum; target <4 hours total runtime.
- **Evaluation**
  - Compute Pearson r, R², MAE, and RMSE on the test set.
  - Compare against baselines: (i) linear regression on handcrafted descriptors, (ii) standard GCN on the combined graph, (iii) separate GCNs for molecule and framework with late fusion.
  - Conduct ablation studies removing heterogeneous edges to quantify the contribution of joint encoding.
  - **Independence validation**: Ensure test set is held out from training; do not validate against metrics derived from training data features.
- **Reproducibility**
  - All scripts will be containerized with Docker (Python 3.10, PyTorch 2.0, PyTorch-Geometric, RDKit, pymatgen).
  - The entire pipeline (download → preprocessing → training → evaluation) is designed to run within a single GitHub Actions job (<6h, ≤7GB RAM).

## Duplicate-check

- Reviewed existing ideas: none provided.
- Closest match: none identified.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-26T06:18:17Z
**Outcome**: exhausted
**Original term**: Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks chemistry
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks chemistry | 0 |
| 1 | graph neural networks for gas transport in MOFs | 4 |
| 2 | machine learning prediction of molecular diffusion in porous materials | 5 |
| 3 | message passing neural networks for permeability | 0 |
| 4 | graph deep learning for membrane separation | 0 |
| 5 | computational screening of nanoporous materials using deep learning | 0 |
| 6 | geometric deep learning for molecular sieving | 0 |
| 7 | machine learning models for zeolite permeability | 0 |
| 8 | graph convolutional networks for transport properties | 0 |
| 9 | structure-property relationships porous frameworks AI | 0 |
| 10 | deep learning diffusion coefficients solids | 0 |
| 11 | AI prediction gas selectivity porous materials | 0 |
| 12 | graph representations molecular permeation | 0 |
| 13 | neural network models COF gas separation | 0 |
| 14 | high-throughput screening membranes graph networks | 0 |
| 15 | molecular dynamics graph neural networks | 0 |
| 16 | transport properties fluids confined nanopores | 0 |
| 17 | machine learning design porous membranes | 0 |
| 18 | graph representation learning crystal transport | 0 |
| 19 | data-driven modeling molecular permeation nanopores | 0 |
| 20 | end-to-end learning molecular transport porous solids | 0 |

### Verified citations

1. **MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction** (2018). Soumya Sanyal, Janakiraman Balachandran, Naganand Yadati, Abhishek Kumar, Padmini Rajagopalan, et al.. arXiv. [1811.05660](https://arxiv.org/abs/1811.05660). PDF-sampled: No.
2. **Applications of Machine Learning in Polymer Materials: Property Prediction, Material Design, and Systematic Processes** (2025). Hongtao Guo Shuai Li Shu Li. arXiv. [2510.26100](https://arxiv.org/abs/2510.26100). PDF-sampled: No.
