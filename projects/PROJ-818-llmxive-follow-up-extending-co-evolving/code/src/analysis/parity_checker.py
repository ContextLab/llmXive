"""
Post-run parity verification module.

This module generates a comprehensive report verifying that the rule-evaluation
budget was strictly adhered to across all batch runs, satisfying FR-002.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParityVerificationError(Exception):
    """Raised when parity verification fails or data is missing."""
    pass

@dataclass
class RunParityRecord:
    """Record of a single run's parity metrics."""
    run_id: str
    condition: str
    seed: int
    total_rule_evaluations: int
    expected_budget: int
    parity_violated: bool
    deviation: int
    file_path: str

@dataclass
class ParityReport:
    """Aggregated parity verification report."""
    total_runs: int
    runs_with_violations: int
    all_conditions_meet_parity: bool
    expected_budget: int
    condition_stats: Dict[str, Dict[str, Any]]
    details: List[RunParityRecord]
    verification_passed: bool

def load_single_run_metrics(file_path: Path) -> Dict[str, Any]:
    """Load metrics from a single run's final_metrics.json."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ParityVerificationError(f"Metrics file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ParityVerificationError(f"Invalid JSON in {file_path}: {e}")

def extract_evaluation_count(metrics: Dict[str, Any]) -> int:
    """
    Extract the total rule evaluation count from metrics.
    Looks for 'total_rule_evaluations' or calculates from 'rule_evaluations' history.
    """
    if 'total_rule_evaluations' in metrics:
        return int(metrics['total_rule_evaluations'])
    
    # Fallback: check for a history or cumulative count
    if 'rule_evaluations' in metrics:
        evals = metrics['rule_evaluations']
        if isinstance(evals, list) and len(evals) > 0:
            return int(evals[-1])
        if isinstance(evals, int):
            return evals

    raise ParityVerificationError("Could not find total rule evaluation count in metrics")

def extract_condition_from_path(file_path: Path) -> str:
    """
    Extract condition name from the file path structure.
    Expected pattern: .../results/run_<id>_<condition>/final_metrics.json
    """
    parts = file_path.parts
    # Look for a directory name that contains the condition
    for part in reversed(parts[:-1]): # Skip filename
        if 'sequential' in part.lower():
            return 'sequential'
        if 'mixed' in part.lower():
            return 'mixed'
        if 'coevolving' in part.lower():
            return 'coevolving'
    
    # Fallback: try to parse from directory name
    parent_dir = file_path.parent.name
    if 'sequential' in parent_dir:
        return 'sequential'
    if 'mixed' in parent_dir:
        return 'mixed'
    if 'coevolving' in parent_dir:
        return 'coevolving'
    
    return 'unknown'

def collect_all_run_metrics(results_dir: Path) -> List[Tuple[Path, Dict[str, Any], str]]:
    """
    Recursively find all final_metrics.json files in the results directory.
    Returns a list of (file_path, metrics, condition).
    """
    if not results_dir.exists():
        raise ParityVerificationError(f"Results directory not found: {results_dir}")
    
    run_files = []
    for root, _, files in os.walk(results_dir):
        if 'final_metrics.json' in files:
            file_path = Path(root) / 'final_metrics.json'
            try:
                metrics = load_single_run_metrics(file_path)
                condition = extract_condition_from_path(file_path)
                run_files.append((file_path, metrics, condition))
            except ParityVerificationError as e:
                logger.warning(f"Skipping {file_path}: {e}")
    
    return run_files

def generate_parity_report(
    results_dir: Path, 
    expected_budget: int,
    seed_config_path: Optional[Path] = None
) -> ParityReport:
    """
    Generate a comprehensive parity report for all runs in the results directory.
    
    Args:
        results_dir: Path to the data/results directory containing run subfolders.
        expected_budget: The integer cap for rule evaluations (from config).
        seed_config_path: Optional path to batch_config.json to map run IDs to seeds.
    
    Returns:
        ParityReport object with detailed statistics.
    """
    run_data = collect_all_run_metrics(results_dir)
    
    if not run_data:
        raise ParityVerificationError("No run metrics found in results directory")
    
    # Load seed mapping if available
    seed_map = {}
    if seed_config_path and seed_config_path.exists():
        try:
            with open(seed_config_path, 'r') as f:
                config = json.load(f)
                # Assume structure: { "conditions": { "sequential": [seeds], ... } }
                # We need to map run_id -> seed. This depends on how batch_config.json is structured.
                # If it's a flat list of runs, we map by index.
                if 'runs' in config:
                    for i, run in enumerate(config['runs']):
                        seed_map[run.get('run_id', f'run_{i}')] = run.get('seed', 0)
        except Exception as e:
            logger.warning(f"Could not load seed config: {e}")

    details = []
    condition_stats: Dict[str, Dict[str, int]] = {
        'sequential': {'count': 0, 'sum': 0, 'violations': 0},
        'mixed': {'count': 0, 'sum': 0, 'violations': 0},
        'coevolving': {'count': 0, 'sum': 0, 'violations': 0},
        'unknown': {'count': 0, 'sum': 0, 'violations': 0}
    }
    
    runs_with_violations = 0
    
    for file_path, metrics, condition in run_data:
        try:
            total_evals = extract_evaluation_count(metrics)
        except ParityVerificationError as e:
            logger.warning(f"Could not extract eval count from {file_path}: {e}")
            continue

        # Determine run ID
        run_id = file_path.parent.name
        
        # Determine seed
        seed = seed_map.get(run_id, 0)
        if seed == 0:
            # Try to parse from run_id if it follows a pattern like run_123
            try:
                if '_' in run_id:
                    seed = int(run_id.split('_')[1])
            except (IndexError, ValueError):
                pass

        parity_violated = total_evals > expected_budget
        deviation = total_evals - expected_budget
        
        if parity_violated:
            runs_with_violations += 1
            condition_stats[condition]['violations'] += 1
        
        condition_stats[condition]['count'] += 1
        condition_stats[condition]['sum'] += total_evals

        details.append(RunParityRecord(
            run_id=run_id,
            condition=condition,
            seed=seed,
            total_rule_evaluations=total_evals,
            expected_budget=expected_budget,
            parity_violated=parity_violated,
            deviation=deviation,
            file_path=str(file_path)
        ))

    # Calculate condition averages
    final_condition_stats = {}
    for cond, stats in condition_stats.items():
        if stats['count'] > 0:
            final_condition_stats[cond] = {
                'count': stats['count'],
                'total_evaluations': stats['sum'],
                'average_evaluations': stats['sum'] / stats['count'],
                'violations': stats['violations']
            }
        else:
            final_condition_stats[cond] = {
                'count': 0,
                'total_evaluations': 0,
                'average_evaluations': 0,
                'violations': 0
            }

    all_conditions_meet_parity = runs_with_violations == 0
    verification_passed = all_conditions_meet_parity and (runs_with_violations == 0)

    return ParityReport(
        total_runs=len(details),
        runs_with_violations=runs_with_violations,
        all_conditions_meet_parity=all_conditions_meet_parity,
        expected_budget=expected_budget,
        condition_stats=final_condition_stats,
        details=details,
        verification_passed=verification_passed
    )

def save_parity_report(report: ParityReport, output_path: Path) -> None:
    """Save the parity report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_dict = {
        'summary': {
            'total_runs': report.total_runs,
            'runs_with_violations': report.runs_with_violations,
            'all_conditions_meet_parity': report.all_conditions_meet_parity,
            'expected_budget': report.expected_budget,
            'verification_passed': report.verification_passed
        },
        'condition_statistics': report.condition_stats,
        'details': [asdict(d) for d in report.details]
    }
    
    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    logger.info(f"Parity report saved to {output_path}")

def main():
    """
    CLI entry point for generating the post-run parity verification report.
    
    Usage:
        python -m src.analysis.parity_checker --results-dir data/results --budget 1000
    """
    import argparse

    parser = argparse.ArgumentParser(description='Generate post-run parity verification report')
    parser.add_argument('--results-dir', type=str, default='data/results',
                        help='Path to the results directory containing run subfolders')
    parser.add_argument('--budget', type=int, required=True,
                        help='Expected rule evaluation budget per run')
    parser.add_argument('--seed-config', type=str, default='data/batch_config.json',
                        help='Path to batch_config.json for seed mapping')
    parser.add_argument('--output', type=str, default='data/results/parity_report.json',
                        help='Output path for the parity report')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    seed_config_path = Path(args.seed_config)
    output_path = Path(args.output)

    try:
        logger.info(f"Generating parity report for {results_dir} with budget {args.budget}")
        report = generate_parity_report(results_dir, args.budget, seed_config_path)
        save_parity_report(report, output_path)
        
        if report.verification_passed:
            logger.info("SUCCESS: All runs meet parity requirements.")
            sys.exit(0)
        else:
            logger.error(f"FAILURE: {report.runs_with_violations} runs violated parity requirements.")
            sys.exit(1)
    except ParityVerificationError as e:
        logger.error(f"Parity verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
