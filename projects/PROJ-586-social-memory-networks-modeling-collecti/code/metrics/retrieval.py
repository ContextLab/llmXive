from dataclasses import dataclass
from typing import Iterable, List, Tuple, Union
import numpy as np

@dataclass
class RetrievalMetrics:
    """Container for retrieval‑rate related metrics.

    Attributes
    ----------
    retrieval_rate: float
        The proportion of correctly retrieved items (0 ≤ rate ≤ 1).
    num_agents: int
        Number of agents that participated in the game.
    """
    retrieval_rate: float
    num_agents: int

# Original implementation (if any) has been replaced with a more flexible
# version that tolerates a variety of call signatures used throughout the
# codebase and test suite.
def compute_retrieval_efficiency(*args, **kwargs) -> Tuple[RetrievalMetrics, float]:
    """
    Compute retrieval efficiency in a way that is tolerant to differing
    argument orders and optional parameters.

    The function can be called with:
    - compute_retrieval_efficiency(retrieval_rate, num_agents)
    - compute_retrieval_efficiency(retrieval_rate, num_agents, baseline_agents)
    - compute_retrieval_efficiency(retrieval_rate=retrieval_rate,
                                    num_agents=num_agents)
    - Any combination of the above using *args or **kwargs.

    Parameters
    ----------
    retrieval_rate : float
        Proportion of correctly retrieved items (0‑1).
    num_agents : int
        Number of agents that contributed.
    baseline_agents : int, optional
        Baseline number of agents for the 1/N expectation. If omitted,
        ``num_agents`` is used as the baseline.

    Returns
    -------
    metrics : RetrievalMetrics
        Dataclass instance holding the raw inputs.
    efficiency : float
        Retrieval efficiency defined as ``retrieval_rate * num_agents``.
        This mirrors the original metric definition used elsewhere.
    """
    # Extract positional arguments
    if len(args) >= 2:
        retrieval_rate = args[0]
        num_agents = args[1]
        baseline_agents = args[2] if len(args) >= 3 else None
    else:
        # Fallback to keyword arguments
        retrieval_rate = kwargs.get('retrieval_rate')
        num_agents = kwargs.get('num_agents')
        baseline_agents = kwargs.get('baseline_agents')

    # Validate extracted values
    if retrieval_rate is None or num_agents is None:
        raise ValueError(
            "compute_retrieval_efficiency requires at least "
            "'retrieval_rate' and 'num_agents' arguments."
        )

    # Ensure numeric types
    try:
        retrieval_rate = float(retrieval_rate)
        num_agents = int(num_agents)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid numeric values for retrieval_rate or num_agents.") from exc

    # Optional baseline handling – the original implementation used the
    # baseline to compute a proportion against 1/N_agents.  For compatibility
    # we keep the same formula but allow the caller to omit it.
    if baseline_agents is None:
        baseline_agents = num_agents

    # Guard against division by zero
    if baseline_agents == 0:
        raise ValueError("baseline_agents must be > 0.")

    # Compute efficiency – the original metric was:
    #   efficiency = retrieval_rate / (1 / baseline_agents)
    # which simplifies to retrieval_rate * baseline_agents.
    efficiency = retrieval_rate * baseline_agents

    # Package results
    metrics = RetrievalMetrics(retrieval_rate=retrieval_rate, num_agents=num_agents)
    return metrics, efficiency
