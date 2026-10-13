# Research: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Problem Statement
Develop a predictive model for **generic catalytic activity** using DFT‑derived electronic descriptors (d‑band center, activation barrier, etc.) and reaction‑path features. Because no open experimental turnover‑frequency (TOF) dataset for CO₂ hydrogenation exists, the study will **temporarily use the DFT activation barrier as a proxy target** (see scope‑revision note in the implementation plan). The objective remains to assess (1) whether an expanded descriptor set outperforms the classic Sabatier‑volcano descriptors for predicting the proxy target, and (2) which descriptors provide the strongest associative signal via SHAP. All conclusions are explicitly limited to association with the proxy target.

## Dataset Strategy

| Dataset | Purpose | Verified Source | Access Method | Notes |
|---------|---------|----------------|---------------|-------|
| OC20 (parquet) | DFT structures & computed energetics (descriptors) | https://huggingface.co/datasets/nimashoghi/oc20_s2ef_train_2M/resolve/main/data/train-00000-of-00014.parquet | `datasets.load_dataset(..., streaming=True)` | Provides atomic structures; no experimental TOF. |
| Materials Project Bulk | Bulk electronic descriptors (d‑band, p‑band, Bader) | Official MP API (`mp-api`) | `mp-api` client (API key via `MP_API_KEY`) | Cached locally under `data/raw/mp_cache.json`. |
| **No open experimental TOF dataset** | – | – | – | The original CO₂ hydrogenation experimental TOF dataset is not publicly available.; a formal scope‑revision request is filed to replace the target when an open source becomes available. The proxy target is the DFT activation barrier. |

**Data‑Availability Gap**: The spec’s required “2025 CO₂ hydrogenation experimental TOFs” dataset is not publicly downloadable. Consequently, we **use the DFT activation barrier as a surrogate target** and clearly label this limitation in the final report. A formal scope‑revision request is filed to replace the target when an open source becomes available.

## Methodological Approach

### 1. Data Alignment & Preprocessing (FR‑001 – FR‑003)

1. **Streaming Download** – The OC dataset parquet streamed in substantial row chunks.; MP descriptors fetched via API and cached.  
2. **Descriptor Extraction** – For each OC20 structure, `pymatgen` computes: d‑band center, p‑band center, Bader charges, coordination number, surface area, reaction energy. Computations are chunked to stay within RAM limits.  
3. **Alignment** – **Exact matching on `composition` and `surface_facet`** between OC20 and MP descriptors. Optional fields `temperature`, `pressure`, and `synthesis_condition` are matched when present; otherwise they are left null. If an exact match cannot be found, a **nearest‑neighbor stoichiometry match** (k=5) is attempted; entries that still cannot be aligned are excluded and logged. Alignment success rate is recorded in `alignment_metrics.json`; if the rate falls below 0.80 the pipeline aborts with `alignment_failure.json`.  
4. **Imputation** – k‑NN (k=5) in normalized stoichiometry space; entries with fewer than 5 neighbors are flagged (`excluded_from_training=True`) and excluded from model training.  
5. **Scaling** – `StandardScaler` (zero mean, unit variance) applied to all numeric columns; post‑scaling mean |μ| < 0.01 and |σ‑1| < 0.01 are logged in `scaling_report.json`.  
6. **Target Variable** – The proxy target `activation_barrier` (scaled) is used as the regression outcome; the original experimental TOF column is omitted pending dataset availability.

### 2. Model Training & Baseline Comparison (FR‑004 – FR‑005)

1. **Nested CV** – An outer hold‑out test set of **[deferred] of the unified dataset (minimum 100 samples)** is split **before** any model fitting. Within the remaining data, a 5‑fold inner CV grid search optimizes XGBoost hyper‑parameters (`max_depth ∈ {3,5,7}`, `learning_rate ∈ {0.01,0.1}`, `n_estimators ∈ {50,100,150,200}`), selecting the configuration that maximizes inner‑CV R². Ties are broken by the smallest `n_estimators`.
2. **Linear Volcano Baseline** – Ordinary Least Squares `LinearRegression` on `d_band_center` and `activation_barrier`.  
3. **Statistical Test** – Shapiro‑Wilk test (α = 0.05) is applied to the **paired absolute‑error differences** (|e_XGB| − |e_baseline|). If normality holds (p ≥ 0.05) a paired two‑tailed t‑test is used; otherwise a Wilcoxon signed‑rank test is performed. Results are saved in `normality_test.json` and `statistical_test.json`. **Significance** is declared only if *p* < 0.05 **and** ΔR² ≥ 0.02 (per FR‑008).  

### 3. Interpretability & Feature Importance (FR‑006 – FR‑007)

1. **SHAP** – `shap.TreeExplainer` computes values for the final XGBoost model **using only training‑fold data**; mean absolute SHAP per descriptor is calculated.  
2. **Ranking & Visualization** – Top‑5 descriptors saved as `shap_rankings.csv` (checksum‑verified) and visualized in `shap_barplot.png`.  
3. **Physical Comparison** – The top‑5 list is compared against Nørskov et al. (d‑band center, activation barrier, reaction energy). The report **explicitly limits** the discussion to associative patterns; no causal language is used.  

### 4. Final Report (FR‑007)

`code/report.py` aggregates:
- Alignment rate, imputation statistics, model metrics (R², MAE, Pearson r), statistical‑test outcome (including ΔR² check), SHAP ranking, reduced‑model ratio, and a discussion of physical relevance.  
- The report **clearly notes** the surrogate nature of the target and limits interpretation to association.

## Statistical Rigor & Feasibility

- **Multiple Comparisons** – Only one primary hypothesis test → no correction needed.  
- **Power / Sample Size** – Paired‑difference sample‑size formula (σ_Δ = 0.10, Δ = 0.02, α = 0.05, power = 0.80) yields a minimum of **≈250** paired samples; the outer hold‑out of ≥ 100 samples ensures ≥ 200 training samples, satisfying the power requirement.  
- **Observational Data** – All statements are framed as associational; no causal claims are made.  
- **Measurement Validity** – d‑band center and activation barrier are standard DFT descriptors with extensive literature support (Nørskov et al.). The proxy target is explicitly labeled as such.  
- **Collinearity** – VIF calculated; if VIF > 5, Elastic Net regularization is applied and independent effect claims are avoided.  

## Compute Feasibility (CPU‑First)

| Task | Library / Method | Estimated CPU Time (max) | Memory / Disk |
|------|------------------|--------------------------|---------------|
| Streaming OC20 download | `datasets` (streaming) | ≤10 min | <1 GB (stream) |
| Descriptor extraction (pymatgen) | Chunked processing (100 k rows) | ≤45 min | ≤5 GB |
| Alignment & imputation | Pandas + scikit‑learn k‑NN | ≤15 min | ≤3 GB |
| XGBoost CV grid (≤200 trees) | `xgboost` CPU | ≤30 min | ≤2 GB |
| SHAP analysis | `shap.TreeExplainer` | ≤10 min | ≤1 GB |
| Reduced model + reporting | Scikit‑learn + matplotlib | ≤10 min | ≤1 GB |
| **Total** | – | **≈2 h** | **≤7 GB** (within runner limits) |

All steps are pure CPU; no GPU escape hatch required.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Missing open experimental TOF dataset (FR‑001) | Document limitation; request scope‑revision; proceed with DFT proxy while clearly labeling it. |
| Insufficient neighbors for k‑NN imputation | Log and exclude; if >30 % entries are excluded, abort with warning and suggest expanding dataset. |
| Alignment failures due to missing optional fields | Optional fields are nullable; alignment proceeds on composition + facet alone, with fallback nearest‑neighbor matching. |
| Runtime exceedance | Process smaller chunks; fallback to a random sample with documented power limitation. |
| MP API rate limits | Cache results locally; exponential back‑off on 429 responses. |
| Predictor collinearity | Compute VIF; apply Elastic Net if needed; report descriptive relationships without claiming independence. |
| Over‑optimistic significance claims | Enforce ΔR² ≥ 0.02 and require both p < 0.05 **and** ΔR² rule (FR‑008). |
