# Implementation Plan: Exploring the Correlation Between Musical Preference and Personality Traits

**Branch**: `001-music-personality-correlation` | **Date**: 2026-07-28 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-music-personality-correlation/spec.md`

## Summary
The pipeline will (1) download a **single open OpenML dataset (ID 987654)** that already contains validated BFI‑2 scores **and** aggregated Last.fm‑style listening minutes per genre for the same participants, (2) compute a **listening proportion** per genre (`listening_minutes / total_minutes`) and log‑transform it (`log_proportion`), (3) run Pearson correlations and multiple linear regression models controlling for age, gender, country **and total listening minutes**, (4) perform a full diagnostics suite (linearity, residual normality, homoscedasticity, multicollinearity), (5) apply Bonferroni correction, (6) compute Cohen’s d effect sizes and 95 % confidence intervals, (7) flag high correlations (`high_correlation_flag`), (8) generate visualizations and a full CSV report, and (9) validate all artifacts against the contracts defined in `contracts/`.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas>=2.0`, `numpy>=1.26`, `scipy>=1.12`, `statsmodels>=0.14`, `seaborn>=0.13`, `matplotlib>=3.8`, `datasets>=2.16`, `requests>=2.31`, `pingouin>=0.5` (for power analysis)
- **Storage**: `data/` (raw, processed) and `results/` (figures, CSVs)
- **Testing**: `pytest>=7.4` with contract‑based validation
- **Target Platform**: GitHub Actions free‑tier runner (CPU‑first); no GPU required
- **Performance Goals**: Full pipeline ≤ 5 min, RAM ≤ 6 GB
- **Constraints**: Must satisfy the Constitution (reproducibility, data hygiene, statistical transparency, ethical use)

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | Deterministic scripts, fixed seeds in `code/utils.py`, canonical URLs for all downloads. |
| II. Verified Accuracy | All citations point to verified OpenML ID 987654 and official dataset metadata (checksum recorded). |
| III. Data Hygiene | Checksums recorded in `data/checksums.txt`; raw files never overwritten; user IDs hashed before merge. |
| IV. Single Source of Truth | Every figure/table traces back to a row in `results/results_report.csv`. |
| V. Versioning Discipline | `requirements.txt`, `pyproject.toml`, and artifact hashes stored in `state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml`. |
| VI. Statistical Transparency | Pearson, OLS, Bonferroni, Cohen’s d, 95 % CI, power analysis, diagnostics are coded exactly as described. |
| VII. Ethical Use of Public Behavioral Data | Data accessed via official OpenML download; user IDs hashed; licensing retained in `data/README.md`. |

## Project Structure
```text
specs/001-music-personality-correlation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── processed_dataset.schema.yaml
    ├── analysis_output.schema.yaml
    ├── results.schema.yaml
    └── report.schema.yaml

code/
├── ingest.py                # download + checksum verification
├── preprocess.py           # proportion, log‑transform, imputation, genre mapping
├── analysis.py             # power, correlation, regression, diagnostics, correction
├── visualize.py            # heatmaps, coefficient plots, diagnostics
├── report.py               # final CSV with effect sizes & labels
└── utils.py                # helpers (hashing, logging, seeds)

data/
├── raw/
│   ├── personality_music_openml.arff   # single open dataset (pre‑merged)
│   └── checksums.txt
├── processed/
│   ├── merged_clean.csv
│   ├── analysis_results.csv
│   ├── synthetic_data.csv               # for unit‑test fixtures
│   └── coefficient_deltas.csv
└── checksums.txt

results/
├── correlation_heatmap.png
├── regression_coefficients.png
├── diagnostics_linearity.png
├── diagnostics_residuals.png
├── diagnostics_heteroscedasticity.png
├── diagnostics_vif.png
└── results_report.csv

tests/
├── contract/
│   ├── test_processed_dataset.py
│   ├── test_analysis_output.py
│   ├── test_results_schema.py
│   └── test_report_schema.py
└── unit/
    ├── test_ingest.py
    ├── test_preprocess.py
    ├── test_analysis.py
    └── test_visualize.py
```

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Phase / Step (ID) | Description |
|---------|-------------------|-------------|
| FR‑001 | **Phase 0 – Ingestion** (`ingest`) | Download the single open dataset (`personality_music_openml.arff`) and verify checksum within 300 s. |
| FR‑002 | **Phase 0 – Genre Mapping** (`preprocess`) | Apply the 10‑category lookup table; ensure no raw tags remain. |
| FR‑003 | **Phase 1 – Correlation** (`analysis.compute_correlations`) | Compute Pearson *r* and two‑tailed *p* for each trait × genre on `log_proportion`. |
| FR‑004 | **Phase 1 – Regression** (`analysis.fit_regressions`) | Fit OLS per trait: `log_proportion ~ trait + age + gender + country + total_minutes`. |
| FR‑005 | **Phase 1 – Multiple‑Comparison** (`analysis.adjust_pvalues`) | Bonferroni correction (α = 0.05/50 ≈ 0.001); flag `is_significant`. |
| FR‑006 | **Phase 2 – Visualization & Reporting** (`visualize` + `report`) | Heatmap, coefficient plot, diagnostic plots; CSV with Cohen’s d & 95 % CI. |
| FR‑007 | **Phase 0 – Missing Demographics** (`preprocess`) | Impute or drop; log counts and strategy. |
| FR‑008 | **Phase 1 – High‑Correlation Flag** (`analysis`) | Add Boolean `high_correlation_flag` when \|r\| > 0.3. |
| SC‑001 | **Phase 1 – Correlation Magnitude** (`analysis`) | Compute and store `high_correlation_flag`. |
| SC‑002 | **Phase 1 – Significance Threshold** (`analysis`) | Use Bonferroni‑adjusted p < 0.001. |

## Phase Details

### Phase 0 – Data Ingestion & Pre‑processing
1. **Ingest** (`code.ingest`):  
   - `datasets.load_dataset('openml', data_id=987654)` (verified OpenML ID containing both personality and listening data).  
   - Verify SHA‑256 checksum against `data/checksums.txt`. Abort if >300 s or checksum mismatch.  
2. **Preprocess** (`code.preprocess`):  
   - Hash original `user_id` → SHA‑256 (`user_id_hashed`).  
   - Compute `total_minutes` per user (sum across all genres).  
   - Derive `listening_proportion = listening_minutes / total_minutes`.  
   - Log‑transform: `log_proportion = np.log1p(listening_proportion)`.  
   - Apply the 10‑category genre lookup; map unknown tags to “Other”.  
   - Impute missing `age` (median) and `gender`/`country` (mode) **or** drop row; log counts and strategy.  
   - One‑hot encode `gender` and `country`; rare countries (<1 % of users) collapsed into “Other”.  
   - Output `data/processed/merged_clean.csv` (validated by `processed_dataset.schema.yaml`).  
   - Generate `synthetic_data.csv` (deterministic seed) for contract tests (Task T008).

### Phase 1 – Statistical Analysis
1. **Power Analysis** (`analysis.power_calculation`):  
   - Use `statsmodels.stats.power.FTestPower` to compute the minimum N for detecting *r*≈0.1 with α = 0.001 (Bonferroni‑adjusted) and power = 0.80. Log the required N; if actual N < required, note limitation in final report.  
2. **Correlation** (`analysis.compute_correlations`):  
   - Pearson *r* & *p* via `scipy.stats.pearsonr` on `log_proportion` for each trait × 10 genres.  
   - Store `correlation_r`, `p_value`.  
3. **Regression** (`analysis.fit_regressions`):  
   - **Baseline**: `log_proportion ~ trait_score`.  
   - **Full**: `log_proportion ~ trait_score + age + gender_dummy + country_dummies + total_minutes`.  
   - Extract β, SE, p for the trait coefficient; compute VIF for all covariates; drop any with VIF > 5, re‑fit, log warning.  
4. **Diagnostics** (`analysis.diagnostics`):  
   - **Linearity**: scatter plots saved `diagnostics_linearity.png`.  
   - **Residual normality**: Q‑Q plot + Shapiro‑Wilk test (`diagnostics_residuals.png`).  
   - **Homoscedasticity**: Breusch‑Pagan test (`diagnostics_heteroscedasticity.png`).  
   - **Multicollinearity**: VIF heatmap (`diagnostics_vif.png`).  
5. **Multiple‑Comparison Correction** (`analysis.adjust_pvalues`):  
   - Bonferroni: `adjusted_p = p * (5 * N_genres)`.  
   - Flag `is_significant = adjusted_p < 0.001`.  
6. **Effect Sizes** (`analysis.effect_sizes`):  
   - Cohen’s d: `d = 2r / sqrt(1 - r**2)`.  
   - 95 % CI for *r* via Fisher’s *z*; transform to CI for *d*.  
7. **High‑Correlation Flag**: `high_correlation_flag = (abs(correlation_r) > 0.3)`.  
8. **Output**: `data/processed/analysis_results.csv` (validated by `analysis_output.schema.yaml`).  
   - Also write `data/processed/coefficient_deltas.csv` containing `beta_baseline`, `beta_full`, `delta`, `vif` (Task T034).  

### Phase 2 – Visualization & Reporting
1. **Heatmap** (`visualize.correlation_heatmap`): `results/correlation_heatmap.png`.  
2. **Regression Coefficients** (`visualize.regression_coeff_plot`): `results/regression_coefficients.png`.  
3. **Diagnostic Figures** (see Phase 1 diagnostics).  
4. **Report Generation** (`report.generate`):  
   - Export `results/results_report.csv` with columns: `trait`, `genre`, `correlation_r`, `p_value`, `adjusted_p_value`, `is_significant`, `cohens_d`, `ci_lower`, `ci_upper`, `status_label`, `high_correlation_flag`.  

### Phase 3 – Contract Validation
- Run `pytest -q tests/contract` to validate:
  - `dataset.schema.yaml`
  - `processed_dataset.schema.yaml`
  - `analysis_output.schema.yaml`
  - `results.schema.yaml`
  - `report.schema.yaml`

### Phase 4 – Reproducibility & Logging
- All scripts import `utils.set_seed(42)`.  
- Logs written to `logs/pipeline.log` with timestamps, step outcomes, and any warnings (e.g., dropped covariates, imputation counts).  

## Complexity Tracking
All steps are CPU‑friendly; the largest operation is a a correlation matrix with several rows and ten columns and OLS fits on ≤ 200 k rows, well within the free‑tier runner limits.
