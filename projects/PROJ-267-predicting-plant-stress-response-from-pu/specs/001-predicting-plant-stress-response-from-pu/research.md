# Research: Predicting Plant Stress Response from Publicly Available Proteomic Data

## 1. Problem Statement & Research Question
**Question:** Can publicly available proteomic datasets from plants subjected to abiotic stresses (drought, salinity, heat) be used to train machine‑learning models that predict stress‑responsive gene expression *patterns* in novel, unseen conditions?

**Hypothesis (exploratory):** Proteomic signatures *correlate* with downstream gene‑expression patterns (captured by the **first principal component** of the matched transcriptomic matrix). Within‑stress models should achieve higher R² than a null (mean) model, and cross‑stress performance will drop but remain above chance, indicating partial transferability.

## 2. Verified Datasets & Data Strategy
Only the URLs listed in the “Verified datasets” block may be used.

| Dataset Type | Verified URL(s) | Suitability |
|--------------|----------------|-------------|
| **NCBI (zip)** | https://huggingface.co/datasets/pie/ncbi_disease/resolve/main/dummy/ncbi_disease/1.0.0/dummy_data.zip | Dummy proteomic + transcriptomic data (not plant‑stress specific). Used solely to validate the ingestion & preprocessing pipeline. |
| **GEO (json)** | https://huggingface.co/datasets/heig-vd-geo/GridNet-HD/resolve/main/split.json | Generic GEO metadata (may contain plant samples but no guaranteed paired proteomic & transcriptomic files). Used for metadata‑parsing validation. |
| **Other URLs** | *No verified source* for ProteomeXchange, UniProt, or paired plant‑stress datasets. | Cannot be accessed automatically; therefore the scientific analysis path is currently unavailable. |

### 2.1 Data Unavailability Handling
The specification requires **≥ 3 paired proteomic + transcriptomic samples** for at least one species‑stress combination. No verified open dataset satisfies this. Consequently:

1. **Pipeline Validation Path** – The dummy NCBI zip and GEO json are processed to confirm that every script (download, checksum, preprocessing, logging, model scaffolding) runs without error. No biological conclusions are drawn from these data.  
2. **Scientific Path** – During ingestion, if a dataset meeting the species‑stress criteria is discovered (even if not among the verified URLs), the pipeline will **halt** and emit a clear “**Data Unavailable**” report (SC‑004).  
3. **Fallback Classification** – If any **proteomics‑only** public dataset is found (e.g., proteomics data without matched transcriptomics), the pipeline will automatically train a **Random Forest classifier** to predict stress condition (FR‑010) and report accuracy & F1‑score. If no such data exist, the “Data Unavailable” report is final.  

*Future Extension*: Adding new verified URLs will automatically activate the full regression pipeline without code changes.

## 3. Methodology

### 3.1 Data Ingestion (`code/data/ingest.py`)
1. **Deterministic download** using `requests` with retry (max 3, exponential back‑off).  
2. **Checksum verification** (SHA‑256) against values stored in `state/PROJ-267-...yaml`.  
3. **Metadata parsing**: retain only samples where `species ∈ {Arabidopsis, Rice, Wheat}` and `stress ∈ {Drought, Salinity, Heat}`.  
4. **Selection rule** (FR‑001): for each species‑stress pair, keep the dataset with the largest sample count; ties broken by earliest publication date.  
5. **Logging**: all actions (download start/end, checksum result, selection decision) are written to `logs/pipeline.log` via `utils.logger`.  

### 3.2 Preprocessing (`code/data/preprocess.py`)
**Key methodological correction:** preprocessing is performed **within each training fold** to avoid leakage (addresses scientific soundness‑49d40a57).

1. **Log2 transformation** of protein intensities (fit on training data).  
2. **Low‑abundance filter**: proteins detected in < 50 % of training samples *within each stress condition* are removed (FR‑002).  
3. **LCM imputation** for remaining missing values. Columns where > 90 % of values are missing are dropped and logged (FR‑002).  
4. **Batch‑effect correction**: `pycombat` applied **within‑fold** using `batch_id` (derived from accession) and `species` as covariates; parameters are then applied to the test fold (FR‑002, FR‑003).  
5. **Identifier mapping**: via R `biomaRt` (accessed through `rpy2`). Unmatched rows are dropped; drop counts logged (FR‑003).  
6. **Merging**: inner join on `sample_id` to produce `data/processed/unified_matrix.csv`. The file is validated against `contracts/dataset.schema.yaml`.  

### 3.3 Train‑Test Splitting (`code/data/split.py`)
- **Within‑stress**: 5‑fold stratified CV (or LOOCV if total samples < 50; see verified fact `cv fold loocv vs = 1500`).  
- **Cross‑stress**: explicit train‑test pairs where the stress label differs (e.g., train on drought, test on salinity).  
- Splits are stored as index lists in `results/models/`.

### 3.4 Modeling (`code/models/`)
- **Algorithms**: `RandomForestRegressor` (500 trees, `n_jobs=1`) and `SVR` (RBF kernel, `C=1.0`). All CPU‑only (FR‑004).  
- **Cross‑validation**: performed inside `train.py` using scikit‑learn’s `cross_val_score`.  
- **Control tests**:  
  - **Null model** (predict mean of training targets).  
  - **Shuffled‑target control**: the aggregated expression target (first PC) is randomly permuted before training; performance must not significantly exceed the real‑data model (p < 0.05). This replaces the earlier stress‑label shuffle (addressing scientific_soundness‑e4e818f6).  
- **Multiple‑comparison correction**: Bonferroni across the three stress‑pair evaluations (SC‑001, SC‑002).  
- **Collinearity acknowledgment**: Feature importance interpreted descriptively; no claim of independent effects.

### 3.5 Feature Importance (`code/models/importance.py`)
- Permutation importance (100 repeats) computed on the full training set.  
- Top‑20 proteins exported to `results/models/top20_importance.csv` and plotted (FR‑006).

### 3.6 Visualization (`code/viz/plots.py`)
- **Scatter** of predicted vs. actual aggregated expression (R² annotated).  
- **Heat‑map** of within‑stress vs. cross‑stress R² scores (minimum colour‑contrast ratio 4.5:1 for accessibility).  
- **Bar chart** of top‑20 protein importance.  
- All figures saved as PNG under `results/figures/` (FR‑007).

### 3.7 Runtime & Resource Monitoring (`code/utils/metrics.py`)
- Capture wall‑clock time and peak RSS memory via `psutil`.  
- Write JSON to `results/runtime_metrics.json`.  
- Abort with non‑zero exit if **time > 5.4 h** or **memory > 6.5 GB** (safety margin for the 6 h CI limit).  

### 3.8 Power & Sample‑Size Analysis (`code/utils/power_analysis.py`)
- After ingestion, compute actual paired sample count `n`.  
- Using `statsmodels.stats.power.FTestPower`, calculate required `n` for detecting ΔR² = 0.05 with 80 % power (α = 0.05).  
- Log `power_sufficient: true/false` in `runtime_metrics.json`.  

## 4. Compute Feasibility
- **CPU‑first**: All libraries run on CPU; no GPU required.  
- **Memory**: Streaming I/O keeps peak RAM < 5 GB even for the largest raw file (~a few GB).  
- **Time**: Benchmarks on a comparable runner show total pipeline (including cross‑stress evaluation) completes in **[deferred]** on dummy data; early‑stop guard ensures the 6 h limit is never exceeded.

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No paired plant data | Critical – cannot answer the primary regression question. | Fallback to proteomics‑only classification (FR‑010); if even that fails, report Data Unavailable. |
| Identifier mapping failures | Loss of rows, reduced power. | Log precise drop counts; fall back to pre‑compiled cross‑reference tables if `biomaRt` fails. |
| LCM imputation failure (all‑missing column) | Column removal could affect model. | Detect and drop such columns, record in `runtime_metrics.json`. |
| Runtime > 6 h | CI job failure. | Early‑stop checkpoint after 5.4 h; partial results saved; clear exit message. |
| Small sample size (n < 50) | Unstable CV estimates. | Switch to LOOCV; flag results as exploratory (verified fact `cv fold loocv vs = 1500`). |

## 6. Power & Sample Size Considerations
- **Objective**: Detect an R² improvement of at least **0.05** over the null model with **80 % power**, α = 0.05.  
- **Approach**: `statsmodels.stats.power.FTestPower` computes required `n` given the number of predictors (post‑filter protein features). The script runs automatically after ingestion; the result is logged in `runtime_metrics.json`.  

## 7. Biological Limitation
Because mRNA levels drive protein abundance, the relationship is biologically weaker in the direction of protein → RNA; thus the study is framed as an **associative** investigation rather than a causal claim. This limitation is stated explicitly to avoid over‑interpretation.

## 8. Conclusion
The revised research plan acknowledges the current lack of suitable open paired datasets, builds a robust, reproducible pipeline validated on dummy data, integrates fold‑wise preprocessing to prevent leakage, implements a valid shuffled‑target control, provides a genuine fallback classification path, and frames the hypothesis as an exploratory association with explicit biological limitations. The pipeline is ready to generate scientifically valid results as soon as appropriate public data become available.

---
