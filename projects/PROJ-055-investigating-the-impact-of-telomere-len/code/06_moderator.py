"""
code/06_moderator.py
Implements the Ecological Moderator Analysis (User Story 3).

This module orchestrates the fitting of the extended PGLS model with an interaction
term (telomere_length * migration_status), calculates AIC differences against the
base model, and extracts interaction statistics.

Dependencies:
- code/04_model_pglS.py (for base model results structure)
- code/R/03_fit_moderator.R (must exist)
- data/processed/merged_data.csv (input)
- results/model_summary.csv (base model output from T025)
"""
import os
import sys
import logging
import subprocess
import csv
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
CODE_DIR = PROJECT_ROOT / "code"
R_SCRIPTS_DIR = CODE_DIR / "R"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "logs" / "moderator_analysis.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("moderator_analysis")

def load_base_model_results() -> Dict[str, Any]:
    """
    Loads the base model results from results/model_summary.csv.
    Returns a dictionary containing coefficient, se, p_value, aic, lambda.
    """
    model_path = RESULTS_DIR / "model_summary.csv"
    
    if not model_path.exists():
        logger.error(f"Base model results file not found: {model_path}")
        raise FileNotFoundError(
            f"Required base model file '{model_path}' not found. "
            "Please ensure T025 (save_model_results) has been completed successfully."
        )
    
    try:
        with open(model_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                raise ValueError("model_summary.csv is empty.")
            
            # Assume single row for base model summary
            row = rows[0]
            
            return {
                'coefficient': float(row.get('coefficient', 0)),
                'se': float(row.get('se', 0)),
                'p_value': float(row.get('p_value', 1.0)),
                'aic': float(row.get('aic', 0.0)),
                'lambda': float(row.get('lambda', 0.0)),
                'species_count': int(row.get('species_count', 0))
            }
    except Exception as e:
        logger.error(f"Failed to load base model results: {e}")
        raise

def run_moderator_r_script() -> bool:
    """
    Executes the R script code/R/03_fit_moderator.R.
    This script fits the PGLS model: lifespan ~ telomere_length * migration_status
    using phylolm and writes results to results/moderator_model_results.csv.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    r_script_path = R_SCRIPTS_DIR / "03_fit_moderator.R"
    
    if not r_script_path.exists():
        logger.error(f"Moderator R script not found: {r_script_path}")
        return False
    
    merged_data_path = DATA_DIR / "processed" / "merged_data.csv"
    phylogeny_path = DATA_DIR / "phylogeny" / "tree.nwk"
    output_path = RESULTS_DIR / "moderator_model_results.csv"
    
    if not merged_data_path.exists():
        logger.error(f"Input merged data not found: {merged_data_path}")
        return False
    
    if not phylogeny_path.exists():
        logger.error(f"Phylogenetic tree not found: {phylogeny_path}")
        return False

    logger.info(f"Executing R script: {r_script_path}")
    logger.info(f"Input data: {merged_data_path}")
    logger.info(f"Tree: {phylogeny_path}")
    logger.info(f"Output: {output_path}")

    try:
        # Construct command
        cmd = [
            "Rscript",
            str(r_script_path),
            "--data", str(merged_data_path),
            "--tree", str(phylogeny_path),
            "--output", str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout:
            logger.info(f"R Script stdout:\n{result.stdout}")
        if result.stderr:
            logger.info(f"R Script stderr:\n{result.stderr}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"R Script execution failed with code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Rscript executable not found. Please ensure R is installed and in PATH.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running R script: {e}")
        return False

def load_moderator_results() -> Dict[str, Any]:
    """
    Loads the results from the moderator model run.
    Expects results/moderator_model_results.csv.
    """
    results_path = RESULTS_DIR / "moderator_model_results.csv"
    
    if not results_path.exists():
        logger.error(f"Moderator results file not found: {results_path}")
        raise FileNotFoundError(
            f"Moderator results file '{results_path}' not found. "
            "Please ensure the R script (03_fit_moderator.R) ran successfully."
        )
    
    try:
        with open(results_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                raise ValueError("moderator_model_results.csv is empty.")
            
            # Expecting interaction term row or full summary
            # We look for the interaction term specifically: telomere_length:migration_status
            interaction_row = None
            base_row = None
            
            for row in rows:
                term = row.get('term', '')
                if 'interaction' in term.lower() or 'telomere_length:migration_status' in term:
                    interaction_row = row
                elif 'telomere_length' in term and 'migration' not in term:
                    base_row = row
            
            if not interaction_row:
                # Fallback: if specific interaction term isn't found, take the last row or first row
                # depending on R output format. Assuming the last row is the interaction if sorted.
                # But safer to raise error if strict schema isn't met.
                logger.warning("Interaction term not explicitly found, checking first row as fallback.")
                interaction_row = rows[0] 
                
            return {
                'interaction_coefficient': float(interaction_row.get('estimate', 0)),
                'interaction_se': float(interaction_row.get('std.error', 0)),
                'interaction_p_value': float(interaction_row.get('p.value', 1.0)),
                'aic': float(interaction_row.get('aic', 0.0)),
                'lambda': float(interaction_row.get('lambda', 0.0)),
                'logLik': float(interaction_row.get('logLik', 0.0))
            }
    except Exception as e:
        logger.error(f"Failed to load moderator results: {e}")
        raise

def calculate_aic_difference(base_results: Dict[str, Any], moderator_results: Dict[str, Any]) -> float:
    """
    Calculates the AIC difference between the moderator model and the base model.
    AIC_diff = AIC_moderator - AIC_base
    
    A negative AIC_diff indicates the moderator model is better.
    """
    aic_base = base_results.get('aic', 0.0)
    aic_mod = moderator_results.get('aic', 0.0)
    
    diff = aic_mod - aic_base
    logger.info(f"AIC Base Model: {aic_base:.4f}")
    logger.info(f"AIC Moderator Model: {aic_mod:.4f}")
    logger.info(f"AIC Difference (Mod - Base): {diff:.4f}")
    
    return diff

def extract_interaction_stats(
    base_results: Dict[str, Any], 
    moderator_results: Dict[str, Any], 
    aic_diff: float
) -> Dict[str, Any]:
    """
    Compiles the final interaction statistics including the p-value and significance.
    """
    p_val = moderator_results.get('interaction_p_value', 1.0)
    is_significant = p_val < 0.05
    
    return {
        'interaction_coefficient': moderator_results['interaction_coefficient'],
        'interaction_se': moderator_results['interaction_se'],
        'interaction_p_value': p_val,
        'interaction_significant': is_significant,
        'aic_base': base_results['aic'],
        'aic_moderator': moderator_results['aic'],
        'aic_difference': aic_diff,
        'improved_model': 'Moderator' if aic_diff < 0 else 'Base'
    }

def save_moderator_analysis_results(stats: Dict[str, Any]) -> None:
    """
    Saves the final analysis results to results/moderator_analysis_summary.csv.
    """
    output_path = RESULTS_DIR / "moderator_analysis_summary.csv"
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=stats.keys())
            writer.writeheader()
            writer.writerow(stats)
        
        logger.info(f"Moderator analysis results saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save moderator analysis results: {e}")
        raise

def main():
    """
    Main entry point for Task T034.
    1. Load base model results (from T025).
    2. Run the moderator R script.
    3. Load moderator results.
    4. Calculate AIC difference.
    5. Extract and save interaction stats.
    """
    logger.info("Starting Moderator Analysis (T034)...")
    
    try:
        # Step 1: Load Base Model
        logger.info("Loading base model results...")
        base_results = load_base_model_results()
        
        # Step 2: Run R Script
        logger.info("Running moderator R script...")
        if not run_moderator_r_script():
            logger.error("Failed to run moderator R script. Aborting.")
            sys.exit(1)
        
        # Step 3: Load Moderator Results
        logger.info("Loading moderator model results...")
        moderator_results = load_moderator_results()
        
        # Step 4: Calculate AIC Difference
        logger.info("Calculating AIC difference...")
        aic_diff = calculate_aic_difference(base_results, moderator_results)
        
        # Step 5: Extract Stats
        logger.info("Extracting interaction statistics...")
        final_stats = extract_interaction_stats(base_results, moderator_results, aic_diff)
        
        # Step 6: Save Results
        logger.info("Saving analysis summary...")
        save_moderator_analysis_results(final_stats)
        
        logger.info("Moderator Analysis (T034) completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during moderator analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())