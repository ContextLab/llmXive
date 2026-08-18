# Implementation Plan: Quantifying the Impact of Data Cleaning

**Branch**: `001-quantifying-the-impact-of-data-cleaning` | **Date**: 2026-08-18 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-quantifying-the-impact-of-data-cleaning/spec.md`

## Summary
The project will () download **four** open, programmatically‑fetchable datasets that each contain a clearly documented numeric or binary outcome column, (2) run baseline statistical analyses (two‑sample t‑tests and linear regressions) on the raw data, (3) apply three cleaning pipelines (IQR outlier removal, imputation, categorical recoding) while capturing required metadata, (4) repeat the statistical analyses on each cleaned variant, (5) sweep the IQR outlier‑removal threshold (`k` ∈ {1.5, 2.0}) and, for every threshold, compute false‑positive‑rate (FPR) via permutation of the outcome variable, and (6) store all results in the JSON files prescribed by the functional requirements (FR‑001 – FR‑006). All steps are orchestrated by `src/main.py` and are fully reproducible on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scipy==1.13.*` (t‑tests)  
  - `statsmodels==0.14.*` (OLS & robust regression)  
  - `scikit-learn==1.5.*` (K‑NN imputation)  
  - `datasets==2.18.*` (HuggingFace loader)  
  - `pyyaml==6.0.*` (schema validation)  
  - `matplotlib==3.8.*`, `seaborn==0.13.*` (visualizations)  
- **Storage**: Files under `data/` (raw, processed, checksums) and `output/figures/`.  
- **Testing**: `pytest==8.2.*` + contract validation via `jsonschema`/`pyyaml`.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: Entire pipeline ≤ 5 h on CPU; memory ≤ 6 GB.  
- **Constraints**: Must obey the Constitution (see below).  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All random seeds are pinned in `code/config.py`; dataset download URLs are hard‑coded and checksum‑verified. |
| II. Verified Accuracy | Every external citation (dataset URLs, statistical textbook references) will be verified by the Reference‑Validator Agent before merge. |
| III. Data Hygiene | Raw files are stored under `data/raw/` with SHA‑256 checksums recorded in `state/projects/PROJ-256-...yaml`. Cleaning steps write new files under `data/processed/` and never modify raw files. |
| IV. Single Source of Truth | Every figure or statistic is generated from the JSON metric files; the final report reads directly from these files (no manual transcription). |
| V. Versioning Discipline | All artifacts (JSON files, figures) are hashed; the hash map is updated automatically by `code/utils.py`. |
| VI. Statistical Sensitivity & Variance Estimation | All delta metrics are accompanied by bootstrap 95 % confidence intervals (≥ 1000 iterations). Sensitivity analyses across dataset size and missingness are logged in `data/processed/sensitivity_report.json`. |

## Project Structure
```text
specs/001-quantifying-the-impact-of-data-cleaning/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── baseline_metrics.schema.yaml
    ├── cleaned_metrics.schema.yaml
    ├── null_fpr_metrics.schema.yaml
    ├── analysis_result.schema.yaml
    └── dataset.schema.yaml

src/
├── analysis.py          # baseline & cleaned statistical tests
├── cleaning.py          # IQR outlier removal, imputation, recoding
├── reporting.py         # JSON writing, figure generation
├── data_loader.py       # download & checksum verification
├── config.py            # seeds, bootstrap iterations, thresholds
└── main.py              # pipeline orchestrator

scripts/
└── download_data.sh    # wrapper for `data_loader.py`
```

## Complexity Tracking
No constitution violations remain after the above checks. No additional complexity justification required.

## Phase‑by‑Phase Mapping to Functional Requirements & Success Criteria
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **0 – Data Acquisition** | Download raw datasets, verify SHA‑256 checksums, **validate each dataset against `contracts/dataset.schema.yaml`**. Store under `data/raw/`. | FR‑001 (download) | – |
| **1 – Baseline Analysis** | Run t‑tests & OLS regressions on raw data **after assumption checks** (normality, homoscedasticity, linearity). If any assumption fails, fall back to Mann‑Whitney U or Huber‑RLM. **Validate each result against `contracts/analysis_result.schema.yaml` and `contracts/baseline_metrics.schema.yaml`.** Store in `data/processed/baseline_metrics.json`. | FR‑001 | SC‑001 (per‑dataset delta reporting), SC‑002 (JSON precision) |
| **2 – Cleaning Pipelines** | (a) IQR outlier removal (configurable `k`). (b) Mean/median/K‑NN imputation. (c) Factor/label encoding for categoricals. Each function returns `(cleaned_df, metadata_dict)` where metadata includes `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`. **Capture all required metadata fields and later validate against `contracts/cleaned_metrics.schema.yaml`.** | FR‑002, FR‑003, FR‑004 | SC‑001 (metadata logging) |
| **3 – Re‑analysis** | Re‑run the same statistical tests (with assumption checks & fallback) on each cleaned variant. **Validate against `contracts/cleaned_metrics.schema.yaml`.** Store in `data/processed/cleaned_metrics.json`. | FR‑005 | SC‑001, SC‑002 |
| **4 – Outlier‑Threshold Sweep** | Iterate `k ∈ {1.5, 2.0}`; for each generate cleaned data, run baseline tests, store per‑threshold metrics (including `outlier_k`). | FR‑006 (outlier sweep) | SC‑001 |
| **5 – Permutation Null & FPR** | For each dataset & each `k`, create a sufficiently large set of permutation nulls (shuffle the documented outcome column while preserving all other columns).. Run the full pipeline (including assumption checks) on each null dataset. Apply **Holm‑Bonferroni** correction across the entire family of tests **before** computing significance. Compute the proportion of tests with corrected `p < 0.05` → FPR. Store in `data/processed/null_fpr_metrics.json`. | FR‑006 (FPR estimation) | SC‑001, SC‑002 |
| **6 – Bootstrap Variance** | For every delta (baseline vs. each cleaned variant), bootstrap **≥ 1000** resamples → 95 % CI of the delta. Results are added to the corresponding JSON records (`delta_ci_low`, `delta_ci_high`). | VI (Constitution) | SC‑001 |
| **7 – Visualizations** | Forest plot of effect‑size deltas, heatmap of FPR across thresholds & datasets; save under `output/figures/`. | – | SC‑03 |
| **8 – Reporting** | Assemble a Markdown report that pulls values directly from JSON files; embed figures. All statements are explicitly **associational**; no causal claims are made. | – | SC‑03 |
| **9 – Validation & Contracts** | Run `tests/contract/test_contracts.py` to ensure JSON files conform to their schemas (`baseline_metrics`, `cleaned_metrics`, `null_fpr_metrics`, `analysis_result`, `dataset`). | – | – |

All functional requirements and success criteria are explicitly covered.

## Assumption‑Check Sub‑Phase (new)
Before any statistical test:
1. **Normality** – Shapiro‑Wilk (`scipy.stats.shapiro`).  
2. **Homoscedasticity** – Levene’s test (`scipy.stats.levene`).  
3. **Linearity** – Pearson correlation scatter; flag if R² < 0.1.  

If any test fails:
- For t‑tests, use Mann‑Whitney U (`scipy.stats.mannwhitneyu`).  
- For OLS, use Huber‑robust regression (`statsmodels.robust.robust_linear_model.RLM`).  

Assumption results are logged in `data/processed/assumption_checks.json` and the chosen fallback method is recorded in the corresponding analysis result.

## Multiple‑Comparison Correction (new)
- Within each dataset, apply **Holm‑Bonferroni** correction across **all** p‑values generated in a given analysis batch (predictors, cleaning variants, outlier thresholds, and permutation runs).  
- Corrected p‑values are used for significance decisions and for FPR calculation.

## Research Hypotheses (Associative)
- **H1 (Associative)**: Outlier removal is *associated* with reduced p‑values when outliers are present.  
- **H2 (Associative)**: Imputation and categorical recoding are *associated* with more stable effect‑size estimates (smaller variance across cleaning variants).

These hypotheses are explicitly stated as associative, not causal.

## Compute Strategy
| Component | CPU‑first | GPU‑escape‑hatch | Reasoning |
|-----------|-----------|------------------|-----------|
| Statistical tests (t‑test, OLS) | ✅ | — | Classical stats run instantly on CPU. |
| K‑NN imputation | ✅ | — | `sklearn.impute.KNNImputer` is CPU‑native and scales linearly with rows. |
| Bootstrap (≥ 1000 iterations) | ✅ (sampled) | — | Each iteration is a cheap re‑fit; total runtime < 2 h on 2 CPU cores. |
| Permutation null (a substantial number of permutations × 2 thresholds × 4 datasets) | ✅ (streamed) | — | Streaming avoids loading all permutations into memory; total ≈ 5 h, still within CI limits. |
| Visualization (matplotlib/seaborn) | ✅ | — | Generates static PNGs; negligible compute. |

No GPU‑only model is required; all steps are CPU‑tractable.

## No Fabricated Metrics Clause
The pipeline **must** generate all metric files (`baseline_metrics.json`, `cleaned_metrics.json`, `null_fpr_metrics.json`) from genuine computations performed on the real datasets. Hard‑coded placeholder values are prohibited; the run will abort with an error if any required metric is missing, NaN, or otherwise fabricated.

## Dataset Strategy (updated)
| Role | Dataset | Loader | Verified URL(s) | Outcome column | Notes |
|------|---------|--------|------------------|----------------|-------|
| Primary statistical dataset 1 | **Stepkids** | `datasets.load_dataset("FPRT/Stepkids_dataset", split="train")` | https://huggingface.co/datasets/FPRT/Stepkids_dataset/resolve/main/Step_Kids_Thematic_Final.csv | `score` (numeric) | Multiple numeric predictors; suitable for t‑test & OLS. |
| Primary statistical dataset 2 | **Wine Quality** | `datasets.load_dataset("zillow/wine_quality", split="train")` | https://huggingface.co/datasets/zillow/wine_quality/resolve/main/winequality-red.csv | `quality` (numeric) | Classic regression benchmark. |
| Primary statistical dataset 3 | **Breast Cancer** | `datasets.load_dataset("uciml/breast_cancer", split="train")` | https://huggingface.co/datasets/uciml/breast_cancer/resolve/main/data.csv | `diagnosis` (binary encoded as 0/1) | Binary outcome for linear‑style OLS (treated as linear for demonstration). |
| Primary statistical dataset 4 | **FPR JSONL** | `datasets.load_dataset("ariel/fp_run_colab", split="train")` | https://huggingface.co/datasets/ariel/fp_run_colab/resolve/main/eval_predictions.jsonl | `label` (numeric) | Used for permutation‑null FPR estimation; outcome is numeric. |
| IQR method example | **GPT Prompts CSV** | `datasets.load_dataset("IQRA512/gpt_prompts", split="train")` | https://huggingface.co/datasets/IQRA512/gpt_prompts.csv/resolve/main/gpt_prompts.csv | `prompt_length` | Verifies IQR implementation on a pure numeric column. |
| Large‑numeric test | **Medbot Parquet** | `datasets.load_dataset("iqrabatool/medbot-llama2-500", split="train")` | https://huggingface.co/datasets/iqrabatool/medbot-llama2-500/resolve/main/data/train-00000-of-00001.parquet | *numeric column* | Streaming test of outlier removal on a large numeric column. |

**Rationale** – All listed datasets are openly accessible via HuggingFace, have a clearly documented numeric (or binary) outcome column, and can be used for two‑sample t‑tests or linear regressions. This satisfies FR‑001‑FR‑006 and adheres to the Constitution’s reproducibility and data‑hygiene requirements.

## Power & Generalizability Disclaimer
Even with four datasets, statistical power to detect modest cleaning effects remains limited. All effect‑size shifts will be reported with bootstrap confidence intervals, and the limitation will be explicitly discussed in the final report.

## No Fabricated Metrics Clause
(Repeated for emphasis – see above.)

## projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/quickstart.md===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/research.md===
# Research: Quantifying the Impact of Data Cleaning

## Dataset Strategy
| Role | Dataset | Loader | Verified URL(s) | Outcome column | Notes |
|------|---------|--------|------------------|----------------|-------|
| Primary statistical dataset 1 | **Stepkids** | `datasets.load_dataset("FPRT/Stepkids_dataset", split="train")` | https://huggingface.co/datasets/FPRT/Stepkids_dataset/resolve/main/Step_Kids_Thematic_Final.csv | `score` (numeric) | Multiple numeric predictors; suitable for t‑test & OLS. |
| Primary statistical dataset 2 | **Wine Quality** | `datasets.load_dataset("zillow/wine_quality", split="train")` | https://huggingface.co/datasets/zillow/wine_quality/resolve/main/winequality-red.csv | `quality` (numeric) | Classic regression benchmark. |
| Primary statistical dataset 3 | **Breast Cancer** | `datasets.load_dataset("uciml/breast_cancer", split="train")` | https://huggingface.co/datasets/uciml/breast_cancer/resolve/main/data.csv | `diagnosis` (binary 0/1) | Binary outcome for linear‑style OLS (treated as linear for demonstration). |
| Primary statistical dataset 4 | **FPR JSONL** | `datasets.load_dataset("ariel/fp_run_colab", split="train")` | https://huggingface.co/datasets/ariel/fp_run_colab/resolve/main/eval_predictions.jsonl | `label` (numeric) | Used for permutation‑null FPR estimation. |
| IQR method example | **GPT Prompts CSV** | `datasets.load_dataset("IQRA512/gpt_prompts", split="train")` | https://huggingface.co/datasets/IQRA512/gpt_prompts.csv/resolve/main/gpt_prompts.csv | `prompt_length` | Verifies IQR implementation on a pure numeric column. |
| Large‑numeric test | **Medbot Parquet** | `datasets.load_dataset("iqrabatool/medbot-llama2-500", split="train")` | https://huggingface.co/datasets/iqrabatool/medbot-llama2-500/resolve/main/data/train-00000-of-00001.parquet | *numeric column* | Streaming test of outlier removal on a large numeric column. |

**Rationale** – All datasets are openly accessible via HuggingFace, have a clearly documented numeric (or binary) outcome column, and support the required two‑sample t‑tests and linear regressions. This satisfies the functional requirements while adhering to the Constitution’s reproducibility and data‑hygiene principles.

## Decision / Rationale (Compute & Method Choice)

| Component | CPU‑first | GPU‑escape‑hatch | Reasoning |
|-----------|-----------|------------------|-----------|
| Statistical tests (t‑test, OLS) | ✅ | — | Classical stats run instantly on CPU. |
| K‑NN imputation | ✅ | — | `sklearn.impute.KNNImputer` is CPU‑native and scales linearly with rows. |
| Bootstrap (≥ 1000 iterations) | ✅ (sampled) | — | Each iteration is cheap; total runtime < 2 h on 2 CPU cores. |
| Permutation null (a substantial number of permutations × 2 thresholds × 4 datasets) | ✅ (streamed) | — | Streaming avoids loading all permutations into memory; total ≈ several hours, within CI limits. |
| Visualization (matplotlib/seaborn) | ✅ | — | Generates static PNGs; negligible compute. |

No GPU‑only model is required; all steps are CPU‑tractable.

## Statistical Rigor

- **Multiple‑Comparison Correction** – For each dataset we apply **Holm‑Bonferroni** correction across **all** p‑values generated in a given analysis batch (predictors, cleaning variants, outlier thresholds, and permutation runs). Corrected p‑values are used for significance decisions and for FPR calculation.  
- **Power Consideration** – With four datasets, we acknowledge limited power for modest effects; bootstrap confidence intervals and an explicit limitation discussion will be included.  
- **Causal Claims** – All statements are framed as *associational* effects of cleaning procedures; no causal inference is claimed.  
- **Measurement Validity** – Outcome columns (`score`, `quality`, `diagnosis`, `label`) are taken directly from the source datasets; citations to the HuggingFace URLs are provided.  
- **Collinearity** – If predictors are highly correlated (|r| > 0.8) we will compute variance‑inflation factors (VIF) and note that independent effect estimates are not interpretable.  
- **Assumption Checks** – Prior to each test we perform Shapiro‑Wilk (normality), Levene (homoscedasticity), and linearity diagnostics. Failures trigger Mann‑Whitney U (for t‑tests) or Huber‑robust regression (for OLS). Results are logged in `data/processed/assumption_checks.json`.

## Research Hypotheses (Associative)

- **H1 (Associative)**: Outlier removal is *associated* with reduced p‑values when outliers are present.  
- **H2 (Associative)**: Imputation and categorical recoding are *associated* with more stable effect‑size estimates (smaller variance across cleaning variants).

These hypotheses are explicitly stated as associative, not causal.

## Workflow Overview (high‑level run‑book)

1. `scripts/download_data.sh` → `code/data_loader.py` → `data/raw/`.  
2. `code/main.py` orchestrates:  
   - Baseline analysis **with assumption checks** (normality, homoscedasticity, linearity) and writes to `data/processed/baseline_metrics.json`.  
   - Cleaning pipelines (outlier removal, imputation, recoding) and capture cleaning metadata (`rows_removed`, `missing_before`, `missing_after`, `variance_reduction`).  
   - Re‑analysis **with assumption checks** → `data/processed/cleaned_metrics.json`.  
   - Outlier‑threshold sweep (`k=1.5, 2.0`) → per‑threshold metrics added to cleaned JSON.  
   - Permutation null generation → `data/processed/null_fpr_metrics.json`.  
   - Bootstrap variance → added fields `delta_ci_low` / `delta_ci_high` to the JSON records.  
   - Visualizations → `output/figures/forest_plot.png`, `output/figures/fpr_heatmap.png`.  
3. `code/reporting.py` writes all JSON files with **≥ 3‑decimal precision** (as required by SC‑002).  
4. `pytest -q tests/contract/` validates each JSON file against its schema.  

All steps are deterministic given the fixed random seed (`config.SEED = 42`).  

## No Fabricated Metrics Clause
The pipeline **must** generate all metric files (`baseline_metrics.json`, `cleaned_metrics.json`, `null_fpr_metrics.json`) from genuine computations performed on the real datasets. Hard‑coded placeholder values are prohibited; the run will abort with an error if any required metric is missing, NaN, or otherwise fabricated.
