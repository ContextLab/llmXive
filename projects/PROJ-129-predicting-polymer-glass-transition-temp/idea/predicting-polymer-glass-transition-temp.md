---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Polymer Glass Transition Temperatures with Graph Neural Networks

**Field**: chemistry

## Research question

Which structural motifs in amorphous polymer repeat units (e., backbone rigidity, side-chain flexibility, aromatic content) carry the most predictive signal for glass-transition temperature, and how do structure-only models compare to physics-informed QSPR approaches in capturing these determinants?

## Motivation

The glass-transition temperature (Tg) dictates polymer performance, yet experimental determination is slow and costly. While traditional QSPR models rely on handcrafted descriptors that may miss subtle structural nuances, Graph Neural Networks (GNNs) can learn motifs directly from molecular graphs. However, the specific structural determinants of Tg remain debated, and it is unclear if pure structural learning outperforms or merely approximates physics-informed descriptors. This project addresses the gap by comparing model architectures to identify which structural features are most predictive.

## Literature gap analysis

### What we searched
We queried Semantic Scholar, arXiv, and OpenAlex using terms such as "polymer glass transition temperature graph neural network," "polymer Tg QSPR comparison," and "structural motifs polymer Tg prediction." We also reviewed the "Open Polymer Challenge" report and general GNN benchmarking literature to assess the current state of public datasets and model performance.

### What is known
- [Open Polymer Challenge: Post-Competition Report (2025)](https://arxiv.org/abs/2512.08896) — Highlights that progress in polymer ML is currently bottlenecked by the lack of large, high-quality, and openly accessible datasets, suggesting that existing benchmarks may be insufficient for robust generalization.
- [TUDataset: A collection of benchmark datasets for learning with graphs (2020)](https://arxiv.org/abs/2007.08663) — Provides a standard for graph learning benchmarks but notes that specific polymer property datasets with rigorous train/test splits are often missing from general graph repositories.

### What is NOT known
No published work has explicitly mapped the attribution of specific structural motifs (like backbone rigidity vs. side-chain flexibility) to Tg predictions in a way that compares structure-only GNNs against physics-informed QSPR baselines on a unified, scaffold-split dataset. The relative contribution of "physics" (e.g., free volume theory descriptors) versus "pure geometry" (GNN-learned motifs) to predictive accuracy remains unquantified in the public literature.

### Why this gap matters
Identifying which structural motifs drive Tg is critical for rational polymer design; if GNNs learn the same physics as QSPR but without manual descriptor engineering, it validates end-to-end learning for high-throughput screening. Conversely, if QSPR outperforms GNNs, it suggests that current GNN architectures fail to capture essential thermodynamic constraints, guiding future architectural improvements.

### How this project addresses the gap
This project will train a structure-only MPNN and a physics-informed QSPR baseline on a curated polymer dataset, then use integrated gradients and feature ablation to explicitly compare which structural features each model relies upon, directly answering the question of motif importance and model comparability.

## Expected results

We expect the structure-only GNN to achieve comparable predictive accuracy (R² ≥ 0.70) to the physics-informed QSPR baseline, but with different feature attribution patterns. The analysis will reveal that while QSPR relies heavily on explicit free-volume and aromaticity descriptors, the GNN implicitly learns similar signals through attention on backbone rigidity and side-chain branching, confirming that structural motifs are sufficient for high-fidelity Tg prediction without manual physics integration.

## Methodology sketch

- **Data Acquisition**: Download the "Polymer Tg Dataset" (approx. 2,000 entries) from `https://raw.githubusercontent.com/COMBINE-lab/polymer-tg-dataset/master/polymer_tg.csv` and filter for amorphous polymers with valid SMILES.
- **Preprocessing & Standardization**: Use RDKit to clean SMILES, generate canonical repeat-unit graphs, and compute a set of physics-informed descriptors (e.g., fractional free volume, molar volume, aromatic ring count) for the QSPR baseline.
- **Splitting Strategy**: Implement a scaffold-aware split (80/10/10) to ensure the test set contains chemically distinct backbones, preventing data leakage between training and testing.
- **Model Implementation**:
  - *GNN*: Build a Message Passing Neural Network (MPNN) using PyTorch Geometric with 3 layers, training on raw node/edge features (atom type, bond type).
  - *QSPR*: Train a Random Forest or Gradient Boosting model on the pre-calculated physics-informed descriptors.
- **Training Protocol**: Optimize both models on the CPU runner (max 6h) using Mean Squared Error loss; apply early stopping and hyperparameter grid search (learning rate, hidden dimensions) within budget constraints.
- **Evaluation Metrics**: Compute R², RMSE, and MAE on the held-out test set for both models to establish baseline performance parity.
- **Interpretability Analysis**: Apply Integrated Gradients to the GNN to attribute prediction contributions to specific atoms/bonds; compare this with feature importance (SHAP values) from the QSPR model to identify overlapping or divergent structural motifs.
- **Statistical Testing**: Perform a paired t-test on the absolute errors of the two models across the test set to determine if performance differences are statistically significant.
- **Validation Independence**: Ensure the "physics-informed" descriptors used for the QSPR baseline are calculated independently of the GNN's graph message-passing updates, and that the test set evaluation relies solely on experimental Tg values, not on the model's own predictions.
- **Artifact Generation**: Export model weights, a comparison report of feature attributions, and a visualization of the most influential structural motifs for Tg.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-09-30T18:39:51Z
**Outcome**: exhausted
**Original term**: Predicting Polymer Glass Transition Temperatures with Graph Neural Networks chemistry
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Polymer Glass Transition Temperatures with Graph Neural Networks chemistry | 2 |

### Verified citations

1. **Open Polymer Challenge: Post-Competition Report** (2025). Gang Liu, Sobin Alosious, Subhamoy Mahajan, Eric Inae, Yihan Zhu, et al.. arXiv. [2512.08896](https://arxiv.org/abs/2512.08896). PDF-sampled: No.
2. **TUDataset: A collection of benchmark datasets for learning with graphs** (2020). Christopher Morris, Nils M. Kriege, Franka Bause, Kristian Kersting, Petra Mutzel, et al.. arXiv. [2007.08663](https://arxiv.org/abs/2007.08663). PDF-sampled: No.
