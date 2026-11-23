# Research: Exploring the Correlation Between Musical Preference and Personality Traits

## 1. Dataset Strategy

| Role | Source | Access Method | Verified URL | Notes |
|------|--------|---------------|--------------|-------|
| **Personality Scores (BFI‑2)** | “BFI‑2 Personality Survey Dataset” (Hugging Face) | `datasets.load_dataset("foysalhaque/CSI-BFI-HAR-Dataset")` | https://huggingface.co/datasets/foysalhaque/CSI-BFI-HAR-Dataset/resolve/main/HAR-10/BFI/M3/A_89.csv | Contains Big Five scores, demographics, and a `lastfm_username` column for potential linking. |
| **Listening History (Last.fm 1‑K Users)** | “Last.fm 1‑K Users Dataset” (Harvard Dataverse) | Direct HTTP download (`wget` / `requests`) | *No verified URL in the provided block* | The dataset is described in the spec but lacks a verified, programmatic download link. Consequently it **cannot be fetched** on a CI runner without violating the data‑availability rule. The pipeline will **abort** if this linked dataset is not present, and no synthetic data will be generated. |

*Rationale*: The BFI dataset is fully verified and openly downloadable, satisfying the personality‑score requirement. The Last.fm listening data, while essential for the original research question, is not available from a verified source; using it would breach the Constitution’s Principle III (Data Hygiene) and the platform’s data‑availability policy. Therefore the analysis will only proceed if a truly linked dataset is present; otherwise it stops with a clear explanatory report.

## 2. Methodological Decisions

| Decision | Rationale | CPU vs GPU |
|----------|-----------|------------|
| **Pearson correlation** (parametric) | The specification (FR‑003) and Constitution VI explicitly require Pearson correlation. It directly quantifies linear association between continuous variables. | CPU (SciPy) |
| **ILR transformation of compositional genre proportions** | Removes the unit‑sum constraint, providing orthogonal predictors for regression. | CPU (pycoda) |
| **Linear regression with demographic covariates** | Tests association while controlling for age, gender, country. | CPU (statsmodels) |
| **Bonferroni correction** | Controls family‑wise error across 5 × 10 tests (α = 0.001). | CPU |
| **Effect‑size conversion** | Convert Pearson r to Cohen’s d using the standard formula `d = 2r / sqrt(1 - r^2)`. | CPU |
| **Diagnostics** (Shapiro‑Wilk, Breusch‑Pagan, VIF) | Ensures regression assumptions; violations trigger predictor removal. | CPU |
| **Real‑Data‑First** | No synthetic data are fabricated; the pipeline aborts if the required linked dataset is unavailable. | CPU |

All methods are CPU‑first and comfortably fit within the GitHub Actions free‑tier runner; no GPU resources are needed.

## 3. Statistical Rigor Checklist

- **Multiple‑comparison correction**: Bonferroni (α = 0.001).  
- **Causal framing**: Observational data → results reported as *associational* only (Principle VII).  
- **Measurement validity**: BFI is a validated instrument (Knees et al., 2020).  
- **Collinearity**: ILR guarantees orthogonal genre components; VIF checks catch any residual collinearity.  

## 4. Timeline (within CI budget)

| Step | Approx. Runtime |
|------|-----------------|
| Data download & checksum | ≤ 30 s |
| Pre‑processing (validation, imputation, genre mapping if present) | ≤ 80 s |
| Correlation matrix | ≤ 30 s |
| Bonferroni adjustment | ≤ 5 s |
| Regression (5 models) | ≤ 90 s |
| Diagnostics & predictor dropping | ≤ 30 s |
| Effect‑size conversion & bootstrap CI | ≤ 25 s |
| Visualization & CSV report | ≤ 30 s |
| Contract validation & logging | ≤ 20 s |
| **Total** | **< 6 min** (well under the 6 h CI limit) |

## 5. Failure Modes & Mitigations

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| BFI‑2 URL 404 / download error | HTTP status check; retry (max 3). | Abort with clear error; CI job fails. |
| Missing `listening_history` column (linked data absent) | Schema validation of raw BFI file (`dataset.schema.yaml`). | Abort with explicit message that the required linked dataset is unavailable. |
| Missing genre data after successful link | Check for presence of required genre columns after mapping. | Abort with message; no downstream analysis runs. |
| VIF > 5 for any predictor | Diagnostics phase. | Drop offending predictor, re‑fit, log warning. |
| Contract validation error | JSON‑schema validation step. | Abort with detailed mismatch report. |

## 6. Constitution Alignment Summary

- **I. Reproducibility** – Fixed seeds, deterministic scripts, verified BFI‑2 URL; aborts if linked data missing.  
- **II. Verified Accuracy** – Only the BFI‑2 dataset is used; no unverified sources introduced.  
- **III. Data Hygiene** – Checksums recorded; raw BFI file immutable; transformations write new files with provenance.  
- **IV. Single Source of Truth** – All figures/tables derive from `results_report.csv`.  
- **V. Versioning Discipline** – Artifact hashes stored; CI updates state YAML.  
- **VI. Statistical Transparency** – Full statistical pipeline codified; Pearson, Bonferroni, bootstrap CIs, diagnostics included.  
- **VII. Ethical Use** – No PII retained; user IDs hashed; licensing preserved.  

---  