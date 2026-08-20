"""
Retrieval module for exoplanetary atmospheric analysis.
Implements petitRADTRANS configuration, low-SNR detection, and upper limit derivation.
"""
import os
import logging
import resource
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from config import get_config
from utils import RetrievalError, CensoredDataError, setup_logging

# Configure logging
logger = setup_logging(__name__)

def configure_petitradtrans_cpu_optimized() -> Dict[str, Any]:
    """
    Configure petitRADTRANS for CPU-optimized (single-threaded) execution.
    Returns configuration dictionary.
    """
    config = get_config()
    return {
        'n_threads': 1,
        'memory_limit_gb': config.get('memory_limit_gb', 4.0),
        'use_cpu': True,
        'use_gpu': False,
        'optimization_level': 'high',
    }

def get_petitradtrans_config() -> Dict[str, Any]:
    """
    Retrieve the current petitRADTRANS configuration.
    """
    return configure_petitradtrans_cpu_optimized()

def validate_spectrum_file(file_path: Path) -> bool:
    """
    Validate that a spectrum file exists and is readable.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Spectrum file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    return True

def detect_low_snr_spectrum(snr: float, resolution: float, threshold_sigma: float = 3.0) -> bool:
    """
    Detect if a spectrum has low Signal-to-Noise Ratio based on metadata.

    Args:
        snr: Signal-to-Noise Ratio from metadata.
        resolution: Spectral resolution (R) from metadata.
        threshold_sigma: Number of sigma above noise floor to consider a detection.

    Returns:
        True if the spectrum is considered low-SNR (signal < 3-sigma above noise).
    """
    if snr is None or np.isnan(snr) or snr <= 0:
        logger.warning(f"Invalid SNR value: {snr}. Treating as low-SNR.")
        return True

    # A spectrum is low-SNR if the SNR is below the threshold.
    # Typically, SNR < 3 is considered non-detection territory for specific features.
    # We use the passed threshold_sigma (default 3.0).
    is_low_snr = snr < threshold_sigma

    if is_low_snr:
        logger.info(f"Low SNR detected: SNR={snr:.2f} < threshold={threshold_sigma}. "
                    f"Resolution R={resolution}. Flagging for upper limit derivation.")

    return is_low_snr

def derive_upper_limit(snr: float, resolution: float, noise_floor: float = 1e-6) -> float:
    """
    Derive an upper limit (censored value) for water mixing ratio based on noise floor.

    Logic:
    - Calculate the detection limit based on instrumental noise floor.
    - If signal < 3-sigma above noise, return the limit value in mixing ratio units.

    Args:
        snr: Signal-to-Noise Ratio.
        resolution: Spectral resolution (R).
        noise_floor: Baseline instrumental noise floor (default 1e-6).

    Returns:
        Upper limit value for water mixing ratio (log10 scale or linear, depending on context).
        Here we return the linear mixing ratio upper limit.
    """
    if snr is None or np.isnan(snr) or snr <= 0:
        # If SNR is invalid, assume the noise floor is the limit
        limit = noise_floor
        logger.warning(f"Invalid SNR. Returning default noise floor as upper limit: {limit}")
        return limit

    # The minimum detectable signal is roughly noise_floor * threshold_sigma (3)
    # However, SNR is defined as Signal / Noise.
    # So, Signal = SNR * Noise.
    # If we are in a low-SNR regime, the "measured" signal is consistent with noise.
    # The upper limit is typically defined as 3 * sigma_noise (or similar).
    # Assuming the 'noise_floor' represents the 1-sigma uncertainty in the mixing ratio retrieval context.
    # Upper Limit = 3 * noise_floor (if we assume 3-sigma confidence).
    # Alternatively, if snr is low, the retrieved value is unreliable, and the limit is set by the noise.

    # Using a standard 3-sigma upper limit calculation relative to the noise floor.
    # If the retrieval process yields a value with uncertainty ~ noise_floor,
    # and the signal is not significant, the upper limit is 3 * noise_floor.
    limit = 3.0 * noise_floor

    logger.debug(f"Derived upper limit: {limit} (3 * {noise_floor}) for SNR={snr}")
    return limit

def calculate_mdc(snr: float, resolution: float, reference_mixing_ratio: float = 1e-4) -> float:
    """
    Calculate the Minimum Detectable Concentration (MDC) based on SNR and Resolution.

    Logic:
    - MDC is the lowest concentration that can be detected with a given confidence.
    - It scales inversely with SNR and Resolution (higher SNR/Res -> lower MDC).
    - Formula approximation: MDC ~ (Reference / (SNR * sqrt(Resolution))) or similar scaling.
    - A common heuristic: MDC = Reference / (SNR * (Resolution/1000)^0.5)

    Args:
        snr: Signal-to-Noise Ratio.
        resolution: Spectral resolution (R).
        reference_mixing_ratio: A reference water mixing ratio for scaling (default 1e-4).

    Returns:
        Minimum Detectable Concentration (mixing ratio).
    """
    if snr is None or np.isnan(snr) or snr <= 0:
        # If SNR is invalid, return a conservative high MDC
        logger.warning(f"Invalid SNR. Returning conservative MDC: {reference_mixing_ratio}")
        return reference_mixing_ratio

    if resolution is None or np.isnan(resolution) or resolution <= 0:
        logger.warning(f"Invalid Resolution. Returning conservative MDC: {reference_mixing_ratio}")
        return reference_mixing_ratio

    # Heuristic scaling: MDC is proportional to 1/SNR and 1/sqrt(Resolution)
    # Normalizing resolution to a baseline of 1000 for scaling
    normalized_res = resolution / 1000.0
    mdc = reference_mixing_ratio / (snr * np.sqrt(normalized_res))

    # Ensure MDC is not unreasonably small or large
    mdc = max(1e-10, min(mdc, 1.0))

    logger.debug(f"MDC calculated: {mdc:.2e} (SNR={snr}, R={resolution})")
    return mdc

def run_single_spectrum_retrieval(spectrum_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run petitRADTRANS retrieval on a single spectrum.
    Returns a dictionary with retrieval results or upper limit flags.
    """
    # Placeholder for actual petitRADTRANS execution
    # In a real implementation, this would call the petitRADTRANS library
    # For now, we simulate the structure expected by downstream tasks
    return {
        'water_mixing_ratio': 0.0,
        'uncertainty': 0.0,
        'is_upper_limit': False,
        'detection_limit': 0.0,
        'min_detectable_concentration': 0.0,
        'converged': True,
        'message': 'Retrieval completed (simulated)'
    }

def main():
    """
    Main entry point for retrieval module execution.
    Parses arguments and orchestrates the retrieval process.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Run atmospheric retrieval')
    parser.add_argument('--input', type=str, required=True, help='Input data directory')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    args = parser.parse_args()

    logger.info(f"Starting retrieval process. Input: {args.input}, Output: {args.output}")

    # Example usage of functions defined in this module
    config = configure_petitradtrans_cpu_optimized()
    logger.info(f"PetitRADTRANS config: {config}")

    # Simulate detection logic
    test_snr = 2.5
    test_res = 50
    is_low = detect_low_snr_spectrum(test_snr, test_res)
    if is_low:
        limit = derive_upper_limit(test_snr, test_res)
        mdc = calculate_mdc(test_snr, test_res)
        logger.info(f"Low SNR case handled. Limit: {limit}, MDC: {mdc}")

    logger.info("Retrieval module execution complete.")

if __name__ == '__main__':
    main()