"""
Threshold calculation module for network topology construction.

This module calculates the edge threshold distance for graph construction
based on material-specific lattice constants and configuration settings.

Dependencies:
    - T005: Configuration management (config.yaml with statistical_override)
    - T009: Material constants lookup (src/data/materials.py)
"""

import logging
from typing import Optional, Union, Dict, Any

from src.config import get_config, ConfigError
from src.data.materials import get_lattice_constant, get_material_constants
from src.logging_config import get_data_ingestion_logger

logger = get_data_ingestion_logger(__name__)

DEFAULT_THRESHOLD_NM = 2.0
DEFAULT_MULTIPLIER = 2.0


class ThresholdCalculationError(Exception):
    """Raised when threshold calculation fails due to missing data or config."""
    pass


def calculate_threshold(
    material: str,
    config_path: Optional[str] = None,
    statistical_multiplier: Optional[float] = None
) -> float:
    """
    Calculate the edge threshold distance for graph construction.

    The threshold is determined by:
    1. Retrieving the material-specific lattice constant (from T009)
    2. Checking the config for a statistical_override flag (from T005)
    3. If statistical_override is active, apply the multiplier to the lattice constant
    4. Otherwise, return the fixed default threshold (2.0 nm)

    Args:
        material: Name of the material (e.g., 'graphene', 'MoS2')
        config_path: Optional path to config.yaml. If None, uses default location.
        statistical_multiplier: Optional override for the multiplier. If None,
            reads from config or uses DEFAULT_MULTIPLIER.

    Returns:
        float: Threshold distance in nanometers.

    Raises:
        ThresholdCalculationError: If material is not found or config is invalid.
        ConfigError: If configuration loading fails.

    Example:
        >>> # For graphene with statistical_override=True and multiplier=2.5
        >>> threshold = calculate_threshold('graphene', config_path='config.yaml')
        >>> # Returns: lattice_constant * 2.5
    """
    # Load configuration
    try:
        config = get_config(config_path)
    except ConfigError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise ThresholdCalculationError(f"Configuration error: {e}")

    # Check if statistical override is active
    statistical_override = config.get('statistical_override', False)

    # Determine multiplier
    if statistical_multiplier is not None:
        multiplier = statistical_multiplier
    elif statistical_override:
        multiplier = config.get('statistical_multiplier', DEFAULT_MULTIPLIER)
    else:
        multiplier = None

    # Retrieve material lattice constant
    try:
        lattice_constant = get_lattice_constant(material)
    except ValueError as e:
        error_msg = f"Material '{material}' not found in materials database: {e}"
        logger.error(error_msg)
        raise ThresholdCalculationError(error_msg)

    # Calculate threshold
    if statistical_override and multiplier is not None:
        threshold = lattice_constant * multiplier
        logger.info(
            f"[US1] Calculated statistical threshold for {material}: "
            f"lattice_constant={lattice_constant:.4f} nm * multiplier={multiplier} = {threshold:.4f} nm"
        )
    else:
        threshold = DEFAULT_THRESHOLD_NM
        logger.info(
            f"[US1] Using fixed threshold for {material}: {threshold:.4f} nm "
            f"(statistical_override={statistical_override})"
        )

    return threshold


def get_threshold_config() -> Dict[str, Any]:
    """
    Retrieve threshold-related configuration settings.

    Returns:
        dict: Configuration dictionary containing:
            - statistical_override (bool)
            - statistical_multiplier (float)
            - default_threshold (float)
    """
    try:
        config = get_config()
    except ConfigError:
        # Return defaults if config fails
        return {
            'statistical_override': False,
            'statistical_multiplier': DEFAULT_MULTIPLIER,
            'default_threshold': DEFAULT_THRESHOLD_NM
        }

    return {
        'statistical_override': config.get('statistical_override', False),
        'statistical_multiplier': config.get('statistical_multiplier', DEFAULT_MULTIPLIER),
        'default_threshold': DEFAULT_THRESHOLD_NM
    }


def main():
    """
    CLI entry point for threshold calculation testing.

    Usage:
        python -m src.data_ingestion.threshold [--material GRAPHENE] [--config CONFIG_PATH]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate edge threshold for network graph construction'
    )
    parser.add_argument(
        '--material', '-m',
        type=str,
        default='graphene',
        help='Material name (default: graphene)'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Path to config.yaml (default: uses default location)'
    )
    parser.add_argument(
        '--multiplier',
        type=float,
        default=None,
        help='Override statistical multiplier (optional)'
    )

    args = parser.parse_args()

    try:
        threshold = calculate_threshold(
            material=args.material,
            config_path=args.config,
            statistical_multiplier=args.multiplier
        )
        print(f"Calculated threshold for {args.material}: {threshold:.4f} nm")
    except ThresholdCalculationError as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == '__main__':
    main()