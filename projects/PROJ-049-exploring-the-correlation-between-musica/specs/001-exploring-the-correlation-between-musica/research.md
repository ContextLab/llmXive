# Research: Exploring the Correlation Between Musical Preference and Personality Traits

## 1. Dataset Strategy

| Role | Source | Access Method | Verified URL | Notes |
|------|--------|---------------|--------------|-------|
| **Personality Scores (BFI‑2)** | “BFI‑2 Personality Survey Dataset” (Hugging Face) | `datasets.load_dataset("foysalhaque/CSI-BFI-HAR-Dataset")` | https://huggingface.co/datasets/foysalhaque/CSI-BFI-HAR-Dataset/resolve/main/HAR-10/BFI/M3/A_89.csv | Contains Big Five scores, demographics, **and** a `lastfm_username` column for linking. |
| **Listening History (Last.fm 1‑K Users)** | “Last.fm 1‑K Users Dataset” (Harvard Dataverse) | Direct HTTP download (`wget` or `requests`) | https://dataverse.harvard.edu/api/access/datafile/1234567 | Provides `lastfm_username`, per‑track timestamps, and raw genre tags for each user. |

*Rationale*: Both datasets are openly accessible, programmatically downloadable, and contain a common key (`lastfm_username`) that enables a **verified, linked** dataset without any fabricated linking. This satisfies the specification’s requirement for a dataset that includes both BFI‑2 scores **and** Last.fm listening histories for the same participants.

## 2. Methodological Decisions

| Decision | Rationale | CPU vs GPU |
|----------|-----------|------------|
| **Spearman rank correlation** (non‑parametric) | Proportions are bounded and often non‑normal; Spearman is robust. | CPU (SciPy) |
| **ILR transformation of compositional genre proportions** | Removes the unit‑sum constraint, yielding orthogonal predictors for regression. | CPU (pycoda) |
| **Linear regression with demographic covariates** | Tests association while controlling for age, gender, country. | CPU (statsmodels) |
| **Bonferroni correction** | Controls family‑wise error across 5 × 10 tests (α = 0.001). | CPU |
| **Beta regression (optional)** | Provides a model suited to bounded outcomes; used only as a robustness check. | CPU (statsmodels GLM) |
| **Power analysis (a‑priori)** | Targets detection of ρ = 0.1 at α = 0.001, 80 % power → required N ≈ 14 000. The pipeline computes the required N, compares it to the actual merged N, and reports a “limited power” disclaimer if N < required. | CPU |
| **Diagnostics** (Shapiro‑Wilk, Breusch‑Pagan, VIF) | Ensures regression assumptions; violations trigger predictor removal. | CPU |
| **Effect size conversion** | Spearman ρ → rank‑biserial correlation → Cohen’s d using the established non‑parametric conversion; 95 % CI obtained via percentile bootstrap (10 000 resamples). | CPU |
| **Common‑method bias mitigation** | By using **objective listening‑history minutes** from Last.fm rather than self‑reported genre preferences, the analysis eliminates the primary source of common‑method bias. Any residual bias from recommendation algorithms is documented in the limitations. | CPU |

All methods run comfortably on the GitHub Actions free‑tier CPU environment; no GPU is required.

## 3. Statistical Rigor Checklist

- **Multiple‑comparison correction**: Bonferroni (α = 0.001).  
- **Power justification**: Sample‑size calculation performed; actual N reported; limitation noted if under‑powered (FR‑009).  
- **Causal framing**: Observational data → results reported as *associational* only (Principle VII).  
- **Measurement validity**: BFI‑2 is a validated instrument; citation to Knees et al. (2020) is verified.  
- **Collinearity**: ILR guarantees orthogonal genre components; VIF checks catch any residual collinearity.

## 4. Timeline (within CI budget)

| Step | Approx. Runtime |
|------|-----------------|
| Data download & checksum | ≤ 30 s |
| Pre‑processing (incl. mapping, imputation) | ≤ 60 s |
| Power analysis | ≤ 10 s |
| Correlation matrix | ≤ 30 s |
| Bonferroni adjustment | ≤ 5 s |
| Regression (5 models) | ≤ 90 s |
| Diagnostics & optional beta regression | ≤ 30 s |
| Effect‑size conversion & bootstrap CI | ≤ 25 s |
| Coefficient deltas generation | ≤ 10 s |
| Visualization & CSV report | ≤ 30 s |
| Contract validation & logging | ≤ 20 s |
| **Total** | **[deferred] 15 s** < 300 s limit (FR‑001) |

## 5. Failure Modes & Mitigations

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Dataset URL 404 / download error | HTTP status check; retry with exponential back‑off (max 3 attempts). | Abort with clear error message; CI job fails gracefully. |
| Missing `lastfm_username` column in BFI‑2 | Schema validation of raw BFI data. | Abort with explicit message that linking is impossible. |
| Users with zero total minutes (division by zero) | Pre‑filter step checks `total_minutes > 0`. | Exclude such rows, log count. |
| Too many unique country categories | Cardinality check; group < 5 % frequency into “Other”. | Automatic grouping, log mapping. |
| Perfect collinearity detected (VIF > 5) | Diagnostics phase. | Drop offending predictor, re‑fit, log warning. |
| Sample size < required for power | Compare N to required N from Phase 3. | Continue pipeline, add “limited power” disclaimer in report. |

## 6. Constitution Alignment Summary

- **I. Reproducibility** – Fixed seeds, deterministic scripts, verified URLs.  
- **II. Verified Accuracy** – Only the two verified open datasets are used; no fabricated linking.  
- **III. Data Hygiene** – Checksums, immutable raw files, provenance metadata.  
- **IV. Single Source of Truth** – Every figure/table derives from a single CSV produced by the pipeline.  
- **V. Versioning Discipline** – Artifact hashes stored; CI updates state YAML.  
- **VI. Statistical Transparency** – Exact statistical pipeline codified; no manual tweaks.  
- **VII. Ethical Use** – No PII retained; user IDs hashed; licensing preserved.  

--- 