# Data Model: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Overview
The data model defines the shape of raw, intermediate, and final artifacts used throughout the pipeline. All files are validated against the JSON‑Schema contracts in `contracts/`.

## Entities

### 1. Raw VAERS Record (source parquet)
| Field | Type | Description |
|-------|------|-------------|
| `VAERS_ID` | integer | Unique report identifier. |
| `VAX_TYPE` | string | Vaccine name (e.g., “COVID‑19”, “Influenza”). |
| `SOC_CODE` | string | MedDRA System Organ Class code (if present). |
| `REPT_DATE` | string (date) | Date the report was submitted (YYYY‑MM‑DD). |
| `AGE` | number | Patient age in years (may be missing). |
| `SEX` | string | “M”, “F”, or “U”. |
| `VAX_DATE` | string (date) | Date of vaccination (often missing). |
| `EVENT_DATE` | string (date) | Date of adverse event (may be missing). |
| `OUTCOME` | string | Outcome description. |
| *(additional fields may exist; they are ignored after validation)* |

### 2. Cleaned & Grouped Record (`data/processed/cleaned.parquet`)
| Field | Type | Description |
|-------|------|-------------|
| `VAERS_ID` | integer | Propagated from raw. |
| `VAX_GROUP` | string | One of `"COVID-19"`, `"Non-COVID-Non-Flu"`, `"Flu-only"`. |
| `SOC_CODE` | string | MedDRA SOC code (mapped). |
| `SOC_NAME` | string | Human‑readable SOC name. |
| `REPT_DATE` | date | Parsed `YYYY‑MM‑DD`. |
| `AGE` | number | Numeric age (may be NaN). |
| `SEX` | string | “M”, “F”, “U”. |
| *(no missing SOC or REPT_DATE rows survive this stage)* |

### 3. Signal Record (`output/signals.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | string | MedDRA SOC code. |
| `SOC_NAME` | string | SOC name. |
| `ROR` | number | Reporting Odds Ratio. |
| `ROR_CI_lower` | number | Lower 95 % CI. |
| `ROR_CI_upper` | number | Upper 95 % CI. |
| `PRR` | number | Proportional Reporting Ratio. |
| `PRR_CI_lower` | number | Lower 95 % CI. |
| `PRR_CI_upper` | number | Upper 95 % CI. |
| `IC` | number | Information Component. |
| `IC_CI_lower` | number | Lower 95 % CI. |
| `IC_CI_upper` | number | Upper 95 % CI. |
| `p_value_raw` | number | Fisher exact test p‑value. |
| `p_value_adj` | number | BH‑adjusted p‑value. |
| `is_signal` | boolean | True if ≥ 2 of 3 metric thresholds satisfied. |
| `signal_metrics` | string (JSON array) | List of metrics that passed thresholds. |

### 4. Temporal Profile Record (`output/temporal_profiles/<SOC>.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | string | SOC identifier. |
| `week_offset` | integer | Weeks relative to median COVID‑19 `REPT_DATE`. |
| `count_covid` | integer | Weekly count for COVID‑19 reports. |
| `count_non_covid` | integer | Weekly count for Non‑COVID‑Non‑Flu reports. |
| `total_count` | integer | Sum of the two counts. |

### 5. Sensitivity Comparison Record (`output/sensitivity_analysis.csv`)
| Field | Type | Description |
|-------|------|-------------|
| `SOC_CODE` | string | SOC identifier. |
| `delta_ROR` | number | ROR (COVID vs. Flu‑only) − ROR (COVID vs. Non‑COVID‑Non‑Flu). |
| `delta_PRR` | number | Same for PRR. |
| `delta_IC` | number | Same for IC. |
| `baseline` | string | `"Flu-only"` (always for this table). |

## Constraints
- **Memory**: All DataFrames must stay ≤ 7 GB; `src/utils/config.py` sets `MAX_MEMORY_GB = 7`.  
- **Date format**: `REPT_DATE` stored as ISO `YYYY‑MM‑DD`.  
- **SOC Mapping**: Mapping file `data/meddra_to_soc.csv` must contain at least 95 % of observed `SOC_CODE`s; missing codes are logged and excluded.  
- **Continuity correction**: 0.5 added to any zero cell before metric calculation.  
- **Schema validation**: `src/data/validate.py` enforces `contracts/dataset.schema.yaml` before any downstream step.  

---
