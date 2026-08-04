# Data Model: The Influence of Simulated Social Status on Risk-Taking Behavior

## 1. Entity Definitions

### 1.1 Participant
The unit of observation.
- **Attributes**:
  - `participant_id`: Unique string identifier (e.g., "P001").
  - `status_level`: Categorical (High, Low).
  - `observed_behavior`: Categorical (Risky, Conservative).
  - `risk_taking_score`: Numeric (Continuous or Binary, depending on simulation).
  - `condition`: Derived string (e.g., "High_Risky").
  - `is_outlier`: Boolean (flagged during sensitivity analysis).

### 1.2 ModelResult
The output of the regression analysis.
- **Attributes**:
  - `fixed_effects`: Dict of coefficients (intercept, main effects, interaction).
  - `standard_errors`: Dict of SEs.
  - `p_values`: Dict of p-values.
  - `adjusted_p_values`: Dict of Bonferroni-corrected p-values for post-hoc comparisons (**FR-006**).
  - `ci_width`: Float (Width of the 95% Confidence Interval for the interaction coefficient) (**SC-003**).
  - `random_effects`: (If applicable) Variance components.
  - `vif_scores`: Dict of VIFs for fixed effects (**FR-004**).
  - `design_type`: String ("within-subjects" or "between-subjects").
  - `outcome_type`: String ("continuous" or "binary").

### 1.3 SensitivityResult
The output of the outlier sweep.
- **Attributes**:
  - `threshold`: Float (2.5, 3.0, 3.5).
  - `interaction_coefficient`: Float.
  - `interaction_p_value`: Float.
  - `sample_size`: Int (N after exclusion).

### 1.4 SimulationParameters
Metadata recording the generation process (**SC-004**).
- **Attributes**:
  - `instrument`: String (e.g., "BART").
  - `effect_size`: Float (Cohen's d used).
  - `interaction_effect`: Float (True interaction effect used in generation).
  - `seed`: Int.
  - `mode`: String ("recovery" or "null").

## 2. Data Flow

1.  **Generation**: `generate_data.py` -> `data/raw/simulated_data.csv` (or directly to processed).
2.  **Preprocessing**: `preprocess.py` reads raw -> `data/processed/cleaned_data.csv` + `data/processed/outcome_type.json` + `data/processed/design_type.json` + `data/processed/simulation_parameters.json`.
3.  **Design Detection**: `preprocess.py` detects design type (based on rows per ID) and writes `design_type.json`.
4.  **Model Fitting**: `analysis.py` reads cleaned data + config -> `data/processed/model_results.json` + `data/processed/vif_scores.json`.
5.  **Sensitivity**: `analysis.py` -> `data/processed/sensitivity_results.json` + `data/processed/stability_metric.json`.
6.  **Reporting**: `reporting.py` reads all JSONs -> `report/forest_plot.png`, `report/final_report.pdf`.
7.  **Hash Update**: `hash_update.py` computes hashes and updates state file.

## 3. File Specifications

### 3.1 `data/processed/cleaned_data.csv`
- **Columns**: `participant_id`, `status_level`, `observed_behavior`, `risk_taking_score`, `is_outlier`.
- **Constraints**: No missing values in key columns; `status_level` and `observed_behavior` strictly binarized.

### 3.2 `data/processed/outcome_type.json`
- **Schema**: `{"type": "continuous" | "binary"}`.

### 3.3 `data/processed/design_type.json`
- **Schema**: `{"design_type": "within-subjects" | "between-subjects"}`.

### 3.4 `data/processed/simulation_parameters.json`
- **Schema**: `{"instrument": "BART", "effect_size": 0.4, "interaction_effect": 0.3, "seed": 42, "mode": "recovery"}`.

### 3.5 `data/processed/model_results.json`
- **Schema**: Contains fixed effects, p-values, `ci_width`, VIFs, adjusted p-values, and design type.

### 3.6 `data/processed/stability_metric.json`
- **Schema**: `{"is_stable": true, "p_values": [0.02, 0.03, 0.04]}` (True if all p < 0.05).

## 4. Validation Rules

- **FR-002**: `status_level` and `observed_behavior` must have exactly 2 levels.
- **FR-003**: Model family must match `outcome_type`.
- **FR-004**: VIF > 5.0 must be flagged in logs.
- **FR-005**: Sensitivity sweep must run for 2.5, 3.0, 3.5 SD.
- **SC-003**: `ci_width` must be calculated and stored.
- **SC-002**: `stability_metric.json` must confirm p-value stability across thresholds.