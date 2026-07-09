# Data Model: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

## 1. Overview
This document defines the schema for the unified dataset and the analysis output. It ensures that the pipeline adheres to FR-001 (Data Ingestion), FR-002 (Discount Rate Calculation), and FR-004 (Regression Model Construction). It explicitly supports the **Synthetic Data Generation (SDG)** strategy defined in `research.md`.

## 2. Unified Dataset Schema (`data/processed/unified_analysis.csv`)

The unified dataset contains one row per participant.

| Column Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `participant_id` | String | Unique identifier (UUID or anonymized ID). | Ingestion/Synthetic |
| `age` | Integer | Age in years. | Demographics |
| `gender` | String | Categorical (Male, Female, Other). | Demographics |
| `education` | Integer | Years of education or ordinal scale. | Demographics |
| `discount_rate_k` | Float | Derived temporal discounting rate ($k$) from hyperbolic fit. | Modeling |
| `log_k` | Float | Natural log of `discount_rate_k`. | Derived |
| `procrastination_score` | Float | Total score on the procrastination scale. | Ingestion/Synthetic |
| `wm_accuracy` | Float | Working memory accuracy (0.0 - 1.0). | Ingestion/Synthetic |
| `wm_rt` | Float | Working memory reaction time (ms). | Ingestion/Synthetic |
| `wm_load_group` | String | (Optional) Binary group (High/Low) based on median split. | Derived |
| `fit_status` | String | "Success" or "Failed" (if hyperbolic fit failed). | Modeling |
| `dgp_ground_truth` | Float | (Synthetic Only) The true interaction coefficient used in DGP generation. | DGP |

## 3. Derived Variables & Logic

### 3.1 Discount Rate ($k$)
- **Input**: Indifference points ($A, D$) from raw data or DGP.
- **Model**: $V = A / (1 + k \cdot D)$.
- **Method**: `scipy.optimize.curve_fit`.
- **Failure Handling**: If fit fails (e.g., no convergence), `fit_status` = "Failed", `discount_rate_k` = `NaN`. Participant excluded from primary analysis.

### 3.2 Interaction Term
- **Input**: `log_k` (centered), `wm_accuracy` (centered).
- **Logic**: `interaction = centered_log_k * centered_wm_accuracy`.
- **Note**: Centering is performed to reduce multicollinearity (VIF).

## 4. Output Schema (`data/processed/analysis_results.json`)

The final analysis output is a JSON file containing the model statistics and validation metrics.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_summary` | Object | OLS summary statistics (R-squared, AIC, BIC). |
| `coefficients` | Object | Map of predictor names to coefficients. |
| `p_values` | Object | Map of predictor names to p-values. |
| `interaction_p` | Float | P-value for the interaction term ($\log(k) \times WM$). |
| `interaction_significant` | Boolean | `True` if `interaction_p < 0.05`. |
| `interaction_effect_size` | Float | Estimated coefficient for the interaction term. |
| `vif_scores` | Object | VIF for each predictor. |
| `bootstrap_ci` | Object | 95% CI for interaction coefficient (Lower, Upper). |
| `dgp_recovery` | Object | (Synthetic Only) Comparison of estimated CI vs. DGP ground truth. |
| `sensitivity_analysis` | Array | List of p-values from threshold sweeps. |
| `excluded_count` | Integer | Number of participants excluded due to fit failure or missing data. |

## 5. Data Hygiene & Versioning
- **Raw Data**: Stored in `data/raw/` with checksums.
- **Processed Data**: Stored in `data/processed/`.
- **Immutability**: Raw data is never modified. All derived columns are written to new files.
- **Checksums**: SHA-256 hashes recorded in `state/projects/PROJ-196/...yaml`.