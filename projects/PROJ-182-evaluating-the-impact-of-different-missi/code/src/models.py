"""
Base data model classes for the RD missing data simulation pipeline.

These classes define the core data structures used throughout the project,
matching the schema definitions in the contracts/ directory.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class SimulationConfig:
    """Configuration for the RD data simulation.

    Attributes:
        sample_size: Number of observations to generate.
        true_effect: The true treatment effect (tau) used in data generation.
        exclusion_restriction: The coefficient for the exclusion restriction variable Z* (z_instrument).
        seed: Random seed for reproducibility.
        bandwidth_floor: Minimum bandwidth for estimation (default 0.05).
        nominal_level: Confidence level for intervals (default 0.95).
    """
    sample_size: int
    true_effect: float
    exclusion_restriction: float
    seed: int = 42
    bandwidth_floor: float = 0.05
    nominal_level: float = 0.95


@dataclass
class MissingnessPattern:
    """Represents a missingness mask and its metadata.

    Attributes:
        mask: Boolean array where True indicates missing data.
        mechanism: Type of missingness ('MCAR', 'MAR', 'MNAR').
        rate: Target missingness rate.
    """
    mask: np.ndarray
    mechanism: str
    rate: float

    def __post_init__(self):
        if not isinstance(self.mask, np.ndarray):
            self.mask = np.array(self.mask)
        if self.mask.dtype != bool:
            self.mask = self.mask.astype(bool)


@dataclass
class EstimationResult:
    """Result from a single RD estimation run.

    Attributes:
        estimator_name: Name of the estimator used (e.g., 'Naive', 'MI', 'IPW', 'Selection').
        estimate: Point estimate of the treatment effect.
        se: Standard error of the estimate.
        ci_lower: Lower bound of the confidence interval.
        ci_upper: Upper bound of the confidence interval.
        converged: Boolean indicating if the estimation converged.
        error_message: Optional error message if estimation failed.
        bandwidth: Bandwidth used for local linear regression (if applicable).
        mechanism: Missingness mechanism applied to this dataset.
        missing_rate: Actual missingness rate in the dataset.
    """
    estimator_name: str
    estimate: float
    se: float
    ci_lower: float
    ci_upper: float
    converged: bool = True
    error_message: Optional[str] = None
    bandwidth: Optional[float] = None
    mechanism: Optional[str] = None
    missing_rate: Optional[float] = None

    def __post_init__(self):
        # Handle NaN values gracefully
        if not np.isfinite(self.estimate):
            self.converged = False
            if not self.error_message:
                self.error_message = "Estimate is NaN or Inf"


@dataclass
class AggregatedMetric:
    """Aggregated metrics across multiple Monte Carlo replications.

    Attributes:
        estimator_name: Name of the estimator.
        mechanism: Missingness mechanism.
        missing_rate: Missingness rate used.
        bias: Mean difference between estimates and true effect.
        rmse: Root mean squared error.
        coverage: Proportion of confidence intervals containing the true effect.
        n_replications: Number of replications included in the aggregation.
        true_effect: The ground truth effect value used.
    """
    estimator_name: str
    mechanism: str
    missing_rate: float
    bias: float
    rmse: float
    coverage: float
    n_replications: int
    true_effect: float

    @classmethod
    def from_results(
        cls,
        results: List[EstimationResult],
        true_effect: float,
        mechanism: str,
        missing_rate: float,
        estimator_name: str
    ) -> 'AggregatedMetric':
        """Create aggregated metrics from a list of estimation results.

        Args:
            results: List of EstimationResult objects.
            true_effect: Ground truth treatment effect.
            mechanism: Missingness mechanism type.
            missing_rate: Missingness rate.
            estimator_name: Name of the estimator.

        Returns:
            AggregatedMetric instance.
        """
        if not results:
            return cls(
                estimator_name=estimator_name,
                mechanism=mechanism,
                missing_rate=missing_rate,
                bias=0.0,
                rmse=0.0,
                coverage=0.0,
                n_replications=0,
                true_effect=true_effect
            )

        estimates = [r.estimate for r in results if r.converged and np.isfinite(r.estimate)]
        ci_lowers = [r.ci_lower for r in results if r.converged and np.isfinite(r.ci_lower)]
        ci_uppers = [r.ci_upper for r in results if r.converged and np.isfinite(r.ci_upper)]

        n_valid = len(estimates)
        if n_valid == 0:
            return cls(
                estimator_name=estimator_name,
                mechanism=mechanism,
                missing_rate=missing_rate,
                bias=np.nan,
                rmse=np.nan,
                coverage=np.nan,
                n_replications=len(results),
                true_effect=true_effect
            )

        # Bias: mean(est - true)
        bias = float(np.mean(estimates) - true_effect)

        # RMSE: sqrt(mean((est - true)^2))
        rmse = float(np.sqrt(np.mean((np.array(estimates) - true_effect) ** 2)))

        # Coverage: mean(L <= true <= U)
        covered = sum(1 for l, u in zip(ci_lowers, ci_uppers) if l <= true_effect <= u)
        coverage = covered / len(ci_lowers) if ci_lowers else 0.0

        return cls(
            estimator_name=estimator_name,
            mechanism=mechanism,
            missing_rate=missing_rate,
            bias=bias,
            rmse=rmse,
            coverage=coverage,
            n_replications=n_valid,
            true_effect=true_effect
        )