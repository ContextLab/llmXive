# Research: Predicting Perovskite Stability via Compositional Fingerprints

## Research Question
How does elemental composition determine the thermal decomposition temperature ($T_d$) of metal halide perovskites, and can compositional descriptors alone predict stability across diverse perovskite families?

## Dataset Strategy

The project relies on the following verified datasets. **No other URLs are used.**

| Dataset Name | Source URL | Format | Relevance to Study |
|:--- |:--- |:--- |:--- |
| **NREL Pulse Diagnostics** | ` | JSON | Primary source for perovskite composition and thermal stability data (TGA onset). Contains `instrument_type` and `precision` metadata. |

**Critical Note on Dataset-Variable Fit**:
The spec requires $T_d$ (decomposition temperature) and elemental composition. The NREL JSON is the primary candidate. **No verified secondary dataset exists** for perovskite T_d in the current scope. The 'TGA (Synthetic/Experimental)' and 'TGA (Parquet)' URLs previously considered are invalid (structural crack data or generic TGA data without perovskite specificity) and have been removed.

**Fallback Strategy**:
If the NREL source yields < 200 entries after filtering, the pipeline will halt with a "Data Gap" error. No alternative dataset will be substituted.

**Instrument & Precision Verification**:
To address reviewer concerns (e.g., Marie Curie), the ingestion script will filter for entries where `instrument_type` is 'TGA' or 'Thermogravimetric Analyzer' and record the `precision` (typically ±5°C to ±10°C). Entries without this metadata will be flagged or excluded.

**Circularity Mitigation**:
The ingestion script will explicitly check if the source dataset's `T_d` is labeled as 'experimental', 'TGA', or 'onset'. If the source data contains a column like `thermodynamic_stability` or `calculated_T_d` derived from formation enthalpy, those entries will be filtered out programmatically to prevent data leakage (tautological validation).

## Methodology

### 1. Data Acquisition & Cleaning
- **Source**: Fetch NREL JSON.
- **Filtering**: Retain only entries with experimentally measured $T_d$ (TGA onset) and `instrument_type` = 'TGA'.
- **Missing Data**: Exclude entries with ≥2 missing descriptor values.
- **Retry Logic**: Implement exponential backoff (min, 2min, 4min) for API/network failures (FR-001).
- **Verification**: Perform HTTP reachability and 'title-token-overlap' validation against the primary source citation before processing (Constitution II).

### 2. Feature Engineering (Compositional Descriptors)
Compute the following for each perovskite formula $A_x B_y X_z$ (using `pymatgen` for deterministic parsing):
- **Atomic Fractions**: $x, y, z$ (normalized).
- **Weighted Averages**:
 - Weighted Ionic Radius: $\sum f_i \cdot r_i$
 - Weighted Electronegativity: $\sum f_i \cdot \chi_i$
 - Weighted Formation Enthalpy: $\sum f_i \cdot \Delta H_f$
 - **Weighted First Ionization Energy**: $\sum f_i \cdot I_i$ (FR-002 compliance)
 - (Where $f_i$ is the atomic fraction of element $i$).
- **Variance Metrics**: Variance of ionic radius, electronegativity, and ionization energy across A/B/X sites.
- **Family Assignment**:
 - Parse formula to identify A-site and B-site elements.
 - If B-site contains two distinct elements (e.g., Ag, Bi), classify as 'double'.
 - Otherwise, classify by the dominant B-site element (e.g., Pb → 'lead-halide', Sn → 'tin-halide').
- **Collinearity Check**: Compute Variance Inflation Factor (VIF) for all descriptors.
 - **Action**: If VIF > 5, drop the feature with the highest VIF and re-calculate. Repeat until all VIFs ≤ 5. If all features are collinear, switch to Elastic Net (regularization) for that model run.

### 3. Model Training
- **Algorithms**: Random Forest, Gradient Boosting, Elastic Net (scikit-learn).
- **Validation**: 5-fold Cross-Validation, stratified by perovskite family (lead-halide, tin-halide, double).
- **Hyperparameter Search**: Grid search limited to ≤10 combinations per model (Constitution VI).
- **Metrics**: RMSE, $R^2$, MAE.
- **Compute Budget**: Total runtime ≤ 4 hours on CPU-only runner.

### 4. Interpretability & Validation
- **Feature Importance**: SHAP values from the best model.
- **Statistical Significance**: Permutation testing (1000 permutations) with **Benjamini-Hochberg** correction (FR-007) to control FDR at q < 0.05.
- **External Validation (FR-006)**:
 - **Primary**: Test on held-out experimental data from the literature (if available in verified sources).
 - **Fallback Proxy**: If no external literature data exists, hold out an entire chemical family (e.g., 'tin-halide' if training is 'lead-halide' only) to simulate OOD conditions.
 - **Limitation**: If only one family exists, the OOD test is not possible; this limitation will be reported explicitly.
- **Generalizability**: Report $R^2$ and RMSE separately for in-distribution vs. out-of-distribution sets.
- **Success Criteria**: Evaluate permutation test results against Constitution VII thresholds: R² ≥ 0.6 supports hypothesis; R² < 0.3 triggers methodology revision.

### 5. Versioning & State Update
- **Hashing**: Compute SHA-256 hashes for `descriptors.csv` and `model_runs.json`.
- **State Update**: Use `state_manager.py` to write these hashes to `state/projects/...yaml`, ensuring Versioning Discipline compliance.

## Statistical Rigor & Assumptions

- **Observational Nature**: The study is observational. Claims are framed as associational, not causal.
- **Multiple Comparisons**: Benjamini-Hochberg correction applied to feature importance p-values.
- **Power Analysis**: Target $n \ge \times$ features (approx. 100-200 entries) for stable regression.
- **Measurement Uncertainty**: $T_d$ uncertainty assumed ±5°C to ±10°C (TGA precision). Used for weighting if metadata exists.
- **Collinearity**: VIF > 5 triggers feature removal or Elastic Net fallback.