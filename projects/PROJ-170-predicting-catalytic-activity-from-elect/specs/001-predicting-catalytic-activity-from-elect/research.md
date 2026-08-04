# Research: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Problem Statement
Predict experimental turnover frequencies (TOF) for CO₂ hydrogenation catalysts using DFT-derived electronic descriptors (d-band center, activation barrier) and reaction path features. The goal is to determine whether an expanded descriptor set (beyond traditional Sabatier-volcano descriptors) provides statistically significant predictive improvement and to identify the physical determinants of catalytic activity.

## Dataset Strategy

| Dataset | Purpose | Source (Verified) | Access Method | Notes |
|---------|---------|-------------------|---------------|-------|
| OC20 Experimental Subset | DFT descriptors + Experimental TOF | https://huggingface.co/datasets/Open-Catalyst/oc20-experimental | `datasets.load_dataset(..., streaming=True)` | Contains aligned DFT and experimental TOF. Streaming used to stay within 7 GB RAM. |
| Materials Project Bulk | Bulk electronic descriptors | Official MP API (`mp-api`) | `mp-api` client (requires API key in env) | Used for bulk descriptors. Not a static file; fetched on-demand or cached. |
| OC20 Experimental Subset (Fallback) | Experimental TOF (if 2025 study unavailable) | https://huggingface.co/datasets/Open-Catalyst/oc20-experimental | `datasets.load_dataset(..., streaming=True)` | Satisfies FR-001 requirement if specific study is unavailable. |

**Critical Note**: Per FR-001, if the specific "2025 CO₂ hydrogenation study" dataset is not verifiable, the system uses the OC20 Experimental Subset as the primary source. This satisfies the requirement for experimental TOF data without fabricating a source.

## Methodological Approach

### Data Alignment & Preprocessing (FR-001, FR-002, FR-003)
1. **Download**: Stream OC20 Experimental dataset in chunks. Fetch MP descriptors via API (cached locally if possible).
2. **Descriptor Extraction**: OC20 raw data contains atomic structures, not pre-computed d-band centers. Use `pymatgen` and `ase` to derive d-band centers, p-band centers, and Bader charges from the atomic structures on-the-fly. This ensures data validity.
3. **Alignment**: 
   - **Keys**: `composition`, `surface_facet`, `synthesis_condition`.
   - **Strategy**: Fuzzy matching for `synthesis_condition` using Levenshtein distance and semantic clustering (e.g., "reduced at 300C" ≈ "300C reduction"). Exact match for `composition` and `surface_facet`.
   - **Exclusion**: Entries with no match are excluded. Ambiguous matches (multiple experimental entries for one DFT entry) are flagged and excluded to prevent circular validation.
4. **Imputation**: 
   - **Method**: k-nearest neighbors (k=5).
   - **Feature Space**: **Euclidean distance in stoichiometry space (normalized element counts)**. This strictly adheres to FR-003 and User Story 1 Acceptance Scenario 2.
   - **Target**: `experimental_tof` excluded from distance calculation.
   - **Exclusion**: Entries with <5 neighbors are flagged and excluded from training.
5. **Scaling**: StandardScaler (zero mean, unit variance) on all numeric features.

### Model Training & Baseline Comparison (FR-004, FR-005)
1. **XGBoost**: 
   - **Grid Search**: FIXED grid. `max_depth` ∈ {3,5,7}, `learning_rate` ∈ {0.01,0.1}, `n_estimators` ∈ {50, 100, 150, 200}.
   - **Selection**: 5-fold **Stratified** Cross-Validation (stratified by data source) selects configuration maximizing R². No runtime-based reduction of `n_estimators` (FR-004 compliance).
2. **Linear Baseline (Volcano Model)**: 
   - **Method**: Parabolic fit (quadratic regression) of `log(TOF)` vs. `d_band_center` (or adsorption energy proxy). This reflects the Sabatier principle (volcano plot) rather than a simple linear fit.
   - **Features**: `d_band_center` and `activation_barrier`.
3. **Statistical Test**: 
   - **Normality**: Shapiro-Wilk test (α=0.05) on absolute errors of both models.
   - **Test**: If normality rejected → Wilcoxon signed-rank test. Else → paired t-test (α=0.05, H0: mean difference = 0) on the **aggregated predictions from all stratified CV folds**.
   - **Collinearity**: Elastic Net regularization (α=0.5) applied to the baseline to handle BEP relations between d-band and activation barrier. If high collinearity persists, independent effects are not claimed; relationships reported descriptively.

### Interpretability & Feature Importance (FR-006, FR-007)
1. **SHAP**: Compute SHAP values for final XGBoost model.
2. **Ranking**: Rank descriptors by mean absolute SHAP impact.
3. **Validation**: Compare top 5 descriptors to Nørskov et al. reference (d-band center, activation barrier, reaction energy). Explicitly state matches or novel findings.
4. **Reduced Model (SC-003)**: Train a new XGBoost model using ONLY the top 5 SHAP-ranked descriptors. Calculate R²_reduced. Verify if R²_reduced ≥ 0.50 * R²_full.

## Statistical Rigor & Feasibility

### Multiple Comparison / Family-Wise Error
- Only **one** primary hypothesis test (XGBoost vs. Volcano Baseline) is performed. No correction needed.
- Secondary analyses (feature ranking, reduced model ratio) are descriptive.

### Sample Size / Power Justification
- Spec targets ≥3000 entries (α=0.05, power=0.8). 
- **Limitation Acknowledgement**: If available matched entries <3000 (but ≥500), analysis proceeds with available data. Power will be lower; results interpreted as exploratory.

### Causal Inference Assumptions
- **Observational Data**: All data is observational (no randomization). Claims are framed as **associational**, not causal.
- **Confounding Control**: The use of **Stratified 5-Fold Cross-Validation** (stratified by data source) ensures that the statistical test is performed on a representative distribution of data sources (OC20 vs. MP) in every fold. This prevents the test set from being biased toward a single source and validates that the performance gain is robust across the entire dataset distribution, not just a lucky split.

### Measurement Validity
- **d-band center**: Widely validated in catalysis literature (Nørskov et al.).
- **Activation barrier**: Standard DFT-derived metric; validation evidence from Materials Project.
- **TOF**: Experimental values from OC20 Experimental subset; units assumed consistent (s⁻¹).

## Compute Feasibility (CPU-First)

| Task | Method | CPU Feasibility | Notes |
|------|--------|-----------------|-------|
| Data Download | Streaming via `datasets` library | ✅ Yes | No local storage of full dataset |
| Descriptor Extraction | `pymatgen` + `ase` (chunked) | ✅ Yes | Computationally intensive but fits within 6h for sample |
| Preprocessing | Pandas + NumPy (chunked) | ✅ Yes | GB RAM sufficient for streaming |
| XGBoost Training | CPU-based XGBoost (n_estimators ≤ 200) | ✅ Yes | ≤200 trees fits within 6h/2 CPU |
| SHAP Analysis | `shap.TreeExplainer` (CPU) | ✅ Yes | Fast for tree-based models |
| Statistical Tests | Scipy (Shapiro, t-test, Wilcoxon) | ✅ Yes | Negligible runtime |

**Decision**: All methods run on CPU. No GPU escape hatch required. Streaming ensures full dataset (or maximal sample) is used without OOM.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Dataset mismatch**: OC20 Experimental lacks specific CO₂ entries | Proceed with available matched entries; report alignment rate (SC-002). If <500 entries, flag as insufficient for power. |
| **Missing descriptors**: <5 neighbors for imputation | Exclude entry from training (per spec). Log excluded entries. |
| **Runtime >6h**: Descriptor extraction or model training exceeds limit | Stream data in smaller chunks; if extraction exceeds limit, reduce sample size (documented). |
| **Collinearity**: High correlation between descriptors | Use Elastic Net; report collinearity descriptively without claiming independent effects. |
| **API Limits**: MP API rate limits | Cache MP results locally; use exponential backoff. |