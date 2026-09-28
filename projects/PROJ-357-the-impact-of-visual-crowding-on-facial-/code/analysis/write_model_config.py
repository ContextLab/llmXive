"""
Task T037: Generate artifacts/model_config.yaml with hyperparameters, seeds, and model diagnostics.

This script loads the regression results and model configuration (if available),
combines them with the project seed and hyperparameters used for the GLMM fit,
and writes a comprehensive `model_config.yaml` to the artifacts directory.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import yaml
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.glmm_model import load_prepared_data, extract_results
from analysis.reporting import load_regression_results, load_model_config
from config import get_seed, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_model_config(results_path: Path, output_path: Path) -> None:
    """
    Generate the model_config.yaml artifact containing hyperparameters, seeds, and diagnostics.

    Args:
        results_path: Path to the regression_results.json file (T038 artifact).
        output_path: Path where model_config.yaml will be written.
    """
    logger.info(f"Loading regression results from {results_path}")
    
    if not results_path.exists():
        logger.error(f"Results file not found: {results_path}")
        logger.error("This task depends on T038 (regression_results.json) being completed first.")
        raise FileNotFoundError(f"Missing dependency: {results_path}")

    with open(results_path, 'r') as f:
        results_data = json.load(f)

    # Extract key diagnostics from results
    model_diagnostics = {
        "convergence_status": results_data.get("convergence_status", "unknown"),
        "model_type": results_data.get("model_type", "unknown"),
        "fixed_effects": results_data.get("fixed_effects", {}),
        "random_effects_structure": results_data.get("random_effects_structure", {}),
        "fdr_applied": results_data.get("fdr_applied", False),
        "fdr_threshold": results_data.get("fdr_threshold", 0.05),
        "sample_size": results_data.get("sample_size", 0),
        "n_observations": results_data.get("n_observations", 0),
        "n_stimuli": results_data.get("n_stimuli", 0),
        "n_participants": results_data.get("n_participants", 0),
    }

    # Load standard config for seeds and hyperparameters
    seed = get_seed()
    hyperparameters = {
        "random_seed": seed,
        "max_iterations": 1000,
        "convergence_threshold": 1e-6,
        "optimizer": "bfgs",
        "fdr_method": "benjamini_hochberg",
        "fdr_alpha": 0.05,
        "glmm_family": "binomial",
        "glmm_link": "logit",
        "random_effects": ["(1|participant_id)", "(1|stimulus_id)"],
    }

    # Construct the final config structure
    model_config = {
        "project_id": "PROJ-357-the-impact-of-visual-crowding-on-facial-",
        "task_id": "T037",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "hyperparameters": hyperparameters,
        "model_diagnostics": model_diagnostics,
        "data_sources": {
            "stimuli_manifest": "data/interim/stimuli_manifest.json",
            "clutter_metrics": "data/processed/clutter_metrics.csv",
            "human_judgments": "data/processed/human_judgments.csv",
            "regression_results": str(results_path.relative_to(project_root)),
        }
    }

    # Ensure output directory exists
    ensure_directories([output_path.parent])

    # Write to YAML
    with open(output_path, 'w') as f:
        yaml.dump(model_config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Successfully wrote model config to {output_path}")
    return model_config

def main():
    parser = argparse.ArgumentParser(description="Generate model_config.yaml artifact.")
    parser.add_argument(
        "--results", 
        type=str, 
        default="data/processed/regression_results.json",
        help="Path to regression_results.json file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/model_config.yaml",
        help="Path to write model_config.yaml."
    )
    args = parser.parse_args()

    results_path = Path(args.results)
    output_path = Path(args.output)

    # Make paths absolute relative to project root if they aren't already
    if not results_path.is_absolute():
        results_path = project_root / results_path
    if not output_path.is_absolute():
        output_path = project_root / output_path

    try:
        generate_model_config(results_path, output_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error generating model config")
        sys.exit(1)

if __name__ == "__main__":
    main()
