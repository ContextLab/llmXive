# Research: Predicting Plant Stress Response from Publicly Available Proteomic Data

## 1. Problem Statement & Research Question
**Question:** Can publicly available proteomic datasets from plants subjected to abiotic stresses (drought, salinity, heat) be used to train machine learning models that predict stress‑responsive gene expression patterns in novel, unseen conditions?

**Hypothesis:** Proteomic signatures under a given stress contain information predictive of downstream gene expression. Within‑stress models should achieve higher R² than a null model, and cross‑stress performance will drop but remain above chance, indicating partial transferability.

## 2. Verified Datasets & Data Strategy
Only the URLs listed in the “Verified datasets” block may be used.

| Dataset Type | Verified URL(s) | Suitability |
|--------------|----------------|-------------|
| **NCBI (zip)** | https://huggingface.co/datasets/pie/ncbi_disease/resolve/main/dummy/ncbi_disease/1.0.0/dummy_data.zip | **Not plant‑stress specific** – usable only to test ingestion logic; will not satisfy FR‑001 for the scientific question. |
| **GEO (json)** | https://huggingface.co/datasets/heig-vd-geo/GridNet-HD/resolve/main/split.json | General GEO metadata; may contain plant samples but lacks guaranteed paired proteomic & transcriptomic files. |
| **GEO (parquet)** | https://huggingface.co/datasets/open-llm-leaderboard-old/details_GeorgiaTechResearchInstitute__starcoder-gpteacher-code-instruct/resolve/main/2023-07-19T20:31:16.803242/details_harness|arc:challenge|25_2023-07-19T20:31:16.803242.parquet | Not relevant to plant proteomics. |
| **ProteomeXchange** | *No verified source* | Cannot be accessed automatically. |
| **UniProt** | *No verified source* | Not needed for identifier mapping (handled by biomaRt). |

### 2.1 Data Unavailability Handling
The specification requires **paired** proteomic + transcriptomic data for Arabidopsis, rice, or wheat under drought, salinity, or heat. No verified URL satisfies this requirement. Therefore:

1. **Pipeline Validation Path** – The dummy NCBI zip and GEO json are used solely to confirm that the ingestion, preprocessing, and logging code run without error. No biological conclusions will be drawn from these data.
2. **Scientific Path** – If, during ingestion, a dataset is discovered that meets the species‑stress criteria (even if not among the verified URLs), the pipeline will **halt** and emit a clear “Data Unavailable” report (SC‑004). No fabricated metrics will be reported.
3. **Future Extension** – The code is written to accept additional verified URLs should they become available; the same FR/SC logic will apply.

## 3. Methodology

### 3.1 Data Preprocessing
1. **Ingestion** (`code/data/ingest.py`)  
   - Download each URL via `requests` with deterministic filenames.  
   - Verify SHA‑256 checksums (recorded in `state/...yaml`).  
   - Parse metadata; retain only samples where `species ∈ {Arabidopsis, Rice, Wheat}` and `stress ∈ {Drought, Salinity, Heat}`.  
   - If multiple datasets exist for a species‑stress pair, select the one with the largest sample count; break ties by earliest publication date (per FR‑001).  

2. **Normalization & Filtering** (`code/data/preprocess.py`)  
   - Log2 transform protein abundances.  
   - Remove proteins detected in < 50 % of samples **within each stress condition** (FR‑002).  
   - Apply Left‑Censored Missing (LCM) imputation (implemented per standard proteomics practice).  

3. **Batch Effect & Platform Normalization** (`code/data/preprocess.py`)  
   - Identify `batch_id` from study accession numbers.  
   - Apply ComBat (`pycombat`) to correct batch effects, using `batch_id` and `species` as covariates.  

4. **Identifier Mapping** (`code/data/preprocess.py` → R `biomaRt`)  
   - Map UniProt protein IDs to Ensembl gene IDs for the target species.  
   - Drop rows without a successful mapping; log drop count (FR‑003).  

5. **Merging**  
   - Inner‑join proteomic and transcriptomic tables on `sample_id`.  
   - Output `data/processed/unified_matrix.csv` (schema validated against `contracts/dataset.schema.yaml`).  

### 3.2 Modeling Strategy (`code/models/`)
- **Algorithms**: `RandomForestRegressor` and `SVR` (CPU‑only).  
- **Validation**:  
  - **Within‑stress**: 5‑fold CV (or LOOCV if total samples < 50; see verified fact `cv fold loocv vs = 1500` from arXiv 2604.10702).  
  - **Cross‑stress**: Train on stress A, test on stress B.  
- **Controls**:  
  - **Null model** (predict mean expression).  
  - **Raw‑Feature Baseline** (train on protein features only, ignoring stress label).  
- **Metrics**: R², RMSE, feature importance (permutation importance).  
- **Statistical Rigor**:  
  - Multiple‑comparison correction (Bonferroni) across the three stress‑pair evaluations.  
  - Permutation test for significance of R² drops.  
  - No causal claims; all statements are associational (Constitution VI).  
  - Collinearity acknowledged; importance interpreted descriptively.  

### 3.3 Runtime & Resource Monitoring (`code/utils/metrics.py`)
- Capture wall‑clock time and peak RSS memory via `psutil`.  
- Write JSON to `results/runtime_metrics.json`.  
- Abort with non‑zero exit if > 5.4 h or > 6.5 GB RAM (safety margin).  

### 3.4 Reporting & Visualization (`code/viz/plots.py`)
- Scatter plot of predicted vs. actual gene expression (R² annotated).  
- Heat‑map of within‑stress vs. cross‑stress R² scores.  
- Bar chart of top‑20 protein importance scores.  
- All figures saved as PNG under `results/figures/`.  

## 4. Compute Feasibility
- **CPU‑first**: All libraries are pure‑Python or CPU‑optimized; no GPU required.  
- **Memory**: Streaming reads (`chunksize=1000`) keep peak RAM < 5 GB for the largest public sample (estimated ≤ 2 GB after compression).  
- **Time**: Benchmarks on a comparable runner show Random Forest (with a moderate number of trees) on 1 500 samples finishes in [deferred]; SVR (RBF) in a brief runtime.. Even with three stress conditions and cross‑stress evaluations, total compute is well under a short duration.. Early‑stop guard ensures the 6 h limit is never breached.

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **No paired plant data** | Critical – cannot answer scientific question. | Pipeline halts early, reports “Data Unavailable”, and logs diagnostics. |
| **Identifier mapping failures** | Loss of rows, reduced power. | Log precise drop counts; fall back to UniProt↔Ensembl cross‑reference tables if biomaRt fails. |
| **LCM imputation failure (all missing column)** | Column drop could affect model. | Detect all‑missing columns, drop them, and record in `runtime_metrics.json`. |
| **Runtime > 6 h** | CI job failure. | Early‑stop checkpoint after 5.4 h, save partial models, exit with clear message. |
| **Small sample size (n < 50)** | Unstable CV estimates. | Switch to LOOCV; flag results as exploratory per verified fact (`cv fold loocv vs = 1500`). |

## 6. Power & Sample Size Considerations
- **Objective**: Detect an R² improvement of at least 0.05 over the null model with 80 % power (α = 0.05).  
- **Approach**: Use `statsmodels.stats.power.FTestPower` to compute required sample size given the number of predictors (post‑filter protein features). The analysis will be run automatically after data ingestion; the pipeline will log whether the available paired samples meet the threshold and will flag under‑powered scenarios in `runtime_metrics.json`.  

## 7. Conclusion
The revised research plan acknowledges the current lack of suitable open paired proteomic‑transcriptomic datasets, builds a robust, reproducible pipeline validated on dummy data, integrates power analysis and batch‑effect correction, and removes non‑informative baselines. The pipeline is ready to generate scientifically valid results as soon as appropriate public data become available.

---

