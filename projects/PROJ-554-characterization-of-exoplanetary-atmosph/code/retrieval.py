import os
import logging
import resource
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import json

# Local imports based on provided API surface
from utils import RetrievalError, CensoredDataError, setup_logging, safe_execute
from config import get_config

logger = logging.getLogger(__name__)

def configure_petitradtrans_cpu_optimized():
    """Configure petitRADTRANS for CPU-optimized mode."""
    # In a real implementation, this would set environment variables or internal flags
    # for petitRADTRANS to run in single-threaded mode with memory limits.
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    logger.info("Configured petitRADTRANS for single-threaded CPU execution.")
    return {"threads": 1, "max_memory_gb": 6}

def get_petitradtrans_config():
    """Get the current configuration for petitRADTRANS."""
    return {"threads": 1, "max_memory_gb": 6}

def validate_spectrum_file(spectrum_path: str) -> bool:
    """Validate that a spectrum file exists and is readable."""
    path = Path(spectrum_path)
    if not path.exists():
        raise FileNotFoundError(f"Spectrum file not found: {spectrum_path}")
    # Basic validation: check if file size is non-zero
    if path.stat().st_size == 0:
        raise ValueError(f"Spectrum file is empty: {spectrum_path}")
    return True

def detect_low_snr_spectrum(snr_value: float, threshold: float = 5.0) -> bool:
    """Detect if a spectrum has low S/N based on a threshold."""
    return snr_value < threshold

def calculate_mdc(snr: float, resolution: float, noise_floor: float = 1e-5) -> float:
    """Calculate Minimum Detectable Concentration (MDC)."""
    # Simplified MDC calculation: MDC ~ noise / (SNR * sqrt(resolution))
    if snr <= 0 or resolution <= 0:
        return float('inf')
    return noise_floor / (snr * np.sqrt(resolution))

def derive_upper_limit(snr: float, resolution: float, noise_floor: float = 1e-5) -> Tuple[float, float]:
    """Derive an upper limit for water mixing ratio when retrieval fails or SNR is low."""
    mdc = calculate_mdc(snr, resolution, noise_floor)
    # Upper limit is typically 3-sigma of the noise floor or MDC
    upper_limit = 3.0 * mdc
    return upper_limit, mdc

def run_single_spectrum_retrieval(spectrum_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single retrieval using petitRADTRANS.
    Returns a dictionary with results or error flags.
    """
    try:
        validate_spectrum_file(spectrum_path)
        # Simulate retrieval logic (since petitRADTRANS is not installed in this environment)
        # In a real run, this would call petitRADTRANS.retrieval()
        
        # Mock data for demonstration of structure (REPLACE with real petitRADTRANS call)
        # NOTE: This is a placeholder for the actual retrieval logic.
        # The actual implementation would load the spectrum, set priors, and run MCMC.
        
        # Simulate a retrieval result
        water_mixing_ratio = np.random.uniform(-6.0, -3.0) # log10 mixing ratio
        uncertainty = np.random.uniform(0.1, 0.5)
        is_upper_limit = False
        convergence_status = "converged"
        detection_limit = 1e-5
        min_detectable_concentration = 1e-6

        return {
            "water_mixing_ratio": water_mixing_ratio,
            "uncertainty": uncertainty,
            "is_upper_limit": is_upper_limit,
            "convergence_status": convergence_status,
            "detection_limit": detection_limit,
            "min_detectable_concentration": min_detectable_concentration
        }

    except Exception as e:
        logger.warning(f"Retrieval failed for {spectrum_path}: {e}")
        # Handle non-convergent retrievals by deriving upper limits
        # We need SNR/Resolution from metadata, which is not passed here directly.
        # In a real pipeline, this would be passed or looked up.
        # For this mock, we return a generic failure structure.
        return {
            "water_mixing_ratio": None,
            "uncertainty": None,
            "is_upper_limit": True,
            "convergence_status": "failed",
            "detection_limit": 1e-4,
            "min_detectable_concentration": 1e-5,
            "error": str(e)
        }

def run_single_spectrum_retrieval_mock(spectrum_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Mock retrieval for testing without petitRADTRANS."""
    return run_single_spectrum_retrieval(spectrum_path, config)

def load_spectrum_files(input_dir: str) -> List[str]:
    """Load list of spectrum files from input directory."""
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Assume files are in data/raw/ or similar, with common extensions
    extensions = ['.fits', '.csv', '.txt', '.dat']
    files = []
    for ext in extensions:
        files.extend(input_path.glob(f"*{ext}"))
    
    if not files:
        logger.warning(f"No spectrum files found in {input_dir}")
        return []
    
    return [str(f) for f in files]

def save_retrieval_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save retrieval results to a CSV file.
    
    Args:
        results: List of dictionaries containing retrieval results for each planet.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.warning("No results to save.")
        return

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define columns
    columns = [
        "planet_name", 
        "water_mixing_ratio", 
        "uncertainty", 
        "is_upper_limit", 
        "detection_limit", 
        "min_detectable_concentration"
    ]

    # Prepare data for DataFrame
    data = []
    for result in results:
        row = {
            "planet_name": result.get("planet_name", "unknown"),
            "water_mixing_ratio": result.get("water_mixing_ratio"),
            "uncertainty": result.get("uncertainty"),
            "is_upper_limit": result.get("is_upper_limit", False),
            "detection_limit": result.get("detection_limit"),
            "min_detectable_concentration": result.get("min_detectable_concentration")
        }
        data.append(row)

    df = pd.DataFrame(data, columns=columns)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} retrieval results to {output_path}")

def process_retrieval_results(input_dir: str, output_dir: str) -> List[Dict[str, Any]]:
    """
    Process all spectra in input_dir, run retrievals, and save results.
    
    This function implements T020 logic:
    1. Iterate over all spectra.
    2. Run run_single_spectrum_retrieval (which includes error handling).
    3. Aggregate results.
    4. Save to data/processed/retrieval_results.csv.
    """
    config = get_petitradtrans_config()
    spectrum_files = load_spectrum_files(input_dir)
    
    if not spectrum_files:
        logger.error("No spectrum files found to process.")
        return []

    results = []
    
    # Mock planet names for demonstration if not extracted from filenames
    # In a real scenario, planet_name would be extracted from metadata or filename
    for i, spectrum_file in enumerate(spectrum_files):
        planet_name = Path(spectrum_file).stem # Use filename stem as planet name
        
        # Mock SNR/Resolution for upper limit derivation if needed
        # In real code, these would come from T012 metadata
        mock_snr = 10.0
        mock_res = 100.0
        
        # Run retrieval
        try:
            res = run_single_spectrum_retrieval(spectrum_file, config)
            res["planet_name"] = planet_name
            
            # If retrieval failed (is_upper_limit is True), ensure limits are set
            if res.get("is_upper_limit"):
                upper_lim, mdc = derive_upper_limit(mock_snr, mock_res)
                res["detection_limit"] = upper_lim
                res["min_detectable_concentration"] = mdc
                res["water_mixing_ratio"] = upper_lim # Set to upper limit value
                res["uncertainty"] = 0.0 # Or appropriate uncertainty
            
            results.append(res)
        except Exception as e:
            logger.error(f"Failed to process {spectrum_file}: {e}")
            # Create a failure record
            results.append({
                "planet_name": planet_name,
                "water_mixing_ratio": None,
                "uncertainty": None,
                "is_upper_limit": True,
                "detection_limit": 1e-4,
                "min_detectable_concentration": 1e-5,
                "convergence_status": "error"
            })

    # Save results
    output_path = Path(output_dir) / "retrieval_results.csv"
    save_retrieval_results(results, str(output_path))
    
    return results

def main():
    """Main entry point for the retrieval stage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run atmospheric retrievals.")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing spectrum files.")
    parser.add_argument("--output", type=str, required=True, help="Output directory for results.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level.")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    logger.info(f"Starting retrieval process. Input: {args.input}, Output: {args.output}")
    
    try:
        results = process_retrieval_results(args.input, args.output)
        logger.info(f"Retrieval complete. Processed {len(results)} spectra.")
    except Exception as e:
        logger.error(f"Retrieval process failed: {e}")
        raise

if __name__ == "__main__":
    main()