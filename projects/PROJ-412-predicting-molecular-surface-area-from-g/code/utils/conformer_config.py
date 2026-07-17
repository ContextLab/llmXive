"""
Conformer configuration generator for molecular surface area prediction pipeline.

This module generates a JSON configuration file for RDKit conformer generation,
tuned for accurate 3D structure optimization required for SASA calculations.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .config import get_project_root, get_data_dir
from .logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def generate_conformer_config(
    output_path: Optional[str] = None,
    max_iterations: int = 500,
    energy_tolerance: float = 1e-4,
    num_conformers: int = 10,
    use_explicit_hydrogens: bool = True,
    mmff_variant: str = "MMFF94",
    optimize_steps: int = 200
) -> str:
    """
    Generate a JSON configuration file for RDKit conformer generation.

    Args:
        output_path: Path to write the JSON config. Defaults to
                     'data/raw/conformer_config.json' within project root.
        max_iterations: Maximum number of iterations for ETKDG optimization.
        energy_tolerance: Energy tolerance for convergence (kcal/mol).
        num_conformers: Number of conformers to generate per molecule.
        use_explicit_hydrogens: Whether to add explicit hydrogens before optimization.
        mmff_variant: MMFF force field variant ('MMFF94', 'MMFF94s', 'UFF').
        optimize_steps: Maximum optimization steps for MMFF minimization.

    Returns:
        str: The absolute path to the generated configuration file.

    Raises:
        ValueError: If the specified MMFF variant is unsupported.
        IOError: If the config file cannot be written.
    """
    supported_mmff = {"MMFF94", "MMFF94s", "UFF"}
    if mmff_variant not in supported_mmff:
        raise ValueError(
            f"Unsupported MMFF variant: {mmff_variant}. "
            f"Supported: {supported_mmff}"
        )

    config: Dict[str, Any] = {
        "etkdg": {
            "max_iterations": max_iterations,
            "energy_tolerance": energy_tolerance,
            "use_explicit_hydrogens": use_explicit_hydrogens
        },
        "generation": {
            "num_conformers": num_conformers,
            "random_seed": 42  # Fixed seed for reproducibility
        },
        "optimization": {
            "method": mmff_variant,
            "max_steps": optimize_steps,
            "convergence_tolerance": 1e-4
        },
        "metadata": {
            "generated_by": "llmXive conformer_config generator",
            "version": "1.0.0"
        }
    }

    if output_path is None:
        data_dir = get_data_dir()
        output_path = str(Path(data_dir) / "raw" / "conformer_config.json")

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write configuration
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Conformer configuration written to: {output_path}")
    return output_path


def load_conformer_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the conformer configuration from a JSON file.

    Args:
        config_path: Path to the config file. Defaults to the generated
                     location in data/raw/conformer_config.json.

    Returns:
        Dict containing the configuration parameters.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if config_path is None:
        data_dir = get_data_dir()
        config_path = str(Path(data_dir) / "raw" / "conformer_config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Conformer config not found at {config_path}. "
            "Run generate_conformer_config() first."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    logger.debug(f"Loaded conformer configuration from: {config_path}")
    return config


if __name__ == "__main__":
    # CLI entry point for generating the config
    config_file = generate_conformer_config()
    print(f"Successfully generated: {config_file}")
    # Verify by loading it back
    loaded = load_conformer_config(config_file)
    print(f"Configuration loaded successfully: {loaded['optimization']['method']}")