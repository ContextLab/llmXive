# Data Model: Evaluating Statistical Fidelity of Synthetic Data

## Overview
The data model defines the canonical file formats, schemas, and provenance metadata used throughout the pipeline. All artifacts are stored under `data/` (raw / processed) and `outputs/` (synthetic, metrics, report).

## 1. Raw Dataset Record (`data/raw/<name>/metadata.yaml`)
```yaml
dataset_name: "Adult"
source: "openml"
download_url: "https://www.openml.org/d/1590"
checksum_sha256: "a1b2c3d4e5f6..."   # verified at download time
record_count: a large number of records
column_names:
  - age
  - workclass
  - fnlwgt
  - education
  - education-num
  - marital-status
  - occupation
  - relationship
  - race
  - sex
  - capital-gain
  - capital-loss
  - native-country
  - income
```

*Similar `metadata.yaml` files exist for `UCI_HAR` and `UCI_Shopper`.*

## 2. Processed Dataset (`data/processed/<name>/train.parquet`, `holdout.parquet`)
- **Format**: Apache Parquet (columnar, compression `gzip`).  
- **Schema**: All columns are either `int64`, `float64`, or `category`.  
- **Provenance**: Header in accompanying `metadata.yaml` includes:
  - `preprocessing_timestamp`
  - `imputation_strategy`
  - `encoding_strategy`
  - `train_holdout_split: "80/20"`
  - `random_seed: 123`

## 3. Synthetic Dataset (`outputs/synthetic/<dataset>_<model>_seed<NN>.csv`)
- **Format**: CSV (UTF‑8).  
- **Columns**: Identical to the processed training set (order preserved).  
- **Metadata (`.json` side‑car)**:
```json
{
  "dataset": "<dataset>",
  "model": "<CTGAN|DPGAN|CopulaGAN>",
  "seed": 42,
  "row_count": "a substantial number of rows",
  "generated_timestamp": "2026-10-17T12:34:56Z",
  "privacy_epsilon": 1.0   // only for DPGAN, null otherwise
}
```

## 4. Metric Results (`outputs/metrics/metric_results.json`)
A list of objects, each conforming to `contracts/metric_results.schema.yaml` (see contract file). Example entry:
```json
{
  "dataset": "Adult",
  "model": "CTGAN",
  "seed": 42,
  "column": "age",
  "metric_type": "KS",
  "statistic": 0.072,
  "p_value": 0.213,
  "effect_size": 0.072,
  "corrected_p_value": 0.298,
  "faithful": true
}
```

## 5. Aggregated Summary (`outputs/summary/aggregated_metrics.csv`)
- Columns: `dataset`, `model`, `metric_type`, `mean_statistic`, `std_statistic`, `mean_effect_size`, `std_effect_size`, `fraction_faithful`.

## 6. Final Report (`outputs/report/fidelity_report.pdf` & `.json`)
- JSON contains the same tables/figures in machine‑readable form.  
- PDF is generated from a Jinja2‑rendered LaTeX template (no external compilation required on CI; `matplotlib` saves figures as PNG, which are embedded as base64).

---
