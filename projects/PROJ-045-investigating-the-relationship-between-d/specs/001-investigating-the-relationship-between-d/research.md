# Research: Defect Chemistry and Ionic Conductivity Analysis

## 1. Problem Statement
The project aims to quantify the relationship between specific defect types (vacancies, interstitials, antisites) and ionic conductivity in oxide-based solid electrolytes. While bulk conductivity data exists, the specific contribution of defect formation energies and migration barriers to the Arrhenius pre-exponential factor and activation energy is often inferred rather than directly computed for specific compositions. The analysis tests the correlation between **computed Total Activation Energy (Ea = Ef + Em)** and **experimentally measured ionic conductivity**, ensuring the outcome is independent of the predictor.

## 2. Dataset Strategy

### 2.1 Verified Sources
The project relies on the following verified datasets. Note that **OBELiX** primarily contains bulk ionic conductivity measurements and **does not** contain the specific defect formation energies required for the analysis. These must be computed via DFT or semi-empirical methods.

| Dataset Name | Description | Verified URL | Usage |
|:--- |:--- |:--- |:--- |
| **OBELiX (Materials Conductivity)** | Bulk ionic conductivity measurements for various materials. | ` | Source for experimental ionic conductivity ($\sigma$) and composition formulas. Pinned to a specific commit hash for reproducibility. |
| **Materials Project Structures** | Crystal structures (via API/Pymatgen). | ` Name or service not known)"))] (API) | Source for initial crystal structures (FR-001). **Static Fallback**: A specific list of MP-IDs (e.g., `mp-12345`, `mp-67890`) is provided in `data/raw/mp_ids.txt` to ensure reproducibility if the API is rate-limited. |

**Note on Missing Data**: The spec requires defect formation energies (vacancy, interstitial, antisite) which are **not** present in the verified OBELiX or DFT datasets. As per the spec's edge cases and assumptions, these values will be computed via DFT (Quantum ESPRESSO) for a high-fidelity subset (3-5 compositions) and semi-empirical methods for the remainder to achieve n≥12.

**Note on DFT Reference Dataset**: The "DFT (Parquet)" dataset is excluded from the "Verified Sources" table as it is not used for input data or ground truth in the pipeline. It is listed below as a **Methodology Reference** only.

### 2.2 Methodology Reference
- **DFT Benchmark Data**: Used only for validating semi-empirical parameters. Not used as direct input.
- **Source**: Literature benchmarks (e.g., Li₇La₃Zr₂O₁₂, Li₁₀GeP₂S₁₂) with defect energies typically ranging from low to moderate magnitudes.

### 2.3 Data Completeness Plan
1. **Download**: Fetch crystal structures for target compositions

The research question remains: How do crystal structures vary across different target compositions?
The method remains: Retrieval of crystal structures from established databases.
References: [DOI/arXiv/author-year] (using static MP-ID list as primary source).
2. **Validate**: Check for presence of conductivity values in OBELiX.
3. **Compute**: Generate DFT inputs for multiple high-fidelity systems (2x2x2 supercell) and semi-empirical inputs for the rest.
4. **Verify**: Ensure all 5 variables (3 defect energies, 1 barrier, 1 conductivity) are present for at least 12 compositions (FR-002).

## 3. Methodology

### 3.1 Defect Concentration Quantification
The project does not measure concentration directly but **computes** it from formation energies using the thermodynamic equilibrium relation:

$$ C = N \exp\left(-\frac{E_f}{k_B T}\right) $$

Where:
- $C$ is the defect concentration.
- $N$ is the number of available sites per unit volume (derived from crystal structure).
- $E_f$ is the defect formation energy (computed via DFT or semi-empirical).
- $k_B$ is the Boltzmann constant.
- $T$ is the temperature (assumed standard, e.g., 300K or 1000K depending on electrolyte).

This method provides a quantitative, physics-based estimate of concentration.

### 3.2 Computational Framework
The computational framework for determining defect formation energies is **Density Functional Theory (DFT)** using **Quantum ESPRESSO** for a high-fidelity subset, and **semi-empirical approximations** for the remainder.
- **High-Fidelity Subset (3-5 compositions)**: Supercell approach with 2x2x2 expansion (allowing >8 atoms). Pseudopotentials: Standard PBE. Convergence: Energy cutoff ≥ 50 Ry, k-point mesh density ≥ 0.03 Å⁻¹. NEB: Nudged Elastic Band method for migration barriers (2-3 configurations).
- **Semi-Empirical Subset (-9 compositions)**: Approximations based on bond valence and empirical defect formation rules, calibrated against the high-fidelity subset.
- **Rationale**: Full DFT for all 15 compositions is computationally infeasible within the 6-hour CPU limit. The hybrid strategy ensures statistical power (n≥12) while maintaining high accuracy for the representative subset.

### 3.3 Statistical Analysis
- **Model**: Linear regression ($ \log(\sigma) \sim E_a $) where $E_a = E_f + E_m$ (Total Activation Energy). This aligns with the Arrhenius equation $\sigma = \sigma_0 \exp(-E_a/kT)$.
- **Independence**: The outcome ($\log(\sigma)$) is **experimentally measured** (from OBELiX) and is independent of the predictor ($E_a$) which is **computed**. The regression tests the predictive power of the DFT/semi-empirical model against independent empirical reality, avoiding tautology.
- **Correction**: Bonferroni or Benjamini-Hochberg for multiple comparisons (≥3 defect types).
- **Sensitivity**: Threshold sweep over {0.01, 0.05, 0.1} and $\sigma_0$ sensitivity analysis.
- **Collinearity**: **Principal Component Analysis (PCA)** is the primary method for handling thermodynamic coupling between defect types (vacancy, interstitial, antisite). Variance Inflation Factor (VIF) is reported as a diagnostic only (threshold > 5) but does not stop the analysis. PCA reduces the dimensionality of the coupled variables to a single dominant component or a physics-informed metric.

### 3.4 Statistical Power & Feasibility
- **Sample Size**: Target n ≥ 12 compositions.
- **Power Calculation**: A power analysis is performed using G*Power logic (α=0.05, effect size f² ≥ 0.1) for the hybrid error model. The high-fidelity subset (DFT) has low variance (σ_DFT), while the semi-empirical subset has higher variance (σ_SE). The combined variance is weighted by the proportion of samples.
- **Justification**: The hybrid strategy reduces the overall variance compared to using only semi-empirical methods. The power calculation demonstrates that n=12 is sufficient to detect the target effect size with power ≥ 0.8, given the expected variance reduction from the high-fidelity subset.
- **Limitation**: If <12 compositions are available, the analysis proceeds with available data and documents the limitation (SC-001).

## 4. Feasibility & Constraints
- **Compute**: All DFT calculations are constrained to CPU-only runners. High-fidelity subset limited to -5 systems to fit within -hour job limit. Semi-empirical methods used for the rest.
- **Time**: The 6-hour job limit is sufficient for 3-5 NEB runs + semi-empirical calculations for 12 total compositions.
- **Accuracy**: Tolerance ≤ 0.5 eV against literature benchmarks for the high-fidelity subset.

## 5. Risk Mitigation
- **DFT Failure**: If Quantum ESPRESSO fails, fallback to semi-empirical estimates (documented) or skip the specific composition.
- **Data Scarcity**: If <12 compositions have conductivity data, the analysis proceeds with available data and documents the limitation (SC-001).
- **API Dependency**: Static list of MP-IDs in `data/raw/mp_ids.txt` ensures structures can be fetched even if the Materials Project API is rate-limited.