# Research: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Dataset Strategy

### Verified Sources
The project targets the **Metallic Glass Database** compiled by Pauly et al. (DOI: 10.5281/zenodo.10043838).
- **Status**: **Primary Source**.
- **Fallback**: **None**. The previously cited DOI 10.5281/zenodo.11023456 (MatNVP) has been removed as it appears to be non-existent. No other verified fallback exists in the current context.

**Critical Gap & Action Plan**:
1. The `ingest.py` script will attempt to fetch data via the `zenodo` Python library using the primary DOI.
2. **If the Zenodo API fails (404/Timeout) or the dataset lacks required variables (Tg, composition)**: The project **HALTS** with a clear error: `ERROR: Dataset source unreachable or invalid. Scientific results cannot be generated without verified real-world data.`
3. **Simulation Mode Rejected**: Synthetic data generation is explicitly **NOT** permitted for this task. Synthetic data cannot capture the complex, non-linear physical interactions governing metallic glass formation, rendering the 'predictive' goal (FR-003) and 'generalization to unseen families' (LOFO rationale) scientifically void. The pipeline will not proceed to modeling if real data is unavailable.

### Variable Fit Verification
- **Required Variables**: Elemental composition (wt% or at%), $T_g$ (K or C), Alloy Family (inferred or explicit).
- **Derived Variables**: Atomic radius, Electronegativity, Valence Electron Count (from `mendeleev`).
- **Fit Check**: The `ingest.py` script will validate that the raw data contains columns for at least two major elements and a $T_g$ value. If $T_g$ is missing, the record is dropped (FR-001).

### Family Assignment Logic (Scientific Soundness)
- **Definition**: 'Alloy Family' is defined as the element with the highest atomic fraction in the composition, provided it exceeds 40%.
- **Rationale**: This rule is applied *before* feature engineering to avoid circularity. It is a deterministic projection of the composition vector but is distinct from the derived descriptors (radius mismatch, VEC, etc.) which are non-linear combinations of elemental properties.
- **Circularity Warning**: While this rule is distinct, the model is trained to predict $T_g$ based on composition, and the validation split is determined by a function of that composition. This risks the model learning 'family-specific' biases that are trivially predictable from the input features. The LOFO strategy mitigates this by testing on *unseen* families, but the limitation is acknowledged.
- **Minimum Family Count**: The pipeline requires at least **5 distinct alloy families** for LOFO to be statistically valid. If fewer than 5 families are found, the pipeline will halt and report a 'Statistical Power Insufficiency' error, preventing invalid generalization claims.

## 2. Methodology & Statistical Rigor

### Feature Engineering
- **Descriptors**:
  1. **Radius Mismatch ($\delta$)**: $\sqrt{\sum c_i (1 - r_i/\bar{r})^2}$.
  2. **Electronegativity Difference ($\Delta\chi$)**: Standard deviation of Pauling electronegativities.
  3. **Valence Electron Concentration (VEC)**: Weighted mean of valence electrons.
  4. **Weighted Mean Radius ($\bar{r}$)**: Computed for diagnostic logging only (FR-002).
- **Handling Collinearity (VIF)**:
  - **Acknowledgement**: High VIF is expected by construction because these descriptors are mathematically derived from the same set of elemental properties (atomic radius, electronegativity, valence electrons) and the composition vector.
  - **Remediation Strategy**: The system will calculate VIF for the three predictors. If $VIF > 5$ for any predictor, the predictor with the **highest VIF** is dropped. VIF is recalculated for the remaining features. This process repeats iteratively until all remaining predictors have $VIF < 5$. The model is then trained on the remaining features. This ensures model stability and avoids the 'diagnostic flag only' trap.

### Model Training
- **Algorithm**: `GradientBoostingRegressor` (scikit-learn).
- **Validation Strategy**: **Leave-One-Family-Out (LOFO)**.
  - *Rationale*: Ensures the model predicts $T_g$ for *new* alloy families, not just unseen compositions of known families.
  - *Implementation*: GroupBy "Family" (defined by the rule above). Iterate: Train on $N-1$ families, Test on 1.
- **Hyperparameter Tuning**: Grid search over $\le 10$ combinations (e.g., `n_estimators`, `max_depth`).
- **Sensitivity Analysis**: Sweep `max_depth` $\in \{3, 5, 7\}$ and report variance ($\sigma^2$) of $R^2$ (FR-006).

### Statistical Validation
- **Multiple Comparisons**: **Bonferroni Correction** ($\alpha \le 0.05$) for all pairwise correlation p-values (FR-008).
  - *Justification*: With a limited set of predictors, there are correspondingly few pairwise correlations. Benjamini-Hochberg (FDR) is statistically weak and often overly conservative for such a small set (N=3). Bonferroni correction is the standard, more robust method for small hypothesis sets to control family-wise error rate.
- **Confidence Intervals**: Feature importance stability measured via 1000 bootstrapped resamples (SC-002).
- **Causal Framing**: All output text will explicitly state: "These findings are associational only." No "causes" or "determines" language (FR-004).

## 3. Compute Feasibility & Constraints

- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 6h limit).
- **Memory Management**:
  - Datasets will be loaded in chunks if necessary.
  - `pandas` operations optimized; no large intermediate DataFrames.
  - Model training uses CPU-only `scikit-learn` (no PyTorch/CUDA).
- **Runtime Budget**:
  - Ingestion: < 5 min.
  - Descriptor Computation: < 10 min.
  - Training (LOFO + GridSearch): < 2 hours (expected).
  - Analysis (Bootstrapping/VIF): < 1 hour.
  - Total: Well within 6h limit.
- **Fallback**: If dataset size exceeds memory, a random sample (stratified by family) will be taken, with the sampling ratio logged.

## 4. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **LOFO over K-Fold** | Standard K-Fold would allow the model to "memorize" family-specific trends, failing the goal of predicting *new* alloy systems. |
| **Gradient Boosting** | Handles non-linear relationships in materials science data better than linear regression; robust to outliers; CPU-efficient. |
| **Bonferroni Correction** | With 3 predictors, FDR is weak. Bonferroni is the standard for small hypothesis sets to control false positives. |
| **Iterative VIF Remediation** | High VIF is expected by construction. Dropping the highest VIF feature iteratively ensures model stability without arbitrary feature dropping. |
| **Diagnostic Mean Radius** | Included for physical interpretability but excluded from modeling to prevent collinearity with radius mismatch (which uses $\bar{r}$). |
| **No Synthetic Data** | Synthetic data cannot validate the physical descriptors against real-world $T_g$ values. The project halts if real data is unavailable. |