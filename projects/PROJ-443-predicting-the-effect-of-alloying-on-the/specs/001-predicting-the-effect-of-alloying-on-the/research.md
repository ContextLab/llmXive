# Research: Predicting the Effect of Alloying on the Elastic Modulus of High‑Entropy Alloys

## Dataset Strategy

The project relies on public materials databases to retrieve High‑Entropy Alloy (HEA) compositions and elastic constants. Per the project constraints, we use only verified sources.

| Dataset | Source Description | Verified URL / Loader | Usage |
| :--- | :--- | :--- | :--- |
| **OQMD** | Open Quantum Materials Database. Contains DFT‑calculated elastic constants and compositions for thousands of materials. | `https://huggingface.co/datasets/materials-toolkits/oqmd/resolve/main/oqmd.tar.gz` | Primary source for HEA elastic constants and compositions. |
| **Materials Project** | Database of computed materials properties. | `https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv` (via OQMD mirror/verified subset) | Secondary source for validation and cross‑referencing if OQMD is insufficient. |
| **HEA Composition** | Specific HEA subsets with ≥5 elements. | *Derived from OQMD/MP via API filters* | Raw input for feature engineering. |

**Note on Data Availability**: The spec requires ≥500 samples with elastic constants. The pipeline first attempts to retrieve this from OQMD. If the retrieved count is < 500, the system halts with a specific deficit log (e.g., `"Retrieved 320 samples; threshold 500 not met"`). No alternative fabricated dataset will be used.

## Feature Engineering Strategy

### Compositional Descriptors
We compute standard HEA descriptors to capture the "effect of alloying":

1. **Mixing Enthalpy (ΔHₘᵢₓ)** – calculated via Miedema's model **only for the baseline bulk modulus**; **excluded** from the predictor matrix.
2. **Atomic Radius Variance (δ)** – variance of atomic radii weighted by composition.
3. **Entropy of Mixing (ΔSₘᵢₓ)** – ideal mixing entropy.
4. **Valence Electron Concentration (VEC)**.
5. **Electronegativity Variance** – variance of Pauling electronegativities.

### ILR Transformation
- **Method**: `scikit‑bio.ilr` (pivot‑coordinate implementation).  
- **Rationale**: Maps the simplex to Euclidean space, eliminating compositional singularity and multicollinearity.

### Orthogonality Validation & Baseline Decoupling
To address the circularity concern (methodology‑6f01c211):
1. **Baseline Inputs Identification**: The Miedema Bulk Modulus model relies on specific elemental parameters (electron density, electronegativity, valence).
2. **Correlation Check**: Before training, we compute the Pearson correlation between each predictor (e.g., Atomic Radius Variance, VEC) and these specific Miedema inputs.
3. **Residualization**: If any predictor shows |r| > 0.3 with the Miedema inputs, we regress that predictor against the Miedema inputs and use the **residuals** as the new predictor. This ensures the model learns effects *independent* of the baseline model's functional form.

## Modeling Strategy

### Target Variable
- **Primary Target**: **Residual Bulk Modulus** (`B_res = B_observed – B_Miedema`).  
- **Rationale**: Isolates the alloying effect beyond the rule‑of‑mixtures baseline while avoiding physics leakage.

### Algorithms
1. **Random Forest (RF)**
2. **Gradient Boosting (GB)**
3. **ElasticNet (EN)** – with L1/L2 regularization.

All models are trained on CPU only (`n_jobs=1`, `device='cpu'`), with `random_state=42`.

### Validation & Uncertainty
- **Data Split**: [deferred] train / [deferred] validation / [deferred] test (fixed random seed).
- **Grouped Bootstrap**: 1000 iterations, sampling by **unique element set** (e.g., `{Cr, Mn, Fe, Co, Ni}`) to avoid leakage.  
- **Low‑Group Fallback (<30 groups)**: If the number of unique element sets is < 30, standard bootstrap variance is unstable. We switch to **Bayesian Hierarchical Bootstrap**:
  - A hierarchical model is fit where group-level variances are drawn from a weakly informative inverse-gamma prior.
  - This stabilizes the variance estimation, allowing for the computation of valid 95% CIs even with sparse groups.
  - This method satisfies FR-005's requirement for valid CIs without resorting to arbitrary heuristics.
- **Multiple‑Comparison**: Benjamini‑Hochberg FDR correction applied to model‑performance p‑values.  
- **Power Analysis**: 
  - **Residual Variance Pre-Check**: We first estimate the variance of the residual target. If it is very low (<5% of total variance), the effective signal-to-noise ratio is poor.
  - **Adjusted Effect Size**: The power analysis (ΔR² = 0.05) is conditioned on this pre-check. If the residual variance is low, we adjust the assumed effect size downward or flag the study as underpowered for the intended effect.

### Statistical Safeguards
- **Baseline-Descriptor Orthogonality**: Verify that predictors are not deterministic functions of Miedema inputs (VIF < 5, correlation < 0.3). If not, residualize predictors.
- **Residual‑ILR Correlation**: Compute Pearson r between residuals and each ILR component; flag if |r| > 0.3.
- **Power Adequacy**: Confirm sample size ≥ 500; otherwise note limitation in the final report.

## Methodology Validation

| Check | Method | Acceptance Criterion |
|-------|--------|----------------------|
| **Baseline‑Descriptor Orthogonality** | Pearson correlation between predictors and Miedema inputs. | Pass if |r| ≤ 0.3 for all. If not, residualization (T017) applied. |
| **Residual‑ILR Correlation** | Pearson r, |r| > 0.3 triggers warning | Pass if |r| ≤ 0.3 for all components |
| **Power Adequacy** | Analytical calculation (ΔR² = 0.05, conditioned on residual variance) | Sample ≥ 460 (our threshold ≥ 500) |
| **Group Count Adequacy** | Count unique element sets | If < 30 → Bayesian Hierarchical Bootstrap for valid CIs |

## Statistical Rigor & Limitations

- **Associational Nature**: All results are explicitly framed as observational; no causal claims are made.  
- **Sample‑Size Limitation**: If the final dataset is close to 500, power to detect very small effects may be limited; this is reported in the final manuscript.  
- **Collinearity**: VIF screening and residualization mitigate deterministic relationships; any remaining high VIF is reported.  
- **Bootstrap Validity**: Grouped bootstrap respects chemical independence; Bayesian Hierarchical Bootstrap ensures valid CI estimation when groups are scarce.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).  
- **Strategy**: All heavy computations (bootstrap, model training) are parallelized over the two cores where possible; memory usage stays below 6 GB. The Bayesian Hierarchical Bootstrap is implemented with `pymc` using CPU-only sampling (NoUTurnSampler).