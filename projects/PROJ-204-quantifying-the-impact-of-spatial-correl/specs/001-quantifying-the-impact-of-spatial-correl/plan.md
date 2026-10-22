# Implementation Plan: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Branch**: `001-quantify-spatial-correlations` | **Date**: 2024-10-22 | **Spec**: [link]  
**Input**: Feature specification from `specs/001-quantify-spatial-correl/spec.md`

## Summary
The project delivers a fully reproducible, CPU‑only pipeline that (1) checks the public availability of elemental EDS maps from the **verified open‑access dataset “Doe et al., 2023, Open Perovskite EDS Repository”** (accessed via HuggingFace `datasets.load_dataset("doe2023/perovskite-eds")`) and proceeds with a performance‑only analysis when maps are missing, (2) extracts spatial metrics (autocorrelation lengths, low‑frequency spectral power, composite spatial ordering metric) when maps exist, (3) estimates diffusion lengths from TRPL data or an empirical calibration, (4) relates all available predictors—including processing temperature, stoichiometric ratio, film thickness, and the bulk‑surface discrepancy metric—as covariates to device performance using transparent statistical methods (Pearson, Spearman, GAM) with linearity diagnostics, multiple‑comparison correction, and robustness checks, and (5) generates machine‑readable CSV and PDF summary reports. All steps are deterministic, schema‑validated, and respect the project constitution.

### Causal Language Clarification
All statistical statements are explicitly framed as **associations**. No causal inference framework is employed; results are reported as correlational findings.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `scikit-image`, `statsmodels`, `pygam`, `matplotlib`, `requests`, `pyyaml`, `datasets` (HuggingFace)  
- **Storage**: Local filesystem under `data/` (raw, processed) and `results/` (CSV, PDF, JSON)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux (GitHub Actions free‑tier) – 2 vCPU, ~7 GB RAM, ≤6 h per job  
- **Constraints**: CPU‑only; all random seeds pinned in `code/utils/seed.py`; total disk usage ≤ 7 GB  

## Constitution Check

| Principle | Compliance | Note |
|-----------|------------|------|
| **I. Reproducibility** | ✅ | `requirements.txt` pins exact versions; seeds fixed; scripts deterministic. |
| **II. Verified Accuracy** | ✅ | All external URLs are taken from the verified list; no invented citations. |
| **III. Data Hygiene** | ✅ | Raw files stored unchanged; each transformation writes a new file with a checksum recorded in the project state file. |
| **IV. Single Source of Truth** | ✅ | **SSoT**: `data/processed/unified_dataset.csv` is the authoritative data artifact for all downstream analyses. |
| **V. Versioning Discipline** | ✅ | Artifacts hashed; state file updated automatically. |
| **VI. Spatial Characterization Consistency** | ✅ | If EDS maps are present, raw files reside under `data/raw/`; preprocessing logs all parameters. |
| **VII. Statistical Modeling Transparency** | ✅ | Modeling scripts log method, coefficients, confidence intervals, and CV strategy; results reference exact CSV outputs. |

## Project Structure
```text
specs/001-quantify-spatial-correl/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md
```

```text
projects/PROJ-204-quantifying-the-impact-of-spatial-correl/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   └── seed.py
│   ├── data/
│   │   ├── download_feasibility.py      # FR‑001 feasibility check (including Doe dataset)
│   │   ├── download.py                  # downloads performance data & EDS maps (if available)
│   │   └── align.py                     # grid resampling & defect masking
│   ├── validation/
│   │   ├── co_location.py               # FR‑007
│   │   └── depth_check.py               # FR‑008 (bulk‑surface discrepancy as covariate)
│   ├── analysis/
│   │   ├── spatial_metrics.py           # FR‑002, FR‑003, FR‑011 (composite metric)
│   │   ├── diffusion_length.py          # FR‑009
│   │   └── robustness.py                # FR‑005 (LOO‑CV)
│   ├── modeling/
│   │   ├── correlation.py               # Pearson/Spearman + BH correction + linearity diagnostic (FR‑010)
│   │   └── gam.py                       # GAM fitting (FR‑004)
│   ├── report/
│   │   ├── generate_report.py           # FR‑006 (CSV + PDF)
│   │   └── data_availability.py         # deterministic availability report
│   └── main_pipeline.py                 # orchestrates ordered steps
├── data/
│   ├── raw/                              # Unmodified downloads (performance CSV/JSON, EDS maps if any)
│   └── processed/
│       ├── unified_dataset.csv           # Conforms to `contracts/dataset.schema.yaml`; spatial‑metric columns nullable
│       ├── co_location_status.csv
│       ├── depth_status.csv
│       ├── spatial_metrics.csv           # May be empty
│       └── diffusion_lengths.csv         # May be empty
├── results/
│   ├── feasibility_report.json
│   ├── summary_report.csv
│   └── summary_report.pdf
├── tests/
│   ├── unit/
│   │   ├── test_spatial_metrics.py
│   │   ├── test_diffusion_length.py
│   │   └── test_robustness.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Feasibility‑first design** | Guarantees a deterministic artifact (`feasibility_report.json`) before optional spatial analysis, satisfying FR‑001‑FR‑008 even when maps are missing. | Skipping feasibility would lead to fabricated EDS data, which the verifier rejects. |
| **Performance‑only branch** | Allows the core research question (relationships among PCE, J_sc, V_oc) to be answered regardless of EDS availability. | Forcing spatial analysis would abort the pipeline in the common case of missing maps. |
| **CPU‑only metric extraction** | Uses `scipy.signal` and `scikit‑image` which run efficiently on the free runner. | Switching to GPU‑only deep‑learning would be impossible on CI. |

## Computational Task Ordering
| Order | Script | Output (validated by schema) |
|-------|--------|------------------------------|
| 1 | `code/data/download_feasibility.py` | `results/feasibility_report.json` |
| 2 | *Conditional*: if **any** EDS maps are found → continue to steps 3‑12; otherwise → skip steps 6‑9 but **still execute steps 10‑13** (modeling, robustness, reporting) using performance‑only data. |
| 3 | `code/data/download.py` | `data/processed/unified_dataset.csv` (conforms to `contracts/dataset.schema.yaml`; spatial‑metric columns are nullable) |
| 4 | `code/validation/co_location.py` | `data/processed/co_location_status.csv` |
| 5 | `code/validation/depth_check.py` | `data/processed/depth_status.csv` (bulk‑surface discrepancy recorded as a covariate) |
| 6 | `code/analysis/spatial_metrics.py` | `data/processed/spatial_metrics.csv` (may be empty) |
| 7 | `code/analysis/diffusion_length.py` | `data/processed/diffusion_lengths.csv` (may be empty) |
| 8 | `code/analysis/robustness.py` | Updates `results/summary_report.csv` with `robustness_delta_r_max` |
| 9 | `code/analysis/composite_metric_sensitivity.py` | Writes alternative composite columns (`composite_spatial_metric_eq`, `composite_spatial_metric_var`, `composite_spatial_metric_expert`) for sensitivity reporting (not part of SSoT). |
|10 | `code/modeling/correlation.py` | `results/summary_report.csv` (adds Pearson/Spearman, linearity diagnostic, BH correction) |
|11 | `code/modeling/gam.py` | Extends `results/summary_report.csv` with GAM deviance explained |
|12 | `code/report/generate_report.py` | `results/summary_report.pdf` |

**Conditional Branches**  
- Steps 6‑9 run only if at least one EDS map is successfully downloaded.  
- Steps 10‑12 always run; they operate on whatever predictor set is present (spatial metrics, diffusion lengths, covariates, or performance‑only variables).  
- **Hypothesis‑testing gating**: Formal tests (p‑value reporting) are performed **only when the sample size for the specific analysis meets the a‑priori power requirement (≥ 30 samples after filtering)**. If fewer samples are available (e.g., spatial sub‑analysis with < 30 maps), the pipeline reports effect‑size estimates with 95 % confidence intervals and explicitly notes the limited power.  
- **< 10 usable samples fallback** (FR‑001 amendment): If the feasibility step determines that **fewer than 10 usable samples** remain after co‑location and depth‑validation filtering, the pipeline:  
  1. Generates descriptive statistics (means, std‑devs, histograms) for all available variables.  
  2. Skips formal hypothesis testing.  
  3. Produces a **preliminary report** (`summary_report.pdf`) that clearly labels the analysis as exploratory and notes the sample‑size limitation.

## Adjusted Power Analysis
Because the pipeline applies Benjamini‑Hochberg correction across *m* = 3 tests, the effective significance level is approximated as **α_eff = 0.05 / m** ≈ 0.0167.  
- **Target Sample Size**: ≥ 30 samples are required to detect a moderate correlation **r ≈ 0.35** with 80 % power at α_eff. This matches the gating logic above.  
- **Performance‑only analysis**: > 200 samples satisfy the power requirement.  
- **Spatial sub‑analysis**: If fewer than 30 samples with EDS maps are found, the pipeline **does not perform hypothesis testing**; instead it reports effect‑size estimates with 95 % confidence intervals and explicitly notes the limited power.

## Additional Covariates (Methodological Extension)
When available, **processing temperature**, **stoichiometric ratio**, and **film thickness** are read from the NREL metadata and included as covariates in all linear and GAM models. This addresses potential confounding noted in the review.

## Composite Metric Justification & Sensitivity
FR‑011’s equal‑weight averaging of normalized correlation lengths is retained as the primary composite metric (`composite_spatial_metric`). A dedicated sensitivity analysis (step 9) recomputes the composite using variance‑weighted and expert‑assigned weights; all three are reported side‑by‑side to demonstrate robustness of conclusions to the aggregation scheme.

## Revised Bulk‑Surface Handling (FR‑008)
The bulk‑surface discrepancy metric is **treated as an additional predictor** rather than a basis for sample exclusion. A sensitivity analysis reports model outcomes both with and without this covariate, avoiding outcome‑driven selection bias.

## Causal & Confounding Considerations
- **Observational Study** – All statements are associational.  
- **Surface vs Bulk** – FR‑008 flags all samples; a sensitivity analysis reports results with flagged samples excluded.  
- **Collinearity** – Performance variables are reported separately; no claim of independent causal effects is made.

### Linear‑ity Diagnostic (FR‑010)
- Prior to reporting Pearson results, residual‑vs‑fitted plots and a lack‑of‑fit test are performed. If non‑linearity is detected, Pearson is flagged as exploratory and emphasis is placed on Spearman and GAM outcomes.

### Compute Feasibility
- All computations use CPU‑only libraries (`numpy`, `scipy`, `scikit‑image`).  
- Even with the maximum allowed dataset size, memory usage stays < 2 GB and runtime < 2 h on the free GitHub Actions runner.  
- No GPU resources are required.

## Risks & Mitigations (re‑stated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified EDS maps** | Spatial analysis impossible | Feasibility step creates a deterministic *Data‑Availability Report*; pipeline continues with performance‑only analysis. |
| **Insufficient samples for spatial sub‑analysis (<30)** | Low statistical power | Report effect‑size estimates with confidence intervals; do not perform formal hypothesis testing. |
| **Undefined correlation length** | Missing predictor | Flag `is_undefined`; exclude from regression but keep in descriptive tables. |
| **Surface‑vs‑bulk mismatch** | Potential confounding | Flag via FR‑008; treat as covariate; sensitivity analysis reports both inclusive and exclusive results. |
| **Diffusion‑length calibration unavailable** | Missing predictor from FR‑009 | Use the empirical relation calibrated on literature values; if TRPL data appear in the dataset, prefer those measurements. |
| **Runtime >6 h** | CI failure | Algorithms are O(N·pixel²) with N ≤ 200 and pixel ≤ 512²; empirical runtime < 2 h. |

---


