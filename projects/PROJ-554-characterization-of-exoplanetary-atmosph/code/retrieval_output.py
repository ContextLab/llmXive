"""
T020: Implement output generation for retrieval results.
Saves results to data/processed/retrieval_results.csv.
"""
import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from config import get_config
from data_models import RetrievalResult, CensorshipStatus
from retrieval import run_single_spectrum_retrieval, get_petitradtrans_config
from utils import setup_logging, handle_non_convergent_retrieval

logger = logging.getLogger(__name__)

def process_retrieval_results(results: List[RetrievalResult], output_path: Path) -> None:
    """
    Writes a list of RetrievalResult objects to a CSV file.
    Handles censored data (upper limits) appropriately.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'planet_name', 
        'equilibrium_temperature', 
        'metallicity', 
        'spectral_resolution', 
        'snr', 
        'category',
        'log10_water_mixing_ratio',
        'uncertainty_1sigma',
        'is_censored',
        'censorship_status',
        'convergence_status',
        'retrieval_error'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for res in results:
            row = {
                'planet_name': res.planet_name,
                'equilibrium_temperature': res.equilibrium_temperature,
                'metallicity': res.metallicity,
                'spectral_resolution': res.spectral_resolution,
                'snr': res.snr,
                'category': res.category.value if hasattr(res.category, 'value') else str(res.category),
                'log10_water_mixing_ratio': res.log10_water_mixing_ratio if res.log10_water_mixing_ratio is not None else '',
                'uncertainty_1sigma': res.uncertainty_1sigma if res.uncertainty_1sigma is not None else '',
                'is_censored': res.is_censored,
                'censorship_status': res.censorship_status.value if hasattr(res.censorship_status, 'value') else str(res.censorship_status),
                'convergence_status': res.convergence_status,
                'retrieval_error': res.retrieval_error if res.retrieval_error else ''
            }
            writer.writerow(row)

    logger.info(f"Retrieval results saved to {output_path}")

def main() -> None:
    """
    Main entry point for T020.
    1. Loads configuration.
    2. Reads metadata from data/processed/metadata.csv (produced by T012).
    3. Runs retrieval for each spectrum (using T019 logic for censored data).
    4. Saves aggregated results to data/processed/retrieval_results.csv.
    """
    setup_logging()
    config = get_config()
    
    metadata_path = Path(config['data_dir']) / 'processed' / 'metadata.csv'
    output_path = Path(config['data_dir']) / 'processed' / 'retrieval_results.csv'
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}. Run T012 first.")

    # Read metadata
    metadata_list = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metadata_list.append(row)

    logger.info(f"Processing {len(metadata_list)} spectra for retrieval...")
    
    results: List[RetrievalResult] = []
    
    # Configuration for petitRADTRANS
    prtrans_config = get_petitradtrans_config()

    for idx, meta in enumerate(metadata_list):
        planet_name = meta['planet_name']
        spectrum_file = Path(config['data_dir']) / 'raw' / meta['spectrum_filename']
        
        if not spectrum_file.exists():
            logger.warning(f"Spectrum file missing for {planet_name}: {spectrum_file}")
            # Create a failed result entry
            result = RetrievalResult(
                planet_name=planet_name,
                equilibrium_temperature=float(meta['equilibrium_temperature']) if meta['equilibrium_temperature'] else None,
                metallicity=float(meta['metallicity']) if meta['metallicity'] else None,
                spectral_resolution=int(meta['spectral_resolution']) if meta['spectral_resolution'] else None,
                snr=float(meta['snr']) if meta['snr'] else None,
                category=meta['category'],
                log10_water_mixing_ratio=None,
                uncertainty_1sigma=None,
                is_censored=False,
                censorship_status=CensorshipStatus.UNDETERMINED,
                convergence_status="FAILED_FILE_NOT_FOUND",
                retrieval_error="Spectrum file not found"
            )
            results.append(result)
            continue

        try:
            # Run retrieval
            res = run_single_spectrum_retrieval(
                spectrum_path=spectrum_file,
                config=prtrans_config,
                equilibrium_temperature=float(meta['equilibrium_temperature']) if meta['equilibrium_temperature'] else None,
                metallicity=float(meta['metallicity']) if meta['metallicity'] else None,
                snr=float(meta['snr']) if meta['snr'] else None,
                spectral_resolution=int(meta['spectral_resolution']) if meta['spectral_resolution'] else None
            )
            results.append(res)
            
            if res.convergence_status == "FAILED":
                logger.warning(f"Retrieval failed for {planet_name}, attempting upper limit derivation.")
                # T019 logic is embedded in run_single_spectrum_retrieval, 
                # but we log if it fell back to censored.
                if res.is_censored:
                    logger.info(f"Derived upper limit for {planet_name}.")

        except Exception as e:
            logger.error(f"Error processing {planet_name}: {e}")
            # Handle non-convergent or failed retrievals gracefully
            results.append(handle_non_convergent_retrieval(
                planet_name=planet_name,
                meta=meta,
                error_msg=str(e)
            ))

        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(metadata_list)} spectra.")

    process_retrieval_results(results, output_path)
    logger.info("T020 completed successfully.")

if __name__ == "__main__":
    main()
