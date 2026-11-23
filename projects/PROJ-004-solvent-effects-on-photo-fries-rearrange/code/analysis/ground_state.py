"""
Ground-state characterization module for Photo-Fries rearrangement experiments.

This module performs and logs ground-state structural characterization (UV-Vis spectra,
baseline stability) before photo-irradiation for each solvent condition, establishing
the structural baseline required to distinguish solvent effects from instrumental
artifacts (addressing Rosalind Franklin's request for ground-state characterization).

Outputs:
    data/processed/ground_state_characterization.json: Structured log of all
        ground-state measurements including spectral data, baseline metrics, and
        solvent identifiers.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

# Import from project API surface
from config import get_processed_data_path, get_raw_data_path, ensure_directories
from utils.logging import setup_logging, log_environmental_params
from utils.seeds import set_seed
from data.loaders import get_solvent_properties, SolventDataError


logger = logging.getLogger(__name__)


def load_ground_state_reference_data() -> Dict[str, Any]:
    """
    Load reference data for ground-state characterization.

    This function attempts to load real UV-Vis spectral data from the raw data
    directory. If no real data is found, it raises a FileNotFoundError to prevent
    silent fallback to synthetic data.

    Returns:
        Dict containing spectral data, solvent conditions, and metadata.

    Raises:
        FileNotFoundError: If no real ground-state data file is found.
    """
    raw_data_path = get_raw_data_path()
    possible_files = [
        raw_data_path / "ground_state_spectra.csv",
        raw_data_path / "baseline_spectra.csv",
        raw_data_path / "raw_spectra.csv"
    ]

    for file_path in possible_files:
        if file_path.exists():
            logger.info(f"Loading ground-state reference data from: {file_path}")
            df = pd.read_csv(file_path)
            return {
                "source_file": str(file_path),
                "data": df.to_dict(orient='records'),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    # No real data found - fail loudly as per requirements
    error_msg = (
        "No real ground-state spectral data found in raw data directory. "
        "Expected one of: ground_state_spectra.csv, baseline_spectra.csv, or raw_spectra.csv. "
        "Ground-state characterization requires real measured data. "
        "Please provide experimental UV-Vis spectra data before proceeding."
    )
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)


def calculate_baseline_metrics(spectral_data: List[Dict[str, Any]], 
                               wavelength_range: Tuple[float, float] = (300.0, 400.0)) -> Dict[str, float]:
    """
    Calculate baseline stability metrics from spectral data.

    This function computes key metrics including:
    - Mean absorbance in the specified wavelength range
    - Standard deviation (baseline noise)
    - Signal-to-noise ratio
    - Baseline drift (slope of linear fit)

    Args:
        spectral_data: List of dictionaries containing wavelength and absorbance values.
        wavelength_range: Tuple of (min_wavelength, max_wavelength) for analysis.

    Returns:
        Dictionary containing baseline metrics.
    """
    if not spectral_data:
        raise ValueError("Cannot calculate baseline metrics from empty spectral data")

    # Extract wavelengths and absorbances
    wavelengths = np.array([d.get('wavelength', 0) for d in spectral_data])
    absorbances = np.array([d.get('absorbance', 0) for d in spectral_data])

    # Filter to specified range
    mask = (wavelengths >= wavelength_range[0]) & (wavelengths <= wavelength_range[1])
    if not np.any(mask):
        logger.warning(f"No data points in wavelength range {wavelength_range}")
        return {
            "mean_absorbance": 0.0,
            "std_absorbance": 0.0,
            "signal_to_noise_ratio": 0.0,
            "baseline_drift": 0.0,
            "n_points": 0
        }

    filtered_wavelengths = wavelengths[mask]
    filtered_absorbances = absorbances[mask]

    # Calculate metrics
    mean_abs = np.mean(filtered_absorbances)
    std_abs = np.std(filtered_absorbances)
    
    # Signal-to-noise ratio (mean / std)
    snr = mean_abs / std_abs if std_abs > 0 else float('inf')

    # Baseline drift (linear regression slope)
    if len(filtered_wavelengths) > 1:
        coeffs = np.polyfit(filtered_wavelengths, filtered_absorbances, 1)
        drift = coeffs[0]  # slope
    else:
        drift = 0.0

    return {
        "mean_absorbance": float(mean_abs),
        "std_absorbance": float(std_abs),
        "signal_to_noise_ratio": float(snr),
        "baseline_drift": float(drift),
        "n_points": int(np.sum(mask)),
        "wavelength_range_min": float(wavelength_range[0]),
        "wavelength_range_max": float(wavelength_range[1])
    }


def characterize_ground_state(solvent_name: str, 
                              spectral_data: List[Dict[str, Any]],
                              environmental_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform complete ground-state characterization for a single solvent condition.

    This function:
    1. Validates spectral data quality
    2. Calculates baseline stability metrics
    3. Identifies characteristic absorption peaks
    4. Logs all measurements with metadata

    Args:
        solvent_name: Name of the solvent being characterized.
        spectral_data: List of dictionaries with wavelength/absorbance pairs.
        environmental_params: Optional dictionary of environmental conditions.

    Returns:
        Complete characterization record for the solvent condition.
    """
    if not solvent_name:
        raise ValueError("Solvent name is required for ground-state characterization")

    # Get solvent properties for validation
    try:
        solvent_props = get_solvent_properties(solvent_name)
        dielectric_constant = solvent_props.get('dielectric_constant', None)
    except SolventDataError as e:
        logger.warning(f"Could not retrieve properties for {solvent_name}: {e}")
        dielectric_constant = None

    # Calculate baseline metrics
    baseline_metrics = calculate_baseline_metrics(spectral_data)

    # Identify characteristic peaks (simple peak detection)
    wavelengths = np.array([d.get('wavelength', 0) for d in spectral_data])
    absorbances = np.array([d.get('absorbance', 0) for d in spectral_data])

    # Find local maxima (peaks)
    peak_indices = []
    for i in range(1, len(absorbances) - 1):
        if absorbances[i] > absorbances[i-1] and absorbances[i] > absorbances[i+1]:
            if absorbances[i] > 0.05:  # Minimum threshold for peak detection
                peak_indices.append(i)

    peaks = []
    for idx in peak_indices:
        peaks.append({
            "wavelength": float(wavelengths[idx]),
            "absorbance": float(absorbances[idx])
        })

    # Sort peaks by absorbance (most significant first)
    peaks.sort(key=lambda x: x['absorbance'], reverse=True)

    # Build characterization record
    characterization = {
        "solvent_name": solvent_name,
        "dielectric_constant": dielectric_constant,
        "characterization_timestamp": datetime.now(timezone.utc).isoformat(),
        "baseline_metrics": baseline_metrics,
        "detected_peaks": peaks[:5],  # Top 5 peaks
        "spectral_quality": {
            "n_data_points": len(spectral_data),
            "wavelength_range": [
                float(min(wavelengths)) if len(wavelengths) > 0 else None,
                float(max(wavelengths)) if len(wavelengths) > 0 else None
            ],
            "absorbance_range": [
                float(min(absorbances)) if len(absorbances) > 0 else None,
                float(max(absorbances)) if len(absorbances) > 0 else None
            ]
        },
        "environmental_conditions": environmental_params or {},
        "validation_flags": {
            "baseline_stable": baseline_metrics['std_absorbance'] < 0.01,
            "sufficient_data": len(spectral_data) >= 10,
            "peaks_detected": len(peaks) > 0
        }
    }

    # Log validation results
    if not characterization['validation_flags']['baseline_stable']:
        logger.warning(f"Baseline instability detected for {solvent_name}: "
                     f"std={baseline_metrics['std_absorbance']:.4f}")
    if not characterization['validation_flags']['sufficient_data']:
        logger.warning(f"Insufficient data points for {solvent_name}: "
                     f"n={len(spectral_data)}")

    return characterization


def run_ground_state_characterization() -> Dict[str, Any]:
    """
    Execute the full ground-state characterization pipeline.

    This function:
    1. Loads real ground-state spectral data
    2. Groups data by solvent condition
    3. Performs characterization for each solvent
    4. Aggregates results and writes to output file

    Returns:
        Dictionary containing all characterization results and metadata.
    """
    logger.info("Starting ground-state characterization pipeline")
    
    # Set seed for reproducibility (though we use real data)
    set_seed(42)

    # Load reference data
    reference_data = load_ground_state_reference_data()
    raw_records = reference_data['data']

    if not raw_records:
        raise ValueError("No spectral data records found in reference file")

    # Group by solvent
    solvent_groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in raw_records:
        solvent = record.get('solvent', record.get('solvent_name', 'unknown'))
        if solvent not in solvent_groups:
            solvent_groups[solvent] = []
        solvent_groups[solvent].append(record)

    logger.info(f"Found {len(solvent_groups)} unique solvent conditions")

    # Characterize each solvent
    all_characterizations = []
    for solvent_name, spectra in solvent_groups.items():
        logger.info(f"Characterizing ground state for: {solvent_name}")
        
        # Extract spectral data for this solvent
        spectral_data = [
            {
                'wavelength': r.get('wavelength', 0),
                'absorbance': r.get('absorbance', 0)
            }
            for r in spectra
            if 'wavelength' in r and 'absorbance' in r
        ]

        if not spectral_data:
            logger.warning(f"No valid spectral data for {solvent_name}, skipping")
            continue

        # Perform characterization
        char_record = characterize_ground_state(
            solvent_name=solvent_name,
            spectral_data=spectral_data,
            environmental_params={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "ground_state_characterization"
            }
        )
        all_characterizations.append(char_record)

    # Build final result
    result = {
        "pipeline_version": "1.0.0",
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_file": reference_data['source_file'],
        "n_solvents_characterized": len(all_characterizations),
        "characterizations": all_characterizations,
        "summary_statistics": {
            "total_spectra_processed": len(raw_records),
            "solvents_with_valid_baseline": sum(
                1 for c in all_characterizations 
                if c['validation_flags']['baseline_stable']
            ),
            "solvents_with_detected_peaks": sum(
                1 for c in all_characterizations 
                if c['validation_flags']['peaks_detected']
            )
        }
    }

    # Write output
    output_path = get_processed_data_path() / "ground_state_characterization.json"
    ensure_directories()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)

    logger.info(f"Ground-state characterization complete. Results written to: {output_path}")
    logger.info(f"Characterized {len(all_characterizations)} solvent conditions")

    return result


def main():
    """CLI entry point for ground-state characterization."""
    parser = argparse.ArgumentParser(
        description="Perform ground-state structural characterization for Photo-Fries experiments"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    try:
        result = run_ground_state_characterization()
        print(f"Successfully characterized {result['n_solvents_characterized']} solvent conditions")
        print(f"Output written to: {get_processed_data_path() / 'ground_state_characterization.json'}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())