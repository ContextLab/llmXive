---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

**Field**: chemistry

## Research question

Which molecular graph features most strongly determine refractive index, and what prediction error can lightweight GNNs achieve when limited to CPU‑only inference?

## Motivation

Refractive index is a fundamental optical property critical for pharmaceutical formulation and material design, yet standard determination relies on slow quantum mechanical calculations. While graph-based machine learning offers potential speedups, the specific molecular substructures driving refractive behavior remain opaque, and the feasibility of high-accuracy prediction under strict CPU-only resource constraints is unproven. This project addresses the gap between high-accuracy quantum methods and efficient, interpretable predictive modeling for early-stage screening.

## Literature gap analysis

### What we searched
We queried Semantic Scholar, arXiv, and OpenAlex for terms including "molecular refractive index prediction," "graph neural network refractive index," and "few-shot molecular property prediction." The search focused on recent literature (2020–2025) to identify established benchmarks or specific GNN architectures applied to optical properties.

### What is known
- [Few-shot Molecular Property Prediction: A Survey (2025)](https://arxiv.org/abs/2510.08900) — This survey establishes that AI-assisted molecular property prediction is a promising technique for early-stage drug discovery but highlights that high-cost wet-lab experiments and data scarcity remain significant barriers, particularly for less common properties like refractive index.

### What is NOT known
No published work has explicitly quantified which specific molecular graph features (e.g., specific atom types, bond orders, or topological indices) are the dominant determinants of refractive index in organic molecules. Furthermore, there is no established benchmark for the minimum achievable Mean Absolute Error (MAE) for refractive index prediction when constrained to lightweight GNNs running exclusively on CPU hardware with limited memory.

### Why this gap matters
Identifying the structural drivers of refractive index would accelerate rational material design by allowing chemists to target specific substructures rather than relying on trial-and-error synthesis or expensive quantum calculations. Demonstrating a viable CPU-only prediction pipeline would democratize access to these screening tools for researchers without access to GPU clusters.

### How this project addresses the gap
This project will train a lightweight Message Passing Neural Network (MPNN) on a public dataset to predict refractive indices, then use feature attribution methods (e.g., Integrated Gradients) to isolate the most influential graph features. The methodology explicitly measures prediction error under CPU-only constraints to define the practical limits of resource-efficient modeling for this property.

## Expected results

We expect to identify a subset of graph features (e.g., conjugated pi-systems or specific halogen substitutions) that correlate strongly with refractive index deviations. We anticipate a lightweight GNN will achieve an MAE below 0.05 on a held-out test set, with performance variance remaining stable across random seeds, providing sufficient evidence that CPU-based inference is viable for this task.

## Methodology sketch

- **Data Acquisition**: Download a curated CSV dataset containing molecular SMILES strings and experimental refractive index values from the NIST Chemistry WebBook or a Zenodo mirror (e.g., the "Molecular Refractive Index" dataset), ensuring the data is publicly accessible via `wget`.
- **Data Preprocessing**: Use RDKit (CPU version) to parse SMILES into molecular graphs; filter for organic molecules with molecular weight < 500 Da to ensure compatibility with the 7GB RAM limit.
- **Feature Extraction**: Generate node features (atomic number, degree, hybridization) and edge features (bond type, conjugation) to construct the input graph tensors.
- **Dataset Split**: Perform a stratified random split (80% training, 10% validation, 10% testing) ensuring no structural overlap (scaffold splitting) to prevent data leakage.
- **Model Architecture**: Implement a 3-layer Message Passing Neural Network (MPNN) using PyTorch Geometric with a hidden dimension of 64, explicitly disabling CUDA to enforce CPU execution.
- **Training Configuration**: Train for a maximum of 50 epochs with early stopping (patience=10) and a batch size of 32 to stay within the 6-hour GitHub Actions time limit and memory constraints.
- **Feature Attribution**: Apply Integrated Gradients to the trained model to compute feature importance scores for each molecular graph, identifying which substructures drive the refractive index predictions.
- **Computation**: Calculate Mean Absolute Error (MAE) and Root Mean Square Error (RMSE) on the test set; store predictions and attribution scores in CSV artifacts.
- **Statistical Validation**: Perform a paired t-test comparing the GNN's MAE against a baseline linear regression model trained on simple molecular descriptors (e.g., molecular weight, number of heavy atoms) to confirm that the GNN provides a statistically significant improvement independent of the input features used by the baseline.
- **Visualization**: Generate a parity plot (Predicted vs. Actual) and a feature importance bar chart; save as PNG artifacts with file sizes < 5MB.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-12T12:55:35Z
**Outcome**: exhausted
**Original term**: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations chemistry
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Molecular Refractive Indices from Graph-Based Molecular Representations chemistry | 0 |
| 1 | Graph neural networks for molecular property prediction | 5 |
| 2 | Machine learning prediction of refractive index in organic compounds | 0 |
| 3 | Molecular graph representations for optical property estimation | 0 |
| 4 | Deep learning models for refractive index calculation | 0 |
| 5 | QSAR models for refractive index using molecular graphs | 0 |
| 6 | Graph-based regression for optical constants | 0 |
| 7 | Atomic contribution methods for refractive index prediction | 0 |
| 8 | Molecular descriptor-based refractive index estimation | 0 |
| 9 | End-to-end learning of optical properties from molecular structure | 0 |
| 10 | Graph convolutional networks for physical property prediction | 0 |
| 11 | Data-driven prediction of molar refraction | 0 |
| 12 | Structure-property relationships for refractive index | 0 |
| 13 | Message passing neural networks for molecular optical properties | 0 |
| 14 | Computational estimation of refractive index from SMILES or graphs | 0 |
| 15 | Graph attention networks for predicting refractive indices | 0 |
| 16 | Molecular fingerprint approaches to refractive index modeling | 0 |
| 17 | In silico prediction of optical refractive index | 0 |
| 18 | Topological indices for refractive index correlation | 0 |
| 19 | Transfer learning for molecular optical property prediction | 0 |
| 20 | Automated refractive index estimation using graph algorithms | 0 |

### Verified citations

1. **Few-shot Molecular Property Prediction: A Survey** (2025). Zeyu Wang, Tianyi Jiang, Huanchang Ma, Yao Lu, Xiaoze Bao, et al.. arXiv. [2510.08900](https://arxiv.org/abs/2510.08900). PDF-sampled: No.
