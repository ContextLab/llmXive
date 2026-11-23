import os
import sys
import argparse
import logging
from pathlib import Path
from utils.config import get_results_dir, get_data_dir, set_seed, get_seed
from eval.iou_calculator import main as run_iou_analysis
from eval.sensitivity import main as run_sensitivity_analysis_script
from eval.predictor import main as run_confidence_intervals_script
from eval.interpret import main as run_grad_cam_analysis

def setup_analysis_logging():
    """Setup logging for analysis scripts."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_results_dir() / "analysis.log")
        ]
    )
    return logging.getLogger("analyze")

def run_iou_analysis_wrapper(args):
    """Wrapper to run IoU analysis."""
    logging.info("Running IoU analysis...")
    return run_iou_analysis()

def run_grad_cam_analysis_wrapper(args):
    """Wrapper to run Grad-CAM analysis."""
    logging.info("Running Grad-CAM analysis...")
    return run_grad_cam_analysis()

def run_sensitivity_analysis_wrapper(args):
    """Wrapper to run sensitivity analysis."""
    logging.info("Running sensitivity analysis...")
    return run_sensitivity_analysis_script()

def run_confidence_intervals_wrapper(args):
    """Wrapper to run confidence intervals analysis."""
    logging.info("Running confidence intervals analysis...")
    return run_confidence_intervals_script()

def main():
    """Main orchestration script for analysis tasks."""
    parser = argparse.ArgumentParser(description="Run analysis tasks for material strength prediction")
    parser.add_argument("--iou", action="store_true", help="Run IoU calculation")
    parser.add_argument("--grad-cam", action="store_true", help="Run Grad-CAM visualization")
    parser.add_argument("--sensitivity", action="store_true", help="Run sensitivity analysis")
    parser.add_argument("--confidence-intervals", action="store_true", help="Run confidence intervals calculation")
    parser.add_argument("--all", action="store_true", help="Run all analysis tasks")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    logger = setup_analysis_logging()
    set_seed(args.seed)
    
    if args.all or (not args.iou and not args.grad_cam and not args.sensitivity and not args.confidence_intervals):
        # Default to running all if no specific task is specified
        args.iou = True
        args.grad_cam = True
        args.sensitivity = True
        args.confidence_intervals = True
    
    if args.grad_cam:
        run_grad_cam_analysis_wrapper(args)
    
    if args.iou:
        run_iou_analysis_wrapper(args)
    
    if args.sensitivity:
        run_sensitivity_analysis_wrapper(args)
    
    if args.confidence_intervals:
        run_confidence_intervals_wrapper(args)
    
    logger.info("All requested analysis tasks completed.")

if __name__ == "__main__":
    main()
