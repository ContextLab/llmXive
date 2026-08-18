# Research: Quantifying the Impact of Data Cleaning

## Dataset Strategy
| Role | Dataset | Loader | Verified URL(s) | Outcome column | Notes |
|------|---------|--------|------------------|----------------|-------|
| Primary statistical dataset 1 | **Stepkids** | `datasets.load_dataset("FPRT/Stepkids_dataset", split="train")` | https://huggingface.co/datasets/FPRT/Stepkids_dataset/resolve/main/Step_Kids_Thematic_Final.csv | `score` (numeric) | Multiple numeric predictors; suitable for t‑test & OLS. |
| Primary statistical dataset 2 | **Wine Quality** | `datasets.load_dataset("zillow/wine_quality", split="train")` | https://huggingface.co/datasets/zillow/wine_quality/resolve/main/winequality-red.csv | `quality` (numeric) | Classic regression benchmark. |
| Primary statistical dataset 3 | **Breast Cancer** | `datasets.load_dataset("uciml/breast_cancer", split="train")` | https://huggingface.co/datasets/uciml/breast_cancer/resolve/main/data.csv | `diagnosis` (binary 0/1) | Binary outcome for linear modeling. |
| Primary statistical dataset 4 | **FPR JSONL** | `datasets.load_dataset("ariel/fp_run_colab", split="train")` | https://huggingface.co/datasets/ariel/fp_run_colab/resolve/main/eval_predictions.jsonl | `label` (numeric) | Used for permutation‑null FPR estimation. |
| IQR method example | **GPT Prompts CSV** | `datasets.load_dataset("IQRA512/gpt_prompts", split="train")` | https://huggingface.co/datasets/IQRA512/gpt_prompts.csv/resolve/main/gpt_prompts.csv | `prompt_length` | Verifies IQR implementation on a pure numeric column. |
| Large‑numeric test | **Medbot Parquet** | `datasets.load_dataset("iqrabatool/medbot-llama2-500", split="train")` | https://huggingface.co/datasets/iqrabatool/medbot-llama2-500/resolve/main/data/train-00000-of-00001.parquet | *numeric column* | Streaming test of outlier removal on a large numeric column. |

**Rationale** – All datasets are openly accessible via HuggingFace, have a clearly documented numeric (or binary) outcome column, and support the required two‑sample t‑tests and OLS regressions. This satisfies the functional requirements while adhering to the Constitution’s reproducibility and data‑hygiene principles.

## Decision / Rationale (Compute & Method Choice)

| Component | CPU‑first | GPU‑escape‑hatch | Reasoning |
|-----------|-----------|------------------|-----------|
| Statistical tests (t‑test, OLS) | ✅ | — | Classical stats run instantly on CPU. |
| K‑NN imputation | ✅ | — | `sklearn.impute.KNNImputer` is CPU‑native and scales linearly with rows. |
| Bootstrap (≥ 1000 iterations) | ✅ (sampled) | — | Each iteration is cheap; total runtime < 2 h on 2 CPU cores. |
| Permutation null (a substantial number of permutations × 2 thresholds × 4 datasets) | ✅ (streamed) | — | Streaming avoids loading all permutations; total ≈ several hours, within CI limits. |
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

- **H1 (Associative)**: Outlier removal is *associated* with reduced p‑values when genuine outliers are present.  
- **H2 (Associative)**: Imputation and categorical recoding are *associated* with more stable effect‑size estimates (smaller variance across cleaning variants).

These hypotheses are explicitly stated as associative, not causal.

## Workflow Overview (high‑level run‑book)

1. `scripts/download_data.sh` → `code/data_loader.py` → `data/raw/` (checksum).  
2. `code/main.py` orchestrates:  
   - Baseline analysis **with assumption checks** → `data/processed/baseline_metrics.json`.  
   - Cleaning pipelines (outlier removal, imputation, recoding) → intermediate cleaned files + metadata.  
   - Re‑analysis **with assumption checks** → `data/processed/cleaned_metrics.json`.  
   - Outlier‑threshold sweep (`k=1.5, 2.0`) → per‑threshold metrics added to cleaned JSON.  
   - Permutation null generation → `data/processed/null_fpr_metrics.json`.  
   - Bootstrap variance → added fields `delta_ci_low`, `delta_ci_high`.  
   - Visualizations → `output/figures/forest_plot.png`, `output/figures/fpr_heatmap.png`.  
3. `code/reporting.py` writes all JSON files with **≥ 3‑decimal precision** (as required by SC‑002).  
4. `pytest -q tests/contract/` validates each JSON file against its schema.  

All steps are deterministic given the fixed random seed (`config.SEED = 42`).  
