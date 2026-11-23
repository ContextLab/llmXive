"""
Traceability Logger for the Statistical Power Analysis Pipeline.

This module generates a comprehensive JSON configuration log that documents
the exact pipeline parameters used for a specific analysis run. It explicitly
records that fMRIPrep is NOT used, includes the pipeline configuration hash,
and logs details about ROI masks, smoothing kernels (temporal/spatial), and GLM settings.

Output: results/paper/pipeline_config.json
"""
import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure the project root is in the path for relative imports if run as script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.seed_manager import get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_pipeline_config(
    roi_mask: str,
    temporal_kernel_fwhm: float,
    spatial_kernel_fwhm: float,
    glm_config: Dict[str, Any],
    datasets_used: List[str],
    paradigms_used: List[str],
    smoothing_method: str = "Gaussian",
    boundary_handling: str = "reflect",
    preprocessing_tool: str = "Custom CPU-tractable (NOT fMRIPrep)",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a structured dictionary representing the full pipeline configuration.

    Args:
        roi_mask: Path or name of the ROI mask used (e.g., 'AAL').
        temporal_kernel_fwhm: FWHM for temporal smoothing in seconds.
        spatial_kernel_fwhm: FWHM for spatial smoothing in mm.
        glm_config: Dictionary of GLM parameters (e.g., model type, contrasts).
        datasets_used: List of dataset IDs (e.g., ['ds000030']).
        paradigms_used: List of paradigm names processed.
        smoothing_method: Method used for smoothing (default: Gaussian).
        boundary_handling: Boundary handling strategy for convolution.
        preprocessing_tool: Explicit statement about preprocessing tool.
        notes: Optional additional notes.

    Returns:
        A dictionary containing the full configuration and metadata.
    """
    config = {
        "pipeline_name": "Statistical Power Analysis of Openly Available fMRI Datasets",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "seed": get_seed(),
        "preprocessing": {
            "tool": preprocessing_tool,
            "fmriprep_used": False,
            "roi_mask": roi_mask,
            "temporal_smoothing": {
                "kernel_fwhm_seconds": temporal_kernel_fwhm,
                "method": smoothing_method,
                "boundary_handling": boundary_handling
            },
            "spatial_smoothing": {
                "kernel_fwhm_mm": spatial_kernel_fwhm,
                "method": smoothing_method
            }
        },
        "glm": glm_config,
        "data_sources": {
            "datasets": datasets_used,
            "paradigms": paradigms_used
        },
        "notes": notes
    }

    return config

def compute_full_pipeline_hash(config: Dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 hash of the pipeline configuration.

    This hash serves as a unique identifier for the exact set of parameters
    used, ensuring traceability and reproducibility.

    Args:
        config: The pipeline configuration dictionary.

    Returns:
        A hex string representing the SHA-256 hash.
    """
    # Sort keys to ensure deterministic serialization
    config_str = json.dumps(config, sort_keys=True, separators=(',', ':'))
    hash_object = hashlib.sha256(config_str.encode('utf-8'))
    return hash_object.hexdigest()

def log_pipeline_configuration(
    config: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Log the pipeline configuration to a JSON file.

    Args:
        config: The configuration dictionary (must include 'pipeline_config_hash' if pre-computed,
                or it will be computed and added).
        output_path: Path to the output JSON file. Defaults to results/paper/pipeline_config.json.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        output_path = Path("results/paper/pipeline_config.json")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Compute hash if not present
    if "pipeline_config_hash" not in config:
        config["pipeline_config_hash"] = compute_full_pipeline_hash(config)
        logger.info(f"Computed pipeline_config_hash: {config['pipeline_config_hash']}")
    else:
        logger.info(f"Using existing pipeline_config_hash: {config['pipeline_config_hash']}")

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Pipeline configuration logged to: {output_path}")
    return output_path

def main(args: Optional[List[str]] = None) -> int:
    """
    CLI entry point for the traceability logger.

    Parses arguments, constructs the configuration, computes the hash,
    and writes the JSON output.
    """
    parser = argparse.ArgumentParser(
        description="Log pipeline configuration for traceability."
    )
    parser.add_argument(
        "--roi-mask",
        type=str,
        default="AAL",
        help="Name or path of the ROI mask used."
    )
    parser.add_argument(
        "--temporal-kernel",
        type=float,
        default=4.0,
        help="Temporal smoothing kernel FWHM in seconds."
    )
    parser.add_argument(
        "--spatial-kernel",
        type=float,
        default=4.0,
        help="Spatial smoothing kernel FWHM in mm."
    )
    parser.add_argument(
        "--datasets",
        type=str,
        nargs="+",
        default=["ds000030"],
        help="List of dataset IDs used."
    )
    parser.add_argument(
        "--paradigms",
        type=str,
        nargs="+",
        default=["Motor"],
        help="List of paradigms analyzed."
    )
    parser.add_argument(
        "--glm-model",
        type=str,
        default="OLS",
        help="GLM model type (e.g., OLS, GLS)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/paper/pipeline_config.json",
        help="Output path for the JSON config file."
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Optional notes to include in the config."
    )

    parsed_args = parser.parse_args(args)

    # Construct GLM config
    glm_config = {
        "model_type": parsed_args.glm_model,
        "standardize": True,
        "drift_model": "cosine",
        "high_pass": 128.0,
        "noise_model": "ar1"
    }

    # Create configuration
    config = create_pipeline_config(
        roi_mask=parsed_args.roi_mask,
        temporal_kernel_fwhm=parsed_args.temporal_kernel,
        spatial_kernel_fwhm=parsed_args.spatial_kernel,
        glm_config=glm_config,
        datasets_used=parsed_args.datasets,
        paradigms_used=parsed_args.paradigms,
        notes=parsed_args.notes
    )

    # Log configuration
    output_path = Path(parsed_args.output)
    log_pipeline_configuration(config, output_path)

    return 0

if __name__ == "__main__":
    sys.exit(main())