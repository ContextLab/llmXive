# Implementation Plan: Exploring the Correlation Between Musical Preference and Personality Traits

**Branch**: `001-music-personality-correlation` | **Date**: 2024-08-12 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-exploring-the-correlation-between-musica/spec.md`

## Summary
The project will ingest a linked dataset containing Big Five Inventory (BFI‑2) scores and Last.fm listening histories, map raw genre tags to ten standardized categories, compute proportion‑based and raw‑minute genre preference scores, run Pearson (or Spearman when needed) correlations and multiple linear regressions with demographic covariates, apply Bonferroni correction, conduct diagnostic checks, generate visualizations, and produce a reproducible report with effect sizes and confidence intervals.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `seaborn`, `matplotlib`, `datasets` (🤗 HuggingFace), `pyyaml`, `scikit-learn` (for imputation), `click` (CLI), `pytest` (testing)  
- **Storage**: CSV files under `data/` and intermediate parquet files for streaming large inputs.  
- **Testing**: `pytest` with fixtures for synthetic data; contract validation using `jsonschema`/`pyyaml`.  
- **Target Platform**: Linux GitHub Actions runner (multiple CPU cores, sufficient RAM).  
- **Constraints**: CPU‑first execution; no GPU required.  
- **Scale/Scope**: Target ≥ 14 000 participants (as per power analysis) but will abort if the linked dataset provides fewer rows, ensuring statistical power requirements are met.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic (fixed random seeds) and fetch datasets from canonical URLs. |
| II. Verified Accuracy | All external citations limited to URLs listed in the “Verified datasets” block (BFI‑2 CSV). |
| III. Data Hygiene | Raw downloads are checksummed; transformations write new files with provenance metadata. |
| IV. Single Source of Truth | Every figure/table references a row in `data/processed/analysis_results.csv`. |
| V. Versioning Discipline | Artifacts are hashed; `state/projects/...yaml` is updated on each run. |
| VI. Statistical Transparency | Pearson, Spearman fallback, regression, Bonferroni, Cohen’s d, diagnostics are coded exactly as specified. |
| VII. Ethical Use of Public Behavioral Data | BFI‑2 accessed via HuggingFace; Last.fm data is either a real public archive (when available) or a synthetic placeholder for testing, with user IDs hashed. |

## Project Structure
```
specs/001-exploring-the-correlation-between-musica/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis_output.schema.yaml
    ├── dataset.schema.yaml
    ├── processed_dataset.schema.yaml
    ├── report.schema.yaml
    └── results.schema.yaml

src/
├── ingest/
│   ├── download.py          # fetches BFI‑2 & Last.fm data (or aborts if linked data missing)
│   └── preprocess.py        # cleaning, genre mapping, imputation, raw‑minute aggregation
├── analysis/
│   ├── power_analysis.py    # a‑priori sample‑size calculation, hard abort if N < 14 000
│   ├── correlations.py      # Pearson + diagnostics; fallback to Spearman
│   ├── regressions.py       # multiple linear regression using raw genre minutes + covariates; diagnostics, VIF, delta computation
│   └── effect_sizes.py      # Cohen’s d, CI via Fisher‑z
├── reporting/
│   ├── visualizations.py    # heatmap generation
│   └── report.py            # CSV export with effect sizes, CI, and significance labels
└── utils/
    └── logging.py

data/
├── raw/
│   ├── bfi2.csv
│   └── lastfm_synthetic.parquet   # generated only for testing; real linked dataset required for production
├── processed/
│   ├── merged_dataset.csv
│   ├── analysis_results.csv
│   ├── coefficient_deltas.csv
│   └── results_report.csv
└── checksums.txt

tests/
├── contract/
│   └── test_contracts.py
└── unit/
    ├── test_preprocess.py
    ├── test_correlations.py
    └── test_regressions.py
```

## Phase Mapping to Functional & Success Criteria
| Phase | Tasks | FRs addressed | SCs addressed |
|-------|-------|---------------|---------------|
| **0 – Research & Design** | Draft `research.md`, `data-model.md`, `quickstart.md`; define schemas. | — | — |
| **1 – Data Ingestion** | Download BFI‑2 CSV; attempt to download a **real** linked Last.fm dataset. If unavailable, abort with clear error. For CI testing, generate synthetic placeholder (`synthetic_data.py`). Clean, merge, map genres, compute total minutes, apply imputation/exclusion. | FR‑001, FR‑002, FR‑007, FR‑009, FR‑010, SC‑006 | SC‑006 |
| **2 – Power Analysis** | Compute required N for r = 0.1 at α = 0.001, 80 % power → N ≈ 14 000. **Hard abort** if actual N < 14 000; log requirement. | FR‑011 | SC‑003 |
| **3 – Correlation Computation** | Compute proportion‑based genre scores, log‑transform. Run Shapiro‑Wilk normality test and linearity check on each trait‑genre pair. If assumptions hold, compute Pearson *r*; otherwise compute Spearman ρ. Record p‑values. | FR‑003, FR‑005 | SC‑002, SC‑005 |
| **4 – Regression Modeling** | Fit 5 separate multiple linear regressions (one per trait) using **raw `listening_minutes`** per genre as predictors, plus covariates: age, gender, country (one‑hot with rare groups collapsed), **total listening minutes** (continuous). Perform diagnostics (linearity, normality of residuals, homoscedasticity, VIF). Drop predictors with VIF > 5, log warnings. Compute coefficient deltas (β_full − β_baseline) and flag >10 % change. | FR‑004, FR‑012, FR‑013 | SC‑004 |
| **5 – Effect Size & Reporting** | Convert significant *r* to Cohen’s d; compute 95 % CI via Fisher‑z. Generate heatmap PNG, create `results_report.csv` with Cohen’s d, CI, and explicit “Non‑significant (adjusted p ≥ 0.001)” labels. | FR‑006 | SC‑007 |
| **6 – Contract Validation** | Validate `merged_dataset.csv` (processed_dataset.schema.yaml), `analysis_results.csv` (analysis_output.schema.yaml), `coefficient_deltas.csv` (results.schema.yaml), and `results_report.csv` (report.schema.yaml). Abort on any mismatch. | FR‑013 | SC‑004 |
| **7 – Testing & CI** | Run unit tests, contract tests, and timing benchmark (≤ 300 s for ingestion). | All FRs | All SCs |
| **8 – Documentation** | Populate `quickstart.md` with step‑by‑step commands; ensure reproducibility instructions. | — | — |

## Edge‑Case Handling (per US‑1 & US‑2)
- **Missing data**: Rows with missing BFI scores or total listening minutes are excluded; demographic missingness handled via mean/median (numeric) or mode (categorical) imputation, logged.  
- **Zero listening minutes**: Users with `total_minutes == 0` are excluded before proportion calculation.  
- **Rare country categories**: Countries representing < 1 % of the sample are collapsed into “Other”.  
- **Collinearity**: VIF computed; any predictor with VIF > 5 is dropped with a warning.  
- **Download failures**: HTTP errors abort with clear messages; CI job fails fast (≤ 300 s).  

## Timeline (approx.)
| Week | Deliverable |
|------|-------------|
| 1 | Research doc, data model, quickstart, schemas |
| 2 | Data ingestion scripts, power analysis module |
| 3 | Correlation & regression modules, diagnostics |
| 4 | Visualization, reporting, contract validation |
| 5 | Full CI pipeline, tests, documentation polishing |
| 6 | Final review, reproducibility audit |

---

