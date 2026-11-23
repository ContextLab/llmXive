# llmXive API Documentation

This document describes the public interfaces for the llmXive automated science pipeline.
All modules are located under `code/`.

## Table of Contents

1. [Generators](#generators)
2. [Policy & Execution Engines](#policy--execution-engines)
3. [Analysis Modules](#analysis-modules)
4. [Utilities](#utilities)
5. [Main Orchestrator](#main-orchestrator)

---

## Generators

### `code/generators/synthetic_workflow.py`

Generates deterministic synthetic workflow DAGs with varying depths and complexities.

**Public API:**
- `SyntheticWorkflowGenerator(seed: int, min_depth: int = 1, max_depth: int = 20, complexity_range: tuple = (1, 10))`
 - **Constructor:** Initializes the generator with a deterministic seed.
 - **Methods:**
 - `generate_workflows(count: int) -> List[Dict]`: Generates a list of workflow dictionaries.
 - `save_workflows(output_path: str) -> None`: Saves generated workflows to JSON.
- `main()`: CLI entry point for standalone execution.

**Usage:**
```python
from generators.synthetic_workflow import SyntheticWorkflowGenerator

generator = SyntheticWorkflowGenerator(seed=42)
workflows = generator.generate_workflows(500)
generator.save_workflows("data/raw/workflows.json")
```

---

## Policy & Execution Engines

### `code/engines/oracle_policy.py`

Independent rule-based validator that defines ground-truth policy validity.
Separate from execution engines to ensure unbiased ground truth.

**Public API:**
- `OraclePolicyEngine(policy_rules: Dict[str, Any])`
 - **Constructor:** Loads policy rules from a configuration dictionary.
 - **Methods:**
 - `validate_step(workflow: Dict, step: Dict, context: Dict) -> Tuple[bool, Optional[str]]`:
 Validates a single step against the full policy graph.
 Returns `(is_valid, error_message)`.
 - `validate_workflow(workflow: Dict, full_context: Dict) -> List[Dict]`:
 Validates the entire workflow and returns a list of violation logs.
- `main()`: CLI entry point.

**Key Behavior:**
- Returns `False` and a specific violation reason if a step violates data sovereignty or other hard constraints.
- Used by `FullContextEngine` to generate ground-truth execution logs.

### `code/engines/full_context.py`

Executes workflows with the full policy graph context, invoking the Oracle for validation.

**Public API:**
- `FullContextEngine(oracle_engine: OraclePolicyEngine)`
 - **Constructor:** Requires an initialized `OraclePolicyEngine`.
 - **Methods:**
 - `execute(workflow: Dict) -> Dict`:
 Executes a workflow step-by-step.
 - Invokes `oracle_engine.validate_step` for each step.
 - Records `policy-violation` flags in the execution log if validation fails.
 - Handles edge cases:
 - **Single-node graphs / depth=0**: Sets `context_reduction_pct` to `'[deferred]'` and `status` to `'edge_case'`.
 - `save_log(log: Dict, output_path: str) -> None`: Saves the execution log to JSON.
- `main()`: CLI entry point.

**Output Schema:**
- `ExecutionLog`: Contains `workflow_id`, `steps`, `violations`, `status`, `context_reduction_pct`.

### `code/engines/compressed_context.py`

Executes workflows using compressed context via BFS/DFS truncation.

**Public API:**
- `CompressedContextEngine(depth_limit: int, traversal_mode: str = 'bfs')`
 - **Constructor:** Configures the compression depth and traversal strategy.
 - `depth_limit`: Maximum depth of context to include.
 - `traversal_mode`: Either `'bfs'` or `'dfs'`.
 - **Methods:**
 - `compress_context(workflow: Dict, depth_limit: int) -> Dict`:
 Extracts the minimal policy subgraph using the specified traversal.
 - `execute(workflow: Dict, oracle_engine: OraclePolicyEngine) -> Dict`:
 Executes the workflow with the compressed context.
 - Counts actual tokens using `utils.token_counter`.
 - Logs `policy-violation` if truncation cuts off required nodes.
 - `get_token_count(context: Dict) -> int`:
 Returns the exact token count of the compressed context.
- `main()`: CLI entry point.

**Key Behavior:**
- Uses `tiktoken cl100k_base` for accurate token counting (not node count proxies).
- Handles `depth=0` gracefully (no context passed).

---

## Analysis Modules

### `code/analysis/tradeoff_model.py`

Performs statistical analysis to model the trade-off curve between context reduction and error rate.

**Public API:**
- `load_processed_logs(input_dir: str) -> List[Dict]`:
 Loads execution logs from `data/processed/`.
- `logistic_function(x: np.ndarray, L: float, k: float, x0: float) -> np.ndarray`:
 The logistic function used for curve fitting.
- `fit_tradeoff_curve(data: List[Dict]) -> Tuple[Dict, np.ndarray, np.ndarray]`:
 Fits a logistic regression model to the data.
 - Returns: `(params, x_curve, y_curve)`
- `calculate_safe_threshold(params: Dict, error_threshold: float = 0.01) -> float`:
 Identifies the maximum context reduction where error ≤ 1%.
- `generate_regression_data(data: List[Dict]) -> List[Dict]`:
 Prepares data points for the regression curve CSV.
- `run_analysis(input_dir: str, output_dir: str) -> Dict`:
 Orchestrates the full analysis pipeline.
- `main()`: CLI entry point.

**Output:**
- `data/results/tradeoff_curve.csv`: Raw regression data points.
- `data/results/threshold_ci.json`: Confidence interval for the safe threshold.

### `code/analysis/multiple_comparison_correction.py`

Implements statistical corrections for multiple comparisons (Bonferroni, Benjamini-Hochberg).

**Public API:**
- `bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]`:
 Applies Bonferroni correction to a list of p-values.
- `benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[float]`:
 Applies Benjamini-Hochberg correction to control FDR.
- `apply_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]`:
 Generic correction dispatcher.
- `calculate_fdr_threshold(p_values: List[float], alpha: float = 0.05) -> float`:
 Calculates the FDR threshold.
- `main()`: CLI entry point.

### `code/analysis/threshold_detection.py`

Detects the safe operating threshold with bootstrapped confidence intervals.

**Public API:**
- `bootstrap_threshold(data: List[Dict], n_resamples: int = 1000) -> Dict`:
 Performs bootstrapping to estimate the threshold distribution.
 - Returns: `{"mean": float, "ci_lower": float, "ci_upper": float}`
- `detect_threshold_with_correction(data: List[Dict], correction_method: str = 'bonferroni') -> Dict`:
 Combines multiple comparison correction with threshold detection.
- `main()`: CLI entry point.

### `code/analysis/generate_regression_data.py`

Utility for generating raw regression data CSVs.

**Public API:**
- `load_processed_logs(input_dir: str) -> List[Dict]`:
 Loads logs from `data/processed/`.
- `save_regression_data_to_csv(data: List[Dict], output_path: str) -> None`:
 Saves the regression curve data to a CSV file.
- `main()`: CLI entry point.

---

## Utilities

### `code/utils/token_counter.py`

Token counting using `tiktoken`.

**Public API:**
- `count_tokens_cl100k_base(text: Union[str, List[Dict]]) -> int`:
 Counts tokens in a string or a list of context dictionaries using `cl100k_base`.
- `main()`: CLI entry point.

### `code/utils/state_manager.py`

Manages project state and artifact checksums.

**Public API:**
- `compute_file_hash(file_path: str) -> str`:
 Computes SHA-256 hash of a file.
- `compute_directory_hashes(dir_path: str) -> Dict[str, str]`:
 Computes hashes for all files in a directory.
- `load_state(state_path: str) -> Dict`:
 Loads the project state YAML.
- `save_state(state: Dict, state_path: str) -> None`:
 Saves the project state YAML.
- `update_state_with_artifacts(state_path: str, artifact_paths: List[str]) -> None`:
 Updates the state file with new artifact hashes.
- `main()`: CLI entry point.

---

## Main Orchestrator

### `code/main.py`

Orchestrates the full pipeline: Generation → Full Execution → Compressed Execution → Analysis.

**Public API:**
- `ensure_directories() -> None`:
 Creates `data/raw/`, `data/processed/`, `data/results/`, `state/`.
- `generate_workflows(count: int, output_dir: str) -> List[str]`:
 Generates workflows and returns paths to saved files.
- `validate_with_oracle(workflow_paths: List[str], oracle_config: str) -> List[Dict]`:
 Validates workflows against the Oracle.
- `execute_full_context(workflow_paths: List[str], output_dir: str) -> List[str]`:
 Executes workflows with full context and saves logs.
- `execute_compressed_context(workflow_paths: List[str], output_dir: str, depth: int) -> List[str]`:
 Executes workflows with compressed context.
- `run_analysis(input_dir: str, output_dir: str) -> Dict`:
 Runs the analysis module.
- `main()`: CLI entry point with argument parsing.

**CLI Usage:**
```bash
python code/main.py --generate 500 --execute-full --execute-compressed --depth 2 --analyze
```

---

## Schema References

- **Workflow Schema:** `contracts/workflow.schema.yaml`
- **Execution Log Schema:** `contracts/execution_log.schema.yaml`
- **Analysis Results Schema:** `contracts/analysis_results.schema.yaml`