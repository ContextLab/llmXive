# Research: Predicting Molecular Dipole Moments with Graph Neural Networks

## 1. Research Question & Hypothesis

**Primary Question**: To what extent does 3D conformational geometry provide independent predictive information for molecular dipole moments beyond 2D connectivity and atom types?

**Hypothesis**: 3D conformational geometry provides statistically significant independent predictive information for molecular dipole moments compared to 2D connectivity alone, particularly for molecules with polar functional groups and specific bond angles.

**Rationale**: Dipole moments are vector quantities dependent on the spatial arrangement of charge. While 2D connectivity defines atom types and bond orders, it lacks the geometric information (bond angles, dihedral angles) necessary to fully determine the net dipole vector. Graph Neural Networks (GNNs) like SchNet are designed to be 3D-equivariant/invariant and should capture these spatial features, whereas 2D descriptors (Morgan fingerprints) and non-geometric baselines (Topological Coulomb matrices) may miss critical directional information.

## 2. Dataset Strategy

### 2.1 Dataset Selection: QM9
The QM9 dataset is the standard benchmark for small organic molecules with quantum mechanical properties. It contains a large set of molecules with equilibrium geometries and dipole moments calculated at the B3LYP/6-31G(2df,p) level.

**Variable Fit Verification**:
* **Predictors**: The dataset contains D coordinates (x, y, z for each atom), atom types (C, N, O, F, H), and bond connectivity.
* **Outcome**: The dataset explicitly includes the dipole moment vector (μx, μy, μz) and magnitude (μ).
* **Fit**: The dataset contains ALL required variables. No synthetic substitution is needed.

### 2.2 Source & Access
* **Canonical Reference**: DOI `10.1038/sdata.2014.22` (McGibbon et al., 2014).
* **Verified Download Source**: Per the project's "Verified datasets" block, the DOI has no direct verified URL. However, verified Hugging Face mirrors exist.
 * **Primary Source**: `
* **Dataset Verification**: The mirror `lisn519010/QM9` has been verified to contain the full 134k molecules with the required columns (`dipole_vector`, `coordinates`, `atom_numbers`). The schema matches the QM9 specification.

### 2.3 Data Handling & Preprocessing
* **Streaming**: To respect the 8GB RAM constraint, the pipeline will use `streaming=True` where possible or load in chunks.
* **Missing Coordinates**: Molecules with missing 3D coordinates will be flagged and excluded. A report `data/reports/excluded_molecules.csv` will be generated (addressing FR-002, User Story 1).
* **Subset**: A random subset of **[deferred] molecules** will be used to ensure the pipeline completes within 6 hours on 2 vCPUs.
* **Normalization**: Coordinates will be centered at the origin. Dipole magnitudes will be normalized.

### 2.4 Addressing Reviewer Concerns (Physical Reality)
* **Concern**: Validation against physical reality (X-ray/dielectric data) is missing.
* **Response**: The spec explicitly states: "Physical measurement validation is out of scope... validation will use QM9 quantum calculation reference data as the ground truth standard." QM9 dipole moments are derived from DFT (B3LYP), which is the accepted computational ground truth for this class of molecules. Experimental validation is a downstream requirement, not a feature requirement. The plan adheres to the spec's scope.

## 3. Methodology

### 3.1 Feature Engineering
* **3D Features**:
 * Atom types (one-hot).
 * 3D coordinates (relative distances).
 * SchNet edge features (Gaussian expansion of inter-atomic distances).
* **2D Features (Baseline)**:
 * Morgan Fingerprints (radius=2, nBits=2048).
 * **Topological Coulomb Matrices**: Eigenvalues of the Coulomb matrix constructed using **graph distances** (topological path lengths) instead of Euclidean distances. This ensures the baseline is strictly 2D and does not leak 3D geometric information.
 * *Note*: Standard Coulomb matrices (using Euclidean distances) are excluded from the 2D baseline to prevent construct validity failure.

### 3.2 Models
* **GNN (SchNet)**:
 * Architecture: Lightweight SchNet (2 interaction blocks, 32 hidden units).
 * Implementation: PyTorch Geometric (`torch_geometric.nn`).
 * Mode: CPU-only (default precision).
 * *GPU Escape Hatch*: If the model fails to converge or exceeds time limits on CPU, the pipeline will detect CUDA availability (if offloaded to Kaggle) and re-run with `device="cuda"` and 8-bit quantization. However, the primary plan is CPU-tractable.
* **Baseline (Random Forest)**:
 * Algorithm: `sklearn.ensemble.RandomForestRegressor`.
 * Inputs: Concatenation of Morgan fingerprints and Topological Coulomb matrix eigenvalues.
 * Hyperparameters: `n_estimators=100`, `max_depth=None`.
* **Ablation Variants**:
 * **SchNet-Randomized**: SchNet trained with shuffled 3D coordinates (breaks geometry signal).
 * **SchNet-2D**: SchNet architecture trained **without** 3D coordinates (only 2D features).
 * **RF-Combined**: Random Forest trained on 2D + 3D features.

### 3.3 Training Protocol
* **Splits**: Random 80/10/10 (Train/Val/Test). **No stratification by dipole magnitude** to avoid data leakage.
* **Seeds**: 5 independent random seeds (e.g., 42, 123, 456, 789, 1011).
* **Epochs**: 50 epochs with early stopping (patience=10).
* **Metrics**: MAE, RMSE (computed on the test set).
* **Statistical Test**: **Wilcoxon signed-rank test** (α=0.05) on the RMSE distributions across the 5 seeds to determine if the GNN outperforms the baseline significantly. **Bootstrap confidence intervals** (1000 resamples) will be computed for the performance difference.

### 3.4 Interpretability
* **Random Forest**: Permutation Importance (scikit-learn).
* **GNN**: **Input Gradients** (gradient of output w.r.t. input coordinates) and **Integrated Gradients**. This correctly attributes importance to the 3D geometry, as requested by the research question.
* **Output**: Top 3 structural features (atoms/bonds) contributing to prediction variance.

## 4. Statistical Rigor & Power

* **Multiple Comparisons**: Only one primary hypothesis test (GNN vs. RF) is performed. Bonferroni correction is not strictly required for a single test, but the t-test will be two-tailed.
* **Sample Size / Power**:
 * QM9 has ~134k molecules. A sample of [deferred] is sufficient for regression tasks with low variance.
 * *Power Limitation*: If the effect size (difference in MAE) is small, 5 seeds might yield wide confidence intervals. The plan acknowledges this limitation and reports the CI width.
* **Causal Inference**: The study uses an **ablation design** (randomizing 3D coords) to support causal claims regarding the contribution of geometry. Claims are framed as "causal contribution of geometry" based on the ablation results.
* **Collinearity**: 2D and 3D features are not definitionally collinear (2D is connectivity, 3D is geometry). However, 3D features are derived from the same atoms. The plan reports feature importance descriptively.

## 5. Compute Feasibility

* **CPU-First**: SchNet with 32 hidden units and 5k samples is computationally feasible on 2 vCPUs within 6 hours.
* **Memory**: Streaming and chunked processing ensure <8GB RAM usage.
* **GPU Escape Hatch**: If the CPU run exceeds the 6h limit, the runner will auto-offload to Kaggle GPU. The plan includes a `device` flag that defaults to `cpu` but switches to `cuda` if available, with a reduced batch size to fit ~16GB VRAM.

## 6. Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Use Hugging Face QM9** | Verified URL exists; DOI has no direct link. Ensures CI reproducibility. |
| **Topological Coulomb Matrices** | Ensures the 2D baseline is strictly 2D and does not leak 3D geometric information. |
| **SchNet (CPU) + RF** | SchNet is 3D-aware; RF is a strong 2D baseline. Both run on CPU. |
| **Ablation Variants** | Required to causally isolate the 3D geometry signal. |
| **Wilcoxon Test + Bootstrap** | Robust statistical test for small sample size (n=5) and non-normality. |
| **Input Gradients** | Correctly attributes importance to 3D geometry for the GNN. |
| **Random Splits** | Avoids data leakage from target-value stratification. |
| **Exclude Missing Coords** | Required by User Story 1 (edge case). |
| **No Physical Benchmarks** | Spec explicitly excludes experimental validation (Assumptions). |