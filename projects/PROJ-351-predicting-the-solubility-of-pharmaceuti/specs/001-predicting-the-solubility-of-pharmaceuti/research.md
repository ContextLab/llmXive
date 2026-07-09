# Research: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## 1. Problem Definition & Hypothesis

**Problem**: Predict aqueous solubility (logS) of pharmaceutical compounds.
**Hypothesis**: Graph Neural Networks (GNNs), specifically Message Passing Neural Networks (MPNN), will capture topological and electronic features of molecules better than fixed descriptors (Morgan fingerprints) used in Random Forest baselines, resulting in a statistically significant reduction in RMSE.
**Null Hypothesis**: There is no statistically significant difference in prediction error between the MPNN and Random Forest models on the ESOL dataset.

## 2. Dataset Strategy

The ESOL (Delaney) dataset is the canonical source for this task. It contains a substantial collection of molecules with experimental logS values and SMILES strings.

| Dataset Name | Source URL (Verified) | Usage | Validation Status |
|--------------|-----------------------|-------|-------------------|
| ESOL (MoleculeNet) | ` | Primary training/evaluation data. Contains `smiles` and `logS`. | **Verified**: URL accessible; format CSV; contains required columns. |
| SMILES Sample | ` | Optional: Sanity check for RDKit parsing robustness. | **Verified**: URL accessible. |

**Data Fit Confirmation**:
- **Required Variables**: `smiles` (input), `logS` (target).
- **Dataset Content**: The ESOL dataset explicitly provides `smiles` and `logS`.
- **Missing Variables**: None. The spec assumes no additional variables (pH, temperature) are needed.
- **Conclusion**: The ESOL dataset is a perfect fit for the defined analysis.

## 3. Methodology

### 3.1 Data Preprocessing & Splitting

1. **Download**: Fetch CSV from the verified HuggingFace URL.
2. **Cleaning**:
 - Parse SMILES using `rdkit.Chem.MolFromSmiles`.
 - Exclude rows where `MolFromSmiles` returns `None` (invalid syntax).
 - Exclude rows where `logS` is `NaN`.
 - **Log**: Record count of excluded rows (Constitution Principle VI).
3. **Scaffold-Based Splitting (Critical)**:
 - **Strategy**: Replace random/quantile splitting with a **Murcko Scaffold Split**.
 - **Method**: Extract the Bemis-Murcko scaffold for each molecule using RDKit.
 - **Allocation**: Group molecules by scaffold. Assign scaffolds to Train/Val/Test sets using a standard split ratio to ensure that no scaffold appears in both training and test sets.
 - **Rationale**: This prevents "data leakage" where the model memorizes similar structures rather than learning generalizable chemical rules. It ensures the test set represents a true generalization challenge.
 - **Constraint**: If a scaffold is too large, it may force an imbalance; we will enforce a minimum scaffold count threshold and log any exclusions.

### 3.2 Feature Engineering

1. **Baseline (Random Forest)**:
 - Convert SMILES to Morgan Fingerprints (radius=2, 2048 bits) using `rdkit.Chem.AllChem.GetMorganFingerprintAsBitVect`.
 - Input: Binary vector.
2. **GNN (MPNN) - Raw Graph**:
 - Convert SMILES to `rdkit.Chem.rdchem.Mol`.
 - Extract atom features: Atomic number, hybridization, formal charge, aromaticity.
 - Extract bond features: Bond type, conjugation, stereochemistry.
 - Convert to `torch_geometric.data.Data` object.
3. **GNN (MPNN) - Fixed Features (Ablation)**:
 - **Purpose**: To isolate the contribution of "message passing" from "feature representation."
 - **Method**: Use the same Morgan Fingerprints (radius=2, 2048 bits) as the *node features* for the GNN, rather than raw atomic properties.
 - **Rationale**: If the "Raw Graph" GNN outperforms the "Fixed Features" GNN, the improvement is due to message passing. If they are equal, the baseline RF might be sufficient, or the GNN isn't learning topology.

### 3.3 Model Architectures

1. **Random Forest**:
 - Library: `scikit-learn`.
 - Hyperparameters: `n_estimators=100`, `max_depth=None`, `random_state=42`.
 - **Rationale**: Standard baseline, fast on CPU, robust to noise.
2. **Message Passing Neural Network (MPNN) - Raw Graph**:
 - Library: `torch_geometric`.
 - Architecture: Multiple Message Passing layers (GCNConv), 128 hidden units, ReLU activation.
 - **Constraint**: Must run on CPU (`device='cpu'`). No CUDA calls.
 - **Rationale**: Simplified architecture to ensure convergence within 6 hours on 2 vCPU.
3. **Message Passing Neural Network (MPNN) - Fixed Features**:
 - Architecture: Same as above, but input node features are the 2048-bit Morgan fingerprint vectors (possibly projected to 128 dimensions via a linear layer to reduce input size).
 - **Rationale**: Controls for feature quality vs. architecture.

### 3.4 Statistical Analysis & Validation

1. **Metrics**: RMSE, R-squared for all models.
2. **Validation Strategy**:
 - **Primary**: **Scaffold Split** (80/10/10) to ensure independence of test data.
 - **Secondary**: **5x2 Cross-Validation** (stratified by scaffold) to estimate variance, but final significance testing uses the held-out test set to avoid overfitting the CV folds.
3. **Significance Test (Cluster-Robust)**:
 - **Problem**: Standard t-tests assume independent errors. In chemistry, errors are correlated within structural clusters (scaffolds).
 - **Solution**: **Scaffold-Aware Permutation Test**.
 - Calculate the observed difference in RMSE (or MAE) between GNN and RF on the test set.
 - Permute the *labels* (logS values) **within** each scaffold cluster in the test set to generate a null distribution of error differences.
 - Compute the p-value as the proportion of permuted differences that are as extreme as the observed difference.
 - **Rationale**: This respects the dependency structure of the data and provides a valid p-value even when errors are not independent.
 - **Normality Check**: Perform Shapiro-Wilk test on error differences. If non-normal, report Wilcoxon signed-rank p-value as a secondary robustness check.
4. **Power Analysis (A Priori & Exploratory)**:
 - **Constraint Acknowledgement**: With N ≈ 112, the study is underpowered to detect small effect sizes (Cohen's d < 0.4).
 - **Strategy**: Instead of a misleading post-hoc power calculation, we will perform a **simulation-based Minimum Detectable Effect Size (MDES)** analysis.
 - Simulate 1000 datasets of size N=112 with known effect sizes.
 - Determine the effect size required to achieve 80% power at alpha=0.05 given the observed variance.
 - **Reporting**: If the result is non-significant, we will explicitly state: "The study was exploratory; the minimum detectable effect size was X. We cannot rule out small improvements."

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (limited CPU, 7GB RAM, 14GB Disk, No GPU).
- **Time Budget**: ≤ 6 hours.
- **Mitigation Strategies**:
 - **Dataset Size**: ESOL is small. No sampling required.
 - **Model Size**: MPNN limited to -3 layers and 128 hidden units.
 - **Library Pins**: Explicitly pin `torch` to a CPU-only wheel version.
 - **Early Stopping**: Prevents wasted compute on non-converging models.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **GNN Fails to Converge** | High (No results) | Early stopping; fallback to reporting baseline only if GNN loss diverges; log error. |
| **Memory Overflow** | High (Job Kill) | Process data in chunks if needed; limit batch size to 1 (since dataset is small); monitor RAM. |
| **SMILES Parsing Errors** | Medium (Data Loss) | Log and exclude; if >5% loss, flag data quality issue. |
| **Baseline > GNN** | Low (Negative Result) | Report honestly; interpret as "fixed descriptors sufficient for this small dataset." |
| **Low Statistical Power** | Medium (Inconclusive) | Report MDES; acknowledge limitation; do not claim "no difference" if p > 0.05. |
| **Scaffold Imbalance** | Medium (Data Skew) | If a single scaffold dominates, report distribution; ensure test set has at least 5 distinct scaffolds. |

## 6. Decision Rationale

- **Why CPU-only?** The spec and CI constraints mandate free-tier execution. GPU methods are infeasible.
- **Why Scaffold Split?** Random splits in cheminformatics often leak structural information, inflating performance. Scaffold splits are the gold standard for generalization testing.
- **Why Permutation Test?** Standard t-tests fail when errors are correlated (structural clusters). Permutation tests respect the data structure.
- **Why Ablation Study (GNN-FP)?** To distinguish whether the GNN is learning *topology* or just memorizing *features* provided by the fingerprint.
- **Why Simulation-based Power?** With N=112, standard power calculations are unstable. Simulation provides a realistic estimate of what the study can detect.