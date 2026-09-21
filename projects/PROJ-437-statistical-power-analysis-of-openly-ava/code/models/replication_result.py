"""Replication Result Entity Definition.

Defines the `ReplicationResult` dataclass used to store the outcome of a
single replication trial in the statistical power analysis pipeline.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReplicationResult:
    """Entity representing the outcome of a single replication test.

    Attributes:
        effect_size_est (float): The estimated effect size (e.g., Cohen's d)
            from the training or full dataset analysis.
        p_value (float): The p-value associated with the statistical test.
        replication_success (bool): True if the replication was successful
            (direction match AND magnitude within ±20% of training estimate),
            False otherwise.
        smoothing_kernel_used (float): The smoothing kernel size (in mm)
            applied during preprocessing for this result.
    """

    effect_size_est: float
    p_value: float
    replication_success: bool
    smoothing_kernel_used: float