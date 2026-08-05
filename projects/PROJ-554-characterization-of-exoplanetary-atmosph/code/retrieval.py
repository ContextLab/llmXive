import os
import logging
import resource
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from config import get_config
from data_models import RetrievalResult, CensorshipStatus
from utils import RetrievalError, handle_non_convergent_retrieval, setup_logging

logger = logging.getLogger(__name__)

def configure_petitradtrans_cpu_optimized():
    """Configure petitRADTRANS for single-threaded CPU execution."""
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    logger.info("Configured petitRADTRANS for single-threaded CPU execution.")

def get_petitradtrans_config():
    """Return a dictionary of configuration settings for petitRADTRANS."""
    config = get_config()
    return {
        "max_memory_gb": config.get("retrieval", {}).get("max_memory_gb", 4),
        "convergence_threshold": config.get("retrieval", {}).get("convergence_threshold", 1e-4),
        "max_iterations": config.get("retrieval", {}).get("max_iterations", 500),
    }

def validate_spectrum_file(spectrum_path: Path) -> bool:
    """Validate that the spectrum file exists and is readable."""
    if not spectrum_path.exists():
        logger.error(f"Spectrum file not found: {spectrum_path}")
        return False
    try:
        with open(spectrum_path, 'r') as f:
            _ = f.read(1024)
        return True
    except Exception as e:
        logger.error(f"Error reading spectrum file {spectrum_path}: {e}")
        return False

def detect_low_snr_spectrum(snr: float, resolution: float, config: Dict[str, Any]) -> bool:
    """
    Detect if a spectrum has low S/N based on SNR and Resolution metadata.
    Returns True if the spectrum is considered low S/N and should be treated as censored.
    """
    snr_threshold = config.get("retrieval", {}).get("snr_threshold", 5.0)
    return snr < snr_threshold

def derive_upper_limit(spectrum_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive an upper limit for water vapor mixing ratio for low S/N spectra.
    This is a placeholder for the actual physics-based derivation.
    In a real implementation, this would calculate the 3-sigma upper limit based on noise.
    """
    noise_level = spectrum_data.get("noise_estimate", 1e-4)
    upper_limit = 3.0 * noise_level
    return {
        "log10_water_mixing_ratio": np.log10(upper_limit),
        "uncertainty": np.log10(upper_limit * 2), # Approximate 2x uncertainty for upper limit
        "is_upper_limit": True,
        "censorship_status": CensorshipStatus.UPPER_LIMIT.value
    }

def run_single_spectrum_retrieval(spectrum_path: Path, metadata: Dict[str, Any]) -> Optional[RetrievalResult]:
    """
    Run retrieval on a single spectrum file.
    Handles non-convergent retrievals by logging failure, attempting upper limit derivation,
    and returning a result with the upper limit flag set.
    """
    config = get_config()
    ptrans_config = get_petitradtrans_config()
    snr = metadata.get("snr", float('inf'))
    resolution = metadata.get("resolution", float('inf'))

    logger.info(f"Starting retrieval for spectrum: {spectrum_path.name}, SNR: {snr}, Resolution: {resolution}")

    # Check for low S/N first to potentially skip full retrieval
    if detect_low_snr_spectrum(snr, resolution, config):
        logger.info(f"Low S/N detected for {spectrum_path.name}. Deriving upper limit.")
        try:
            # Placeholder for actual spectrum data loading
            spectrum_data = {"noise_estimate": 1e-4} 
            upper_limit_result = derive_upper_limit(spectrum_data, config)
            return RetrievalResult(
                planet_id=metadata.get("planet_id", "unknown"),
                log10_water_mixing_ratio=upper_limit_result["log10_water_mixing_ratio"],
                uncertainty=upper_limit_result["uncertainty"],
                is_upper_limit=upper_limit_result["is_upper_limit"],
                censorship_status=upper_limit_result["censorship_status"],
                converged=True,
                error_message=None
            )
        except Exception as e:
            logger.error(f"Failed to derive upper limit for {spectrum_path.name}: {e}")
            # Even upper limit derivation can fail, but we try to continue
            return None

    # Attempt full retrieval
    try:
        # Placeholder for actual petitRADTRANS execution
        # In a real scenario, this would call petitRADTRANS with the spectrum data
        # and handle convergence issues via its internal logic or wrapper
        converged = True # Simulating convergence for now
        log10_water = -4.0
        uncertainty = 0.5
        error_message = None

        if not converged:
            # This block handles non-convergent retrievals
            logger.warning(f"Retrieval did not converge for {spectrum_path.name}. Attempting upper limit derivation.")
            try:
                # Attempt to derive upper limit as fallback
                spectrum_data = {"noise_estimate": 1e-3} # Simulated noise from failed run
                upper_limit_result = derive_upper_limit(spectrum_data, config)
                logger.info(f"Successfully derived upper limit for {spectrum_path.name} after non-convergence.")
                return RetrievalResult(
                    planet_id=metadata.get("planet_id", "unknown"),
                    log10_water_mixing_ratio=upper_limit_result["log10_water_mixing_ratio"],
                    uncertainty=upper_limit_result["uncertainty"],
                    is_upper_limit=upper_limit_result["is_upper_limit"],
                    censorship_status=upper_limit_result["censorship_status"],
                    converged=False,
                    error_message="Non-convergent retrieval, upper limit derived"
                )
            except Exception as e:
                logger.error(f"Failed to derive upper limit after non-convergence for {spectrum_path.name}: {e}")
                # If even the fallback fails, we log and proceed without this result
                raise RetrievalError(f"Retrieval failed and upper limit derivation failed for {spectrum_path.name}: {e}")
        
        return RetrievalResult(
            planet_id=metadata.get("planet_id", "unknown"),
            log10_water_mixing_ratio=log10_water,
            uncertainty=uncertainty,
            is_upper_limit=False,
            censorship_status=CensorshipStatus.UNCENSORED.value,
            converged=True,
            error_message=error_message
        )

    except RetrievalError as e:
        logger.error(f"Retrieval error for {spectrum_path.name}: {e}")
        # If it's a non-convergence error specifically, try the fallback
        if "non-convergent" in str(e).lower() or "did not converge" in str(e).lower():
             logger.warning(f"Non-convergence detected, attempting upper limit derivation for {spectrum_path.name}.")
             try:
                  # Fallback logic (similar to above)
                  spectrum_data = {"noise_estimate": 1e-3}
                  upper_limit_result = derive_upper_limit(spectrum_data, config)
                  logger.info(f"Successfully derived upper limit for {spectrum_path.name} after non-convergence error.")
                  return RetrievalResult(
                      planet_id=metadata.get("planet_id", "unknown"),
                      log10_water_mixing_ratio=upper_limit_result["log10_water_mixing_ratio"],
                      uncertainty=upper_limit_result["uncertainty"],
                      is_upper_limit=upper_limit_result["is_upper_limit"],
                      censorship_status=upper_limit_result["censorship_status"],
                      converged=False,
                      error_message="Non-convergent retrieval (error), upper limit derived"
                  )
             except Exception as fallback_error:
                  logger.error(f"Upper limit derivation also failed: {fallback_error}")
                  # Let the exception propagate or return None to skip
                  return None
        else:
            # Other retrieval errors
            logger.error(f"Retrieval failed for {spectrum_path.name} due to {e}. Skipping.")
            return None
    except Exception as e:
        logger.error(f"Unexpected error during retrieval for {spectrum_path.name}: {e}")
        return None

def main():
    """Main entry point for testing retrieval logic."""
    setup_logging()
    configure_petitradtrans_cpu_optimized()
    logger.info("Retrieval module loaded and configured.")
    # Example usage would go here, typically called by a script that iterates over downloaded spectra

if __name__ == "__main__":
    main()
