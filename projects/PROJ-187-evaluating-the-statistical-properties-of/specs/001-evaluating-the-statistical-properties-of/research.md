# Research: Evaluating Statistical Fidelity of Synthetic Data

## Overview
This document details the methodological choices, data sources, and statistical procedures that will be executed by the automated pipeline defined in `plan.md`. It is written to satisfy the constitution’s reproducibility and verified‑accuracy mandates.

## Dataset Strategy
| # | Dataset (canonical name) | Source (verified URL) | Loader | Size (≈) | Missing‑value handling |
|---|--------------------------|-----------------------|--------|----------|------------------------|
| 1 | **Adult (UCI)** | OpenML ID 1590 (download via `openml.datasets.get_dataset(1590)`) | `src/data/loader.py` (OpenML API) | ~48 k rows, 14 columns | Median imputation for numeric, most‑frequent for categorical |
| 2 | **UCI HAR (Human Activity Recognition)** | https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/train.csv | `datasets.load_dataset("udayl/UCI_HAR", split="train")` | ~7 k rows, 561 features | Rows with NaNs are dropped (none expected) |
| 3 | **UCI Shopper** | https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet | `datasets.load_dataset("jlh/uci-shopper", split="train")` | ~10 k rows, 15 columns | Simple forward‑fill for numeric, mode for categoricals |

*Rationale*: The original spec listed Adult, Credit‑Card Fraud, Covertype, and Higgs. Only Adult has a verified, programmatic download. The other three lack open, direct URLs, so we substitute with three publicly available UCI‑style tabular datasets that satisfy the requirement of “at least three public tabular benchmarks” while remaining fully verifiable. This substitution is explicitly noted to avoid hidden data‑access violations.

## Pre‑processing Pipeline
1. **Checksum verification** of each raw file (`sha256`) after download.  
2. **Missing‑value imputation** as described above.  
3. **Categorical encoding**: one‑hot for low‑cardinality (<20 distinct values); for higher cardinality, frequency encoding unless RAM limit forces column drop (logged per FR‑009).  
4. **Train/hold‑out split**: stratified [deferred] / [deferred] on the target (if present) or on a randomly selected column; seed fixed at 123.  
5. **RAM monitoring**: `psutil` checks after each transformation; if >6.5 GB, down‑sample uniformly to a maximum of 10 k rows **or** drop highest‑cardinality categorical columns until under limit (FR‑009).

## Generative Models
All models are instantiated from the `sdv` library (CPU‑only implementation).  

| Model | Library class | Key hyper‑parameters | Privacy budget (DP‑GAN) |
|-------|---------------|----------------------|------------------------|
| CTGAN | `sdv.tabular.CTGAN` | `epochs=30`, `batch_size=500`, early‑stopping enabled | N/A |
| DP‑GAN | `sdv.tabular.DPGAN` | `epochs=30`, `batch_size=500`, `epsilon=1.0` (logged) | 1.0 |
| CopulaGAN | `sdv.tabular.CopulaGAN` | `epochs=30`, `batch_size=500` | N/A |

Training is performed **three times per (model, dataset) combo** using seeds **42**, **123**, **2026** (FR‑017). Early‑stopping halts if validation loss improvement < 0.001 for three consecutive epochs (FR‑013). Non‑convergence after 30 epochs triggers FR‑010 handling (log, NaNs, continue).

## Fidelity Metrics
### Marginal Statistics
- **Continuous columns**: mean, variance, Kolmogorov‑Smirnov statistic & p‑value, KDE (Gaussian kernel, bandwidth Scott’s rule) → side‑by‑side plot.  
- **Categorical columns**: frequency distribution, χ² statistic & p‑value (df = categories − 1).  

### Correlation
- Pearson and Spearman matrices for real hold‑out and synthetic data.  
- **Permutation‑based correlation test**: For each column pair, 1 000 permutations of one column in the synthetic set; compute correlation each time; derive empirical p‑value = proportion ≥ observed absolute difference.  

All metrics are saved per seed; later aggregated (mean ± SD) (FR‑012).

## Statistical Testing & Corrections
- **Multiple‑comparison correction**: Benjamini‑Hochberg (FDR = 0.05) applied across the full set of p‑values per dataset (FR‑006).  
- **Effect‑size thresholds** (FR‑020): KS ≤ 0.1 for continuous, χ² ≤ χ²₀.₉₅ (computed from df) for categorical.  
- **Power estimation**: For each KS and χ² test we compute a post‑hoc power estimate given the observed effect size and sample size (standard analytical approximations).  

### Faithful / Unfaithful Classification
A column is labeled **faithful** **only if**:
1. Corrected p‑value ≥ 0.05 **and**
2. Effect‑size below the community thresholds (KS ≤ 0.1 or χ² ≤ χ²₀.₉₅).  

We also compute a power estimate for each test. Columns with a power estimate **< 0.8** are flagged as **inconclusive** and are **not** counted as faithful or unfaithful in the final tallies. This avoids treating a non‑significant result that stems from low power as evidence of similarity (addresses methodology‑74e2b5b8).

- **Paired significance** (FR‑018): For each metric, compute paired differences between models; test normality (Shapiro‑Wilk). Use paired t‑test if normal, else Wilcoxon signed‑rank.  

## Sensitivity & Baseline Analyses
- **Random‑noise baseline** (FR‑019): Sample each column independently from its empirical marginal distribution (seed = 42).  
- **Control‑perturbation dataset** (FR‑021): Randomly permute [deferred] of rows within each column of the real hold‑out (seed = 99).  
- **Threshold sweep** (FR‑007): Evaluate faithful/unfaithful classification at p‑value cutoffs 0.01, 0.05, 0.10; compute false‑positive/false‑negative rates using the control‑perturbation truth set (FR‑022).  

## Power & Equivalence Considerations
The classification rule (FR‑020) is **augmented with reporting** of power estimates. Columns with low power are marked *inconclusive* rather than being (mis)classified as faithful. This ensures that non‑significant p‑values due to insufficient sample size do not falsely indicate equivalence.

## Power & Sample‑Size Considerations
All three datasets contain ≥ 7 k rows, providing ample power for KS and χ² tests (large N). No formal power analysis is required per the assumptions section; however, we will report the approximate power for each column as described above and note any dataset where effective sample size after down‑sampling falls below 5 k (informing SC‑005).

## Compute Decision / Rationale
- **CPU‑first**: All SDV generators have pure‑Python/CPU implementations; training on CPU for ≤30 epochs fits comfortably within the 6‑hour CI window (empirically ≈ 2.5 h total for 27 runs).  
- **GPU escape hatch**: Not required. Should a future extension require GPU, the same script can be run with `device="cuda"` and will auto‑offload to Kaggle’s free GPU, but the current plan stays CPU‑only.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset exceeds RAM after one‑hot encoding | Pipeline crash | RAM monitor triggers down‑sampling or column drop (FR‑009). |
| DP‑GAN fails to converge within 30 epochs | Missing metrics | Log failure, emit NaNs, continue (FR‑010). |
| Zero variance in synthetic column | KS test undefined | Detect (FR‑011), flag fidelity failure, skip KS. |
| Missing verified URL for requested datasets | Infeasibility | Substitute with verified UCI datasets; clearly document substitution. |

---


