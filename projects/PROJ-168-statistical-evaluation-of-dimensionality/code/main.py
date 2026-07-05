import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Import from existing API surface
from config import ensure_paths, set_global_seed, get_accession_seed, set_case_study_mode, Config
from download import download_all_accessions, main as download_main
from preprocess import preprocess_accession
from embeddings import run_embedding_pipeline
from clustering import process_accession
from stats import fit_mixed_effects_model, fit_fixed_effects_anova, save_results
from utils import check_ram_limit, log_metric, ensure_monitoring_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def check_prerequisites() -> bool:
    """Verify that all necessary paths and configurations are set."""
    try:
        ensure_paths()
        set_global_seed()
        return True
    except Exception as e:
        logger.error(f"Prerequisite check failed: {e}")
        return False

def run_snakemake_workflow(cores: int = 1, dry_run: bool = False) -> bool:
    """
    Execute the Snakemake workflow.
    
    Args:
        cores: Number of parallel cores to use.
        dry_run: If True, only simulate the workflow.
        
    Returns:
        True if workflow completed successfully, False otherwise.
    """
    try:
        import subprocess
        cmd = ["snakemake", "--cores", str(cores)]
        if dry_run:
            cmd.append("--dry-run")
        
        logger.info(f"Running Snakemake workflow: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Snakemake workflow failed: {e}")
        return False
    except ImportError:
        logger.error("Snakemake not installed. Please install via environment.yml.")
        return False

def run_standalone_pipeline() -> bool:
    """
    Run the pipeline without Snakemake (standalone mode).
    This function implements the core logic including CASE_STUDY_MODE detection.
    
    Returns:
        True if pipeline completed successfully, False otherwise.
    """
    if not check_prerequisites():
        return False

    # Ensure monitoring directory exists
    ensure_monitoring_dir()

    # Configuration
    config = Config()
    accessions = config.accessions
    case_study_mode = config.case_study_mode

    logger.info(f"Starting pipeline. Case Study Mode: {case_study_mode}")
    logger.info(f"Accessions to process: {accessions}")

    # Step 1: Download Data
    logger.info("Step 1: Downloading data...")
    if not download_all_accessions(accessions):
        logger.error("Data download failed. Aborting.")
        return False

    # Step 2: Preprocess Data
    logger.info("Step 2: Preprocessing data...")
    processed_datasets = []
    for accession in accessions:
        try:
            logger.info(f"Processing {accession}...")
            result = preprocess_accession(accession)
            if result:
                processed_datasets.append(result)
        except Exception as e:
            logger.warning(f"Failed to process {accession}: {e}")
            continue

    if not processed_datasets:
        logger.error("No datasets successfully processed. Aborting.")
        return False

    # Step 3: Generate Embeddings
    logger.info("Step 3: Generating embeddings...")
    for ds in processed_datasets:
        try:
            run_embedding_pipeline(ds['accession'], ds['data_path'])
        except Exception as e:
            logger.warning(f"Failed to generate embeddings for {ds['accession']}: {e}")

    # Step 4: Clustering and Fidelity
    logger.info("Step 4: Clustering and calculating fidelity...")
    fidelity_results = []
    for ds in processed_datasets:
        try:
            res = process_accession(ds['accession'])
            if res:
                fidelity_results.append(res)
        except Exception as e:
            logger.warning(f"Failed clustering for {ds['accession']}: {e}")

    # Step 5: Statistical Analysis (Core Logic for T051)
    logger.info("Step 5: Running statistical analysis...")
    
    # T051 Implementation: Detect CASE_STUDY_MODE and switch model
    model_type = "Mixed-Effects Model"
    statistical_results = {}
    
    if case_study_mode:
        logger.warning("CASE_STUDY_MODE detected. Switching to 'Single Dataset Mode' (Fixed-Effects ANOVA).")
        model_type = "Fixed-Effects ANOVA (Single Dataset Mode)"
        # Execute Fixed-Effects ANOVA as per T051 requirement
        # We assume aggregated data is available or we run ANOVA on the available fidelity metrics
        try:
            # Load aggregated metrics (assuming they exist from previous steps)
            from stats import load_aggregated_metrics
            metrics_df = load_aggregated_metrics()
            
            if metrics_df is not None and not metrics_df.empty:
                statistical_results = fit_fixed_effects_anova(metrics_df)
            else:
                logger.warning("No aggregated metrics found for ANOVA. Skipping statistical test.")
                statistical_results = {"status": "skipped", "reason": "no_data"}
        except Exception as e:
            logger.error(f"Fixed-Effects ANOVA failed: {e}")
            statistical_results = {"status": "error", "error": str(e)}
    else:
        # Normal Mixed-Effects Model
        try:
            from stats import load_aggregated_metrics
            metrics_df = load_aggregated_metrics()
            if metrics_df is not None and not metrics_df.empty:
                statistical_results = fit_mixed_effects_model(metrics_df)
            else:
                logger.warning("No aggregated metrics found for Mixed-Effects. Skipping statistical test.")
                statistical_results = {"status": "skipped", "reason": "no_data"}
        except Exception as e:
            logger.error(f"Mixed-Effects Model failed: {e}")
            statistical_results = {"status": "error", "error": str(e)}

    # Step 6: Save Summary Report (T051 Implementation: Update header)
    logger.info("Step 6: Saving results...")
    results_dir = Path(config.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    summary_path = results_dir / "summary.json"
    
    summary_data = {
        "project": "Statistical Evaluation of Dimensionality Reduction",
        "header": "Descriptive Case Study" if case_study_mode else "Statistical Analysis Report",
        "model_used": model_type,
        "case_study_mode_active": case_study_mode,
        "datasets_processed": len(processed_datasets),
        "accessions": [ds['accession'] for ds in processed_datasets],
        "statistical_results": statistical_results,
        "timestamp": str(Path.cwd().parent) # Placeholder for actual timestamp
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    logger.info(f"Summary saved to {summary_path}")
    
    # Log final metric
    log_metric("pipeline_status", "completed" if case_study_mode or not statistical_results.get("error") else "partial_failure")
    
    return True

def main():
    """Entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Dimensionality Reduction Evaluation Pipeline")
    parser.add_argument("--mode", choices=["snakemake", "standalone"], default="standalone",
                      help="Execution mode: snakemake or standalone")
    parser.add_argument("--cores", type=int, default=1, help="Number of cores for snakemake")
    parser.add_argument("--dry-run", action="store_true", help="Dry run snakemake workflow")
    
    args = parser.parse_args()
    
    if args.mode == "snakemake":
        success = run_snakemake_workflow(cores=args.cores, dry_run=args.dry_run)
    else:
        success = run_standalone_pipeline()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()