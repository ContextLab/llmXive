# Data Model: Simulated Social Comparison on Self-Esteem in VR

## Overview
This document defines the data structures used in the analysis pipeline. All data is stored in CSV/Parquet format to ensure reproducibility and compatibility with the CPU-only environment.

## Entity: Participant
Represents a single subject in the study (real or synthetic).

### Attributes
| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | `string` | Unique identifier | Unique, not null |
| `avatar_condition` | `float` | Exposure intensity to idealized avatars | Range [0.0, 1.0] |
| `comparison_tendency` | `float` | INCOM score (Social Comparison Orientation) | Range [0.0, 100.0] (or normalized) |
| `selfesteem_pre` | `float` | Rosenberg Self-Esteem Scale score (Pre) | Range [10.0, 40.0] |
| `selfesteem_post` | `float` | Rosenberg Self-Esteem Scale score (Post) | Range [10.0, 40.0] |
| `selfesteem_change` | `float` | Calculated as `post - pre` | Derived |
| `missingness_flag` | `boolean` | Indicator if record had missing values imputed | False if complete |
| `missingness_mechanism` | `string` | (Synthetic only) MCAR, MAR, or MNAR flag | Used for sensitivity analysis |

### Relationships
-   One-to-One with `RegressionResult` (aggregated).
-   One-to-Many with `BootstrapSample` (if tracking individual bootstrap samples, though usually aggregated).

## Entity: RegressionResult
Aggregated statistical output from the primary analysis.

### Attributes
| Attribute | Type | Description |
| :--- | :--- | :--- |
| `model_id` | `string` | Unique identifier for the model run |
| `coefficient_condition` | `float` | $\beta_1$ estimate |
| `pval_condition` | `float` | P-value for condition |
| `coefficient_tendency` | `float` | $\beta_2$ estimate |
| `pval_tendency` | `float` | P-value for tendency |
| `coefficient_interaction` | `float` | $\beta_3$ estimate |
| `pval_interaction` | `float` | P-value for interaction |
| `pval_interaction_corrected` | `float` | Bonferroni/Holm corrected p-value |
| `r_squared` | `float` | Model R-squared |
| `shapiro_p` | `float` | Normality test p-value |
| `breusch_pagan_p` | `float` | Homoscedasticity test p-value |
| `vif_max` | `float` | Maximum VIF among predictors |
| `power_achieved` | `float` | Post-hoc power (Real Data Path only) |
| `parameter_recovery_bias` | `float` | Bias for synthetic path (|beta_hat - beta_true|) |

## Data Flow
1.  **Raw Data**: `data/raw/synthetic_dataset.csv` (or real).
2.  **Processed Data**: `data/processed/cleaned_imputed.csv` (MICE applied, change scores computed).
3.  **Model Output**: `data/outputs/regression_results.json` (Diagnostics + Coefficients).
4.  **Bootstrap Output**: `data/outputs/bootstrap_stability.csv` (Distribution of $\beta_3$).
5.  **Sensitivity Output**: `data/outputs/sensitivity_report.json` (Missingness mechanism impact).