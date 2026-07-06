# Data Model: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

## 1. Overview

This document defines the data structures for raw EEG data, processed epochs, synchrony metrics, and behavioral outputs. All data is stored in `data/` subdirectories.

## 2. Raw Data Schema

Raw data is downloaded from OpenNeuro (or verified source) and stored as BIDS-compliant files.

**Directory**: `data/raw/`  
**Format**: BIDS (Brain Imaging Data Structure)  
**Key Files**:
- `sub-XX/func/sub-XX_task-switching_eeg.edf` (or `.fif`)
- `sub-XX/func/sub-XX_task-switching_events.tsv`

**Constraints**:
- Must contain `stimulus_type` column in events (values: `switch`, `stay`).
- Must contain `onset` and `duration` columns.
- Must contain `reaction_time` (optional in events, often in separate behavioral file).

## 3. Processed Data Schema

### 3.1 Epochs
**Directory**: `data/processed/`  
**Format**: MNE-Python Epochs (`.fif` or `.pkl`)  
**Schema**:
- `subject_id`: str (e.g., "sub-01")
- `epochs`: array-like (n_trials, n_channels, n_times)
- `events`: array-like (n_trials, 3) - [sample, 0, event_code]
- `event_id`: dict - mapping of event codes to labels (switch, stay)
- `info`: MNE Info object (channels, montage, sampling frequency)

**Derived Fields**:
- `clean`: bool (True if ICA applied and no excessive artifact removal)
- `trial_count`: int (Total trials per condition)

### 3.2 Synchrony Metrics
**Directory**: `data/metrics/`  
**Format**: CSV / Parquet  
**Schema**: `synchrony_metrics.csv`

| Column | Type | Description |
|--------|------|-------------|
| `subject_id` | str | Unique subject identifier |
| `condition` | str | "switch" or "stay" |
| `band` | str | "theta" or "gamma" |
| `pair` | str | Electrode pair (e.g., "F3-P3") |
| `wpli` | float | Weighted Phase-Lag Index value |
| `plv` | float | Phase-Locking Value (optional) |
| `mean_wpli` | float | Mean wPLI across pairs for this band/condition |

### 3.3 Behavioral Metrics
**Directory**: `data/metrics/`  
**Format**: CSV  
**Schema**: `behavioral_metrics.csv`

| Column | Type | Description |
|--------|------|-------------|
| `subject_id` | str | Unique subject identifier |
| `rt_switch` | float | Mean RT for switch trials (ms) |
| `rt_stay` | float | Mean RT for stay trials (ms) |
| `switching_cost` | float | `rt_switch - rt_stay` (ms) |
| `accuracy_switch` | float | Accuracy for switch trials |
| `accuracy_stay` | float | Accuracy for stay trials |
| `n_trials_switch` | int | Count of switch trials |
| `n_trials_stay` | int | Count of stay trials |

### 3.4 Trial-Level Data (FR-009 Input)
**Directory**: `data/trial_level/`  
**Format**: CSV  
**Schema**: `per_trial_synchrony.csv`

| Column | Type | Description |
|--------|------|-------------|
| `subject_id` | str | Unique subject identifier |
| `trial_id` | int | Unique trial identifier |
| `condition` | str | "switch" or "stay" |
| `reaction_time` | float | Reaction time for this trial (ms) |
| `synchrony_theta` | float | wPLI value for theta band for this trial |
| `synchrony_gamma` | float | wPLI value for gamma band for this trial |
| `window` | str | Pre-stimulus window used (e.g., "-500_0") |

**Note**: This file is the input for the Linear Mixed-Effects (LME) model in FR-009. It links trial-level synchrony to trial-level RT.

### 3.5 Analysis Results
**Directory**: `data/results/`  
**Format**: JSON / CSV  
**Schema**: `correlation_results.json`

- `correlation_coefficient`: float
- `p_value`: float
- `p_value_corrected`: float (Bonferroni)
- `n_permutations`: int
- `confidence_interval`: [lower, upper]
- `method`: str (e.g., "pearson", "spearman")

### 3.6 Trial-Level Analysis Results (FR-009 Output)
**Directory**: `data/results/`  
**Format**: JSON  
**Schema**: `trial_level_analysis.json`

- `model_type`: str (e.g., "lme4", "statsmodels")
- `formula`: str (e.g., "RT ~ synchrony_theta + (1|subject_id)")
- `fixed_effects`: dict (coefficients for fixed effects)
- `random_effects_variance`: dict (variance components)
- `p_value`: float (p-value for the synchrony predictor)
- `r_squared`: float (marginal and conditional R-squared)
- `n_trials`: int (total trials used)
- `n_subjects`: int (total subjects used)
- `interpretation`: str (Associational interpretation note)

### 3.7 Sensitivity Report
**Directory**: `data/results/`  
**Format**: JSON  
**Schema**: `sensitivity_report.json`

- `primary_window`: str (e.g., "-500_0")
- `shifted_windows`: [str] (e.g., ["-600_0", "-400_0"])
- `primary_r`: float
- `shifted_r_values`: [float]
- `r_change_max`: float
- `primary_p`: float
- `shifted_p_values`: [float]
- `stable`: bool (True if r_change < 0.1 and p < 0.05 for all windows)

### 3.8 Data Gap Report (Dataset Unavailable)
**Directory**: `data/results/`  
**Format**: JSON  
**Schema**: `data_gap_report.json`

- `search_query`: str (e.g., "task-switching")
- `datasets_found`: int (number of datasets found)
- `datasets_validated`: int (number of datasets with valid schema)
- `reason`: str (e.g., "No task-switching dataset found in OpenNeuro")
- `timestamp`: str (ISO 8601)

## 4. Exclusion Log

**Directory**: `data/`  
**Format**: CSV  
**Schema**: `exclusions.csv`

| Column | Type | Description |
|--------|------|-------------|
| `subject_id` | str | Subject ID |
| `reason` | str | "insufficient_trials", "excessive_artifact", "missing_data" |
| `details` | str | Log message with specific counts |

## 5. Data Flow

1. **Download**: Raw BIDS data -> `data/raw/`
2. **Preprocess**: Raw -> Clean Epochs -> `data/processed/`
3. **Compute**: Epochs -> Synchrony Metrics -> `data/metrics/synchrony_metrics.csv`
4. **Behavior**: Raw Events -> Behavioral Metrics -> `data/metrics/behavioral_metrics.csv`
5. **Trial-Level**: Epochs + Events -> `data/trial_level/per_trial_synchrony.csv`
6. **Analyze**: Metrics -> Correlation Results -> `data/results/`
7. **Trial-Level Analysis**: `per_trial_synchrony.csv` -> LME Model -> `data/results/trial_level_analysis.json`
8. **Sensitivity**: Primary -> Shifted Windows -> `data/results/sensitivity_report.json`
9. **Data Gap**: If search fails -> `data/results/data_gap_report.json`