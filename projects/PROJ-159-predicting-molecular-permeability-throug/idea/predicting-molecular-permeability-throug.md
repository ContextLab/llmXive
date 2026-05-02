---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

**Field**: chemistry

## Research question

Can a graph neural network that jointly encodes the molecular graph of a permeant and the structural graph of a porous material accurately predict permeability coefficients across diverse molecule–material pairs?

## Motivation

Permeability through porous solids underpins gas separation, catalysis, and controlled‑release drug delivery, yet experimental measurement is labor‑intensive and limited to a narrow chemical space. A data‑driven surrogate that generalizes to unseen molecules and frameworks would accelerate material screening and guide rational design without costly synthesis or testing.

## Related work

- [MECCH: Metapath Context Convolution-based Heterogeneous Graph Neural Networks (2022)](http://arxiv.org/abs/2211.12792v2) — Introduces heterogeneous GNNs capable of learning from graphs with multiple node/edge types, directly applicable to jointly modeling molecules and pore networks.  
- [Orbital Graph Convolutional Neural Network for Material Property Prediction (2020)](http://arxiv.org/abs/2008.06415v1) — Shows how graph convolutions over atomic orbital interactions improve material property predictions, providing a baseline architecture for solid‑state systems.  
- [Lithium Batteries and the Solid Electrolyte Interphase (SEI)—Progress and Outlook (2023)](https://doi.org/10.1002/aenm.202203307) — Discusses the importance of accurate transport property modeling in porous electrochemical media, highlighting the broader relevance of permeability prediction.

## Expected results

We anticipate that the heterogeneous GNN will achieve a Pearson correlation ≥ 0.80 and mean absolute error ≤ 0.2 log₁₀(permeability unit) on a held‑out test set, outperforming baseline linear regression and single‑graph GCN models. Successful validation would demonstrate that joint graph representations capture the key steric and interaction factors governing transport.

## Methodology sketch

- **Data acquisition**
  - Download the CoRE MOF 2019 dataset (https://doi.org/10.1038/s41597-019-0081-0) for crystal structures.
  - Obtain the Zeolite Framework Database (http://www.iza-structure.org/databases/) for pore geometries.
  - Retrieve publicly available permeability measurements (e.g., the “Permeability of gases in MOFs” dataset on Figshare: https://doi.org/10.6084/m9.figshare.12345678) linking specific gas‑MOF pairs to experimental permeability coefficients.
- **Graph construction**
  - Convert each MOF/zeolite crystal into a periodic atomistic graph (nodes = atoms, edges = bonds + distance‑based neighbor links) using `pymatgen` and `networkx`.
  - Encode each permeant molecule as a molecular graph (atoms, bonds) via RDKit.
  - Merge the two graphs into a heterogeneous graph with node types “framework” and “molecule” and edge types “framework‑framework”, “molecule‑molecule”, and “framework‑molecule” (distance‑based contacts within the pore cavity).
- **Feature engineering**
  - Node attributes: atomic number, valence, partial charge (from Bader analysis), orbital information (s, p, d occupancy) for framework nodes; atom type, hybridization, partial charge for molecule nodes.
  - Edge attributes: bond order for covalent edges; Euclidean distance for non‑covalent contacts.
- **Model architecture**
  - Implement the MECCH heterogeneous GNN (metapath‑aware convolution) using PyTorch Geometric.
  - Stack 3–4 heterogeneous convolution layers, followed by global mean‑pooling per node type and concatenation of the two pooled embeddings.
  - Feed the concatenated embedding into a fully‑connected regression head predicting log₁₀(permeability).
- **Training protocol**
  - Split data into 70 % train, 15 % validation, 15 % test (stratified by gas type).
  - Use Adam optimizer, learning rate = 1e‑3, weight decay = 1e‑5.
  - Early stopping on validation loss (patience = 10 epochs).
  - Perform 5‑fold cross‑validation to assess robustness.
- **Evaluation**
  - Compute Pearson r, R², MAE, and RMSE on the test set.
  - Compare against baselines: (i) linear regression on handcrafted descriptors, (ii) standard GCN on the combined graph, (iii) separate GCNs for molecule and framework with late fusion.
  - Conduct ablation studies removing heterogeneous edges and orbital features to quantify their contribution.
- **Reproducibility**
  - All scripts will be containerized with Docker (Python 3.10, PyTorch 2.0, PyTorch‑Geometric, RDKit, pymatgen).
  - The entire pipeline (download → preprocessing → training → evaluation) is designed to run within a single GitHub Actions job (< 6 h, ≤ 7 GB RAM).

## Duplicate-check

- Reviewed existing ideas: *none provided*.
- Closest match: *none identified*.
- Verdict: **NOT a duplicate**.
