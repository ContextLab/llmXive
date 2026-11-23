"""
Metrics computation module for consensus gap closure analysis.

This module computes the consensus gap closure metric for every trajectory
found in the experiment logs, comparing the Adapter condition against the
Static baseline.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models.entities import ConflictTrajectory, SocioCognitiveStateType
from models.evaluator import ConsensusGapEvaluator, calculate_consensus_gap_scores
from config import ensure_directories

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryGapMetrics:
    """Container for gap metrics computed for a single trajectory."""
    trajectory_id: str
    condition: str  # 'Adapter' or 'Static'
    initial_gap: float
    final_gap: float
    gap_closure: float
    gap_closure_percent: float
    is_improved: bool

def load_experiment_logs(logs_path: Path) -> List[Dict[str, Any]]:
    """
    Load experiment logs from JSON file.

    Args:
        logs_path: Path to the experiment_logs.json file

    Returns:
        List of log entries

    Raises:
        FileNotFoundError: If the logs file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not logs_path.exists():
        raise FileNotFoundError(f"Experiment logs not found at {logs_path}")

    with open(logs_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)

    if not isinstance(logs, list):
        raise ValueError("Expected experiment logs to be a list of entries")

    return logs

def compute_gap_closure_for_trajectory(
    trajectory_id: str,
    logs: List[Dict[str, Any]],
    evaluator: ConsensusGapEvaluator
) -> List[TrajectoryGapMetrics]:
    """
    Compute consensus gap closure metrics for a specific trajectory.

    This function:
    1. Filters logs for the given trajectory_id
    2. Groups by condition (Adapter vs Static)
    3. Calculates initial and final consensus gaps for each condition
    4. Computes the closure metric

    Args:
        trajectory_id: The unique identifier of the trajectory
        logs: Full list of experiment log entries
        evaluator: The ConsensusGapEvaluator instance

    Returns:
        List of TrajectoryGapMetrics objects (one per condition found)
    """
    # Filter logs for this trajectory
    trajectory_logs = [log for log in logs if log.get('trajectory_id') == trajectory_id]

    if not trajectory_logs:
        logger.warning(f"No logs found for trajectory_id: {trajectory_id}")
        return []

    # Group by condition
    conditions = {}
    for log in trajectory_logs:
        cond = log.get('condition', 'Unknown')
        if cond not in conditions:
            conditions[cond] = []
        conditions[cond].append(log)

    metrics_list = []

    for condition, cond_logs in conditions.items():
        # Sort logs by turn number to establish timeline
        sorted_logs = sorted(cond_logs, key=lambda x: x.get('turn_number', 0))

        # Extract turn outputs and states for evaluation
        turn_outputs = []
        for log in sorted_logs:
            output = log.get('llm_output', '')
            if output:
                turn_outputs.append(output)

        if not turn_outputs:
            logger.warning(f"No LLM outputs found for trajectory {trajectory_id} "
                         f"under condition {condition}")
            continue

        # Calculate consensus gap scores for this condition
        # The evaluator expects a list of dialogue turns
        gap_scores = evaluator.evaluate_trajectory(turn_outputs)

        if not gap_scores:
            logger.warning(f"Could not compute gap scores for trajectory {trajectory_id} "
                         f"condition {condition}")
            continue

        # Compute metrics
        initial_gap = gap_scores[0] if gap_scores else 0.0
        final_gap = gap_scores[-1] if gap_scores else 0.0
        gap_closure = initial_gap - final_gap
        gap_closure_percent = (gap_closure / initial_gap * 100) if initial_gap > 0 else 0.0
        is_improved = gap_closure > 0

        metrics = TrajectoryGapMetrics(
            trajectory_id=trajectory_id,
            condition=condition,
            initial_gap=initial_gap,
            final_gap=final_gap,
            gap_closure=gap_closure,
            gap_closure_percent=gap_closure_percent,
            is_improved=is_improved
        )
        metrics_list.append(metrics)

    return metrics_list

def compute_all_trajectory_metrics(
    logs_path: Path,
    evaluator: Optional[ConsensusGapEvaluator] = None
) -> Tuple[List[TrajectoryGapMetrics], Dict[str, Any]]:
    """
    Compute consensus gap closure metrics for all trajectories in the logs.

    Args:
        logs_path: Path to experiment_logs.json
        evaluator: Optional ConsensusGapEvaluator instance. If None, creates a default.

    Returns:
        Tuple of:
            - List of all TrajectoryGapMetrics objects
            - Summary statistics dictionary
    """
    # Load logs
    logs = load_experiment_logs(logs_path)
    logger.info(f"Loaded {len(logs)} experiment log entries")

    # Initialize evaluator if not provided
    if evaluator is None:
        evaluator = ConsensusGapEvaluator()

    # Get unique trajectory IDs
    trajectory_ids = list(set(log.get('trajectory_id') for log in logs if log.get('trajectory_id')))
    logger.info(f"Found {len(trajectory_ids)} unique trajectories")

    all_metrics = []
    for tid in trajectory_ids:
        trajectory_metrics = compute_gap_closure_for_trajectory(tid, logs, evaluator)
        all_metrics.extend(trajectory_metrics)

    # Compute summary statistics
    summary = compute_summary_statistics(all_metrics)

    return all_metrics, summary

def compute_summary_statistics(metrics: List[TrajectoryGapMetrics]) -> Dict[str, Any]:
    """
    Compute aggregate statistics from trajectory gap metrics.

    Args:
        metrics: List of TrajectoryGapMetrics objects

    Returns:
        Dictionary containing summary statistics
    """
    if not metrics:
        return {
            'total_trajectories': 0,
            'adapter_count': 0,
            'static_count': 0,
            'avg_gap_closure_adapter': None,
            'avg_gap_closure_static': None,
            'improvement_rate_adapter': None,
            'improvement_rate_static': None
        }

    adapter_metrics = [m for m in metrics if m.condition == 'Adapter']
    static_metrics = [m for m in metrics if m.condition == 'Static']

    def calc_stats(metric_list: List[TrajectoryGapMetrics]) -> Dict[str, float]:
        if not metric_list:
            return {'count': 0, 'avg_closure': None, 'improvement_rate': None}

        count = len(metric_list)
        avg_closure = sum(m.gap_closure for m in metric_list) / count
        improved_count = sum(1 for m in metric_list if m.is_improved)
        improvement_rate = (improved_count / count * 100) if count > 0 else 0.0

        return {
            'count': count,
            'avg_closure': avg_closure,
            'improvement_rate': improvement_rate
        }

    adapter_stats = calc_stats(adapter_metrics)
    static_stats = calc_stats(static_metrics)

    return {
        'total_trajectories': len(set(m.trajectory_id for m in metrics)),
        'adapter_count': adapter_stats['count'],
        'static_count': static_stats['count'],
        'avg_gap_closure_adapter': adapter_stats['avg_closure'],
        'avg_gap_closure_static': static_stats['avg_closure'],
        'improvement_rate_adapter': adapter_stats['improvement_rate'],
        'improvement_rate_static': static_stats['improvement_rate'],
        'gap_closure_difference': (
            adapter_stats['avg_closure'] - static_stats['avg_closure']
            if adapter_stats['avg_closure'] is not None and static_stats['avg_closure'] is not None
            else None
        )
    }

def write_metrics_report(
    metrics: List[TrajectoryGapMetrics],
    summary: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write metrics and summary to a JSON report file.

    Args:
        metrics: List of TrajectoryGapMetrics objects
        summary: Summary statistics dictionary
        output_path: Path to write the report
    """
    ensure_directories(output_path)

    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': summary,
        'trajectory_metrics': [
            {
                'trajectory_id': m.trajectory_id,
                'condition': m.condition,
                'initial_gap': m.initial_gap,
                'final_gap': m.final_gap,
                'gap_closure': m.gap_closure,
                'gap_closure_percent': m.gap_closure_percent,
                'is_improved': m.is_improved
            }
            for m in metrics
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Wrote metrics report to {output_path}")

def main() -> None:
    """Main entry point for computing consensus gap closure metrics."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    from config import get_config_summary
    config_summary = get_config_summary()
    logger.info(f"Starting metrics computation with config: {config_summary}")

    # Define paths
    logs_path = Path(config_summary['data_processed_dir']) / 'experiment_logs.json'
    output_path = Path(config_summary['data_results_dir']) / 'gap_closure_metrics.json'

    try:
        # Compute metrics
        metrics, summary = compute_all_trajectory_metrics(logs_path)

        # Log summary
        logger.info(f"Computed metrics for {summary['total_trajectories']} trajectories")
        logger.info(f"Adapter avg gap closure: {summary.get('avg_gap_closure_adapter', 'N/A')}")
        logger.info(f"Static avg gap closure: {summary.get('avg_gap_closure_static', 'N/A')}")

        # Write report
        write_metrics_report(metrics, summary, output_path)

        logger.info("Metrics computation completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during metrics computation: {e}")
        raise

if __name__ == '__main__':
    main()
