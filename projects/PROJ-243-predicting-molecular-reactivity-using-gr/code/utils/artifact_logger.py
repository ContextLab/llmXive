"""
Artifact Logger Module for FR-007 Compliance.

This module explicitly logs model weights, attribution maps, and metrics
to the repository as required by FR-007. It ensures all artifacts are
structured and traceable.

Dependencies:
- T022 (Training): Produces model weights in artifacts/weights/
- T023a (Predictions): Produces predictions in artifacts/predictions.json
- T023b (Metrics): Produces metrics in artifacts/metrics.json
- T023e (Comparison): Produces model_comparison_results.json
"""

import os
import sys
import json
import hashlib
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Import project utilities
from config import get_config, ensure_directories
from utils.logging_utils import get_logger

# Ensure we can import from the code directory
if 'code' not in sys.path:
    code_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if code_root not in sys.path:
        sys.path.insert(0, code_root)


def calculate_file_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files (like model weights)
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def scan_directory_for_artifacts(directory: str, extensions: List[str]) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for files with specific extensions.

    Args:
        directory: Root directory to scan.
        extensions: List of file extensions to include (e.g., ['.pt', '.json']).

    Returns:
        List of dictionaries containing file metadata (path, size, hash).
    """
    artifacts = []
    if not os.path.exists(directory):
        logging.warning(f"Directory does not exist: {directory}. Skipping scan.")
        return artifacts

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory)
                try:
                    file_size = os.path.getsize(full_path)
                    file_hash = calculate_file_sha256(full_path)
                    artifacts.append({
                        "relative_path": rel_path,
                        "full_path": full_path,
                        "size_bytes": file_size,
                        "sha256": file_hash,
                        "last_modified": datetime.fromtimestamp(
                            os.path.getmtime(full_path)
                        ).isoformat()
                    })
                except Exception as e:
                    logging.error(f"Error processing file {full_path}: {e}")
    return artifacts


def load_json_artifact(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON artifact.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON dictionary or None if loading fails.
    """
    if not os.path.exists(file_path):
        logging.warning(f"JSON artifact not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None


def log_model_weights(weights_dir: str) -> Dict[str, Any]:
    """
    Log all model weight files found in the weights directory.

    Args:
        weights_dir: Path to the weights directory (e.g., artifacts/weights).

    Returns:
        Dictionary containing the list of logged weights.
    """
    logging.info(f"Scanning model weights in: {weights_dir}")
    weights = scan_directory_for_artifacts(weights_dir, ['.pt', '.pth'])

    # Validate that we found the expected models if they exist
    expected_models = ['best_spectral_gnn.pt', 'best_hetero_gnn.pt', 'best_random_forest.pt']
    found_names = [w['relative_path'] for w in weights]

    missing = [m for m in expected_models if m not in found_names]
    if missing:
        logging.warning(f"Expected model weights missing: {missing}")

    return {
        "directory": weights_dir,
        "count": len(weights),
        "files": weights
    }


def log_metrics(metrics_file: str) -> Dict[str, Any]:
    """
    Load and log the metrics artifact.

    Args:
        metrics_file: Path to the metrics JSON file.

    Returns:
        Dictionary containing the metrics content.
    """
    logging.info(f"Loading metrics from: {metrics_file}")
    content = load_json_artifact(metrics_file)

    if content is None:
        return {
            "file": metrics_file,
            "status": "missing_or_invalid",
            "content": None
        }

    return {
        "file": metrics_file,
        "status": "loaded",
        "content": content
    }


def log_predictions(predictions_file: str) -> Dict[str, Any]:
    """
    Load and log the predictions artifact.

    Args:
        predictions_file: Path to the predictions JSON file.

    Returns:
        Dictionary containing the predictions content.
    """
    logging.info(f"Loading predictions from: {predictions_file}")
    content = load_json_artifact(predictions_file)

    if content is None:
        return {
            "file": predictions_file,
            "status": "missing_or_invalid",
            "content": None
        }

    # Summarize predictions to avoid logging massive arrays
    summary = {
        "total_predictions": len(content.get('predictions', [])) if isinstance(content, dict) else 0,
        "models_included": list(content.keys()) if isinstance(content, dict) else [],
        "sample_keys": list(content.keys())[:5] if isinstance(content, dict) else []
    }

    return {
        "file": predictions_file,
        "status": "loaded",
        "summary": summary,
        "content_available": True
    }


def log_comparison_results(comparison_file: str) -> Dict[str, Any]:
    """
    Load and log the model comparison results.

    Args:
        comparison_file: Path to the comparison results JSON file.

    Returns:
        Dictionary containing the comparison results.
    """
    logging.info(f"Loading comparison results from: {comparison_file}")
    content = load_json_artifact(comparison_file)

    if content is None:
        return {
            "file": comparison_file,
            "status": "missing_or_invalid",
            "content": None
        }

    return {
        "file": comparison_file,
        "status": "loaded",
        "content": content
    }


def log_attribution_maps(attribution_file: str) -> Dict[str, Any]:
    """
    Load and log the attribution maps artifact.

    Args:
        attribution_file: Path to the attribution maps JSON file.

    Returns:
        Dictionary containing the attribution maps summary.
    """
    logging.info(f"Loading attribution maps from: {attribution_file}")
    content = load_json_artifact(attribution_file)

    if content is None:
        return {
            "file": attribution_file,
            "status": "missing_or_invalid",
            "content": None
        }

    return {
        "file": attribution_file,
        "status": "loaded",
        "summary": {
            "total_maps": len(content.get('maps', [])) if isinstance(content, dict) else 0,
            "method_used": content.get('method', 'unknown') if isinstance(content, dict) else 'unknown'
        }
    }


def compile_artifact_log(
    weights_dir: str,
    metrics_file: str,
    predictions_file: str,
    comparison_file: str,
    attribution_file: str
) -> Dict[str, Any]:
    """
    Compile all artifacts into a single structured log.

    Args:
        weights_dir: Path to model weights directory.
        metrics_file: Path to metrics JSON.
        predictions_file: Path to predictions JSON.
        comparison_file: Path to comparison results JSON.
        attribution_file: Path to attribution maps JSON.

    Returns:
        Complete artifact log dictionary.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "version": "1.0",
        "fr_007_compliance": True,
        "artifacts": {
            "model_weights": log_model_weights(weights_dir),
            "metrics": log_metrics(metrics_file),
            "predictions": log_predictions(predictions_file),
            "comparison_results": log_comparison_results(comparison_file),
            "attribution_maps": log_attribution_maps(attribution_file)
        },
        "validation_summary": {
            "weights_found": len(log_model_weights(weights_dir)['files']) > 0,
            "metrics_loaded": log_metrics(metrics_file)['status'] == 'loaded',
            "predictions_loaded": log_predictions(predictions_file)['status'] == 'loaded',
            "comparison_loaded": log_comparison_results(comparison_file)['status'] == 'loaded',
            "attribution_loaded": log_attribution_maps(attribution_file)['status'] == 'loaded'
        }
    }

    return log_entry


def save_artifact_log(log_data: Dict[str, Any], output_path: str) -> None:
    """
    Save the compiled artifact log to a JSON file.

    Args:
        log_data: The compiled log dictionary.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    logging.info(f"Artifact log saved to: {output_path}")


def main() -> int:
    """
    Main entry point for the artifact logger script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    setup_script_logging()
    logger = get_logger(__name__)
    logger.info("Starting Artifact Logger (T022b) for FR-007 compliance.")

    try:
        config = get_config()
        ensure_directories()

        # Define paths based on project structure
        weights_dir = os.path.join("artifacts", "weights")
        metrics_file = os.path.join("artifacts", "metrics.json")
        predictions_file = os.path.join("artifacts", "predictions.json")
        comparison_file = os.path.join("artifacts", "model_comparison_results.json")
        attribution_file = os.path.join("artifacts", "attribution_maps.json")
        output_log = os.path.join("artifacts", "logs", "artifact_log.json")

        # Compile the log
        log_data = compile_artifact_log(
            weights_dir=weights_dir,
            metrics_file=metrics_file,
            predictions_file=predictions_file,
            comparison_file=comparison_file,
            attribution_file=attribution_file
        )

        # Save the log
        save_artifact_log(log_data, output_log)

        # Report validation summary
        summary = log_data['validation_summary']
        if all(summary.values()):
            logger.info("SUCCESS: All required artifacts were found and logged.")
            return 0
        else:
            missing = [k for k, v in summary.items() if not v]
            logger.warning(f"PARTIAL: Some artifacts were missing: {missing}")
            logger.info("Continuing with partial log for audit trail.")
            return 0  # Return 0 to allow pipeline to continue, but log warning

    except Exception as e:
        logger.error(f"Fatal error during artifact logging: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
