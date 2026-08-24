# Data Model: Simulated Social Status on Risk-Taking

## Overview

This document defines the schema for the synthetic dataset, the preprocessed data, and the model outputs. It ensures that the data pipeline adheres to the constraints of the factorial design (2x2) and the requirements for mixed-effects modeling.

## Entity Definitions

### 1. Participant
- **Definition**: An individual unit of observation.
- **Attributes**:
  - `participant_id`: Unique string identifier.
  - `condition`: Derived combination of status and behavior.

### 2. Condition (Experimental Factor)
- **Definition**: A combination of `status_level` and `observed_behavior`.
- **Levels**:
  - `status_level`: Binary (High, Low).
  - `observed_behavior`: Binary (Risky, Conservative).
- **Combinations**: 4 total (High/Risky, High/Conservative, Low/Risky, Low/Conservative).

### 3. Risk Metric
- **Definition**: The dependent variable representing risk-taking behavior.
- **Source**: Simulated to match the distribution of the Balloon Analog Risk Task (BART).
- **Type**: Continuous (number of pumps) or Binary (burst vs. cash out), determined dynamically.

## Schema Details

### Raw Data Schema (`data/raw/simulated_data.csv`)

| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique ID | Unique, non-null |
| `status_level` | string | Status of observed agent | Values: "High", "Low" |
| `observed_behavior` | string | Behavior of observed agent | Values: "Risky", "Conservative" |
| `risk_taking_score` | float | Outcome variable | Non-negative; distribution based on BART |
| `seed` | int | Random seed for reproducibility | Fixed per run |

### Processed Data Schema (`data/processed/cleaned_data.csv`)

| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique ID | Unique |
| `status_level` | category | Categorical factor | Levels: ["High", "Low"] |
| `observed_behavior` | category | Categorical factor | Levels: ["Risky", "Conservative"] |
| `risk_taking_score` | float | Outcome | No missing values (imputed or excluded) |
| `is_outlier` | boolean | Flag from sensitivity analysis | Default: False |

### Model Configuration (`data/processed/model_config.json`)

```json
{
  "family": "gaussian",
  "random_effects": "(1|participant_id)",
  "fixed_effects": ["status_level", "observed_behavior", "status_level:observed_behavior"],
  "data_structure": "within-subjects"
}
```

### Output Schema (`data/processed/model_output.json`)

| Key | Type | Description |
| :--- | :--- | :--- |
| `fixed_effects` | object | Map of coefficient names to {estimate, std_err, p_value} |
| `interaction_p_value` | float | P-value for the status_level:observed_behavior interaction. |
| `interaction_coefficient` | float | Beta coefficient for the interaction term. |
| `vif_scores` | object | Map of predictors to VIF values |
| `convergence_status` | string | "Success" or "Warning" |

## Data Flow

1. **Generation**: `simulation.py` creates `raw/simulated_data.csv` using `numpy.random.default_rng(seed)`.
2. **Validation**: `preprocess.py` checks for missing levels, bins if necessary (e.g., "Medium" -> "Low"), and detects outcome type.
3. **Analysis**: `analysis.py` fits the model, calculates VIF, and performs sensitivity sweeps.
4. **Reporting**: `reporting.py` generates `forest_plot.png` and `sensitivity_analysis.csv`.
