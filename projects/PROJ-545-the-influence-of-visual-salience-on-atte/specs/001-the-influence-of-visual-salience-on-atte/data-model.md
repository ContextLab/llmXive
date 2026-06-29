# Data Model: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

## Overview

This document defines the data structures, schemas, and transformations used in the project. It ensures that all data flows are reproducible and that the output contracts are met.

## Entities

### 1. Scenario
A single moral dilemma instance.
*   **Attributes**:
    *   `scenario_id`: Unique identifier (string).
    *   `choice`: Binary outcome (0 = Left, 1 = Right).
    *   `stimulus_type`: "text" (only).
    *   `text_salience_score`: Computed text salience score (float, 0.0–1.0).
    *   `visual_salience_score`: Null (not applicable for this dataset).
    *   `salience_source`: "text_heuristic".
    *   `attributes`: Dictionary of control variables (species, age, gender, status, lives).
    *   `image_url`: Null (dataset is text-only).
    *   `text_content`: Text description (string).

### 2. Model Parameters
The fitted values for the aDDM.
*   **Attributes**:
    *   `drift_rate`: Base drift rate (float).
    *   `threshold`: Decision threshold (float).
    *   `non_decision_time`: Non-decision time (float).
    *   `salience_weight`: The fitted salience weight (float).
    *   `log_likelihood`: The log-likelihood of the fit (float).
    *   `converged`: Boolean indicating convergence status.
    *   `retry_count`: Number of retries attempted (int).

### 3. Comparison Metric
Statistical measures for model evaluation.
*   **Attributes**:
    *   `model_type`: "baseline" or "salience".
    *   `aic`: Akaike Information Criterion (float).
    *   `bic`: Bayesian Information Criterion (float).
    *   `log_likelihood`: Log-likelihood (float).
    *   `p_value`: Significance of improvement (float, corrected).
    *   `threshold_value`: The salience weight value used in sensitivity analysis (float).

## Data Flow

1.  **Ingestion**: Raw Moral Machine data → `data/raw/moral_machine_subset.csv` (≤ 5k rows).
2.  **Salience Computation**: `moral_machine_subset.csv` → `data/processed/salience_enriched.csv` (adds `text_salience_score`).
3.  **Model Fitting**: `salience_enriched.csv` → `data/processed/model_fits.json` (one entry per scenario).
4.  **Analysis**: `model_fits.json` + `salience_enriched.csv` → `data/processed/comparison_report.csv` (AIC/BIC, VIF, sensitivity).

## File Schemas

### `salience_enriched.csv`
*   `scenario_id`: string
*   `choice`: int (0/1)
*   `text_salience_score`: float (0.0–1.0)
*   `visual_salience_score`: float (null)
*   `salience_source`: string ("text_heuristic")
*   `stimulus_type`: string ("text")
*   `species_1`: string
*   `age_1`: string
*   `lives_1`: int
*   `species_2`: string
*   `age_2`: string
*   `lives_2`: int

### `model_fits.json`
*   `scenario_id`: string
*   `drift_rate`: float
*   `threshold`: float
*   `salience_weight`: float
*   `log_likelihood`: float
*   `converged`: boolean

### `comparison_report.csv`
*   `metric`: string ("AIC", "BIC", "VIF", "LogLik")
*   `model_type`: string ("baseline", "salience")
*   `value`: float
*   `threshold_sweep`: float (for sensitivity analysis rows)


## projects/PROJ-545-the-influence-of-visual-salience-on-atte/specs/001-the-influence-of-visual-salience-on-atte/quickstart.md

# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the Moral Machine dataset (Open Science Framework repository).
*   A GitHub Actions Free Runner (or local machine with sufficient RAM and CPU cores).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-545-the-influence-of-visual-salience-on-atte
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Preparation

1.  **Download the dataset**:
    Run the ingestion script to download and subset the Moral Machine dataset.
    ```bash
    python code/data/ingest.py --subset-size <SUBSET_SIZE> --seed 42
    ```
    *Output*: `data/raw/moral_machine_subset.csv`

2.  **Compute Salience**:
    Run the salience computation script (text-only).
    ```bash
    python code/data/salience.py --input data/raw/moral_machine_subset.csv --output data/processed/salience_enriched.csv
    ```
    *Output*: `data/processed/salience_enriched.csv` (includes `text_salience_score` column).

## Running the Analysis

1.  **Fit the aDDM Models**:
    Run the grid search and fitting script.
    ```bash
    python code/models/fit.py --input data/processed/salience_enriched.csv --output data/processed/model_fits.json
    ```
    *Note*: This may take up to 30 minutes per fold on a CPU.

2.  **Run Model Comparison & Sensitivity**:
    Run the comparison and sensitivity analysis.
    ```bash
    python code/analysis/compare.py --fits data/processed/model_fits.json --data data/processed/salience_enriched.csv
    ```
    *Output*: `data/processed/comparison_report.csv`

## Verification

To verify the pipeline:
1.  Check that `salience_enriched.csv` has no null values in `text_salience_score`.
2.  Check that `comparison_report.csv` contains entries for threshold sweeps across a range of low, medium, and high values.
3.  Ensure the VIF diagnostic is present and flags any collinearity > 5.0.

## Troubleshooting

*   **Non-convergence**: If a scenario fails to converge, check `logs/fit.log` for the retry count (capped at a predefined limit).
*   **Missing Images**: Not applicable; dataset is text-only.
*   **Memory Errors**: Ensure the subset size is ≤ 5,000 rows.


## projects/PROJ-545-the-influence-of-visual-salience-on-atte/specs/001-the-influence-of-visual-salience-on-atte/contracts/dataset.schema.yaml

$schema: "http://json-schema.org/draft-07/schema#"
title: "Salience Enriched Dataset Schema"
description: "Schema for the processed dataset with computed text salience scores."
type: "object"
properties:
  scenario_id:
    type: "string"
    description: "Unique identifier for the moral dilemma scenario."
  choice:
    type: "integer"
    description: "Binary choice outcome (0 = Left, 1 = Right)."
    minimum: 0
    maximum: 1
  text_salience_score:
    type: "number"
    description: "Computed text salience score (0.0–1.0)."
    minimum: 0.0
    maximum: 1.0
  visual_salience_score:
    type: "null"
    description: "Not applicable for this text-only dataset."
  salience_source:
    type: "string"
    description: "Method used to compute salience."
    enum:
      - "text_heuristic"
  stimulus_type:
    type: "string"
    description: "Type of stimulus."
    enum:
      - "text"
  species_1:
    type: "string"
    description: "Species of the first actor."
  age_1:
    type: "string"
    description: "Age category of the first actor."
  lives_1:
    type: "integer"
    description: "Number of lives in the first option."
    minimum: 0
  species_2:
    type: "string"
    description: "Species of the second actor."
  age_2:
    type: "string"
    description: "Age category of the second actor."
  lives_2:
    type: "integer"
    description: "Number of lives in the second option."
    minimum: 0
required:
  - scenario_id
  - choice
  - text_salience_score
  - salience_source
  - stimulus_type
additionalProperties: true


## projects/PROJ-545-the-influence-of-visual-salience-on-atte/specs/001-the-influence-of-visual-salience-on-atte/contracts/model_output.schema.yaml

$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Output Schema"
description: "Schema for aDDM fitting results and comparison metrics."
type: "object"
properties:
  run_id:
    type: "string"
    description: "Unique identifier for the model run."
  dataset_version:
    type: "string"
    description: "Checksum or version of the input dataset."
  parameters:
    type: "object"
    description: "Fitted aDDM parameters."
    properties:
      drift_rate:
        type: "number"
      threshold:
        type: "number"
      non_decision_time:
        type: "number"
      salience_weight:
        type: "number"
        minimum: 0.0
        maximum: 1.0
      attribute_coefficients:
        type: "object"
        description: "Coefficients for scenario attribute covariates (lives_saved, lives_lost, species, social_status, age_group, gender)."
        additionalProperties:
          type: "number"
    required:
      - drift_rate
      - threshold
      - non_decision_time
      - salience_weight
      - attribute_coefficients
  metrics:
    type: "object"
    description: "Performance metrics."
    properties:
      log_likelihood:
        type: "number"
      aic:
        type: "number"
      bic:
        type: "number"
      convergence_status:
        type: "string"
        enum:
          - "converged"
          - "failed"
      cv_fold:
        type: "integer"
        minimum: 1
        maximum: 5
    required:
      - log_likelihood
      - aic
      - bic
      - convergence_status
      - cv_fold
  diagnostics:
    type: "object"
    description: "Statistical diagnostics."
    properties:
      vif_salience:
        type: "number"
        description: "Variance Inflation Factor for salience predictor."
      vif_flag:
        type: "boolean"
        description: "Whether VIF > 5.0 threshold was exceeded."
      remediation_applied:
        type: "array"
        items:
          type: "string"
          enum:
            - "residualization"
            - "joint_effect_only"
        description: "Remediation steps taken if VIF exceeded threshold."
      multiple_comparison_corrected:
        type: "boolean"
        description: "Whether Bonferroni correction was applied."
      cv_convergence_rate:
        type: "number"
        minimum: 0.0
        maximum: 1.0
        description: "Proportion of 5-fold CV splits that converged (SC-002 target: ≥ 0.95)."
    required:
      - vif_salience
      - vif_flag
      - remediation_applied
      - multiple_comparison_corrected
      - cv_convergence_rate
  simulation_calibration:
    type: "object"
    description: "Simulation-based calibration results."
    properties:
      true_salience_weight:
        type: "number"
      fitted_salience_weight:
        type: "number"
      recovery_error:
        type: "number"
        description: "Absolute difference between true and fitted weights."
    required:
      - true_salience_weight
      - fitted_salience_weight
      - recovery_error
  culpability_detection:
    type: "object"
    description: "FR-008 culpability label detection result."
    properties:
      explicit_labels_found:
        type: "boolean"
        description: "Whether explicit 'actual culpability' labels were found."
      proxy_variables_used:
        type: "array"
        items:
          type: "string"
        description: "List of proxy control variables used (e.g., lives_saved, species)."
    required:
      - explicit_labels_found
      - proxy_variables_used
  sensitivity_analysis:
    type: "array"
    description: "Results of the salience weight sweep over {0.01, 0.05, 0.10}."
    items:
      type: "object"
      properties:
        salience_weight_value:
          type: "number"
        log_likelihood:
          type: "number"
        aic:
          type: "number"
      required:
        - salience_weight_value
        - log_likelihood
        - aic
required:
  - run_id
  - dataset_version
  - parameters
  - metrics
  - diagnostics
  - simulation_calibration
  - culpability_detection
  - sensitivity_analysis
additionalProperties: false



## projects/PROJ-545-the-influence-of-visual-salience-on-atte/specs/001-the-influence-of-visual-salience-on-atte/contracts/processed_scenario.schema.yaml

$schema: "http://json-schema.org/draft-07/schema#"
title: "Processed Scenario Schema"
description: "Schema for scenario data after text salience computation."
type: "object"
properties:
  scenario_id:
    type: "string"
    description: "Unique identifier for the moral dilemma instance."
  stimulus_type:
    type: "string"
    enum:
      - "text"
    description: "Type of stimulus provided in the dilemma."
  text_salience_score:
    type: "number"
    minimum: 0.0
    maximum: 1.0
    description: "Computed text salience score (0.0-1.0)."
  visual_salience_score:
    type: "null"
    description: "Not applicable for this text-only dataset."
  choice_outcome:
    type: "integer"
    enum:
      - 0
      - 1
    description: "Binary choice outcome recorded in dataset."
  attributes:
    type: "object"
    description: "Scenario attributes (lives, species, status, age, gender)."
    properties:
      lives_saved:
        type: "integer"
      lives_lost:
        type: "integer"
      species:
        type: "string"
      social_status:
        type: "string"
      age_group:
        type: "string"
      gender:
        type: "string"
    required:
      - lives_saved
      - lives_lost
required:
  - scenario_id
  - stimulus_type
  - text_salience_score
  - choice_outcome
  - attributes
additionalProperties: false