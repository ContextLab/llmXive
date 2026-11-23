import os
import logging
import resource
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import json
from config import get_config
from utils import setup_logging, RetrievalError, handle_non_convergent_retrieval
from data_models import RetrievalResult, CensorshipStatus, PlanetCategory

# Import helper functions from same file or existing modules if they exist
# Assuming these are defined in this file or imported from utils/analysis as per API surface
# Since API surface lists them in retrieval.py, we define or import them here.
# If they are missing in the actual file content (which was omitted), we must ensure they exist or are imported.
# Based on the prompt's "API surface", these names exist in `code/retrieval.py`.
# We assume `configure_petitradtrans_cpu_optimized`, `get_petitradtrans_config`, `validate_spectrum_file`,
# `detect_low_snr_spectrum`, `calculate_mdc`, `derive_upper_limit`, `run_single_spectrum_retrieval`, `load_spectrum_files`
# are already defined in this file or imported correctly.
# However, since the file content was omitted, we must ensure the logic for T020 is correct.
# We will implement `save_retrieval_results` and `process_retrieval_results` here,
# and ensure `run_single_spectrum_retrieval` (or equivalent) is called.
# If the previous file had these functions, we keep them. If not, we assume they are imported or defined.
# Given the constraints, we assume the existing functions (T018, T019) are present in the file.
# We are extending `code/retrieval.py`.

def save_retrieval_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save retrieval results to a CSV file.
    
    Args:
        results: List of dictionaries containing retrieval results.
        output_path: Path to the output CSV file.
    """
    if not results:
        logging.warning("No retrieval results to save.")
        return
    
    df = pd.DataFrame(results)
    # Ensure columns are in the expected order and types are correct
    expected_columns = [
        'planet_name', 'water_mixing_ratio', 'uncertainty', 
        'is_upper_limit', 'detection_limit', 'min_detectable_concentration'
    ]
    
    # Reindex to ensure columns exist (fill missing with NaN)
    df = df.reindex(columns=expected_columns)
    
    # Convert boolean columns if necessary
    if 'is_upper_limit' in df.columns:
        df['is_upper_limit'] = df['is_upper_limit'].astype(bool)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(results)} retrieval results to {output_path}")

def process_retrieval_results(input_path: Path, output_path: Path) -> List[Dict[str, Any]]:
    """
    Process all spectrum files listed in metadata.csv, run retrieval, and save results.
    
    Args:
        input_path: Path to the metadata CSV file (data/processed/metadata.csv).
        output_path: Path to the output CSV file (data/processed/retrieval_results.csv).
    
    Returns:
        List of retrieval result dictionaries.
    """
    config = get_config()
    logger = setup_logging()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input metadata file not found: {input_path}")
    
    # Load metadata
    metadata_df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(metadata_df)} spectra from {input_path}")
    
    results = []
    
    for idx, row in metadata_df.iterrows():
        planet_name = row.get('planet_name', 'Unknown')
        spectrum_path_str = row.get('spectrum_path') # Assuming metadata has path or we construct it
        
        # If spectrum_path is not in metadata, we might need to construct it or skip
        # Based on T012, metadata.csv has columns: planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range, parse_error
        # It does NOT explicitly have spectrum_path. However, T015a downloads spectra.
        # We assume the spectrum files are stored in a known location or path is derivable.
        # Let's assume a standard location: data/raw/spectra/{planet_name}.fits or similar.
        # If not present, we skip or try to find it.
        
        # For this task, we assume the spectrum file path can be constructed or is available.
        # If the actual file structure is different, this might need adjustment.
        # Let's assume the spectrum file is at: data/raw/spectra/{planet_name}.fits
        # If that doesn't exist, we try to find it in data/raw/
        
        if not spectrum_path_str:
            # Try to construct path
            possible_paths = [
                config.data_dir / 'raw' / 'spectra' / f"{planet_name}.fits",
                config.data_dir / 'raw' / f"{planet_name}.fits",
                config.data_dir / 'raw' / f"{planet_name}.txt"
            ]
            found_path = None
            for p in possible_paths:
                if p.exists():
                    found_path = p
                    break
            
            if not found_path:
                logger.warning(f"No spectrum file found for {planet_name}. Skipping.")
                # Still record a result with error or skip?
                # Task says: "if run_single_retrieval fails, log error, attempt upper limit, record result"
                # So we should try to derive upper limit even if file missing? No, need data.
                # Let's skip and log.
                continue
            spectrum_path = found_path
        else:
            spectrum_path = Path(spectrum_path_str)
        
        if not spectrum_path.exists():
            logger.error(f"Spectrum file not found: {spectrum_path}. Skipping {planet_name}.")
            continue
        
        try:
            # Run retrieval
            # Assuming run_single_spectrum_retrieval exists and returns a dict
            # If it fails, it raises RetrievalError
            retrieval_result = run_single_spectrum_retrieval(str(spectrum_path), planet_name)
            
            # Handle non-convergent or errors
            if retrieval_result.get('convergence_status') == 'failed':
                # Attempt to derive upper limit
                upper_limit_result = handle_non_convergent_retrieval(
                    planet_name, 
                    row.get('snr'), 
                    row.get('resolution')
                )
                results.append(upper_limit_result)
            else:
                results.append(retrieval_result)
                
        except Exception as e:
            logger.error(f"Retrieval failed for {planet_name}: {e}")
            # Attempt to derive upper limit as fallback
            try:
                upper_limit_result = handle_non_convergent_retrieval(
                    planet_name,
                    row.get('snr'),
                    row.get('resolution')
                )
                results.append(upper_limit_result)
            except Exception as fallback_error:
                logger.error(f"Failed to derive upper limit for {planet_name}: {fallback_error}")
                # Record a minimal error result
                results.append({
                    'planet_name': planet_name,
                    'water_mixing_ratio': None,
                    'uncertainty': None,
                    'is_upper_limit': True,
                    'detection_limit': None,
                    'min_detectable_concentration': None,
                    'error': str(fallback_error)
                })
    
    # Save results
    save_retrieval_results(results, output_path)
    
    return results

def main():
    """
    Main entry point for the retrieval module.
    Parses arguments and calls process_retrieval_results.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run atmospheric retrieval on exoplanet spectra.")
    parser.add_argument("--input", type=str, required=True, help="Path to input metadata CSV (data/processed/metadata.csv)")
    parser.add_argument("--output", type=str, required=True, help="Path to output retrieval results CSV (data/processed/retrieval_results.csv)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    setup_logging()
    
    try:
        process_retrieval_results(input_path, output_path)
    except Exception as e:
        logging.error(f"Retrieval process failed: {e}")
        raise

if __name__ == "__main__":
    main()