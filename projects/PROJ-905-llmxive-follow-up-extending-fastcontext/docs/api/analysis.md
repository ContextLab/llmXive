# Statistical Analysis API Reference

This module provides utilities for comparative analysis of exploration metrics between
"Regular" and "Irregular" repository sets. It includes statistical tests, regression analysis,
and degradation calculations.

## Functions

### `load_exploration_logs(log_path: Path) -> List[Dict[str, Any]]`

Loads exploration logs from a JSONL file.

**Parameters:**
- `log_path` (Path): Path to the `.jsonl` file.

**Returns:**
- `List[Dict[str, Any]]`: List of log entries.

### `load_scores_map(scores_path: Path) -> Dict[str, float]`

Loads regularity scores from a CSV file into a dictionary mapping repo IDs to scores.

**Parameters:**
- `scores_path` (Path): Path to the scores CSV.

**Returns:**
- `Dict[str, float]`: Mapping of `repo_id` -> `regularity_score`.

### `calculate_regression_analysis(scores: List[float], deltas: List[float]) -> Tuple[float, float]`

Performs a simple linear regression to find the relationship between regularity scores and performance deltas.

**Parameters:**
- `scores` (List[float]): List of regularity scores.
- `deltas` (List[float]): List of performance deltas (Baseline - Lite).

**Returns:**
- `Tuple[float, float]`: (slope, r_squared).

### `calc_degradation(baseline_value: float, lite_value: float) -> float`

Calculates the percentage degradation of the Lite model compared to the baseline.

**Formula:**
`((baseline - lite) / baseline) * 100`

**Parameters:**
- `baseline_value` (float): Baseline metric value.
- `lite_value` (float): Lite metric value.

**Returns:**
- `float`: Percentage degradation.

### `run_ttest(baseline_values: List[float], lite_values: List[float]) -> Tuple[float, float]`

Performs a paired statistical test (T-test or Wilcoxon) based on normality check.

**Parameters:**
- `baseline_values` (List[float]): List of baseline metrics.
- `lite_values` (List[float]): List of Lite metrics.

**Returns:**
- `Tuple[float, float]`: (statistic, p_value).
 - Uses `scipy.stats.shapiro` for normality. If p < 0.05, uses Wilcoxon signed-rank; otherwise, uses paired t-test.

### `calculate_effect_size(baseline_values: List[float], lite_values: List[float]) -> float`

Calculates Cohen's d effect size for the difference between two groups.

**Parameters:**
- `baseline_values` (List[float]): List of baseline metrics.
- `lite_values` (List[float]): List of Lite metrics.

**Returns:**
- `float`: Cohen's d value.

### `find_threshold(scores: List[float], deltas: List[float]) -> float`

Identifies a boundary threshold where performance degradation becomes significant.
Uses a sensitivity analysis approach to find the score where the trend changes.

**Parameters:**
- `scores` (List[float]): List of regularity scores.
- `deltas` (List[float]): List of performance deltas.

**Returns:**
- `float`: The identified threshold score.

### `calculate_performance_degradation_irregular(logs: List[Dict], scores_map: Dict) -> float`

Calculates the average performance degradation specifically for the "Irregular" set (low scores).

**Parameters:**
- `logs` (List[Dict]): Exploration logs.
- `scores_map` (Dict): Mapping of repo IDs to scores.

**Returns:**
- `float`: Average degradation percentage for the irregular set.

### `generate_statistical_summary(logs_path: Path, scores_path: Path) -> Dict[str, Any]`

Orchestrates the full statistical analysis pipeline and returns a summary dictionary.

**Parameters:**
- `logs_path` (Path): Path to exploration logs.
- `scores_path` (Path): Path to regularity scores.

**Returns:**
- `Dict[str, Any]`: Summary containing:
 - `p_value`: float
 - `effect_size`: dict with `cohen_d`
 - `degradation_percent`: float
 - `boundary_threshold`: float
 - `regression_slope`: float
 - `r_squared`: float

### `main()`

CLI entry point to run the full analysis and save results to `data/results/statistical_summary.json`.

**Usage:**
```bash
python -m analysis --logs data/results/exploration_logs.jsonl --scores data/processed/regularity_scores.csv
```