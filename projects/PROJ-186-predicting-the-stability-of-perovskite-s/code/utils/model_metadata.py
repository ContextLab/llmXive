"""
Model metadata management and verification for the Perovskite Stability Pipeline.

This module ensures that all critical model metadata, specifically the DFT functional
used to generate training labels (PBE), is explicitly stored and verifiable.
"""
import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
EXPECTED_DFT_FUNCTIONAL = "PBE"
METADATA_FILENAME = "model_metadata.json"
MODEL_FILENAME = "model.pkl"

def save_model_metadata(
    output_dir: str,
    dft_functional: str = EXPECTED_DFT_FUNCTIONAL,
    model_type: str = "RandomForestRegressor",
    feature_columns: Optional[list] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    training_stats: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save model metadata to a JSON file in the results directory.

    Args:
        output_dir: Directory to save the metadata file.
        dft_functional: The DFT functional used for training labels (e.g., "PBE").
        model_type: The type of scikit-learn model used.
        feature_columns: List of feature names used for training.
        hyperparameters: Dictionary of best hyperparameters found during CV.
        training_stats: Dictionary containing training set size, RMSE, etc.

    Returns:
        Path to the saved metadata file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metadata = {
        "dft_functional": dft_functional,
        "model_type": model_type,
        "feature_columns": feature_columns,
        "hyperparameters": hyperparameters or {},
        "training_stats": training_stats or {},
        "metadata_version": "1.0"
    }

    metadata_file = output_path / METADATA_FILENAME

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved model metadata to {metadata_file}")
    return metadata_file

def load_model_metadata(results_dir: str) -> Dict[str, Any]:
    """
    Load model metadata from the results directory.

    Args:
        results_dir: Directory containing the model metadata file.

    Returns:
        Dictionary containing model metadata.

    Raises:
        FileNotFoundError: If metadata file does not exist.
        json.JSONDecodeError: If metadata file is corrupted.
    """
    metadata_file = Path(results_dir) / METADATA_FILENAME

    if not metadata_file.exists():
        raise FileNotFoundError(f"Model metadata file not found at {metadata_file}")

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    return metadata

def verify_dft_functional(results_dir: str, expected_functional: str = EXPECTED_DFT_FUNCTIONAL) -> bool:
    """
    Verify that the DFT functional in model metadata matches the expected value.

    This is a critical check to ensure the model was trained on data generated
    with the correct DFT functional (PBE), as required by the research specification.

    Args:
        results_dir: Directory containing the model metadata file.
        expected_functional: The expected DFT functional (default: "PBE").

    Returns:
        True if the functional matches, False otherwise.
    """
    try:
        metadata = load_model_metadata(results_dir)
        actual_functional = metadata.get("dft_functional")

        if actual_functional is None:
            logger.error("DFT functional not found in model metadata!")
            return False

        if actual_functional != expected_functional:
            logger.error(
                f"DFT functional mismatch: Expected '{expected_functional}', "
                f"but found '{actual_functional}' in model metadata."
            )
            return False

        logger.info(f"DFT functional verified: '{actual_functional}' matches expected '{expected_functional}'")
        return True

    except FileNotFoundError as e:
        logger.error(f"Cannot verify DFT functional: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Cannot verify DFT functional: Invalid JSON in metadata file - {e}")
        return False

def embed_metadata_in_model(model_path: str, metadata: Dict[str, Any]) -> None:
    """
    Embed metadata directly into the model pickle file (as an attribute).

    This provides a backup mechanism to ensure metadata travels with the model.

    Args:
        model_path: Path to the model pickle file.
        metadata: Dictionary of metadata to embed.
    """
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Add metadata as an attribute to the model object
    if not hasattr(model, 'perovskite_metadata'):
        model.perovskite_metadata = {}
    
    model.perovskite_metadata.update(metadata)

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    logger.info(f"Embedded metadata into model at {model_path}")

def extract_metadata_from_model(model_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract embedded metadata from a model pickle file.

    Args:
        model_path: Path to the model pickle file.

    Returns:
        Dictionary of embedded metadata, or None if not found.
    """
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        if hasattr(model, 'perovskite_metadata'):
            return model.perovskite_metadata
        
        logger.warning(f"No embedded metadata found in model at {model_path}")
        return None

    except Exception as e:
        logger.error(f"Failed to extract metadata from model: {e}")
        return None

def main():
    """
    Main entry point for verifying model metadata.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Verify DFT functional in model metadata")
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory containing model metadata (default: results)"
    )
    parser.add_argument(
        "--expected-functional",
        type=str,
        default=EXPECTED_DFT_FUNCTIONAL,
        help=f"Expected DFT functional (default: {EXPECTED_DFT_FUNCTIONAL})"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.info(f"Verifying DFT functional in {args.results_dir}")
    
    success = verify_dft_functional(args.results_dir, args.expected_functional)
    
    if success:
        logger.info("Verification PASSED: DFT functional is correctly stated as PBE")
        return 0
    else:
        logger.error("Verification FAILED: DFT functional mismatch or missing")
        return 1

if __name__ == "__main__":
    exit(main())
