# llmXive API Reference

This document describes the public interfaces for the llmXive automated science pipeline.
All functions listed here are intended for external consumption by the pipeline orchestrator
or other modules. Internal helper functions are not documented unless explicitly exported.

## Utility Functions (`code/utils/`)

### `entropy.py`

Utilities for calculating Shannon entropy on text data.

#### `calculate_shannon_entropy(text: Union[str, bytes]) -> float`
Calculates the Shannon entropy of the input text.

- **Parameters**:
 - `text`: Input string or bytes. If string, it is encoded to UTF-8 bytes.
- **Returns**:
 - `float`: The entropy value in bits.
- **Notes**:
 - Calculates entropy at the byte level for UTF-8 encoded text.
 - Returns 0.0 if the input is empty or contains only a single unique byte.

#### `clamp_entropy(entropy_value: float, min_val: float = 0.0, max_val: float = 8.0) -> float`
Clamps an entropy value to a specific range to prevent numerical instability.

- **Parameters**:
 - `entropy_value`: The raw entropy value.
 - `min_val`: Minimum allowed value (default 0.0).
 - `max_val`: Maximum allowed value (default 8.0, max for byte-level entropy).
- **Returns**:
 - `float`: The clamped entropy value.

#### `entropy_per_token(text: str, min_tokens: int = 1) -> float`
Calculates entropy normalized per token (or per byte if tokens are not defined).

- **Parameters**:
 - `text`: Input text string.
 - `min_tokens`: Minimum number of tokens to avoid division by zero.
- **Returns**:
 - `float`: Entropy per token.

---

### `heuristics.py`

Heuristic functions for calculating semantic density and technical token ratios.

#### `calculate_technical_token_ratio(text: str, technical_tokens: List[str] = None) -> float`
Calculates the ratio of technical tokens to total tokens in the text.

- **Parameters**:
 - `text`: Input text string.
 - `technical_tokens`: Optional list of technical tokens. If None, uses the default domain-specific list:
 `['search_context', 'retrieval_window', 'semantic_density', 'agent_state', 'trajectory_log',
 'masking_policy', 'evidence_turn', 'focus_decay', 'stale_observation', 'retention_limit',
 'critical_evidence', 'heuristic_solver', 'logistic_function', 'regime_map']`.
- **Returns**:
 - `float`: Ratio of technical tokens (0.0 to 1.0).

#### `calculate_composite_density(text: str, alpha: float = 0.5, beta: float = 0.5) -> float`
Calculates the composite density score using Shannon entropy and technical token ratio.

- **Formula**: `alpha * Shannon_Entropy + beta * Technical_Token_Ratio`
- **Parameters**:
 - `text`: Input text string.
 - `alpha`: Weight for entropy component (default 0.5).
 - `beta`: Weight for technical token ratio component (default 0.5).
- **Returns**:
 - `float`: Composite density score.

---

## Trajectory Generation (`code/generate_trajectories.py`)

Functions for generating synthetic search trajectories with controlled semantic density.

#### `generate_text_block(length: int, density_level: str) -> str`
Generates a text block with a specific semantic density level.

- **Parameters**:
 - `length`: Desired length of the text block.
 - `density_level`: One of 'low', 'medium', 'high'.
- **Returns**:
 - `str`: Generated text block.

#### `inject_critical_evidence(text: str, evidence_index: int) -> str`
Injects a critical evidence marker into the text at a specific index.

- **Parameters**:
 - `text`: Base text string.
 - `evidence_index`: Index where evidence should be injected.
- **Returns**:
 - `str`: Text with injected evidence.

#### `clamp_density(density: float, min_density: float = 0.0, max_density: float = 1.0) -> float`
Clamps density values to a valid range.

- **Parameters**:
 - `density`: Raw density value.
 - `min_density`: Minimum allowed density.
 - `max_density`: Maximum allowed density.
- **Returns**:
 - `float`: Clamped density value.

#### `validate_density_computation(text: str, expected_density: float, tolerance: float = 0.01) -> bool`
Validates that the computed density of text matches the expected value within tolerance.

- **Parameters**:
 - `text`: Text to validate.
 - `expected_density`: Expected density value.
 - `tolerance`: Acceptable deviation (default 0.01).
- **Returns**:
 - `bool`: True if validation passes.

#### `generate_trajectory(seed: int, density_level: str, evidence_turn: int) -> Dict[str, Any]`
Generates a complete trajectory with controlled density and evidence injection.

- **Parameters**:
 - `seed`: Random seed for reproducibility.
 - `density_level`: Target density level ('low', 'medium', 'high').
 - `evidence_turn`: Turn index where critical evidence appears.
- **Returns**:
 - `Dict[str, Any]`: Trajectory object containing text, metadata, and calculated density.

#### `main()`
Entry point for the trajectory generation script.

- **Functionality**:
 - Parses command-line arguments.
 - Generates 500 trajectories with controlled density.
 - Writes output to `data/raw/trajectories.json`.

---

## Agent Simulation (`code/simulate_agent.py`)

Functions for simulating agent behavior with variable retention horizons.

#### `sigmoid(x: float) -> float`
Computes the sigmoid function: `1 / (1 + exp(-x))`.

- **Parameters**:
 - `x`: Input value.
- **Returns**:
 - `float`: Sigmoid of x.

#### `heuristic_solver_success(density: float, alpha: float, threshold: float) -> bool`
Determines if the heuristic solver succeeds based on density and parameters.

- **Formula**: `P(retrieval) = sigmoid(alpha * (density - threshold))`
- **Parameters**:
 - `density`: Semantic density of the trajectory.
 - `alpha`: Scaling parameter for the logistic function.
 - `threshold`: Critical density threshold.
- **Returns**:
 - `bool`: True if the solver succeeds (sampled from probability).

#### `check_evidence_visibility(critical_turn: int, current_turn: int, retention_horizon: int) -> bool`
Checks if critical evidence is visible given the current turn and retention horizon.

- **Logic**: Returns True if `critical_turn >= current_turn - retention_horizon + 1`.
- **Parameters**:
 - `critical_turn`: Turn index of critical evidence.
 - `current_turn`: Current simulation turn.
 - `retention_horizon`: Number of turns to retain.
- **Returns**:
 - `bool`: True if evidence is visible.

#### `load_trajectories_streaming(input_path: str, batch_size: int = 100)`
Generator that loads trajectories from a JSON file in batches.

- **Parameters**:
 - `input_path`: Path to the trajectories JSON file.
 - `batch_size`: Number of trajectories per batch.
- **Yields**:
 - `List[Dict]`: Batches of trajectory data.

#### `run_simulation_batch(traj_batch: List[Dict], alpha: float, threshold: float, horizon_range: List[int]) -> List[Dict]`
Runs simulation for a batch of trajectories across multiple horizons.

- **Parameters**:
 - `traj_batch`: List of trajectory dictionaries.
 - `alpha`: Scaling parameter for heuristic solver.
 - `threshold`: Density threshold for heuristic solver.
 - `horizon_range`: List of retention horizons to test.
- **Returns**:
 - `List[Dict]`: Simulation results with success/failure outcomes.

#### `write_batch_to_file(results: List[Dict], output_path: str)`
Writes a batch of simulation results to a JSON file.

- **Parameters**:
 - `results`: List of result dictionaries.
 - `output_path`: Path to output file.

#### `get_memory_usage_gb() -> float`
Reports current memory usage in gigabytes.

- **Returns**:
 - `float`: Memory usage in GB.

#### `main()`
Entry point for the agent simulation script.

- **Functionality**:
 - Parses command-line arguments (alpha, threshold, horizon range).
 - Loads trajectories in streaming batches.
 - Runs simulation and writes results to `data/processed/simulation_results.json`.
 - Monitors memory usage.