# Data Model: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Overview
The data model defines the shape of raw, intermediate, and final artifacts used throughout the pipeline. All files are validated against the JSON‑Schema contracts in `contracts/`.

## Entities

### 1. Raw VAERS Record (source parquet)
| Field | Type | Description |
|-------|------|-------------|
| `VAERS_ID` | integer | Unique report identifier. |
| `VAX_TYPE` | string | Vaccine name (e.g., “COVID‑19”, “Influenza”). |
| `SOC_CODE` | string | MedDRA System Organ Class code (as provided). |
| `REPT_DATE` | string (date) | Date the report was submitted (YYYY‑MM‑DD). |
| `AGE` | number | Patient age in years (may be missing). |
| `SEX` | string | “M”, “F”, or “U”. |
| *(additional fields are allowed but ignored after validation)* |

### 2. Cleaned & Grouped Record (`data/processed/cleaned.parquet`)
| Field | Type | Description |
|-------|------|-------------|
| `VAERS_ID` | integer | Propagated from raw. |
| `VAX_GROUP` | string | `"COVID-19"`, `"Non-COVID-Non-Flu"` or `"Flu-only"` (derived). |
| `SOC_CODE` | string | MedDRA SOC code (mapped). |
| `SOC_NAME` | string | Human‑readable SOC name (from `meddra_to_soc.csv`). |
| `REPT_DATE` | date | Parsed `YYYY‑MM‑DD`. |
| `AGE` | number | Numeric age (may be NaN). |
| `SEX` | string | “M”, “F”, “U”. |
| *(no rows with missing `SOC_CODE` or `REPT_DATE` survive this stage)* |

### 3. Signal Record (`output/signals.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | string | MedDRA SOC code. |
| `SOC_NAME` | string | Human‑readable SOC name. |
| `ROR` | number | Reporting Odds Ratio. |
| `ROR_CI_lower` | number | Lower 95 % CI for ROR. |
| `ROR_CI_upper` | number | Upper 95 % CI for ROR. |
| `PRR` | number | Proportional Reporting Ratio. |
| `PRR_CI_lower` | number | Lower 95 % CI for PRR. |
| `PRR_CI_upper` | number | Upper 95 % CI for PRR. |
| `IC` | number | Information Component. |
| `IC_CI_lower` | number | Lower 95 % CI for IC. |
| `IC_CI_upper` | number | Upper 95 % CI for IC. |
| `p_value_raw` | number | Fisher exact test p‑value. |
| `p_value_adj` | number | Benjamini‑Hochberg adjusted p‑value. |
| `is_signal` | boolean | True if the SOC meets the signal criteria (≥ 2 metrics exceed thresholds, BH‑adjusted p‑value < 0.05, and hold‑out validation passes). |
| `signal_metrics` | string (JSON array) | List of metrics that passed thresholds (`["ROR","PRR"]`, etc.). |

### 4. Temporal Profile Record (`output/temporal_profiles/<SOC>.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | string | SOC identifier. |
| `week_offset` | integer | Weeks relative to median COVID‑19 `REPT_DATE`. |
| `count_covid` | integer | Weekly count for COVID‑19 reports. |
| `count_non_covid` | integer | Weekly count for Non‑COVID‑Non‑Flu reports. |
| `total_count` | integer | Sum of the two counts. |

*Optional visualisation*: a PNG plot (`output/temporal_profiles/<SOC>.png`) may be generated for each SOC, but PNG files are **auxiliary** and are not covered by a JSON‑Schema contract.

### 5. Sensitivity Comparison Record (`output/sensitivity_analysis.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | string | SOC identifier. |
| `delta_ROR` | number | Difference in ROR between Flu‑only and Non‑COVID‑Non‑Flu baselines. |
| `delta_PRR` | number | Difference in PRR between Flu‑only and Non‑COVID‑Non‑Flu baselines. |
| `delta_IC` | number | Difference in IC between Flu‑only and Non‑COVID‑Non‑Flu baselines. |
| `baseline` | string | Constant value `"Flu-only"` (for documentation). |

## Constraints
- **Memory**: All DataFrames must stay ≤ 7 GB; `src/utils/config.py` sets `MAX_MEMORY_GB = 7`.  
- **Date format**: `REPT_DATE` stored as ISO `YYYY‑MM‑DD`.  
- **SOC Mapping Coverage**: `data/meddra_to_soc.csv` must contain ≥ 95 % of observed `SOC_CODE`s; missing codes are logged and excluded.  
- **Continuity correction**: 0.5 added to any zero cell before metric calculation.  
- **Schema validation**: `src/data/validate_raw.py` validates against `contracts/raw_dataset.schema.yaml`; `src/data/validate_clean.py` validates against `contracts/cleaned_dataset.schema.yaml`.  

---

