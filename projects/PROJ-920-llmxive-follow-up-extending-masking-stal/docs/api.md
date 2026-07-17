# API Documentation

This document describes the public functions and classes available in the llmXive follow-up project.
The API is organized into utility modules, trajectory generation, agent simulation, and analysis.

## Table of Contents

- [Utility Functions](#utility-functions)
 - [code/utils/entropy.py](#codeutilsentropypy)
 - [code/utils/heuristics.py](#codeutilsheuristicspy)
- [Trajectory Generation](#trajectory-generation)
 - [code/generate_trajectories.py](#codegenerate_trajectoryspy)
- [Agent Simulation](#agent-simulation)
 - [code/simulate_agent.py](#codesimulate_agentpy)
- [Analysis & Visualization](#analysis--visualization)
 - [code/analyze_results.py](#codeanalyze_resultspy)
 - [code/visualize_results.py](#codevisualize_resultspy)

---

## Utility Functions

### `code/utils/entropy.py`

Utilities for calculating Shannon entropy on text data.

#### `calculate_shannon_entropy(text: str, level: str = "byte") -> float`

Calculate the Shannon entropy of a given text string.

- **Parameters**:
 - `text` (str): The input text to analyze.
 - `level` (str): The granularity of analysis. Currently supports `"byte"` (UTF-8 byte-level tokens).
- **Returns**:
 - `float`: The calculated Shannon entropy in bits per token.
- **Raises**:
 - `ValueError`: If an unsupported `level` is provided.

---

### `code/utils/heuristics.py`

Heuristic functions for calculating composite density scores based on entropy and technical token ratios.

#### `calculate_technical_token_ratio(text: str, technical_tokens: Set[str] = None) -> float`

Calculate the ratio of technical tokens to total tokens in the text.

- **Parameters**:
 - `text` (str): The input text to analyze.
 - `technical_tokens` (Set[str], optional): A set of technical tokens to match. If None, a default set is used.
- **Returns**:
 - `float`: The ratio of technical tokens (0.0 to 1.0).

#### `calculate_composite_density(text: str) -> float`

Calculate the composite density score using the formula:
`0.6 * Shannon_Entropy + 0.4 * Technical_Token_Ratio`

- **Parameters**:
 - `text` (str): The input text to analyze.
- **Returns**:
 - `float`: The composite density score.

---

## Trajectory Generation

### `code/generate_trajectories.py`

Module for generating synthetic search trajectories with controlled semantic density and critical evidence injection.

#### `generate_text_block(density_level: str, length: int) -> str`

Generate a block of text with a specific semantic density level.

- **Parameters**:
 - `density_level` (str): The target density level ("low", "medium", or "high").
 - `length` (int): The approximate length of the text block in characters.
- **Returns**:
 - `str`: The generated text block.

#### `inject_critical_evidence(text: str, evidence: str, position: int) -> str`

Inject critical evidence into a text block at a specific position.

- **Parameters**:
 - `text` (str): The base text.
 - `evidence` (str): The critical evidence string to inject.
 - `position` (int): The index where the evidence should be inserted.
- **Returns**:
 - `str`: The modified text with evidence injected.

#### `clamp_density(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float`

Clamp a density value to a specified range to handle edge cases.

- **Parameters**:
 - `value` (float): The value to clamp.
 - `min_val` (float): The minimum allowed value.
 - `max_val` (float): The maximum allowed value.
- **Returns**:
 - `float`: The clamped value.

#### `validate_density_computation(text: str, expected_density: float, tolerance: float = 0.01) -> bool`

Validate that the computed density of a text matches the expected value within a tolerance.

- **Parameters**:
 - `text` (str): The text to validate.
 - `expected_density` (float): The expected density value.
 - `tolerance` (float): The acceptable deviation.
- **Returns**:
 - `bool`: True if the density is within tolerance, False otherwise.

#### `generate_trajectory(density_level: str, evidence_turn: int, seed: int = None) -> Dict[str, Any]`

Generate a single synthetic trajectory with controlled density and injected evidence.

- **Parameters**:
 - `density_level` (str): The target density level ("low", "medium", "high").
 - `evidence_turn` (int): The turn index where critical evidence appears.
 - `seed` (int, optional): Random seed for reproducibility.
- **Returns**:
 - `Dict[str, Any]`: A dictionary containing the trajectory data, metadata, and calculated density.

#### `main()`

Entry point for the trajectory generation script. Generates 500 trajectories and writes them to `data/raw/`.

---

## Agent Simulation

### `code/simulate_agent.py`

Module for simulating a rule-based agent processing trajectories with variable retention horizons.

#### `sigmoid(x: float) -> float`

Compute the sigmoid function: `1 / (1 + exp(-x))`.

- **Parameters**:
 - `x` (float): The input value.
- **Returns**:
 - `float`: The sigmoid of x.

#### `heuristic_solver_success(density: float, alpha: float = 5.0, threshold: float = 0.5) -> bool`

Determine if the heuristic solver succeeds based on density using a logistic function.
`P(success) = sigmoid(alpha * (density - threshold))`

- **Parameters**:
 - `density` (float): The semantic density of the trajectory.
 - `alpha` (float): Scaling factor for the logistic function.
 - `threshold` (float): Critical density threshold.
- **Returns**:
 - `bool`: True if the agent succeeds, False otherwise.

#### `check_evidence_visibility(evidence_turn: int, current_turn: int, retention_horizon: int) -> bool`

Check if critical evidence is visible given the current turn and retention horizon.

- **Parameters**:
 - `evidence_turn` (int): The turn where evidence appears.
 - `current_turn` (int): The current turn index.
 - `retention_horizon` (int): The number of turns the agent retains history.
- **Returns**:
 - `bool`: True if evidence is within the retention window, False otherwise.

#### `run_simulation(trajectory_file: str, horizon_range: List[int] = None) -> List[Dict[str, Any]]`

Run the simulation loop over a set of trajectories with varying retention horizons.

- **Parameters**:
 - `trajectory_file` (str): Path to the JSON file containing trajectories.
 - `horizon_range` (List[int], optional): List of retention horizons to test. Defaults to 1 to max_turns.
- **Returns**:
 - `List[Dict[str, Any]]`: A list of simulation results, each containing horizon, density, success status, etc.

#### `main()`

Entry point for the simulation script. Loads trajectories, runs simulations, and writes results to `data/processed/`.

---

## Analysis & Visualization

### `code/analyze_results.py`

Module for statistical analysis of simulation results using logistic regression.

#### `load_simulation_data(input_file: str) -> List[Dict[str, Any]]`

Load simulation results from a JSON file.

- **Parameters**:
 - `input_file` (str): Path to the JSON file.
- **Returns**:
 - `List[Dict[str, Any]]`: The loaded data.

#### `validate_sample_size(data: List[Dict[str, Any]], min_size: int = 30) -> bool`

Validate that the dataset meets the minimum sample size for statistical power.

- **Parameters**:
 - `data` (List[Dict[str, Any]]): The simulation results.
 - `min_size` (int): Minimum required sample size.
- **Returns**:
 - `bool`: True if sample size is sufficient, False otherwise.

#### `build_formula_with_splines(df_var: int = 3) -> str`

Build the formula string for logistic regression with natural splines.

- **Parameters**:
 - `df_var` (int): Degrees of freedom for the splines.
- **Returns**:
 - `str`: The formula string (e.g., "success ~ ns(horizon, df=3) * density").

#### `run_logistic_regression(data: List[Dict[str, Any]], formula: str) -> Dict[str, Any]`

Run logistic regression on the simulation data.

- **Parameters**:
 - `data` (List[Dict[str, Any]]): The simulation results.
 - `formula` (str): The regression formula.
- **Returns**:
 - `Dict[str, Any]`: Regression results including coefficients and p-values.

#### `write_summary(results: Dict[str, Any], output_file: str) -> None`

Write regression summary to a JSON file.

- **Parameters**:
 - `results` (Dict[str, Any]): The regression results.
 - `output_file` (str): Path to the output JSON file.

#### `write_hypothesis_summary(results: Dict[str, Any], output_file: str) -> None`

Write a human-readable hypothesis summary based on regression results.

- **Parameters**:
 - `results` (Dict[str, Any]): The regression results.
 - `output_file` (str): Path to the output text file.

#### `main()`

Entry point for the analysis script. Runs the full analysis pipeline.

---

### `code/visualize_results.py`

Module for generating 3D surface plots from regression results.

#### `load_regression_summary(input_file: str) -> Dict[str, Any]`

Load regression summary from a JSON file.

- **Parameters**:
 - `input_file` (str): Path to the JSON file.
- **Returns**:
 - `Dict[str, Any]`: The loaded summary.

#### `generate_surface_grid(data: Dict[str, Any], horizon_steps: int = 20, density_steps: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`

Generate a 3D grid of predicted success rates based on regression coefficients.

- **Parameters**:
 - `data` (Dict[str, Any]): The regression summary.
 - `horizon_steps` (int): Number of steps for the horizon axis.
 - `density_steps` (int): Number of steps for the density axis.
- **Returns**:
 - `Tuple[np.ndarray, np.ndarray, np.ndarray]`: X, Y, and Z arrays for the surface plot.

#### `plot_3d_surface(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, output_file: str) -> None`

Generate and save a 3D surface plot.

- **Parameters**:
 - `X` (np.ndarray): X-axis data (Horizon).
 - `Y` (np.ndarray): Y-axis data (Density).
 - `Z` (np.ndarray): Z-axis data (Success Rate).
 - `output_file` (str): Path to the output PNG file.

#### `main()`

Entry point for the visualization script. Generates the 3D surface plot.