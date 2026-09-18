# Research: Quantifying the Impact of Data Cleaning

## Overview
The study assesses how routine preprocessing steps (outlier removal, imputation, categorical recoding) influence statistical inference outcomes (effect size, p‑value, confidence‑interval overlap). Two research hypotheses are tested:

* **H1 (Associative)** – Cleaning operations are *associated* with systematic changes in **effect‑size** estimates (Wilcoxon signed‑rank test on `effect_size_change`).
* **H2 (Associative)** – Imputation and recoding are *associated* with increased stability of effect‑size estimates, reflected by higher `ci_overlap` and reduced variance.

## Dataset Strategy
| Role | Dataset | Size Bin | Missingness Level | Verified URL | Loader |
|------|---------|----------|-------------------|--------------|--------|
| Baseline & cleaning variants | UCI Wine Quality | >200 | none | `https://archive.ics.uci.edu/ml/datasets/Wine+Quality` | `openml.datasets.get_dataset(1862)` |
| Additional binary outcome | UCI Breast Cancer Wisconsin Diagnostic | 50‑200 | none | `https://archive.ics.uci.edu/ml/datasets/Breast+Cancer+Wisconsin+Diagnostic` | `openml.datasets.get_dataset(151)` |
| MCAR missingness | Malawi booklets | 50‑200 | MCAR | `https://huggingface.co/datasets/mcarthuradal/malawi/resolve/main/booklets/bk0-00000-of-00001.parquet` | `datasets.load_dataset("mcarthuradal/malawi", split="train")` |
| MAR missingness | CAD‑1000‑hours | >200 | MAR | `https://huggingface.co/datasets/markov-ai/cad-1000-hours/resolve/main/autocad/59f5afb1-7193-4434-83ef-bad577bf09ed/output_files/output.csv` | `datasets.load_dataset("markov-ai/cad-1000-hours", split="train")` |
| MNAR missingness | HW4_CLASSIFICATION_mnar | <50 | MNAR | `https://huggingface.co/datasets/pppereira3/HW4_CLASSIFICATION_mnar/resolve/main/data/test-00000-of-00001.parquet` | `datasets.load_dataset("pppereira3/HW4_CLASSIFICATION_mnar", split="test")` |
| Additional OpenML binary outcome | UCI Heart Disease | 50‑200 | none | – | `openml.datasets.get_dataset(53)` |
| Additional OpenML continuous outcome | UCI Parkinsons Telemonitoring | >200 | none | – | `openml.datasets.get_dataset(167124)` |
| Additional OpenML continuous outcome | UCI Diabetes | >200 | none | – | `openml.datasets.get_dataset(531)` |
| Additional OpenML binary outcome | UCI German Credit | 50‑200 | none | – | `openml.datasets.get_dataset(31)` |
| Additional OpenML binary outcome | UCI Adult Income | >200 | none | – | `openml.datasets.get_dataset(1590)` |
| Additional OpenML continuous outcome | UCI Student Performance | 50‑200 | none | – | `openml.datasets.get_dataset(40945)` |

All listed datasets have a clearly documented binary or continuous outcome variable (as required by FR‑001). The five datasets with verified URLs satisfy the citation rule; the remaining seven are obtained programmatically via OpenML and are openly downloadable.

## Decision / Rationale
* **CPU‑first**: All statistical methods (t‑tests, linear regression, permutation, bootstrap) are implemented with `scipy`, `statsmodels`, and `scikit‑learn`, which run comfortably on the GitHub Actions CPU tier. No GPU is required, satisfying the compute feasibility constraints.
* **Open data**: The chosen datasets are openly licensed and programmatically accessible, meeting the data‑availability requirement.
* **Factorial design**: By isolating each cleaning operation and their interactions, we can attribute observed changes to specific steps (addresses methodology‑e6720e24).
* **Unified effect‑size handling**: Effect sizes are reported per test type (Cohen’s d for t‑tests, partial R² for regressions) to avoid mixing incomparable metrics (addresses methodology‑b2eb8e76).
* **Power analysis**: Explicit a‑priori calculations are performed for both t‑tests and the paired Wilcoxon test; the required minimum of 12 datasets is satisfied (addresses methodology‑01750387 and spec_coverage‑074016c7).
* **Multiple‑comparison correction**: Holm‑Bonferroni is used within‑dataset and Holm is used for Wilcoxon tests, avoiding an extra Bonferroni layer (addresses methodology‑ff78b058).
* **Permutation FPR & benchmarks**: Permutation‑based FPR estimation is complemented by synthetic null‑effect and d = 0.5 benchmarks (addresses methodology‑5698a23b and FR‑020).

## Statistical Rigor
| Aspect | Implementation |
|--------|----------------|
| **Multiple‑comparison correction** | Holm‑Bonferroni across all cleaning‑variant p‑values per dataset (FR‑007). Holm correction for Wilcoxon tests (replaces Bonferroni) (FR‑029). |
| **Power analysis** | A priori power analysis for two‑sample t‑test (Cohen’s d = 0.5, α = 0.05, power ≥ 0.8) – documented in `power_analysis.txt`. Non‑parametric power analysis for paired Wilcoxon (Cohen = 0.5) – also in `power_analysis.txt`. |
| **Causal assumptions** | Observational data; all claims framed as *associative* (H1, H2). |
| **Measurement validity** | Outcome columns are taken from dataset documentation; no inference of outcome variable (FR‑005). |
| **Collinearity** | Encoding produces numeric columns; variance inflation factors are reported but no independent‑effect claims are made (SC‑016). |
| **Permutation‑based FPR** | ≥ 1 000 permutations per missingness mechanism, outcome shuffled prior to cleaning, Holm‑Bonferroni applied, FPR ≤ 0.05 required (FR‑006). |
| **Bootstrap** | `BOOTSTRAP_ITERATIONS` from `config.py` (default 1000) used uniformly (FR‑014, FR‑026). |
| **Assumption checks** | Shapiro‑Wilk, Levene, linearity (R² ≥ 0.7). Robust alternatives invoked automatically (Welch’s t, rank‑based regression) and recorded (`robust_test_used`). |

## Expected Deliverables
- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/bootstrap_metrics.json`
- `data/processed/sensitivity_metrics.json`
- `data/processed/hypothesis_test_results.json`
- `data/processed/comparison_report.json`
- Visualisations under `output/figures/`
- `power_analysis.txt`
- Contract schema files under `contracts/`
- Full reproducibility logs and checksum manifests.

---


