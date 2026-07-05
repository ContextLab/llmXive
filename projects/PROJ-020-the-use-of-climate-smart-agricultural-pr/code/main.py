import logging
import sys
from pathlib import Path
from data.download import download_lsms, download_nasa_power, download_faostat
from data.clean import run_sampling_pipeline, clean_and_merge, apply_imputation_weights, validate_imputation_quality, get_imputation_report
from utils.config import get_target_countries, get_target_years, get_data_dir
from utils.logging import initialize_logging, flush_provenance_cache

def main():
    """
    Orchestrate the full data pipeline:
    1. Download raw data (LSMS, FAOSTAT, NASA POWER)
    2. Clean, merge, and impute
    3. Apply sampling weights and stratification
    4. Save the final processed dataset
    """
    logger = initialize_logging()
    logger.info("Starting llmXive data pipeline for T019.")
    
    # Initialize directories
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    state_dir = data_dir / "state"
    
    for d in [raw_dir, processed_dir, state_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download Data
    logger.info("Step 1: Initiating data download...")
    countries = get_target_countries()
    years = get_target_years()
    
    # Download LSMS data
    logger.info(f"Downloading LSMS data for {countries}...")
    lsms_paths = []
    for country in countries:
        for year in years:
            try:
                path = download_lsms(country, year)
                if path:
                    lsms_paths.append(path)
                    logger.info(f"Downloaded LSMS {country} {year} -> {path}")
            except Exception as e:
                logger.warning(f"Failed to download LSMS {country} {year}: {e}")
    
    # Download FAOSTAT data
    logger.info(f"Downloading FAOSTAT data for {countries}...")
    faostat_paths = []
    for country in countries:
        try:
            path = download_faostat(country)
            if path:
                faostat_paths.append(path)
                logger.info(f"Downloaded FAOSTAT {country} -> {path}")
        except Exception as e:
            logger.warning(f"Failed to download FAOSTAT {country}: {e}")
    
    # Download NASA POWER data (requires coordinates, handled in clean.py or specific logic)
    # For the entry point, we assume coordinates are available in LSMS or a config file
    # The clean.py logic will handle the actual NASA POWER fetching if needed based on LSMS coordinates.
    logger.info("NASA POWER data will be fetched during the cleaning phase based on survey coordinates.")
    
    # Step 2: Clean, Merge, Impute, and Sample
    logger.info("Step 2: Running cleaning, merging, and sampling pipeline...")
    
    # The run_sampling_pipeline function orchestrates:
    # - Loading raw data
    # - Merging on country/year
    # - Imputing missing values
    # - Calculating design weights
    # - Stratified sampling
    # - Saving the final parquet
    
    output_path = run_sampling_pipeline(raw_dir, processed_dir)
    
    if output_path and output_path.exists():
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
        
        # Validate quality
        report = get_imputation_report()
        if report:
            logger.info(f"Imputation Report: {report}")
    else:
        logger.error("Pipeline completed but no output file was generated.")
        raise RuntimeError("Data pipeline failed to produce output.")
    
    # Step 3: Flush Provenance
    logger.info("Step 3: Flushing provenance cache...")
    flush_provenance_cache(state_dir / "provenance_log.json")
    logger.info("Provenance log flushed to state/provenance_log.json.")
    
    logger.info("All tasks completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())