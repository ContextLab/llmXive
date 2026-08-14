# Research: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## 1. Research Question & Hypothesis

**Question**: How does the topological structure of atomic defects (specifically, the connectivity of mismatched species pairs) correlate with thermal conductivity in disordered Cu-Ni and Au-Ag alloys?

**Hypothesis**: Higher clustering coefficients and lower percolation thresholds in the defect network will correlate with reduced thermal conductivity due to increased phonon scattering at defect interfaces.

**Scope Clarification**: Due to the unavailability of verified real-world datasets containing both atomic coordinates and thermal conductivity for these specific alloys, this research focuses on **Methodological Validation**. We will generate synthetic data using first-principles physics (Lennard-Jones potentials) to validate the *pipeline's ability* to detect structure-transport correlations, while explicitly acknowledging that the specific material hypothesis remains untested with real data. The synthetic data generation ensures **ensemble independence** through randomized seeds and thermalization steps.

## 2. Dataset Strategy

### 2.1 Verified Sources
Per the project constraints, we must rely **only** on the verified datasets provided in the "Verified datasets" block.

| Dataset Name | Verified URL | Variables Available | Fit for Purpose |
|:--- |:--- |:--- |:--- |
| **NEMD Data (nemdo)** | ` | `ij_link1_0` (thermal conductivity proxy) | **Not Applicable**. Contains thermal conductivity but **NO atomic coordinates or species**. Cannot be used for graph construction. |
| **OpenKim / Materials Cloud** | (Specified in FR-001) | (Unknown/Unverified) | **No Verified Source**. No verified source found for Cu-Ni/Au-Ag + coordinates + conductivity. |
| **Synthetic Data (Generated)** | `code/synthetic.py` | Coordinates, Species, Proxy Conductivity | **Fit for Methodological Validation**. Generates data from first principles with ensemble independence. |

### 2.2 Feasibility Assessment & Gap Analysis
**CRITICAL FINDING**: The specification requires atomic coordinates (x, y, z) and species (Cu, Ni, Au, Ag) to construct the defect graph (FR-002). The **only** verified dataset containing thermal conductivity (`nemdo`) **does not contain atomic coordinates**.

- **Gap**: The dataset-variable fit for the *real-world hypothesis* is **FAILED**. We cannot construct the "DefectGraph" required by the spec for real data because the input data lacks the necessary predictor variables.
- **Action Plan**:
 1. **Phase 0 (Data Audit)**: Attempt to download from OpenKim/Materials Cloud. If missing, log failure.
 2. **Switch to Synthetic Mode**: Generate a synthetic dataset using `ase` (Atomic Simulation Environment) with Lennard-Jones potentials to simulate disordered alloys.
 3. **Independent Conductivity Estimation**: Estimate thermal conductivity in the synthetic dataset using a phonon-scattering model (e.g., Callaway model approximation) based on defect density and mass difference, **NOT** derived from the graph metrics themselves. This avoids tautology.
 4. **Validation**: Use the synthetic data to validate the *methodology* (graph construction, metric extraction, correlation analysis).
 5. **Reporting**: Clearly distinguish between "Real Data Results" (N=0, failed) and "Synthetic Validation Results" (Methodology validated).

*Note: No synthetic data is used to claim real-world physics; it is used to validate the pipeline's statistical and graph-theoretic integrity.*

## 3. Methodology

### 3.1 Data Ingestion & Graph Construction
- **Real Data Input**: MD Snapshot (CSV/Parquet with `x`, `y`, `z`, `species`).
- **Synthetic Input**: Generated via `ase` with Lennard-Jones potentials (randomized alloy composition).
- **Algorithm**:
 1. Parse atomic positions and species.
 2. Compute Voronoi tessellation (using `scipy.spatial.Voronoi`).
 3. Identify nearest neighbors for each atom.
 4. Create edges **only** between neighbors of **different** species.
 5. Construct `networkx.Graph`.
- **Error Handling**: If coordinates are missing in real data, raise `DataAvailabilityError`.

### 3.2 Topological Metric Extraction
- **Metrics**:
 - Clustering Coefficient ($C$): Average of local clustering coefficients.
 - Mean Degree ($\langle k \rangle$): Average node degree.
 - Degree Variance ($\sigma_k^2$): Variance of the degree distribution.
 - Percolation Threshold ($p_c$): Estimated via `networkx.algorithms.approximation.percolation_threshold` on the largest connected component.
- **Robustness**:
 - If graph is disconnected, calculate $p_c$ only on the largest component.
 - If no edges exist, return `NaN` and log a warning.

### 3.3 Statistical Analysis
- **Correlation**: Pearson ($r$) and Spearman ($\rho$) between each metric and thermal conductivity.
- **Significance Testing**:
 - Calculate raw p-values.
 - Apply **Bonferroni Correction**: $p_{adj} = p_{raw} \times m$ (where $m$ is the number of metrics tested).
 - Significance threshold: $p_{adj} < 0.05$.
- **Power Analysis**:
 - Post-hoc power calculation for the observed correlation coefficient and sample size ($N$).
 - For Synthetic Mode: N=50.
 - For Real Data Mode (N=0): Report "Insufficient Data for Power Analysis".
 - If N < 20, explicitly flag low power.

### 3.4 Sensitivity Analysis (SC-004)
- **Task**: Sweep significance threshold (p < 0.01, 0.05, 0.10).
- **Check**: Verify rank-order stability of correlation coefficients (change < 0.1).
- **Output**: Report stability of conclusions across thresholds.

### 3.5 Visualization
- Scatter plots (Metric vs. Thermal Conductivity) with regression lines.
- Correlation heatmap (Metrics vs. Thermal Conductivity).
- Resolution: 300 DPI, saved as PNG.

## 4. Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied to control Family-W Error Rate (FR-006).
- **Causal Inference**: Results are **associational** only. No randomization exists; we cannot claim causality.
- **Collinearity**: Metrics like mean degree and variance are mathematically related. We will report them separately but acknowledge the lack of independence in the interpretation.
- **Sample Size**: Assumed N=50 (Synthetic). Power analysis is mandatory (FR-007).
- **Null Hypothesis**: $H_0: \rho = 0$ (no correlation).
- **Synthetic Data Assumption**: The synthetic data generation (LJ potentials) approximates the physical behavior of disordered alloys sufficiently to validate the *methodology*, but does not claim to replicate exact real-world values.
- **Ensemble Independence**: Synthetic snapshots are generated with unique random seeds and thermalization steps to ensure statistical independence, addressing the concern that a single snapshot may not represent the bulk property.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Dual-Mode Execution** | Real data is unavailable. Synthetic data allows methodological validation without fabricating real-world results. |
| **CPU-First** | Graph construction and correlation on N=50 is trivial for CPU. No GPU needed. |
| **Bonferroni over FDR** | Spec (FR-006) explicitly requires Bonferroni for strict control in high-dimensional topological analysis. |
| **Independent Conductivity Model** | Ensures synthetic conductivity is not a mathematical identity of the graph metrics, preserving statistical validity. |
| **Sensitivity Analysis** | Required by SC-004 to ensure robustness of conclusions against arbitrary threshold selection. |

## 6. Risk Register

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Atomic Coordinates** | **Fatal** for real data. | System halts with clear error; switches to synthetic mode for validation. |
| **Small Sample Size (N < 20)** | Low statistical power. | Power analysis reported; results qualified as "exploratory". Synthetic mode uses N=50. |
| **Disconnected Graphs** | Undefined $p_c$. | Calculate on largest component; report NaN if no edges. |
| **Tautological Correlation** | Invalid science. | Synthetic conductivity derived from independent phonon model, NOT graph metrics. |
| **Lack of Ensemble Independence** | Invalid statistics. | Synthetic generation uses unique seeds and thermalization steps to ensure independence. |
