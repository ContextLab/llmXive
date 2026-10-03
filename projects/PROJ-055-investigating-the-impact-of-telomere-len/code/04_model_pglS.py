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

# Configure logging
from logging_config import init_project_logging, log_memory_status
from config import get_config

# Initialize logging for this module
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
    return species_count >= threshold

def fetch_phylogenetic_tree(species_list: List[str], tree_path: Path) -> Optional[Path]:
    """
    Fetch phylogenetic tree for the given species list using rotl (via R).
    
    Args:
        species_list: List of species names.
        tree_path: Path to save the Newick tree file.
        
    Returns:
        Path to the saved tree file, or None if fetching fails.
    """
    logger.info(f"Fetching phylogenetic tree for {len(species_list)} species...")
    
    try:
        # Initialize R environment
        ro.r('library(rotl)')
        ro.r('library(ape)')
        
        # Convert species list to R character vector
        species_r = ro.StrVector(species_list)
        
        # Fetch tree using rotl
        # Note: This might fail if species names don't match exactly
        ro.r(f'''
            species_list <- {list(species_list)}
            tree <- tol_tree(species_list)
            write.tree(tree, file="{tree_path}")
        ''')
        
        if tree_path.exists():
            logger.info(f"Phylogenetic tree saved to {tree_path}")
            return tree_path
        else:
            logger.error("Tree file was not created by R script")
            return None
            
    except Exception as e:
        logger.error(f"Failed to fetch phylogenetic tree: {str(e)}")
        return None

def extract_unique_species(data_path: Path) -> List[str]:
    """
    Extract unique species names from the merged dataset.
    
    Args:
        data_path: Path to the merged CSV file.
        
    Returns:
        List of unique species names.
    """
    logger.info(f"Extracting unique species from {data_path}")
    
    try:
        df = pd.read_csv(data_path)
        if 'species' not in df.columns:
            raise ValueError("Column 'species' not found in merged data")
        
        unique_species = df['species'].unique().tolist()
        logger.info(f"Found {len(unique_species)} unique species")
        return unique_species
        
    except Exception as e:
        logger.error(f"Failed to extract species: {str(e)}")
        raise

def run_r_pglS_model(data_path: Path, tree_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Run the PGLS model using the R script.
    
    Args:
        data_path: Path to the merged CSV file.
        tree_path: Path to the phylogenetic tree file.
        output_path: Path to save the R output (if any).
        
    Returns:
        Dictionary containing model results.
    """
    logger.info("Running PGLS model via R script...")
    
    try:
        # Initialize R environment
        pandas2ri.activate()
        
        # Load the R script
        r_script_path = Path("code/R/01_fit_pglS.R")
        if not r_script_path.exists():
            raise FileNotFoundError(f"R script not found: {r_script_path}")
        
        # Read and execute R script
        with open(r_script_path, 'r') as f:
            r_code = f.read()
        
        # Replace placeholders with actual paths
        r_code = r_code.replace("{{DATA_PATH}}", str(data_path))
        r_code = r_code.replace("{{TREE_PATH}}", str(tree_path))
        r_code = r_code.replace("{{OUTPUT_PATH}}", str(output_path))
        
        # Execute R code
        ro.r(r_code)
        
        # Extract results from R environment if saved there
        # This assumes the R script saves results to a global variable or file
        results = {}
        
        # Try to extract lambda if available
        try:
            lambda_val = ro.r['lambda_value']
            if lambda_val is not None:
                results['lambda'] = float(lambda_val[0])
        except:
            logger.warning("Lambda value not found in R environment")
        
        logger.info("PGLS model completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Failed to run PGLS model: {str(e)}")
        raise

def save_model_results(model_results: Dict[str, Any], output_path: Path, lambda_value: float) -> None:
    """
    Save model results to a CSV file and log the phylogenetic signal (lambda).
    
    Args:
        model_results: Dictionary containing model statistics (coefficient, SE, p-value, etc.)
        output_path: Path to save the results CSV.
        lambda_value: The phylogenetic signal (lambda) value.
    """
    logger.info(f"Saving model results to {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for CSV
    result_row = {
        'parameter': 'telomere_length',
        'estimate': model_results.get('coefficient', None),
        'std_error': model_results.get('std_error', None),
        'p_value': model_results.get('p_value', None),
        'lambda': lambda_value
    }
    
    # Write to CSV
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=result_row.keys())
        writer.writeheader()
        writer.writerow(result_row)
    
    # Log the phylogenetic signal
    logger.info(f"Phylogenetic signal (lambda): {lambda_value:.4f}")
    
    # Also log to a separate log file for easy access
    log_path = Path("logs/phylogenetic_signal.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(f"Lambda: {lambda_value:.4f}\n")
    
    logger.info(f"Model results saved to {output_path}")
    logger.info(f"Phylogenetic signal logged to {log_path}")

def main():
    """Main function to execute the PGLS modeling pipeline."""
    # Initialize configuration
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    
    # Set up paths
    merged_data_path = project_root / "data" / "processed" / "merged_data.csv"
    tree_dir = project_root / "data" / "phylogeny"
    tree_path = tree_dir / "bird_phylogeny.tre"
    results_dir = project_root / "results"
    output_path = results_dir / "model_summary.csv"
    
    # Ensure directories exist
    tree_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize logging
    init_project_logging()
    log_memory_status()
    
    logger.info("Starting PGLS modeling pipeline...")
    
    try:
        # Check if merged data exists
        if not merged_data_path.exists():
            raise FileNotFoundError(f"Merged data not found: {merged_data_path}")
        
        # Extract unique species
        species_list = extract_unique_species(merged_data_path)
        
        # Check species power
        if not check_species_power(len(species_list)):
            logger.warning("Low Power: Phylogenetic inference unreliable")
            logger.warning(f"Only {len(species_list)} species found, minimum required: 15")
            # Log this warning but continue if possible
            # Create a placeholder result indicating low power
            low_power_result = {
                'parameter': 'telomere_length',
                'estimate': None,
                'std_error': None,
                'p_value': None,
                'lambda': None,
                'status': 'Low Power'
            }
            
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=low_power_result.keys())
                writer.writeheader()
                writer.writerow(low_power_result)
            
            logger.info("Low power warning logged to results/model_summary.csv")
            return
        
        # Fetch phylogenetic tree
        if not tree_path.exists():
            tree_path = fetch_phylogenetic_tree(species_list, tree_path)
            if tree_path is None:
                raise RuntimeError("Failed to fetch phylogenetic tree")
        
        # Run PGLS model
        model_results = run_r_pglS_model(merged_data_path, tree_path, output_path)
        
        # Extract lambda value from model results or R environment
        # This might need adjustment based on how the R script returns results
        lambda_value = model_results.get('lambda', 0.0)
        
        # Save model results
        save_model_results(model_results, output_path, lambda_value)
        
        logger.info("PGLS modeling pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"PGLS modeling pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
