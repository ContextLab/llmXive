"""
Fixed-Point Oracle for Evaluation.

Implements an immutable evaluation functional that strictly returns performance
metrics without accepting any modification to its own logic or criteria during
the recursion cycle. This addresses von Neumann's "Fixed-Point Problem" by
ensuring the evaluation criteria remain constant and cannot be patched by the
generative model.
"""
import torch
import torch.nn as nn
from typing import Dict, Any, Tuple, Optional, Callable
from pipeline.evaluator import run_all_benchmarks
from pipeline.model import get_model_param_count
from utils.memory import check_and_terminate_if_exceeds
import config


class FixedPointOracle:
    """
    An immutable evaluation functional.

    This class encapsulates the evaluation logic in a way that prevents the
    generative model from modifying the criteria or logic of evaluation.
    The evaluation function is "frozen" at instantiation and cannot be
    altered by the recursive process.
    """

    def __init__(self, benchmark_datasets: Optional[Dict[str, Any]] = None):
        """
        Initialize the oracle with the benchmark datasets.

        Args:
            benchmark_datasets: Pre-loaded datasets for GSM8K, ARC-Challenge,
                                and Wikitext-2. If None, the evaluator will
                                load them internally (with caching).
        """
        # We do NOT expose a setter for the evaluation logic.
        # The evaluation logic is defined by the methods below and cannot
        # be overridden by the generative model.
        self._benchmark_datasets = benchmark_datasets
        self._version = "1.0.0"  # Immutable version identifier

    def evaluate_cycle(
        self,
        modification: Dict[str, Any],
        model_weights: torch.Tensor,
        model_structure: nn.Module
    ) -> Dict[str, float]:
        """
        Evaluate a cycle of modification and return performance metrics.

        This is the fixed-point functional. It takes the modification proposal
        and the resulting model weights/structure, runs the evaluation, and
        returns metrics. The logic inside this function cannot be changed by
        the generative model because:
        1. The function logic is defined in this immutable class.
        2. The evaluation criteria (benchmarks) are fixed.
        3. There is no mechanism for the model to inject new logic here.

        Args:
            modification: The modification proposal dict (unused in evaluation,
                          but required for the functional signature).
            model_weights: The state_dict of the modified model.
            model_structure: The nn.Module instance of the modified model.

        Returns:
            A dictionary containing performance metrics:
            - 'GSM8K': Accuracy on GSM8K dataset
            - 'ARC': Accuracy on ARC-Challenge dataset
            - 'ECE': Expected Calibration Error on Wikitext-2
            - 'param_count': Total number of parameters
        """
        # Enforce memory limit before heavy evaluation
        ram_limit = config.get_ram_limit()
        check_and_terminate_if_exceeds(limit_gb=ram_limit)

        # Ensure the model is in eval mode
        model_structure.eval()

        # Load weights into the structure
        model_structure.load_state_dict(model_weights)

        # Run benchmarks using the fixed evaluator logic
        # We pass the model directly; the evaluator handles dataset loading
        # or uses cached data if available.
        metrics = run_all_benchmarks(model_structure, datasets=self._benchmark_datasets)

        # Add parameter count
        metrics['param_count'] = get_model_param_count(model_structure)

        return metrics

    def get_version(self) -> str:
        """Return the immutable version of this oracle."""
        return self._version


def create_immutable_oracle() -> FixedPointOracle:
    """
    Factory function to create a new Fixed-Point Oracle instance.

    This ensures that every time an oracle is needed, it is a fresh instance
    of the immutable logic, not a modified version.
    """
    return FixedPointOracle()
