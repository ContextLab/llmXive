import json
import os
import sys
import hashlib
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
    """Raised when parity verification fails."""
    pass

@dataclass
class RunParityRecord:
    run_id: str
    condition: str
    evaluation_count: int
    target_budget: int
    is_valid: bool
    deviation: int

@dataclass
class ParityReport:
    total_runs: int
    valid_runs: int
    invalid_runs: int
    overall_parity_valid: bool
    runs: List[RunParityRecord]
    target_budget: int

def load_single_run_metrics(file_path: Path) -> Dict[str, Any]:
    """Load metrics from a single run result file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_evaluation_count(metrics: Dict[str, Any]) -> int:
    """Extract the evaluation count from run metrics."""
    # The metrics structure should have a 'rule_evaluations' or similar key
    # Based on T022/T023, we expect the total count to be tracked
    count = metrics.get('total_rule_evaluations', 0)
    if count == 0:
        count = metrics.get('evaluation_count', 0)
    return count

def extract_condition_from_path(file_path: Path) -> str:
    """Extract condition name from file path (e.g., run_sequential_001 -> sequential)."""
    parts = file_path.name.split('_')
    if len(parts) >= 3:
        return parts[1]  # e.g., 'sequential' from 'run_sequential_001.json'
    return "unknown"

def collect_all_run_metrics(results_dir: Path) -> List[Dict[str, Any]]:
    """Collect metrics from all run result files in the directory."""
    run_files = list(results_dir.glob("run_*.json"))
    if not run_files:
        raise FileNotFoundError(f"No run result files found in {results_dir}")
    
    all_metrics = []
    for file_path in sorted(run_files):
        try:
            metrics = load_single_run_metrics(file_path)
            metrics['_file_path'] = str(file_path)
            all_metrics.append(metrics)
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    return all_metrics

def generate_parity_report(
    results_dir: Path,
    target_budget: int
) -> ParityReport:
    """Generate a parity report from all run results."""
    runs_data = collect_all_run_metrics(results_dir)
    
    run_records = []
    valid_count = 0
    invalid_count = 0
    
    for metrics in runs_data:
        file_path = Path(metrics['_file_path'])
        run_id = file_path.stem
        condition = extract_condition_from_path(file_path)
        evaluation_count = extract_evaluation_count(metrics)
        
        is_valid = (evaluation_count == target_budget)
        deviation = evaluation_count - target_budget
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            logger.warning(f"Parity mismatch in {run_id}: {evaluation_count} vs {target_budget}")
        
        run_records.append(RunParityRecord(
            run_id=run_id,
            condition=condition,
            evaluation_count=evaluation_count,
            target_budget=target_budget,
            is_valid=is_valid,
            deviation=deviation
        ))
    
    overall_valid = (invalid_count == 0)
    
    return ParityReport(
        total_runs=len(run_records),
        valid_runs=valid_count,
        invalid_runs=invalid_count,
        overall_parity_valid=overall_valid,
        runs=run_records,
        target_budget=target_budget
    )

def save_parity_report(report: ParityReport, output_path: Path) -> None:
    """Save the parity report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert dataclasses to dicts for JSON serialization
    report_dict = {
        'total_runs': report.total_runs,
        'valid_runs': report.valid_runs,
        'invalid_runs': report.invalid_runs,
        'overall_parity_valid': report.overall_parity_valid,
        'target_budget': report.target_budget,
        'runs': [asdict(r) for r in report.runs]
    }
    
    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    logger.info(f"Parity report saved to {output_path}")

def generate_parity_checksum(parity_report_path: Path, output_path: Path) -> None:
    """
    Generate a deterministic SHA-256 checksum file for the parity report.
    This satisfies the 'post-run checksum' requirement of FR-002.
    """
    if not parity_report_path.exists():
        raise FileNotFoundError(f"Parity report not found: {parity_report_path}")
    
    # Read the report content
    with open(parity_report_path, 'rb') as f:
        content = f.read()
    
    # Compute SHA-256 hash
    checksum = hashlib.sha256(content).hexdigest()
    
    # Write checksum to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(f"{checksum}  {parity_report_path.name}\n")
    
    logger.info(f"Parity checksum generated: {output_path} ({checksum})")

def main():
    """
    CLI entry point for generating parity checksum artifact.
    
    Usage:
        python src/analysis/parity_checker.py generate-checksum \
            --report data/results/parity_report.json \
            --output data/results/parity_checksum.sha256
    """
    parser = __create_parser__()
    args = parser.parse_args()
    
    if args.command == 'generate-checksum':
        report_path = Path(args.report)
        output_path = Path(args.output)
        
        logger.info(f"Generating checksum for {report_path}")
        generate_parity_checksum(report_path, output_path)
        logger.info("Checksum generation complete")
    else:
        parser.print_help()
        sys.exit(1)

def __create_parser__():
    import argparse
    parser = argparse.ArgumentParser(
        prog='parity_checker',
        description='Parity checking and checksum generation for co-evolving policy distillation'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate checksum command
    checksum_parser = subparsers.add_parser(
        'generate-checksum',
        help='Generate SHA-256 checksum for parity report'
    )
    checksum_parser.add_argument(
        '--report',
        required=True,
        help='Path to parity report JSON file'
    )
    checksum_parser.add_argument(
        '--output',
        required=True,
        help='Path for output checksum file'
    )
    
    return parser

if __name__ == '__main__':
    main()