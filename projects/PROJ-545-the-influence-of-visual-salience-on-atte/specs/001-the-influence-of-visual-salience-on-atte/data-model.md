# Data Model: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

## Entities

### Scenario
Represents a single moral dilemma instance.
- **Fields**: `scenario_id`, `stimulus_type` (image/text), `salience_score`, `choice_outcome` (0/1), `attributes` (json: lives, species, status, age, gender).
- **Constraints**: `salience_score` ∈ [0.0, 1.0].

### ModelParameters
Represents the fitted aDDM configuration.
- **Fields**: `run_id`, `dataset_version`, `drift_rate`, `threshold`, `non_decision_time`, `salience_weight`, `log_likelihood`, `convergence_status`, `cv_fold`, `vif_salience`.
- **Constraints**: `salience_weight` ∈ [0.0, 1.0].

### ComparisonMetric
Represents the output of model comparison.
- **Fields**: `metric_name` (AIC/BIC/LL), `baseline_value`, `salience_value`, `difference`, `p_value`, `corrected_p_value`, `cv_fold`.
- **Constraints**: `p_value` ∈ [0.0, 1.0].

### SimulationGroundTruth
Represents synthetic data for calibration.
- **Fields**: `simulation_id`, `true_salience_weight`, `generated_choices`, `fitted_salience_weight`, `recovery_error`.
- **Constraints**: `true_salience_weight` ∈ [0.0, 1.0].

## Data Flow

1.  **Ingest**: `raw/moral_machine.csv` → `processed/scenarios.parquet`.
2.  **Compute**: `processed/scenarios.parquet` + `salience.py` → `processed/scenarios_salient.parquet`.
3.  **Detect**: `processed/scenarios.parquet` → `logs/culpability_detection.json` (FR-008).
4.  **Fit**: `processed/scenarios_salient.parquet` + `models/fit.py` → `results/model_params.json` (5-fold CV).
5.  **Simulate**: `models/simulate.py` → `results/simulation_ground_truth.json` (calibration).
6.  **Compare**: `results/model_params.json` + `analysis/compare.py` → `results/comparison_report.json`.

## aDDM Mathematical Specification

The choice-only aDDM variant uses the following drift rate equation:

$$v = w_s \times \text{salience} + \sum_{i=1}^{k} \beta_i \times \text{attribute}_i + \epsilon$$

Where:
- $w_s$ is the salience weight parameter (estimated via grid search over 0.0 to 1.0 in steps of 0.1)
- $\text{salience}$ is the computed salience score (0.0–1.0)
- $\beta_i$ are coefficients for scenario attribute covariates
- $\epsilon \sim \mathcal{N}(0, \sigma^2)$ is Gaussian noise

**Note**: This is a choice-only variant. The standard aDDM requires response time (RT) data for full parameter identifiability. The absence of RT data in the Moral Machine dataset is a known methodological limitation.

## Validation Rules

- **Salience**: Must be float. If image missing, text heuristic used (0.0–1.0).
- **Choice**: Binary (0 or 1).
- **Weights**: Sum of probabilities must equal 1.0 (if applicable).
- **Checksums**: All `processed/` files checksummed per Constitution Principle III.
- **Culpability Detection**: Log must confirm absence of explicit 'actual culpability' labels before proceeding.
- **CV Convergence**: ≥ 95% of 5-fold splits must converge within 30 minutes (SC-002).

