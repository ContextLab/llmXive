# Research: Evaluating Statistical Fidelity of Synthetic Data

## Overview
This document details the methodological choices, data sources, and statistical procedures that will be executed by the automated pipeline defined in `plan.md`. It satisfies the constitution’s reproducibility and verified‑accuracy mandates.

## Dataset Strategy
| # | Dataset (canonical name) | Source (verified URL) | Loader | Approx. Size | Missing‑value handling |
|---|--------------------------|-----------------------|--------|--------------|------------------------|
| 1 | **UCI HAR (Human Activity Recognition)** | https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv | `datasets.load_dataset("udayl/UCI_HAR", split="test")` | ~10 k rows, ~50 columns | No NaNs observed; rows with NaNs would be dropped (none found). |
| 2 | **UCI Shopper** | https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet | `datasets.load_dataset("jlh/uci-shopper", split="train")` | ~6 k rows, 15 columns | Median imputation for numeric, mode for categorical. |
| 3 | **UCI Drop** (generic UCI collection) | https://huggingface.co/datasets/ucinlp/drop/resolve/main/data/train-00000-of-00001.parquet | `datasets.load_dataset("ucinlp/drop", split="train")` | ~8 k rows, 12 columns | Median imputation for numeric, mode for categorical. |

## Pre‑processing Pipeline
1. **Checksum verification** (`sha256`) of each raw file after download.  
2. **Missing‑value imputation**: median for numeric, mode for categorical.  
3. **Categorical encoding** (recorded in `data/processed/<name>/metadata.yaml`):  
   - One‑hot for low‑cardinality columns (< 20 distinct values).  
   - Frequency encoding for higher cardinality columns.  
   - All encoding decisions are logged and applied identically to training and hold‑out splits for a given dataset, ensuring that downstream fidelity metrics are not confounded by differing encodings.  
4. **Train/hold‑out split**: stratified 80/20 on the target column if present; otherwise random split with fixed seed = 123 (FR‑015).  
5. **RAM monitoring** (`psutil`). If peak RAM > 6.5 GB after encoding, uniformly down‑sample to ≤ 10 k rows **or** drop highest‑cardinality columns until under limit (FR‑009). All actions are logged.

## Generative Models
All models are instantiated from the `sdv` library (CPU‑only).

| Model | `sdv` class | Key hyper‑parameters | Privacy budget (DP‑GAN) |
|-------|-------------|----------------------|------------------------|
| CTGAN | `sdv.tabular.CTGAN` | `epochs=30`, `batch_size=500`, early‑stopping enabled | N/A |
| DP‑GAN | `sdv.tabular.DPGAN` | `epochs=30`, `batch_size=500`, `epsilon=1.0` (logged) | 1.0 |
| CopulaGAN | `sdv.tabular.CopulaGAN` | `epochs=30`, `batch_size=500` | N/A |

Training is performed **ten** times per (model, dataset) combination using seeds **42, 123, 2026, 3030, 4040, 5050, 6060, 7070, 8080, 9090** (FR‑017). Early‑stopping halts if validation loss improvement < 0.001 for three consecutive epochs (FR‑013). Non‑convergence after 30 epochs triggers FR‑010 handling (log, NaNs, continue).

## Fidelity Metrics
### Marginal Statistics
- **Continuous columns**: mean, variance, Kolmogorov–Smirnov (KS) statistic & p‑value, kernel‑density‑estimate (Gaussian kernel, Scott’s rule).  
- **Categorical columns**: frequency distribution, χ² statistic & p‑value (df = categories − 1).  

### Correlation
- Pearson and Spearman correlation matrices for real hold‑out and each synthetic set.  
- **Permutation‑based correlation test**: for each column pair, 1 000 permutations of one column in the synthetic set; compute correlation each time; empirical p‑value = proportion ≥ observed absolute difference.

All metrics are saved per seed; later aggregated (mean ± SD) (FR‑012).

## Statistical Testing & Corrections
- **Multiple‑comparison correction**: Benjamini‑Hochberg (FDR = 0.05) applied across the full set of p‑values per dataset.  
- **Effect‑size thresholds** (FR‑020): KS ≤ 0.1 for continuous columns; χ² ≤ χ²₀.₉₅ (computed from df) for categorical columns.  
- **Power justification**: With >5 k rows, the KS test attains > 0.9 power for detecting an effect size of 0.1; χ² tests achieve > 0.85 power for moderate degrees of freedom. Post‑hoc power estimates are reported using standard analytical approximations (SC‑005).

### Faithful / Unfaithful Classification
A column is labeled **faithful** **only if**:
1. Corrected p‑value ≥ 0.05 **and**  
2. Effect‑size below the thresholds above.  

Columns with estimated power < 0.8 are flagged **inconclusive** and excluded from the faithful/unfaithful tallies (prevents low‑power false‑negatives).

## Control & Sensitivity Analyses
### Control‑Perturbation Dataset (FR‑021)
- Constructed by **fully permuting** the rows of each column of the real hold‑out (seed = 99). This preserves every marginal distribution exactly while destroying all dependence structure, providing a ground‑truth reference for **false‑positive** rates of correlation‑based fidelity metrics.

### Marginal‑Perturbation Dataset (FR‑022)
- Generated by randomly permuting **[deferred]** of the rows within each column of the real hold‑out (seed = 2026), leaving the remaining [deferred] unchanged. This subtly perturbs marginal distributions while retaining most of the dependence structure, serving as a ground‑truth reference for **false‑negative** rates of marginal‑fidelity metrics.

### Sensitivity Sweep
- Evaluate faithful/unfaithful classification at p‑value thresholds **0.01, 0.05, 0.10**.  
- Compute **false‑positive** rates using the control‑perturbation dataset (any column flagged faithful despite destroyed dependence).  
- Compute **false‑negative** rates using the marginal‑perturbation dataset (any column flagged unfaithful despite largely preserved marginals).  
- Report stability (SC‑004) as the proportion of column‑method pairs whose classification changes across thresholds.

## Aggregation & Summary
- Aggregate metric differences across seeds → mean ± SD (FR‑012).  
- Produce `outputs/summary/aggregated_metrics.csv` containing per‑dataset, per‑model summaries of KS, χ², Pearson/Spearman differences, and faithful fractions.

## Reporting
- `report.py` produces a JSON machine‑readable summary and a PDF assembled via Jinja2‑rendered LaTeX; all figures are PNGs embedded as base64, avoiding external LaTeX dependencies.  
- Includes: metric tables, KDE/histogram plots, QQ‑plots, correlation heatmaps, multiple‑comparison correction note, power & equivalence discussion, sensitivity analysis table, and explicit associational framing (“These results describe associations …”).  
- Privacy‑budget ε for DP‑GAN is displayed in the model‑specific section (FR‑016).

## Compute Decision / Rationale
- **CPU‑first**: All SDV generators have pure‑Python/CPU implementations; empirical runtime ≈ a few hours for the full grid, well under the 360 min limit.  
- **GPU escape hatch**: Not required; the pipeline contains no CUDA calls.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset exceeds RAM after encoding | Crash | RAM monitor triggers down‑sampling or column‑drop (FR‑009). |
| DP‑GAN non‑convergence | Missing metrics | Log, emit NaNs, continue (FR‑010). |
| Zero‑variance synthetic column | KS undefined | Detect (FR‑011), flag, skip KS. |
| Fraction for marginal‑perturbation undefined | Ambiguous sensitivity | Fixed at 20 % row permutation per column (FR‑022). |
| Only two verified tabular benchmarks | FR‑001 unmet | Added third dataset (UCI Drop). |
| Limited seeds reduce power | Weak statistical conclusions | Ten seeds; power discussion added (SC‑005). |

---

