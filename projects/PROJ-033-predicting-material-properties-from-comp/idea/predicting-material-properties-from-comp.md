---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Material Properties from Compositional Data with Graph Neural Networks

**Field**: materials science

## Research question

To what extent do compositional features (element identity, periodic table properties) encode predictive signal for band gap and hardness in crystalline materials, and how much information is lost when crystal structure is excluded from the representation?

## Motivation

Materials discovery is bottlenecked by expensive DFT simulations and experimental synthesis that require full crystal structure information. If compositional representations alone retain sufficient predictive signal, they could enable rapid screening of candidate materials where structure is unknown or synthesis is uncertain. This work addresses the gap between traditional composition-based heuristics and full-structure deep learning approaches by quantifying the information loss when structural data is excluded.

## Related work

- [Dynamic embedding representation for graph neural networks to enhance materials property prediction with limited datasets (2026)](https://validate.perfdrive.com/fb803c746e9148689b3984a31fccd902/?ssa=e1b80503-0de5-4ac4-95a6-10a35463e808&ssb=10229208567&ssc=https%3A%2F%2Fiopscience.iop.org%2Farticle%2F10.1088%2F2053-1591%2Fae5148&ssi=1e894fbb-cnvj-467b-a312-5e3006ade71b&ssk=botmanager_support@radware.com&ssm=84724404606010237103774801240358&ssn=c219c5f203ac02569c9e4d9d968d0b3361aa217e5d8f-7097-4287-94a3ae&sso=8193fb57-e4aa0417bf84b4d15f014619dc8ee573d60e501b9a348afd&ssp=42522588061782635675178262109102329&ssq=92369655790734047967857907212182059243188&ssr=MTc0LjE2OS4xMTQuNTc=&sst=llmxive-librarian/1.0%20(https%3A%2F%2Fgithub.com%2FContextLab%2FllmXive)&ssu=&ssv=&ssw=&ssx=eyJ1em14IjoiN2Y5MDAwYmJkZjRhMTctMTZjZi00M2YxLWFjNTEtNjI4YzM1ODM2MDNhMS0xNzgyNjU3OTA3MTkwMC1iYTQwZjI4ZDJmYmZmMjljMTAiLCJfX3V6bWYiOiI3ZjkwMDAyMTdlNWQ4Zi03MDk3LTQyODctOWI1Ny1lNGFhMDQxN2JmODQxLTE3ODI2NTc5MDcxOTAwLTAwNGVhNGFhNDhiMDhiNjU0MGExMCIsInJkIjoiaW9wLm9yZyJ9) — Demonstrates GNNs can learn material property relationships even with limited datasets, supporting the feasibility of composition-only training.
- [Orbital Graph Convolutional Neural Network for Material Property Prediction (2020)](https://arxiv.org/abs/2008.06415) — Explores atomic orbital interactions in GNNs, establishing how compositional representations can encode physical property relationships.
- [Materials Representation and Transfer Learning for Multi-Property Prediction (2021)](https://pubs.aip.org/apr/article/8/2/021409/1067988/Materials-representation-and-transfer-learning-for) — Discusses representation learning challenges in materials ML, providing context for comparing compositional vs. structural feature encodings.
- [Density Prediction Models for Energetic Compounds Merely Using Molecular Topology (2021)](https://pubs.acs.org/doi/10.1021/acs.jcim.0c01393) — Shows property prediction is feasible using only molecular topology, establishing precedent for structure-agnostic approaches.

## Expected results

We expect composition-only GNNs to achieve R² > 0.6 for band gap prediction but show significant degradation (ΔR² > 0.15) compared to structure-aware baselines, particularly for hardness which depends more on crystal packing. The performance gap will vary systematically by crystal system, with larger losses observed in anisotropic structures where directional bonding dominates property determination.

## Methodology sketch

- **Data acquisition**: Download Materials Project Open Data (https://doi.org/10.17188/1399059); extract composition, band gap (eV), hardness (GPa), and crystal system for ≤10,000 crystalline materials; limit to ≤7GB RAM via chunked loading.
- **Compositional graph construction**: Parse chemical formulas to create element-level nodes with features (atomic number, electronegativity, valence electrons, atomic radius); connect all element pairs with periodic table distance as edge weights.
- **Structure-aware baseline**: For comparison subset (≤2,000 materials), construct full crystal graphs using atom positions and coordination information from Materials Project CIF files.
- **Train/test split**: Stratified 80/10/10 split by crystal system to ensure distributional consistency; verify test set materials are not in training set (deduplicate by formula + structure ID).
- **Model architecture**: Implement lightweight GNN (2-3 graph convolution layers, hidden dim ≤128) using PyTorch Geometric; train on CPU with batch size ≤32.
- **Training procedure**: Optimize with Adam (lr=1e-3, early stopping patience=10 epochs); limit to ≤50 epochs with max 30-minute runtime per epoch; use 5-fold cross-validation for variance estimation.
- **Statistical evaluation**: Compute R², MAE, and RMSE for both band gap and hardness on held-out test set; use independent test set (never seen during training or validation) to avoid circular validation.
- **Baseline comparison**: Compare against random forest and linear regression trained on the same compositional features; quantify GNN advantage as ΔR² over baselines.
- **Information loss quantification**: Calculate performance gap between composition-only and structure-aware models; analyze error patterns by crystal system to identify where structural information is most critical.
- **Embedding analysis**: Perform PCA on learned node embeddings; correlate principal components with periodic properties using Pearson correlation (p-value < 0.05 threshold) to verify chemical interpretability.

## Duplicate-check

- Reviewed existing ideas: N/A (initial flesh-out in this field).
- Closest match: None identified in current corpus.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-28T15:06:43Z
**Outcome**: success
**Original term**: Predicting Material Properties from Compositional Data with Graph Neural Networks materials science
**Verified citation count**: 11

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Material Properties from Compositional Data with Graph Neural Networks materials science | 11 |

### Verified citations

1. **Dynamic embedding representation for graph neural networks to enhance materials property prediction with limited datasets** (2026). Vishu Gupta, Kamal Choudhary, Youjia Li, Muhammed Nur Talha Kilic, D. Wines, et al.. Materials Research Express. [https://doi.org/10.1088/2053-1591/ae5148](https://doi.org/10.1088/2053-1591/ae5148). PDF-sampled: No.
2. **Application of Parallelized Graph Neural Networks in Predicting Molecular Properties from Large-Scale Chemical Databases** (2025). Piotr Tomaszewski, Adam Wojcik. Data Engineering and Applications. [https://doi.org/10.64972/dea.2025.v3i1.68](https://doi.org/10.64972/dea.2025.v3i1.68). PDF-sampled: Inaccessible.
3. **StrainTensorNet: Predicting crystal structure elastic properties using SE(3)-equivariant graph neural networks** (2023). T. Pakornchote, A. Ektarawong, Thiparat Chotibut. Physical Review Research. [https://doi.org/10.1103/physrevresearch.5.043198](https://doi.org/10.1103/physrevresearch.5.043198). PDF-sampled: No.
4. **Orbital Graph Convolutional Neural Network for Material Property Prediction** (2020). Mohammadreza Karamad, Rishikesh Magar, Yuting Shi, Samira Siahrostami, Ian D. Gates, et al.. arXiv. [2008.06415](https://arxiv.org/abs/2008.06415). PDF-sampled: No.
5. **Regression with Large Language Models for Materials and Molecular Property Prediction** (2024). R. Jacobs, Maciej P. Polak, Lane E. Schultz, Hamed Mahdavi, Vasant Honavar, et al.. arXiv.org. [https://doi.org/10.48550/arXiv.2409.06080](https://doi.org/10.48550/arXiv.2409.06080). PDF-sampled: No.
6. **Materials Representation and Transfer Learning for Multi-Property Prediction** (2021). Shufeng Kong, D. Guevarra, Carla P. Gomes, J. Gregoire. Applied Physics Reviews. [https://doi.org/10.1063/5.0047066](https://doi.org/10.1063/5.0047066). PDF-sampled: No.
7. **Few-shot Molecular Property Prediction: A Survey** (2025). Zeyu Wang, Tianyi Jiang, Huanchang Ma, Yao Lu, Xiaoze Bao, et al.. arXiv. [2510.08900](https://arxiv.org/abs/2510.08900). PDF-sampled: No.
8. **At-Scale Data-Driven Exploration of High-Voltage Cathode-Active Materials for Sodium Batteries** (2026). Suchona Akter, Mohammadjafar Momeni. n/a. [2605.27229](https://arxiv.org/abs/2605.27229). PDF-sampled: No.
9. **Advancing material property prediction: using physics-informed machine learning models for viscosity** (2024). Alex K. Chew, M. Sender, Zachary Kaplan, Anand Chandrasekaran, Jackson Chief Elk, et al.. Journal of Cheminformatics. [https://doi.org/10.1186/s13321-024-00820-5](https://doi.org/10.1186/s13321-024-00820-5). PDF-sampled: No.
10. **Density Prediction Models for Energetic Compounds Merely Using Molecular Topology** (2021). Chunming Yang, Jie Chen, Runwen Wang, Miao Zhang, Chaoyang Zhang, et al.. Journal of Chemical Information and Modeling. [https://doi.org/10.1021/acs.jcim.0c01393](https://doi.org/10.1021/acs.jcim.0c01393). PDF-sampled: No.
11. **Material symmetry recognition and property prediction accomplished by crystal capsule representation** (2023). Chao Liang, Yilimiranmu Rouzhahong, Caiyuan Ye, Chong Li, Biao Wang, et al.. Nature Communications. [https://doi.org/10.1038/s41467-023-40756-2](https://doi.org/10.1038/s41467-023-40756-2). PDF-sampled: No.
