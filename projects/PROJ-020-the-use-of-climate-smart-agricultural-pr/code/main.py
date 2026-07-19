import logging
import sys
from pathlib import Path
from data.download import download_lsms, download_nasa_power, download_faostat
from data.clean import run_sampling_pipeline, clean_and_merge, apply_imputation_weights, validate_imputation_quality, get_imputation_report
from utils.config import get_target_countries, get_target_years, get_data_dir, get_processed_data_dir
from utils.logging import initialize_logging, flush_provenance_cache
from analysis.model import run_mixed_effects_model, run_mediation_analysis, calculate_fdr_adjusted_pvalues
from analysis.robustness import run_robustness_pipeline
from viz.plots import main as viz_main

def main():
    """
    Orchestrate the full data pipeline: Download -> Clean -> Save.
    This script enforces prerequisites before execution and ensures
    the final deliverable is produced.
    """
    logger = initialize_logging()
    logger.info("Starting llmXive data pipeline (T019).")
    
    # 1. Prerequisite Checks
    # Check for data-model.md (T007b)
    data_model_path = Path("specs/001-csa-food-security/data-model.md")
    if not data_model_path.exists():
        raise FileNotFoundError(
            f"Prerequisite missing: {data_model_path}. "
            "Task T007b (data-model.md definition) must be completed first."
        )
    
    # 2. Check for the expected final deliverable path (Enforcement)
    # The task requires us to PRODUCE it. We check if it exists AFTER running,
    # but we also verify the path is valid.
    processed_dir = get_processed_data_dir()
    expected_deliverable = processed_dir / "merged_sample.parquet"
    
    # Ensure the directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Initialize Directories
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    state_dir = data_dir / "state"
    figures_dir = data_dir.parent / "figures"
    
    for d in [raw_dir, state_dir, figures_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # 4. Step 1: Download Data
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
    
    # 5. Step 2: Clean, Merge, Impute, and Sample
    logger.info("Step 2: Running cleaning, merging, and sampling pipeline...")
    output_path = run_sampling_pipeline(raw_dir, processed_dir)
    
    if not output_path or not output_path.exists():
        logger.error("Data pipeline failed to produce output.")
        raise RuntimeError("Data pipeline failed to produce output.")
    
    logger.info(f"Data pipeline completed. Output: {output_path}")
    
    # 6. Validate Quality
    report = get_imputation_report()
    if report:
        logger.info(f"Imputation Report: {report}")
    
    # 7. Verify Final Deliverable (Enforcement)
    # This is the critical check required by the task description.
    # It MUST raise FileNotFoundError if the file is missing.
    if not expected_deliverable.exists():
        raise FileNotFoundError(
            f"Critical Deliverable Missing: {expected_deliverable} was not created by the pipeline. "
            "The pipeline must write this file to disk."
        )
    
    logger.info(f"Verified deliverable exists: {expected_deliverable}")
    logger.info("Data pipeline (T019) completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())