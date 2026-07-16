import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Import from sibling modules using exact API surface names
from utils.logger import setup_logging, get_logger
from config import TrainingConfig, DataConfig, AnalysisConfig, ensure_dirs

def load_hyperparameter_log(log_path: str) -> List[Dict[str, Any]]:
    """
    Load the hyperparameter search results from a JSON file.
    
    Args:
        log_path: Path to the JSON file containing search results.
        
    Returns:
        List of dictionaries, each containing hyperparameters and metrics.
    """
    logger = get_logger(__name__)
    
    if not os.path.exists(log_path):
        logger.error(f"Hyperparameter log file not found: {log_path}")
        return []
    
    try:
        with open(log_path, 'r') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {log_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading {log_path}: {e}")
        return []

def format_hyperparameter_entry(entry: Dict[str, Any], rank: int) -> str:
    """
    Format a single hyperparameter configuration entry for the log file.
    
    Args:
        entry: Dictionary containing hyperparameters and metrics.
        rank: Rank of this configuration (1-based).
        
    Returns:
        Formatted string representation of the entry.
    """
    lines = []
    lines.append(f"Rank: {rank}")
    lines.append("-" * 40)
    
    # Extract and sort hyperparameters for consistent output
    hyperparams = entry.get('hyperparameters', {})
    metrics = entry.get('metrics', {})
    
    # Sort hyperparameters alphabetically
    for key in sorted(hyperparams.keys()):
        value = hyperparams[key]
        lines.append(f"  {key}: {value}")
    
    lines.append("  Metrics:")
    for key in sorted(metrics.keys()):
        value = metrics[key]
        if isinstance(value, float):
            lines.append(f"    {key}: {value:.6f}")
        else:
            lines.append(f"    {key}: {value}")
    
    lines.append("")
    return "\n".join(lines)

def generate_hyperparameter_log(
    input_path: str,
    output_path: str,
    top_n: int = 10
) -> None:
    """
    Generate a formatted log file of the top N hyperparameter configurations.
    
    Args:
        input_path: Path to the JSON file containing all search results.
        output_path: Path where the formatted log file will be saved.
        top_n: Number of top configurations to include (default: 10).
    """
    logger = get_logger(__name__)
    
    # Load all results
    results = load_hyperparameter_log(input_path)
    
    if not results:
        logger.warning("No hyperparameter results found. Creating empty log file.")
        with open(output_path, 'w') as f:
            f.write("# Hyperparameter Search Log - No Results\n")
        return
    
    # Sort by validation R² (descending)
    sorted_results = sorted(
        results,
        key=lambda x: x.get('metrics', {}).get('val_r2', 0),
        reverse=True
    )
    
    # Select top N
    top_results = sorted_results[:top_n]
    
    # Generate formatted log content
    logger.info(f"Generating log for top {len(top_results)} configurations...")
    
    lines = []
    lines.append(f"# Hyperparameter Search Log - Top {len(top_results)} Configurations")
    lines.append(f"# Generated from: {input_path}")
    lines.append(f"# Sorted by: Validation R² (descending)")
    lines.append("")
    
    for i, entry in enumerate(top_results, 1):
        lines.append(format_hyperparameter_entry(entry, i))
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write("\n".join(lines))
    
    logger.info(f"Hyperparameter log saved to: {output_path}")

def main():
    """Main entry point for the hyperparameter logging script."""
    parser = argparse.ArgumentParser(
        description="Log top hyperparameter configurations and their validation scores."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="artifacts/hyperparameter_search_results.json",
        help="Path to JSON file containing hyperparameter search results"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/hyperparameter_search.log",
        help="Path for the output log file"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top configurations to log (default: 10)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger = get_logger(__name__)
    
    logger.info(f"Starting hyperparameter log generation...")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Top N: {args.top_n}")
    
    # Ensure output directories exist
    ensure_dirs()
    
    # Generate the log
    generate_hyperparameter_log(
        input_path=args.input,
        output_path=args.output,
        top_n=args.top_n
    )
    
    logger.info("Hyperparameter log generation complete.")

if __name__ == "__main__":
    main()
