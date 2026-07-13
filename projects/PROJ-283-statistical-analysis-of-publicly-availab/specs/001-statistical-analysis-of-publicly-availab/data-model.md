# Data Model: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

## Entity Definitions

### 1. GameRecord
Represents a single parsed chess game with calculated features.

| Field | Type | Description | Source/Calculation |
|-------|------|-------------|--------------------|
| `game_id` | string | Unique identifier (e.g., Lichess ID) | PGN Header |
| `white_rating` | int | White player's rating | PGN Header |
| `black_rating` | int | Black player's rating | PGN Header |
| `eco_code` | string | Original ECO code (e.g., "B00") | PGN Header |
| `eco_family` | string | Collapsed opening family (e.g., "King's Pawn") | Mapping Logic (FR-011) |
| `avg_move_time_white` | float | Average time per move for White (seconds) | PGN Move Times |
| `avg_move_time_black` | float | Average time per move for Black (seconds) | PGN Move Times |
| `material_imbalance_move5` | float | Material difference at move 5 (White - Black) | PGN Board State |
| `outcome` | float | Actual result: 1.0 (Win), 0.5 (Draw), 0.0 (Loss) | PGN Result |
| `elo_expected_prob` | float | Expected win probability for White | Elo Formula (FR-003) |
| `outcome_deviation` | float | `outcome - elo_expected_prob` | Calculation (FR-004) |

**Constraints**:
- `elo_expected_prob` is capped in $[0.0001, 0.9999]$.
- `outcome_deviation` is in $[-1, 1]$.
- No nulls in `white_rating`, `black_rating`, `outcome`, `elo_expected_prob`, `outcome_deviation`.
- Games with missing `avg_move_time` are excluded.

### 2. RegressionModel
Represents the output of a fitted statistical model.

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | "gaussian_glm" or "ridge" |
| `coefficients` | dict | Map of feature name to coefficient value |
| `p_values` | dict | Map of feature name to raw p-value (from Wald Z or LRT) |
| `p_values_fdr` | dict | Map of feature name to FDR-corrected p-value |
| `r_squared` | float | Model R² score |
| `aic` | float | Akaike Information Criterion |
| `cv_scores` | list(float) | R² scores from 5-fold cross-validation |
| `significant_features` | list(string) | Features with p < 0.01 (FDR corrected) |

### 3. DiagnosticReport
Aggregated validation results.

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | Associated model type |
| `residual_plot_path` | string | Path to saved PNG |
| `predicted_vs_actual_path` | string | Path to saved PNG |
| `cv_mean_r2` | float | Mean R² across folds |
| `cv_std_r2` | float | Standard deviation of R² |
| `sensitivity_results` | dict | Map of threshold -> count of significant features |

## Data Flow

1. **Ingestion**: Raw PGN -> `GameRecord` (raw).
2. **Cleaning**: `GameRecord` (raw) -> Filtered `GameRecord` (clean).
3. **Contract Validation**: `GameRecord` (clean) -> Validated `GameRecord` (against `game_record.schema.yaml`).
4. **Feature Engineering**: `GameRecord` (clean) -> `GameRecord` (features).
5. **Modeling**: `GameRecord` (features) -> `RegressionModel`.
6. **Validation**: `RegressionModel` -> `DiagnosticReport`.