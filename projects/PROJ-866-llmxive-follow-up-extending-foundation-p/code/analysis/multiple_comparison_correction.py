import numpy as np
from typing import List, Tuple, Dict, Optional, Any
import warnings


def bonferroni_correction(p_values: List[float]) -> List[float]:
    """Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of raw p-values.

    Returns:
        List of corrected p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected


def benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction.

    Args:
        p_values: List of raw p-values.

    Returns:
        List of corrected p-values (q-values).
    """
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values with original indices
    indexed_pvals = sorted(enumerate(p_values), key=lambda x: x[1])
    sorted_indices, sorted_pvals = zip(*indexed_pvals)

    # Calculate BH corrected values
    corrected = [0.0] * n
    rank = n
    min_val = 1.0

    for i in range(n - 1, -1, -1):
        idx = sorted_indices[i]
        p = sorted_pvals[i]
        q = p * n / (i + 1)
        min_val = min(min_val, q)
        corrected[idx] = min_val

    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        corrected[i] = min(corrected[i], corrected[i + 1])

    return corrected


def apply_correction(
    p_values: List[float], method: str = "bonferroni"
) -> List[float]:
    """Apply a specified multiple comparison correction method.

    Args:
        p_values: List of raw p-values.
        method: Correction method ('bonferroni' or 'benjamini_hochberg').

    Returns:
        List of corrected p-values.
    """
    if method == "bonferroni":
        return bonferroni_correction(p_values)
    elif method == "benjamini_hochberg":
        return benjamini_hochberg_correction(p_values)
    else:
        raise ValueError(f"Unknown correction method: {method}")


def calculate_fdr_threshold(
    p_values: List[float], alpha: float = 0.05
) -> Optional[float]:
    """Calculate the FDR threshold for Benjamini-Hochberg.

    Args:
        p_values: List of raw p-values.
        alpha: Desired FDR level.

    Returns:
        The threshold p-value, or None if no significant results.
    """
    n = len(p_values)
    if n == 0:
        return None

    sorted_pvals = sorted(p_values)
    for i, p in enumerate(sorted_pvals):
        if p > (i + 1) * alpha / n:
            if i == 0:
                return None
            return sorted_pvals[i - 1]
    return sorted_pvals[-1]


def main() -> None:
    """Main entry point for multiple comparison correction."""
    # This is a utility module; actual usage is via other scripts.
    print("Multiple comparison correction utilities loaded.")


if __name__ == "__main__":
    main()
