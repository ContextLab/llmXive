# Research: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Problem Statement
We aim to predict catalytic turnover frequency (TOF) from DFT‑derived electronic descriptors and reaction‑path features. The core obstacle is the absence of a publicly downloadable experimental TOF dataset for the 2025 CO₂ hydrogenation study. Consequently, the pipeline currently focuses on (1) constructing a reproducible, open‑source unified dataset of computational descriptors, (2) documenting rigorous alignment, imputation, and scaling procedures, and (3) preparing the downstream modeling infrastructure for when the experimental TOF data become available.

## Dataset Strategy

| Dataset | Purpose | Verified Source | Access Method | Notes |
|---------|---------|----------------|---------------|-------|
| **OC20 (parquet)** | DFT structures & energetics (source of descriptors) | https://huggingface.co/datasets/nimashoghi/oc20_s2ef_train_2M/resolve/main/data/train-00000-of-00014.parquet | `datasets.load_dataset(..., streaming=True)` | Streamed to stay within RAM. |
| **Materials Project bulk descriptors** | Bulk electronic properties (d‑band, p‑band, Bader) | Materials Project API (`mp-api` client) – open programmatic endpoint | `mp_api` Python client; cached locally. | Requires `MP_API_KEY` env var; cached to avoid rate limits. |
| **Experimental TOF** | Target variable (log‑TOF) | **No open source** (verified block: “TOFs: NO verified source found”) | – | A **scope‑revision request** is issued (see Phase 4). |

**Data‑Availability Gap**: FR‑001 cannot be satisfied until an open experimental TOF dataset is supplied. The pipeline will generate `aligned_dataset.csv` with a **null** `experimental_tof` column and pause downstream analysis.

## Methodological Approach

### 1. Data Acquisition & Descriptor Extraction (FR‑001 – FR‑003)
1. **Stream OC20** using HuggingFace `datasets` (CPU‑only).  
2. **Fetch MP bulk descriptors** via `mp-api`; store in a local JSON cache (`data/raw/mp_cache.json`).  
3. **Chunked descriptor computation**: for each OC20 structure, use `pymatgen` to calculate:
   - d‑band center  
   - p‑band center  
   - Bader charge  
   - Activation barrier (from provided reaction energetics)  
   - Reaction energy  
   - Coordination number  
   - Surface area  
   The results are appended to a temporary Parquet file (`data/processed/oc20_descriptors.parquet`).  
4. **Alignment**: exact string matching on `composition` + `surface_facet`; optional fields (`temperature`, `pressure`, `synthesis_condition`) matched when present. If exact match fails, a **stoichiometry‑space k‑NN (k=5)** fallback is attempted. Entries that cannot be aligned are excluded and logged. Alignment success rate is saved in `alignment_metrics.json` (must be ≥ 0.80).  
5. **Imputation**: k‑NN (k=5) on normalized element‑count vectors; rows with <5 neighbors are flagged (`excluded_from_training=True`) and later omitted from model training.  
6. **Scaling**: `StandardScaler` to zero mean/unit variance; post‑scaling diagnostics (`|μ| < 0.01`, `|σ‑1| < 0.01`) stored in `scaling_report.json`.  
7. **Target column**: `experimental_tof` left as `null` pending a real TOF dataset. The unified CSV (`aligned_dataset.csv`) conforms to `contracts/aligned_dataset.schema.yaml`.

### 2. Scope‑Revision Request (addresses T014, T015)
- `code/request_scope_revision.py` creates `outputs/scope_revision_request.json` describing the missing experimental TOF dataset and the scientific impact of its absence.  
- A **placeholder CSV** (`data/raw/experimental_tof_placeholder.csv`) containing only the header row is written, its SHA‑256 hash computed, and a **single‑line** entry (no trailing newline) added to `data/checksums.txt`. This satisfies the checksum verification (T015) while clearly indicating the data gap.

### 3. Model Training & Baseline (FR‑004 – FR‑005) – *Deferred*
- **Hold‑out split**: 20 % of the unified dataset is randomly selected (seed 42) *before* any CV, saved as `outputs/holdout_indices.npy`.  
- **XGBoost grid search**: 5‑fold CV over max_depth ∈ {3,5,7}, learning_rate ∈ {0.01,0.1}, n_estimators ∈ {50,100,150,200}; best hyper‑parameters saved to `best_params.json`. Ties broken by smallest `n_estimators`.  
- **Linear baseline**: uses only `d_band_center` and `activation_barrier`.  
- **Statistical testing**: Shapiro‑Wilk on absolute‑error differences (α = 0.05). If p ≥ 0.05 → paired t‑test; else → Wilcoxon signed‑rank test. Results stored in `statistical_test.json`.  

### 4. SHAP Interpretability (FR‑006 – FR‑007) – *Deferred*
- Compute SHAP values for the final XGBoost model; rank descriptors by mean absolute SHAP impact; save `shap_rankings.csv` (validated against `contracts/feature_importance.schema.yaml`) and `shap_barplot.png`.  
- The report will compare the top‑5 descriptors to the Nørskov reference (d‑band center, activation barrier, reaction energy) and include an explicit disclaimer that SHAP provides associative, not causal, insight (SC‑007).

### 5. Reduced‑Model Verification (SC‑003) – *Deferred*
- Train a second XGBoost model on only the top‑5 SHAP descriptors; compute `r_squared_reduced / r_squared_full`. The ratio must be ≥ 0.50; results recorded in `reduced_model_metrics.json`.

### 6. Final Report (FR‑007) – *Deferred*
- `code/report.py` aggregates alignment metrics, model performance, statistical‑test outcomes, SHAP rankings, and the Nørskov comparison. The JSON companion is validated against `contracts/report_schema.yaml`; the human‑readable `final_report.md` is produced.

## Statistical Rigor & Feasibility
- **Multiple comparisons** – Only a single primary hypothesis test; no correction needed.  
- **Power analysis** – Paired‑difference sample size ≈ 250 for ΔMAE = 0.1 log‑TOF (α = 0.05, power = 0.80). With a 20 % hold‑out, a dataset of ≥ 1250 aligned rows yields ≥ 1000 training samples, satisfying the power requirement.  
- **Observational nature** – All conclusions framed as associative; no causal claims.  
- **Measurement validity** – d‑band center, reaction energy, etc., are standard DFT descriptors with extensive validation in the catalysis literature.  
- **Collinearity** – Compute Variance Inflation Factor (VIF); if any VIF > 5, replace linear baseline with Elastic Net and avoid independent‑effect phrasing.

## Compute Feasibility (CPU‑First)
All steps are designed to run on the free GitHub Actions runner:

| Step | Estimated Wall‑Clock | Peak RAM |
|------|----------------------|----------|
| OC20 streaming download | ≤ 10 min | < 1 GB |
| MP descriptor fetch | ≤ 5 min | < 1 GB |
| Descriptor extraction (pymatgen) | ≤ 45 min | ≤ 5 GB |
| Alignment & imputation | ≤ 15 min | ≤ 3 GB |
| **Total (pre‑modeling)** | **≈ 1 h** | **≤ 5 GB** |

Model training (XGBoost ≤ 200 trees) also fits comfortably within the CPU budget; if runtime threatens the 6 h limit, we will reduce `n_estimators` or use a stratified subsample, noting the impact on power.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Missing experimental TOF (FR‑001) | Scope‑revision request; pipeline pauses after alignment; all upstream artifacts remain reproducible. |
| <5 neighbors for k‑NN | Log and exclude; abort with warning if >30 % excluded. |
| MP API rate limits | Local cache; exponential back‑off on 429. |
| Runtime exceedance | Process smaller chunks or subsample; record any reduction in `metrics.json`. |
| Predictor collinearity | Compute VIF; switch baseline to Elastic Net if needed. |
| Checksum formatting error (T015) | Write checksum line with `.strip()`; unit test ensures exactly 64‑char hash. |
| Placeholder TOF file empty (T014) | Provide header‑only CSV, compute hash, record correctly; clearly marked as placeholder. |

---
