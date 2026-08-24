import math
import os
import json
from collections import Counter
from typing import Any, Dict, List, Union, Optional
from pathlib import Path

import pandas as pd

from utils.errors import DataValidationError, fail_loudly
from utils.logging import get_logger, log_info, log_error, log_exception

logger = get_logger(__name__)


def compute_shannon_entropy(sequence: Union[str, List[str]]) -> float:
    """
    Compute Shannon entropy of a token sequence.

    Args:
        sequence: A string or list of tokens (actions/words).

    Returns:
        Normalized Shannon entropy in [0, 1].
    """
    if isinstance(sequence, str):
        # Tokenize by whitespace for simplicity; could be extended
        tokens = sequence.split()
    else:
        tokens = list(sequence)

    if not tokens:
        return 0.0

    counts = Counter(tokens)
    total = len(tokens)
    entropy = 0.0

    for count in counts.values():
        if count == 0:
            continue
        prob = count / total
        entropy -= prob * math.log2(prob)

    # Normalize by max possible entropy (log2 of unique tokens)
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    if max_entropy == 0:
        return 0.0

    return entropy / max_entropy


def _parse_intent_graph(intent_str: str) -> Dict[str, List[str]]:
    """
    Parse a semantic intent string into a dependency graph (adjacency list).

    Assumed format: "action1 -> action2, action3; action2 -> action4"
    This extracts dependencies from the ORIGINAL semantic intent, NOT generated text.

    Args:
        intent_str: The original semantic intent description.

    Returns:
        Adjacency list representing the dependency graph.
    """
    graph = {}
    if not intent_str or not isinstance(intent_str, str):
        return graph

    # Simple parser for "A -> B, C" style
    try:
        parts = intent_str.replace(";", "\n").split("\n")
        for part in parts:
            if "->" not in part:
                continue
            left, right = part.split("->", 1)
            source = left.strip()
            if not source:
                continue
            if source not in graph:
                graph[source] = []
            targets = [t.strip() for t in right.split(",")]
            for t in targets:
                if t and t not in graph[source]:
                    graph[source].append(t)
            # Ensure targets exist as keys even if they have no children
            for t in targets:
                if t and t not in graph:
                    graph[t] = []
    except Exception as e:
        log_error(f"Failed to parse intent graph: {intent_str}. Error: {e}")
        return {}

    return graph


def compute_dependency_depth(intent_str: str) -> int:
    """
    Compute the maximum dependency depth (longest path) from the ORIGINAL semantic intent.

    Constraint: MUST derive graph depth from the *original semantic intent* of the base case,
    NOT the generated text (to avoid circular correlation per FR-002/Constitution VI).

    Args:
        intent_str: The original semantic intent description string.

    Returns:
        Integer depth >= 1. Returns 1 if no dependencies found (leaf node).
    """
    if not intent_str:
        return 1

    graph = _parse_intent_graph(intent_str)
    if not graph:
        return 1

    # Memoization for longest path from each node
    memo = {}

    def dfs(node: str, visited: set) -> int:
        if node in memo:
            return memo[node]

        if node in visited:
            # Cycle detected, break it by returning 0 for this path
            return 0

        visited.add(node)
        max_child_depth = 0
        for child in graph.get(node, []):
            child_depth = dfs(child, visited)
            max_child_depth = max(max_child_depth, child_depth)

        visited.remove(node)
        depth = 1 + max_child_depth
        memo[node] = depth
        return depth

    # Find max depth starting from any root (node with no incoming edges)
    # Or simply compute max over all nodes if roots are not explicitly marked
    all_nodes = set(graph.keys())
    # Heuristic: treat nodes with no incoming edges as roots, but if ambiguous, check all
    # For simplicity and robustness, compute max depth from all nodes
    max_depth = 0
    for node in all_nodes:
        d = dfs(node, set())
        max_depth = max(max_depth, d)

    # Depth must be at least 1
    return max(1, max_depth)


def compute_complexity_score(entropy: float, depth: int) -> float:
    """
    Compute the Sequence Complexity Score.

    Formula: Complexity = Entropy * (1 + log2(Depth))
    This combines randomness (entropy) with structural depth.

    Args:
        entropy: Normalized Shannon entropy [0, 1].
        depth: Dependency depth (integer >= 1).

    Returns:
        Complexity score (float).
    """
    if depth < 1:
        raise DataValidationError(f"Depth must be >= 1, got {depth}")
    if not (0.0 <= entropy <= 1.0):
        raise DataValidationError(f"Entropy must be in [0, 1], got {entropy}")

    return entropy * (1 + math.log2(depth))


def validate_complexity_scores(df: pd.DataFrame) -> bool:
    """
    Validate the complexity scores dataframe.

    Checks:
    - Required columns exist: case_id, variant_type, entropy, depth, complexity_score
    - depth is integer >= 1
    - entropy is in [0, 1]
    - complexity_score is non-negative

    Args:
        df: The dataframe to validate.

    Returns:
        True if valid.

    Raises:
        DataValidationError: If validation fails.
    """
    required_cols = {"case_id", "variant_type", "entropy", "depth", "complexity_score"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise DataValidationError(f"Missing required columns: {missing}")

    # Check depth
    if not all(isinstance(d, (int, np.integer)) and d >= 1 for d in df["depth"]):
        raise DataValidationError("All depth values must be integers >= 1")

    # Check entropy
    if not all(0.0 <= e <= 1.0 for e in df["entropy"]):
        raise DataValidationError("All entropy values must be in [0, 1]")

    # Check complexity_score
    if not all(c >= 0 for c in df["complexity_score"]):
        raise DataValidationError("All complexity_score values must be non-negative")

    return True


def main():
    """
    Main entry point to compute complexity scores from variants.csv.

    Reads:
        data/processed/variants.csv (case_id, variant_type, entropy, intent_str)
        data/raw/wbench_metadata.json (for original semantic intent if not in variants)

    Writes:
        data/processed/complexity_scores.csv (case_id, variant_type, entropy, depth, complexity_score)
    """
    import numpy as np

    variants_path = Path("data/processed/variants.csv")
    if not variants_path.exists():
        fail_loudly(f"Input file not found: {variants_path}. Run T013 first.")

    log_info(f"Reading variants from {variants_path}")
    df = pd.read_csv(variants_path)

    # Ensure we have the original intent.
    # If 'intent_str' is not in variants, we might need to join with metadata.
    # For now, assume 'intent_str' or 'original_intent' is in the variants CSV.
    intent_col = None
    for col in ["intent_str", "original_intent", "semantic_intent"]:
        if col in df.columns:
            intent_col = col
            break

    if intent_col is None:
        # Try to load metadata if available
        metadata_path = Path("data/raw/wbench_metadata.json")
        if metadata_path.exists():
            log_info("Loading metadata for original intents...")
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            # Assume metadata is a list of dicts with 'case_id' and 'intent'
            meta_map = {str(item["case_id"]): item.get("intent", "") for item in metadata}
            df["intent_str"] = df["case_id"].astype(str).map(meta_map)
            intent_col = "intent_str"
        else:
            fail_loudly("No intent column found in variants.csv and no metadata file available.")

    log_info("Computing dependency depths from original semantic intents...")
    depths = []
    for intent in df[intent_col]:
        d = compute_dependency_depth(intent)
        depths.append(d)
    df["depth"] = depths

    log_info("Computing complexity scores...")
    scores = []
    for _, row in df.iterrows():
        try:
            score = compute_complexity_score(row["entropy"], row["depth"])
            scores.append(score)
        except DataValidationError as e:
            log_error(f"Validation error for case {row['case_id']}: {e}")
            scores.append(float('nan'))

    df["complexity_score"] = scores

    # Validate output
    try:
        validate_complexity_scores(df)
        log_info("Complexity scores validated successfully.")
    except DataValidationError as e:
        log_error(f"Validation failed: {e}")
        # Continue anyway but log warning, or fail loudly?
        # Per constraints, we should fail loudly if data is bad.
        fail_loudly(f"Output validation failed: {e}")

    output_path = Path("data/processed/complexity_scores.csv")
    log_info(f"Writing complexity scores to {output_path}")
    df[["case_id", "variant_type", "entropy", "depth", "complexity_score"]].to_csv(
        output_path, index=False
    )

    log_info("Task T015 completed successfully.")


if __name__ == "__main__":
    main()
