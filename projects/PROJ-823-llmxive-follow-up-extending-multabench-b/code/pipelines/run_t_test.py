"""
Pipeline script to orchestrate t-test analysis for User Story 3.
Compares CPU-Conditioned performance against GPU-Tuned baselines.
"""
import os
import sys
import json
import argparse
from pathlib import Path

from utils.logging import setup_logging, get_logger, log_info, log_error
from config import ensure_directories
from analysis.t_test_analysis import run_t_test_analysis

logger = get_logger(__name__)


def main():
    """Main entry point for the t-test analysis pipeline."""
    parser = argparse.ArgumentParser(description='Run t-test analysis pipeline')
    parser.add_argument('--run-id', type=str, default=None,
                      help='Run ID for artifact naming (optional)')
    parser.add_argument('--conditioned-metrics', type=str,
                      default='data/artifacts/metrics_conditioned_agg.json',
                      help='Path to conditioned metrics file')
    parser.add_argument('--gpu-baselines', type=str,
                      default='data/artifacts/gpu_tuned_baselines.csv',
                      help='Path to GPU-Tuned baselines file')
    parser.add_argument('--output', type=str,
                      default='data/artifacts/t_test_results.json',
                      help='Path for output results')
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    # Setup logging
    setup_logging()
    
    logger.info("Starting t-test analysis pipeline")
    
    conditioned_path = Path(args.conditioned_metrics)
    baselines_path = Path(args.gpu_baselines)
    output_path = Path(args.output)
    
    if not conditioned_path.exists():
        logger.error(f"Conditioned metrics file not found: {conditioned_path}")
        sys.exit(1)
        
    if not baselines_path.exists():
        logger.error(f"GPU-Tuned baselines file not found: {baselines_path}")
        sys.exit(1)
    
    try:
        result = run_t_test_analysis(conditioned_path, baselines_path, output_path)
        
        logger.info(f"Analysis complete. Results saved to {output_path}")
        logger.info(f"Summary: {json.dumps(result['summary'], indent=2)}")
        
        return 0
    except Exception as e:
        log_error(f"Pipeline failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
