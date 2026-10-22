# Data Model: Evaluating Statistical Fidelity of Synthetic Data

## Overview
Defines canonical file formats, schemas, and provenance metadata for all artifacts produced by the pipeline. All files reside under `data/` (raw/processed) or `outputs/` (synthetic, metrics, figures, report). No artifact is written to the platform‑owned `state/` directory.

## 1. Raw Dataset Record (`data/raw/<name>/metadata.yaml`)
```yaml
dataset_name: "UCI_HAR"   # or "UCI_Shopper" or "UCI_Adult"
source: "huggingface"
download_url: "https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv"
checksum_sha256: "a1b2c3d4e5f6..."   # verified at download time
record_count: a substantially large number of records               # approximate, recorded after download
column_names:
  - col_1
  - col_2
  # …
```

## 2. Processed Dataset (`data/processed/<name>/train.parquet`, `holdout.parquet`)
- **Format**: Apache Parquet (`gzip` compression).  
- **Schema**: Columns typed as `int64`, `float64`, or `category`.  
- **Provenance metadata** (`data/processed/<name>/metadata.yaml`):
```yaml
preprocessing_timestamp: "2026-10-22T08:12:34Z"
imputation_strategy:
  numeric: "median"
  categorical: "mode"
encoding_strategy:
  one_hot_threshold: 20
  high_cardinality_action: "drop_if_ram_exceeds"
train_holdout_split: "80/20"
random_seed: 123
row_count_before_downsample: a large initial row count
row_count_after_downsample: a substantially reduced number of rows
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
  "row_count": 9500,
  "generated_timestamp": "2026-10-22T12:34:56Z",
  "privacy_epsilon": null   // null for non‑DP models, numeric for DP‑GAN
}
```

## 4. Random‑Noise Baseline Dataset (`outputs/baseline/random_noise_<dataset>.csv`)
- **Format**: CSV (UTF‑8).  
- **Columns**: Same schema as the processed hold‑out.  
- **Generation**: Each column sampled independently from the empirical marginal distribution of the hold‑out (seed = 42).  
- **Side‑car metadata (`.json`):
```json
{
  "dataset": "<dataset>",
  "generation_method": "independent_marginal_sampling",
  "seed": 42,
  "row_count": 9500,
  "generated_timestamp": "2026-10-22T13:00:00Z"
}
```

## 5. Control‑Perturbation Dataset (`outputs/control/control_perturb_<dataset>.parquet`)
- **Format**: Apache Parquet (`gzip`).  
- **Generation**: Randomly permutes **[deferred]** of rows in each column of the real hold‑out (seed = 99). This preserves the marginal distribution exactly while destroying all dependence structure. It is used **solely** to estimate false‑positive rates for correlation‑based fidelity metrics (FR‑021).
- **Provenance metadata (`metadata.yaml`):
```yaml
perturbation_type: "row_permutation"
fraction_permuted: 0.10
seed: 99
generated_timestamp: "2026-10-22T13:30:00Z"
```

## 6. Metric Results (`outputs/metrics/metric_results.json`)
A JSON array where each element conforms to `contracts/metric_results.schema.yaml`. Example entry:
```json
{
  "dataset": "UCI_HAR",
  "model": "CTGAN",
  "seed": 42,
  "column": "acceleration_x",
  "column_type": "continuous",
  "real_mean": 0.123,
  "synth_mean": 0.119,
  "mean_diff": -0.004,
  "real_var": 0.045,
  "synth_var": 0.047,
  "var_diff": 0.002,
  "ks_stat": 0.032,
  "ks_pvalue": 0.78,
  "chi2_stat": null,
  "chi2_pvalue": null,
  "pearson_real": 0.56,
  "pearson_synth": 0.53,
  "pearson_diff": 0.03,
  "spearman_real": 0.58,
  "spearman_synth": 0.55,
  "spearman_diff": 0.03,
  "perm_corr_pvalue": 0.12,
  "corrected_pvalue": 0.34,
  "faithful": true,
  "effect_size": "small",
  "power_estimate": 0.92
}
```

## 7. Aggregated Summary (`outputs/summary/aggregated_metrics.csv`)
Columns:
- `dataset`
- `model`
- `metric_type` (e.g., `KS`, `Chi2`, `PearsonDiff`, `SpearmanDiff`)
- `mean_statistic`
- `std_statistic`
- `mean_effect_size`
- `std_effect_size`
- `fraction_faithful`

## 8. Final Report (`outputs/report/fidelity_report.pdf` & `.json`)
- JSON mirrors the PDF content (tables, figures encoded as base64).  
- PDF is generated from a Jinja2‑rendered LaTeX template; all figures are PNGs embedded as base64, avoiding external LaTeX dependencies.  

---



