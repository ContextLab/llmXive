# Data Model: Statistical Modeling of Temporal Dependence in Cryptocurrency Price Fluctuations

## Overview
The project manipulates three logical data entities:

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **AssetPriceRaw** | Unprocessed OHLCV records for a single asset. | `date (ISO8601)`, `open (float)`, `high (float)`, `low (float)`, `close (float)`, `volume (float)` |
| **AssetReturnSeries** | Daily log‑returns and volatility proxy derived from `AssetPriceRaw`. | `date`, `btc_return`, `eth_return`, `vol_proxy_sq`, `vol_proxy_10d_std` |
| **RegimeLabelSeries** | Integer regime label aligned with `AssetReturnSeries`. | `date`, `regime (int; 1=Low‑Vol, 2=High‑Vol, …)` |
| **RSVARModel** | Collection of regime‑specific VAR parameters. | `regime (int)`, `coef_matrix (k×k)`, `cov_matrix (k×k)`, `lag (int)` |
| **ModelComparisonMetrics** | Summary statistics for model selection & hypothesis tests. | `model_name`, `BIC`, `LR_pvalue`, `bootstrap_resamples`, `test_type` |

All files are stored under `data/` (raw & derived) or `results/` (model outputs). Each transformation writes a new file; original raw files are never overwritten (Constitution Principle III).

## Schema Definitions
Below are the JSON‑compatible schemas used by the contract tests. See `contracts/` for the full YAML versions.

### `raw_price.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Raw OHLCV price record"
type: object
required: [date, open, high, low, close, volume]
properties:
  date:
    type: string
    format: date
    description: "Trading day (ISO‑8601)."
  open:
    type: number
  high:
    type: number
  low:
    type: number
  close:
    type: number
  volume:
    type: number
additionalProperties: false
```

### `regime_labels.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Regime label series"
type: array
items:
  type: object
  required: [date, regime]
  properties:
    date:
      type: string
      format: date
    regime:
      type: integer
      enum: [1, 2, 3]   # 1=Low‑Vol, 2=High‑Vol, 3=optional third regime
additionalProperties: false
```

### `rsvart_output.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "RS‑VAR model output per regime"
type: object
required: [regime, lag, coef_matrix, cov_matrix, autocorr_btc, autocorr_eth, cross_corr_resid]
properties:
  regime:
    type: integer
  lag:
    type: integer
    minimum: 1
  coef_matrix:
    type: array
    items:
      type: array
      items:
        type: number
  cov_matrix:
    type: array
    items:
      type: array
      items:
        type: number
  autocorr_btc:
    type: number
  autocorr_eth:
    type: number
  cross_corr_resid:
    type: number
additionalProperties: false
```

All schemas are version‑controlled under `contracts/` and will be validated by the CI test suite.

---
