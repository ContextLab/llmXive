"""
Main entry point for the full analysis pipeline.
Orchestrates download, clean, model, viz, and robustness steps.
"""
import logging
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data.download import download_lsms, download_nasa_power, download_faostat
from data.clean import run_sampling_pipeline, clean_and_merge, apply_imputation_weights, validate_imputation_quality, get_imputation_report
from utils.config import get_target_countries, get_target_years, get_data_dir, get_processed_data_dir
from utils.logging import initialize_logging

def main():
    """Run the full pipeline."""
    logger = initialize_logging(name="main")
    logger.log("main_started")
    
    try:
        # Step 1: Download data
        logger.log("starting_download")
        countries = get_target_countries()
        years = get_target_years()
        
        for country in countries:
            for year in years:
                download_lsms(country, year)
                # Download climate data for each country (approximate coords)
                coords = {
                    "Kenya": (-1.2921, 36.8219),
                    "India": (28.6139, 77.2090),
                    "Vietnam": (21.0285, 105.8542)
                }
                if country in coords:
                    lat, lon = coords[country]
                    download_nasa_power(lat, lon, f"{year}-01-01", f"{year}-12-31")
                download_faostat("CROP_PROD")
        
        logger.log("download_complete")
        
        # Step 2: Run cleaning pipeline
        logger.log("starting_cleaning")
        run_sampling_pipeline()
        logger.log("cleaning_complete")
        
        # Step 3: Run model (placeholder for T023)
        logger.log("modeling_skipped_for_now")
        
        # Step 4: Run viz (placeholder for T031-T034)
        logger.log("visualization_skipped_for_now")
        
        logger.log("main_complete")
        return 0
        
    except Exception as e:
        logger.log("main_error", error=str(e))
        raise

if __name__ == "__main__":
    sys.exit(main())