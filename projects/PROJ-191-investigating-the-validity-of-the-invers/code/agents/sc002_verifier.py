import os
import sys
import json
import logging
from pathlib import Path
from config import get_logger, ProjectConfig

def load_json_safe(path: Path) -> dict:
    """Load a JSON file safely, raising a clear error if it doesn't exist or is invalid."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def compute_sc002_verification(bayes_factor_k: float, null_distribution: list) -> dict:
    """
    Compute SC-002 verification metrics.
    
    Args:
        bayes_factor_k: The observed Bayes factor K from primary inference.
        null_distribution: List of Bayes factors from null simulations (alpha=0).
        
    Returns:
        Dictionary with verification results.
    """
    if not null_distribution:
        raise ValueError("Null distribution is empty; cannot compute p-value.")
        
    # Kass-Raftery criterion: K > 3 indicates strong evidence
    kass_raftery_pass = bayes_factor_k > 3.0
    
    # Compute p-value: fraction of null samples >= observed K
    # This tests if the observed K is significantly larger than what we'd expect by chance
    p_value = sum(1 for k_null in null_distribution if k_null >= bayes_factor_k) / len(null_distribution)
    
    # Baseline pass: p-value < 0.05 (statistically significant)
    baseline_pass = p_value < 0.05
    
    return {
        "K_value": bayes_factor_k,
        "Kass_Raftery_Pass": kass_raftery_pass,
        "P_value": p_value,
        "Baseline_Pass": baseline_pass,
        "null_samples_count": len(null_distribution)
    }

def main():
    """Main entry point for SC-002 verification."""
    config = ProjectConfig()
    logger = get_logger(__name__)
    
    # Define paths
    results_dir = config.data_results_dir
    bayes_factor_path = results_dir / "bayes_factor.json"
    null_baseline_path = results_dir / "null_baseline_report.json"
    output_path = results_dir / "validity_report.json"
    
    logger.info(f"Starting SC-002 verification. Results dir: {results_dir}")
    
    try:
        # Load primary Bayes factor
        logger.info(f"Loading Bayes factor from {bayes_factor_path}")
        bayes_data = load_json_safe(bayes_factor_path)
        bayes_factor_k = bayes_data.get("bayes_factor")
        if bayes_factor_k is None:
            raise ValueError("Bayes factor not found in bayes_factor.json")
        
        # Load null simulation baseline
        logger.info(f"Loading null baseline from {null_baseline_path}")
        null_data = load_json_safe(null_baseline_path)
        
        # Extract null distribution - could be in different formats
        null_samples = null_data.get("null_samples", [])
        if not null_samples and "bayes_factors" in null_data:
            null_samples = null_data["bayes_factors"]
        
        if not null_samples:
            raise ValueError("No null samples found in null_baseline_report.json")
        
        # Compute verification
        logger.info(f"Computing SC-002 verification with K={bayes_factor_k}, {len(null_samples)} null samples")
        verification = compute_sc002_verification(bayes_factor_k, null_samples)
        
        # Write output
        logger.info(f"Writing validity report to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(verification, f, indent=2)
        
        # Log results
        logger.info(f"SC-002 Verification Results:")
        logger.info(f"  K_value: {verification['K_value']:.4f}")
        logger.info(f"  Kass_Raftery_Pass: {verification['Kass_Raftery_Pass']}")
        logger.info(f"  P_value: {verification['P_value']:.4f}")
        logger.info(f"  Baseline_Pass: {verification['Baseline_Pass']}")
        
        if verification['Baseline_Pass'] and verification['Kass_Raftery_Pass']:
            logger.info("SC-002 VERIFICATION PASSED: Strong evidence for Yukawa modification detected.")
        else:
            logger.warning("SC-002 VERIFICATION FAILED: Insufficient evidence for Yukawa modification.")
            
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required file missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())