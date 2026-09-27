# Semantic Alignment Logic: GSM8K and MiniGrid

## Overview

This document defines the **Semantic Alignment** logic used to determine the validity of generated token sequences against ground-truth solutions for two distinct task types: **GSM8K** (mathematical reasoning) and **MiniGrid** (navigation/reasoning in grid worlds).

The core objective is to perform a **deterministic, token-level comparison** between the model's generated output and the canonical ground-truth paths to assign a binary validity label (`true`/`false`) to each token position.

## Ground Truth Sources

Validity labeling relies on the `data/canonical_ground_truth.jsonl` artifact, which contains:
- `prompt_id`: Unique identifier for the problem instance.
- `task_type`: Either `"gsm8k"` or `"minigrid"`.
- `canonical_solution`: The ground-truth answer string (for GSM8K).
- `valid_paths`: A list of valid shortest paths (for MiniGrid).

## Alignment Strategies by Task Type

### 1. GSM8K (Mathematical Reasoning)

**Strategy:** Exact String Matching of the Final Answer.

**Logic:**
1. **Normalization:** Both the generated sequence and the `canonical_solution` are normalized to remove leading/trailing whitespace and convert to lowercase to handle case-insensitive variations (e.g., "42" vs "42.").
2. **Extraction:** The model's generation is expected to conclude with the final answer. The alignment logic identifies the terminal segment of the generated tokens that represents the answer (typically the last few tokens).
3. **Comparison:**
 - If the normalized extracted answer **exactly matches** the normalized `canonical_solution`, the token sequence is labeled **VALID**.
 - If there is any discrepancy (numerical mismatch, missing unit, extra characters), the sequence is labeled **INVALID**.
4. **Token-Level Labeling:**
 - Tokens preceding the final answer segment are labeled based on the final outcome of the sequence.
 - If the sequence is valid, all tokens are `validity: true`.
 - If the sequence is invalid, the specific token where the divergence occurs (or the first token of the incorrect answer segment) is marked `validity: false`.

**Edge Cases:**
- **Multiple Formatting Styles:** If the ground truth is "42" and the model generates "The answer is 42", the logic must extract "42" before comparison.
- **Ambiguity:** If no ground-truth path matches after exhaustive checking, the token is marked `invalid` and a warning is logged to `logs/generation.log` (JSON format).

### 2. MiniGrid (Navigation & Goal State)

**Strategy:** Multi-Path Exact Sequence Matching.

**Logic:**
1. **Path Representation:** Ground truth is provided as `valid_paths`, a list of strings where each string represents a valid shortest path from `start_state` to `goal_state` (e.g., `["North", "East", "East", "South"]`).
2. **Iterative Matching:** For a given `prompt_id`, the generated token sequence is compared against **every** path in the `valid_paths` list.
3. **Matching Criteria:**
 - The generated sequence must **exactly match** at least one path in `valid_paths` token-for-token.
 - Case sensitivity is handled by normalizing tokens to a standard case (e.g., uppercase) before comparison.
4. **Decision Rule:**
 - **Valid:** If the generated sequence matches **ANY** of the known valid paths, the entire sequence is labeled **VALID**.
 - **Invalid:** If the generated sequence fails to match **ALL** known valid paths, it is labeled **INVALID**.
5. **Token-Level Labeling:**
 - If a match is found, all tokens in the sequence are `validity: true`.
 - If no match is found, the token at the index where the generated sequence first deviates from all known valid paths is marked `validity: false`. If the sequence is shorter than the shortest valid path, the final token is marked invalid.

## Implementation Constraints

- **No Heuristics:** Alignment must not rely on fuzzy matching or semantic similarity scores (e.g., BERTScore) for the binary validity flag. It must be deterministic.
- **Fail-Loudly:** If the `canonical_ground_truth.jsonl` is missing or malformed for a specific `prompt_id`, the process must raise an error rather than guessing.
- **Logging:** All mismatches must be logged with `prompt_id`, `reason: "no_match"`, and `validity: false` to `logs/generation.log`.

## Pseudocode Reference

```python
def label_validity(generated_tokens, ground_truth_record):
 task_type = ground_truth_record["task_type"]
 prompt_id = ground_truth_record["prompt_id"]

 if task_type == "gsm8k":
 generated_ans = extract_answer(generated_tokens)
 target_ans = normalize(ground_truth_record["canonical_solution"])
 is_valid = (normalize(generated_ans) == target_ans)

 elif task_type == "minigrid":
 valid_paths = ground_truth_record["valid_paths"]
 generated_path = normalize_tokens(generated_tokens)
 # Check against ALL known valid paths
 is_valid = any(generated_path == normalize_tokens(path) for path in valid_paths)

 else:
 raise ValueError(f"Unknown task type: {task_type}")

 if not is_valid:
 log_warning(prompt_id, "no_match")

 return assign_token_labels(generated_tokens, is_valid)
```

## Dependencies

- `data/canonical_ground_truth.jsonl` (Input)
- `logs/generation.log` (Output for warnings)
- `src/generation/generation.py` (Implementation of `label_validity`)