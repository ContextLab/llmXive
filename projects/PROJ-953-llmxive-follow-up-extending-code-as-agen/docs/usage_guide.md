# Usage Guide: Interpreting Results and Decision Boundaries

This guide explains how to run the pipeline, interpret the generated artifacts, and understand the decision boundary logic.

## Running the Pipeline

The pipeline is designed to be run sequentially. Each step produces artifacts required by the next.

1. **Ingestion**: `code/scripts/ingest.py`
2. **Feature Extraction**: `code/scripts/extract_features.py`
3. **Feature Finalization**: `code/scripts/generate_features.py`
4. **Model Training**: `code/scripts/train_model.py`

## Interpreting Ground Truth (`data/processed/ground_truth.csv`)

This CSV contains the foundational data for the project.

- **`task_id`**: Unique identifier for the task.
- **`code_diff`**: The code changes associated with the task.
- **`dynamic_execution_outcome`**: The result of running the task in a full environment.
 - **`Pass`**: Tests passed.
 - **`Fail`**: Tests failed.
 - **`Timeout/Fail`**: The task exceeded the time limit. *Note: These are treated as failures for safety.*
 - **`Unparseable`**: The code could not be parsed by `tree-sitter`. These rows are retained but excluded from feature extraction.

## Understanding Structural Metrics

The `features.csv` file contains calculated metrics for each task:

- **`lines_of_code`**: Basic size metric.
- **`cyclomatic_complexity`**: Measured using `radon`. Indicates branching complexity.
- **`dependency_depth`**: Depth of the import/dependency graph.
- **`semantic_complexity_score`**: A derived score based on AST node types (if available).
- **Fallback Logic**: If semantic nodes are missing, the system falls back to `lines_of_code` as a proxy, ensuring no data is lost.

## The Decision Boundary

The core output of the project is the decision boundary, found in `data/processed/threshold_sweep.json` and `data/processed/model_report.json`.

### How it Works
The model predicts the probability that a task needs dynamic execution. By setting a threshold (e.g., 0.05), we can classify tasks as "Safe to Skip" or "Need Dynamic".

### Sensitivity Analysis
The `threshold_sweep.json` file contains a sweep of thresholds and their corresponding False Negative Rates (FNR).
- **FNR**: The rate at which the model incorrectly predicts "Safe to Skip" for a task that actually needs execution.
- **Safety Constraint**: The pipeline flags the model as **unsafe** if the minimum achievable FNR is > 0.1%.

### Interpreting the Report
In `model_report.json`:
- **`framing`**: Always set to `"associational"` to reflect that the model learns correlations, not causation.
- **`unsafe`**: A boolean flag. If `true`, do not use the model for production skipping.
- **`correlation_coefficient`**: The strength of the relationship between structural features and execution necessity.

## Example Workflow

1. **Run Training**:
 ```bash
 python code/scripts/train_model.py
 ```
2. **Check Safety**:
 Open `data/processed/model_report.json`. If `"unsafe": true`, the current structural features are insufficient to safely skip dynamic execution with the required confidence.
3. **Analyze Correlations**:
 Look at the `correlation_coefficient` to understand which features are driving the predictions. High complexity tasks are more likely to need dynamic execution.

## GPU Constraints

The `baseline_runner` explicitly verifies that no GPU is used. If you see an error regarding CUDA, ensure your environment is CPU-only. This is a safety constraint to ensure reproducibility and cost control.