"""
T034: Moderator Analysis Implementation

Calls the moderator R script (code/R/03_fit_moderator.R), reads the base model
results from results/model_summary.csv, calculates the AIC difference, and extracts
the interaction coefficient and p-value.
"""
import os
import sys
import logging
import subprocess
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import from existing project utilities
from config import get_config
from logging_config import init_project_logging, log_memory_status

# Ensure we can import from the code directory
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

logger = logging.getLogger(__name__)

def load_base_model_results(base_model_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the base PGLS model results from results/model_summary.csv.
    Returns a dictionary with the model statistics.
    """
    if not base_model_path.exists():
        logger.error(f"Base model results file not found: {base_model_path}")
        return None

    try:
        with open(base_model_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                logger.error("Base model results file is empty")
                return None
            # Assuming single row for base model
            return rows[0]
    except Exception as e:
        logger.error(f"Failed to read base model results: {e}")
        return None

def run_moderator_r_script(
    r_script_path: Path,
    data_path: Path,
    tree_path: Path,
    output_path: Path
) -> Tuple[bool, str]:
    """
    Execute the moderator R script via subprocess.
    Returns (success, message).
    """
    if not r_script_path.exists():
        return False, f"R script not found: {r_script_path}"
    if not data_path.exists():
        return False, f"Input data not found: {data_path}"
    if not tree_path.exists():
        return False, f"Phylogeny tree not found: {tree_path}"

    cmd = [
        "Rscript",
        str(r_script_path),
        "--data", str(data_path),
        "--tree", str(tree_path),
        "--output", str(output_path)
    ]

    logger.info(f"Running moderator R script: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"R script failed with code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            logger.error(error_msg)
            return False, error_msg
        
        logger.info(f"Moderator R script completed successfully")
        if result.stdout:
            logger.info(f"R script output: {result.stdout.strip()}")
        return True, "Success"
        
    except subprocess.TimeoutExpired:
        error_msg = "R script execution timed out"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to execute R script: {e}"
        logger.error(error_msg)
        return False, error_msg

def load_moderator_results(moderator_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the moderator model results from the output CSV.
    Returns a dictionary with the model statistics.
    """
    if not moderator_path.exists():
        logger.error(f"Moderator model results file not found: {moderator_path}")
        return None

    try:
        with open(moderator_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                logger.error("Moderator model results file is empty")
                return None
            return rows[0]
    except Exception as e:
        logger.error(f"Failed to read moderator model results: {e}")
        return None

def calculate_aic_difference(base_aic: float, moderator_aic: float) -> float:
    """
    Calculate the AIC difference between the moderator and base models.
    AIC_diff = AIC_moderator - AIC_base
    Negative values indicate the moderator model is better.
    """
    return moderator_aic - base_aic

def extract_interaction_stats(
    moderator_results: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Extract the interaction coefficient and p-value from the moderator results.
    The interaction term is expected to be 'telomere_length:migration_statusMigratory'
    or similar, depending on how R names the factor interaction.
    """
    interaction_coef = None
    interaction_pval = None
    interaction_term_name = None

    # Look for the interaction term in the results
    # The term name might vary, so we search for terms containing 'migration' and 'telomere'
    # or specifically the interaction pattern
    for key, value in moderator_results.items():
        key_lower = key.lower()
        if 'interaction' in key_lower or ('migration' in key_lower and 'telomere' in key_lower):
            if 'coef' in key_lower or 'estimate' in key_lower:
                try:
                    interaction_coef = float(value)
                    interaction_term_name = key
                except (ValueError, TypeError):
                    pass
            elif 'p.value' in key_lower or 'pvalue' in key_lower or 'p_val' in key_lower:
                try:
                    interaction_pval = float(value)
                except (ValueError, TypeError):
                    pass

    # If we found the coefficient but not the p-value (or vice versa), try alternative column names
    if interaction_coef is None:
        for key in ['interaction_coef', 'telomere_length:migration_statusMigratory_coef', 'coef_interaction']:
            if key in moderator_results:
                try:
                    interaction_coef = float(moderator_results[key])
                    interaction_term_name = key
                    break
                except (ValueError, TypeError):
                    pass

    if interaction_pval is None:
        for key in ['interaction_pval', 'telomere_length:migration_statusMigratory_pval', 'p_value_interaction']:
            if key in moderator_results:
                try:
                    interaction_pval = float(moderator_results[key])
                    break
                except (ValueError, TypeError):
                    pass

    if interaction_coef is not None and interaction_pval is not None:
        return {
            "interaction_term": interaction_term_name,
            "interaction_coef": interaction_coef,
            "interaction_p_value": interaction_pval
        }
    
    logger.warning("Could not extract both interaction coefficient and p-value from moderator results")
    return None

def save_moderator_analysis_results(
    results_path: Path,
    base_model: Dict[str, Any],
    moderator_model: Dict[str, Any],
    aic_diff: float,
    interaction_stats: Optional[Dict[str, Any]]
) -> bool:
    """
    Save the moderator analysis results to a CSV file.
    """
    try:
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_path, 'w', newline='') as f:
            fieldnames = [
                'metric', 'value', 'base_model_value', 'moderator_model_value', 'interpretation'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Base model stats
            writer.writerow({
                'metric': 'base_aic',
                'value': base_model.get('aic', ''),
                'base_model_value': base_model.get('aic', ''),
                'moderator_model_value': '',
                'interpretation': 'AIC of base model (lifespan ~ telomere_length)'
            })
            
            # Moderator model stats
            writer.writerow({
                'metric': 'moderator_aic',
                'value': moderator_model.get('aic', ''),
                'base_model_value': '',
                'moderator_model_value': moderator_model.get('aic', ''),
                'interpretation': 'AIC of moderator model (lifespan ~ telomere_length * migration_status)'
            })
            
            # AIC difference
            writer.writerow({
                'metric': 'aic_difference',
                'value': f"{aic_diff:.4f}",
                'base_model_value': '',
                'moderator_model_value': '',
                'interpretation': 'AIC_diff = AIC_moderator - AIC_base (negative = moderator better)'
            })
            
            # Interaction stats
            if interaction_stats:
                writer.writerow({
                    'metric': 'interaction_term',
                    'value': interaction_stats['interaction_term'],
                    'base_model_value': '',
                    'moderator_model_value': '',
                    'interpretation': 'Name of the interaction term'
                })
                writer.writerow({
                    'metric': 'interaction_coef',
                    'value': f"{interaction_stats['interaction_coef']:.4f}",
                    'base_model_value': '',
                    'moderator_model_value': '',
                    'interpretation': 'Coefficient for the interaction term'
                })
                writer.writerow({
                    'metric': 'interaction_p_value',
                    'value': f"{interaction_stats['interaction_p_value']:.4f}",
                    'base_model_value': '',
                    'moderator_model_value': '',
                    'interpretation': 'P-value for the interaction term'
                })
            else:
                writer.writerow({
                    'metric': 'interaction_coef',
                    'value': '',
                    'base_model_value': '',
                    'moderator_model_value': '',
                    'interpretation': 'Could not extract interaction coefficient'
                })
                writer.writerow({
                    'metric': 'interaction_p_value',
                    'value': '',
                    'base_model_value': '',
                    'moderator_model_value': '',
                    'interpretation': 'Could not extract interaction p-value'
                })
        
        logger.info(f"Moderator analysis results saved to {results_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save moderator analysis results: {e}")
        return False

def main():
    """
    Main entry point for the moderator analysis task (T034).
    """
    # Initialize logging
    log_memory_status()
    logger.info("Starting moderator analysis (T034)")

    # Get configuration
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data'))
    results_dir = Path(config.get('results_dir', 'results'))
    
    # Define paths
    base_model_path = results_dir / 'model_summary.csv'
    moderator_r_script = code_dir / 'R' / '03_fit_moderator.R'
    processed_data_path = data_dir / 'processed' / 'merged_data.csv'
    tree_path = data_dir / 'phylogeny' / 'bird_tree.newick'
    moderator_results_path = results_dir / 'moderator_model_summary.csv'
    final_analysis_path = results_dir / 'moderator_analysis_results.csv'

    # Step 1: Load base model results
    logger.info(f"Loading base model results from {base_model_path}")
    base_model = load_base_model_results(base_model_path)
    if not base_model:
        logger.error("Cannot proceed without base model results. T025 must be completed first.")
        sys.exit(1)

    try:
        base_aic = float(base_model.get('aic', 0))
        logger.info(f"Base model AIC: {base_aic}")
    except (ValueError, TypeError):
        logger.error("Could not parse base model AIC value")
        sys.exit(1)

    # Step 2: Run the moderator R script
    logger.info(f"Running moderator R script: {moderator_r_script}")
    success, message = run_moderator_r_script(
        moderator_r_script,
        processed_data_path,
        tree_path,
        moderator_results_path
    )
    
    if not success:
        logger.error(f"Moderator R script failed: {message}")
        sys.exit(1)

    # Step 3: Load moderator model results
    logger.info(f"Loading moderator model results from {moderator_results_path}")
    moderator_model = load_moderator_results(moderator_results_path)
    if not moderator_model:
        logger.error("Could not load moderator model results")
        sys.exit(1)

    try:
        moderator_aic = float(moderator_model.get('aic', 0))
        logger.info(f"Moderator model AIC: {moderator_aic}")
    except (ValueError, TypeError):
        logger.error("Could not parse moderator model AIC value")
        sys.exit(1)

    # Step 4: Calculate AIC difference
    aic_diff = calculate_aic_difference(base_aic, moderator_aic)
    logger.info(f"AIC difference (Moderator - Base): {aic_diff:.4f}")
    if aic_diff < 0:
        logger.info("Moderator model has lower AIC (better fit)")
    elif aic_diff > 2:
        logger.info("Significant improvement with moderator model (AIC diff > 2)")
    else:
        logger.info("Minimal difference between models")

    # Step 5: Extract interaction statistics
    interaction_stats = extract_interaction_stats(moderator_model)
    if interaction_stats:
        logger.info(f"Interaction coefficient: {interaction_stats['interaction_coef']:.4f}")
        logger.info(f"Interaction p-value: {interaction_stats['interaction_p_value']:.4f}")
        if interaction_stats['interaction_p_value'] < 0.05:
            logger.info("Interaction effect is statistically significant (p < 0.05)")
        else:
            logger.info("Interaction effect is not statistically significant (p >= 0.05)")
    else:
        logger.warning("Could not extract interaction statistics")

    # Step 6: Save final analysis results
    if save_moderator_analysis_results(
        final_analysis_path,
        base_model,
        moderator_model,
        aic_diff,
        interaction_stats
    ):
        logger.info("Moderator analysis completed successfully")
        logger.info(f"Results saved to {final_analysis_path}")
    else:
        logger.error("Failed to save moderator analysis results")
        sys.exit(1)

if __name__ == "__main__":
    main()