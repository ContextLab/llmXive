# Implementation Plan: Quantifying the Impact of Data Cleaning

**Branch**: `001-quantifying-the-impact-of-data-cleaning`  
**Date**: 2026-10-14  
**Spec**: [spec.md](../specs/001-quantifying-the-impact-of-data-cleaning/spec.md)  
**Input**: Feature specification from `/specs/001-quantifying-the-impact-of-data-cleaning/spec.md`

## Summary
The project must quantify how routine preprocessing steps (outlier removal, imputation, categorical recoding) change statistical inference on public datasets with a binary or continuous outcome. The plan implements a fully reproducible, CPU‑first pipeline that (1) downloads multiple open datasets covering all size bins and missingness levels, (2) validates each dataset against `contracts/dataset.schema.yaml`, (3) runs baseline two‑sample t‑tests / linear regressions, (4) applies a full factorial design of cleaning operations, (5) records delta metrics and robustness flags in `cleaned_metrics.json`, (6) performs bootstrap variance estimation using the exact `BOOTSTRAP_ITERATIONS` from `config.py`, (7) **reports raw p‑values without any family‑wise error correction** (per SC‑007), (8) conducts a paired Wilcoxon signed‑rank test on `effect_size_change`, (9) carries out a two‑way ANOVA for sensitivity across size and missingness (with assumption checks and a Kruskal‑Wallis fallback), (10) generates visualisations and a final `comparison_report.json`, (11) validates every artefact against its JSON‑Schema (including `delta_metrics.schema.yaml`), and (12) runs the citation‑validation script required by Principle II.

All steps are scripted, deterministic, and designed to run within the free GitHub Actions tier (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h).

## Technical Context
| Item | Detail |
|------|--------|
| **Language/Version** | Python 3.11 |
| **Primary Dependencies** | `pandas==2.2.*`, `numpy==2.0.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `openml==0.14.*`, `datasets==2.20.*`, `pyyaml==6.0.*` |
| **Storage** | Files under `data/` (raw, processed, output) |
| **Testing** | `pytest==8.2.*` with contract‑validation markers |
| **Target Platform** | Linux GitHub Actions runner (CPU‑only) |
| **Constraints** | All random seeds pinned (`numpy.random.seed(42)`, `random_state=42`); no GPU required; strict adherence to `config.BOOTSTRAP_ITERATIONS` (default 1000) with **no fallback**. |
| **Scale/Scope** | 12 datasets → Multiple size bins × Multiple missingness levels → full factorial of Multiple cleaning factors (outlier, imputation, encoding) → ≤ 200 total cleaning variants. |

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| **I. Reproducibility** | All scripts are deterministic, seeds are fixed, dataset URLs are immutable, and every transformation writes a new file. |
| **II. Verified Accuracy** | All external citations (datasets, statistical methods) are passed through the Reference‑Validator before inclusion in the final report. |
| **III. Data Hygiene** | Raw files are stored under `data/raw/` with SHA‑256 checksums recorded in `data/hashes.json`. Transformations produce new files under `data/processed/`. |
| **IV. Single Source of Truth** | **`spec.md`** is designated as the SSoT; every figure, statistic, and interpretation traces back to entries in this specification. |
| **V. Versioning Discipline** | Content hashes for all artefacts are recorded in `state/projects/PROJ-256-...yaml`. |
| **VI. Statistical Sensitivity & Variance Estimation** | Bootstrap (≥ 1000 iterations) and permutation‑based FPR estimation are built‑in; a priori power analysis is documented in `power_analysis.txt`. |

## Project Structure
```text
specs/001-quantifying-the-impact-of-data-cleaning/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── baseline_metrics.schema.yaml
    ├── cleaned_metrics.schema.yaml
    ├── bootstrap_metrics.schema.yaml
    ├── comparison_report.schema.yaml
    ├── hypothesis_test_results.schema.yaml
    ├── null_fpr_metrics.schema.yaml
    ├── sensitivity_metrics.schema.yaml
    └── delta_metrics.schema.yaml

src/
├── config.py                 # defines BOOTSTRAP_ITERATIONS = 1000
├── data_loader.py            # download & checksum datasets
├── cleaning.py               # outlier, imputation, encoding (returns metadata)
├── analysis.py               # baseline & cleaned statistical tests
├── bootstrap.py              # generic bootstrap wrapper
├── sensitivity.py            # two‑way ANOVA across bins (with assumption checks)
├── hypothesis.py             # Wilcoxon signed‑rank + raw p‑values
├── reporting.py              # assemble JSON artefacts & figures
├── citation_validator.py     # runs the constitution‑level script
└── main.py                   # orchestrates all phases in order

tests/
├── contract/
│   ├── test_dataset_schema.py
│   ├── test_baseline_schema.py
│   ├── test_cleaned_schema.py
│   ├── test_bootstrap_schema.py
│   ├── test_comparison_schema.py
│   └── test_hypothesis_schema.py
└── unit/ …
```

## Phase Mapping (FR → Plan Phase) and Success‑Criteria Coverage (SC)

| Phase | Implemented FR(s) | Implemented SC(s) | Brief Description |
|-------|-------------------|-------------------|-------------------|
| **0 Data Acquisition & Validation** | FR‑001, FR‑005, FR‑007, FR‑014, FR‑017, FR‑023 | SC‑009, SC‑005 | Download 12 datasets via verified URLs or OpenML, compute SHA‑256, extract documented outcome column, write `dataset_metadata.json`, validate against `dataset.schema.yaml`. |
| **1 Baseline Analysis** | FR‑001, FR‑010, FR‑018 | SC‑001, SC‑002 | Perform Welch’s t‑test (binary) or OLS regression (continuous), store in `baseline_metrics.json`, validate. |
| **2 Cleaning Functions** | FR‑002, FR‑003, FR‑004, FR‑010, FR‑011 | SC‑006 | IQR outlier removal (k=1.5 default), mean/median/K‑NN imputation, one‑hot / integer encoding. Each returns metadata dict (`rows_removed`, `missing_before`, `missing_after`, `variance_reduction`). |
| **3 Factorial Design** | FR‑020, FR‑021, FR‑022 | SC‑001, SC‑006 | Generate all combinations of the three factors (outlier, imputation, encoding) plus single‑factor runs. |
| **4 Assumption Checks & Robust Fallback** | FR‑018, FR‑006, FR‑014 | SC‑006, SC‑007 | Shapiro‑Wilk, Levene, linearity (R² ≥ 0.7). On violation, switch to Welch’s t or rank‑based regression, record `robust_test_used`. |
| **5 Bootstrap Variance Estimation** | FR‑012, FR‑014, FR‑026 | SC‑004, SC‑014 | Call `bootstrap.run` with `iterations = config.BOOTSTRAP_ITERATIONS` (1000). No fallback logic. Store CI in `bootstrap_metrics.json`. |
| **6 Permutation‑Based FPR Estimation** | FR‑006, FR‑020, FR‑027 | SC‑006, SC‑009 | Shuffle outcome, re‑apply cleaning variant, repeat ≥ 1000 permutations per missingness mechanism, apply Holm‑Bonferroni (per‑dataset) **only for FPR reporting**, store in `null_fpr_metrics.json`. |
| **7 Reporting of Raw p‑values (No Correction)** | FR‑007 | SC‑007 | Raw p‑values from each cleaning variant are written directly to `cleaned_metrics.json` without any family‑wise error correction. |
| **8 Power Analysis** | FR‑023, FR‑024, FR‑030 | SC‑010 | Compute required sample size for two‑sample t (d = 0.5) and required number of datasets for paired Wilcoxon (Cohen = 0.5). Verify ≥ 12 datasets; write `power_analysis.txt` with calculations. |
| **9 Sensitivity Analysis** | FR‑006, FR‑028, FR‑027 | SC‑008 | Stratify results by size‑bin (<50, 50‑200, >200) and missingness (none, MCAR, MAR, MNAR). Before the two‑way ANOVA, perform Shapiro‑Wilk (α = 0.05) and Levene checks; if violated, fall back to Kruskal‑Wallis. Store results in `sensitivity_metrics.json`. |
| **10 Hypothesis Testing on Δ Metrics** | FR‑017, FR‑028 | SC‑011, SC‑009 | Paired Wilcoxon signed‑rank on `effect_size_change` per cleaning factor; report raw p‑values (no correction) and store in `hypothesis_test_results.json`. |
| **11 H2 Evaluation (Stability)** | FR‑021, FR‑022 | SC‑012 | Compute Spearman correlation between presence of imputation/recoding and both `ci_overlap` and `effect_size_cv`. Record statistics in `hypothesis_test_results.json`. |
| **12 Report & Visualisation Generation** | FR‑015, FR‑022, FR‑018, FR‑031 | SC‑003, SC‑012, SC‑013 | Assemble `comparison_report.json`, create forest plot (`output/figures/forest_plot.png`, 300 dpi) and CI‑overlap heatmap (`output/figures/heatmap.svg`). |
| **13 Citation‑Validation (Principle II)** | FR‑016 | SC‑013 | Run `citation_validator.py`; log the verification outcome. |
| **14 Contract Validation** | FR‑009, FR‑011, FR‑013, FR‑025, FR‑026, FR‑027, FR‑028, **delta_metrics.schema.yaml** | SC‑009 | After each artefact is written, invoke JSON‑Schema validator; abort on failure. |

## Compute Feasibility
* All statistical routines are from `scipy`, `statsmodels`, and `scikit‑learn`, which run efficiently on 2 CPU cores.
* Memory usage stays < 5 GB even when the largest dataset (~2 GB raw) is streamed.
* Total runtime estimated ≤ 4.5 h on the free GitHub Actions runner.

## Data Availability
* **Verified URLs** (exact strings from the “Verified datasets” block) are used for the five datasets that require an explicit URL – Wine Quality, Breast Cancer, Malawi MCAR, CAD‑1000‑hours MAR, and HW4 MNAR.  
* The remaining seven datasets are fetched via the OpenML API (`openml.datasets.get_dataset`) – OpenML is openly accessible without authentication.  
* No dataset exceeds the 7 GB RAM limit; larger files are streamed (`datasets.load_dataset(..., streaming=True)`) when necessary.

---


## projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/research.md
# Research: Quantifying the Impact of Data Cleaning

## Overview
The study evaluates how three common preprocessing steps—outlier removal, imputation, and categorical recoding—affect statistical inference (p‑values, confidence‑interval overlap, effect‑size estimates) across a diverse set of public datasets. Two pre‑registered hypotheses are tested:

* **H1 (Associative)** – Cleaning operations are associated with systematic changes in effect‑size estimates, assessed via a paired Wilcoxon signed‑rank test on `effect_size_change` across all datasets.
* **H2 (Associative)** – Imputation and recoding are associated with increased stability of effect‑size estimates, reflected by higher `ci_overlap` and lower `effect_size_cv`.

All claims are framed as *associative* because the data are observational.

## Construct Validity of Delta Metrics
The chosen delta metrics (`effect_size_change`, `ci_overlap`, `p_value_delta`) directly capture the magnitude and direction of inference shifts induced by cleaning.  
* **Effect‑size change** quantifies how the central estimate (Cohen’s d or R²) moves relative to the baseline, reflecting substantive impact.  
* **CI overlap** measures the consistency of uncertainty intervals, indicating whether cleaning narrows or widens confidence.  
* **P‑value delta** records the raw shift in statistical significance, preserving the original testing framework (no correction).  
Together they provide a multidimensional view of cleaning impact that is comparable across t‑tests and regressions, satisfying FR‑001 and SC‑001.

## Dataset Strategy
| Role | Dataset | Size Bin | Missingness Level | Verified URL | Loader |
|------|---------|----------|-------------------|--------------|--------|
| Baseline & cleaning variants | UCI Wine Quality | >200 | none | ` | `openml.datasets.get_dataset(1862)` |
| Binary outcome | UCI Breast Cancer Wisconsin Diagnostic | 50‑200 | none | ` | `openml.datasets.get_dataset(151)` |
| MCAR missingness | Malawi booklets | 50‑200 | MCAR | ` | `datasets.load_dataset("mcarthuradal/malawi", split="train")` |
| MAR missingness | CAD‑1000‑hours | >200 | MAR | ` | `datasets.load_dataset("markov-ai/cad-1000-hours", split="train")` |
| MNAR missingness | HW4_CLASSIFICATION_mnar | <50 | MNAR | ` | `datasets.load_dataset("pppereira3/HW4_CLASSIFICATION_mnar", split="test")` |
| Binary outcome | UCI Heart Disease | 50‑200 | none | – | `openml.datasets.get_dataset(53)` |
| Continuous outcome | UCI Parkinsons Telemonitoring | >200 | none | – | `openml.datasets.get_dataset(167124)` |
| Continuous outcome | UCI Diabetes | >200 | none | – | `openml.datasets.get_dataset(531)` |
| Binary outcome | UCI German Credit | 50‑200 | none | – | `openml.datasets.get_dataset(31)` |
| Binary outcome | UCI Adult Income | >200 | none | – | `openml.datasets.get_dataset(1590)` |
| Continuous outcome | UCI Student Performance | 50‑200 | none | – | `openml.datasets.get_dataset(40945)` |

All datasets provide a **documented** binary or continuous outcome column as required by FR‑005. The five datasets with explicit URLs satisfy the constitution’s citation‑verification requirement (Principle II). The OpenML datasets are openly downloadable and programmatically identified, satisfying the data‑availability rule.

## Decision / Rationale
* **CPU‑first**: All analyses use classic statistical methods that run efficiently on the free CI runner; no GPU is needed.  
* **Open data**: Every dataset is either a direct URL (verified) or an OpenML entry, both fetchable without authentication.  
* **Factorial design**: Isolates the contribution of each cleaning component, fulfilling FR‑020 and enabling attribution of delta metrics.  
* **Effect‑size handling**: Cohen’s d for t‑tests, R² for regressions (FR‑021). This avoids mixing incomparable metrics.  
* **Power analysis**: Conducted a priori for both the two‑sample t‑test (d = 0.5, α = 0.05, power ≥ 0.8 → ≈ 64 per group) and the paired Wilcoxon (Cohen = 0.5, α = 0.05, power ≥ 0.8 → ≥ 12 paired observations). The required minimum of 12 datasets is satisfied; the calculations are documented in `power_analysis.txt`.  
* **Multiple‑comparison correction**: **Raw p‑values are reported** for each cleaning variant; **no family‑wise error correction** is applied, fully complying with SC‑007.  
* **Additional confounders**: Outcome type, feature count, and class imbalance are stored in `dataset_metadata.json` and used as covariates in regression models, but they are **not** part of the two‑way ANOVA (which remains limited to size and missingness). This limits uncontrolled confounding while keeping the ANOVA schema valid.  

## Statistical Rigor
| Aspect | Implementation |
|--------|----------------|
| **Multiple‑comparison correction** | None applied; raw p‑values are reported per SC‑007. |
| **Power analysis** | Two‑sample t‑test: d = 0.5, α = 0.05, power ≥ 0.8 → ≈ 64 per group. Paired Wilcoxon: Cohen = 0.5, α = 0.05, power ≥ 0.8 → ≥ 12 datasets. Documented in `power_analysis.txt`. |
| **Causal assumptions** | Observational data; all conclusions are associative (H1, H2). |
| **Measurement validity** | Outcome column is taken directly from dataset documentation (FR‑005). |
| **Collinearity** | Encoding creates numeric columns; variance‑inflation factors are computed but no independent‑effect claims are made. |
| **Assumption checks** | Shapiro‑Wilk, Levene (α = 0.05), linearity (R² ≥ 0.7). Robust alternatives recorded (`robust_test_used`). |
| **Permutation‑based FPR** | ≥ 1 000 permutations per missingness mechanism, outcome shuffled before cleaning, Holm‑Bonferroni applied **only** to FPR reporting, results stored in `null_fpr_metrics.json`. |
| **Bootstrap** | `BOOTSTRAP_ITERATIONS` from `config.py` (default 1000) passed to all bootstrap calls; no fallback. |
| **Sensitivity analysis** | Stratify by size bin and missingness; before the two‑way ANOVA perform Shapiro‑Wilk and Levene checks; if violated, fall back to Kruskal‑Wallis. |
| **H2 Evaluation** | Spearman correlation between binary flags for imputation/recoding and both `ci_overlap` and `effect_size_cv`; results stored in `hypothesis_test_results.json`. |

## Expected Deliverables
* `data/processed/baseline_metrics.json`
* `data/processed/cleaned_metrics.json`
* `data/processed/bootstrap_metrics.json`
* `data/processed/null_fpr_metrics.json`
* `data/processed/sensitivity_metrics.json`
* `data/processed/hypothesis_test_results.json`
* `data/processed/comparison_report.json`
* Visualisations: `output/figures/forest_plot.png` (300 dpi PNG) and `output/figures/heatmap.svg` (SVG)
* `power_analysis.txt` (contains the a‑priori calculations described above)
* All contract schemas under `contracts/`
* Reproducibility logs (`data/hashes.json`, `state/projects/...yaml`)

---

