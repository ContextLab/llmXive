# llmXive API Documentation

This document provides the public API signatures and usage guidelines for the core modules in the llmXive automated science pipeline.

## `code/renderer.py`

The `renderer` module is responsible for converting RNG-Bench visual states into ASCII grid representations and generating structured event logs.

### Public Functions

- `validate_grid_coordinates(grid: List[List[str]], x: int, y: int) -> bool`
 Validates if coordinates are within grid bounds.

- `validate_grid_bounds(grid: List[List[str]], width: int, height: int) -> bool`
 Ensures grid dimensions match expected bounds.

- `validate_ascii_grid(grid_str: str) -> bool`
 Validates the format of an ASCII grid string.

- `render_error_block(error_type: str) -> str`
 Generates a standardized error block string (e.g., `ERROR: STATE_CORRUPT`).

- `generate_ascii_grid(seed: int, width: int, height: int) -> str`
 Generates an ASCII representation of the game state for a given seed.

- `render_visual_to_ascii(visual_path: str) -> str`
 Converts a visual frame (PNG) to its ASCII equivalent.

- `validate_grid_bounds_for_visual(visual_path: str, width: int, height: int) -> bool`
 Validates visual frame dimensions against expected grid size.

- `create_event_entry(timestep: int, state: Dict, action: str) -> Dict`
 Creates a structured event log entry for a specific timestep.

- `append_event_to_log(log_path: str, entry: Dict) -> None`
 Appends an event entry to an existing JSON log file.

- `save_event_log_to_file(log_path: str, events: List[Dict]) -> None`
 Saves a complete list of events to a JSON file.

- `load_event_log_from_file(log_path: str) -> List[Dict]`
 Loads event log data from a JSON file.

- `validate_event_log(events: List[Dict]) -> bool`
 Validates the structure and consistency of an event log.

- `generate_event_log(seed: int, steps: int) -> List[Dict]`
 Generates a full event log for a simulated run.

- `run_renderer(seeds: List[int], output_dir: str, mode: str = "ascii") -> None`
 Main entry point to run the renderer pipeline for multiple seeds.

- `main()`
 CLI entry point for the renderer module.

---

## `code/agent_loop.py`

The `agent_loop` module implements the text-only agent logic, including context management, inference, and error handling.

### Public Classes & Functions

- `class AgentConfig`
 Configuration dataclass for agent parameters (model path, context size, step limit).

- `class AgentState`
 Tracks the internal state of the agent during a run.

- `class TextAgent`
 Core agent class handling model loading, inference, and mental map updates.

- `log_discarded_run(run_id: str, reason: str, output_path: str) -> None`
 Logs a discarded run to `results/discarded_runs.csv` with the specified reason.

- `run_error_handling_test() -> None`
 Executes a test scenario to verify NaN/OOM error handling.

- `run_step_limit_test() -> None`
 Executes a test scenario to verify hard step limit enforcement.

- `main()`
 CLI entry point for running the agent loop.

---

## `code/scorer.py`

The `scorer` module calculates the "Memory Gap" metric using structured JSON comparison and semantic similarity.

### Public Functions

- `load_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer`
 Loads the pre-trained sentence transformer model for semantic similarity.

- `calculate_semantic_similarity(text1: str, text2: str, model: SentenceTransformer) -> float`
 Computes the cosine similarity between two text embeddings.

- `identify_missing_critical_items(agent_map: Dict, ground_truth: Dict) -> List[str]`
 Identifies critical items (keys, doors) present in ground truth but missing from the agent's mental map.

- `calculate_memory_gap_score(agent_output: Dict, ground_truth: Dict, model: SentenceTransformer) -> Dict`
 Calculates the final Memory Gap score using the formula:
 `score = (1 - semantic_similarity) + (1.0 * missing_items_count)`

- `run_scorer_test() -> None`
 Runs unit tests to validate scoring logic.

- `main()`
 CLI entry point for the scorer module.

---

## `code/stats.py`

The `stats` module provides statistical analysis utilities, including the Mann-Whitney U test and confidence interval calculations.

### Public Functions

- `mann_whitney_u_test(group_a: List[float], group_b: List[float], alternative: str = "less") -> Tuple[float, float]`
 Performs a one-tailed Mann-Whitney U test to compare two distributions. Returns (U statistic, p-value).

- `calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> Tuple[float, float]`
 Calculates the confidence interval for a given dataset.

- `aggregate_results(agent_scores: List[float], baseline_scores: List[float]) -> Dict`
 Aggregates results into a summary dictionary including means, stds, and test conclusions.

- `run_stats_test() -> None`
 Runs unit tests for statistical functions.

- `main()`
 CLI entry point for the stats module.