# Data Model: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

## Entity Definitions

### 1. GameRecord
Represents a single parsed chess game with engineered features.

| Field | Type | Description | Source / Calculation |
|-------|------|-------------|----------------------|
| `game_id` | string | Unique identifier (e.g., Lichess or Stockfish game hash) | PGN header or generated UUID |
| `white_rating` | integer | White player's rating (may be missing in some open datasets) | PGN header (if present) |
| `black_rating` | integer | Black player's rating (may be missing) | PGN header (if present) |
| `eco_code` | string | Original ECO code (e.g., "B00") | PGN header |
| `eco_family` | string | Collapsed opening family (e.g., "King's Pawn") | Mapping table (FR‑011) |
| `avg_move_time_white` | number | Mean time per move for White (seconds) | Mean of `move_times` list |
| `avg_move_time_black` | number | Mean time per move for Black (seconds) | Mean of `move_times` list |
| `material_imbalance_move10` | number | Material difference at move 10 (White – Black) | Piece‑value calculation after each side’s 10th move |
| `outcome` | number | Actual result (1.0 = White win, 0.5 = draw, 0.0 = loss) | PGN result tag |
| `elo_expected_prob` | number | Expected win probability for White (capped) | Elo logistic formula (FR‑003) – present only if ratings are available |
| `outcome_deviation` | number | Difference between actual and expected outcome (may be null if ratings missing) | Direct subtraction (FR‑004) |
| `time_control` | string | Time‑control category (blitz, rapid, classical) | PGN tag `TimeControl` or inferred from clock settings |

**Constraints**
- `elo_expected_prob` ∈ `[0.0001, 0.9999]` when present.
- `outcome_deviation` ∈ `[-1, 1]` when present.
- No nulls in `white_rating`, `black_rating`, `outcome`, `eco_code`, `material_imbalance_move10` **if** those columns exist in the source dataset.
- Games missing any `move_time` entry are **excluded** before schema validation (Edge Case 3).

### 2. RegressionModel
Output of a fitted statistical model.

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"beta_glm"` or `"ridge"` |
| `coefficients` | object (dict) | Feature → coefficient value |
| `p_values` | object (dict) | Feature → raw p‑value |
| `p_values_fdr` | object (dict) | Feature → FDR‑corrected p‑value |
| `r_squared` | number | Model R² (0 → 1) |
| `aic` | number | Akaike Information Criterion |
| `cv_scores` | array[number] | k‑fold CV R² scores (a modest number of items) |
| `significant_features` | array[string] | Features with `p_values_fdr < 0.01` |

### 3. DiagnosticReport
Aggregated validation artifacts.

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | Associated model (`beta_glm` / `ridge`) |
| `residual_plot_path` | string | Path to PNG file |
| `predicted_vs_actual_path` | string | Path to PNG (when outcome deviation is available) |
| `feature_importance_path` | string | Path to PNG (ridge coefficients magnitude) |
| `cv_mean_r2` | number | Mean CV R² |
| `cv_std_r2` | number | Standard deviation of CV R² |
| `sensitivity_results` | object | `{threshold: count_of_significant_features}` |

## Data Flow Diagram (Logical)

1. **Download** → Raw PGN files (`data/raw/`)  
2. **Parse** (`parse_pgn_stream`) → `GameRecord` objects (in‑memory)  
3. **Process** → Cleaned `GameRecord` DataFrame (excludes missing move times, adds ECO families, time‑control)  
4. **Validate** → Contract validation against `game_record.schema.yaml`  
5. **Model** → `RegressionModel` objects (Beta GLM & Ridge)  
6. **Validate Models** → `DiagnosticReport` (plots, CV stats, sensitivity)  
7. **Export** → CSV/JSON outputs (`data/outputs/`) validated against `model_output.schema.yaml`

All intermediate files are version‑hashed and stored under `data/` with accompanying checksum files.

---

