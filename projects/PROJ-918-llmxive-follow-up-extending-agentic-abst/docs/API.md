# API Documentation: llmXive Core Modules

This document provides detailed API references for the core modules of the llmXive pipeline.

## Data Modules

### `code/data/ingest.py`

**Purpose**: Fetch and verify benchmark data

**Public API**:
```python
from data.ingest import (
 calculate_file_hash,
 load_expected_checksums,
 verify_data_integrity,
 fetch_benchmark_data,
 run_ingestion_pipeline
)
```

**Functions**:
- `calculate_file_hash(filepath: Path) -> str`: Compute SHA256 hash of a file
- `load_expected_checksums() -> Dict[str, str]`: Load expected checksums from config
- `verify_data_integrity(filepath: Path, expected_hash: str) -> bool`: Verify file integrity
- `fetch_benchmark_data(output_dir: Path) -> Path`: Download benchmark from Hugging Face
- `run_ingestion_pipeline() -> Path`: Execute full ingestion workflow

**Returns**: Path to downloaded data file

**Raises**: `RuntimeError` if data fetch fails and no fallback available

---

### `code/data/extract_features.py`

**Purpose**: Extract state features from interaction trajectories

**Public API**:
```python
from data.extract_features import (
 compute_query_context_distance,
 extract_features,
 main
)
```

**Functions**:
- `compute_query_context_distance(query: str, context: str) -> float`:
 Compute cosine distance using all-MiniLM-L6-v2
- `extract_features(dataset_path: Path, labels_path: Path) -> pd.DataFrame`:
 Parse trajectories and compute all features
- `main()`: Entry point for CLI execution

**Features Extracted**:
- `search_count`: Number of tool calls
- `error_freq`: Ratio of failed attempts
- `token_usage`: Cumulative tokens used
- `turn_number`: Interaction step index
- `embedding_distance`: Query-context semantic distance
- `abstention_label`: Ground truth label from oracle

---

### `code/data/preprocess.py`

**Purpose**: Clean and validate dataset

**Public API**:
```python
from data.preprocess import (
 load_preprocessing_config,
 calculate_missing_statistics,
 perform_mean_imputation,
 validate_dataset,
 generate_validation_report,
 main
)
```

**Functions**:
- `load_preprocessing_config() -> Dict`: Load preprocessing settings
- `calculate_missing_statistics(df: pd.DataFrame) -> Dict`: Count missing values per column
- `perform_mean_imputation(df: pd.DataFrame) -> pd.DataFrame`: Replace NaN with column means
- `validate_dataset(df: pd.DataFrame) -> bool`: Check if missing >5% critical variables
- `generate_validation_report(stats: Dict, is_valid: bool) -> Dict`: Create validation report
- `main()`: Entry point for CLI execution

**Output**:
- Cleaned DataFrame
- `data/validation_report.json`

---

## Model Modules

### `code/models/train_meta_critic.py`

**Purpose**: Train Meta-Critic classifier

**Public API**:
```python
from models.train_meta_critic import (
 load_data,
 prepare_features,
 train_model,
 evaluate_model,
 log_abstention_events,
 save_artifacts,
 main
)
```

**Functions**:
- `load_data(features_path: Path) -> Tuple[pd.DataFrame, pd.Series]`: Load features and labels
- `prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]`: Split features/labels
- `train_model(X_train, y_train) -> XGBClassifier`: Train XGBoost model
- `evaluate_model(model, X_test, y_test) -> Dict`: Calculate accuracy, precision, recall
- `log_abstention_events(model, X_test) -> List[Dict]`: Record abstention predictions
- `save_artifacts(model, metrics, abstention_logs, output_dir: Path)`: Save model and logs

**Output**:
- `models/meta_critic_model.json`
- `models/model_metrics.json`

---

### `code/oracle/solver.py`

**Purpose**: Generate ground truth abstention labels

**Public API**:
```python
from oracle.solver import (
 SearchNode,
 BoundedExhaustiveSolver,
 run_oracle_on_dataset,
 main
)
```

**Classes**:
- `SearchNode`: Represents a node in the search tree
 - Attributes: `state`, `action`, `cost`, `parent`
- `BoundedExhaustiveSolver`:
 - `__init__(max_tokens: int, max_turns: int)`
 - `solve(task: Dict) -> Tuple[bool, int]`: Returns (solved, tokens_used)

**Functions**:
- `run_oracle_on_dataset(dataset_path: Path) -> pd.DataFrame`:
 Run solver on all tasks, generate labels
- `main()`: Entry point for CLI execution

**Output**: `data/processed/labels.parquet`

---

## Simulation Modules

### `code/simulation/simulation_framework.py`

**Purpose**: Execute agent interaction simulations

**Public API**:
```python
from simulation.simulation_framework import (
 AgentSimulation,
 run_simulation_loop,
 evaluate_meta_critic_state,
 run_baseline_simulation,
 main
)
```

**Classes**:
- `AgentSimulation`:
 - `__init__(model: Optional[XGBClassifier], baseline_mode: bool)`
 - `run(task: Dict) -> Dict`: Execute simulation for a task

**Functions**:
- `run_simulation_loop(tasks: List[Dict], model: XGBClassifier) -> List[Dict]`:
 Run Meta-Critic guided simulations
- `evaluate_meta_critic_state(model, state_features) -> bool`:
 Predict abstention for given state
- `run_baseline_simulation(tasks: List[Dict]) -> List[Dict]`:
 Run full-context baseline simulations

**Output**: Simulation results with token counts, turn counts, success flags

---

## Analysis Modules

### `code/analysis/statistical_tests.py`

**Purpose**: Perform statistical significance testing

**Public API**:
```python
from analysis.statistical_tests import (
 load_simulation_results,
 perform_mann_whitney_u_test,
 perform_kolmogorov_smirnov_test,
 calculate_cohens_d,
 calculate_variance_inflation_factor,
 generate_statistical_report,
 plot_distribution_comparison
)
```

**Functions**:
- `load_simulation_results(results_path: Path) -> Dict`: Load simulation JSON
- `perform_mann_whitney_u_test(group1, group2) -> Tuple[float, float]`:
 Return (statistic, p-value)
- `perform_kolmogorov_smirnov_test(group1, group2) -> Tuple[float, float]`:
 Return (statistic, p-value)
- `calculate_cohens_d(group1, group2) -> float`: Calculate effect size
- `calculate_variance_inflation_factor(X: np.ndarray) -> Dict[str, float]`:
 Calculate VIF for each feature
- `generate_statistical_report(test_results: Dict) -> Dict`: Compile results
- `plot_distribution_comparison(group1, group2, output_path: Path)`:
 Generate histogram/KDE plot

---

### `code/analysis/survival_analysis.py`

**Purpose**: Analyze token consumption as survival data

**Public API**:
```python
from analysis.survival_analysis import (
 load_survival_data,
 perform_kaplan_meier_analysis,
 perform_logrank_test,
 perform_kolmogorov_smirnov_test,
 perform_mann_whitney_u_test,
 generate_survival_report,
 main
)
```

**Functions**:
- `load_survival_data(results_path: Path) -> pd.DataFrame`:
 Load data with event/censoring indicators
- `perform_kaplan_meier_analysis(df, event_col, time_col) -> KaplanMeierFitter`:
 Fit Kaplan-Meier estimator
- `perform_logrank_test(group1, group2) -> float`:
 Compare survival curves (returns p-value)
- `generate_survival_report(km_fit, logrank_p, output_path: Path)`:
 Create survival report

**Output**:
- `data/results/survival_analysis.json`
- `figures/survival_curves.png`

---

### `code/analysis/sensitivity_analysis.py`

**Purpose**: Evaluate decision threshold robustness

**Public API**:
```python
from analysis.sensitivity_analysis import (
 load_simulation_results,
 calculate_metrics_at_threshold,
 run_sensitivity_sweep,
 save_results,
 plot_sensitivity_curve,
 main
)
```

**Functions**:
- `calculate_metrics_at_threshold(results: List[Dict], threshold: float) -> Dict`:
 Calculate FP/FN rates at threshold
- `run_sensitivity_sweep(results: List[Dict], thresholds: List[float]) -> List[Dict]`:
 Sweep across thresholds
- `plot_sensitivity_curve(metrics: List[Dict], output_path: Path)`:
 Generate sensitivity curve plot

**Output**:
- `data/results/sensitivity_analysis.json`
- `figures/sensitivity_curve.png`

---

## Reporting Modules

### `code/analysis/generate_baseline_comparison.py`

**Purpose**: Compare Meta-Critic vs. baseline

**Public API**:
```python
from analysis.generate_baseline_comparison import (
 load_json_safe,
 calculate_token_reduction,
 calculate_effect_size,
 main
)
```

**Functions**:
- `load_json_safe(filepath: Path) -> Dict`: Load JSON with error handling
- `calculate_token_reduction(baseline_tokens, critic_tokens) -> float`:
 Calculate percentage reduction
- `calculate_effect_size(group1, group2) -> float`: Calculate Cohen's d
- `main()`: Entry point for CLI execution

**Output**: `data/results/baseline_comparison.json`

---

### `code/analysis/generate_statistical_report.py`

**Purpose**: Generate comprehensive markdown report

**Public API**:
```python
from analysis.generate_statistical_report import (
 load_json_safe,
 calculate_effect_size,
 generate_markdown_report,
 plot_results,
 main
)
```

**Functions**:
- `generate_markdown_report(results: Dict) -> str`:
 Compile all results into markdown
- `plot_results(results: Dict, output_dir: Path)`:
 Generate all required plots
- `main()`: Entry point for CLI execution

**Output**: `data/results/statistical_report.md`

---

## Configuration Module

### `code/config.py`

**Purpose**: Centralized configuration management

**Public API**:
```python
from config import (
 load_config,
 get_config,
 get_path,
 get_seed,
 get_hyperparameter,
 get_simulation_config,
 save_config
)
```

**Functions**:
- `load_config(config_path: Optional[Path] = None) -> Dict`:
 Load configuration from YAML or environment
- `get_config() -> Dict`: Get current configuration
- `get_path(key: str) -> Path`: Retrieve a path configuration
- `get_seed() -> int`: Get random seed
- `get_hyperparameter(key: str) -> Any`: Get model hyperparameter
- `get_simulation_config() -> Dict`: Get simulation settings
- `save_config(config: Dict, output_path: Path)`: Save configuration to YAML

---

## Logging Module

### `code/logging_config.py`

**Purpose**: Centralized logging setup

**Public API**:
```python
from logging_config import setup_logging
```

**Functions**:
- `setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger`:
 Configure logging for the entire pipeline

**Usage**:
```python
import logging
from logging_config import setup_logging

logger = setup_logging(level="INFO", log_file="logs/pipeline.log")
logger.info("Pipeline started")
```