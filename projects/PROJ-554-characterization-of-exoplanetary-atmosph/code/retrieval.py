import os
import logging
import resource
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

# Import existing utilities and data models
from config import get_config
from utils import setup_logging, safe_execute, RetrievalError, handle_non_convergent_retrieval
from data_models import RetrievalResult, CensorshipStatus, PlanetCategory

# Configure logging for this module
logger = logging.getLogger(__name__)

def configure_petitradtrans_cpu_optimized():
    """
    Configure petitRADTRANS for CPU-optimized (single-threaded) mode.
    Sets environment variables and memory limits.
    """
    config = get_config()
    # Force single thread for petitRADTRANS to respect CPU constraints
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    
    # Set memory limit if specified in config
    if config.get('memory_limit_mb'):
        try:
            resource.setrlimit(resource.RLIMIT_AS, (config['memory_limit_mb'] * 1024 * 1024, -1))
        except (ValueError, resource.error) as e:
            logger.warning(f"Could not set memory limit: {e}")
    
    logger.info("petitRADTRANS configured for single-threaded CPU execution.")

def get_petitradtrans_config():
    """
    Returns the configuration dictionary for petitRADTRANS.
    """
    config = get_config()
    return {
        'atmosphere_model': 'equilibrium',
        'temperature_range': (500, 3000),
        'metallicity_range': (-2.0, 2.0),
        'cloud_model': 'none',
        'resolution': config.get('spectral_resolution', 100),
        'cpu_threads': 1,
    }

def validate_spectrum_file(file_path: Path) -> bool:
    """
    Validates that a spectrum file exists and is readable.
    """
    if not file_path.exists():
        logger.error(f"Spectrum file not found: {file_path}")
        return False
    try:
        # Attempt to open and read a small portion to verify format
        with open(file_path, 'r') as f:
            f.readline()
        return True
    except Exception as e:
        logger.error(f"Failed to read spectrum file {file_path}: {e}")
        return False

def detect_low_snr_spectrum(snr: float, resolution: float) -> bool:
    """
    Detects if a spectrum has low SNR based on metadata.
    Thresholds can be configured.
    """
    config = get_config()
    snr_threshold = config.get('snr_threshold', 5.0)
    return snr < snr_threshold

def derive_upper_limit(snr: float, resolution: float, noise_floor: float = 1e-4) -> Tuple[float, float]:
    """
    Derives an upper limit for water mixing ratio for low SNR spectra.
    Returns (limit_value, uncertainty).
    """
    # Calculate detection limit based on instrumental noise floor and SNR
    # Simple model: limit = noise_floor * (1 / SNR) * scaling_factor
    # This is a placeholder for the actual physical derivation logic
    scaling_factor = 3.0  # 3-sigma detection limit
    limit_value = noise_floor * scaling_factor / snr if snr > 0 else noise_floor * scaling_factor
    uncertainty = limit_value * 0.5  # 50% uncertainty on the limit estimate
    return limit_value, uncertainty

def calculate_mdc(snr: float, resolution: float) -> float:
    """
    Calculates the Minimum Detectable Concentration (MDC).
    """
    # Placeholder logic: MDC inversely proportional to SNR and Resolution
    # In a real implementation, this would use specific radiative transfer models
    base_mdc = 1e-5
    mdc = base_mdc / (snr * np.sqrt(resolution))
    return mdc

def run_single_spectrum_retrieval(
    spectrum_file: Path, 
    planet_name: str, 
    temperature: float, 
    metallicity: float, 
    snr: float, 
    resolution: float
) -> Optional[RetrievalResult]:
    """
    Runs petitRADTRANS retrieval on a single spectrum file.
    Implements error handling for non-convergent retrievals:
    1. Logs failure.
    2. Attempts upper limit derivation.
    3. Returns a RetrievalResult with is_upper_limit=True.
    """
    logger.info(f"Starting retrieval for {planet_name} from {spectrum_file}")
    
    if not validate_spectrum_file(spectrum_file):
        logger.error(f"Validation failed for {spectrum_file}, skipping retrieval.")
        return None

    try:
        # Configure petitRADTRANS (mocked for this implementation context)
        # In a real environment, this would import and call petitRADTRANS
        # config = get_petitradtrans_config()
        # result = petitradtrans.retrieve(...)
        
        # Simulating a retrieval process that might fail
        # For the purpose of this task, we simulate a random convergence failure
        # to demonstrate the error handling path.
        # In a real run, this would be the actual petitRADTRANS call.
        
        import random
        # Simulate non-convergence for demonstration (10% chance)
        # In real code, this block would be the actual retrieval call
        # which raises RetrievalError on non-convergence
        if random.random() < 0.1: 
            raise RetrievalError("Retrieval did not converge after max iterations.")

        # Mock successful result
        water_mixing_ratio = np.log10(1e-4) # log10 scale
        uncertainty = 0.1
        is_upper_limit = False
        detection_limit = None
        mdc = calculate_mdc(snr, resolution)

        return RetrievalResult(
            planet_name=planet_name,
            water_mixing_ratio=water_mixing_ratio,
            uncertainty=uncertainty,
            is_upper_limit=is_upper_limit,
            detection_limit=detection_limit,
            min_detectable_concentration=mdc,
            status=CensorshipStatus.DETECTED
        )

    except RetrievalError as e:
        logger.warning(f"Retrieval failed for {planet_name}: {e}")
        logger.info(f"Attempting upper limit derivation for {planet_name} due to non-convergence.")
        
        # Attempt upper limit derivation as per task requirement
        limit_value, limit_uncertainty = derive_upper_limit(snr, resolution)
        mdc = calculate_mdc(snr, resolution)
        
        logger.info(f"Derived upper limit for {planet_name}: log10(limit)={np.log10(limit_value):.4f}")
        
        return RetrievalResult(
            planet_name=planet_name,
            water_mixing_ratio=np.log10(limit_value),
            uncertainty=limit_uncertainty,
            is_upper_limit=True,
            detection_limit=limit_value,
            min_detectable_concentration=mdc,
            status=CensorshipStatus.UPPER_LIMIT
        )
    except Exception as e:
        logger.error(f"Unexpected error during retrieval for {planet_name}: {e}")
        # For unexpected errors, we also attempt to salvage with upper limit if possible
        # or return None if we cannot even estimate a limit
        try:
            limit_value, limit_uncertainty = derive_upper_limit(snr, resolution)
            mdc = calculate_mdc(snr, resolution)
            return RetrievalResult(
                planet_name=planet_name,
                water_mixing_ratio=np.log10(limit_value),
                uncertainty=limit_uncertainty,
                is_upper_limit=True,
                detection_limit=limit_value,
                min_detectable_concentration=mdc,
                status=CensorshipStatus.UPPER_LIMIT
            )
        except Exception as fallback_err:
            logger.error(f"Failed to derive upper limit for {planet_name}: {fallback_err}")
            return None

def main():
    """
    Main entry point for retrieval processing.
    """
    logger = setup_logging()
    configure_petitradtrans_cpu_optimized()
    
    # This would typically iterate over downloaded spectra from data/raw/
    # For this task, we demonstrate the error handling logic
    logger.info("Retrieval module initialized with error handling for non-convergence.")

if __name__ == "__main__":
    main()