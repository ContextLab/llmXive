# Data Model: Evaluating Statistical Fidelity of Synthetic Data

## Overview
Defines canonical file formats, schemas, and provenance metadata for all artifacts produced by the pipeline. All files reside under `data/` (raw/processed) or `outputs/` (synthetic, metrics, figures, report).

## 1. Raw Dataset Record (`data/raw/<name>/metadata.yaml`)
```yaml
dataset_name: "UCI_HAR"
source: "huggingface"
download_url: "https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv"
checksum_sha256: "a1b2c3d4e5f6..."   # verified at download time
record_count: a substantial number of records
column_names:
  - column_1
  - column_2
  # … (A substantial total number of columns.)
```
Similar `metadata.yaml` files exist for `UCI_Shopper`.

## 2. Processed Dataset (`data/processed/<name>/train.parquet`, `holdout.parquet`)
- **Format**: Apache Parquet (`gzip` compression).  
- **Schema**: Columns typed as `int64`, `float64`, or `category`.  
- **Provenance metadata** (`data/processed/<name>/metadata.yaml`):
```yaml
preprocessing_timestamp: "2026-10-18T08:12:34Z"
imputation_strategy:
  numeric: "median"
  categorical: "mode"
encoding_strategy:
  one_hot_threshold: 20
  high_cardinality_action: "drop_if_ram_exceeds"
train_holdout_split: "80/20"
random_seed: 123
row_count_before_downsample: a substantial number of rows
row_count_after_downsample: a reduced dataset comprising several thousand rows   # or reduced if downsampling triggered
encoding_log:
  dropped_columns: []               # list of column names dropped due to RAM
  frequency_encoded_columns: []     # list of columns encoded by frequency
```

## 3. Synthetic Dataset (`outputs/synthetic/<dataset>_<model>_seed<NN>.csv`)
- **Format**: CSV (UTF‑8).  
- **Columns**: Identical order and names to the processed training set.  
- **Side‑car metadata (`.json`):
```json
{
  "dataset": "<dataset>",
  "model": "<CTGAN|DPGAN|CopulaGAN>",
  "seed": 42,
  "row_count": "a substantial number of rows",
  "generated_timestamp": "2026-10-18T12:34:56Z",
  "privacy_epsilon": "a chosen privacy budget"   // null for non‑DP models
}
```

## 4. Metric Results (`outputs/metrics/metric_results.json`)
A JSON array where each element conforms to `contracts/metric_results.schema.yaml`. Example entry:
```json
{
  "dataset": "UCI_HAR",
  "model": "CTGAN",
  "seed": 42,
  "column": "acceleration_x",
  "column_type": "continuous",
  "real_mean": a modest positive value,
  "synth_mean": "a small positive value",
  "mean_diff": "slightly negative",
  "real_var": "a small positive value",
  "synth_var": "a modest variance",
  "var_diff": a small negative value,
  "ks_stat": "a low magnitude",
  "ks_pvalue": <computed_pvalue>,
  "chi2_stat": null,
  "chi2_pvalue": null,
  "metric_type": "PearsonDiff",
  "real_val": "a moderate proportion (to be determined)",
  "synth_val": "moderate",
  "diff": "a small positive difference",
  "pvalue": "statistically significant",
  "fisher_z_deviation": "a modest positive deviation",
  "corrected_p_value": <value indicating marginal significance>,
  "faithful": true,
  "effect_size": "anticipated to be modest",
  "power_estimate": "high"
}
```

## 5. Aggregated Summary (`outputs/summary/aggregated_metrics.csv`)
Columns:
- `dataset`
- `model`
- `metric_type`
- `mean_statistic`
- `std_statistic`
- `mean_effect_size`
- `std_effect_size`
- `fraction_faithful`

## 6. Control‑Perturbation Datasets
- **Correlation‑perturbation** (`outputs/control/corr_perturb_<dataset>.parquet`): column‑wise row permutation of the real hold‑out. **Purpose**: estimate **false‑positive** rates for correlation‑based fidelity tests (any significant correlation detected here is a false positive).  
- **Marginal‑perturbation** (`outputs/control/marginal_perturb_<dataset>.parquet`): for each column, replace a random **subset** of values with draws from the empirical marginal distribution (preserves the dependence structure while perturbing the marginals). **Purpose**: estimate **false‑negative** rates for marginal‑based fidelity tests (any non‑significant marginal test here is a false negative).  
Both files include a matching `metadata.yaml` indicating the perturbation type and seed.

## 7. Final Report (`outputs/report/fidelity_report.pdf` & `.json`)
- JSON mirrors the PDF content (tables, figures encoded as base64).  
- PDF is generated from a Jinja2‑rendered LaTeX template; all figures are PNGs embedded as base64, avoiding external LaTeX dependencies.

---


