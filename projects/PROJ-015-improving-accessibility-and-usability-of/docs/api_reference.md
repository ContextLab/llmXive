# API Reference: PROJ-015 Core Modules

## `code/analysis/`

### `data_cleaner.py`
- **`DataCleaner`**: Class for cleaning raw session data.
 - `clean_sessions(raw_dir: Path) -> pd.DataFrame`: Filters incomplete sessions and applies SUS imputation.
- **`main()`**: Entry point for standalone data cleaning.

### `generate_metrics_summary.py`
- **`calculate_effect_size(df: pd.DataFrame, group_col: str) -> float`**: Computes Cohen's d for pairwise comparisons.
- **`generate_metrics_summary(df: pd.DataFrame) -> pd.DataFrame`**: Aggregates statistical test results.
- **`main()`**: Generates `metrics_summary.csv`.

### `stat_utils.py`
- **`StatUtils`**: Utility class for statistical tests.
 - `shapiro_wilk(data: np.array) -> Tuple[float, float]`: Tests normality.
 - `rm_anova(df: pd.DataFrame, metric: str) -> Dict[str, Any]`: Performs repeated measures ANOVA.
 - `holm_bonferroni(p_values: List[float]) -> List[float]`: Adjusts p-values for multiple comparisons.
- **`main()`**: Entry point for statistical analysis.

### `visualizer.py`
- **`Visualizer`**: Class for generating plots.
 - `plot_boxplot(df: pd.DataFrame, metric: str, output_path: Path)`: Creates box plots with error bars.
- **`main()`**: Generates all figures.

### `run_analysis.py`
- **`main()`**: Orchestrates the full analysis pipeline (cleaning, testing, visualization, reporting).

## `code/simulator/`

### `app.py`
- **`run_session_flow()`**: Manages the Streamlit session lifecycle.
- **`calculate_sus_score(responses: List[int]) -> float`**: Computes SUS score with imputation logic.

### `counterbalance.py`
- **`LatinSquareCounterbalancer`**: Assigns interface sequences.
 - `get_sequence(participant_id: str) -> List[str]`: Returns order (e.g., ["Traditional", "Explainable"]).

### `metrics_collector.py`
- **`MetricsCollector`**: Records interaction metrics.
 - `record_completion_time(time_ms: int)`: Logs task completion time.
 - `record_error_count(count: int)`: Logs error count.

### `session_logger.py`
- **`SessionLogger`**: Handles raw data persistence.
 - `log_session(session_data: Dict)`: Writes to `data/raw/session_{id}.json` with checksum.

### `xai_generator.py`
- **`XAIOverlayGenerator`**: Generates rule-based XAI overlays.
 - `generate_overlay(task_difficulty: int) -> Dict`: Returns heatmap opacity and explanation text.

### `xai_wrapper.py`
- **`ConfigurableXAIWrapper`**: Switches between XAI algorithms.
 - `set_algorithm(algo: str)`: Selects "rule-based", "shap", or "lime".
 - `get_overlay() -> XAIOverlay`: Returns the current XAI overlay.

## `code/utils/`

### `checksum.py`
- **`compute_file_checksum(file_path: Path) -> str`**: Computes SHA-256 hash.
- **`generate_checksum_file(file_path: Path)`:**: Creates a `.checksum` file.

### `logger.py`
- **`get_logger(name: str) -> logging.Logger`**: Configures project-wide logging.

### `seed.py`
- **`set_seed(seed: int)`:**: Initializes random seeds for reproducibility.

## `code/config/`

### `settings.py`
- **`Settings`**: Dataclass for configuration.
- **`get_settings() -> Settings`**: Loads settings from environment or defaults.

## Notes
- All modules assume `code/` is in `sys.path`.
- Data paths are relative to the project root.
- Statistical functions use `scipy.stats` and `numpy`.
