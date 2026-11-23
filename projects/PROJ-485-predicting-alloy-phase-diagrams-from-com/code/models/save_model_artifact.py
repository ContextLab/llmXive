"""
Save trained model artifact with version hash and state update.
Implements T029: Save trained model artifact to data/artifacts/model.pkl with version hash.
Verification: Assert file exists and hash is recorded in state.
"""
import os
import sys
import pickle
import json
import hashlib
import argparse
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.checksum import compute_file_sha256
from main import load_state, save_state, update_step_status

logger = get_logger(__name__)

def load_training_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load training configuration from YAML file."""
    import yaml
    if not os.path.exists(config_path):
        log_error(logger, f"Config file not found: {config_path}", "CONFIG_MISSING")
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_evaluation_report(report_path: str = "data/artifacts/evaluation_report.json") -> Dict[str, Any]:
    """Load evaluation report from JSON file."""
    if not os.path.exists(report_path):
        log_error(logger, f"Evaluation report not found: {report_path}", "REPORT_MISSING")
        return {}
    
    with open(report_path, 'r') as f:
        return json.load(f)

def compute_version_hash(model_path: str, evaluation_report: Dict[str, Any]) -> str:
    """
    Compute a version hash based on model checksum and key evaluation metrics.
    This ensures reproducibility and version tracking (Constitution Principle V).
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Get file checksum
    file_hash = compute_file_sha256(model_path)
    
    # Include key metrics in hash for versioning
    metrics_str = json.dumps(
        {
            'mae': evaluation_report.get('aggregate_mae', 'N/A'),
            'r2': evaluation_report.get('aggregate_r2', 'N/A'),
            'power': evaluation_report.get('power_analysis', {}).get('power', 'N/A')
        },
        sort_keys=True
    )
    
    # Combine file hash and metrics
    combined = f"{file_hash}:{metrics_str}"
    version_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    
    return version_hash

def save_model_artifact(
    model: Any,
    output_path: str,
    evaluation_report: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """
    Save model artifact with metadata and compute version hash.
    
    Args:
        model: Trained model object (e.g., RandomForestRegressor)
        output_path: Path to save the pickle file
        evaluation_report: Dictionary containing evaluation metrics
        config: Training configuration dictionary
        
    Returns:
        str: Version hash of the saved artifact
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create artifact metadata
    artifact_metadata = {
        'version_hash': '',  # Will be updated after save
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'config_snapshot': {
            'model_type': config.get('model_type', 'random_forest'),
            'n_estimators': config.get('n_estimators', 100),
            'max_depth': config.get('max_depth', None)
        },
        'evaluation_summary': {
            'mae': evaluation_report.get('aggregate_mae'),
            'r2': evaluation_report.get('aggregate_r2'),
            'power': evaluation_report.get('power_analysis', {}).get('power')
        }
    }
    
    # Save model and metadata together
    artifact_data = {
        'model': model,
        'metadata': artifact_metadata
    }
    
    with open(output_path, 'wb') as f:
        pickle.dump(artifact_data, f)
    
    log_info(logger, f"Model artifact saved to {output_path}")
    
    # Compute version hash after saving
    version_hash = compute_version_hash(output_path, evaluation_report)
    
    # Update metadata with version hash
    artifact_metadata['version_hash'] = version_hash
    
    # Rewrite with updated metadata
    artifact_data['metadata'] = artifact_metadata
    with open(output_path, 'wb') as f:
        pickle.dump(artifact_data, f)
    
    log_info(logger, f"Version hash computed: {version_hash}")
    
    return version_hash

def load_model_artifact(model_path: str) -> tuple:
    """
    Load model artifact and return model and metadata.
    
    Args:
        model_path: Path to the pickle file
        
    Returns:
        tuple: (model, metadata_dict)
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        artifact_data = pickle.load(f)
    
    return artifact_data['model'], artifact_data['metadata']

def main():
    """Main entry point for saving model artifact."""
    parser = argparse.ArgumentParser(description='Save trained model artifact with version hash')
    parser.add_argument('--model-path', type=str, 
                      default='data/processed/trained_model.pkl',
                      help='Path to the trained model pickle file')
    parser.add_argument('--output-path', type=str,
                      default='data/artifacts/model.pkl',
                      help='Path to save the final model artifact')
    parser.add_argument('--report-path', type=str,
                      default='data/artifacts/evaluation_report.json',
                      help='Path to evaluation report JSON')
    parser.add_argument('--config-path', type=str,
                      default='code/config.yaml',
                      help='Path to configuration YAML')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        log_info(logger, "Loading configuration...")
        config = load_training_config(args.config_path)
        
        # Load evaluation report
        log_info(logger, "Loading evaluation report...")
        evaluation_report = load_evaluation_report(args.report_path)
        
        if not evaluation_report:
            log_error(logger, "Failed to load evaluation report", "REPORT_MISSING")
            sys.exit(1)
        
        # Load the trained model (from intermediate save)
        log_info(logger, f"Loading trained model from {args.model_path}...")
        if not os.path.exists(args.model_path):
            log_error(logger, f"Trained model not found: {args.model_path}", "MODEL_MISSING")
            sys.exit(1)
        
        with open(args.model_path, 'rb') as f:
            model_data = pickle.load(f)
            # Handle both direct model and wrapped model formats
            if isinstance(model_data, dict) and 'model' in model_data:
                model = model_data['model']
            else:
                model = model_data
        
        # Save model artifact with version hash
        log_info(logger, "Saving model artifact with version hash...")
        version_hash = save_model_artifact(
            model=model,
            output_path=args.output_path,
            evaluation_report=evaluation_report,
            config=config
        )
        
        # Update state with artifact hash
        log_info(logger, "Updating project state...")
        state = load_state()
        update_step_status(state, 'T029', 'completed', {
            'artifact_path': args.output_path,
            'version_hash': version_hash,
            'file_size_bytes': os.path.getsize(args.output_path)
        })
        save_state(state)
        
        log_info(logger, f"Model artifact successfully saved: {args.output_path}")
        log_info(logger, f"Version hash: {version_hash}")
        
        # Verify file exists
        if os.path.exists(args.output_path):
            log_info(logger, "Verification: Model artifact file exists")
        else:
            log_error(logger, "Verification failed: Model artifact file not found", "FILE_NOT_FOUND")
            sys.exit(1)
        
    except Exception as e:
        log_error(logger, f"Error saving model artifact: {str(e)}", "SAVE_MODEL_FAILED")
        import traceback
        log_error(logger, traceback.format_exc(), "STACK_TRACE")
        sys.exit(1)

if __name__ == "__main__":
    main()