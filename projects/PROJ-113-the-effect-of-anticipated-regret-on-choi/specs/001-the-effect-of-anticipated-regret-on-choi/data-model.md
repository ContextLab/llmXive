# Data Model: The Effect of Anticipated Regret on Choice Deferral

## Overview
This document defines the data structures used throughout the research pipeline, from raw ingestion to final model outputs. All data transformations are deterministic and reproducible.

## Entities

### 1. Trial
A single decision event.
- **Unique Identifier**: `trial_id` (String/Int)
- **Participant ID**: `participant_id` (String/Int) - Groups trials for random effects.
- **Deferral Flag**: `deferral` (Boolean) - 1 if choice was deferred, 0 otherwise.
- **Option Count**: `option_count` (Int) - Number of options presented.
- **Regret Proxy**: `regret_proxy` (Float) - **Min-Max Regret** (max(EU) - EU_chosen).
- **Normalized Regret**: `normalized_regret` (Float) - `regret_proxy` / (max(EU) - min(EU)).
- **Covariates**:
  - `perceived_risk` (Float) - Or proxy (price variance).
  - `time_pressure` (Float) - Time available vs. time taken.
  - `decision_style` (String) - Categorical (e.g., "maximizing", "satisficing").
  - `stakes` (Float) - Global magnitude of attributes (to test interaction with regret).

### 2. Option
Individual items within a trial.
- **Trial ID**: `trial_id` (String/Int) - Foreign key.
- **Option ID**: `option_id` (String/Int)
- **Attributes**:
  - `price` (Float)
  - `rating` (Float)
  - `other_attributes` (Dict) - Any other numeric features.

## Data Flow

1. **Raw Input**: Parquet files from HuggingFace.
2. **Intermediate**:
   - `data/processed/options_normalized.parquet`: Normalized attributes per trial (global scaling).
   - `data/processed/trials_with_proxy.csv`: Final analysis dataset with computed `regret_proxy` and `normalized_regret`.
3. **Model Output**:
   - `results/coefficients.csv`: Regression coefficients, SE, p-values.
   - `results/vif_report.csv`: Variance Inflation Factors.
   - `results/robustness_report.csv`: Results from sensitivity analysis and secondary dataset.

## Transformations

### Global Normalization
For each attribute $A$ across the entire dataset:
1. Calculate global min ($min_A$) and max ($max_A$).
2. Normalize: $x' = (x - min_A) / (max_A - min_A)$.

### Regret Proxy Calculation
For each trial $t$:
1. Extract attribute matrix $A_t$ (rows = options, cols = attributes).
2. Compute Expected Utility: $EU_i = \sum w_j \cdot x'_{ij}$.
3. Identify $EU_{max} = \max(EU_{1..k})$ and $EU_{chosen}$ (or 0 if deferral).
4. Compute **Regret Proxy**: $R_t = EU_{max} - EU_{chosen}$.
5. Compute **Normalized Regret**: $NR_t = R_t / (EU_{max} - EU_{min})$.

### Deferral Logic
- If `choice_timestamp` is null or > `deadline`, `deferral = 1`.
- Else `deferral = 0`.

## Data Quality Rules
- **Missing Values**: Impute numeric covariates with mean. Log count.
- **Single Option**: If `option_count` == 1, `regret_proxy` = 0.
- **Zero Variance**: If all options have identical attributes, `regret_proxy` = 0.