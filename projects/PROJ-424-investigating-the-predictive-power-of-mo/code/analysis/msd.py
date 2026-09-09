"""
Mean Squared Displacement (MSD) Analysis Module.

This module implements the extraction of MSD from simulation trajectories,
performs linear regression to estimate diffusion coefficients, and validates
linearity against the strict R² threshold defined in the project constitution.

References:
- Constitution Principle VI: R² ≥ 0.95 required for valid diffusion estimation.
- spec.md FR-008: Diffusion coefficient validity threshold.
"""

import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
import json

import numpy as np
from scipy import stats

# Import project configuration and logging utilities
from config import Solvent, AnalysisConfig
from utils.logging import get_logger
from utils.data_fetcher import validate_nist_refs

# Ensure logger is configured
logger = get_logger(__name__)


@dataclass
class MSDResult:
    """
    Container for the results of an MSD analysis.

    Attributes:
        solvent: The solvent type analyzed.
        timescale: The simulation timescale (e.g., '1ns', '10ns').
        r_squared: The R² value from the linear regression of MSD vs time.
        slope: The slope of the linear fit (related to diffusion).
        intercept: The y-intercept of the linear fit.
        diffusion_coefficient: The calculated diffusion coefficient (m²/s).
        is_valid: Boolean indicating if R² >= 0.95.
        error_message: Optional error message if analysis failed.
    """
    solvent: str
    timescale: str
    r_squared: float
    slope: float
    intercept: float
    diffusion_coefficient: float
    is_valid: bool
    error_message: Optional[str] = None


def load_trajectory_timeseries(trajectory_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load time and MSD data from a trajectory analysis file.

    Expected file format: CSV with columns 'time' and 'msd'.
    The time is in picoseconds (ps) and MSD is in nm².

    Args:
        trajectory_path: Path to the MSD data file.

    Returns:
        Tuple of (time_array, msd_array) as numpy arrays.

    Raises:
        FileNotFoundError: If the trajectory file does not exist.
        ValueError: If the file format is invalid or data is missing.
    """
    if not trajectory_path.exists():
        raise FileNotFoundError(f"Trajectory file not found: {trajectory_path}")

    try:
        data = np.loadtxt(trajectory_path, delimiter=',', skiprows=1)
        if data.shape[1] < 2:
            raise ValueError("Data file must have at least two columns (time, msd)")

        time = data[:, 0]
        msd = data[:, 1]

        # Filter out any non-finite values
        valid_mask = np.isfinite(time) & np.isfinite(msd)
        if not np.all(valid_mask):
            logger.warning(f"Removed {np.sum(~valid_mask)} non-finite data points from {trajectory_path}")
            time = time[valid_mask]
            msd = msd[valid_mask]

        if len(time) < 2:
            raise ValueError("Insufficient data points for regression (need >= 2)")

        return time, msd

    except Exception as e:
        logger.error(f"Failed to load trajectory data from {trajectory_path}: {e}")
        raise


def perform_linear_regression(time: np.ndarray, msd: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Perform linear regression on MSD vs Time data.

    In 3D isotropic diffusion, MSD = 6 * D * t.
    The slope of the linear fit corresponds to 6 * D.

    Args:
        time: Array of time values (ps).
        msd: Array of MSD values (nm²).

    Returns:
        Tuple of (slope, intercept, r_squared, p_value).
    """
    if len(time) < 2:
        raise ValueError("Need at least 2 data points for linear regression.")

    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(time, msd)

    r_squared = r_value ** 2

    logger.debug(f"Regression results: slope={slope:.6f}, intercept={intercept:.6f}, R²={r_squared:.6f}")

    return slope, intercept, r_squared, p_value


def validate_linearity(r_squared: float, threshold: float = 0.95) -> bool:
    """
    Validate that the MSD vs Time relationship is linear enough.

    This function enforces Constitution Principle VI and spec.md FR-008,
    which require an R² of at least 0.95 for the diffusion coefficient
    to be considered valid.

    Args:
        r_squared: The R² value from the regression.
        threshold: The minimum acceptable R² (default 0.95).

    Returns:
        True if R² >= threshold, False otherwise.
    """
    is_valid = r_squared >= threshold
    if not is_valid:
        logger.warning(f"Linearity validation failed: R²={r_squared:.4f} < {threshold}")
    else:
        logger.info(f"Linearity validation passed: R²={r_squared:.4f} >= {threshold}")
    return is_valid


def calculate_diffusion_coefficient(slope: float, time_unit: str = 'ps', length_unit: str = 'nm') -> float:
    """
    Calculate the diffusion coefficient from the regression slope.

    Formula: D = slope / (2 * dim)
    For 3D: D = slope / 6

    Unit conversions:
    - Slope is in nm²/ps
    - Target D is in m²/s
    - 1 nm²/ps = (1e-9 m)² / (1e-12 s) = 1e-18 / 1e-12 = 1e-6 m²/s

    Args:
        slope: The slope from linear regression (nm²/ps).
        time_unit: Time unit of input data (default 'ps').
        length_unit: Length unit of input data (default 'nm').

    Returns:
        Diffusion coefficient in m²/s.
    """
    # Assuming 3D diffusion
    dim = 3.0
    raw_d = slope / (2.0 * dim)

    # Convert nm²/ps to m²/s
    # 1 nm = 1e-9 m => 1 nm² = 1e-18 m²
    # 1 ps = 1e-12 s
    # 1 nm²/ps = 1e-18 / 1e-12 = 1e-6 m²/s
    conversion_factor = 1e-6

    d_in_ms = raw_d * conversion_factor

    logger.debug(f"Calculated D: slope={slope}, raw_D={raw_d}, D_m2s={d_in_ms}")

    return d_in_ms


def analyze_msd(
    trajectory_path: Path,
    solvent: str,
    timescale: str,
    config: Optional[AnalysisConfig] = None
) -> MSDResult:
    """
    Perform full MSD analysis for a single trajectory.

    Steps:
    1. Load time and MSD data.
    2. Perform linear regression.
    3. Validate linearity (R² >= 0.95).
    4. Calculate diffusion coefficient.

    Args:
        trajectory_path: Path to the MSD data file.
        solvent: Name of the solvent.
        timescale: Simulation timescale.
        config: Optional AnalysisConfig for overrides.

    Returns:
        MSDResult object containing all analysis metrics.
    """
    if config is None:
        # Default config if not provided
        config = AnalysisConfig(r_squared_threshold=0.95)

    try:
        logger.info(f"Analyzing MSD for {solvent} at {timescale} from {trajectory_path}")

        # 1. Load Data
        time, msd = load_trajectory_timeseries(trajectory_path)

        # 2. Linear Regression
        slope, intercept, r_squared, p_value = perform_linear_regression(time, msd)

        # 3. Validate Linearity
        is_valid = validate_linearity(r_squared, config.r_squared_threshold)

        # 4. Calculate Diffusion Coefficient
        diffusion_coefficient = calculate_diffusion_coefficient(slope)

        result = MSDResult(
            solvent=solvent,
            timescale=timescale,
            r_squared=r_squared,
            slope=slope,
            intercept=intercept,
            diffusion_coefficient=diffusion_coefficient,
            is_valid=is_valid
        )

        if not is_valid:
            logger.warning(f"Result for {solvent}/{timescale} is INVALID due to low R².")

        return result

    except Exception as e:
        logger.error(f"Analysis failed for {solvent}/{timescale}: {e}", exc_info=True)
        return MSDResult(
            solvent=solvent,
            timescale=timescale,
            r_squared=0.0,
            slope=0.0,
            intercept=0.0,
            diffusion_coefficient=0.0,
            is_valid=False,
            error_message=str(e)
        )


def batch_analyze_msd(
    results_dir: Path,
    config: Optional[AnalysisConfig] = None
) -> List[MSDResult]:
    """
    Analyze all MSD files in a directory.

    Expects files named {solvent}_{timescale}.csv (e.g., water_1ns.csv).

    Args:
        results_dir: Directory containing MSD CSV files.
        config: Optional AnalysisConfig.

    Returns:
        List of MSDResult objects.
    """
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    results = []
    msd_files = list(results_dir.glob("*.csv"))

    if not msd_files:
        logger.warning(f"No CSV files found in {results_dir}")
        return results

    for file_path in msd_files:
        # Parse filename: solvent_timescale.csv
        stem = file_path.stem
        parts = stem.split('_')
        if len(parts) >= 2:
            solvent = parts[0]
            timescale = '_'.join(parts[1:]) # Handle cases like 10_ns if split differently
            # Basic heuristic for timescale if split by underscore
            # Assuming standard format: water_1ns.csv -> water, 1ns
            if len(parts) == 2:
                solvent, timescale = parts
            else:
                # Fallback for complex names, assume first part is solvent
                solvent = parts[0]
                timescale = "_".join(parts[1:])

            result = analyze_msd(file_path, solvent, timescale, config)
            results.append(result)
        else:
            logger.warning(f"Skipping file with unexpected name format: {file_path.name}")

    return results


def save_analysis_results(results: List[MSDResult], output_path: Path) -> None:
    """
    Save analysis results to a JSON file.

    Args:
        results: List of MSDResult objects.
        output_path: Path to the output JSON file.
    """
    data = [
        {
            "solvent": r.solvent,
            "timescale": r.timescale,
            "r_squared": r.r_squared,
            "slope": r.slope,
            "intercept": r.intercept,
            "diffusion_coefficient": r.diffusion_coefficient,
            "is_valid": r.is_valid,
            "error_message": r.error_message
        }
        for r in results
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved {len(results)} results to {output_path}")


def main() -> None:
    """
    Main entry point for MSD analysis script.

    Reads configuration, finds trajectory files, performs analysis,
    and saves results.
    """
    # Setup logging
    log = get_logger("msd_analysis")
    log.info("Starting MSD Analysis Pipeline")

    # Define paths (relative to project root)
    # In a real scenario, these might come from CLI args or a config file
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data" / "processed" / "msd"
    output_dir = base_dir / "data" / "processed" / "analysis"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config if available, else use defaults
    # Assuming config is handled by the global config module
    try:
        from config import AnalysisConfig
        analysis_config = AnalysisConfig()
    except ImportError:
        analysis_config = None

    # Validate NIST refs exist (as per T006c requirement)
    try:
        validate_nist_refs()
        log.info("NIST references validated successfully.")
    except Exception as e:
        log.error(f"NIST reference validation failed: {e}")
        # We continue analysis but note that comparison won't be possible
        # unless the error is critical. For T016, we just log.

    # Run batch analysis
    if data_dir.exists():
        results = batch_analyze_msd(data_dir, analysis_config)
        save_analysis_results(results, output_dir / "msd_results.json")
    else:
        log.warning(f"Data directory {data_dir} does not exist. No analysis performed.")
        # Create an empty result file to indicate completion status
        save_analysis_results([], output_dir / "msd_results.json")

    log.info("MSD Analysis Pipeline Completed")


if __name__ == "__main__":
    main()