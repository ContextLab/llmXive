# Data Model: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

## Entity Definitions

### 1. AlloyComposition
Represents a single metallic glass formulation.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition_id` | string | Unique identifier (hash of composition string). | Generated |
| `elements` | object | Dictionary of element symbol to atomic fraction. | Dataset / Gen |
| `atomic_radius_mean` | float | Weighted mean atomic radius (Å). | Feature Eng |
| `electronegativity_var` | float | Variance of electronegativity. | Feature Eng |
| `vec_mean` | float | Weighted mean Valence Electron Concentration. | Feature Eng |
| `vec_raw` | float | Sum of weighted Valence Electron Counts (aggregate). | Feature Eng |
| `size_mismatch` | float | Atomic size mismatch parameter ($\delta$). | Feature Eng |
| `pairwise_mismatch` | float | Sum of absolute differences for all unique pairs. | Feature Eng |
| `triplet_interaction` | float | Variance of radii among the three elements. | Feature Eng |
| `log_rc_target` | float | Target variable: $log_{10}(R_c)$ (K s$^{-1}$). | Dataset |
| `family_cluster` | string | Primary metallic element family (e.g., "Zr-based"). | Derived |

### 2. ModelPrediction
Output of the screening phase for a candidate composition.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition_string` | string | String representation (e.g., "Zr50Cu30Al20"). | Generated |
| `predicted_mean` | float | Predicted $log_{10}(R_c)$ mean. | Model |
| `confidence_lower` | float | 2.5th percentile of bootstrapped + conformal predictions. | Bootstrap/Conformal |
| `confidence_upper` | float | 97.5th percentile of bootstrapped + conformal predictions. | Bootstrap/Conformal |
| `conservative_score` | float | `predicted_mean` - 1.645 * (`upper` - `lower`). | Derived |
| `do_a_status` | string | "in_do_a" or "high_extrapolation_risk". | Conformal/Mahalobis |
| `novelty` | boolean | `true` if not in training set or Materials Project. | Novelty Check |
| `ranking` | integer | Rank in the sorted list of candidates. | Post-Proc |

### 3. VerificationRequest
Artifact generated for experimental validation (FR-008).

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `candidate_id` | string | Reference to the composition. | Generated |
| `composition` | string | The alloy formula. | Generated |
| `predicted_rc` | float | Predicted critical cooling rate ($10^{log\_rc}$). | Model |
| `status` | string | Always "pending_verification". | Hardcoded |
| `risk_flag` | string | "low" or "high". | DoA |

## Data Flow

1.  **Raw Ingestion**: `data/raw/GFA_D2.csv` $\rightarrow$ `data/processed/engineered_features.csv`
    -   *Transformation*: Element parsing, descriptor calculation (incl. pairwise/triplet), missing value handling, schema check for `critical_cooling_rate`.
2.  **Model Training**: `data/processed/engineered_features.csv` $\rightarrow$ `output/best_model.pkl`
    -   *Transformation*: Scaling, LOCO split, hyperparameter tuning, validation, heteroscedasticity check & retraining.
3.  **Screening**: `output/best_model.pkl` + `elements_list` $\rightarrow$ `output/top_candidates.csv`
    -   *Transformation*: Combinatorial generation, prediction, novelty check, DoA check, conservative scoring, filtering.
4.  **Analysis**: `output/best_model.pkl` $\rightarrow$ `output/shap_summary.png`
    -   *Transformation*: SHAP value calculation.
5.  **Verification**: `output/top_candidates.csv` $\rightarrow$ `output/verification_requests.json`
    -   *Transformation*: Format conversion, status assignment.

## Constraints & Validation Rules

-   **Fraction Sum**: $\sum c_i \in [0.99, 1.01]$. If outside, normalize to 1.0.
-   **Target Range**: $log_{10}(R_c)$ must be finite and non-negative.
-   **Unknown Elements**: Rows with elements not in Pymatgen are dropped.
-   **Threshold**: Only candidates with `upper_bound` <= `threshold` (10th percentile of training set, fallback 25th) are included in the primary ranking.
-   **Uncertainty**: Candidates with `high_extrapolation_risk` are excluded from the top 10.