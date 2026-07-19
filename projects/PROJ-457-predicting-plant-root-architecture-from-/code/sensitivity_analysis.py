import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import from sibling modules as per API surface
from config import get_config, setup_logging
from modeling import fit_lmm

# Setup logger
logger = setup_logging()

# Literature ranges for nutrient coefficients (Phosphorus and Nitrogen)
# These are hardcoded physiological ranges from literature as per task constraint.
# Format: (lower_bound, upper_bound) for the coefficient of nutrient -> root_metric
LITERATURE_RANGES = {
    "phosphorus": {
        "mean": 0.45,
        "std": 0.15,
        "lower": 0.15,
        "upper": 0.75
    },
    "nitrogen": {
        "mean": 0.38,
        "std": 0.12,
        "lower": 0.14,
        "upper": 0.62
    }
}

def load_model_coefficients(model_artifact_path: str) -> Dict[str, Any]:
    """
    Loads the model artifact containing LMM coefficients.
    Expects the artifact to be a JSON file with 'lmm' -> 'coefficients'.
    """
    if not os.path.exists(model_artifact_path):
        raise FileNotFoundError(f"Model artifact not found at {model_artifact_path}")
    
    with open(model_artifact_path, 'r') as f:
        data = json.load(f)
    
    if 'lmm' not in data or 'coefficients' not in data['lmm']:
        raise ValueError(f"Invalid model artifact structure at {model_artifact_path}")
    
    return data['lmm']['coefficients']

def extract_lmm_coefficients(coefficients: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
    """
    Extracts observed coefficients and confidence intervals for nutrient predictors.
    Returns a dict: { nutrient_name: (observed_coeff, ci_lower) }
    Note: CI is expected as [lower, upper] in the model artifact.
    """
    extracted = {}
    
    # We look for nutrient columns. Assuming the model artifact stores coefficients
    # with keys like 'phosphorus', 'nitrogen' or similar.
    for nutrient, data in coefficients.items():
        if nutrient in LITERATURE_RANGES:
            # Expecting data to have 'coef' and 'conf_int' keys
            coef = data.get('coef')
            conf_int = data.get('conf_int') # Expected to be [lower, upper]
            
            if coef is not None and conf_int is not None:
                extracted[nutrient] = {
                    'observed': float(coef),
                    'ci': [float(conf_int[0]), float(conf_int[1])]
                }
    
    return extracted

def compare_against_literature(extracted_coeffs: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Compares extracted coefficients against literature ranges.
    Returns a list of analysis results.
    """
    results = []
    
    for nutrient, data in extracted_coeffs.items():
        lit = LITERATURE_RANGES[nutrient]
        
        observed = data['observed']
        ci = data['ci']
        
        lit_mean = lit['mean']
        lit_lower = lit['lower']
        lit_upper = lit['upper']
        
        # Calculate percent deviation from literature mean
        if lit_mean != 0:
            percent_deviation = ((observed - lit_mean) / lit_mean) * 100
        else:
            percent_deviation = 0.0 if observed == 0 else float('inf')
        
        # Check overlap with literature range
        # Overlap if the confidence interval intersects with the literature range
        overlap = not (ci[1] < lit_lower or ci[0] > lit_upper)
        
        results.append({
            "nutrient": nutrient,
            "percent_deviation": round(percent_deviation, 4),
            "literature_mean": lit_mean,
            "observed_coefficient": round(observed, 4),
            "confidence_interval": [round(ci[0], 4), round(ci[1], 4)],
            "literature_overlap": overlap
        })
    
    return results

def calculate_sensitivity_metrics(results: List[Dict]) -> Dict[str, Any]:
    """
    Aggregates sensitivity metrics.
    Since the task asks for a single JSON output, we assume we might focus on a primary nutrient
    or aggregate. However, the requirement says "Generate artifacts/sensitivity/sensitivity_analysis.json"
    with specific keys. If multiple nutrients exist, we will create an entry for each,
    or if the task implies a single aggregate, we might average. 
    Given the keys in the prompt (percent_deviation, literature_mean, etc. are singular),
    but we have multiple nutrients, we will structure the output as a list of these objects
    if multiple exist, or just the object if one exists. 
    
    Re-reading prompt: "Output: Generate ... sensitivity_analysis.json. Required Keys: ...".
    It implies a single object structure. However, we have P and N. 
    To be safe and complete, we will output a JSON object where keys are nutrients 
    mapping to these result objects, OR if the task implies a summary, we might need to pick one.
    But usually sensitivity analysis covers all. 
    Let's produce a list of such objects to be robust, or a dict keyed by nutrient.
    The prompt's "Required Keys" list looks like a single record schema.
    Let's assume the output file should contain a list of these records if multiple nutrients,
    or we can output a dict with nutrient names as keys.
    
    Actually, looking at the strict requirement: "Required Keys: ...". 
    If I output a list, the keys are inside the list items.
    Let's output a JSON object with a key "results" containing the list, 
    OR simply the list itself. 
    However, to be most compatible with a "single object" expectation if the parser is strict:
    If there are multiple, we might need to summarize or output a list.
    Let's output a list of dictionaries, each matching the required keys.
    """
    return results

def run_sensitivity_analysis(model_artifact_path: str, output_path: str) -> None:
    """
    Orchestrates the sensitivity analysis and writes the output JSON.
    """
    logger.info(f"Starting sensitivity analysis using model artifact: {model_artifact_path}")
    
    # Load coefficients
    coefficients = load_model_coefficients(model_artifact_path)
    
    # Extract relevant nutrient coefficients
    extracted = extract_lmm_coefficients(coefficients)
    
    if not extracted:
        logger.warning("No nutrient coefficients found for sensitivity analysis.")
        # Write empty or error result?
        results = []
    else:
        # Compare against literature
        results = compare_against_literature(extracted)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write results
    # The task requires specific keys. If multiple nutrients, we output a list of objects.
    # If the downstream expects a single object, this might need adjustment, but 
    # scientifically we have multiple coefficients.
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis results written to {output_path}")

def main():
    config = get_config()
    
    # Default paths based on project structure
    model_artifact_path = config.get("MODEL_ARTIFACT_PATH", "artifacts/models/model_results.json")
    output_path = config.get("SENSITIVITY_OUTPUT_PATH", "artifacts/sensitivity/sensitivity_analysis.json")
    
    # If the model artifact path is not in config, try standard locations
    if not os.path.exists(model_artifact_path):
        # Try relative to project root
        possible_paths = [
            "artifacts/models/model_results.json",
            "artifacts/models/lmm_results.json",
            "artifacts/reports/model_metrics.json"
        ]
        found = False
        for p in possible_paths:
            if os.path.exists(p):
                model_artifact_path = p
                found = True
                break
        if not found:
            logger.error("Could not locate model artifact for sensitivity analysis.")
            # We must fail loudly if we can't find the input
            raise FileNotFoundError("Model artifact not found. Cannot perform sensitivity analysis.")
    
    run_sensitivity_analysis(model_artifact_path, output_path)

if __name__ == "__main__":
    main()