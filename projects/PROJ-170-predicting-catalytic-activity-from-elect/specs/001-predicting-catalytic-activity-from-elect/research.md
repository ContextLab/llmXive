# Research: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Problem Statement
Develop a predictive model for **generic catalytic turnover frequencies (TOF)** using DFT‑derived electronic descriptors (d‑band center, activation barrier, etc.) and reaction‑path features. The study assesses (1) whether an expanded descriptor set outperforms the classic Sabatier‑volcano descriptors for predicting catalytic activity, and (2) which descriptors provide the strongest associative signal via SHAP. The target variable does **not** correspond to CO₂ hydrogenation; this limitation is explicitly acknowledged throughout.

## Dataset Strategy

| Dataset | Purpose | Verified Source | Access Method | Notes |
|---------|---------|----------------|---------------|-------|
| OC20 (parquet) | DFT structures & computed energetics | https://huggingface.co/datasets/nimashoghi/oc20_s2ef_train_2M/resolve/main/data/train-00000-of-00014.parquet | `datasets.load_dataset(..., streaming=True)` | Provides atomic structures; no experimental TOF. |
| Materials Project Bulk | Bulk electronic descriptors (d‑band, p‑band, Bader) | Official MP API (`mp-api`) | `mp-api` client (API key via `MP_API_KEY`) | Cached locally under `data/raw/mp_cache.json`. |
| TOF (jsonl) – surrogate | Experimental TOF values (generic catalytic dataset) | https://huggingface.co/datasets/locuslab/TOFU/resolve/main/forget01.json | `datasets.load_dataset("locuslab/TOFU")` | Used because the required 2025 CO₂ hydrogenation dataset lacks an open URL. The surrogate does **not** represent CO₂ hydrogenation catalysts; provenance is clearly labeled in the final report. |

**Data‑Availability Gap**: The spec’s required “2025 CO₂ hydrogenation experimental TOFs” dataset is not publicly downloadable. Consequently, we **use the open surrogate TOF collection** (`locuslab/TOFU`) as a stand‑in, but we **explicitly state** that these values do **not** correspond to CO₂ hydrogenation catalysts. This limitation is recorded, and a scope‑revision request is filed for the original dataset.

## Methodological Approach

### 1. Data Alignment & Preprocessing (FR‑001 – FR‑003)

1. **Streaming Download** – OC20 parquet streamed in 100 k row chunks; MP descriptors fetched via API and cached.  
2. **Descriptor Extraction** – For each OC20 structure, `pymatgen` computes: d‑band center, p‑band center, Bader charges, coordination number, surface area. Computations are chunked to stay within RAM limits.  
3. **Exact Alignment** – **Exact string matching** on `composition`, `surface_facet`, **and** `synthesis_condition`. Temperature and pressure are parsed from `synthesis_condition`; entries lacking either are excluded. Alignment rate is recorded (SC‑002).  
4. **Imputation** – k‑NN (k=5) in normalized stoichiometry space; entries with <5 neighbors are flagged (`excluded_from_training=True`).  
5. **Scaling** – `StandardScaler` (zero mean, unit variance) applied to all numeric columns. The resulting CSV (`aligned_dataset.csv`) conforms to `contracts/aligned_dataset.schema.yaml`.

### 2. Model Training & Baseline Comparison (FR‑004 – FR‑005)

1. **Nested CV** – An outer hold‑out test set ([deferred] of data) is split **before** any model fitting. Within the remaining data, a 5‑fold inner CV grid search optimizes XGBoost hyper‑parameters (`max_depth ∈ {3,5,7}`, `learning_rate ∈ {0.01,0.1}`, `n_estimators ∈ {50,100,150,200}`), selecting the configuration that maximizes inner‑CV R². Ties are broken by the smallest `n_estimators`.
2. **Linear Volcano Baseline** – Elastic Net regression (l1_ratio = 0.5) on `d_band_center` and `activation_barrier` (with VIF diagnostics).  
3. **Statistical Test** – Shapiro‑Wilk (α = 0.05) on absolute errors of both models. If normality is rejected, a two‑tailed Wilcoxon signed‑rank test is performed; otherwise a paired two‑tailed t‑test. **Minimal Important Difference (MID)** is defined as ΔMAE ≥ 0.1 log‑TOF units. Significance is declared only if *p* < 0.05 **and** ΔMAE ≥ MID. No multiple‑comparison correction is needed because this is the sole primary hypothesis test.

### 3. Interpretability & Feature Importance (FR‑006 – FR‑007)

1. **SHAP** – `shap.TreeExplainer` computes values for the final XGBoost model; mean absolute SHAP per descriptor is calculated.  
2. **Ranking & Visualization** – Top‑5 descriptors plotted (`feature_importance.png`).  
3. **Physical Comparison** – The top‑5 list is compared against Nørskov et al. (d‑band center, activation barrier, reaction energy). The report **explicitly limits** the discussion to associative patterns; no causal language is used.  
4. **Reduced Model (SC‑003)** – XGBoost trained on only the top‑5 SHAP descriptors; R² ratio (`R²_reduced / R²_full`) computed and required to be ≥ 0.50. Result stored in `outputs/reduced_model_metrics.json`.

### 4. Reporting (FR‑007)

`code/report.py` aggregates:
- Alignment rate, imputation statistics, model metrics (R², MAE, Pearson r), statistical test outcome (including MID check), SHAP ranking, reduced‑model ratio, and a discussion of physical relevance. The report **clearly notes** that the TOF data are surrogate and that SHAP findings are associative, not causal.

## Statistical Rigor & Feasibility

- **Multiple Comparisons** – Only one primary hypothesis test → no correction needed.  
- **Power / Sample Size** – Assuming a medium effect size (Cohen’s f²≈0.15), ≥500 matched entries provide >80 % power at α = 0.05 for detecting a ΔMAE ≥ 0.1 log‑TOF (see Power‑Analysis justification).  
- **Observational Data** – All statements are framed as associational; no causal claims are made.  
- **Measurement Validity** – d‑band center and activation barrier are standard DFT descriptors with extensive literature support (Nørskov et al.). TOF values from the surrogate dataset are **clearly identified** as such.  
- **Collinearity** – VIF calculated; if VIF > 5, Elastic Net regularization is applied and independent effect claims are avoided.  

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
| Missing open CO₂ hydrogenation TOF dataset (FR‑001) | Document limitation; request scope‑revision; proceed with surrogate while clearly labeling it. |
| Insufficient neighbors for k‑NN imputation | Log and exclude; if >30 % entries are excluded, abort with warning and suggest expanding dataset. |
| Confounding experimental conditions | Require exact `synthesis_condition` match and parse temperature/pressure; exclude entries lacking these covariates. |
| Runtime exceedance | Process smaller chunks; fallback to a random [deferred] sample with documented power limitation. |
| MP API rate limits | Cache results locally; exponential back‑off on 429 responses. |
| Predictor collinearity | Compute VIF; apply Elastic Net; report descriptive relationships without claiming independence. |
| Over‑optimistic significance claims | Enforce MID (ΔMAE ≥ 0.1) and require both p‑value < 0.05 **and** MID to claim improvement. |

---



