# Research: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

## Dataset Strategy

| Dataset Name | Purpose | Source URL (Verified) | Loading Method |
|:--- |:--- |:--- |:--- |
| **QM9 (Full)** | Primary training data (Atomic/Bond properties + HOMO-LUMO gap) | ` | `pandas.read_parquet` |
| **QM9 (Enthalpy)** | Secondary target validation (optional) | ` | `pandas.read_parquet` |
| **QM9 (Gaps)** | Target variable verification (HOMO-LUMO gap) | ` | `pandas.read_parquet` |
| **Reactive Substructures** | Ground truth for interpretability (FR-008) | *Static Asset* (Local `data/assets/reactive_substructures.csv`) | `pandas.read_csv` |
| **Kinetic Data** | Proxy validation (FR-009) | *Static Asset* (Local `data/assets/kinetic_rates.csv`) | `pandas.read_csv` |

**Dataset Fit Verification**:
The QM9 dataset (verified sources above) contains:
* **Predictors**: Atomic number, hybridization, formal charge, bond type, conjugation (via SMILES parsing).
* **Outcome**: HOMO-LUMO gap (DFT-calculated).
* **Covariates**: Molecular weight, number of atoms.
* **Fit**: **Confirmed**. The dataset contains all variables required for the FR-001 to FR-006 plan. The "DFT-calculated" target is present in the `gaps-qm9-1k` or `full` QM9 sources.

**Note on DFT Source**: The spec mentions "DFT-calculated" properties. The verified QM9 datasets *are* the source of these DFT values (computed previously). No external "DFT-calculated" dataset URL exists in the verified block; we rely on the QM9 sources which *contain* these pre-computed values.

## Model Architecture Rationale

1. **Spectral GNN**:
 * **Why**: Operates in the spectral domain (graph Fourier transform), effective for capturing global molecular properties.
 * **CPU Feasibility**: Uses fixed eigendecomposition (can be pre-computed or approximated) and lightweight matrix multiplications. Avoids deep recursion of message passing.
2. **Heterophily-aware GNN (VR-GNN principles)**:
 * **Why**: Molecular graphs often exhibit **heterophily** (connected atoms have different properties, e.g., C bonded to O). Standard GNNs smooth features, losing this contrast.
 * **Mechanism**: Uses higher-order neighborhood aggregation or specialized message passing that does not assume feature similarity between neighbors.
3. **Random Forest Baseline**:
 * **Why**: Robust, non-parametric, and highly efficient on CPU. Morgan fingerprints provide a strong, standard benchmark for "hand-crafted" descriptors.

## Statistical Analysis Plan

* **Primary Metric**: Pearson Correlation Coefficient ($R$) between predicted and actual HOMO-LUMO gap.
* **Secondary Metric**: Mean Squared Error (MSE) and Mean Absolute Error (MAE).
* **Statistical Test**:
 * **Primary**: **Wilcoxon signed-rank test** on prediction errors (GNN vs. RF). This non-parametric test is chosen because molecular regression residuals (QM9) are often heteroscedastic and non-normal, violating t-test assumptions.
 * **Sensitivity**: **Paired t-test** (FR-006) performed as a secondary check. If the t-test and Wilcoxon results diverge, the Wilcoxon result is reported as the primary finding.
 * *Null Hypothesis*: The median difference in prediction errors between GNN and RF is zero.
 * *Correction*: Bonferroni correction applied for multiple comparisons ($\alpha_{adj} \approx 0.016$).
* **Proxy Validation (SC-006)**:
 * The correlation between HOMO-LUMO gap (thermodynamic) and experimental reaction rates (kinetic) is **not** treated as a universal law.
 * **Scope**: Validation is restricted to the subset of molecules in the external kinetic dataset where the reaction mechanism is known to be dominated by frontier orbital interactions (e.g., nucleophilic attacks on carbonyls).
 * **Metric**: Mechanism-consistent correlation coefficient.
* **Interpretability Validation**:
 * **Ground Truth Independence**: The "Curated Reference Set" (FR-008) must be sourced from **experimental literature** or distinct quantum chemistry benchmarks, explicitly excluding any data derived from the QM9 DFT calculations to prevent circular validation.
 * **Metric**: Alignment score between top-5 attributed subgraphs and the curated reference set.
 * **Threshold**: $\ge 0.7$ (SC-003).

## Risk Assessment

1. **Memory Overflow**: Graph construction for full QM (a large-scale molecular dataset) may exceed 4GB RAM.
 * *Mitigation*: Process in batches; limit training set to 10k-20k molecules if necessary. Log memory usage every epoch.
2. **Runtime Exceedance**: Training 50 epochs for 3 models on 2 CPUs may take > 6 hours.
 * *Mitigation*: Use early stopping (patience=5). Reduce epochs if convergence is early.
3. **Dataset Mismatch**: If HOMO-LUMO gap is missing from a specific QM9 shard.
 * *Mitigation*: Cross-reference `full` and `gaps` datasets. If missing, fall back to HOMO or LUMO individually (less ideal but viable).
4. **Statistical Assumption Failure**: If residuals are heavily skewed.
 * *Mitigation*: The primary Wilcoxon test is robust to non-normality. The plan explicitly prioritizes this over the t-test for the primary claim.
5. **Circular Validation**: Risk of validating attribution against training-derived data.
 * *Mitigation*: Strict provenance check in Phase 3 to ensure the reference set is independent of QM9.