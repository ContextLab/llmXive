---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Field**: chemistry

## Research question

Which structural and electronic features of small organic molecules carry the most predictive signal for reaction yields or rate constants, and how closely can graph-based ML models approximate quantum-mechanical accuracy on standard benchmark sets?

## Motivation

Computational screening of molecular reactivity typically relies on density functional theory (DFT), which is computationally expensive and often requires specialized hardware. This research addresses the gap for rapid, CPU-based screening methods that leverage publicly available data to identify the specific molecular descriptors driving reactivity. Success would enable resource-constrained environments to perform preliminary reactivity assessments and provide interpretability on which chemical features matter most, complementing black-box "accuracy-only" approaches.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv for terms including "graph neural networks molecular reactivity prediction," "spectral GNN chemical properties," and "GNN heterophily molecular graphs." We also broadened the search to "GNN efficiency benchmarks" and "quantum machine learning reaction yield." The search returned several papers on general GNN efficiency and graph properties (homophily/heterophily) but few that directly benchmark GNNs against quantum-mechanical accuracy for *reaction yields* on standard CPU-constrained benchmarks.

### What is known
- [A Comprehensive Benchmark on Spectral GNNs: The Impact on Efficiency, Memory, and Effectiveness (2024)](https://arxiv.org/abs/2406.09675) — Establishes that spectral GNNs vary significantly in memory and efficiency trade-offs, which is critical for selecting a model architecture that fits within limited compute resources like GitHub Actions runners.
- [Characterizing Graph Datasets for Node Classification: Homophily-Heterophily Dichotomy and Beyond (2022)](https://arxiv.org/abs/2209.06177) — Demonstrates that standard GNNs struggle on heterophilous graphs; this is relevant because molecular graphs often exhibit low homophily (connected atoms have different chemical properties), suggesting standard message-passing may need adaptation for chemical data.
- [VR-GNN: Variational Relation Vector Graph Neural Network for Modeling both Homophily and Heterophily (2022)](https://arxiv.org/abs/2211.14523) — Proposes a GNN variant explicitly designed to handle heterophily, offering a potential architectural candidate for modeling complex atom-bond relationships where neighbor properties differ significantly.

### What is NOT known
No published work in the retrieved literature specifically benchmarks lightweight, CPU-only GNN architectures against DFT-derived reaction yields or rate constants to quantify *which* structural features (e.g., specific bond types, electronic environments) dominate the predictive signal. Furthermore, there is a lack of analysis on whether standard spectral GNN benchmarks translate to the heterophilous nature of molecular graphs in the context of regression tasks for reactivity.

### Why this gap matters
Understanding the specific features driving reactivity is essential for rational catalyst design and for interpreting ML models in chemistry, moving beyond "black box" predictions. Filling this gap would allow researchers to deploy rapid, interpretable screening tools on standard hardware, accelerating the discovery of new reactions without the prohibitive cost of full quantum simulations.

### How this project addresses the gap
This project will train lightweight GNNs on the QM9 dataset (a standard benchmark for molecular properties) and perform feature attribution analysis (e.g., via GNNExplainer or gradient-based methods) to identify the structural/electronic features most correlated with target properties. We will directly compare the model's approximation error against DFT ground truth to quantify the "quantum-mechanical accuracy" achievable under CPU constraints, explicitly testing performance on the heterophilous nature of molecular graphs.

## Expected results

We expect the model to identify specific electronic features (e.g., frontier orbital energies or specific bond orders) as the dominant predictors of reactivity, with the GNN achieving a Pearson correlation coefficient (R) > 0.8 against DFT values on held-out data. The evidence will demonstrate that while spectral GNNs offer efficiency, specific adaptations for heterophily are required to match quantum-mechanical accuracy, and that these adaptations remain feasible within a 6-hour CPU job.

## Methodology sketch

- Download the QM9 dataset (subset of 100,000 molecules with DFT-calculated properties) via HuggingFace Datasets (`huggingface/datasets`) using `wget` or Python API.
- Preprocess SMILES strings into graph structures using RDKit (CPU mode), ensuring node features include atomic number, hybridization, and formal charge, and edge features include bond type and conjugation.
- Implement a lightweight Spectral GNN and a Heterophily-aware GNN (based on VR-GNN principles) using PyTorch (CPU-only, `device='cpu'`), ensuring memory usage stays under 4GB.
- Train both models for 50 epochs with early stopping on a 80/20 train/test split, targeting the prediction of specific DFT properties (e.g., HOMO-LUMO gap as a proxy for reactivity) to approximate reaction yield signals.
- Evaluate performance using Mean Squared Error (MSE), Pearson correlation (R), and MAE, comparing results against a Random Forest baseline trained on hand-crafted molecular descriptors (Morgan fingerprints).
- Perform feature attribution analysis using GNNExplainer to identify which subgraphs or node features contribute most to the prediction, directly addressing the "which features" part of the research question.
- Apply a paired t-test on the prediction errors of the GNN vs. the Random Forest baseline to statistically assess if the graph-based approach provides a significant improvement in capturing structural nuances.
- Log all artifacts (model weights, attribution maps, metrics) to the repository for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-05T19:08:21Z
**Outcome**: exhausted
**Original term**: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases chemistry
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases chemistry | 3 |

### Verified citations

1. **A Comprehensive Benchmark on Spectral GNNs: The Impact on Efficiency, Memory, and Effectiveness** (2024). Ningyi Liao, Haoyu Liu, Zulun Zhu, Siqiang Luo, Laks V. S. Lakshmanan. arXiv. [2406.09675](https://arxiv.org/abs/2406.09675). PDF-sampled: No.
2. **Characterizing Graph Datasets for Node Classification: Homophily-Heterophily Dichotomy and Beyond** (2022). Oleg Platonov, Denis Kuznedelev, Artem Babenko, Liudmila Prokhorenkova. arXiv. [2209.06177](https://arxiv.org/abs/2209.06177). PDF-sampled: No.
3. **VR-GNN: Variational Relation Vector Graph Neural Network for Modeling both Homophily and Heterophily** (2022). Fengzhao Shi, Ren Li, Yanan Cao, Yanmin Shang, Lanxue Zhang, et al.. arXiv. [2211.14523](https://arxiv.org/abs/2211.14523). PDF-sampled: No.
