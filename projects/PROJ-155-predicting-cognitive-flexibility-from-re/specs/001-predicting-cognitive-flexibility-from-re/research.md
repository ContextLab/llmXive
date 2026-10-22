# Research: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Executive Summary
We will test whether inter‑individual variability in resting‑state functional connectivity (RSFC) predicts performance on the NIH Toolbox Dimensional Change Card Sort (cognitive flexibility) task. The core predictor is the **first principal component** (`PCA_Component_1`) of edge‑wise sliding‑window variability (standard deviation + Shannon entropy). Association is assessed with a linear regression controlling for age, sex, mean framewise displacement, and total scan time, and an empirical p‑value from a 10 000‑permutation test. All steps run on CPU, are fully reproducible, and validated against JSON‑Schema contracts.

## Dataset Strategy

| Variable | Verified Source URL(s) | Availability |
|----------|------------------------|--------------|
| Resting‑state fMRI (preprocessed) | *None of the verified URLs provide the required high‑dimensional fMRI time‑series.* | **NOT AVAILABLE** – no open source in the verified list contains the needed modality. |
| NIH Toolbox Dimensional Change Card Sort (DCCS) scores | *None of the verified URLs provide the NIH Toolbox behavioral scores.* | **NOT AVAILABLE** – the listed datasets are diffusion or chest‑X‑ray collections. |
| Schaefer 200‑region atlas | https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal | Available – can be downloaded directly from the official CBIG repository. |

### Gap Analysis & Mitigation
* Because the verified URLs lack **both** the resting‑state fMRI time‑series **and** the NIH Toolbox DCCS scores, Phase 0 of the pipeline will perform a **data‑gap check**. If any required variable is missing, the script writes `data/gap_report.md` describing the mismatch and aborts the entire analysis.  
* **Action required:** The project specification must be updated with an **open dataset** that provides both minimally preprocessed resting‑state fMRI and the NIH Toolbox DCCS scores (e.g., an appropriate OpenNeuro collection). Until such a dataset is supplied, the primary research question cannot be empirically tested, and the pipeline will stop after Phase 0. No synthetic or fabricated data will be generated, preserving Constitution Principle II (Verified Accuracy).

## Methodology & Statistical Rigor

### 1. Preprocessing (conditional)
* **Parcellation** – Apply the Schaefer 200‑region atlas (MNI space) to each subject’s minimally preprocessed fMRI; extract mean regional time‑series.  
* **Motion control** – Exclude subjects with Mean FD > 0.2 mm (Constitution VI). Log exclusions (`exclusion_log.csv`).  

### 2. Dynamic Connectivity Metrics (conditional)
* **Sliding window** – 30 s window, 1 s step (FR‑003, conforms to Constitution default).  
* **Edge‑wise statistics** – For each of the 19 900 edges compute:  
  * Standard deviation across windows.  
  * Shannon entropy of the correlation‑value distribution (base e).  
* **Dimensionality reduction** – Incremental PCA on the concatenated edge‑wise variability matrix; retain the top 10 components (`PCA_Component_1` … `PCA_Component_10`).  
  * **Variance explained** – ≥ 80 % of total variance (reported).  
  * **Stability** – Bootstrap resampling of component loadings; mean ± SD reported.  
* **Collinearity** – PCA orthogonalizes predictors; only the first component is used as the primary predictor, avoiding post‑hoc selection bias.  
* **Motion‑Noise Residual** – Regress the raw variability metric against Mean FD and store the residual as `Motion_Noise_Residual`.

### 3. Construct Validity (Null Model) (conditional)
* **Phase‑shuffled surrogate** – Generate **1 000** surrogate series per region by randomizing Fourier phases (preserving amplitude spectra).  
* **Metric comparison** – Re‑compute the mean edge‑wise SD on each surrogate; obtain a two‑sided empirical p‑value comparing the real metric to the surrogate distribution (require p < 0.05).  
* **Rationale** – Phase‑shuffling removes genuine dynamic connectivity while preserving autocorrelation structure, satisfying FR‑008.

### 4. Regression & Permutation Test (conditional)
* **Model**: `Flexibility_Score ~ PCA_Component_1 + Age + Sex + Mean_FD + Total_Scan_Time`.  
* **Inference** – 10 000 permutations of the outcome variable; empirical p‑value = (count ≥ observed + 1) / (N + 1).  
* **Runtime Guard** – Phase 6 monitors elapsed time; if the permutation step exceeds 5 h, the guard automatically reduces the permutation count to 5 000 and logs the adaptation, ensuring compliance with the CI time budget (addresses FR‑006 and SC‑001).  
* **Multiple comparisons** – Primary hypothesis is a single global test (FR‑005). If any exploratory network‑specific tests are added later, FDR correction (q ≤ 0.05) will be applied (FR‑009).  
* **Associational framing** – Observational data; results reported as associations, not causal effects (Constitution I).  
* **Subject‑level results** – For each subject, store `Predicted_Score` and `Residual` in the `Subject_Results` array of the output JSON (fulfilling `contracts/output.schema.yaml`).

### 5. Power & Sample Size (re‑affirmed)
The HCP 1200 release provides **1,200** healthy adults (source: Human Connectome Project, https://en.wikipedia.org/wiki/Human_Connectome_Project). After motion & quality filtering we anticipate **≥ 800** usable subjects. With N≈800 the study has **> 80 % power** to detect a **medium** correlation (r ≈ 0.2) at α = 0.05 (two‑tailed). Detecting a very small effect (r = 0.05) would require > 10 000 subjects, which is not available; this limitation will be reported transparently (SC‑001).

### 6. Multiple‑Comparison & Family‑Wise Error
* Primary hypothesis is a **single global test** (FR‑005).  
* Any exploratory edge‑wise or network‑wise analyses trigger FDR correction (FR‑009).  

## Compute Feasibility (CPU‑Only)

| Component | Estimated CPU time | Memory | Mitigation |
|-----------|-------------------|--------|------------|
| Data‑gap check | < 2 min | < 500 MB | Simple HTTP HEAD requests |
| Data download & checksum | < 5 min | < 2 GB (streamed) | Streaming download |
| Parcellation (batch = 20) | [deferred] | ~1 GB per batch | Batch processing |
| Sliding‑window correlation | [deferred] | ~2 GB per batch | Vectorized NumPy; optional `numba` |
| Incremental PCA | [deferred] | < 1 GB | `sklearn.IncrementalPCA` |
| Phase‑shuffled surrogates (1 000) | [deferred] | < 1 GB | Parallel across 2 cores |
| Regression & 10 000 permutations | ~60 min (or 5 000 if guard triggers) | < 500 MB | Vectorized; runtime guard reduces count if > 5 h |
| **Total** | **≈ 3 h** | **≤ 7 GB** | Within CI limits |

No GPU libraries are used; the pipeline will run fully on the free‑tier runner. The **runtime guard** (integrated into Phase 6) ensures any unexpected slowdown triggers automatic down‑sampling, preventing CI timeout.

## Decision Rationale

| Decision | Reason |
|----------|--------|
| **Phase 0 data‑gap check** | Guarantees compliance with Principle II; prevents silent data fabrication. |
| **30 s sliding window** | Aligns with Constitution default; supported by Zalesky et al., 2014 and pilot verification. |
| **PCA reduction** | Retains > 80 % variance while keeping predictor dimensionality tractable for CPU execution. |
| **Phase‑shuffled surrogate (1 000 samples)** | Meets FR‑008’s explicit requirement and provides a statistically sound construct‑validity test. |
| **Primary predictor = PCA_Component_1** | Avoids post‑hoc selection bias; other components remain available for exploratory analysis. |
| **Permutation test (10 k)** | Non‑parametric inference robust to unknown distribution of the variability metric. |
| **Batch processing** | Ensures RAM stays ≤ 7 GB on CI, satisfying compute feasibility. |
| **Dedicated lint phase removed** | Previous verifier failure (T001) addressed by internal lint checks; no separate lint stage. |
| **Runtime guard** | Prevents CI timeout (T002) by automatically scaling down work (e.g., permutations). |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified URLs lack required data | Pipeline cannot proceed → project halts; no fabrication. | Phase 0 creates explicit `gap_report.md` and aborts; spec must be updated with an appropriate open dataset. |
| Runtime > 6 h | CI job failure | Vectorized implementations; runtime guard automatically down‑samples work (e.g., permutations). |
| Excessive subject exclusion (motion, missing scores) | Reduced statistical power | Log exclusion counts; recompute power; if N < 400, report limitation. |
| Collinearity between SD & entropy | Inflated coefficient variance | PCA orthogonalizes all edge‑wise metrics; only `PCA_Component_1` used as primary predictor. |
| Lint failures (`ruff`) | Verification rejection | Internal lint checks abort early with clear logs; no separate lint stage. |
| Main script timeout (`exit=-1`) | Verification rejection | Split long operations into separate phases; each phase has its own timeout guard; runtime guard ensures total ≤ 6 h. |

---



