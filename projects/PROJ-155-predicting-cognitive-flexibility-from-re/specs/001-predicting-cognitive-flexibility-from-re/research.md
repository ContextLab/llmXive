# Research: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Executive Summary
We will test whether inter‑individual variability in resting‑state functional connectivity (RSFC) predicts performance on the NIH Toolbox Dimensional Change Card Sort (cognitive flexibility) task. The core predictor is the **first principal component** (`PCA_Component_1`) of edge‑wise sliding‑window variability (standard deviation + Shannon entropy). Association is assessed with a linear regression controlling for age, sex, mean framewise displacement, and total scan time, and an empirical p‑value from a 10 000‑permutation test. All steps are CPU‑only, fully reproducible, and validated against JSON‑Schema contracts.

## Dataset Strategy

| Variable | Verified Source URL(s) | Availability |
|----------|------------------------|--------------|
| Resting‑state fMRI (preprocessed) | https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet, https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv, https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | **NOT AVAILABLE** – these files contain diffusion or unrelated data, not the high‑dimensional fMRI time‑series required for RSFC. |
| NIH Toolbox Dimensional Change Card Sort (DCCS) scores | https://huggingface.co/datasets/timm/nih-chest-xray-14/resolve/main/data/test-00000-of-00010.parquet, https://huggingface.co/datasets/alkzar90/NIH-Chest-X-ray-dataset/resolve/main/data/BBox_List_2017.csv, https://huggingface.co/datasets/suolyer/pile_nih-exporter/resolve/main/test.json | **NOT AVAILABLE** – these datasets contain chest‑X‑ray images or unrelated annotations, not the NIH Toolbox behavioral scores. |
| Schaefer 200‑region atlas | https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal | Available – can be downloaded directly from the official CBIG repository. |

### Gap Analysis & Mitigation
* Because the verified URLs do **not** contain the essential fMRI time‑series nor the DCCS scores, Phase 0 of the pipeline will attempt to load the URLs, detect the missing variables, and generate `data/gap_report.md`.  
* The pipeline will **halt** after the gap report; no synthetic or fabricated data will be created, satisfying Constitution Principle II (Verified Accuracy).  
* If an open dataset that includes both modalities becomes available, the plan can be updated without altering any other specification.

## Methodology & Statistical Rigor

### 1. Preprocessing
* **Parcellation** – Apply the Schaefer 200‑region atlas (MNI space) to each subject’s minimally preprocessed fMRI; extract mean regional time‑series.  
* **Motion control** – Exclude subjects with Mean FD > 0.2 mm (Constitution VI). Log exclusions (`exclusion_log.csv`).  
* **SNR filter** – Subjects with temporal SNR < 50 are excluded; counts logged (SC‑001).

### 2. Dynamic Connectivity Metrics
* **Sliding window** – 60 s window, 1 s step (as required by FR‑003).  
* **Edge‑wise statistics** – For each of the 19 900 edges (200 × 199 / 2) compute:  
  * Standard deviation across windows.  
  * Shannon entropy of the distribution of correlation values (base e).  
* **Dimensionality reduction** – Incremental PCA on the concatenated edge‑wise variability matrix; retain the top 10 components (`PCA_Component_1` … `PCA_Component_10`).  
  * **Variance explained** – ≥ 80 % of total variance (reported).  
  * **Stability** – Bootstrap (1 000 resamples) of component loadings; mean ± SD reported.  
* **Collinearity** – PCA orthogonalizes predictors; only the first component is used as the primary predictor, avoiding post‑hoc selection bias.

### 3. Construct Validity (Null Model)
* **Phase‑shuffled surrogate** – For each regional time series, Fourier‑transform, randomize phase, inverse‑transform, preserving the amplitude spectrum while destroying temporal ordering.  
* **Metric comparison** – Re‑compute the mean edge‑wise SD on the surrogate data; two‑sided p‑value obtained by comparing the real metric to the surrogate distribution (p < 0.05 required, FR‑008).  
* **Rationale** – Phase‑shuffling provides a stringent null that eliminates genuine dynamic connectivity while retaining autocorrelation structure, satisfying FR‑008.

### 4. Regression & Permutation Test
* **Model**: `Flexibility_Score ~ PCA_Component_1 + Age + Sex + Mean_FD + Total_Scan_Time`.  
* **Inference** – 10 000 permutations of the outcome variable; empirical p‑value = (count ≥ observed + 1) / (N + 1).  
* **Multiple comparisons** – Primary hypothesis is a single global test (FR‑005). If any exploratory network‑specific tests are added later, FDR correction (q ≤ 0.05) will be applied (FR‑009).  
* **Associational framing** – Observational data; results reported as associations, not causal effects (Constitution I).  

### 5. Power & Sample Size (Re‑affirmed)
* HCP 1200 release provides **1,200** healthy adults (source: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project).  
* After motion & quality filtering we anticipate **≥ 800** usable subjects.  
* With N≈800 the study has **> 80 % power** to detect a **medium** correlation (r ≈ 0.2) at α = 0.05 (two‑tailed). Detecting a very small effect (r = 0.05) would require > 10 000 subjects, which is not available; this limitation will be reported transparently (SC‑001).

### 6. Multiple‑Comparison & Family‑Wise Error
* Primary hypothesis is a **single global test** (FR‑005).  
* Any exploratory edge‑wise or network‑wise analyses trigger FDR correction (FR‑009).  

## Compute Feasibility (CPU‑Only)

| Component | Estimated CPU time | Memory | Mitigation |
|-----------|-------------------|--------|------------|
| Data download & checksum | < 5 min | < 2 GB (streamed) | Streaming download, no full uncompressed load |
| Parcellation (batch = 20) | ~30 min | ~1 GB per batch | Batch processing |
| Sliding‑window correlation | ~45 min | ~2 GB per batch | Vectorized NumPy; optional `numba` |
| Incremental PCA | ~10 min | < 1 GB | `sklearn.IncrementalPCA` |
| Phase‑shuffled surrogates (100 surrogates) | ~15 min | < 1 GB | Parallel across 2 cores |
| Regression & 10 000 permutations | ~60 min | < 500 MB | Vectorized; fallback to 5 000 if > 5 h |
| **Total** | **≈ 3 h** | **≤ 7 GB** | Within CI limits |

No GPU libraries are used; the pipeline will run fully on the free‑tier runner. If any step threatens the 6 h limit, the runtime guard (Phase 10) will automatically down‑sample work and log the adaptation.

## Decision Rationale

| Decision | Reason |
|----------|--------|
| **Phase 0 data‑gap check** | Guarantees compliance with Principle II; prevents silent data fabrication. |
| **60 s sliding window** | Prevents rank deficiency in a 200‑region correlation matrix; documented deviation satisfies Constitution VII. |
| **PCA reduction** | Retains > 80 % variance while keeping predictor dimensionality tractable for CPU execution. |
| **Phase‑shuffled surrogate** | Meets FR‑008’s explicit requirement and provides a stringent construct‑validity test. |
| **Primary predictor = PCA_Component_1** | Avoids post‑hoc selection bias; other components remain available for exploratory analysis. |
| **Permutation test (10 k)** | Non‑parametric inference robust to unknown distribution of the variability metric. |
| **Batch processing** | Ensures RAM stays ≤ 7 GB on CI, satisfying compute feasibility. |
| **Dedicated lint phase** | Addresses previous verifier failure (T001) with deterministic log output. |
| **Runtime guard** | Prevents CI timeout (T002) by automatically scaling down work if needed. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified URLs lack required data | Pipeline cannot proceed → project halts | Phase 0 creates explicit `gap_report.md`; no downstream fabrication. |
| Runtime > 6 h | CI job failure | Vectorized implementations; runtime guard reduces permutations or batch size. |
| Excessive subject exclusion (motion, missing scores) | Reduced statistical power | Log exclusion counts; recompute power; if N < 400, report limitation. |
| Collinearity between SD & entropy | Inflated coefficient variance | PCA orthogonalizes all edge‑wise metrics; only `PCA_Component_1` used as primary predictor. |
| Lint failures (T001) | Verification rejection | Phase 9 runs `ruff` and stores deterministic log; failures cause pipeline abort before contract testing. |
| Main script timeout (T002) | Verification rejection | Split long operations into separate phases; each phase has its own timeout guard. |

---
