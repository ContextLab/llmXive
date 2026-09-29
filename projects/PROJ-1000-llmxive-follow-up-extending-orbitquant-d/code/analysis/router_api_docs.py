"""
API Documentation and Usage Examples for code/analysis/router.py.

This file serves as a self-documenting reference for the EntropyRouter class.
It includes docstrings, usage examples, and type hints that align with the
project's implementation standards.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from config import Config

# Import the actual implementation
from analysis.router import EntropyRouter

def example_usage():
    """
    Demonstrates how to initialize and use the EntropyRouter.

    This example assumes that 'data/processed/clustering_report.json' exists.
    """
    # 1. Setup Configuration
    config = Config()
    report_path = config.data_path / "processed" / "clustering_report.json"

    # 2. Initialize the Router
    # The router loads boundaries and matrices from the clustering report.
    try:
        router = EntropyRouter(str(report_path), config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run T022b to generate the clustering report first.")
        return

    # 3. Route a Prompt Entropy Score
    # Example entropy scores (typical range depends on the dataset and model)
    test_scores = [0.1, 0.5, 1.0, 2.5]

    print(f"{'Entropy Score':<15} | {'Matrix Index':<15}")
    print("-" * 35)

    for score in test_scores:
        # Compute the matrix index
        idx = router.route(score)

        # Retrieve the actual matrix (optional, for verification)
        matrix = router.get_matrix(idx)

        print(f"{score:<15.2f} | {idx:<15}")

def api_reference():
    """
    API Reference for EntropyRouter.

    Class: EntropyRouter
    -------------------
    Maps prompt semantic entropy scores to pre-optimized rotation matrix indices.

    Constructor:
        __init__(clustering_report_path: str, config: Optional[Config] = None)
            - clustering_report_path: Path to the JSON file containing boundaries and matrices.
            - config: Optional Config instance.

    Methods:
        route(entropy_score: float) -> int
            - Input: A single float representing the semantic entropy of a prompt.
            - Output: An integer index corresponding to a rotation matrix in the report.
            - Logic:
                * If score <= min_boundary -> returns 0
                * If score >= max_boundary -> returns len(boundaries) - 1
                * Otherwise -> uses binary search (np.searchsorted) to find the interval.

        get_matrix(index: int) -> np.ndarray
            - Input: An integer index.
            - Output: The rotation matrix (numpy array) at that index.
            - Raises: IndexError if index is out of bounds.

    Configuration:
        The boundaries are extracted from the 'boundaries' key in the clustering report.
        The matrices are extracted from the 'matrices' key.
    """
    pass

if __name__ == "__main__":
    print("=== EntropyRouter Usage Example ===")
    example_usage()
    print("\n=== API Reference ===")
    print(api_reference.__doc__)