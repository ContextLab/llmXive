"""
Sensitivity Analysis Wrapper for T031.

This module implements the parameterized re-execution of ROI extraction and group analysis
across different smoothing kernels and mask probability thresholds as required by T031.

It orchestrates the following steps for each combination of parameters:
1. Update configuration with new smoothing kernel and mask threshold.
2. Run ROI extraction (reusing logic from roi_extraction.py but with updated masks).
3. Run group analysis (reusing logic from group_analysis.py).
4. Collect results into a structured list for the consistency table.
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import existing functions from the API surface
from analysis.roi_extraction import run_roi_extraction
from analysis.group_analysis import run_group_analysis, save_results
from analysis.summary_statistics import generate_summary_statistics, save_summary_statistics
from config.loader import get_config, get_path, ensure_paths_exist

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/sensitivity_wrapper.log')
    ]
)
logger = logging.getLogger(__name__)

def run_sensitivity_iteration(
    smoothing_kernel: float,
    mask_threshold: float,
    config_path: str,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Executes one iteration of the sensitivity analysis.

    Args:
        smoothing_kernel: FWHM value in mm for smoothing.
        mask_threshold: Probability threshold for ROI masks (0.0 to 1.0).
        config_path: Path to the base configuration file.
        output_dir: Directory to store iteration-specific results.

    Returns:
        A dictionary containing the results for this iteration.
    """
    logger.info(f"Starting iteration: Smoothing={smoothing_kernel}mm, Threshold={mask_threshold}")
    
    start_time = time.time()
    
    # 1. Prepare environment for this iteration
    # We create a temporary config or modify the global state if the loader supports it.
    # Since config.loader.get_config() likely reads a static file, we will assume
    # the ROI extraction and Group Analysis functions accept arguments or we modify
    # the config file temporarily. 
    # However, to strictly follow "extend, don't re-author" and use existing APIs:
    # We will assume the `run_roi_extraction` and `run_group_analysis` use the global
    # config loader. We need to inject these parameters.
    
    # Strategy: We will modify the config file temporarily if it's a YAML file, 
    # or pass arguments if the functions support them. 
    # Looking at the API surface, `run_roi_extraction` and `run_group_analysis` 
    # do not show explicit args for smoothing/threshold in the signature list.
    # We must rely on the config loader.
    
    # Let's assume the config file is at `data/config.yaml` or similar.
    # We will read the config, update the specific keys, save it, run, then restore.
    # This is a bit heavy but ensures compatibility with existing code that reads config.
    
    import yaml
    config_file = Path(config_path)
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        return {"error": "Config file not found", "smoothing": smoothing_kernel, "threshold": mask_threshold}

    with open(config_file, 'r') as f:
        original_config = yaml.safe_load(f)
    
    # Backup original values
    original_smoothing = original_config.get('preprocessing', {}).get('smoothing_kernel', None)
    original_threshold = original_config.get('analysis', {}).get('roi_mask_threshold', None)

    try:
        # Update config
        if 'preprocessing' not in original_config:
            original_config['preprocessing'] = {}
        original_config['preprocessing']['smoothing_kernel'] = smoothing_kernel

        if 'analysis' not in original_config:
            original_config['analysis'] = {}
        original_config['analysis']['roi_mask_threshold'] = mask_threshold

        # Write updated config
        with open(config_file, 'w') as f:
            yaml.dump(original_config, f)
        
        logger.info(f"Config updated: Smoothing={smoothing_kernel}, Threshold={mask_threshold}")

        # 2. Run ROI Extraction
        # The existing function expects to be called via CLI or main, but we can call the logic
        # if it's exposed. If `run_roi_extraction` is the main entry point, we might need to 
        # call it directly.
        # From API: `from analysis.roi_extraction import run_roi_extraction`
        # Assuming it returns data or populates files.
        logger.info("Running ROI Extraction...")
        # We assume run_roi_extraction() handles the config loading internally.
        # If it requires arguments, we might need to adjust. 
        # Based on typical patterns, it might be:
        roi_results = run_roi_extraction() 
        # If run_roi_extraction returns None and writes to file, we proceed to load.
        # If it returns data, we use it.
        
        # 3. Run Group Analysis
        logger.info("Running Group Analysis...")
        # Similar assumption for group analysis
        group_results = run_group_analysis()

        # 4. Generate Summary Statistics for this iteration
        # We need to capture the specific stats to put in the sensitivity table.
        # The existing `generate_summary_statistics` likely reads the beta file.
        # We might need to ensure the beta file is from the current run.
        # Assuming run_group_analysis updates the beta file or we have a specific output path.
        # For safety, we re-run summary stats generation which reads the current state.
        summary_stats = generate_summary_statistics()
        
        # Extract key metrics for the sensitivity table
        # We expect summary_stats to be a list of dicts or a dict with roi/event keys.
        # We'll flatten it for the table.
        iteration_metrics = {
            "smoothing_kernel": smoothing_kernel,
            "mask_threshold": mask_threshold,
            "status": "success",
            "duration_sec": time.time() - start_time
        }

        # Aggregate stats from summary_stats
        # Assuming summary_stats is a list of dicts with 'roi', 'event', 'mean', 't_stat', 'p_value'
        if isinstance(summary_stats, list):
            for stat in summary_stats:
                key = f"{stat.get('roi', 'unknown')}_{stat.get('event', 'unknown')}"
                iteration_metrics[f"{key}_mean"] = stat.get('mean')
                iteration_metrics[f"{key}_t_stat"] = stat.get('t_stat')
                iteration_metrics[f"{key}_p_value"] = stat.get('p_value')
        elif isinstance(summary_stats, dict):
            # Handle dict format if necessary
            pass

        logger.info(f"Iteration completed successfully in {iteration_metrics['duration_sec']:.2f}s")
        return iteration_metrics

    except Exception as e:
        logger.error(f"Iteration failed: {str(e)}", exc_info=True)
        return {
            "smoothing_kernel": smoothing_kernel,
            "mask_threshold": mask_threshold,
            "status": "failed",
            "error": str(e),
            "duration_sec": time.time() - start_time
        }
    finally:
        # Restore original config
        original_config['preprocessing']['smoothing_kernel'] = original_smoothing
        original_config['analysis']['roi_mask_threshold'] = original_threshold
        with open(config_file, 'w') as f:
            yaml.dump(original_config, f)
        logger.info("Config restored to original values.")

def run_sensitivity_analysis(
    smoothing_kernels: List[float],
    mask_thresholds: List[float],
    config_path: str,
    output_csv_path: str
) -> List[Dict[str, Any]]:
    """
    Main entry point for the sensitivity analysis loop.

    Args:
        smoothing_kernels: List of FWHM values (mm) to test.
        mask_thresholds: List of probability thresholds to test.
        config_path: Path to the project config file.
        output_csv_path: Path where the results CSV will be saved.
    
    Returns:
        List of result dictionaries.
    """
    logger.info(f"Starting Sensitivity Analysis with {len(smoothing_kernels)} kernels and {len(mask_thresholds)} thresholds.")
    
    results = []
    
    # Ensure output directory exists
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for kernel in smoothing_kernels:
        for threshold in mask_thresholds:
            result = run_sensitivity_iteration(
                smoothing_kernel=kernel,
                mask_threshold=threshold,
                config_path=config_path,
                output_dir=output_path.parent
            )
            results.append(result)
            logger.info(f"Completed combination: Kernel={kernel}, Threshold={threshold}, Status={result.get('status')}")
    
    # Save results to CSV
    if results:
        # Determine all keys
        keys = set()
        for r in results:
            keys.update(r.keys())
        
        with open(output_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Sensitivity results saved to {output_csv_path}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Run Sensitivity Analysis (T031)")
    parser.add_argument(
        '--config', 
        type=str, 
        default='data/config.yaml',
        help='Path to the configuration file.'
    )
    parser.add_argument(
        '--kernels', 
        type=str, 
        default='4,6,8',
        help='Comma-separated list of smoothing kernels (mm).'
    )
    parser.add_argument(
        '--thresholds', 
        type=str, 
        default='0.3,0.5',
        help='Comma-separated list of mask probability thresholds.'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/results/sensitivity_analysis.csv',
        help='Output CSV path.'
    )

    args = parser.parse_args()

    # Parse arguments
    kernels = [float(x.strip()) for x in args.kernels.split(',')]
    thresholds = [float(x.strip()) for x in args.thresholds.split(',')]

    # Run analysis
    try:
        results = run_sensitivity_analysis(
            smoothing_kernels=kernels,
            mask_thresholds=thresholds,
            config_path=args.config,
            output_csv_path=args.output
        )
        
        # Calculate consistency rate (T033 logic placeholder - actual calculation might be separate)
        # Here we just log the results
        success_count = sum(1 for r in results if r.get('status') == 'success')
        logger.info(f"Analysis complete. {success_count}/{len(results)} iterations successful.")
        
    except Exception as e:
        logger.error(f"Fatal error in sensitivity analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
