"""
Plotting service for segregation analysis.
Generates heatmaps visualizing segregation energy vs bulk composition and temperature.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from code.config import PROCESSED_PATH, FIGURES_PATH, get_logger

# Ensure output directories exist
FIGURES_PATH.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)


def load_segregation_profiles() -> Dict[str, Any]:
    """
    Load segregation profiles from the processed data file.

    Returns:
        Dict containing segregation profile data.

    Raises:
        FileNotFoundError: If the profiles file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    profiles_path = PROCESSED_PATH / "segregation_profiles.json"
    if not profiles_path.exists():
        logger.error(f"Profiles file not found: {profiles_path}")
        raise FileNotFoundError(f"Profiles file not found: {profiles_path}")

    logger.info(f"Loading segregation profiles from {profiles_path}")
    with open(profiles_path, 'r') as f:
        data = json.load(f)
    return data


def prepare_heatmap_data(
    profiles: Dict[str, Any],
    systems: Optional[List[str]] = None
) -> tuple:
    """
    Prepare data for heatmap generation.

    Args:
        profiles: Segregation profile data.
        systems: Optional list of specific systems to include.

    Returns:
        Tuple of (X, Y, Z) arrays suitable for contour/heatmap plotting.
        X: Bulk concentration
        Y: Temperature
        Z: Segregation energy
    """
    if not isinstance(profiles, dict):
        # Handle list format if necessary
        if isinstance(profiles, list):
            profiles = {"systems": profiles}
        else:
            logger.error("Unexpected profiles format")
            raise ValueError("Unexpected profiles format")

    systems_data = profiles.get("systems", profiles) if isinstance(profiles, dict) else profiles

    if isinstance(systems_data, dict):
        systems_data = list(systems_data.values())

    # Flatten data points
    bulk_concentrations = []
    temperatures = []
    segregation_energies = []

    logger.info("Extracting data points from segregation profiles...")
    for system_entry in systems_data:
        if not isinstance(system_entry, dict):
            continue

        system_name = system_entry.get("system", "Unknown")
        if systems and system_name not in systems:
            continue

        profiles_list = system_entry.get("profiles", [])
        if not isinstance(profiles_list, list):
            # Handle single profile case
            profiles_list = [profiles_list]

        for profile in profiles_list:
            if not isinstance(profile, dict):
                continue

            # Extract bulk composition (handle various formats)
            bulk_comp = profile.get("bulk_composition", {})
            if isinstance(bulk_comp, dict):
                # Assume binary/ternary with solute concentration
                # Look for key solute concentrations (Cr, Mo, V, W)
                for element in ["Cr", "Mo", "V", "W"]:
                    if element in bulk_comp:
                        bulk_val = bulk_comp[element]
                        if isinstance(bulk_val, (int, float)):
                            bulk_concentrations.append(bulk_val)
                            break
                else:
                    # Fallback: use first numeric value found
                    for key, val in bulk_comp.items():
                        if isinstance(val, (int, float)):
                            bulk_concentrations.append(val)
                            break
            elif isinstance(bulk_comp, (int, float)):
                bulk_concentrations.append(bulk_comp)

            # Extract temperature
            temp = profile.get("temperature")
            if temp is None:
                temp = profile.get("T")
            if isinstance(temp, (int, float)):
                temperatures.append(temp)

            # Extract segregation energy
            energy = profile.get("segregation_energy_eV")
            if energy is None:
                energy = profile.get("energy_eV")
            if isinstance(energy, (int, float)):
                segregation_energies.append(energy)

    if not bulk_concentrations or not temperatures or not segregation_energies:
        logger.warning("No valid data points extracted for heatmap. Returning empty arrays.")
        return np.array([]), np.array([]), np.array([])

    X = np.array(bulk_concentrations)
    Y = np.array(temperatures)
    Z = np.array(segregation_energies)

    logger.info(f"Extracted {len(Z)} data points: X_range=[{X.min():.3f}, {X.max():.3f}], "
                f"Y_range=[{Y.min():.1f}, {Y.max():.1f}], Z_range=[{Z.min():.3f}, {Z.max():.3f}]")

    return X, Y, Z


def generate_segregation_heatmap(
    output_path: Optional[Path] = None,
    systems: Optional[List[str]] = None,
    title: str = "Segregation Energy vs Bulk Composition and Temperature"
) -> Path:
    """
    Generate a heatmap visualizing segregation energy vs bulk composition and temperature.

    Args:
        output_path: Path to save the figure. Defaults to FIGURES_PATH/segregation_heatmap.png.
        systems: Optional list of systems to include.
        title: Plot title.

    Returns:
        Path to the generated figure.

    Raises:
        ValueError: If no data is available to plot.
    """
    if output_path is None:
        output_path = FIGURES_PATH / "segregation_heatmap.png"

    logger.info(f"Generating segregation heatmap: {output_path}")

    # Load and prepare data
    profiles = load_segregation_profiles()
    X, Y, Z = prepare_heatmap_data(profiles, systems)

    if len(X) == 0 or len(Y) == 0 or len(Z) == 0:
        error_msg = "No data available to generate heatmap. Check input data."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create 2D histogram / hexbin for better visualization of scattered data
    # Using hexbin to handle scattered data points effectively
    hb = ax.hexbin(
        X, Y, C=Z,
        reduce_C_function=np.mean,
        gridsize=30,
        cmap='viridis',
        mincnt=1
    )

    # Add colorbar
    cbar = fig.colorbar(hb, ax=ax, label='Segregation Energy (eV)')
    cbar.set_label('Segregation Energy (eV)', fontsize=12)

    # Set labels and title
    ax.set_xlabel('Bulk Concentration (fraction)', fontsize=12)
    ax.set_ylabel('Temperature (K)', fontsize=12)
    ax.set_title(title, fontsize=14)

    # Ensure symmetric normalization for handling negative values
    z_min, z_max = Z.min(), Z.max()
    if z_min < 0 and z_max > 0:
        # Symmetric range around zero if data spans negative and positive
        limit = max(abs(z_min), abs(z_max))
        norm = Normalize(vmin=-limit, vmax=limit)
        hb.set_norm(norm)
        cbar.update_normal(hb)

    plt.tight_layout()

    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Heatmap saved to {output_path}")
    return output_path


def main():
    """
    Main entry point for generating the segregation heatmap.
    """
    logger.info("Starting segregation heatmap generation (T024a)...")
    try:
        output_path = generate_segregation_heatmap()
        logger.info(f"Task completed successfully. Output: {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data preparation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during heatmap generation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())