# Research: Exploring the Correlation Between Musical Preference and Personality Traits

## Objective
Determine whether Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) are statistically associated with preferences for ten standardized musical genres, after controlling for age, gender, country, and total listening minutes.

## Methodology Overview
1. **Data Acquisition** – Retrieve an open‑source BFI‑2 dataset (verified HuggingFace URL) and a **real, linked Last.fm listening‑history archive** if one is publicly available.  
   - If a genuine linked dataset cannot be fetched, the pipeline aborts with a clear error (preserving FR‑001).  
   - For CI testing, a reproducible synthetic placeholder (`synthetic_data.py`) can be generated; this is **not** used for final scientific conclusions.
2. **Pre‑processing** – Clean, merge, map raw genre tags to ten categories, compute total listening minutes per user, generate proportion‑based genre scores, log‑transform, and handle missing demographics via imputation or exclusion (with logging).  
3. **Power Analysis** – Perform an a‑priori power calculation targeting detection of Pearson *r* = 0.1 at α = 0.001 (Bonferroni‑adjusted) with [deferred] power. Required N ≈ 14 000. **If the actual sample size is below this threshold, the run aborts**; no downstream analysis proceeds.
4. **Correlation Analysis** – For each trait‑genre pair, first test Pearson assumptions (Shapiro‑Wilk normality of both variables, linearity via scatter plots).  
   - If assumptions hold, compute Pearson *r* and two‑tailed p‑value.  
   - If any assumption fails, compute Spearman ρ instead and note the fallback in the results.  
5. **Multiple Linear Regression** – Fit five separate regression models (one per trait) using **raw `listening_minutes`** per genre as predictors, plus covariates: age (continuous), gender (categorical), country (one‑hot, rare groups collapsed), and total listening minutes (continuous).  
   - Run diagnostic checks: residual normality (Shapiro‑Wilk, p > 0.05), homoscedasticity (Breusch‑Pagan, p > 0.05), and multicollinearity (VIF ≤ 5).  
   - Drop any offending predictor, log a warning, and recompute the model.  
   - Compute beta coefficients, standard errors, and delta between baseline (trait only) and full models; flag deltas > 10 % as “exceeds_threshold”.  
6. **Multiple‑Comparison Correction** – Apply Bonferroni correction for the 50 hypothesis tests (α = 0.001). Flag results as “significant” only if adjusted p < 0.001.  
7. **Effect Size & Confidence Intervals** – Convert significant Pearson *r* (or Spearman ρ) to Cohen’s d; compute 95 % confidence intervals via Fisher‑z transformation.  
8. **Visualization & Reporting** – Produce a heatmap PNG of the correlation matrix, and a CSV report (`results_report.csv`) containing beta coefficients, standard errors, adjusted p‑values, Cohen’s d, 95 % CI, and explicit “Non‑significant (adjusted p ≥ 0.001)” labels.  

## Dataset Strategy

| Dataset | Source (Verified) | Access Method | Notes |
|---------|-------------------|---------------|-------|
| **BFI‑2 Personality Scores** | <https://huggingface.co/datasets/foysalhaque/CSI-BFI-HAR-Dataset/resolve/main/HAR-10/BFI/M3/A_89.csv> (verified) | `datasets.load_dataset("foysalhaque/CSI-BFI-HAR-Dataset", split="train")` | Contains validated BFI‑2 items for each participant. |
| **Last.fm Listening History** | **No verified open source URL**. The specification requires a linked dataset; currently none is publicly available. The pipeline therefore **aborts** if a real linked dataset is not supplied. For development and CI testing, a deterministic synthetic placeholder (`synthetic_data.py`) is generated, matching the schema in `contracts/dataset.schema.yaml`. | Synthetic generation script (`code/synthetic_data.py`) → `data/raw/lastfm_synthetic.parquet` | Placeholder is **only** for testing the pipeline mechanics; it does **not** satisfy FR‑001 for the final scientific analysis. |

> **Rationale**: The constitution’s Verified Accuracy principle forbids using unverified URLs. Since a publicly downloadable, consented linked BFI‑2 + Last.fm dataset does not exist, we must either obtain such a dataset (outside the scope of this plan) or abort. The synthetic placeholder enables CI verification without violating FR‑001.

## Statistical Rigor Checklist
- **Multiple‑Comparison Correction**: Bonferroni (α = 0.001) for 50 tests.  
- **Power Analysis**: Target r = 0.1, α = 0.001, 80 % power → N ≈ 14 000 (FR‑011). Hard abort if N < 14 000.  
- **Causal Framing**: Observational study; all statements are associational.  
- **Measurement Validity**: BFI‑2 is a validated instrument (cite original BFI‑2 validation paper).  
- **Collinearity**: VIF computed; predictors with VIF > 5 are dropped per FR‑012.  

## Decision / Rationale (Compute Feasibility)
- All statistical computations (diagnostics, Pearson/Spearman, regressions, diagnostics) are **CPU‑friendly** and will run within the CI runner’s limits.  
- No GPU‑required models are used; the pipeline stays entirely on CPU.  
- The synthetic placeholder is sufficiently small to guarantee memory safety; the real linked dataset (if obtained) will be streamed if it exceeds RAM limits.

## Deliverables
- `data/processed/merged_dataset.csv` (validated against `contracts/processed_dataset.schema.yaml`).  
- `data/processed/analysis_results.csv` (validated against `contracts/analysis_output.schema.yaml`).  
- `data/processed/coefficient_deltas.csv` (validated against `contracts/results.schema.yaml`).  
- `results/correlation_heatmap.png`.  
- `results/results_report.csv` (validated against `contracts/report.schema.yaml`).  
- All artifacts validated against their respective schemas (FR‑013).  

---

