# Research: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Problem Statement
We aim to predict catalytic activity (turnover frequency, TOF) using DFT‑derived electronic descriptors and reaction‑path features. **At present no open experimental TOF dataset for the 2025 CO₂ hydrogenation study is publicly available**; therefore the full predictive pipeline cannot be completed until such a dataset is provided. The current work will therefore focus on (a) constructing a reproducible alignment of OC20 and Materials Project descriptors, (b) documenting the data‑hygiene and imputation procedures, and (c) preparing the infrastructure for downstream modeling once experimental TOF values are obtained.

## Dataset Strategy

| Dataset | Purpose | Verified Source | Access Method | Notes |
|---------|---------|----------------|---------------|-------|
| OC20 (parquet) | Provides DFT structures and computed energetics (descriptors) | https://huggingface.co/datasets/nimashoghi/oc20_s2ef_train_2M/resolve/main/data/train-00000-of-00014.parquet | `datasets.load_dataset(..., streaming=True)` | Large (on the order of millions of rows); streamed to stay within RAM. |
| Materials Project bulk descriptors | Supplies bulk electronic properties (d‑band, p‑band, Bader) for catalyst compositions | Materials Project API (`mp-api` client; requires `MP_API_KEY`) | Programmatic API call; results cached locally. | Open API; cached to avoid rate limits. |
| Experimental TOF | – | **No open source** | – | The required 2025 CO₂ hydrogenation TOF dataset is not publicly downloadable. A scope‑revision request is filed to supply an open TOF dataset. Until then, modeling steps are deferred. |

**Data‑Availability Gap**: FR‑001 cannot be satisfied because the experimental TOF dataset is not open. We will proceed with the alignment and preprocessing pipeline and pause downstream analysis pending data provision.

## Methodological Approach

### 1. Data Alignment & Preprocessing (FR‑001 – FR‑003)

1. **Streaming download** of OC20 parquet shards via HuggingFace `datasets` (CPU‑only).  
2. **Descriptor extraction** using `pymatgen` on each structure chunk: d‑band center, p‑band center, Bader charge, reaction energy, coordination number, surface area (chunked).  
3. **Alignment** – exact match on `composition` and `surface_facet`; optional `temperature`, `pressure`, `synthesis_condition` matched when present. If exact match fails, a **nearest‑neighbor stoichiometry match** (Euclidean distance in normalized element‑count space, k=5) is attempted. Entries that cannot be aligned are excluded and logged. Alignment success rate ≥ 0.80 is recorded in `alignment_metrics.json`.  
4. **Imputation** – k‑NN (k=5) on stoichiometry space; entries with fewer than five neighbors are flagged (`excluded_from_training=True`) and excluded from model training.  
5. **Scaling** – `StandardScaler` to zero mean/unit variance; post‑scaling checks (`|μ| < 0.01`, `|σ‑1| < 0.01`) saved in `scaling_report.json`.  
6. **Target variable** – **placeholder** column `experimental_tof` is left null until an open dataset is supplied.

### 2. Model Training & Baseline Comparison (FR‑004 – FR‑005)

*Deferred until experimental TOF data become available.* The pipeline will later:
- Create an outer hold‑out ([deferred] ≥ 100 samples) before any hyper‑parameter tuning (FR‑010).
- Perform inner 5‑fold CV grid search for XGBoost (max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, n_estimators ∈ {50,100,150,200}); select hyper‑parameters maximizing R²; ties broken by smallest `n_estimators`.  
- Fit a linear baseline using only `d_band_center` and `p_band_center`.  
- Conduct Shapiro‑Wilk normality test on paired absolute‑error differences; choose paired t‑test or Wilcoxon accordingly; record in `statistical_test.json`.  
- Apply FR‑008 significance rule (p < 0.05 **and** ΔMAE ≥ 0.1 log‑TOF).

### 3. Feature Importance and Interpretability (FR‑006 – FR‑007)

*Deferred.* Once the XGBoost model is trained, we will compute SHAP values, rank descriptors, generate `shap_rankings.csv` and `shap_barplot.png`, and compare the top‑5 descriptors against the Nørskov reference (doi ). A disclaimer will note that SHAP provides associative, not causal, insight (SC‑007).

### 4. Reduced‑Model Verification (SC‑003)

*Deferred.* An XGBoost model trained on only the top‑5 SHAP descriptors will be evaluated; the ratio `r_squared_reduced / r_squared_full` must be ≥ 0.50, recorded in `reduced_model_metrics.json`.

### 5. Final Report (FR‑007)

*Deferred.* When all upstream steps are complete, `code/report.py` will aggregate alignment diagnostics, model performance, statistical‑test results, SHAP rankings, and the Nørskov comparison, validating against `contracts/report_schema.json.schema.yaml`.

## Statistical Rigor & Feasibility

- **Multiple comparisons** – Only one primary hypothesis test; no correction needed.  
- **Power analysis** – Paired‑difference sample‑size formula with α = 0.05, power = 0.80, desired ΔMAE = 0.1 log‑TOF, σ_Δ ≈ 0.12 yields n ≈ 250; the outer hold‑out (≥ 100) leaves ≥ 200 training samples, satisfying power once TOF data are present.  
- **Observational nature** – All statements will be framed as associative; no causal claims.  
- **Measurement validity** – d‑band center, reaction energy, and other descriptors are standard DFT quantities with extensive literature support.  
- **Collinearity** – VIF will be computed; if VIF > 5, Elastic Net will replace linear regression and independent‑effect language will be avoided.  

## Compute Feasibility (CPU‑First)

| Task | Library / Method | Estimated CPU time | Memory |
|------|------------------|-------------------|--------|
| OC20 streaming download | `datasets` (streaming) | ≤ 10 min | < 1 GB |
| Descriptor extraction (pymatgen) | Chunked processing (100 k rows) | ≤ 45 min | ≤ 5 GB |
| Alignment & imputation | Pandas + scikit‑learn k‑NN | ≤ 15 min | ≤ 3 GB |
| **Total (pre‑modeling)** | – | **≈ 1 h** | **≤ 5 GB** |

All steps run on the free GitHub Actions runner; no GPU required.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Missing experimental TOF data (FR‑001) | Scope‑revision request for an open TOF dataset; pipeline pauses after alignment. |
| Insufficient neighbors for k‑NN imputation | Log and exclude; abort with warning if >30 % excluded. |
| Alignment failures due to missing optional fields | Optional fields nullable; fall back to composition+facet exact match. |
| MP API rate limits | Cache responses locally; exponential back‑off on 429. |
| Runtime exceedance | Process smaller chunks; document any reduction and its impact on power. |
| Predictor collinearity | Compute VIF; switch to Elastic Net if needed; avoid independent‑effect claims. |
| Multiple‑comparison concerns | Only one primary test; no correction needed. |

---

