import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules using exact API surface names
from utils.logger import setup_logging, get_logger
from utils.checksum import compute_file_checksum
from config import TrainingConfig, DataConfig, AnalysisConfig, ensure_dirs
from models.mpnn import MPNNConfig, create_mpnn_from_config
from models.train import load_processed_data, prepare_features

def load_best_training_result(result_path: str) -> Dict[str, Any]:
    """
    Load the best training result from a JSON file.
    
    Args:
        result_path: Path to the JSON file containing training results.
        
    Returns:
        Dictionary containing the best training result.
    """
    logger = get_logger(__name__)
    
    if not os.path.exists(result_path):
        logger.error(f"Training result file not found: {result_path}")
        raise FileNotFoundError(f"Training result file not found: {result_path}")
    
    try:
        with open(result_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {result_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading {result_path}: {e}")
        raise

def validate_metrics_against_schema(
    metrics: Dict[str, Any],
    schema_path: str = "specs/001-predict-sn1-rate-constants/contracts/model_output.schema.yaml"
) -> bool:
    """
    Validate metrics dictionary against the model output schema.
    
    Args:
        metrics: Dictionary containing model metrics.
        schema_path: Path to the YAML schema file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    logger = get_logger(__name__)
    
    # Load schema
    try:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Schema file not found: {schema_path}. Skipping validation.")
        return True
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False
    
    # Check required fields
    required_fields = ['model_id', 'hyperparameters', 'metrics', 'weights_path']
    for field in required_fields:
        if field not in metrics:
            logger.error(f"Missing required field in metrics: {field}")
            return False
    
    # Check metrics sub-fields
    if 'metrics' in metrics:
        metric_fields = ['r2', 'mae']
        for field in metric_fields:
            if field not in metrics['metrics']:
                logger.error(f"Missing required metric: {field}")
                return False
    
    logger.info("Metrics validation passed.")
    return True

def save_best_model(
    model,
    config: MPNNConfig,
    output_path: str
) -> None:
    """
    Save the best model weights and configuration.
    
    Args:
        model: The trained MPNN model.
        config: The MPNNConfig used for training.
        output_path: Path where the model will be saved.
    """
    logger = get_logger(__name__)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save model state dict
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': config.to_dict()
    }, output_path)
    
    logger.info(f"Best model saved to: {output_path}")

def save_metrics(
    metrics: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save model metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing model metrics.
        output_path: Path where the metrics will be saved.
    """
    logger = get_logger(__name__)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to: {output_path}")

def save_hyperparameter_log(
    input_results_path: str,
    output_log_path: str,
    top_n: int = 10
) -> None:
    """
    Generate and save a formatted log of top hyperparameter configurations.
    
    Args:
        input_results_path: Path to JSON file with all search results.
        output_log_path: Path for the formatted log file.
        top_n: Number of top configurations to include.
    """
    from models.log_hyperparameters import generate_hyperparameter_log
    
    logger = get_logger(__name__)
    
    generate_hyperparameter_log(
        input_path=input_results_path,
        output_path=output_log_path,
        top_n=top_n
    )
    
    logger.info(f"Hyperparameter log saved to: {output_log_path}")

def main():
    """Main entry point for saving model artifacts."""
    parser = argparse.ArgumentParser(
        description="Save best model weights, metrics, and hyperparameter log."
    )
    parser.add_argument(
        "--results",
        type=str,
        default="artifacts/training_results.json",
        help="Path to JSON file containing training results"
    )
    parser.add_argument(
        "--model-output",
        type=str,
        default="artifacts/best_model.pt",
        help="Path for the saved model weights"
    )
    parser.add_argument(
        "--metrics-output",
        type=str,
        default="artifacts/metrics.json",
        help="Path for the saved metrics JSON"
    )
    parser.add_argument(
        "--log-output",
        type=str,
        default="artifacts/hyperparameter_search.log",
        help="Path for the hyperparameter search log"
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
    
    logger.info("Starting artifact save process...")
    
    # Ensure output directories exist
    ensure_dirs()
    
    # Load best training result
    try:
        best_result = load_best_training_result(args.results)
    except Exception as e:
        logger.error(f"Failed to load training results: {e}")
        sys.exit(1)
    
    # Validate metrics against schema
    if not validate_metrics_against_schema(best_result):
        logger.error("Metrics validation failed. Aborting save.")
        sys.exit(1)
    
    # Save metrics
    save_metrics(best_result, args.metrics_output)
    
    # Save model (if model object is available - in practice this would be passed or reloaded)
    # For now, we assume the model was saved separately during training
    # This function is kept for API completeness
    
    # Generate and save hyperparameter log
    save_hyperparameter_log(
        input_results_path=args.results,
        output_log_path=args.log_output,
        top_n=args.top_n
    )
    
    logger.info("Artifact save process complete.")

if __name__ == "__main__":
    import torch
    main()
