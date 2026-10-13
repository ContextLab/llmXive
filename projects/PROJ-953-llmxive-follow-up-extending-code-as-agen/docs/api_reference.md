# API Reference

This document lists the public entry points of the four core pipeline scripts.
All scripts are located under `code/scripts/` and can be executed directly
from the command line or imported as modules.

## 1. `ingest.py`

```python
# code/scripts/ingest.py

def load_swe_bench(dataset_name: str,
 split: str = 'train',
 streaming: bool = True) -> datasets.arrow_dataset.Dataset:
 """Stream the SWE‑bench dataset from HuggingFace."""

def load_agent_bench(dataset_name: str,
 split: str = 'train',
 streaming: bool = True) -> datasets.arrow_dataset.Dataset:
 """Stream the AgentBench dataset from HuggingFace."""

def parse_swe_bench(example: dict) -> dict:
 """Extract `task_id`, `code_diff`, `original_code`, and status from a SWE‑bench record."""

def parse_agent_bench(example: dict) -> dict:
 """Extract `task_id`, `code_diff`, `original_code`, and status from an AgentBench record."""

def merge_datasets(swe_bench_dataset,
 agent_bench_dataset) -> list[dict]:
 """Combine the two dataset streams into a single list of task dictionaries."""

def write_to_csv(data: list[dict], filepath: pathlib.Path) -> None:
 """Write the merged task list to a CSV file."""

def write_to_json(data: dict, filepath: pathlib.Path) -> None:
 """Write ingestion metadata (sample size, etc.) to a JSON log."""

def main() -> None:
 """CLI entry point. Handles arguments `--sample-size` and `--mode`."""
```

## 2. `baseline_runner.py`

```python
# code/scripts/baseline_runner.py

class ExecutionResult(NamedTuple):
 task_id: str
 return_code: int
 stdout: str
 stderr: str
 outcome: str # "Pass", "Fail", or "Timeout/Fail"

def check_gpu_usage() -> None:
 """Raise RuntimeError if any CUDA libraries are imported."""

def run_with_timeout(cmd: list[str],
 timeout: int,
 cwd: str | None = None,
 env: dict[str, str] | None = None) -> tuple[int, str, str]:
 """Execute a command with a strict timeout."""

def setup_venv(target_dir: pathlib.Path) -> str:
 """Create an isolated virtual environment for a task."""

def install_dependencies(venv_path: str,
 requirements_txt: pathlib.Path | None = None) -> None:
 """Install required packages into the virtual environment."""

def run_baseline_task(task: dict,
 timeout_seconds: int = 600,
 base_venv_path: str | None = None) -> ExecutionResult:
 """Execute a single task in isolation and return its result."""

def main() -> None:
 """CLI entry point. Reads `ground_truth.csv`, runs each task, and writes
 `data/processed/raw_outcomes.json`."""
```

## 3. `extract_features.py`

```python
# code/scripts/extract_features.py

def load_ground_truth(path: str) -> pandas.DataFrame:
 """Load the ground‑truth CSV produced by the ingestion stage."""

def filter_unparseable(df: pandas.DataFrame) -> pandas.DataFrame:
 """Remove rows where `status == "Unparseable"`."""

def get_lines_of_code(code: str) -> int:
 """Count non‑empty lines in a code snippet."""

def get_cyclomatic_complexity(code: str) -> int:
 """Estimate cyclomatic complexity using simple keyword heuristics."""

def get_dependency_depth(code: str) -> int:
 """Estimate the depth of the call‑graph based on indentation."""

def calculate_semantic_complexity_score(code: str) -> float | None:
 """Compute a semantic complexity score via `tree‑sitter`; returns `None`
 when semantic nodes are missing."""

def extract_graph_and_metrics(code: str) -> tuple[dict, dict]:
 """Return a mock dependency graph and a dictionary of all metrics."""

def serialize_graph(graph_data: dict, output_path: str) -> None:
 """Write a graph JSON file to `data/graphs/<task_id>.json`."""

def load_graph_metrics(graphs_dir: str) -> list[dict]:
 """Load previously serialized graph metrics (currently a placeholder)."""

def main() -> None:
 """CLI entry point. Processes `ground_truth.csv` and writes
 `features.csv` plus per‑task graph JSON files."""
```

## 4. `train_model.py`

```python
# code/scripts/train_model.py

def load_features(features_path: str) -> pandas.DataFrame:
 """Read `features.csv` and validate required columns."""

def prepare_train_val_split(df: pandas.DataFrame,
 test_size: float = 0.2) -> tuple[pandas.DataFrame, pandas.DataFrame]:
 """Stratified train/validation split with a fixed random seed."""

def encode_target(outcome: str) -> int:
 """Map execution outcomes to binary labels (0 = safe, 1 = needs dynamic)."""

def train_logistic_regression(X_train: np.ndarray,
 y_train: np.ndarray) -> sklearn.linear_model.LogisticRegression:
 """Fit a Logistic Regression model."""

def train_random_forest(X_train: np.ndarray,
 y_train: np.ndarray) -> sklearn.ensemble.RandomForestClassifier:
 """Fit a Random Forest model."""

def evaluate_model(model,
 X_val: np.ndarray,
 y_val: np.ndarray) -> dict:
 """Compute F1, recall, and false‑negative rate on the validation set."""

def calculate_correlation_coefficient(df: pandas.DataFrame,
 feature_cols: list[str],
 target_col: str) -> dict:
 """Pearson correlation between each structural feature and the binary target."""

def run_sensitivity_analysis(model,
 X_val: np.ndarray,
 y_val: np.ndarray) -> dict:
 """Sweep decision thresholds, record FNR, and determine safety flag."""

def run_training_pipeline(features_path: str,
 output_dir: str) -> dict:
 """End‑to‑end training: load data, train both models, run analysis,
 and write artifacts (`*.pkl`, `threshold_sweep.json`, `model_report.json`)."""

def main() -> None:
 """CLI wrapper. Parses `--features` and `--output` arguments and launches
 the training pipeline."""
```