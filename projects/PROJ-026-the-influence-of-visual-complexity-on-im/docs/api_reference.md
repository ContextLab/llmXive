# API Reference

This document details the public interfaces of the `code/` package modules.

## `config.py`

**Purpose**: Centralized configuration for paths and constants.

**Public Functions**:
- `get_project_root() -> Path`: Returns the absolute path to the project root.
- `ensure_directories()`: Creates necessary directory structures (`data/raw`, `data/processed`, etc.).
- `get_data_path(sub_path: str) -> Path`: Constructs a path relative to the data directory.

## `data.models`

**Purpose**: Pydantic models for data validation.

**Classes**:
- `ImageStimulus`: `path`, `edge_density`, `entropy`, `fractal_dim`
- `ParticipantResponse`: `participant_id`, `session_id`, `reaction_time`, `is_correct`, `timestamp`
- `AggregatedScore`: `participant_id`, `session_id`, `d_score`, `n_trials_valid`, `status`

## `data.process`

**Purpose**: Data cleaning and D-score calculation.

**Public Functions**:
- `filter_trials(df: pd.DataFrame) -> pd.DataFrame`: Removes invalid trials (latency, errors).
- `calculate_d_score(df: pd.DataFrame) -> float`: Implements Greenwald D2 algorithm.
- `aggregate_d_scores(raw_logs: List[Dict]) -> List[AggregatedScore]`: Main aggregation logic.
- `save_aggregated_scores(scores: List[AggregatedScore], path: Path)`: Saves to CSV.

## `stimuli.metrics`

**Purpose**: Visual complexity quantification.

**Public Functions**:
- `calculate_edge_density(image: np.ndarray) -> float`: Uses Canny edge detection.
- `calculate_entropy(image: np.ndarray) -> float`: Shannon entropy of grayscale histogram.
- `calculate_fractal_dim(image: np.ndarray) -> float`: Box-counting dimension.

## `stimuli.process`

**Purpose**: Batch processing of stimuli.

**Public Functions**:
- `categorize_complexity(df: pd.DataFrame) -> pd.DataFrame`: Adds `complexity_category` column.
- `process_stimuli_batch(input_dir: Path, output_path: Path)`: Main batch runner.

## `analysis.permutation`

**Purpose**: Statistical inference.

**Public Functions**:
- `run_permutation_test(group_a: List[float], group_b: List[float], n_permutations: int, seed: int) -> Dict`: Returns p-value and observed statistic.
- `calculate_effect_size(group_a: List[float], group_b: List[float]) -> float`: Cohen's d.
- `run_sensitivity_analysis(df: pd.DataFrame) -> Dict`: LOIO and threshold sweep.
- `calculate_power(effect_size: float, n: int, alpha: float) -> float`: Post-hoc power.

## `viz.plot`

**Purpose**: Visualization.

**Public Functions**:
- `plot_boxplot(df: pd.DataFrame, output_path: Path)`: Seaborn boxplot with confidence intervals.
- `plot_loio_sensitivity(results: Dict, output_path: Path)`: LOIO stability plot.
- `plot_sensitivity(results: Dict, output_path: Path)`: Threshold sweep plot.

## `main`

**Purpose**: Pipeline orchestration.

**Public Functions**:
- `parse_args()`: CLI argument parser.
- `main()`: Executes the full pipeline: Load -> Process -> Analyze -> Plot.
