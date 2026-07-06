# Data Model: Resting-State Network Modularity Predicts Social Network Size

## Entity Definitions

### Subject
Represents an individual participant in the study.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | string | Unique identifier (e.g., "100307") | HCP Behavioral CSV |
| `age` | int | Age in years | HCP Behavioral CSV |
| `sex` | string | 'M' or 'F' | HCP Behavioral CSV |
| `mean_fd` | float | Mean Framewise Displacement (mm) | Derived from fMRI |
| `friends_count` | int | Number of close friends | HCP Behavioral CSV |
| `acquaintances_count` | int | Number of acquaintances | HCP Behavioral CSV |
| `social_network_size` | int | Sum of friends + acquaintances | Derived |
| `modularity_q` | float | Louvain modularity quality index | Derived from Graph |
| `total_strength` | float | Sum of absolute edge weights | Derived from Graph |
| `vif_strength` | float | Variance Inflation Factor for Total Strength | Derived (if > 5, covariate dropped) |

### Graph
Represents the functional connectivity network for a single subject.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | string | Link to Subject | Derived |
| `adjacency_matrix` | array[float] | Sparse or dense correlation matrix | Derived from fMRI |
| `community_assignments` | array[int] | Community labels per node | Louvain Algorithm |
| `modularity_q` | float | Quality index Q | Louvain Algorithm |
| `threshold` | float | Edge density threshold used | Parameter (10%-30%) |

### ModelResult
Represents the output of the statistical analysis.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `model_type` | string | e.g., "OLS", "Sensitivity_10%", "OLS_NoStrength" | Derived |
| `predictor` | string | e.g., "Modularity_Q" | Derived |
| `outcome` | string | e.g., "Social_Network_Size" | Derived |
| `coefficient` | float | Beta coefficient | Statsmodels |
| `std_error` | float | Robust standard error | Statsmodels |
| `p_value` | float | Raw p-value | Statsmodels |
| `adj_p_value` | float | Benjamini-Hochberg adjusted p-value | Derived |
| `confidence_interval` | array[float] | [lower, upper] 95% CI | Statsmodels |
| `vif` | float | VIF for covariates (if applicable) | Derived |

## Data Flow

1.  **Ingestion**: Raw fMRI (NIfTI) + Behavioral (CSV) -> `Subject` table (partial).
2.  **Preprocessing**: fMRI -> Time Series -> Correlation Matrix -> `Graph` (raw).
3.  **Graph Analysis**: Correlation Matrix (thresholded) -> `Graph` (final, with Q).
4.  **Merge**: `Subject` + `Graph` -> `Subject` (complete). *Note: The merge is a strict row-wise join on `subject_id`. If a subject_id exists in one stream but not the other, the subject is excluded and logged.*
5.  **Analysis**: `Subject` (complete) -> `ModelResult`.

## Assumptions & Constraints
- **Missing Data**: Subjects with missing behavioral data for `friends_count` or `acquaintances_count` will be excluded from the primary analysis or imputed with median values (documented in logs).
- **Motion Artifacts**: Subjects with mean FD > 0.5mm will be excluded.
- **Convergence**: If Louvain fails to converge after 3 retries, the subject is excluded.
- **Collinearity**: If VIF for `Total_Strength` > 5, the model is re-run without this covariate, and the result is reported as a sensitivity analysis.
