# Semantic Alignment Logic for GSM8K and MiniGrid

## Overview
This document defines the semantic alignment logic used to match generated token sequences against ground truth paths for validity labeling in the llmXive pipeline. The logic differs between GSM8K (mathematical reasoning) and MiniGrid (navigation) tasks.

## GSM8K Alignment Logic

### Ground Truth Format
- Source: HuggingFace `gsm8k` dataset (train split)
- Format: Natural language solution string ending with a boxed answer
- Example: "The answer is \\boxed{42}"

### Matching Algorithm
1. Extract the final answer from the ground truth solution using regex: `\\boxed{([^}]+)}`
2. Parse the generated token sequence into a coherent answer string
3. Perform exact string matching between generated answer and ground truth answer
4. Validity: `True` if exact match, `False` otherwise

### Edge Cases
- Numerical equivalence: "42" matches "42.0"
- Whitespace normalization: strip leading/trailing whitespace
- Case insensitivity for non-numeric answers

## MiniGrid Alignment Logic

### Ground Truth Format
- Source: Dynamically generated via `scripts/generate_ground_truth_paths.py`
- Format: List of valid shortest paths (sequences of actions)
- Schema: `{"prompt_id": str, "task_type": "minigrid", "valid_paths": List[str], "seed": int, "map_id": str}`

### Path Generation Algorithm
1. Initialize MiniGrid environment with given `seed` and `map_id`
2. Parse start and goal positions from environment state
3. Use BFS (Breadth-First Search) to find all shortest paths from start to goal
4. Convert each path to action sequence (e.g., ["move_forward", "turn_right",...])
5. Store all valid shortest paths in `valid_paths` list

### Matching Algorithm
1. Load ground truth paths for the given `prompt_id` from `data/ground_truth_paths.jsonl`
2. Convert generated token sequence to action sequence
3. Iterate through ALL paths in `valid_paths`:
 - If generated sequence matches ANY path exactly, validity = `True`
 - Continue checking remaining paths if no match found
4. If no path matches after checking all options, validity = `False` and log warning

### Critical Requirements
- **Multi-path support**: Must check ALL valid paths, not just the first one
- **Deterministic generation**: Same seed and map_id must produce identical paths
- **Shortest path constraint**: Only shortest paths are considered valid
- **Action encoding**: Actions must be encoded consistently (e.g., "move_forward", "turn_left", "turn_right", "pickup", "drop", "toggle")

## Implementation Notes

### File Locations
- Ground truth generation script: `scripts/generate_ground_truth_paths.py`
- Ground truth data: `data/ground_truth_paths.jsonl` (generated at runtime)
- Semantic alignment logic: `src/generation/generation.py` (label_validity function)

### Error Handling
- If ground truth path file is missing: raise FileNotFoundError
- If prompt_id not found in ground truth: raise KeyError with descriptive message
- If no valid paths found for MiniGrid: log WARNING and mark as invalid

### Validation
- GSM8K: Verify answer extraction regex matches expected format
- MiniGrid: Verify path generation produces valid action sequences
- Both: Log all validity decisions to `logs/generation.log` in JSON format

## Dependencies
- MiniGrid: `minigrid` package (version compatible with HuggingFace datasets)
- BFS implementation: Standard library `collections.deque`
- Regex: Python standard library `re`

## Version History
- 1.0: Initial specification for GSM8K and MiniGrid alignment logic
