import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from logging_config import setup_logging

# Configure logging
logger = setup_logging("serialize_results")

def serialize_model_results(
    results: Dict[str, Any],
    output_dir: str = "results/models",
    filename_prefix: str = "model_results"
) -> str:
    """
    Serialize model results to JSON with explicit associational framing.
    
    This function ensures all output metadata explicitly states that findings
    are associational and not causal, complying with project constraints.
    
    Args:
        results: Dictionary containing model outputs (coefficients, p-values, etc.)
        output_dir: Directory to save the results file
        filename_prefix: Prefix for the output filename
        
    Returns:
        Path to the saved JSON file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.json")
    
    # Create the output payload with explicit associational framing
    output_payload = {
        "metadata": {
            "timestamp": timestamp,
            "study_type": "simulation",
            "causal_claim": False,
            "framing": "associational",
            "disclaimer": (
                "These results represent statistical associations observed in the data. "
                "No causal claims are made. The study design (simulation) does not support "
                "causal inference. Results are strictly associational."
            )
        },
        "results": results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_payload, f, indent=2, default=str)
    
    logger.info(f"Serialized model results to {output_path}")
    return output_path

def serialize_sensitivity_results(
    sensitivity_data: List[Dict[str, Any]],
    output_dir: str = "results/models",
    filename_prefix: str = "sensitivity_results"
) -> str:
    """
    Serialize sensitivity analysis results to JSON with explicit associational framing.
    
    Args:
        sensitivity_data: List of dictionaries containing sensitivity analysis outputs
        output_dir: Directory to save the results file
        filename_prefix: Prefix for the output filename
        
    Returns:
        Path to the saved JSON file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.json")
    
    # Create the output payload with explicit associational framing
    output_payload = {
        "metadata": {
            "timestamp": timestamp,
            "analysis_type": "sensitivity_analysis",
            "causal_claim": False,
            "framing": "associational",
            "disclaimer": (
                "Sensitivity analysis results indicate the stability of statistical associations "
                "across different threshold definitions. No causal inferences are drawn from these "
                "analyses. All findings are strictly associational."
            )
        },
        "sensitivity_runs": sensitivity_data
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_payload, f, indent=2, default=str)
    
    logger.info(f"Serialized sensitivity results to {output_path}")
    return output_path

def main():
    """
    Main entry point for testing serialization logic.
    Demonstrates the associational framing in output metadata.
    """
    logger.info("Running serialize_results main for demonstration/testing")
    
    # Example dummy results to demonstrate serialization
    dummy_results = {
        "logistic_model": {
            "coef": 0.5,
            "p_value": 0.03,
            "odds_ratio": 1.65
        },
        "linear_model": {
            "coef": 1.2,
            "p_value": 0.01,
            "r_squared": 0.15
        }
    }
    
    # Serialize model results
    model_path = serialize_model_results(dummy_results)
    logger.info(f"Model results saved to: {model_path}")
    
    # Serialize sensitivity results
    dummy_sensitivity = [
        {"threshold": "strict", "coef": 0.5, "p_value": 0.03},
        {"threshold": "moderate", "coef": 0.4, "p_value": 0.05},
        {"threshold": "partial", "coef": 0.3, "p_value": 0.08}
    ]
    sensitivity_path = serialize_sensitivity_results(dummy_sensitivity)
    logger.info(f"Sensitivity results saved to: {sensitivity_path}")
    
    # Verify content includes associational framing
    with open(model_path, 'r') as f:
        content = json.load(f)
        assert content["metadata"]["framing"] == "associational"
        assert content["metadata"]["causal_claim"] is False
        logger.info("Verified: Output metadata correctly frames results as associational")

if __name__ == "__main__":
    main()