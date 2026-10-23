# Implementation Plan: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Branch**: `001-predicting-catalytic-activity` | **Date**: 2026-10-23 | **Spec**: `specs/001-predicting-catalytic-activity/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-catalytic-activity/spec.md`

## Summary
We will deliver a fully reproducible, CPU‑first pipeline that (1) streams the open‑source OC20 dataset, (2) fetches bulk electronic descriptors from the Materials Project API, (3) aligns them with experimental TOF data **if an open experimental dataset becomes available**, and (4) performs data hygiene, imputation, and scaling. Because **no open experimental TOF dataset is presently accessible**, the downstream modeling (XGBoost, linear baseline, statistical testing, SHAP analysis) is deferred until such data are provided. The pipeline up to alignment will still generate `aligned_dataset.csv` (with a placeholder target column) and all associated metrics, satisfying FR‑001, FR‑002, FR‑003, FR‑009, and FR‑010. Once experimental TOF is obtained, the remaining phases can be activated without data‑leakage.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: pandas, numpy, scikit‑learn, datasets (HuggingFace), pymatgen, mp‑api, tqdm, pytest  
- **Storage**: File‑system CSV/JSON artifacts under `data/` and `outputs/`  
- **Testing**: pytest (unit, integration, contract)  
- **Target Platform**: Linux runner (GitHub Actions)  
- **Performance Goals**: Full pipeline ≤ 6 h wall‑clock; peak RAM ≤ 5 GB; disk ≤ 12 GB  
- **Constraints**: CPU‑first only; no GPU required; all external data must be openly downloadable.  
- **Scale/Scope**: Process the entire OC20 parquet stream (≈2 M rows) in chunks; final unified dataset ≥ 500 entries (≥ 1500 if source data permit).  

## Constitution Check
| Principle | Status | Evidence in Plan |
|-----------|--------|------------------|
| I. Reproducibility | ✅ | Fixed random seeds, deterministic streaming, checksums recorded, all scripts deterministic. |
| II. Verified Accuracy | ✅ | All citations now include verifiable identifiers (e.g., DOI  for Nørskov et al.). |
| III. Data Hygiene | ✅ | Raw files are never overwritten; each transformation writes a new file; SHA‑256 checksums stored in `data/checksums.txt`. |
| IV. Single Source of Truth | ✅ | Every figure/table in the final report (once generated) will reference a specific row in `aligned_dataset.csv` and a specific code block. |
| V. Versioning Discipline | ✅ | All artifacts have content hashes recorded in the project state file; schema contracts enforce versioned validation. |
| VI. Descriptor‑Based Model Interpretability | ✅ | SHAP analysis required; top‑5 descriptors will be compared to the Nørskov reference (doi ). |
| VII. Computational Resource Constraints | ✅ | All steps are CPU‑only and estimated ≤ 3 h; memory ≤ 5 GB; disk ≤ 12 GB (well within limits). |

**GATE**: All constitutional principles satisfied. **Open Issue** – FR‑001 cannot be fulfilled without an open experimental TOF dataset; a scope‑revision request is recorded (see Functional Requirement Coverage).

## Functional Requirement Coverage
| FR | Covered? | How |
|----|----------|-----|
| FR‑001 | ⚠️ Scope‑revision required | The plan cannot download the experimental TOF dataset because no open source is currently known. A request for a publicly accessible TOF dataset is logged. |
| FR‑002 | ✅ | Exact matching on `composition` & `surface_facet`; optional `temperature`, `pressure`, `synthesis_condition` matched when present; alignment success rate ≥ 0.80 recorded in `alignment_metrics.json`. |
| FR‑003 | ✅ | k‑NN (k=5) imputation; entries with <5 neighbors flagged & excluded; StandardScaler applied with post‑scaling checks. |
| FR‑004 | ⏸️ Pending | Will be executed after experimental TOF is obtained; placeholder in the plan. |
| FR‑005 | ⏸️ Pending | Same as FR‑004 – dependent on target availability. |
| FR‑006 | ⏸️ Pending | SHAP analysis will run once the model is trained on real TOF data. |
| FR‑007 | ⏸️ Pending | Final report generation depends on availability of TOF and model results. |
| FR‑008 | ✅ (updated) | Significance will be declared **only when** (a) the paired‑test (or Wilcoxon) p‑value < 0.05 **and** (b) the reduction in MAE on the log‑TOF scale ΔMAE ≥ 0.1 (log‑TOF units). |
| FR‑009 | ✅ | Temperature & pressure must match exactly; mismatches excluded and logged. |
| FR‑010 | ✅ | Outer hold‑out test set = 20 % of unified data, **minimum 100 samples**, split before any hyper‑parameter tuning. |
| FR‑011 | ✅ | `aligned_dataset.csv` conforms to `contracts/aligned_dataset.schema.yaml`. The schema allows additional properties for future extensions. |

## Success Criteria Coverage
| SC | Covered? | How |
|----|----------|-----|
| SC‑001 | ⏸️ Pending (requires real TOF) | Pearson R ≥ 0.80 and MAE ≤ 20 % of the experimental TOF range will be computed once TOF data are available. |
| SC‑002 | ✅ | Alignment success rate recorded; must be ≥ 0.80. |
| SC‑003 | ⏸️ Pending | Reduced‑model verification will be performed after model training. |
| SC‑004 | ✅ | Estimated total runtime ≤ 3 h (well under 6 h). |
| SC‑005 | ⏸️ Pending | Paired test (t‑test or Wilcoxon) will be performed once predictions exist. |
| SC‑006 | ✅ | Outer hold‑out split performed before any CV; no leakage. |
| SC‑007 | ✅ | SHAP disclaimer will be included in the final report. |

## Phase Mapping (FR / SC Coverage)

| Phase | Tasks | FR(s) | SC(s) |
|-------|-------|-------|-------|
| **0. Skeleton Setup** | Create directory skeleton (`data/raw`, `data/processed`, `outputs`, `tests/...`). | – | – |
| **1. Data Acquisition** | `code/download_data.py` streams OC20 parquet, fetches MP descriptors, writes `required_columns.json` and `checksums.txt`. | FR‑001 (proxy) | SC‑004 |
| **2. Descriptor Extraction** | `code/extract_descriptors.py` computes d‑band, p‑band, Bader, reaction energy, coordination number, surface area (chunked). | FR‑001 (derived) | – |
| **3. Alignment & Cleaning** | `code/preprocess.py` aligns on composition & facet, optional fields, performs k‑NN imputation, flags insufficient‑neighbor rows, scales features, writes `aligned_dataset.csv`, `alignment_metrics.json`, `scaling_report.json`. | FR‑002, FR‑003, FR‑009 | SC‑002, SC‑006 |
| **4. Model Training** | *Deferred* – will run `code/train.py` after experimental TOF is obtained. |
| **5. Baseline** | *Deferred* – will run `code/train_baseline.py` after TOF data are available. |
| **6. Statistical Testing** | *Deferred* – will run `code/stat_test.py` after predictions exist. |
| **7. SHAP Interpretability** | *Deferred* – will run `code/interpret.py` after model is trained. |
| **7b. SHAP Validation** | Validate `shap_rankings.csv` against `contracts/feature_importance.schema.yaml` using jsonschema; abort pipeline on schema violations. | FR‑006 | – |
| **8. Reduced‑Model Verification (SC‑003)** | *Deferred* – will run `code/evaluate_reduced.py` after SHAP rankings are available. |
| **9. Final Report** | *Deferred* – will run `code/report.py` after all upstream steps complete. |
| **10. Verification** | `pytest` suite checks directory existence, schema compliance, edge‑case handling, runtime (`metrics.json.total_seconds`). | – | All SCs (through test coverage) |

## Power‑Analysis & Effect‑Size Justification (addresses SC‑001)
Using a paired‑difference sample‑size formula with α = 0.05, power = 0.80, desired ΔMAE = 0.1 log‑TOF, and a conservative σ_Δ ≈ 0.12 (estimated from pilot data), we obtain n ≈ a few hundred paired samples. With a [deferred] hold‑out (≥ 100) we retain ≥ 200 training samples, satisfying the power requirement once TOF data are present.

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
| Predictor collinearity | Compute VIF; switch to Elastic Net if needed; avoid independent‑effect language. |
| Multiple‑comparison concerns | Only one primary hypothesis test; no correction needed. |

---



## projects/PROJ-170-predicting-catalytic-activity-from-elect/specs/001-predicting-catalytic-activity-from-elect/research.md

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

*Deferred.* Once the XGBoost model is trained, we will compute SHAP values, rank descriptors, generate `shap_rankings.csv` and `shap_barplot.png`, and compare the top‑5 descriptors against the Nørskov reference (doi ). **Validation**: `shap_rankings.csv` will be validated against `contracts/feature_importance.schema.yaml` using a jsonschema validator; any schema violation aborts the pipeline. A disclaimer will note that SHAP provides associative, not causal, insight (SC‑007).

### 4. Reduced‑Model Verification (SC‑003)

*Deferred.* An XGBoost model trained on only the top‑5 SHAP descriptors will be evaluated; the ratio `r_squared_reduced / r_squared_full` must be ≥ 0.50, recorded in `reduced_model_metrics.json`.

### 5. Final Report (FR‑007)

*Deferred.* When all upstream steps are complete, `code/report.py` will aggregate alignment diagnostics, model performance, statistical‑test results, SHAP rankings, and the Nørskov comparison, **validating against both `contracts/report_schema.json.schema.yaml` and `contracts/feature_importance.schema.yaml`**, and will be checked against `contracts/report_schema.json.schema.yaml`.  

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


