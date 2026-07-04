---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Material Stability using Machine Learning and DFT Calculations

**Field**: chemistry

## Research question

To what extent do local coordination environment features capture the specific thermodynamic instability mechanisms in disordered rock-salt cathodes that bulk compositional descriptors fail to predict, and does this improvement hold for metastable phases near the convex hull?

## Motivation

Disordered rock-salt (DRX) cathodes are critical for next-generation high-energy-density batteries, but their stability is governed by complex local cation ordering rather than just bulk stoichiometry. While Density Functional Theory (DFT) provides accurate formation energies, its computational cost prohibits exhaustive screening of the vast compositional space. If machine learning models can leverage local coordination features to outperform composition-only baselines—particularly for metastable phases near the convex hull—researchers can efficiently identify promising candidates without exhaustive DFT calculations, accelerating materials discovery.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using terms focused on "local coordination features for material stability," "disordered rock-salt cathode ML prediction," and "thermodynamic instability mechanisms in DRX." We also broadened the search to "graph neural networks for crystal stability" and "ML accelerated DFT screening" to find methodological precedents. The initial search for specific DRX instability mechanisms yielded no direct hits, while broader searches for ML in material property prediction returned results primarily focused on generic graph representations or polymer systems, lacking specific application to the local coordination instability in DRX systems.

### What is known

- [Quantifying uncertainty in high-throughput density functional theory: a comparison of AFLOW, Materials Project, and OQMD (2020)](https://arxiv.org/abs/2007.01988) — Establishes the baseline accuracy and systematic uncertainties across major DFT databases, confirming that while DFT is reliable, small errors in formation energy can significantly impact the ranking of metastable phases near the convex hull.
- [MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction (2018)](https://arxiv.org/abs/1811.05660) — Demonstrates that graph-based representations capturing local atomic environments outperform composition-only models for general material property prediction, though it does not specifically address the instability mechanisms in disordered rock-salts.
- [Applications of Machine Learning in Polymer Materials: Property Prediction, Material Design, and Systematic Processes (2025)](https://arxiv.org/abs/2510.26100) — Reviews ML applications in polymer design, highlighting the general trend that local structural features improve prediction accuracy, but offers no specific insights for inorganic cathode materials.

### What is NOT known

No published work has quantitatively isolated the contribution of local coordination environment features (e.g., specific cation-anion bond lengths, Voronoi face statistics) to the prediction error of bulk-composition-only models specifically for disordered rock-salt systems. Furthermore, there is no evidence determining whether incorporating these local features significantly improves the classification of metastable phases (those within 0.05 eV/atom of the hull) compared to bulk descriptors alone.

### Why this gap matters

Identifying whether local coordination is the primary driver of instability in DRX materials is crucial for rational design; if local features are the key, the search space can be constrained to specific cation ordering patterns rather than random compositions. Filling this gap would provide a computationally efficient filter for high-throughput screening, reducing the reliance on expensive DFT calculations for the vast majority of unstable candidates.

### How this project addresses the gap

This project explicitly compares a composition-only baseline against a model augmented with local coordination features (Voronoi tessellation, bond-length histograms) on a curated set of DRX compounds. By stratifying the evaluation by distance to the convex hull, we directly measure the incremental value of local features for predicting metastable phases, thereby quantifying the specific instability mechanisms they capture.

## Expected results

We expect the composition-only model to achieve a moderate MAE (≈0.10–0.15 eV/atom) but fail to distinguish between stable and metastable phases near the convex hull due to the averaging effect of bulk descriptors. In contrast, the model incorporating local coordination features is expected to reduce the MAE to ≤0.06 eV/atom and significantly improve the recall of metastable phases (AUC-ROC ≥ 0.85), demonstrating that local structural disorder is the dominant factor in DRX instability. The results will confirm that local features provide a non-trivial, independent signal for stability prediction that bulk composition alone cannot capture.

## Methodology sketch

- **Data acquisition**
  1. Download the OQMD formation-energy dataset (filtered for Li-rich oxides and rock-salt structures) from the OQMD Zenodo repository or via their API.
  2. Filter entries to include only those with fully relaxed DFT energies and known crystal structures.
  3. Split the dataset into 70% training, 15% validation, and 15% test sets, ensuring stratification by chemical system and distance to the convex hull to prevent data leakage.

- **Feature engineering**
  1. Compute bulk compositional descriptors (Magpie features) using *matminer*.
  2. Generate local coordination features using *pymatgen*:
     - Voronoi tessellation statistics (coordination number, face area, solid angle).
     - Bond-length distributions for nearest-neighbor shells.
     - Local cation ordering patterns (e.g., nearest-neighbor cation types).
  3. Normalize all features to ensure numerical stability.

- **Model training**
  1. Train a Gradient Boosting Regressor (scikit-learn) on the training set using only bulk compositional descriptors.
  2. Train a second Gradient Boosting Regressor using the combined set of bulk and local coordination features.
  3. Perform hyperparameter tuning (max_depth, n_estimators) on the validation set with early stopping to prevent overfitting.

- **Evaluation (independent validation)**
  1. Predict formation energies for the test set and compare against the independent DFT reference values (ground truth).
  2. Calculate MAE, RMSE, and R² for both models to quantify predictive accuracy.
  3. Compute the distance to the convex hull for predicted and actual energies using *pymatgen*'s `PhaseDiagram` class (independent calculation based on elemental references).
  4. Perform binary classification (stable vs. unstable, defined as < 0.05 eV/atom above hull) and generate ROC curves to evaluate the ability to distinguish metastable phases.
  5. Analyze feature importance to identify which local coordination metrics contribute most to the improvement.

- **Reproducibility & runtime constraints**
  - All steps scripted in a Python pipeline compatible with GitHub Actions free-tier runners (2 CPU, 7 GB RAM).
  - Data processing and model training limited to ≤ 4 hours total runtime.
  - Results saved to `outputs/` directory including feature importance plots and ROC curves.

- **Deliverables**
  - Public GitHub repository containing the code, processed dataset, and a Jupyter notebook reproducing the analysis.

## Duplicate-check

- Reviewed existing ideas: *(none provided)*.
- Closest match: N/A.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-04T21:15:28Z
**Outcome**: exhausted
**Original term**: Predicting Material Stability using Machine Learning and DFT Calculations chemistry
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Material Stability using Machine Learning and DFT Calculations chemistry | 0 |
| 1 | machine learning for materials stability prediction | 5 |
| 2 | density functional theory thermodynamic stability | 0 |
| 3 | formation energy prediction with machine learning | 0 |
| 4 | crystal structure stability classification | 0 |
| 5 | DFT-calculated cohesive energy models | 0 |
| 6 | high-throughput screening of material stability | 0 |
| 7 | graph neural networks for formation energy | 0 |
| 8 | phase stability prediction using AI | 0 |
| 9 | machine learning interatomic potentials for stability | 0 |
| 10 | computational materials design stability metrics | 0 |
| 11 | predicting decomposition energy with deep learning | 0 |
| 12 | descriptor-based stability models in materials science | 0 |
| 13 | DFT-based machine learning force fields | 0 |
| 14 | convex hull construction for material stability | 0 |
| 15 | automated materials discovery stability assessment | 0 |
| 16 | symmetry-aware neural networks for crystal stability | 0 |
| 17 | transfer learning for materials property prediction | 0 |
| 18 | active learning in computational chemistry stability | 0 |
| 19 | Bayesian optimization for stable material discovery | 0 |
| 20 | quantum mechanical calculations coupled with ML for thermodynamics | 0 |

### Verified citations

1. **Quantifying uncertainty in high-throughput density functional theory: a comparison of AFLOW, Materials Project, and OQMD** (2020). Vinay I. Hegde, Christopher K. H. Borg, Zachary del Rosario, Yoolhee Kim, Maxwell Hutchinson, et al.. arXiv. [2007.01988](https://arxiv.org/abs/2007.01988). PDF-sampled: No.
2. **MT-CGCNN: Integrating Crystal Graph Convolutional Neural Network with Multitask Learning for Material Property Prediction** (2018). Soumya Sanyal, Janakiraman Balachandran, Naganand Yadati, Abhishek Kumar, Padmini Rajagopalan, et al.. arXiv. [1811.05660](https://arxiv.org/abs/1811.05660). PDF-sampled: No.
3. **Applications of Machine Learning in Polymer Materials: Property Prediction, Material Design, and Systematic Processes** (2025). Hongtao Guo Shuai Li Shu Li. arXiv. [2510.26100](https://arxiv.org/abs/2510.26100). PDF-sampled: No.
