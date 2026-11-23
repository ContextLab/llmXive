# Implementation Plan: Exploring the Correlation Between Musical Preference and Personality Traits

**Branch**: `001-music-personality-correlation` | **Date**: 2026-10-20 | **Spec**: [spec.md](../specs/001-music-personality-correlation/spec.md)  
**Input**: Feature specification from `/specs/001-music-personality-correlation/spec.md`

## Summary
The core requirement is to obtain a **linked dataset** containing both BFI‑2 personality scores and Last.fm listening histories for the same participants. If such a linked dataset cannot be fetched from a verified, programmatically accessible source, the pipeline aborts with a clear error message; no synthetic data are generated. When the dataset is available, the pipeline will map raw genre tags to ten standardized categories, compute proportion‑based genre scores (genre_minutes / total_minutes, with a 1‑minute pseudocount and log‑transform), compute **Pearson** correlation coefficients, run multiple linear regressions controlling for age, gender, and country, apply Bonferroni correction, conduct diagnostic checks, and produce visualizations plus a CSV report with Cohen’s d effect sizes and 95 % confidence intervals.

All methods are CPU‑first and comfortably fit within the GitHub Actions free‑tier runner; no GPU resources are needed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `pycoda==0.5.0`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `datasets==2.20.0`, `pyyaml==6.0.2`, `jsonschema==4.23.0`  
- **Storage**: `data/` for raw and processed files; `results/` for figures, reports, logs.  
- **Testing**: `pytest==8.2.2` with contract validation via `jsonschema`.  
- **Target Platform**: Linux (GitHub Actions free‑tier) – **CPU‑first**; no GPU required.  
- **Constraints**: RAM ≤ 7 GB, Disk ≤ 14 GB, total runtime ≤ 6 h, ingestion time ≤ 300 s (FR‑001).  

All methods are CPU‑tractable and will run within the free‑tier CI environment.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | Fixed random seeds; deterministic scripts; data fetched from verified BFI‑2 URL on every run; aborts if linked dataset missing. |
| **II. Verified Accuracy** | Only the BFI‑2 dataset is used because it has a verified URL. No unverified Last.fm data are introduced. |
| **III. Data Hygiene** | SHA‑256 checksums recorded; raw BFI file immutable; all transformations write new files with provenance metadata. |
| **IV. Single Source of Truth** | Every figure/table derives from `results_report.csv`. |
| **V. Versioning Discipline** | Artifact hashes stored; CI updates `state/projects/...yaml` automatically. |
| **VI. Statistical Transparency** | Exact statistical workflow (Pearson, ILR, Bonferroni, bootstrap CIs, diagnostics) is codified; no manual parameter tweaking. |
| **VII. Ethical Use** | No PII retained; user IDs hashed; licensing preserved. |

## Project Structure
```
specs/001-music-personality-correlation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis_output.schema.yaml
    ├── correlation_results.schema.yaml
    ├── dataset.schema.yaml
    ├── processed_dataset.schema.yaml
    ├── regression_results.schema.yaml
    ├── report.schema.yaml
    └── results.schema.yaml

src/
├── __init__.py
├── data/
│   ├── __init__.py
│   └── ingestion.py
├── analysis/
│   ├── __init__.py
│   ├── preprocess.py
│   ├── stats.py
│   └── report.py
└── cli/
    └── run_pipeline.py

tests/
├── __init__.py
├── contract/
│   └── test_contracts.py
└── unit/
    ├── test_ingestion.py
    ├── test_preprocess.py
    └── test_stats.py
```

*Structure Decision*: A single‑module Python package (`src/`) is sufficient; the project is a research‑oriented library, not a web or mobile app.

## Phase Mapping (FR / SC → Plan Steps)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **Phase 0 – Environment Setup** | Create `data/raw`, `data/processed`, `results`, `logs`; add empty `__init__.py` files in `src/` and `tests/`. | SC‑001 |
| **Phase 0b – Research & Design** | Draft `research.md`; select verified BFI‑2 dataset; acknowledge that the linked Last.fm dataset is unavailable, so the pipeline will abort if not present. | FR‑001 (partial), all FRs (design) |
| **Phase 1 – Data Acquisition** | Download BFI‑2 CSV via Hugging Face; compute SHA‑256 checksum; store under `data/raw/`. Abort with clear error if the linked Last.fm data cannot be obtained (i.e., `listening_history` column missing). | FR‑001, SC‑001 |
| **Phase 2 – Pre‑processing** | Validate BFI schema (`dataset.schema.yaml`); hash `user_id`; impute/exclude missing demographics (FR‑007); if genre data present, compute `total_minutes`, map raw genre tags using the lookup table (FR‑002), compute proportion scores, add 1‑minute pseudocount, log‑transform, and apply ILR transformation; write `processed_dataset.parquet`. | FR‑002, FR‑007, FR‑008, FR‑009 (when data present) |
| **Phase 3 – Correlation Computation** | Compute **Pearson** correlation coefficients for each trait–genre pair using the log‑transformed proportion scores; store in `correlation_results.csv`. | FR‑003, SC‑002 |
| **Phase 4 – Multiple‑Comparison Adjustment** | Apply Bonferroni correction (α = 0.001) → `adjusted_p_value`; flag significance. | FR‑005, SC‑012 |
| **Phase 5 – Regression Modeling** | Fit five **linear regressions** (one per trait) with ILR genre components + age + gender_onehot + country_onehot (no total minutes). Store coefficients, SE, raw p‑values. | FR‑004, SC‑004 |
| **Phase 6 – Diagnostics** | Run Shapiro‑Wilk (normality), Breusch‑Pagan (homoscedasticity), VIF (multicollinearity). Drop predictors with VIF > 5; log actions. | FR‑009, SC‑004 |
| **Phase 7 – Effect‑Size & CI** | Convert Pearson r → Cohen’s d using `d = 2r / sqrt(1 - r^2)`; bootstrap 10 000 resamples for 95 % CI; augment `correlation_results.csv`. | FR‑006, SC‑006 |
| **Phase 8 – Visualization & Reporting** | Generate heatmap `correlation_heatmap.png`; bar plot `regression_coefficients.png`; create `results_report.csv` with Cohen’s d, 95 % CI, and explicit “Non‑significant (adjusted p ≥ 0.001)” labels. | FR‑006, SC‑006 |
| **Phase 9 – Contract Validation** | Validate **all** output artifacts against their JSON‑Schema contracts: `dataset.schema.yaml`, `processed_dataset.schema.yaml`, `analysis_output.schema.yaml`, etc. Abort on any mismatch. | SC‑001 (contract compliance) |
| **Phase 10 – Clean‑up & Logging** | Write `pipeline.log` with timings, checksum info, rows/predictors dropped. | SC‑001, SC‑005 |

All phases are ordered so that data is downloaded before any processing, models are fitted before evaluation, and figures are generated before inclusion in the report.

## Timeline (within CI budget)

| Step | Approx. Runtime |
|------|-----------------|
| Directory creation & `__init__.py` | ≤ 5 s |
| BFI‑2 download & checksum | ≤ 30 s |
| Pre‑processing (validation, imputation, genre mapping if present) | ≤ 80 s |
| Correlation matrix | ≤ 30 s |
| Bonferroni adjustment | ≤ 5 s |
| Regression (5 models) | ≤ 90 s |
| Diagnostics & predictor dropping | ≤ 30 s |
| Effect‑size conversion & bootstrap CI | ≤ 25 s |
| Visualization & CSV report | ≤ 30 s |
| Contract validation & logging | ≤ 20 s |
| **Total** | **< 6 min** (well under the 6 h CI limit) |

## Failure Modes & Mitigations

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| BFI‑2 URL 404 / download error | HTTP status check; retry (max 3). | Abort with clear error; CI job fails. |
| Missing `listening_history` column (linked data absent) | Schema validation of raw BFI file (`dataset.schema.yaml`). | Abort with explicit message that the required linked dataset is unavailable. |
| Missing genre data after successful link | Check for presence of required genre columns after mapping. | Abort with message; no downstream analysis runs. |
| Sample size < required for power (not a spec requirement) | Not applicable – power analysis removed. |
| VIF > 5 for any predictor | Diagnostics phase. | Drop offending predictor, re‑fit, log warning. |
| Contract validation error | JSON‑schema validation step. | Abort with detailed mismatch report. |

## Constitution Alignment Summary
- **I. Reproducibility** – Fixed seeds, deterministic scripts, verified BFI‑2 URL; abort if linked data missing.  
- **II. Verified Accuracy** – Only the BFI‑2 dataset is used; no unverified sources introduced.  
- **III. Data Hygiene** – Checksums recorded; raw BFI file immutable; transformations write new files with provenance.  
- **IV. Single Source of Truth** – All figures/tables derive from `results_report.csv`.  
- **V. Versioning Discipline** – Artifact hashes stored; CI updates state YAML.  
- **VI. Statistical Transparency** – Full statistical pipeline codified; Pearson, Bonferroni, bootstrap CIs, diagnostics included.  
- **VII. Ethical Use** – No PII retained; user IDs hashed; licensing preserved.  

---  