# Research: Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

## Domain Context

Additive manufacturing (AM) of nickel-based superalloys offers superior mechanical properties but is highly sensitive to process parameters. The research question focuses on identifying which parameters (laser power, scan speed, hatch spacing, layer thickness) most strongly influence ductility and quantifying their effects. Key challenges include:
- **Data Scarcity**: Experimental datasets are often small (<250 records) and fragmented across literature.
- **Collinearity**: Energy density ($E_v = P/(v \cdot h \cdot t)$) is mathematically derived from the other four parameters, leading to severe multicollinearity.
- **Heterogeneity**: Data comes from different alloy families (e.g., Inconel 718, Hastelloy X), requiring statistical methods to account for random effects.

## Dataset Strategy

**CRITICAL GAP**: The `spec.md` references a "HuggingFace 'additive-manufacturing-superalloy' collection" and "four cited papers," but the `# Verified datasets` block provided in the input does **not** contain a verified URL for this specific collection or the papers. 

**Mitigation Strategy (Literature Synthesis)**:
1.  **Primary Source**: The system will parse supplementary tables from the **four cited papers** (identified by DOI/Title in the spec) to extract `laser_power`, `scan_speed`, `hatch_spacing`, `layer_thickness`, `ductility`, and `alloy_family`.
2.  **Fallback**: If the HF dataset becomes available (verified URL added), it will be merged.
3.  **Composition Mapping**: Alloy composition flags (Cr, Al, Ti) will be derived from `alloy_family` using a standard alloy composition table (e.g., Inconel 718 -> has_Cr=True).
4.  **Data Volume**: The expected record count is < 100. The pipeline is designed for this scale.

| Dataset Name | Source Type | Verified URL | Usage Plan |
|--------------|-------------|--------------|------------|
| Paper 1 (Supp. Table) | PDF/Excel | *See Spec* (DOI) | **PRIMARY**: Parse table for AM parameters. |
| Paper 2 (Supp. Table) | PDF/Excel | *See Spec* (DOI) | **PRIMARY**: Parse table for AM parameters. |
| Paper 3 (Supp. Table) | PDF/Excel | *See Spec* (DOI) | **PRIMARY**: Parse table for AM parameters. |
| Paper 4 (Supp. Table) | PDF/Excel | *See Spec* (DOI) | **PRIMARY**: Parse table for AM parameters. |
| Materials Project | API | *See Spec* (MP-API) | **SUPPLEMENTARY**: Crystallographic descriptors (if available). |

*Note: The `# Verified datasets` block in the input contained irrelevant data (transaction logs, video metadata). No valid AM superalloy dataset URL was provided. The plan proceeds via Literature Parsing.*

## Statistical Methodology

### Linear Mixed-Effects (LME) Model
- **Fixed Effects**: 
  - **Model A (Components)**: Laser Power, Scan Speed, Hatch Spacing, Layer Thickness.
  - **Model B (Energy)**: Energy Density (if VIF > 5 in Model A).
- **Random Effects**: Random intercept for `alloy_family`.
- **Collinearity Handling**: 
  1. Calculate VIF for Model A components.
  2. If Max VIF > 5, drop components and fit Model B (Energy Density only).
  3. If Max VIF <= 5, retain Model A.
- **Output**: Standardized coefficients, 95% CI, p-values, partial R².
- **Small N Handling**: Use bootstrapping (1000 iterations) to estimate stability of coefficients if N < 50.

### Gradient Boosting (XGBoost)
- **Algorithm**: XGBoost Regressor (hist tree method for CPU efficiency).
- **Validation**: **Leave-One-Alloy-Family-Out (LOAFO)** or **Stratified K-Fold** (K=5 if N>=25). This avoids data starvation.
- **Hyperparameters**: `max_depth=3`, `learning_rate=0.1`, `n_estimators=100` (tuned via CV).
- **Metrics**: Mean R², MAE, RMSE across CV folds.
- **Feature Importance**: Permutation importance on the **same feature set** used by the LME model (Components or Energy Density) to ensure valid comparison.

### Sensitivity Analysis
- Repeat LME fit with $\alpha \in \{0.01, 0.05, 0.10\}$ to assess robustness of parameter rankings.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (multiple CPU cores, several GB RAM).
- **Data Size**: Expected < 100 rows.
- **Time Budget**: An extended duration for XGBoost tuning (LOAFO CV is computationally heavier but feasible for N<100).
- **Libraries**: `statsmodels` (LME), `xgboost` (CPU-only), `scikit-learn`. All have CPU wheels available.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Literature Parsing | No verified HF dataset exists in the input block. Parsing paper tables is the only way to get real experimental data. |
| LOAFO CV | Standard splits fail with N < 100. LOAFO ensures every alloy family is tested. |
| Conditional Feature Set | Prevents singular matrices in LME while testing the "Energy Density Hypothesis" vs "Component Hypothesis". |
| Bootstrapping | Provides stability estimates for p-values/coefficients in small samples. |

## Limitations

- **Sample Size**: N < 100 limits statistical power. P-values are exploratory.
- **Data Source**: Reliance on four papers limits generalizability to other alloys or processes.
- **Physics**: No physics-informed constraints; model learns empirical correlations only.
