# Research: Predicting Molecular Dipole Moments with Graph Neural Networks

## 1. Research Question & Hypothesis

**Primary Question**: To what extent does 3D conformational geometry provide independent predictive information for molecular dipole moments beyond 2D connectivity and atom types?

**Hypothesis**: 3D conformational geometry (bond angles, dihedrals, spatial arrangement) contains significant predictive signal for molecular dipole moments that cannot be fully captured by 2D connectivity (Morgan fingerprints, topological counts) and atom types alone. We hypothesize that a 3D-equivariant GNN (SchNet) will achieve statistically significantly lower Mean Absolute Error (MAE) than a 2D-only Random Forest baseline.

## 2. Dataset Strategy

### 2.1 Primary Dataset: QM9
The QM9 dataset is the selected source for this study. It contains [deferred]+ small organic molecules with computed quantum mechanical properties, including dipole moments (Debye), at the B3LYP/6-31G(2df,p) level of theory.

*   **Source Verification**: The dataset is available via the PyTorch Geometric `QM9` dataset loader. This is the canonical source for this project.
*   **Feasibility Check**: This dataset is directly downloadable via the `torch_geometric` loader, making it feasible for the GitHub Actions CI runner (no credentials required).
*   **Variable Fit**:
    *   **Target**: `mu` (Dipole moment magnitude) - Present.
    *   **Predictors**: `z` (atom types), `pos` (3D coordinates), `edge_index` (connectivity) - Present.
    *   **2D Descriptors**: Morgan fingerprints and topological counts can be generated from `z` and `edge_index`.
*   **Limitation Acknowledgement**: As per the project assumptions, QM9 contains gas-phase DFT calculations. Hydration effects and experimental physical measurements are out-of-scope. The ground truth is the DFT calculation, not a physical experiment.

### 2.2 Data Sampling Strategy
The full QM9 dataset (~134k molecules) may exceed the 6-hour runtime budget on a 2-core CPU when training a GNN 5 times.
* **Strategy**: A random subset of [deferred] molecules will be drawn with a fixed seed (e.g., `seed=42`).
* **Stratification**: To ensure representation, the subset is selected by stratifying the full dataset into 10 bins based on dipole moment magnitude and sampling [deferred] molecules from each bin.
* **Train/Test Split**: The [deferred] molecules are split 80/20 ([deferred] train, [deferred] test) using a random split **within each stratum** to prevent distributional shift bias.
*   **Rationale**: This size is sufficient for statistical power in paired t-tests (SC-004) while ensuring the 6-hour constraint (SC-003) is met. The subset will be stratified by dipole moment magnitude to ensure representation of low and high dipole species.

## 3. Methodology

### 3.1 Feature Extraction
1.  **2D Descriptors (Baseline - Strictly 2D)**:
    *   **Morgan Fingerprints**: Generated using RDKit with radius=2 and nBits=2048. Captures local subgraph connectivity.
    *   **Topological Counts**: Number of atoms, bonds, and specific atom types.
    *   **Exclusion**: **No** Coulomb matrices or pairwise distances are used for the baseline. These are 3D-derived features and would invalidate the comparison.
2.  **3D Descriptors (GNN Input)**:
    *   **Atomic Coordinates**: 3D positions (Angstroms) from QM9.
    *   **Graph Structure**: Nodes = atoms, Edges = bonds (from QM9 connectivity).
    *   **Equivariance**: The SchNet model will use distance-based message passing to ensure rotational invariance of the output.

### 3.2 Models
1.  **Baseline: Random Forest Regressor**:
    *   Input: Morgan fingerprints and topological counts (strictly 2D).
    *   Hyperparameters: `n_estimators=500`, `max_depth=None`.
    *   Rationale: Robust, non-parametric baseline that captures non-linear relationships in 2D/topological features.
2.  **Experimental: SchNet-style GNN**:
    *   Architecture: Continuous-filter convolutional layers.
    *   Input: Atom types (one-hot), 3D positions, edge indices.
    *   Output: Scalar dipole moment.
    *   Constraint: Lightweight configuration (2 interaction blocks, 64 hidden units) to fit within CPU time limits.

### 3.3 Statistical Analysis
*   **Metrics**: Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).
* **Hypothesis Testing**: Paired t-test (α=0.05) on the distribution of **per-molecule absolute errors** (N [deferred]) for each seed.
*   **Confidence Intervals**: 95% CI computed via bootstrapping (1000 resamples) on the per-molecule error distribution within the test set for each seed. Reference: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics).
*   **Aggregation**: The 5 random seeds are used to compute the mean and 95% CI of the MAE/RMSE metrics and to verify that the t-test p-value is consistently <0.05 across all seeds (SC-004).
*   **Multiple Comparison Correction**: Not required as the primary comparison is a single paired test (GNN vs. RF) per seed.

## 4. Decision / Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-First Execution** | The project constraints (6h, 2 CPU) require a lightweight model. A full-scale SchNet on 134k molecules is infeasible on CPU. A 10k subset with 2 interaction blocks is a faithful CPU-tractable form. |
| **QM9 DFT as Ground Truth** | FR-011 explicitly states physical measurement validation is out of scope. QM9 provides high-quality DFT reference data. No experimental benchmark is available or authorized. |
| **Subset Sampling** | Streaming the full dataset is possible, but training 5 GNN epochs on 134k molecules on 2 CPU cores will likely exceed 6 hours. A random subset ensures the pipeline completes while maintaining statistical validity. |
| **No Angle-Aware Layers** | The spec calls for a "lightweight SchNet-style GNN" (FR-004). Adding explicit angle-aware layers (as suggested in rejected tasks) constitutes scope creep and violates the "lightweight" constraint. SchNet's distance-based convolution is sufficient for the research question. |
| **Strictly 2D Baseline** | The baseline uses ONLY 2D features (Morgan fingerprints, topological counts) to ensure a valid comparison. Including 3D-derived features (Coulomb matrices) would invalidate the research question. |

## 5. Limitations & Assumptions

*   **Hydration State**: QM9 molecules are gas-phase; hydration effects are ignored.
*   **Conformational Ensembles**: Only the lowest-energy conformer per molecule is used. Ensemble sampling is future work.
*   **Physical Validation**: The model predicts DFT-calculated dipole moments, not experimental values. This is a known limitation per FR-011.
* **Compute Budget**: The 6-hour limit is a hard constraint. If the subset size causes timeouts, the subset will be reduced to [deferred] molecules, with a note on the resulting power reduction.