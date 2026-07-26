"""
Analysis Service for Semantic Divergence Diagnostic.

This module provides services for statistical analysis, specifically:
1. Pearson correlation between divergence scores and failure rates.
2. Statistical power checks (sample size validation).
3. Logistic regression training and evaluation (for future US3).
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# Third-party
from scipy import stats

# Local imports based on API surface
from src.lib import config
from src.lib.axpo_simulator import load_axpo_simulations, SimulationResult, BatchSimulationResult


class AnalysisServiceError(Exception):
    """Custom exception for analysis service errors."""
    pass


@dataclass
class CorrelationResult:
    """
    Result of a Pearson correlation test.
    """
    correlation_coefficient: float
    p_value: float
    n_samples: int
    significance_flag: bool
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisReport:
    """
    Full analysis report containing correlation results and metadata.
    """
    correlation: CorrelationResult
    dataset_info: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation": self.correlation.to_dict(),
            "dataset_info": self.dataset_info,
            "timestamp": self.timestamp
        }


def validate_sample_size(n: int, min_size: int = 30) -> None:
    """
    Validates that the sample size is sufficient for statistical power.

    Args:
        n: Number of samples.
        min_size: Minimum required sample size (default 30 per FR-010).

    Raises:
        AnalysisServiceError: If n < min_size.
    """
    if n < min_size:
        raise AnalysisServiceError(
            f"Insufficient Sample Size for Power Analysis: N={n} < {min_size}. "
            "Halting analysis as per FR-010."
        )


def calculate_pearson_correlation(
    scores: List[float],
    failure_rates: List[float]
) -> CorrelationResult:
    """
    Calculates the Pearson correlation coefficient and p-value between
    divergence scores and simulated failure rates.

    Args:
        scores: List of semantic divergence scores.
        failure_rates: List of simulated failure rates (0.0 to 1.0).

    Returns:
        CorrelationResult object.

    Raises:
        AnalysisServiceError: If lists are empty, mismatched, or constant.
    """
    if not scores or not failure_rates:
        raise AnalysisServiceError("Input lists for correlation cannot be empty.")

    if len(scores) != len(failure_rates):
        raise AnalysisServiceError(
            f"Mismatched input lengths: scores={len(scores)}, failure_rates={len(failure_rates)}"
        )

    # Validate sample size
    validate_sample_size(len(scores))

    # Convert to numpy arrays for robust handling
    x = np.array(scores)
    y = np.array(failure_rates)

    # Check for constant vectors (zero variance) which cause division by zero
    if np.std(x) == 0 or np.std(y) == 0:
        raise AnalysisServiceError(
            "Cannot calculate correlation: One of the input vectors has zero variance."
        )

    # Calculate Pearson correlation
    try:
        r, p = stats.pearsonr(x, y)
    except Exception as e:
        raise AnalysisServiceError(f"Error calculating Pearson correlation: {e}")

    # Determine significance (p < 0.05)
    significance = p < 0.05

    return CorrelationResult(
        correlation_coefficient=float(r),
        p_value=float(p),
        n_samples=len(scores),
        significance_flag=significance,
        description="Pearson correlation between Semantic Divergence Score and Simulated Failure Rate"
    )


def load_and_merge_analysis_data(
    divergence_data_path: str,
    axpo_sim_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[float], List[float]]:
    """
    Loads divergence scores and merges them with AXPO simulation failure rates.

    Args:
        divergence_data_path: Path to the JSON file containing divergence results.
        axpo_sim_path: Optional path to AXPO simulation results. If None, attempts
                       to load from default config path.

    Returns:
        Tuple of (merged_records, list_of_scores, list_of_failure_rates).

    Raises:
        AnalysisServiceError: If data cannot be loaded or merged.
    """
    # Load divergence data
    if not os.path.exists(divergence_data_path):
        raise AnalysisServiceError(f"Divergence data file not found: {divergence_data_path}")

    with open(divergence_data_path, 'r') as f:
        divergence_records = json.load(f)

    if not isinstance(divergence_records, list):
        # Handle case where data might be wrapped in an object
        if isinstance(divergence_records, dict) and 'results' in divergence_records:
            divergence_records = divergence_records['results']
        else:
            raise AnalysisServiceError("Divergence data must be a list of records.")

    # Load AXPO simulation data
    if axpo_sim_path is None:
        axpo_sim_path = config.AXPO_SIMULATION_OUTPUT_PATH

    if not os.path.exists(axpo_sim_path):
        raise AnalysisServiceError(f"AXPO simulation data file not found: {axpo_sim_path}")

    with open(axpo_sim_path, 'r') as f:
        axpo_data = json.load(f)

    # Normalize AXPO data structure based on expected schema from T007/T021
    # Expected: List of SimulationResult dicts or a dict with 'results' key
    axpo_records = []
    if isinstance(axpo_data, list):
        axpo_records = axpo_data
    elif isinstance(axpo_data, dict) and 'results' in axpo_data:
        axpo_records = axpo_data['results']
    else:
        raise AnalysisServiceError("AXPO data must be a list of results or a dict with 'results' key.")

    # Create lookup for failure rates by problem_id
    # Assuming 'problem_id' is the key in both datasets
    failure_rate_map = {}
    for record in axpo_records:
        pid = record.get('problem_id') or record.get('id')
        if pid:
            # Failure rate is 1 - success_rate, or directly provided
            if 'failure_rate' in record:
                failure_rate_map[pid] = record['failure_rate']
            elif 'success_rate' in record:
                failure_rate_map[pid] = 1.0 - record['success_rate']
            else:
                # Default to 0 if neither found, though this might indicate a schema issue
                failure_rate_map[pid] = 0.0

    # Merge data
    merged_scores = []
    merged_failures = []
    merged_records = []

    for div_record in divergence_records:
        pid = div_record.get('problem_id') or div_record.get('id')
        if not pid:
            continue

        if pid not in failure_rate_map:
            # Log warning or skip? For strict implementation, we skip if no ground truth
            continue

        score = div_record.get('semantic_divergence_score')
        if score is None:
            continue

        failure_rate = failure_rate_map[pid]

        merged_scores.append(score)
        merged_failures.append(failure_rate)
        merged_records.append({
            **div_record,
            'failure_rate': failure_rate
        })

    if len(merged_scores) == 0:
        raise AnalysisServiceError("No matching records found between divergence data and AXPO simulations.")

    return merged_records, merged_scores, merged_failures


def run_correlation_analysis(
    divergence_data_path: str,
    axpo_sim_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> AnalysisReport:
    """
    Orchestrates the full correlation analysis pipeline:
    1. Load and merge data.
    2. Validate sample size.
    3. Calculate Pearson correlation.
    4. Generate report.

    Args:
        divergence_data_path: Path to divergence JSON.
        axpo_sim_path: Path to AXPO simulation JSON.
        output_path: Optional path to write the report JSON.

    Returns:
        AnalysisReport object.
    """
    # Load and merge
    records, scores, failures = load_and_merge_analysis_data(
        divergence_data_path, axpo_sim_path
    )

    # Calculate correlation
    corr_result = calculate_pearson_correlation(scores, failures)

    # Prepare dataset info
    dataset_info = {
        "source_divergence": divergence_data_path,
        "source_axpo": axpo_sim_path or config.AXPO_SIMULATION_OUTPUT_PATH,
        "n_samples": corr_result.n_samples,
        "problem_types": list(set(r.get('problem_type', 'unknown') for r in records))
    }

    # Create report
    report = AnalysisReport(
        correlation=corr_result,
        dataset_info=dataset_info,
        timestamp=config.get_current_timestamp()
    )

    # Write to disk if path provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

    return report

def create_analysis_service() -> 'AnalysisService':
    """
    Factory function to create an AnalysisService instance.
    (Currently stateless, but provided for interface consistency).
    """
    return AnalysisService()


class AnalysisService:
    """
    Service class for analysis operations.
    Wraps the functional interface for potential future stateful operations.
    """

    def __init__(self):
        pass

    def run_correlation(
        self,
        divergence_path: str,
        axpo_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> AnalysisReport:
        return run_correlation_analysis(divergence_path, axpo_path, output_path)

    def validate_power(self, n: int) -> bool:
        try:
            validate_sample_size(n)
            return True
        except AnalysisServiceError:
            return False
