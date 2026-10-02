# Usage Guide: llmXive Pipeline

This guide details how to run the pipeline, interpret the results, and understand the decision boundaries.

## Running the Pipeline

The pipeline is designed to be run sequentially. Each stage produces artifacts that are consumed by the next.

### 1. Ingestion (`ingest.py`)

**Purpose**: Fetch real data from HuggingFace and parse task definitions.

**Command**:
```bash
python code/scripts/ingest.py
```

**Key Behaviors**:
- Fetches `swe-bench` and `agent-bench` subsets.
- Parses `code_diff` and `original_code`.
- **Strict Mode**: If the fetch fails, the process aborts. No synthetic data is created.

**Output**: `data/processed/ground_truth.csv`

### 2. Baseline Execution (`baseline_runner.py`)

**Purpose**: Determine the ground truth by running the code in a sandboxed environment.

**Command**:
```bash
python code/scripts/baseline_runner.py
```

**Key Behaviors**:
- Creates a temporary virtual environment for each task.
- Installs dependencies listed in the task.
- Runs the test suite with a timeout (default 600s).
- **Timeout Handling**: If a task exceeds the timeout, the outcome is recorded as "Timeout/Fail".
- **GPU Constraint**: The script checks for CUDA. If found, it raises an exception to enforce CPU-only execution.

**Output**: Updates `ground_truth.csv` with `dynamic_execution_outcome`.

### 3. Feature Extraction (`extract_features.py`)

**Purpose**: Convert code into structural metrics.

**Command**:
```bash
python code/scripts/extract_features.py
```

**Key Behaviors**:
- Filters out "Unparseable" tasks (those that failed tree-sitter parsing).
- Calculates `semantic_complexity_score` if semantic nodes are present.
- Falls back to `lines_of_code`, `cyclomatic_complexity`, and `dependency_depth` if semantic nodes are missing.
- Serializes dependency graphs to `data/graphs/{task_id}.json`.

**Output**: `data/processed/features.csv`

### 4. Model Training (`train_model.py`)

**Purpose**: Train a classifier to predict execution necessity.

**Command**:
```bash
python code/scripts/train_model.py
```

**Key Behaviors**:
- Splits data into train/validation sets (fixed seed).
- Trains Logistic Regression and Random Forest models (CPU-only).
- Performs a threshold sweep to analyze False Negative Rates (FNR).
- Flags the model as "unsafe" if the minimum achievable FNR > 0.1%.

**Output**: `models/`, `data/processed/threshold_sweep.json`, `data/processed/model_report.json`

## Interpreting Results

### Ground Truth CSV
Columns:
- `task_id`: Unique identifier.
- `code_diff`: The code change to be applied.
- `dynamic_execution_outcome`: One of "Pass", "Fail", "Timeout/Fail", or "Unparseable".

### Features CSV
Contains structural metrics for each task.
- `semantic_complexity_score`: Derived from AST node counts (optional).
- `lines_of_code`: Fallback metric.
- `cyclomatic_complexity`: Measure of control flow complexity.
- `dependency_depth`: Depth of the dependency graph.

### Model Report (`model_report.json`)
- `framing`: Set to "associational" to indicate the nature of the prediction.
- `correlation_coefficient`: Numeric value indicating feature correlation with execution necessity.
- `unsafe`: Boolean flag. `True` if FNR > 0.1%.
- `thresholds`: List of evaluated thresholds and their corresponding FNRs.

## Understanding the Decision Boundary

The pipeline identifies a threshold on the model's output probability (or score) below which a task is considered "safe" to skip dynamic execution.

- **Low FNR Requirement**: To ensure safety, the False Negative Rate (predicting "Pass" when the task actually "Fails") must be ≤ 0.1%.
- **Trade-off**: A stricter threshold (lower probability for "Pass") reduces FNR but increases False Positives (skipping fewer tasks).
- **Safety Flag**: If no threshold achieves FNR ≤ 0.1%, the model is marked "unsafe", indicating that structural features alone are insufficient to reliably predict execution outcomes for this dataset.

## Advanced Usage

### Custom Configuration
Modify environment variables or configuration files to change paths or timeouts. See `code/config/loader.py` for details.

### Parallel Execution
While the pipeline stages are sequential, individual tasks within `baseline_runner.py` and `extract_features.py` can be parallelized. Ensure your environment has sufficient resources.

### Logging
Check `data/logs/` for runtime profiles and execution logs.
