# Research: Quantifying the Impact of Data Cleaning

## Overview
The study evaluates how three common preprocessing steps—outlier removal, imputation, and categorical recoding—affect statistical inference (p‑values, confidence‑interval overlap, effect‑size estimates) across a diverse set of public datasets. Two pre‑registered hypotheses are tested:

* **H1 (Associative)** – Cleaning operations are associated with systematic changes in effect‑size estimates, assessed via a paired Wilcoxon signed‑rank test on `effect_size_change` across all datasets.
* **H2 (Associative)** – Imputation and recoding are associated with increased stability of effect‑size estimates, reflected by higher `ci_overlap` and lower `effect_size_cv`.

All claims are framed as *associative* because the data are observational.

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
* **Power analysis**: Conducted a priori for both the two‑sample t‑test (d = 0.5) and the paired Wilcoxon (Cohen = 0.5). The required minimum of 12 datasets is satisfied (see `power_analysis.txt`).  
* **Multiple‑comparison correction**: Holm‑Bonferroni within each dataset, Holm across Wilcoxon tests (addresses SC‑007).  
* **Permutation FPR & synthetic benchmarks**: Provide a robust check on Type I error inflation (FR‑020, FR‑006).  

## Statistical Rigor
| Aspect | Implementation |
|--------|----------------|
| **Multiple‑comparison correction** | Holm‑Bonferroni across cleaning‑variant p‑values per dataset (FR‑007). Holm correction for Wilcoxon test p‑values (replaces Bonferroni). |
| **Power analysis** | Two‑sample t‑test: d = 0.5, α = 0.05, power ≥ 0.8 → ≈ 64 per group. Paired Wilcoxon: Cohen = 0.5, α = 0.05, power ≥ 0.8 → ≥ 12 datasets. Documented in `power_analysis.txt`. |
| **Causal assumptions** | Observational data; all conclusions are associative (H1, H2). |
| **Measurement validity** | Outcome column is taken directly from dataset documentation (FR‑005). |
| **Collinearity** | Encoding creates numeric columns; variance‑inflation factors are computed but no independent‑effect claims are made. |
| **Assumption checks** | Shapiro‑Wilk (α = 0.05), Levene (α = 0.05), linearity (R² ≥ 0.7). Robust alternatives recorded (`robust_test_used`). |
| **Permutation‑based FPR** | ≥ 1 000 permutations per missingness mechanism, outcome shuffled before cleaning, Holm‑Bonferroni applied; results stored in `null_fpr_metrics.json`. |
| **Bootstrap** | `BOOTSTRAP_ITERATIONS` from `config.py` (default a sufficiently large number of iterations) passed to all bootstrap calls; no fallback. |
| **Sensitivity analysis** | Two‑way ANOVA on `effect_size_change` with factors *size bin* and *missingness level*; results in `sensitivity_metrics.json`. |

## Expected Deliverables
* `data/processed/baseline_metrics.json`
* `data/processed/cleaned_metrics.json`
* `data/processed/bootstrap_metrics.json`
* `data/processed/null_fpr_metrics.json`
* `data/processed/sensitivity_metrics.json`
* `data/processed/hypothesis_test_results.json`
* `data/processed/comparison_report.json`
* Visualisations: `output/figures/forest_plot.png` (300 dpi PNG) and `output/figures/heatmap.svg` (SVG)
* `power_analysis.txt`
* All contract schemas under `contracts/`
* Reproducibility logs (`data/hashes.json`, `state/projects/...yaml`)

---
