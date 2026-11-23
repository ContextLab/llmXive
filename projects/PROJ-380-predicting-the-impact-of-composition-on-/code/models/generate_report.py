import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_paths
from utils.provenance import record_artifact

logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_model_report(
    metrics: Dict[str, float],
    hyperparameters: Dict[str, Any],
    statistical_test: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate the model report JSON file matching contracts/model_output.schema.yaml.
    
    Args:
        metrics: Dictionary with keys R2, MAE, RMSE (floats)
        hyperparameters: Dictionary of best hyperparameters found during grid search
        statistical_test: Dictionary with keys method (str), p_value (float), 
                         confidence_interval (list[float])
        output_path: Path where the report will be saved
    """
    # Validate required fields
    required_metrics = ['R2', 'MAE', 'RMSE']
    for key in required_metrics:
        if key not in metrics:
            raise ValueError(f"Missing required metric: {key}")
        if not isinstance(metrics[key], (int, float)):
            raise TypeError(f"Metric {key} must be a float, got {type(metrics[key])}")

    if 'method' not in statistical_test or 'p_value' not in statistical_test or 'confidence_interval' not in statistical_test:
        raise ValueError("statistical_test must contain 'method', 'p_value', and 'confidence_interval'")

    if not isinstance(statistical_test['confidence_interval'], list) or len(statistical_test['confidence_interval']) != 2:
        raise ValueError("confidence_interval must be a list of two floats")

    report = {
        "metrics": {
            "R2": float(metrics['R2']),
            "MAE": float(metrics['MAE']),
            "RMSE": float(metrics['RMSE'])
        },
        "hyperparameters": hyperparameters,
        "statistical_test": {
            "method": str(statistical_test['method']),
            "p_value": float(statistical_test['p_value']),
            "confidence_interval": [float(x) for x in statistical_test['confidence_interval']]
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Model report saved to: {output_path}")

def main():
    """
    Main entry point to generate the model report.
    
    This script is intended to be run after T026 (grid search) and T027 (statistical comparison)
    have completed and produced their respective output files.
    
    Expected inputs (from previous tasks):
    - data/processed/model_metrics.json: Contains R2, MAE, RMSE
    - data/processed/best_hyperparameters.json: Contains best hyperparameters
    - data/processed/statistical_test_results.json: Contains test method, p-value, CI
    
    Output:
    - artifacts/model_report.json: Final report matching the schema
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    paths = get_paths()
    artifacts_dir = paths['artifacts']
    
    # Define input paths (produced by T026 and T027)
    metrics_path = paths['processed'] / 'model_metrics.json'
    hyperparams_path = paths['processed'] / 'best_hyperparameters.json'
    stats_path = paths['processed'] / 'statistical_test_results.json'
    
    output_path = artifacts_dir / 'model_report.json'

    try:
        # Load inputs
        logger.info(f"Loading metrics from {metrics_path}")
        metrics = load_json_file(metrics_path)
        
        logger.info(f"Loading hyperparameters from {hyperparams_path}")
        hyperparameters = load_json_file(hyperparams_path)
        
        logger.info(f"Loading statistical test results from {stats_path}")
        statistical_test = load_json_file(stats_path)

        # Generate report
        generate_model_report(metrics, hyperparameters, statistical_test, output_path)

        # Record provenance
        record_artifact(output_path, paths['state'])
        
        logger.info("Task T029 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        logger.error("Ensure T026 and T027 have completed successfully.")
        sys.exit(1)
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Invalid data format in input files: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
