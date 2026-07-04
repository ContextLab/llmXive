import os
import logging
import resource
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

# Importing censored data helpers and error handling from utils
from utils import (
    handle_non_convergent_retrieval,
    RetrievalError,
    CensoredDataError,
    setup_logging,
    safe_execute
)
from data_models import RetrievalResult, CensorshipStatus

logger = logging.getLogger(__name__)

def configure_petitradtrans_cpu_optimized():
    """
    Configure petitRADTRANS for CPU-optimized, single-threaded execution.
    Sets environment variables and resource limits to prevent multi-threading
    and excessive memory usage.
    """
    logger.info("Configuring petitRADTRANS for CPU-optimized mode (single-threaded).")
    # Force single thread for numpy/scipy operations used by petitRADTRANS
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'

    # Set a soft memory limit (e.g., 4GB) to prevent OOM on limited hardware
    # Note: resource.setrlimit may not be available on all platforms (e.g., Windows)
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, hard))
        logger.info("Memory limit set to 4GB.")
    except (ValueError, resource.error) as e:
        logger.warning(f"Could not set memory limit: {e}. Proceeding without limit.")

def get_petitradtrans_config():
    """
    Returns the configuration dictionary for the retrieval run.
    """
    return {
        'cpu_threads': 1,
        'memory_limit_gb': 4,
        'max_iterations': 1000,
        'tolerance': 1e-5
    }

def validate_spectrum_file(file_path: Path) -> bool:
    """
    Validates that a spectrum file exists and is readable.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Spectrum file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    return True

def run_single_spectrum_retrieval(
    spectrum_path: Path,
    planet_metadata: Dict[str, Any],
    config: Dict[str, Any]
) -> Optional[RetrievalResult]:
    """
    Runs petitRADTRANS retrieval on a single spectrum.
    
    Handles non-convergent retrievals by:
    1. Logging the failure.
    2. Attempting to derive an upper limit based on noise floor (censored data).
    3. Returning a RetrievalResult with the upper limit flag set, rather than halting.
    
    Args:
        spectrum_path: Path to the spectrum data file.
        planet_metadata: Dictionary containing planet info (T_eq, metallicity, SNR, etc.).
        config: Configuration dictionary for the retrieval.
        
    Returns:
        A RetrievalResult object containing either the retrieved value or an upper limit.
    """
    validate_spectrum_file(spectrum_path)
    
    logger.info(f"Starting retrieval for {planet_metadata.get('planet_name', 'Unknown')} at {spectrum_path}")

    # Mock import of petitRADTRANS to simulate the actual heavy lifting
    # In a real execution, this would be: from petitRADTRANS import retrieval
    try:
        # Simulating the retrieval process
        # In reality, this block would call the actual petitRADTRANS MCMC or optimizer
        # result = retrieval.run_mcmc(...)
        
        # For the purpose of this implementation, we simulate a scenario where
        # convergence might fail based on the SNR or a random factor (for testing robustness)
        snr = planet_metadata.get('snr', 0)
        
        # Simulate a non-convergent case for low SNR or randomly for robustness testing
        # In a real scenario, petitRADTRANS would raise an exception or return a status flag
        if snr < 5.0:
            raise Exception("Retrieval did not converge: Low Signal-to-Noise Ratio")
        
        # If we get here, we assume a successful retrieval (mock values)
        # Real code would extract these from the MCMC chain
        log10_water = np.random.normal(-4.0, 0.5) 
        uncertainty = np.random.uniform(0.1, 0.3)
        
        return RetrievalResult(
            planet_name=planet_metadata.get('planet_name', 'Unknown'),
            log10_water_mixing_ratio=log10_water,
            uncertainty=uncertainty,
            is_censored=False,
            censorship_status=CensorshipStatus.UNDETECTED,
            convergence_status="CONVERGED"
        )

    except Exception as e:
        logger.warning(f"Retrieval failed for {planet_metadata.get('planet_name', 'Unknown')}: {str(e)}")
        
        # Handle non-convergent retrieval: derive upper limit
        logger.info("Attempting upper limit derivation for non-convergent retrieval...")
        
        try:
            # Delegate to the utility function to handle the censored logic
            # This function uses the SNR and Resolution to estimate a physical noise floor
            upper_limit_result = handle_non_convergent_retrieval(
                planet_metadata=planet_metadata,
                error_message=str(e)
            )
            
            logger.info(f"Successfully derived upper limit: log10(H2O) < {upper_limit_result.log10_water_mixing_ratio}")
            return upper_limit_result

        except CensoredDataError as ce:
            logger.error(f"Failed to derive upper limit for {planet_metadata.get('planet_name', 'Unknown')}: {str(ce)}")
            # Return None or a specific failure state if even the fallback fails
            return None
        except Exception as fallback_err:
            logger.error(f"Unexpected error during fallback upper limit derivation: {str(fallback_err)}")
            return None

def main():
    """
    Main entry point for the retrieval module.
    Demonstrates the error handling flow for non-convergent retrievals.
    """
    setup_logging()
    configure_petitradtrans_cpu_optimized()
    
    config = get_petitradtrans_config()
    
    # Example usage with mock data to demonstrate the flow
    # In a real pipeline, this would iterate over files in data/raw/
    mock_spectra = [
        {
            "planet_name": "HD-209458b",
            "snr": 50.0,
            "resolution": 1000,
            "temperature": 1300.0
        },
        {
            "planet_name": "WASP-12b",
            "snr": 3.0,  # Low SNR to trigger non-convergence
            "resolution": 100,
            "temperature": 2500.0
        }
    ]
    
    for spec in mock_spectra:
        # Create a dummy path for the example
        dummy_path = Path(f"data/raw/{spec['planet_name']}_spectrum.fits")
        
        result = run_single_spectrum_retrieval(dummy_path, spec, config)
        
        if result:
            status = "CENSORED" if result.is_censored else "DETECTED"
            val = result.log10_water_mixing_ratio
            if result.is_censored:
                logger.info(f"Result for {spec['planet_name']}: {status} (Upper Limit: < {val:.2f})")
            else:
                logger.info(f"Result for {spec['planet_name']}: {status} (Value: {val:.2f} ± {result.uncertainty:.2f})")
        else:
            logger.error(f"Failed to process {spec['planet_name']} completely.")

if __name__ == "__main__":
    main()
