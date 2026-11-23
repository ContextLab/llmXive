# Research: Predicting Glass Formation Tendency with Machine Learning on Public Data

## 1. Problem Definition & Hypothesis

**Research Question**: Can atomic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) computed from chemical composition predict the glass formation tendency (critical casting thickness $D_c$ or binary glass/crystal label) of metallic alloys?

**Hypothesis**: A small set of top descriptors identified by the model will align with established materials science theories (e.g., Inoue's Rules), specifically highlighting "Mixing Enthalpy" and "Atomic Size Mismatch" as dominant predictors.

**Causal Framing**: All findings will be framed as **associational**. The data is observational; no causal claims (e.g., "X causes Y") will be made. The report will explicitly state the limitations of causal inference.

## 2. Dataset Strategy

### Primary Source
- **Source**: Verified Experimental Dataset (Figshare).
- **Content**: Raw experimental critical casting thickness ($D_c$) and/or binary glass/crystal labels.
- **Access**:
 - **Automated**: Attempt download via verified API/URL.
 - **Manual Fallback**: If API fails (auth/network), the pipeline expects `data/raw/glass_data.csv` to be pre-placed by the user. This satisfies Constitution Principle I (Reproducibility) by ensuring the exact same data file is used regardless of network status.
- **Data Quality Gate**: The dataset MUST contain raw experimental $D_c$ values or empirically observed binary labels. Datasets containing only calculated descriptors or predicted scores are rejected.

### Data Verification & Integrity
- **Checksum**: SHA-256 of the processed dataset will be computed and stored in `state/`.
- **Validation**:
 - **A Priori Power**: Minimum $N \ge 77$ recommended for medium effect size ($f^2=0.15$).
 - **Hard Minimum**: $N \ge 30$. If $N < 30$, halt with `DataValidationError`.
 - **Underpowered Range**: If $30 \le N < 77$, proceed with a `PowerWarning` and report MDES.
 - **Chemical Balance**: Sum of atomic percentages must be within ±1% of [deferred].
 - **Missing Variable**: Rows with missing target or descriptors are dropped; missing entire columns halt execution.

### Variable Mapping
| Variable | Type | Source/Computation |
|:--- |:--- |:--- |
| `composition` | String | Raw input (e.g., "Zr50Cu40Al10") |
| `chemical_family` | String | Derived: Majority element (e.g., "Zr-based") |
| `D_c` | Float | Direct from dataset (Regression target) |
| `label` | Binary | Direct from dataset (Classification target) |
| `delta_atomic_size` | Float | Computed via `pymatgen` (Std Dev of radii) |
| `delta_enthalpy` | Float | Computed via `pymatgen` (Weighted avg) |
| `delta_electronegativity` | Float | Computed via `pymatgen` (Variance) |

## 3. Methodology

### Feature Engineering (Descriptor Computation)
Using `pymatgen`, compute the following descriptors for every composition:
1. **Atomic Size Mismatch ($\delta$)**: $\delta = \sqrt{\sum c_i (1 - \frac{r_i}{\bar{r}})^2}$.
2. **Mixing Enthalpy ($\Delta H_{mix}$)**: $\Delta H_{mix} = \sum_{i \neq j} 4 c_i c_j \Delta H_{ij}^{mix}$.
3. **Electronegativity Difference ($\Delta \chi$)**: Variance of electronegativity weighted by atomic fraction.
*Note*: All descriptors must be non-null. If an element is unknown to `pymatgen`, the sample is flagged and excluded.

### Model Training & Validation
- **Algorithm**: XGBoost (Gradient Boosting) by default.
- **Collinearity Fallback**: If VIF > 10, switch to **Ridge Regression**. If VIF > 30, use **PCA**.
- **Mode Selection**:
 - If $D_c$ is present: Regression (Target: $D_c$).
 - Else if binary label is present: Classification (Target: Glass/Crystal).
 - Else: Halt with `DataValidationError`.
- **Cross-Validation**: **Adaptive Leave-One-Group-Out (LOGO) CV**.
 - **Standard**: Train on all chemical families except one, test on the left-out family. Repeat for all families.
 - **Rationale**: The "chemical family" is derived from the majority element (e.g., "Zr-based"), which serves as a physically meaningful proxy for the matrix packing efficiency driving glass formation.
- **Constraints**:
 - CPU-only execution.
 - Max runtime 6 hours (target < 30 mins).
 - Random seed: fixed for reproducibility.

### Statistical Rigor & Diagnostics
1. **Power Analysis**:
 - **A Priori**: Calculate required $N$ for $f^2=0.15$, $\alpha=0.05$, Power=0.80. **Result**: N=77.
 - **Post-Hoc**: Calculate MDES and achieved power. Report if Power < 0.80 (i.e., if N < 77).
2. **Collinearity**: Variance Inflation Factor (VIF) for top predictors. If VIF > 10, switch model to Ridge.
3. **Circularity Check (Robust, Relative)**:
 - **Permutation Test**: Train model on shuffled targets (multiple iterations).
 - **Threshold**: If Mean R²/AUC of shuffled model $\ge 0.95 \times$ Real Model Performance, flag as `CircularDataError`.
 - **Note**: High R² (0.6-0.8) on real data is valid (physical correlation). The check only flags if the model learns the shuffled data almost as well as the real data.
4. **Selection Bias**:
 - Compare dataset descriptor distribution against a **physically constrained random distribution** (compositions satisfying Inoue's Rules).
 - Report Kolmogorov-Smirnov (K-S) statistic.

### Interpretability & Sensitivity
- **Feature Importance**: Ranked list of all descriptors (or Ridge coefficients).
- **Visualization**: 2D plot of top 2 descriptors (Partial Dependence for regression, Decision Boundary for classification).
- **Threshold Sensitivity**: For classification, sweep threshold across the full range in multiple steps. Report F1-score, Precision, Recall, and optimal cutoff.

## 4. Compute Feasibility

- **CPU-First**: XGBoost/Ridge is highly efficient on CPU. Training on ≤ 1,000 samples with adaptive LOGO CV is expected to complete in < 30 minutes on a 2-core runner.
- **Memory**: Estimated peak memory < 2GB (well within 7GB limit).
- **Disk**: Dataset size < 10MB.
- **GPU Escape Hatch**: Not required for this specific workflow.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Experimental Data Unavailable** | High (No ground truth) | Fallback to manual file upload. If no experimental data exists, the pipeline halts. |
| **Insufficient Samples (<30)** | High (No model) | Halt execution with `DataValidationError`. |
| **Power < 0.80 (30 <= N < 77)** | Medium (False negatives) | Proceed with warning and report MDES. Do not claim "no effect". |
| **Circular Target** | High (Invalid model) | Robust permutation test with relative threshold. Halt if detected. |
| **Collinearity** | Medium (Misleading importance) | Automatic switch to Ridge Regression or PCA. |
| **Missing Cooling Rate** | Medium (Confounder) | Document as a limitation in the final report. |

## 6. Decision Rationale

- **XGBoost/Ridge**: XGBoost for performance; Ridge for stability when collinearity is high.
- **Adaptive LOGO CV**: Ensures valid generalization estimates even with sparse chemical families, avoiding unstable fold metrics.
- **Robust Circularity**: Permutation test with relative threshold detects non-linear circularity and distinguishes strong physics from identity.
- **A Priori Power**: Justifies sample size requirements scientifically (N=77 target).
- **Associational Framing**: Essential for scientific integrity given the observational nature of the data.