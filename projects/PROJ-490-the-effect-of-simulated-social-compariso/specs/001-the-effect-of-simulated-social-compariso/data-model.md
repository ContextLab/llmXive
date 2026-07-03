# Data Model: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

## Entity Definitions

### Dataset Entity
The primary data source, either real (if found) or synthetic.
-   **Type**: Tabular (CSV/Parquet/JSON).
-   **Records**: Participants (N ≥ 100).
-   **Key Attributes**:
    -   `participant_id`: Unique string/integer.
    -   `pre_self_esteem`: Float (RSES score, 0-30 or 0-40). **Used as Covariate in ANCOVA.**
    -   `post_self_esteem`: Float (RSES score). **Outcome Variable.**
    -   `avatar_condition`: Float (0/1 for binary, or continuous intensity).
    -   `comparison_tendency`: Float (INCOM score).
    -   `missingness_flag`: Boolean (if >20% missing in key vars, row excluded).

### Regression Model Entity
The output of the primary analysis.
-   **Type**: Statistical Model Object (serialized to JSON/CSV).
-   **Attributes**:
    -   `coefficients`: Dict {var: float}. Includes `pre_self_esteem`, `avatar_condition`, `comparison_tendency`, `interaction`.
    -   `p_values`: Dict {var: float}.
    -   `confidence_intervals`: Dict {var: [lower, upper]}.
    -   `assumptions`: Dict {shapiro_p: float, breusch_pagan_p: float, vif: Dict, visual_checks: Dict}.
    -   `data_path`: String ("Real" or "Synthetic").
    -   `interpretation_framing`: String ("Empirical Association" or "Simulated Causal Effect").

### Bootstrap Stability Entity
The output of the robustness check.
-   **Type**: Aggregated Statistics.
-   **Attributes**:
 - `interaction_mean`: Float (Mean of $\beta_{interaction}$ across [deferred] iters).
    -   `interaction_ci_lower`: Float (2.5th percentile).
    -   `interaction_ci_upper`: Float (97.5th percentile).
    -   `ci_width_variance`: Float.
    -   `parameter_recovery_bias`: Float (Only for synthetic).

## Data Flow

1.  **Ingestion**:
    -   Input: Raw CSV/JSON or Synthetic Generator.
    -   Output: `data/raw/dataset.csv`.
    -   Checksum: SHA-256 recorded in `state/`.
2.  **Preprocessing**:
    -   Input: `data/raw/dataset.csv`.
    -   Process: Missingness check -> MICE (if <20%) -> Drop (>20%) -> **No change score calculation** (ANCOVA uses pre/post directly).
    -   Output: `data/processed/cleaned_data.csv`.
3.  **Analysis**:
    -   Input: `data/processed/cleaned_data.csv`.
    -   Process: ANCOVA Regression (Post ~ Pre + Condition + Comparison + Interaction) -> Assumption Checks (Visual + Stat) -> Bootstrap.
    -   Output: `data/results/regression_results.json`, `data/results/bootstrap_results.json`.
4.  **Validation**:
    -   Input: Results JSONs.
    -   Process: Validate against `contracts/` schemas.
    -   Output: Validation Pass/Fail report.

## Assumptions & Constraints
-   **Missing Data**: MICE is used only if missingness < 20% in key variables. Otherwise, rows are dropped (FR-013).
-   **Variable Types**: `avatar_condition` is treated as continuous if the dataset provides intensity; otherwise binary (0/1).
-   **Collinearity**: If VIF ≥ 5, the model output will flag "Multicollinearity Detected" and suppress independent effect claims.
-   **Framing**: All results from synthetic data are labeled "Pipeline Validation Only".
-   **Model Specification**: The primary model is **ANCOVA**, not change-score regression, to avoid mathematical coupling.