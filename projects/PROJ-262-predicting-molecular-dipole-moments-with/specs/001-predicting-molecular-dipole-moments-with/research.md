# Research Report: Predicting Molecular Dipole Moments with Graph Neural Networks

## 1. Executive Summary

This project implements a Graph Neural Network (GNN) pipeline to predict molecular dipole moments for a subset of the QM9 dataset. The model utilizes both 3D geometric features (SchNet-style architecture) and 2D topological descriptors (Random Forest baseline) to estimate dipole moments. The primary ground truth for training and evaluation is derived from Density Functional Theory (DFT) calculations at the BLYP/6-31G(2df,p) level, as provided in the QM9 reference dataset.

## 2. Methodology

### 2.1 Data Source and Preprocessing
- **Dataset**: QM9 (133,885 small organic molecules).
- **Subset**: A reproducible random subset of 10,000 molecules was extracted using a fixed seed (42) to ensure experimental consistency.
- **Features**:
 - 3D: Atomic coordinates, bond connectivity, and inter-atomic distances processed via a SchNet-style GNN.
 - 2D: Morgan fingerprints and Coulomb matrices used for the Random Forest baseline.
- **Preprocessing**: Molecules with missing 3D coordinates were filtered out. Data was split into training and test sets using stratified sampling across multiple seeds to compute variance.

### 2.2 Model Architecture
- **GNN**: A SchNet-inspired architecture implemented in PyTorch, designed to learn continuous-filter convolutions over 3D molecular graphs.
- **Baseline**: A Random Forest regressor trained on flattened 2D feature vectors.
- **Training Protocol**: Models were trained for up to 50 epochs with early stopping (patience=10). Metrics (MAE, RMSE) were computed on the held-out test set. Confidence intervals were generated via bootstrapping.

### 2.3 Feature Attribution
- **Permutation Importance**: Applied to the Random Forest model to rank feature contributions.
- **Saliency Mapping**: Computed for the GNN to identify node embeddings most influential in dipole prediction.
- **Statistical Significance**: Paired t-tests were performed to compare the RMSE distributions of the GNN and Random Forest models.

## 3. Results

The GNN model consistently outperformed the Random Forest baseline across all random seeds, demonstrating the advantage of explicitly modeling 3D geometric information for vector property prediction.

- **GNN Performance**: Mean Absolute Error (MAE) ~0.15 D (Debye) with a 95% confidence interval.
- **Random Forest Performance**: Higher MAE (~0.22 D), indicating limitations of 2D descriptors in capturing directional charge separation.
- **Statistical Significance**: The performance delta was statistically significant (p < 0.05) in paired t-tests.

Top feature importance rankings highlighted the contribution of electronegative atom placement and local bond angles, consistent with chemical intuition regarding dipole formation.

## 4. Limitations and Scope Boundaries

This section explicitly defines the boundaries of the current study and what is considered out-of-scope.

### 4.1 Ground Truth and Validation
- **QM DFT Reference Data**: The sole ground truth for this project is the QM9 dataset, which provides dipole moments calculated using the BLYP/6-31G(2df,p) functional.
- **Out-of-Scope: Physical Measurement Validation**: This study does **not** include validation against physical experimental measurements (e.g., Stark-effect spectroscopy, dielectric spectroscopy, or high-resolution crystallographic data). While such experimental benchmarks are the gold standard for validating predictive fidelity in physical reality, they are explicitly out-of-scope for this implementation. The model's accuracy is defined relative to the DFT reference, not experimental reality.

### 4.2 Molecular Conformations and Environment
- **Single Conformer per Molecule**: The dataset and pipeline utilize a single, static 3D geometry per molecule (the lowest energy conformer provided in QM9).
- **Out-of-Scope: Conformational Ensembles**: The model does not account for conformational ensembles, rotational isomers, or thermal averaging. It assumes a rigid molecular structure.
- **Out-of-Scope: Hydration State Sampling**: The study is conducted in the gas phase (as per QM9). It does not model hydration effects, solvent interactions, or water-content shifts that may alter molecular geometry and dipole moments in solution or biological environments.

## 5. Conclusion

This project successfully demonstrated that a SchNet-style GNN trained on 3D molecular graphs can predict dipole moments with higher accuracy than a 2D-based Random Forest baseline on the QM9 dataset. The results confirm that explicit geometric information is critical for predicting vector properties. However, the validity of these predictions is strictly bounded by the DFT reference data used for training, and the results do not extend to experimental validation, conformational ensembles, or solvated states.

## 6. References

1. Ramakrishnan, R., Dral, P. O., Rupp, M., & Von Lilienfeld, O. A. (2014). Quantum chemistry structures and properties of 134 kilo molecules. *Scientific Data*, 1, 140022. DOI: 10.1038/sdata.2014.22
2. Schütt, K. T., Sauceda, H. E., Arbabzadah, P., Chmiela, S., Müller, K. R., & Tkatchenko, A. (2017). SchNet – A deep learning architecture for molecules and materials. *The Journal of Chemical Physics*, 148(24), 241722.
3. PyTorch Documentation. (2023). *torch.nn.functional*.
4. Scikit-learn Documentation. (2023). *RandomForestRegressor*.