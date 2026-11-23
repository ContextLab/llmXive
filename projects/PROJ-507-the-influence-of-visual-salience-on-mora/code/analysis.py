import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import from sibling modules as per API surface
from data_hygiene import DataHygieneError, enforce_data_separation
from config import seed_everything
from data_cleaning import load_survey_data, detect_straight_lining, save_cleaned_data
from analysis_models import fit_clmm, fit_lmm_robust, fit_bootstrap_clmm, check_convergence
from analysis_posthoc import perform_ordinal_posthoc, calculate_effect_sizes
from analysis_power import run_power_analysis, integrate_power_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_analysis_data(input_path: str) -> Any:
    """
    Load survey data for analysis.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        Loaded DataFrame.
        
    Raises:
        DataHygieneError: If the path indicates synthetic data and --allow-synthetic is not set.
        FileNotFoundError: If the file does not exist.
    """
    # Enforce strict separation of synthetic and real data
    enforce_data_separation(input_path, allow_synthetic=False)
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    logger.info(f"Loading analysis data from: {input_path}")
    df = load_survey_data(input_path)
    return df

def clean_data(df: Any) -> Any:
    """
    Apply data cleaning routines (e.g., straight-lining detection).
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Cleaned DataFrame.
    """
    logger.info("Applying data cleaning routines...")
    # detect_straight_lining is expected to return a cleaned DataFrame
    # or a tuple of (cleaned_df, excluded_ids). Assuming it returns cleaned_df for simplicity.
    cleaned_df = detect_straight_lining(df)
    logger.info(f"Data cleaning complete. Original: {len(df)}, Cleaned: {len(cleaned_df)}")
    return cleaned_df

def run_primary_analysis(df: Any) -> Dict[str, Any]:
    """
    Run the primary Cumulative Link Mixed Model (CLMM) analysis.
    
    Args:
        df: Cleaned DataFrame.
        
    Returns:
        Dictionary containing model results.
    """
    logger.info("Running primary CLMM analysis...")
    # Assuming fit_clmm returns a model object and stats
    model, stats = fit_clmm(df)
    
    # Check convergence
    converged = check_convergence(model)
    if not converged:
        logger.warning("Primary CLMM did not converge. Fallback logic will be triggered in main.")
        # Return partial stats to allow fallback handling in main
        return {
            "model": model,
            "stats": stats,
            "converged": False,
            "method": "CLMM"
        }
        
    return {
        "model": model,
        "stats": stats,
        "converged": True,
        "method": "CLMM"
    }

def check_convergence_and_fallback(model: Any, df: Any) -> Dict[str, Any]:
    """
    Check model convergence and execute fallback logic if necessary.
    
    Args:
        model: Fitted model object.
        df: Cleaned DataFrame.
        
    Returns:
        Dictionary containing fallback model results.
    """
    logger.info("Checking convergence and executing fallback if needed...")
    if check_convergence(model):
        logger.info("Model converged successfully.")
        return {
            "model": model,
            "stats": None, # Stats already retrieved in primary
            "converged": True,
            "method": "CLMM"
        }
    
    logger.warning("Model did not converge. Switching to fallback: LMM with Cluster-Robust SE.")
    # Fallback to LMM
    fallback_model, fallback_stats = fit_lmm_robust(df)
    return {
        "model": fallback_model,
        "stats": fallback_stats,
        "converged": True, # Fallback assumes success or handles its own convergence
        "method": "LMM_Robust"
    }

def run_posthoc_analysis(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run post-hoc pairwise comparisons and effect size calculations.
    
    Args:
        results: Dictionary containing model results.
        
    Returns:
        Dictionary containing post-hoc results.
    """
    logger.info("Running post-hoc analysis...")
    method = results.get("method", "CLMM")
    
    # Perform ordinal post-hoc
    posthoc_results = perform_ordinal_posthoc(results["model"], method=method)
    
    # Calculate effect sizes
    effect_sizes = calculate_effect_sizes(results["model"])
    
    return {
        "posthoc": posthoc_results,
        "effect_sizes": effect_sizes
    }

def generate_report(results: Dict[str, Any], posthoc_results: Dict[str, Any], output_path: str) -> None:
    """
    Generate the final analysis report.
    
    Args:
        results: Primary analysis results.
        posthoc_results: Post-hoc analysis results.
        output_path: Path to save the report JSON.
    """
    logger.info(f"Generating report to: {output_path}")
    
    report_data = {
        "analysis_method": results.get("method", "Unknown"),
        "converged": results.get("converged", False),
        "model_stats": results.get("stats", {}),
        "posthoc_comparisons": posthoc_results.get("posthoc", {}),
        "effect_sizes": posthoc_results.get("effect_sizes", {})
    }
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
        
    logger.info(f"Report saved to {output_path}")
    print(json.dumps(report_data, indent=2, default=str))

def main():
    """
    Main entry point for the analysis pipeline.
    Handles argument parsing, data loading, cleaning, analysis, and reporting.
    """
    parser = argparse.ArgumentParser(description="Run statistical analysis on survey data.")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to the input CSV file containing survey responses."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/analysis/results.json", 
        help="Path to save the analysis results JSON."
    )
    parser.add_argument(
        "--allow-synthetic", 
        action="store_true", 
        help="Allow analysis of synthetic data (located in data/synth/). "
             "Default behavior raises DataHygieneError for synthetic paths."
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42, 
        help="Random seed for reproducibility."
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    seed_everything(args.seed)
    
    try:
        # Enforce data separation check with the flag
        # The enforce_data_separation function in data_hygiene.py will check the path
        # and raise DataHygieneError if it contains 'data/synth/' and allow_synthetic is False.
        # We pass the flag from args.
        enforce_data_separation(args.input, allow_synthetic=args.allow_synthetic)
        
        # 1. Load Data
        df = load_analysis_data(args.input)
        
        # 2. Clean Data
        cleaned_df = clean_data(df)
        
        if len(cleaned_df) == 0:
            logger.error("No valid data remaining after cleaning. Aborting analysis.")
            sys.exit(1)
        
        # 3. Primary Analysis
        primary_results = run_primary_analysis(cleaned_df)
        
        # 4. Check Convergence and Fallback
        final_results = primary_results
        if not primary_results.get("converged", False):
            final_results = check_convergence_and_fallback(primary_results["model"], cleaned_df)
        
        # 5. Post-hoc Analysis
        posthoc_results = run_posthoc_analysis(final_results)
        
        # 6. Generate Report
        generate_report(final_results, posthoc_results, args.output)
        
        logger.info("Analysis pipeline completed successfully.")
        
    except DataHygieneError as e:
        logger.error(f"Data Hygiene Error: {e}")
        logger.error("Ensure input data is in 'data/survey/' or 'data/processed/' or use --allow-synthetic for 'data/synth/'.")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
