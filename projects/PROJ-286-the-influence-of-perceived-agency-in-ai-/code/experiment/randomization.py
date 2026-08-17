"""
Randomization logic for the Perceived Agency experiment.

This module implements randomized assignment to experimental conditions
(High, Low, Control) with a fixed seed for reproducibility.

Requirement: FR-001 - Explicitly implement randomized assignment to ensure
independent variable manipulation.
"""

import random
from typing import List, Dict, Any, Optional

# Valid condition labels as defined in the experiment design
CONDITIONS = ["High", "Low", "Control"]


def assign_condition(seed: Optional[int] = None) -> str:
    """
    Randomly assign a participant to one of the experimental conditions.

    This function implements the core randomization logic required for
    FR-001. It uses Python's random module with an optional seed for
    reproducibility.

    Args:
        seed: Optional random seed. If None, uses system time.
              For reproducibility in tests or batch runs, provide a fixed integer.

    Returns:
        str: One of "High", "Low", or "Control"

    Example:
        >>> assign_condition(seed=42)
        'High'
    """
    if seed is not None:
        random.seed(seed)
    return random.choice(CONDITIONS)


def assign_conditions_batch(n: int, seed: Optional[int] = None) -> List[str]:
    """
    Assign multiple participants to conditions in a balanced or random manner.

    For the experiment, we use simple randomization with a fixed seed.
    The seed ensures that the same sequence of assignments is reproducible.

    Args:
        n: Number of participants to assign
        seed: Optional random seed for reproducibility

    Returns:
        List[str]: List of condition assignments in order

    Note:
        This implementation uses simple randomization. For stricter balance,
        a blocked or stratified design could be implemented, but the current
        task requires basic randomized assignment with reproducibility.
    """
    if seed is not None:
        random.seed(seed)
    return [random.choice(CONDITIONS) for _ in range(n)]


def get_randomization_state(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Get the current state of the randomization for logging purposes.

    Args:
        seed: Optional seed to initialize state

    Returns:
        Dict containing seed value and available conditions
    """
    return {
        "seed": seed,
        "conditions": CONDITIONS,
        "algorithm": "random.choice"
    }


def main():
    """
    Command-line interface for testing randomization.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Test randomization assignment for the experiment."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of assignments to generate (default: 10)"
    )

    args = parser.parse_args()

    print(f"Running randomization with seed={args.seed}, n={args.n}")
    assignments = assign_conditions_batch(args.n, seed=args.seed)

    print("\nAssignments:")
    for i, cond in enumerate(assignments, 1):
        print(f"  Participant {i}: {cond}")

    print(f"\nCondition distribution:")
    from collections import Counter
    counts = Counter(assignments)
    for cond in CONDITIONS:
        print(f"  {cond}: {counts.get(cond, 0)}")


if __name__ == "__main__":
    main()
