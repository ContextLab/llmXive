"""
Data generator utilities for simulation.
Provides functions to generate synthetic datasets for various statistical tests.
"""

import json
import os
from typing import Tuple, Union, Optional, List, Dict
import numpy as np

from code.simulation.logging_config import get_logger, log_operation
from code.simulation import get_rng

# ----------------------------------------------------------------------
# Helper / validation utilities
# ----------------------------------------------------------------------
def validate_distribution_params(dist_type: str, params: dict) -> bool:
    """
    Validate that the parameters supplied for a given distribution are
    sensible.  Returns True if validation passes, otherwise raises a
    ValueError with an explanatory message.
    """
    if dist_type == "normal":
        if "mean" not in params or "std" not in params:
            raise ValueError("Normal distribution requires 'mean' and 'std'.")
        if params["std"] <= 0:
            raise ValueError("Standard deviation must be positive.")
    elif dist_type == "multinomial":
        if "n" not in params or "p" not in params:
            raise ValueError("Multinomial distribution requires 'n' and 'p' (probability vector).")
        p = np.asarray(params["p"], dtype=float)
        if not np.isclose(p.sum(), 1):
            raise ValueError("Probability vector 'p' must sum to 1.")
        if (p < 0).any():
            raise ValueError("Probability vector 'p' cannot contain negative values.")
    elif dist_type == "contingency":
        if "rows" not in params or "cols" not in params:
            raise ValueError("Contingency table requires 'rows' and 'cols' counts.")
        if params["rows"] <= 0 or params["cols"] <= 0:
            raise ValueError("'rows' and 'cols' must be positive integers.")
    else:
        raise ValueError(f"Unsupported distribution type: {dist_type}")
    return True

# ----------------------------------------------------------------------
# Normal data generator (two‑sample)
# ----------------------------------------------------------------------
def generate_normal_data(
    mean: float,
    std: float,
    n: int,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """
    Generate a single‑sample of normally‑distributed data.
    """
    if rng is None:
        rng = get_rng()
    validate_distribution_params("normal", {"mean": mean, "std": std})
    return rng.normal(loc=mean, scale=std, size=n)

def generate_two_sample_data(
    mean1: float,
    std1: float,
    n1: int,
    mean2: float,
    std2: float,
    n2: int,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two independent normal samples for a two‑sample t‑test.
    """
    if rng is None:
        rng = get_rng()
    sample1 = generate_normal_data(mean1, std1, n1, rng)
    sample2 = generate_normal_data(mean2, std2, n2, rng)
    return sample1, sample2

# ----------------------------------------------------------------------
# Multinomial / categorical data generator (for chi‑squared)
# ----------------------------------------------------------------------
def generate_multinomial_data(
    n: int,
    p: List[float],
    size: int = 1,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """
    Generate multinomial draws.  Returns an array of shape (size, len(p)).
    """
    if rng is None:
        rng = get_rng()
    validate_distribution_params("multinomial", {"n": n, "p": p})
    return rng.multinomial(n=n, pvals=p, size=size)

# ----------------------------------------------------------------------
# Contingency table generator (for chi‑squared with expected counts)
# ----------------------------------------------------------------------
def generate_contingency_table_data(
    rows: int,
    cols: int,
    total: int,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """
    Generate a random contingency table with the specified number of rows,
    columns and total count.  The table entries are drawn from a multinomial
    distribution with a uniform probability vector.
    """
    if rng is None:
        rng = get_rng()
    validate_distribution_params(
        "contingency", {"rows": rows, "cols": cols}
    )
    prob = np.full(rows * cols, 1.0 / (rows * cols))
    flat = rng.multinomial(total, prob)
    return flat.reshape(rows, cols)

# ----------------------------------------------------------------------
# ANOVA data generator (one‑way)
# ----------------------------------------------------------------------
def generate_anova_data(
    group_means: List[float],
    std: float,
    n_per_group: int,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate data for a one‑way ANOVA.
    Returns a tuple (observations, group_labels).
    """
    if rng is None:
        rng = get_rng()
    if std <= 0:
        raise ValueError("Standard deviation must be positive.")
    groups = []
    labels = []
    for i, mu in enumerate(group_means):
        grp = rng.normal(loc=mu, scale=std, size=n_per_group)
        groups.append(grp)
        labels.append(np.full(n_per_group, i))
    observations = np.concatenate(groups)
    group_labels = np.concatenate(labels)
    return observations, group_labels
