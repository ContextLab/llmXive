"""
Model Output Module for T027.

Saves individual alpha parameters and group-level hyperparameters to data/models/
for valid participants only (input filtered by T028).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np

# Import from existing project API surface
from utils.io import ensure_dir, save_json, load_json, IOLoadError, IOSaveError
from utils.logger import get_logger
from utils.config import get_config
from modeling.convergence_reporter import load_valid_participants, ConvergenceReportError

# Configure logger
logger = get_logger(__name__)


class ModelOutputError(Exception):
    """Custom exception for model output generation errors."""
    pass


def load_posterior_samples(posterior_path: Path) -> Dict[str, Any]:
    """
    Load posterior samples from the belief updater results.

    Args:
        posterior_path: Path to the posterior samples JSON file.

    Returns:
        Dictionary containing posterior samples and metadata.

    Raises:
        ModelOutputError: If the file cannot be loaded or is malformed.
    """
    if not posterior_path.exists():
        raise ModelOutputError(f"Posterior samples file not found: {posterior_path}")

    try:
        data = load_json(posterior_path)
        logger.info(f"Loaded posterior samples from {posterior_path}")
        return data
    except Exception as e:
        raise ModelOutputError(f"Failed to load posterior samples: {e}")


def extract_individual_alphas(posterior_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract individual alpha parameters from posterior samples.

    Args:
        posterior_data: Dictionary containing posterior samples.

    Returns:
        Dictionary mapping participant_id to alpha value.
    """
    individual_alphas = {}

    # Expected structure: {'participants': {'p01': {'alpha': [samples]}, ...}}
    participants = posterior_data.get('participants', {})

    for pid, pdata in participants.items():
        if 'alpha' in pdata:
            # Take the mean of the posterior samples as the point estimate
            alpha_samples = np.array(pdata['alpha'])
            alpha_mean = float(np.mean(alpha_samples))
            individual_alphas[pid] = alpha_mean
            logger.debug(f"Extracted alpha={alpha_mean:.4f} for participant {pid}")
        else:
            logger.warning(f"Participant {pid} missing 'alpha' in posterior data")

    return individual_alphas


def extract_group_hyperparameters(posterior_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract group-level hyperparameters from posterior samples.

    Args:
        posterior_data: Dictionary containing posterior samples.

    Returns:
        Dictionary containing group-level hyperparameter estimates.
    """
    group_params = {}

    # Expected structure: {'group_params': {'mu_alpha': [samples], 'sigma_alpha': [samples]}}
    group_data = posterior_data.get('group_params', {})

    for param_name, samples in group_data.items():
        samples_array = np.array(samples)
        group_params[param_name] = {
            'mean': float(np.mean(samples_array)),
            'std': float(np.std(samples_array)),
            'median': float(np.median(samples_array)),
            'ci_95_lower': float(np.percentile(samples_array, 2.5)),
            'ci_95_upper': float(np.percentile(samples_array, 97.5))
        }
        logger.debug(f"Extracted group {param_name}: mean={group_params[param_name]['mean']:.4f}")

    return group_params


def save_model_output(
    individual_alphas: Dict[str, float],
    group_hyperparameters: Dict[str, Any],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save model output to a JSON file.

    Args:
        individual_alphas: Dictionary mapping participant_id to alpha value.
        group_hyperparameters: Dictionary containing group-level hyperparameters.
        output_path: Path where the output file will be saved.
        metadata: Optional metadata to include in the output.

    Returns:
        Path to the saved file.

    Raises:
        IOSaveError: If the file cannot be saved.
    """
    ensure_dir(output_path.parent)

    output_data = {
        'metadata': metadata or {},
        'individual_alphas': individual_alphas,
        'group_hyperparameters': group_hyperparameters,
        'summary': {
            'n_participants': len(individual_alphas),
            'alpha_mean': float(np.mean(list(individual_alphas.values()))) if individual_alphas else None,
            'alpha_std': float(np.std(list(individual_alphas.values()))) if individual_alphas else None
        }
    }

    try:
        save_json(output_path, output_data)
        logger.info(f"Saved model output to {output_path}")
        return output_path
    except Exception as e:
        raise IOSaveError(f"Failed to save model output: {e}")


def generate_model_output(
    valid_participants: List[str],
    posterior_path: Path,
    output_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Generate model output for valid participants only.

    Args:
        valid_participants: List of participant IDs that passed convergence checks.
        posterior_path: Path to the posterior samples file from belief_updater.
        output_dir: Directory where output will be saved.
        config: Optional configuration dictionary.

    Returns:
        Path to the saved output file.

    Raises:
        ModelOutputError: If generation fails.
    """
    # Load posterior samples
    posterior_data = load_posterior_samples(posterior_path)

    # Extract all individual alphas
    all_alphas = extract_individual_alphas(posterior_data)

    # Filter to valid participants only
    filtered_alphas = {
        pid: alpha for pid, alpha in all_alphas.items()
        if pid in valid_participants
    }

    if not filtered_alphas:
        logger.warning("No valid participants found for model output generation")
        raise ModelOutputError("No valid participants to generate output for")

    # Extract group hyperparameters
    group_hyperparameters = extract_group_hyperparameters(posterior_data)

    # Prepare metadata
    metadata = {
        'source_posterior': str(posterior_path),
        'valid_participants': valid_participants,
        'n_valid_participants': len(valid_participants),
        'config': config or {}
    }

    # Define output path
    output_filename = "model_parameters.json"
    output_path = output_dir / output_filename

    # Save output
    save_model_output(filtered_alphas, group_hyperparameters, output_path, metadata)

    return output_path


def main():
    """
    Main entry point for generating model output.

    Usage:
        python -m code.modeling.model_output [--posterior POSTERIOR_PATH]
                                             [--output-dir OUTPUT_DIR]
                                             [--config CONFIG_PATH]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate model output for valid participants'
    )
    parser.add_argument(
        '--posterior',
        type=Path,
        default=Path('data/models/posterior_samples.json'),
        help='Path to posterior samples file'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/models'),
        help='Directory to save output'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=None,
        help='Path to config file (optional)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Load config if provided
    config = None
    if args.config and args.config.exists():
        config = load_json(args.config)
        logger.info(f"Loaded config from {args.config}")

    try:
        # Load valid participants from convergence reporter
        valid_participants = load_valid_participants()

        if not valid_participants:
            logger.error("No valid participants found. Check convergence report.")
            sys.exit(1)

        logger.info(f"Processing {len(valid_participants)} valid participants")

        # Generate model output
        output_path = generate_model_output(
            valid_participants=valid_participants,
            posterior_path=args.posterior,
            output_dir=args.output_dir,
            config=config
        )

        logger.info(f"Model output saved to {output_path}")
        print(f"SUCCESS: Model output generated at {output_path}")

    except ConvergenceReportError as e:
        logger.error(f"Convergence report error: {e}")
        sys.exit(1)
    except ModelOutputError as e:
        logger.error(f"Model output error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()