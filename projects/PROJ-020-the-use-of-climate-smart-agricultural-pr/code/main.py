import logging
import sys
from pathlib import Path
from data.download import download_lsms, download_nasa_power, download_faostat
from data.clean import run_sampling_pipeline, clean_and_merge, apply_imputation_weights, validate_imputation_quality, get_imputation_report
from utils.config import get_target_countries, get_target_years, get_data_dir
from utils.logging import initialize_logging, flush_provenance_cache
from analysis.model import run_mixed_effects_model, run_mediation_analysis, calculate_fdr_adjusted_pvalues
from analysis.robustness import run_robustness_pipeline
from viz.plots import main as viz_main

def main():
    """
    Orchestrate the full analysis and visualization pipeline:
    1. Download raw data (LSMS, FAOSTAT, NASA POWER)
    2. Clean, merge, impute, and sample
    3. Run Mixed-Effects Modeling and Diagnostics
    4. Run Robustness Checks (Bootstrap, Leave-One-Region-Out)
    5. Generate Visualizations (Scatter, Coefficient, Distribution, Maps)
    6. Save all outputs to data/processed/ and figures/
    """
    logger = initialize_logging()
    logger.info("Starting llmXive full analysis pipeline for T037.")
    
    # Initialize directories
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    state_dir = data_dir / "state"
    figures_dir = data_dir.parent / "figures"
    
    for d in [raw_dir, processed_dir, state_dir, figures_dir]:
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
    
    # Step 2: Clean, Merge, Impute, and Sample
    logger.info("Step 2: Running cleaning, merging, and sampling pipeline...")
    output_path = run_sampling_pipeline(raw_dir, processed_dir)
    
    if not output_path or not output_path.exists():
        logger.error("Data pipeline failed to produce output.")
        raise RuntimeError("Data pipeline failed to produce output.")
    
    logger.info(f"Data pipeline completed. Output: {output_path}")
    
    # Validate quality
    report = get_imputation_report()
    if report:
        logger.info(f"Imputation Report: {report}")
    
    # Step 3: Run Statistical Modeling
    logger.info("Step 3: Running Mixed-Effects Model and Mediation Analysis...")
    model_results_path = run_mixed_effects_model(processed_dir, figures_dir)
    if model_results_path:
        logger.info(f"Model results saved to {model_results_path}")
    
    logger.info("Step 3b: Running Mediation Analysis...")
    mediation_results_path = run_mediation_analysis(processed_dir, figures_dir)
    if mediation_results_path:
        logger.info(f"Mediation results saved to {mediation_results_path}")
    
    # Step 4: Run Robustness Checks
    logger.info("Step 4: Running Robustness Checks (Bootstrap & Leave-One-Region-Out)...")
    robustness_results_path = run_robustness_pipeline(processed_dir, figures_dir)
    if robustness_results_path:
        logger.info(f"Robustness results saved to {robustness_results_path}")
    
    # Step 5: Generate Visualizations
    logger.info("Step 5: Generating Visualizations...")
    viz_main()
    
    # Step 6: Flush Provenance
    logger.info("Step 6: Flushing provenance cache...")
    flush_provenance_cache(state_dir / "provenance_log.json")
    logger.info("Provenance log flushed to state/provenance_log.json.")
    
    logger.info("Full analysis pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())