# Research: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Executive Summary
We will test whether inter‑individual variability in resting‑state functional connectivity (RSFC) predicts performance on the NIH Toolbox Dimensional Change Card Sort (cognitive flexibility) task. The core predictor is the **first principal component** (`PCA_Component_1`) of edge‑wise sliding‑window variability (standard deviation + Shannon entropy). Association is assessed with a linear regression controlling for age, sex, mean framewise displacement, and total scan time, and an empirical p‑value from a 10 000‑permutation test. All steps are CPU‑only, reproducible, and verified against JSON‑Schema contracts.

## Dataset Strategy

| Variable | Source (Verified URLs) | Availability |
|----------|------------------------|--------------|
| **Raw resting‑state fMRI** | HCP parquet URLs (see Verified Datasets block) | **NO VERIFIED SOURCE FOUND** – the listed parquet files contain diffusion data, not the required high‑dimensional fMRI volumes. |
| **NIH Toolbox DCCS scores** | NIH CSV URLs (see Verified Datasets block) | **NO VERIFIED SOURCE FOUND** – the provided NIH Chest‑X‑ray CSVs do not contain the Dimensional Change Card Sort scores. |
| **Schaefer Atlas** | Publicly available from the CBIG repository on GitHub | Available – will be downloaded directly from the official CBIG repository. |

### Gap Analysis & Mitigation
* Because the verified URLs do **not** contain the essential fMRI time‑series nor the Flexibility scores, Phase 0 of the pipeline will attempt to load the URLs, detect the missing variables, and generate `data/gap_report.md`.  
* The pipeline will **halt** after the gap report; no synthetic data will be fabricated, satisfying Constitution Principle II (Verified Accuracy).  
* If an open dataset that includes both modalities becomes available, the plan can be updated without altering the current specification.

## Methodology & Statistical Rigor

### 1. Preprocessing
* **Parcellation** – Schaefer 200‑region atlas applied to MNI‑space fMRI; mean regional time‑series extracted.  
* **Motion control** – Subjects with Mean FD > 0.2 mm excluded (Constitution Principle VI).  
* **SNR filter** – Subjects with temporal SNR < 50 excluded; counts logged (SC‑001).

### 2. Dynamic Connectivity Metrics
* **Sliding window** – 60 s window, 1 s step (justified in Constitution Check).  
* **Edge‑wise SD & Shannon entropy** – computed for each of the 19 900 edges (200 × 199 / 2).  
* **Dimensionality reduction** – PCA on the edge‑wise variability matrix; **top 10 components** retained (`PCA_Component_1` … `PCA_Component_10`).  
    * **Variance explained** – ≥ 80 % of total variance (reported).  
    * **Stability** – Bootstrap resampling (1000 samples) yields mean ± SD of component loadings; reported in Phase 4 logs.  
* **Collinearity** – PCA orthogonalizes components; only the first component (`PCA_Component_1`) is used as the primary predictor, avoiding post‑hoc selection bias.

### 3. Construct Validity (Null Model)
* **Phase‑shuffled surrogate** – For each region, the time series is Fourier‑transformed, phase‑randomized, and inverse‑transformed, preserving the amplitude spectrum but destroying temporal ordering.  
* **Test** – Two‑sided p‑value comparing the real variability metric (mean edge SD) against the surrogate distribution (p < 0.05 required, FR‑008).  
* **Rationale** – Phase‑shuffling provides a stringent null that eliminates genuine dynamic connectivity while retaining autocorrelation structure, satisfying FR‑008 (which explicitly requires a phase‑shuffled null).

### 4. Regression & Permutation
* **Model**: `Flexibility_Score ~ PCA_Component_1 + Age + Sex + Mean_FD + Total_Scan_Time`.  
* **Inference** – 10 000 permutations of the outcome variable; empirical p‑value = (count ≥ obs + 1) / (N + 1).  
* **Multiple comparisons** – Primary hypothesis is a **single global test**. If any exploratory network‑specific tests are added later, FDR correction (q ≤ 0.05) will be applied (FR‑009).  
* **Associational framing** – Observational data; results reported as associations, not causal effects (Constitution Principle I).  

### 5. Power & Sample Size (Revised)
* The HCP 1200 release provides up to **1,200** healthy adults (source: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project).  
* After motion and quality filtering we anticipate **≥ 800** usable subjects.  
* With N≈800 the study has **> 80 % power to detect a medium effect** (r ≈ 0.2) at α = 0.05 (two‑tailed). Detecting a very small effect (r = 0.05) would require > 10 000 subjects, which is not available; this limitation will be reported transparently.  

### 6. Multiple‑Comparison & Family‑Wise Error
* Primary hypothesis is a **single global test** (FR‑005).  
* Any exploratory edge‑wise or network‑wise analyses trigger FDR correction (FR‑009).  

## Compute Feasibility (CPU‑Only)

| Component | Estimated CPU Cost | Memory Footprint | Mitigation |
|-----------|-------------------|------------------|------------|
| Data download & checksum | < 5 min | < 2 GB (streamed) | Streaming download, no full uncompressed load |
| Parcellation (200 regions) | [deferred] (batch = 20) | ~1 GB per batch | Batch processing |
| Sliding‑window correlation (60 s) | [deferred] | ~2 GB per batch | Vectorized NumPy, optional `numba` |
| PCA (edge‑wise matrix) | [deferred] | < 1 GB | Incremental PCA (`sklearn.decomposition.IncrementalPCA`) |
| Phase‑shuffled surrogate (100 surrogates) | [deferred] | < 1 GB | Parallel across 2 CPU cores |
| Regression & 10 000 permutations | ~60 min | < 500 MB | Permutation vectorized; fallback to 5 000 if runtime > 5 h |
| **Total** | **≈ 3 h** | **≤ 7 GB** | Within CI limits |

No GPU libraries are used; the pipeline will run fully on the free‑tier runner. If any step exceeds resources, the script will automatically down‑sample (e.g., reduce permutations) and log the change.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Phase 0 data‑gap check** | Guarantees compliance with Principle II; avoids silent data fabrication. |
| **60 s window** | Prevents rank deficiency in a 200‑region correlation matrix; documented deviation satisfies Constitution Check. |
| **PCA reduction** | Retains network‑specific variance while keeping predictor dimensionality tractable for CPU execution. |
| **Phase‑shuffled surrogate** | Meets FR‑008's requirement for a phase‑shuffled null and provides a stringent test of dynamic structure. |
| **Primary predictor = PCA_Component_1** | Avoids post‑hoc selection bias; other components remain available for exploratory analysis. |
| **Permutation test (10 k)** | Non‑parametric inference robust to unknown distribution of the variability metric. |
| **Batch processing** | Ensures RAM stays < 7 GB on CI, satisfying compute feasibility. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Verified URLs lack required data** | Pipeline cannot proceed → project halts. | Phase 0 generates explicit `gap_report.md`; no downstream fabrication. |
| **Runtime > 6 h** | CI job failure. | Vectorized code, optional down‑sampling of permutations, runtime guard. |
| **Excessive subject exclusion** | Reduced statistical power. | Log exclusion counts; recompute power; if N < 400, report limitation. |
| **Collinearity between SD & Entropy** | Inflated variance of coefficients. | Use PCA to orthogonalize; report variance explained; do not claim independent effects. |

---
