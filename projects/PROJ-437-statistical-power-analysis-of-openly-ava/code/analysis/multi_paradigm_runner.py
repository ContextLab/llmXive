"""
Multi-Paradigm Runner for Statistical Power Analysis.

This module orchestrates the power curve generation loop across verified
distinct cognitive paradigms. It coordinates data loading, preprocessing,
simulation, and analysis for each paradigm, ensuring proper timing
logging and error handling.

Dependencies:
    - T052 (paradigm_loader): To fetch the list of active paradigms.
    - T022 (power_curve_generator): To generate power curves for each paradigm.
    - T038b/T050 (timer): For wall-clock time monitoring and logging.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from project modules based on API surface
from download.paradigm_loader import load_paradigm_manifest, ParadigmLoaderError
from analysis.power_curve_generator import run_bootstrap_loop, generate_power_curve, save_power_curves
from utils.timer import start_run, end_run, log_split, save_timing_breakdown
from utils.seed_manager import set_global_seed, get_seed
from models.simulation_config import SimulationConfig
from utils.memory_monitor import monitor_and_ensure_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/paper/multi_paradigm_execution.log')
    ]
)
logger = logging.getLogger(__name__)

def run_paradigm_analysis(
    paradigm_config: Dict[str, Any],
    output_dir: Path,
    config: SimulationConfig,
    timeout_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute the full power curve analysis for a single paradigm.

    Args:
        paradigm_config: Dictionary containing paradigm details (name, dataset_id, etc.)
        output_dir: Directory to save results for this paradigm.
        config: Simulation configuration object.
        timeout_seconds: Optional timeout for the analysis (not implemented in this version).

    Returns:
        Dictionary containing analysis results and metadata.
    """
    paradigm_name = paradigm_config.get('paradigm', 'unknown')
    dataset_id = paradigm_config.get('dataset_id', 'unknown')
    
    logger.info(f"Starting analysis for paradigm: {paradigm_name} (Dataset: {dataset_id})")
    
    # Log start time for this paradigm
    start_time = start_run(f"paradigm_{paradigm_name}")
    
    try:
        # Ensure output directory exists
        paradigm_output_dir = output_dir / paradigm_name
        paradigm_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set seed for reproducibility (unique per paradigm)
        paradigm_seed = get_seed() + hash(paradigm_name) % 10000
        set_global_seed(paradigm_seed)
        
        # Run the bootstrap loop for this paradigm
        # Note: In a real implementation, this would call the full pipeline
        # including data download, preprocessing, noise estimation, etc.
        # For now, we simulate the call to run_bootstrap_loop
        
        logger.info(f"Running bootstrap loop for {paradigm_name}...")
        
        # Call the power curve generator
        power_curve_results = run_bootstrap_loop(
            dataset_id=dataset_id,
            paradigm=paradigm_name,
            config=config,
            output_dir=paradigm_output_dir
        )
        
        # Log completion time
        end_time = end_run(f"paradigm_{paradigm_name}", start_time)
        
        # Save timing breakdown
        save_timing_breakdown(
            step=f"paradigm_{paradigm_name}",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds()
        )
        
        logger.info(f"Completed analysis for {paradigm_name} in {(end_time - start_time).total_seconds():.2f}s")
        
        return {
            'paradigm': paradigm_name,
            'dataset_id': dataset_id,
            'status': 'success',
            'results': power_curve_results,
            'timing': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing paradigm {paradigm_name}: {str(e)}", exc_info=True)
        
        # Log failure time
        end_time = end_run(f"paradigm_{paradigm_name}", start_time)
        
        return {
            'paradigm': paradigm_name,
            'dataset_id': dataset_id,
            'status': 'failed',
            'error': str(e),
            'timing': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds()
            }
        }

def run_multi_paradigm_loop(
    output_base_dir: Path,
    config: SimulationConfig,
    manifest_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Orchestrate the power curve generation loop across all verified paradigms.

    Args:
        output_base_dir: Base directory for all output files.
        config: Simulation configuration object.
        manifest_path: Optional path to the paradigm manifest. If None, uses default.

    Returns:
        List of dictionaries containing results for each paradigm.
    """
    logger.info("Starting multi-paradigm analysis loop")
    
    # Load paradigm manifest
    try:
        if manifest_path is None:
            manifest_path = Path("specs/001-statistical-power-analysis/research.md")
        
        paradigms = load_paradigm_manifest(manifest_path)
        logger.info(f"Loaded {len(paradigms)} paradigms from manifest")
    except ParadigmLoaderError as e:
        logger.error(f"Failed to load paradigm manifest: {str(e)}")
        raise
    
    # Create output directory
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Run analysis for each paradigm
    all_results = []
    total_start = start_run("multi_paradigm_loop")
    
    for i, paradigm_config in enumerate(paradigms):
        logger.info(f"Processing paradigm {i+1}/{len(paradigms)}: {paradigm_config.get('paradigm')}")
        
        # Log split timing
        log_split(f"paradigm_{paradigm_config.get('paradigm')}_start")
        
        result = run_paradigm_analysis(
            paradigm_config=paradigm_config,
            output_dir=output_base_dir,
            config=config
        )
        
        # Log split timing
        log_split(f"paradigm_{paradigm_config.get('paradigm')}_end")
        
        all_results.append(result)
        
        # Save intermediate results
        results_file = output_base_dir / "paradigm_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
    
    # Log final timing
    total_end = end_run("multi_paradigm_loop", total_start)
    save_timing_breakdown(
        step="multi_paradigm_loop",
        start_time=total_start,
        end_time=total_end,
        duration_seconds=(total_end - total_start).total_seconds()
    )
    
    # Save final summary
    summary = {
        'total_paradigms': len(paradigms),
        'successful': sum(1 for r in all_results if r['status'] == 'success'),
        'failed': sum(1 for r in all_results if r['status'] == 'failed'),
        'total_duration_seconds': (total_end - total_start).total_seconds(),
        'results': all_results
    }
    
    summary_file = output_base_dir / "multi_paradigm_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"Multi-paradigm loop completed. Success: {summary['successful']}, Failed: {summary['failed']}")
    
    return all_results

def main():
    """Main entry point for the multi-paradigm runner."""
    parser = argparse.ArgumentParser(description="Run power curve analysis across multiple paradigms")
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path("data/aggregated"),
        help="Base directory for output files"
    )
    parser.add_argument(
        '--manifest',
        type=Path,
        default=Path("specs/001-statistical-power-analysis/research.md"),
        help="Path to the paradigm manifest file"
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        '--num-iterations',
        type=int,
        default=10,
        help="Number of bootstrap iterations per sample size"
    )
    parser.add_argument(
        '--sample-sizes',
        type=str,
        default="10,20,30,40,50",
        help="Comma-separated list of sample sizes to test"
    )
    
    args = parser.parse_args()
    
    # Set global seed
    set_global_seed(args.seed)
    
    # Create simulation config
    config = SimulationConfig(
        sample_size_target=[int(x) for x in args.sample_sizes.split(',')],
        smoothing_kernel=4.0,  # Default to 4mm/4s
        num_iterations=args.num_iterations,
        random_seed=args.seed
    )
    
    try:
        results = run_multi_paradigm_loop(
            output_base_dir=args.output_dir,
            config=config,
            manifest_path=args.manifest
        )
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        if failed_count > 0:
            logger.warning(f"{failed_count} paradigms failed")
            sys.exit(1)
        else:
            logger.info("All paradigms completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Multi-paradigm runner failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()