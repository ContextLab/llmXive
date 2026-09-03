# Data Model: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments (Methodological Validation)

## Entity Definitions

### Participant
- **Definition**: An individual user in the study (Real Data).
- **Attributes**:
  - `participant_id` (str): Unique identifier.
  - `foundation_scores` (dict): Keys: `care`, `fairness`, `loyalty`, `authority`, `purity`. Values: float (0-100).
  - `demographics` (dict): Optional. Age, gender, etc.
- **Source**: MFQ dataset.

### Vignette
- **Definition**: A moral scenario mapped to a VR scene.
- **Attributes**:
  - `story_id` (str): Unique identifier.
  - `text` (str): The moral story text.
  - `salience_level` (str): "low" or "high" (derived from `unity_blend_shapes.yaml`).
  - `blend_shape_params` (dict): Explicit Unity parameters for the expression.
- **Source**: Moral Stories dataset + `unity_blend_shapes.yaml`.

### VRInteractionLog (Simulated)
- **Definition**: Simulated interaction data for a participant-vignette pair.
- **Attributes**:
  - `participant_id` (str): FK to Participant.
  - `story_id` (str): FK to Vignette.
  - `response_time` (float): Simulated RT in seconds.
  - `gaze_metrics` (dict): Simulated gaze data (e.g., `fixation_count`, `saccade_amplitude`).
  - `judgment_rating` (float): Simulated moral judgment (1-7 scale).
  - `ground_truth_effect` (float): The known effect size used in simulation for validation.
- **Source**: `simulate_logs.py` (generated from story + salience).
- **Note**: This entity is **Synthetic**. It is not real human data.

### ModelResult
- **Definition**: Output of the Bayesian model.
- **Attributes**:
  - `model_id` (str): Identifier for the run.
  - `posterior_samples` (dict): Posterior distributions for coefficients.
  - `aic` (float): AIC score.
  - `waic` (float): WAIC score.
  - `convergence` (dict): R-hat, effective sample size.
  - `ground_truth_recovery` (dict): Bias and coverage metrics for `ground_truth_effect`.
- **Source**: `bayesian_model.py`.

### BaselineModel
- **Definition**: A model where the `salience_level` coefficient is fixed to 0.
- **Attributes**:
  - `model_id` (str): Identifier for the baseline run.
  - `aic` (float): AIC score.
  - `waic` (float): WAIC score.
- **Source**: `model_comparison.py`.

### ValidationReport
- **Definition**: Output of the validation step.
- **Attributes**:
  - `bonferroni_p_values` (dict): Interaction p-values (Bonferroni corrected).
  - `sensitivity_analysis` (list): Results for thresholds {2, 10, 20}.
  - `parameter_recovery` (dict): Bias and coverage for `ground_truth_effect`.
- **Source**: `validation.py`.

## Data Flow

1.  **Ingestion**: `fetch_real.py` downloads MFQ and Moral Stories to `data/raw/`.
2.  **Mapping**: `vr_mapping_logic.py` assigns `salience_level` and `blend_shape_params` to each story based on `unity_blend_shapes.yaml`.
3.  **Simulation**: `simulate_logs.py` generates `VRInteractionLog` for each participant-story pair, using `foundation_scores` as covariates for the simulation parameters.
4.  **Merging**: `merge_data.py` creates a unified DataFrame: `participant_id`, `story_id`, `salience_level`, `foundation_scores`, `response_time`, `gaze_metrics`, `judgment_rating`.
5.  **Analysis**: `bayesian_model.py` and `regression.py` consume the merged DataFrame.
6.  **Validation**: `validation.py` checks parameter recovery, Bonferroni, and sensitivity.

## Data Hygiene Rules

-   **Checksums**: All files in `data/raw/` are checksummed.
-   **Immutability**: Raw files are never modified. Derivations are written to `data/processed/`.
-   **PII**: No PII is stored. `participant_id` is a random UUID.
-   **Versioning**: `unity_blend_shapes.yaml` and `simulate_logs.py` parameters are versioned.
-   **Labeling**: All synthetic data files are prefixed with `simulated_` or have a `source: synthetic` flag in metadata.