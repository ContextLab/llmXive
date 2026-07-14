"""
Main orchestration script for disorder effect quantification.

Executes parallel disorder realizations using joblib, coordinating
Hamiltonian generation, eigenstate analysis, and result storage.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import joblib
import numpy as np

# Project imports
from config import get_config
from generate_hamiltonian import generate_hamiltonian
from storage_utils import log_provenance_entry, save_localization_length
from logger_utils import get_logger, log_numerical_warning
from analyze_pr import analyze_single_realization

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def process_realization(args: Tuple[int, int, float]) -> Dict[str, Any]:
    """
    Process a single disorder realization.

    Args:
        args: Tuple of (realization_index, system_size, disorder_strength)

    Returns:
        Dictionary containing results for this realization
    """
    realization_index, L, W = args
    config = get_config()
    logger = get_logger(__name__)

    try:
        # Generate Hamiltonian
        hamiltonian = generate_hamiltonian(L, W, seed=config.RANDOM_SEED + realization_index)

        # Analyze realization (compute PR and localization length)
        result = analyze_single_realization(hamiltonian, L, W, realization_index)

        # Save results
        if result.get('localization_length') is not None:
            save_localization_length(
                result['localization_length'],
                W,
                L,
                realization_index,
                config.DATA_PROCESSED_PATH
            )

        return {
            'success': True,
            'realization_index': realization_index,
            'L': L,
            'W': W,
            'localization_length': result.get('localization_length'),
            'pr_values': result.get('pr_values'),
            'eigenstate_count': result.get('eigenstate_count', 0)
        }

    except Exception as e:
        logger.error(f"Failed to process realization {realization_index} (L={L}, W={W}): {str(e)}")
        log_numerical_warning(f"Realization {realization_index} failed: {str(e)}")
        return {
            'success': False,
            'realization_index': realization_index,
            'L': L,
            'W': W,
            'error': str(e)
        }

def run_orchestration() -> Dict[str, Any]:
    """
    Main orchestration function.

    Generates and processes multiple disorder realizations across
    different system sizes and disorder strengths.
    """
    config = get_config()
    logger = get_logger(__name__)

    logger.info("Starting orchestration for disorder effect quantification")
    start_time = datetime.now()

    # Build list of tasks: (realization_index, L, W)
    tasks = []
    task_index = 0

    # Generate tasks for each combination of L and W
    # Target: multiple widths × 100 samples as specified in FR-011
    for W in config.DISORDER_WIDTHS:
        for L in config.SYSTEM_SIZES:
            for _ in range(config.NUM_REALIZATIONS_PER_WIDTH):
                tasks.append((task_index, L, W))
                task_index += 1

    logger.info(f"Generated {len(tasks)} total realization tasks")
    logger.info(f"Disorder widths: {config.DISORDER_WIDTHS}")
    logger.info(f"System sizes: {config.SYSTEM_SIZES}")
    logger.info(f"Realizations per width: {config.NUM_REALIZATIONS_PER_WIDTH}")

    # Execute in parallel using joblib
    logger.info(f"Starting parallel execution with {config.NUM_CPUS} workers")

    results = joblib.Parallel(n_jobs=config.NUM_CPUS, verbose=10)(
        joblib.delayed(process_realization)(task)
        for task in tasks
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Aggregate results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    summary = {
        'total_tasks': len(tasks),
        'successful': len(successful),
        'failed': len(failed),
        'duration_seconds': duration,
        'timestamp': start_time.isoformat(),
        'config': {
            'disorder_widths': config.DISORDER_WIDTHS,
            'system_sizes': config.SYSTEM_SIZES,
            'num_realizations_per_width': config.NUM_REALIZATIONS_PER_WIDTH,
            'num_cpus': config.NUM_CPUS
        }
    }

    # Log summary
    logger.info(f"Orchestration complete: {len(successful)}/{len(tasks)} successful in {duration:.2f}s")

    if failed:
        logger.warning(f"{len(failed)} tasks failed. Check logs for details.")
        summary['failed_indices'] = [r['realization_index'] for r in failed]

    # Save summary to metadata
    metadata_path = Path(config.DATA_METADATA_PATH)
    metadata_path.mkdir(parents=True, exist_ok=True)
    summary_file = metadata_path / 'orchestration_summary.json'

    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Summary saved to {summary_file}")

    return summary

def main():
    """Entry point for the orchestration script."""
    try:
        summary = run_orchestration()
        print(f"Orchestration completed: {summary['successful']}/{summary['total_tasks']} successful")
        return 0
    except Exception as e:
        print(f"Orchestration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())