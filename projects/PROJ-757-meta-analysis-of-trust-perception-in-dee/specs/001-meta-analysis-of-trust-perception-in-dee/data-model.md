# Data Model: Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in CSV/Parquet format under `data/` and processed in-memory for analysis.

## Entity Definitions

### 1. Study (Primary Record)
Represents a primary research paper included in the meta-analysis.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `study_id` | str | Unique identifier (e.g., DOI or generated hash) | Search Result |
| `title` | str | Full title of the paper | Search Result |
| `year` | int | Publication year | Search Result |
| `source` | str | API source (OpenAlex, Semantic Scholar, arXiv) | Search Result |
| `abstract` | str | Abstract text | Search Result |
| `doi` | str | Digital Object Identifier | Search Result |
| `included` | bool | Inclusion status after screening | Screening Log |
| `exclusion_reason` | str | Reason for exclusion (e.g., "NO_TRUST_METRIC") | Screening Log |
| `adjudicated` | bool | Flag: was this study resolved by automated tie-breaker? (Always False if halted) | Screening Log |
| `realism_level` | float/str | Stratified realism score (if reported) | Extracted Data |
| `media_literacy_score` | float/NaN | Mean media literacy score of participants (NaN if categorical only) | Extracted Data |
| `n_authentic` | int | Sample size for authentic condition | Extracted Data |
| `n_deepfake` | int | Sample size for deepfake condition | Extracted Data |
| `mean_authentic` | float | Mean trust rating (authentic) | Extracted Data |
| `mean_deepfake` | float | Mean trust rating (deepfake) | Extracted Data |
| `sd_authentic` | float | SD trust rating (authentic) | Extracted Data |
| `sd_deepfake` | float | SD trust rating (deepfake) | Extracted Data |
| `odds_ratio` | float | Odds ratio (if binary outcome) | Extracted Data |
| `ci_lower` | float | Lower CI bound (if OR) | Extracted Data |
| `ci_upper` | float | Upper CI bound (if OR) | Extracted Data |
| `t_stat` | float | t-statistic (if reported) | Extracted Data |
| `p_value` | float | p-value (if reported and exact) | Extracted Data |
| `p_value_raw` | str | Raw p-value string (e.g., "p < 0.05") to preserve inexactness | Extracted Data |
| `p_value_is_inexact` | bool | Flag: was p-value rounded/inexact? | Extracted Data |
| `sd_imputed` | bool | Flag: was SD imputed? (Always False for primary) | Harmonization Log |
| `sd_reconstructed` | bool | Flag: was SD reconstructed from exact p/t? | Harmonization Log |
| `sd_missing` | bool | Flag: was SD missing and unrecoverable? | Harmonization Log |

### 2. EffectSize (Derived Record)
Represents the calculated effect size for a study.

| Field | Type | Description |
|-------|------|-------------|
| `study_id` | str | Foreign key to Study |
| `effect_size` | float | Cohen's d or log-OR |
| `se` | float | Standard error |
| `metric_type` | str | "cohens_d" or "log_odds" |
| `included_in_primary` | bool | True if not excluded by FR-003 (False if `sd_reconstructed` or `sd_missing` or `p_value_is_inexact`) |
| `included_in_regression` | bool | True if moderator data exists and is continuous |

### 3. Moderator (Derived Record)
Represents study-level moderators for regression.

| Field | Type | Description |
|-------|------|-------------|
| `study_id` | str | Foreign key to Study |
| `realism` | float/str | Realism level (continuous or categorical) |
| `media_literacy` | float | Media literacy score (NaN if categorical only) |

## Data Flow

1. **Search**: `01_search_and_screen.py` -> `data/search_results/raw_studies.csv`
2. **Screening**: `01_search_and_screen.py` -> `data/screening/screening_log.csv`, `data/screening/inclusion_criteria.yaml`
3. **Harmonization**: `02_effect_size_calc.py` -> `data/harmonized/effect_sizes.csv`
4. **Analysis**: `03_meta_analysis_driver.py` reads `effect_sizes.csv` -> `results/analysis_output.csv`
5. **Robustness**: `04_robustness_checks.py` reads `analysis_output.csv` -> `results/robustness/`

## Data Constraints

- **Missing Values**: All missing numeric fields must be `NaN`.
- **Flags**: `sd_imputed`, `sd_reconstructed`, `sd_missing`, `p_value_is_inexact` must be boolean.
- **Uniqueness**: `study_id` must be unique.
- **Exclusion Rule**: If `sd_missing` is True OR `sd_reconstructed` is True OR `p_value_is_inexact` is True, `included_in_primary` MUST be False.
- **Adjudication**: If `adjudicated` is True, the `exclusion_reason` should be null (included) or the specific reason if excluded by tie-breaker. (Note: Pipeline halts if Kappa < 0.6, so this flag is rarely True).

## Inclusion Criteria Artifact

The file `data/screening/inclusion_criteria.yaml` MUST be generated in Phase 1.1. It contains the machine-readable rules used for screening:
```yaml
criteria:
  - type: "peer_reviewed"
    value: true
  - type: "trust_metric"
    value: "explicit"
  - type: "moderator_data"
    value: ["media_literacy", "realism_stratification"]
```