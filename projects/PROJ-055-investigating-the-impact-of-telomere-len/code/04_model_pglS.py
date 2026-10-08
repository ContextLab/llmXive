import os
import sys
import logging
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

# Ensure local imports work if running as script or module
try:
    from config import get_config
    from logging_config import init_project_logging, handle_memory_pressure, log_memory_status
except ImportError:
    # Fallback for direct execution context where path might differ
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config
    from logging_config import init_project_logging, handle_memory_pressure, log_memory_status

logger = logging.getLogger(__name__)

def check_species_power(species_count: int, threshold: int = 15) -> bool:
    """
    Check if the number of species is sufficient for phylogenetic inference.
    
    Args:
        species_count: Number of unique species in the dataset.
        threshold: Minimum number of species required (default 15).
        
    Returns:
        True if power is sufficient, False otherwise.
    """
    if species_count < threshold:
        logger.warning(f"Low Power: Phylogenetic inference unreliable (n={species_count} < {threshold})")
        return False
    return True

def extract_unique_species(data_path: str) -> List[str]:
    """
    Extract unique species names from the merged dataset.
    
    Args:
        data_path: Path to the merged CSV file.
        
    Returns:
        List of unique species names.
    """
    df = pd.read_csv(data_path)
    if 'species' not in df.columns:
        raise ValueError(f"Column 'species' not found in {data_path}")
    
    unique_species = df['species'].dropna().unique().tolist()
    logger.info(f"Extracted {len(unique_species)} unique species from {data_path}")
    return unique_species

def fetch_phylogenetic_tree(species_list: List[str], output_dir: str) -> str:
    """
    Fetch the phylogenetic tree for the given species list using rotl.
    
    Args:
        species_list: List of species names.
        output_dir: Directory to save the Newick tree file.
        
    Returns:
        Path to the saved Newick tree file.
    """
    os.makedirs(output_dir, exist_ok=True)
    tree_path = os.path.join(output_dir, "bird_phylogeny.nwk")
    
    # Check if tree already exists to avoid redundant API calls
    if os.path.exists(tree_path):
        logger.info(f"Phylogenetic tree already exists at {tree_path}")
        return tree_path

    logger.info(f"Fetching phylogenetic tree for {len(species_list)} species via rotl...")
    
    # Use R via rpy2 to call rotl
    ro.r('library(rotl)')
    ro.r('library(ape)')
    
    species_names_r = ro.StrVector(species_list)
    
    # Construct R command to fetch tree
    # We use tnrs to match names, then tol_tree to get the tree
    r_code = f"""
    species <- {species_names_r}
    matched <- tnrs(species)
    tree <- tol_tree(matched$unique_name)
    write.tree(tree, file="{tree_path}")
    """
    
    try:
        ro.r(r_code)
        logger.info(f"Successfully saved phylogenetic tree to {tree_path}")
    except Exception as e:
        logger.error(f"Failed to fetch phylogenetic tree: {e}")
        raise
        
    return tree_path

def run_r_pglS_model(data_path: str, tree_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Run the PGLS model using the R script 01_fit_pglS.R.
    
    Args:
        data_path: Path to the merged CSV data.
        tree_path: Path to the phylogenetic tree file.
        output_dir: Directory for R output files.
        
    Returns:
        Dictionary containing model results (coefficient, se, p_value, lambda).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare paths for R script
    r_script_path = os.path.join(Path(__file__).parent, "R", "01_fit_pglS.R")
    if not os.path.exists(r_script_path):
        raise FileNotFoundError(f"R script not found: {r_script_path}")
    
    # Prepare arguments for R script
    args = [
        "--data", data_path,
        "--tree", tree_path,
        "--output_dir", output_dir
    ]
    
    logger.info(f"Running R PGLS script: {r_script_path} with args {args}")
    
    # We will use subprocess to call Rscript
    import subprocess
    try:
        result = subprocess.run(
            ["Rscript", r_script_path] + args,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"R script stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"R script stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"R script failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise
    
    # The R script is expected to write a summary file, e.g., model_results.csv
    # or we can parse the output. Let's assume the R script writes a CSV.
    # Based on T023 description, it should output summary stats.
    # We will look for a standard output file or parse the stdout if needed.
    # For robustness, let's assume the R script writes to `results/model_summary_raw.csv`
    # or we can read the R output if it prints to console.
    # However, T023 says "outputting ... to results/model_summary.csv" effectively.
    # Let's assume the R script writes a file named `pgls_results.csv` in output_dir.
    
    results_file = os.path.join(output_dir, "pgls_results.csv")
    if os.path.exists(results_file):
        df_res = pd.read_csv(results_file)
        # Expect columns: coefficient, se, p_value, lambda
        if df_res.empty:
            raise ValueError("R script produced an empty results file.")
        row = df_res.iloc[0]
        return {
            "coefficient": float(row.get("coefficient", 0)),
            "se": float(row.get("se", 0)),
            "p_value": float(row.get("p_value", 1.0)),
            "lambda": float(row.get("lambda", 0.0))
        }
    else:
        # Fallback: try to parse stdout if R printed JSON or CSV
        # This is less robust but handles cases where file writing failed
        logger.warning("R script did not produce expected output file. Attempting to parse stdout.")
        # This is a placeholder; ideally R script writes the file.
        # If we can't find it, we raise an error.
        raise FileNotFoundError(f"R script did not produce results file at {results_file}")

def save_model_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save the model results to a CSV file.
    
    Args:
        results: Dictionary containing model results.
        output_path: Path to the output CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df = pd.DataFrame([results])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved model results to {output_path}")
    
    # Log the phylogenetic signal (lambda)
    lambda_val = results.get("lambda", 0.0)
    logger.info(f"Phylogenetic signal (lambda): {lambda_val:.4f}")

def main():
    """
    Main entry point for the PGLS modeling step.
    """
    # Initialize config and logging
    config = get_config()
    init_project_logging(config)
    
    # Check memory pressure
    handle_memory_pressure()
    log_memory_status()
    
    # Paths
    merged_data_path = config.get("paths", {}).get("merged_data", "data/processed/merged_data.csv")
    phylogeny_dir = config.get("paths", {}).get("phylogeny", "data/phylogeny")
    results_dir = config.get("paths", {}).get("results", "results")
    output_csv_path = os.path.join(results_dir, "model_summary.csv")
    
    # Check if merged data exists
    if not os.path.exists(merged_data_path):
        logger.error(f"Merged data file not found: {merged_data_path}")
        sys.exit(1)
    
    # Extract species
    species_list = extract_unique_species(merged_data_path)
    if not species_list:
        logger.error("No species found in merged data.")
        sys.exit(1)
    
    # Check power
    if not check_species_power(len(species_list)):
        # Log the low power message as required by T024
        logger.warning("Low Power: Phylogenetic inference unreliable")
        # We still try to run, but log the warning. 
        # The task says "skip the modeling step" but also "log the exact string".
        # If we skip, we might not produce a result file. 
        # Let's assume we skip the heavy R part but still create a placeholder or exit gracefully.
        # However, T025 requires saving results. If we skip, what do we save?
        # The instruction says "skip the modeling step (do not halt the entire pipeline abruptly)".
        # We will log and return early, perhaps writing a 'skipped' status or just exiting.
        # Given T025 asks to save results, if we skip, we can't save real results.
        # We will log and exit with a specific code or write a 'skipped' record.
        # Let's write a record indicating the model was skipped due to low power.
        skipped_result = {
            "coefficient": None,
            "se": None,
            "p_value": None,
            "lambda": None,
            "status": "skipped_low_power"
        }
        save_model_results(skipped_result, output_csv_path)
        logger.info("Modeling skipped due to low power. Results marked as skipped.")
        return
    
    # Fetch tree
    tree_path = fetch_phylogenetic_tree(species_list, phylogeny_dir)
    
    # Run R model
    try:
        model_results = run_r_pglS_model(merged_data_path, tree_path, results_dir)
        save_model_results(model_results, output_csv_path)
        logger.info("PGLS modeling completed successfully.")
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()