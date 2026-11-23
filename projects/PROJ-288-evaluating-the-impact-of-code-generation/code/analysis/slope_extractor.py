import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from analysis.simex_correction import load_analysis_results, save_analysis_results
from data.logging_config import get_logger

logger = get_logger(__name__)

def extract_code_size_slope(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract the slope coefficient for 'code_lines_changed' from the LMER results.
    
    This implements SC-003: Extract the impact of code size on review time.
    
    Args:
        results: The analysis results dictionary containing LMER output.
                
    Returns:
        A dictionary containing the extracted slope coefficient and metadata.
    """
    code_size_slope = None
    p_value = None
    
    # Check if LMER results exist
    if 'lmer' not in results:
        logger.warning("No LMER results found in analysis_results.json")
        return {
            "code_size_slopes": None,
            "note": "LMER analysis not performed or failed"
        }
    
    lmer_results = results['lmer']
    
    # Extract fixed effects coefficients
    if 'coefficients' in lmer_results:
        coefficients = lmer_results['coefficients']
        
        # Look for code_lines_changed in the coefficients
        # The structure might be a dict or list depending on serialization
        if isinstance(coefficients, dict):
            if 'code_lines_changed' in coefficients:
                code_size_slope = coefficients['code_lines_changed'].get('estimate')
                p_value = coefficients['code_lines_changed'].get('p_value')
            elif 'lines_changed' in coefficients:
                code_size_slope = coefficients['lines_changed'].get('estimate')
                p_value = coefficients['lines_changed'].get('p_value')
        elif isinstance(coefficients, list):
            for coeff in coefficients:
                if coeff.get('term') in ['code_lines_changed', 'lines_changed']:
                    code_size_slope = coeff.get('estimate')
                    p_value = coeff.get('p_value')
                    break
    
    # If SIMEX was applied, try to get the corrected slope
    if 'simex_corrected_coefficients' in results:
        simex_results = results['simex_corrected_coefficients']
        if isinstance(simex_results, dict) and 'code_lines_changed' in simex_results:
            code_size_slope = simex_results['code_lines_changed'].get('estimate')
            p_value = simex_results['code_lines_changed'].get('p_value')
    
    slope_info = {
        "code_size_slopes": {
            "estimate": code_size_slope,
            "p_value": p_value,
            "interpretation": "Minutes of review time added per line of code changed"
        }
    }
    
    if code_size_slope is None:
        logger.warning("Could not extract code size slope from LMER results")
        slope_info["note"] = "Code size slope not found in coefficients"
    else:
        logger.info(f"Extracted code size slope: {code_size_slope:.6f} (p={p_value})")
        
    return slope_info

def run_slope_extraction(results_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Run the full slope extraction pipeline.
    
    Args:
        results_path: Path to the analysis_results.json file.
        output_path: Path where the updated results will be saved.
        
    Returns:
        The updated analysis results dictionary.
    """
    logger.info(f"Loading analysis results from {results_path}")
    results = load_analysis_results(results_path)
    
    logger.info("Extracting code size slope coefficients")
    slope_info = extract_code_size_slope(results)
    
    # Append the slope information to the results
    results['code_size_slopes'] = slope_info['code_size_slopes']
    
    logger.info(f"Saving updated results to {output_path}")
    save_analysis_results(results, output_path)
    
    return results

def main():
    """Main entry point for the slope extraction script."""
    logger.info("Starting code size slope extraction")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    results_path = project_root / "data" / "analysis_results.json"
    output_path = project_root / "data" / "analysis_results.json"
    
    if not results_path.exists():
        logger.error(f"Analysis results file not found: {results_path}")
        logger.error("Please run the analysis pipeline (T021-T026) first.")
        sys.exit(1)
    
    try:
        results = run_slope_extraction(results_path, output_path)
        
        # Print summary
        if 'code_size_slopes' in results and results['code_size_slopes']:
            slope = results['code_size_slopes'].get('estimate')
            p_val = results['code_size_slopes'].get('p_value')
            print(f"Code Size Impact Analysis:")
            print(f"  Slope: {slope:.6f} minutes per line")
            print(f"  P-value: {p_val}")
            if slope and p_val:
                if p_val < 0.05:
                    print(f"  Result: Statistically significant impact")
                else:
                    print(f"  Result: No statistically significant impact")
        else:
            print("Could not extract code size slope.")
            
        logger.info("Slope extraction completed successfully")
        
    except Exception as e:
        logger.error(f"Error during slope extraction: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
