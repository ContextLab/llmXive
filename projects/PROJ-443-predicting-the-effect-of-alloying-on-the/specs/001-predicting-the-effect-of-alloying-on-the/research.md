# Research: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Dataset Strategy

The project relies on two primary public databases for High-Entropy Alloy (HEA) composition and elastic constants. The strategy strictly adheres to the "Verified datasets" block provided in the prompt.

| Dataset | Source URL | Format | Usage | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **OQMD (Targets)** | `https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv` | CSV | Primary source for elastic constants (Bulk Modulus) and composition. | Verified via HuggingFace. **Critical Check**: Must contain `bulk_modulus` or `elastic_constants`. If missing, project halts as a fundamental data availability failure. |
| **OQMD (Completion)** | `https://huggingface.co/datasets/jablonkagroup/oqmd/resolve/main/completion_0/test-00000-of-00001.parquet` | Parquet | Supplementary source for composition data. | Verified via HuggingFace. Used if OQMD targets CSV lacks specific alloy variants. |
| **Materials Project (API)** | *API Access Required* | JSON/REST | Secondary source for elastic constants. | **Query Strategy**: Query for entries with `elastic_stiffness` tensor present and `elements_count >= 5`. If API fails or returns < 500 samples, the system triggers a hard halt. No unverified fallback exists. |

**Data Sufficiency Check**:
The pipeline will first attempt to aggregate samples from OQMD (verified URLs) and the Materials Project API.
- **Threshold**: ≥ 500 valid HEA samples (≥5 principal elements + elastic constants).
- **Action if < 500**: Hard halt with log: "Retrieved [N] samples; threshold 500 not met".
- **Fallback**: **None**. The spec mandates a hard halt. No literature merge or unverified source is authorized.

**Dataset Variable Fit**:
- **Required Variables**: Elemental composition (atomic %), Bulk Modulus (GPa).
- **Derived Variables**: Mixing enthalpy (Miedema), Atomic radius variance, ILR-transformed composition.
- **Fit Check**: The OQMD targets CSV is verified to contain formation energy. We **must** verify it contains **Bulk Modulus**. If the verified OQMD dataset lacks Bulk Modulus, the plan **cannot** proceed with the Residual Bulk Modulus target. The implementation will include a validation step: "Check if OQMD targets contain 'bulk_modulus' or 'elastic_constants'. If missing, halt." If missing, the project scope must be revised or halted.

## Statistical Methodology

### 1. Target Variable: Residual Bulk Modulus
- **Definition**: $B_{residual} = B_{observed} - B_{Miedema}$
- **Constraint (FR-008)**: When predicting $B_{residual}$, the predictor set **MUST NOT** include any features derived from Miedema's model (e.g., Mixing Enthalpy calculated via Miedema). This prevents the model from simply "learning" the Miedema correction, which would be circular validation.
- **Implementation**: Miedema-derived features are calculated but **immediately dropped** from the feature matrix if the target is $B_{residual}$.
- **Validation (FR-009)**: Prior to training, compute Pearson correlation ($r$) between $B_{residual}$ and all compositional descriptors.
  - **Logic**: If $|r| > 0.1$ for any **Miedema-derived** feature, log a warning: "Potential confound detected: Residuals correlate with Miedema feature X (|r|={val})". Proceed with caution but do not halt.
  - **Clarification**: Correlation with **non-linear** compositional descriptors (e.g., atomic radius variance) is expected and represents the signal to be learned (non-linear alloying effects), not a confound. The check is specifically for *Miedema-derived* features to ensure orthogonality.

### 2. Feature Engineering
- **Composition Handling**: Raw atomic percentages sum to unity (closure constraint).
- **Transformation**: Apply **Isometric Log-Ratio (ILR)** transformation to break singularity.
- **Descriptors**: Atomic radius variance, electronegativity variance, valence electron concentration (VEC).
- **Exclusion**: Explicitly filter out Miedema-derived features from the final feature matrix if the target is $B_{residual}$.

### 3. Model Training
- **Algorithms**: Random Forest (RF), Gradient Boosting (GB), ElasticNet (EN).
- **Infrastructure**: CPU-only (scikit-learn).
- **Hyperparameters**: Default grids or reduced grids to fit 6h runtime.
- **Validation**: 5-fold Cross-Validation.

### 4. Evaluation & Rigor
- **Metrics**: R², RMSE, MAE on held-out test set.
- **Confidence Intervals & Resampling Strategy**:
  - **Group Count > 50**: Perform **Grouped Bootstrap** (sufficient iterations, grouping by unique set of constituent elements) to compute 95% CI for R².
  - **Group Count 10-50**: **Primary Metric**: Perform **Leave-One-Alloy-Out (LOAO) Cross-Validation** (iterating over unique element sets) to estimate R² and variance. This addresses statistical instability in small-group regimes where bootstrap variance is high. Grouped bootstrap is retained as a supplementary (secondary) metric.
  - **Group Count < 10**: Log warning: "Insufficient groups for grouped bootstrap (N=[N]); falling back to standard bootstrap with caution" and proceed. **Do NOT** use Leave-One-System-Out (LOSO).
- **Multiple Comparison Correction**: Apply **Benjamini-Hochberg FDR** to p-values from pairwise model performance comparisons.
- **Null Hypothesis Test**: **Permutation Test**. Shuffle target labels 1000 times to generate a null distribution where true R²=0. Calculate the p-value as the proportion of permuted R² values ≥ observed R². Output p-value and boolean `significant` flag (if p < 0.05).
- **Sensitivity Analysis (FR-006)**:
  - **Thresholds**: $\{0.25, 0.30, 0.35\}$.
  - **Method**: Report the **observed R²** from the primary evaluation (LOAO or Grouped Bootstrap) against these thresholds.
  - **Decision Rule**: The primary scientific claim (R² > 0.3) is **rejected** if the Permutation Test p-value > 0.05. The threshold sweep is strictly for **descriptive robustness reporting** (showing how the observed effect size compares to these benchmarks), not for testing a non-zero null hypothesis via permutation (which is statistically invalid).
  - **Output**: Variance in observed R² across thresholds and the primary p-value.

### 5. Interpretability & Reporting
- **Method**: SHAP (CPU-compatible) or Permutation Importance.
- **Framing**: **Associational only**.
  - **Mandatory Disclaimer**: "These findings are associational and do not imply causation."
  - **Justification**: Observational data; no random assignment of elements.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (modest CPU, ~7 GB RAM).
- **Strategy**:
  - **Data**: Load OQMD CSV into pandas. Filter immediately. If > 7 GB, sample rows or process in chunks.
  - **Models**: Use `n_estimators=100` (default) for RF/GB. ElasticNet is lightweight.
  - **Bootstrap/LOAO**: 1000 iterations on ~500 samples or LOAO on ~50 groups is computationally feasible (~1-2 hours).
  - **Permutation Test**: 1000 iterations is feasible.
- **No GPU**: All libraries pinned to CPU versions.

## Risk Mitigation

1. **Dataset Mismatch**: If verified sources lack Bulk Modulus, the pipeline halts with a clear error.
2. **Sample Insufficiency**: Hard halt if < 500 samples. **No fallback**.
3. **Overfitting**: Hard halt if Train R² - Test R² > 95th percentile of bootstrap distribution of gaps.
4. **Circular Validation**: Explicit code check to remove Miedema features when target is Residual.
5. **API Failure**: Retry logic (with a configurable maximum number of attempts). If Materials Project fails, rely on OQMD. If total < 500, halt.
6. **Insufficient Groups**: If groups < 10, fallback to standard bootstrap with warning. If 10-50, use LOAO.