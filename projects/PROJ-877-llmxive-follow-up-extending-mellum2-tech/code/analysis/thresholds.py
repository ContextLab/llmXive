"""
Threshold analysis script for detecting non-linear shifts in complexity vs loss.

This script serves as the CLI entry point for the threshold detection logic.
It wraps the core functionality from `analysis.threshold` to provide a
command-line interface as expected by the run-book (quickstart.md).

It loads inferred data, runs change-point detection, model comparison,
and sensitivity analysis, then writes results to `data/results/us2_threshold_candidates.json`.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import core logic from the existing threshold module
from analysis.threshold import (
    load_threshold_candidates,
    write_threshold_candidates,
    load_feasibility_report,
    calculate_threshold_candidates,
    run_model_comparison,
    run_sensitivity_analysis,
    load_correlation_stats
)
from config import get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_inferred_data(input_path: Path) -> list:
    """
    Load inferred data from a JSONL file.
    
    Args:
        input_path: Path to the inferred data JSONL file.
        
    Returns:
        List of dictionaries containing inference results.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Inferred data file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                data.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                continue
    
    if not data:
        raise ValueError(f"No valid records found in {input_path}")
        
    logger.info(f"Loaded {len(data)} records from {input_path}")
    return data


def extract_metrics(data: list) -> tuple:
    """
    Extract complexity and loss metrics from inferred data.
    
    Args:
        data: List of inference result dictionaries.
        
    Returns:
        Tuple of (complexity_values, loss_values, chunk_ids)
    """
    complexity_values = []
    loss_values = []
    chunk_ids = []
    
    for record in data:
        # Expecting fields based on T017 inference output
        if 'complexity' in record and 'normalized_loss' in record:
            complexity_values.append(record['complexity'])
            loss_values.append(record['normalized_loss'])
            chunk_ids.append(record.get('chunk_id', f"unknown_{len(chunk_ids)}"))
        else:
            # Fallback: try common field names
            complexity = record.get('cyclomatic_complexity') or record.get('complexity')
            loss = record.get('normalized_loss') or record.get('token_loss')
            
            if complexity is not None and loss is not None:
                complexity_values.append(complexity)
                loss_values.append(loss)
                chunk_ids.append(record.get('chunk_id', f"unknown_{len(chunk_ids)}"))
            else:
                logger.warning(f"Skipping record missing required fields: {record.get('chunk_id', 'unknown')}")
    
    if not complexity_values:
        raise ValueError("No valid complexity/loss pairs found in data")
        
    return complexity_values, loss_values, chunk_ids


def main():
    parser = argparse.ArgumentParser(
        description="Detect non-linear thresholds in complexity vs loss relationship."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        required=True,
        help="Path to inferred data file (JSONL format)."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/results/us2_threshold_candidates.json",
        help="Path to output threshold candidates JSON file."
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging."
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    project_root = get_project_root()
    input_path = Path(args.input)
    output_path = project_root / args.output
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting threshold analysis")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # 1. Load data
        inferred_data = load_inferred_data(input_path)
        complexities, losses, chunk_ids = extract_metrics(inferred_data)
        
        # 2. Load feasibility report for parameters (perturbation magnitudes, etc.)
        feasibility_path = project_root / "data/results/feasibility_report.json"
        feasibility_report = None
        if feasibility_path.exists():
            with open(feasibility_path, 'r') as f:
                feasibility_report = json.load(f)
            logger.info(f"Loaded feasibility report: {feasibility_path}")
        else:
            logger.warning(f"Feasibility report not found at {feasibility_path}. Using defaults.")
            feasibility_report = {
                "perturbation_magnitudes": [0.01, 0.05, 0.1],
                "bootstrap_count": 1000
            }
        
        # 3. Run threshold detection
        logger.info("Detecting change points...")
        threshold_candidates = calculate_threshold_candidates(
            complexities, 
            losses, 
            chunk_ids
        )
        
        # 4. Run model comparison (Linear vs Piecewise)
        logger.info("Running model comparison...")
        model_comparison = run_model_comparison(complexities, losses, threshold_candidates)
        
        # 5. Run sensitivity analysis
        logger.info("Running sensitivity analysis...")
        sensitivity_results = run_sensitivity_analysis(
            complexities, 
            losses, 
            threshold_candidates,
            perturbation_magnitudes=feasibility_report.get("perturbation_magnitudes", [0.01, 0.05, 0.1]),
            bootstrap_count=feasibility_report.get("bootstrap_count", 1000)
        )
        
        # 6. Compile results
        final_results = {
            "status": "completed",
            "input_file": str(input_path),
            "sample_size": len(complexities),
            "threshold_candidates": threshold_candidates,
            "model_comparison": model_comparison,
            "sensitivity_analysis": sensitivity_results,
            "stability_status": sensitivity_results.get("stability_status", "unknown")
        }
        
        # 7. Write output
        write_threshold_candidates(output_path, final_results)
        
        logger.info(f"Successfully wrote results to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during threshold analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()