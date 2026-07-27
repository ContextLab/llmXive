"""
Task T040: Generate analysis_results.json containing coefficients, SEs, p-values, adjusted p-values, and CI.

This script loads the results from the statistical analysis pipeline (GLMM/ZINB),
applies Bonferroni correction if not already applied in the model runner,
formats the results into a structured JSON artifact, and writes it to
data/derived/analysis_results.json.

It depends on the `code/analyze.py` module which performs the actual modeling.
"""
import os
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Import analysis functions from the existing module
from analyze import (
    load_master_dataset,
    clean_data,
    run_glmm,
    run_zinb_model,
    apply_bonferroni_correction,
    run_analysis
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_confidence_interval(coeff: float, se: float, z_score: float = 1.96) -> dict:
    """Calculate 95% Confidence Interval."""
    lower = coeff - (z_score * se)
    upper = coeff + (z_score * se)
    return {
        "lower": round(lower, 6),
        "upper": round(upper, 6),
        "level": 0.95
    }

def extract_model_results(model_result, model_type: str, variable_name: str) -> dict:
    """
    Extract coefficients, SEs, p-values, and CIs from a statsmodels results object.
    
    Args:
        model_result: The fitted model results object.
        model_type: Type of model ('glmm' or 'zinb').
        variable_name: The specific variable name to extract (e.g., 'llm_adoption_flag').
    
    Returns:
        Dictionary with formatted results.
    """
    try:
        # statsmodels summary2 or params/summary extraction
        params = model_result.params
        bse = model_result.bse
        pvalues = model_result.pvalues
        
        # Handle different output structures based on model type
        if variable_name in params.index:
            coeff = float(params[variable_name])
            se = float(bse[variable_name])
            pval = float(pvalues[variable_name])
            
            ci = format_confidence_interval(coeff, se)
            
            return {
                "variable": variable_name,
                "model_type": model_type,
                "coefficient": round(coeff, 6),
                "std_error": round(se, 6),
                "p_value": round(pval, 6),
                "confidence_interval": ci,
                "significant_at_0.05": pval < 0.05,
                "significant_at_0.01": pval < 0.01
            }
        else:
            logger.warning(f"Variable {variable_name} not found in model results for {model_type}")
            return None
    except Exception as e:
        logger.error(f"Error extracting results for {variable_name} in {model_type}: {e}")
        return None

def run_derivation_pipeline():
    """
    Main pipeline to generate analysis_results.json.
    """
    # Paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "derived"
    output_file = data_dir / "analysis_results.json"
    
    # Ensure output directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading master dataset from {data_dir / 'master_dataset.csv'}")
    df = load_master_dataset()
    
    if df is None or df.empty:
        logger.error("Master dataset is empty or missing. Cannot run analysis.")
        return False
    
    logger.info("Cleaning data...")
    df_clean = clean_data(df)
    
    if df_clean.empty:
        logger.error("Cleaned data is empty. Check cleaning logic.")
        return False
    
    logger.info("Running GLMM analysis...")
    glmm_results = run_glmm(df_clean)
    
    logger.info("Running ZINB analysis...")
    zinb_results = run_zinb_model(df_clean)
    
    # Structure to hold all results
    final_results = {
        "metadata": {
            "dataset_rows": len(df_clean),
            "dataset_columns": list(df_clean.columns),
            "analysis_date": pd.Timestamp.now().isoformat(),
            "models_used": ["GLMM", "ZINB"]
        },
        "models": {}
    }
    
    # Extract GLMM results
    if glmm_results:
        logger.info("Extracting GLMM results...")
        # Assuming run_glmm returns a dict or object with 'results' and 'formula'
        # We need to extract specific variables of interest
        # Common variables: llm_adoption_flag, domain_complexity, project_size
        target_vars = ['llm_adoption_flag', 'domain_complexity', 'project_size', 'diff_complexity_score']
        
        glmm_extracted = []
        if hasattr(glmm_results, 'results'):
            res_obj = glmm_results.results
            for var in target_vars:
                # Try to find the variable in the params index
                # statsmodels might use different naming (e.g., 'C(llm_adoption_flag)[T.1]')
                found = False
                for idx in res_obj.params.index:
                    if var in idx:
                        result = extract_model_results(res_obj, "GLMM", idx)
                        if result:
                            result["target_variable"] = var
                            glmm_extracted.append(result)
                            found = True
                if not found:
                    # Fallback: try direct match if exact name exists
                    result = extract_model_results(res_obj, "GLMM", var)
                    if result:
                        result["target_variable"] = var
                        glmm_extracted.append(result)
        
        final_results["models"]["GLMM"] = {
            "results": glmm_extracted,
            "formula": getattr(glmm_results, 'formula', "N/A")
        }
        
        # Apply Bonferroni correction to p-values
        logger.info("Applying Bonferroni correction...")
        corrected_results = apply_bonferroni_correction(glmm_extracted)
        final_results["models"]["GLMM"]["results_corrected"] = corrected_results

    # Extract ZINB results
    if zinb_results:
        logger.info("Extracting ZINB results...")
        target_vars = ['llm_adoption_flag', 'domain_complexity', 'project_size']
        
        zinb_extracted = []
        # ZINB model usually has two parts: count and zero-inflation
        # We'll try to extract from both if available
        if isinstance(zinb_results, dict):
            for part_name, res_obj in zinb_results.items():
                for var in target_vars:
                    found = False
                    for idx in res_obj.params.index:
                        if var in idx:
                            result = extract_model_results(res_obj, f"ZINB_{part_name}", idx)
                            if result:
                                result["model_part"] = part_name
                                result["target_variable"] = var
                                zinb_extracted.append(result)
                                found = True
                    if not found:
                        result = extract_model_results(res_obj, f"ZINB_{part_name}", var)
                        if result:
                            result["model_part"] = part_name
                            result["target_variable"] = var
                            zinb_extracted.append(result)
        
        final_results["models"]["ZINB"] = {
            "results": zinb_extracted,
            "formula": getattr(zinb_results, 'formula', "N/A") if not isinstance(zinb_results, dict) else "Dual-part model"
        }
        
        # Apply Bonferroni correction to ZINB results
        if zinb_extracted:
            corrected_zinb = apply_bonferroni_correction(zinb_extracted)
            final_results["models"]["ZINB"]["results_corrected"] = corrected_zinb
    
    # Write to JSON
    logger.info(f"Writing results to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    logger.info(f"Successfully generated {output_file}")
    return True

def main():
    success = run_derivation_pipeline()
    if not success:
        logger.error("Derivation pipeline failed.")
        exit(1)
    else:
        logger.info("Derivation pipeline completed successfully.")

if __name__ == "__main__":
    main()