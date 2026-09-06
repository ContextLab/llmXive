import os
import sys
import logging
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Import from existing API surface
from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

def load_sensitivity_data(input_path: str) -> pd.DataFrame:
    """
    Load sensitivity analysis results from CSV.
    Expected columns: min_cluster_size, min_samples, region_size, mean_correlation, robustness_score
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Sensitivity analysis data not found at: {input_path}")
    
    df = pd.read_csv(input_path)
    required_cols = ['min_cluster_size', 'min_samples', 'region_size', 'mean_correlation', 'robustness_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Sensitivity data missing required columns: {missing_cols}")
    
    return df

def validate_against_sc003(sensitivity_df: pd.DataFrame, threshold: float = 0.7) -> dict:
    """
    Validate sensitivity analysis results against SC-003 requirements.
    
    SC-003 Requirements:
    - Robustness must be maintained across parameter sweeps
    - Jaccard Index (robustness_score) should remain above threshold
    - Decoupled region identification must be stable
    
    Returns validation report dict.
    """
    validation_results = {
        "sc003_compliant": True,
        "threshold": threshold,
        "total_sweeps": len(sensitivity_df),
        "successful_sweeps": 0,
        "failed_sweeps": 0,
        "min_robustness": float('inf'),
        "max_robustness": float('-inf'),
        "mean_robustness": 0.0,
        "failed_configs": [],
        "passed_configs": [],
        "summary": "",
        "recommendation": ""
    }
    
    if len(sensitivity_df) == 0:
        validation_results["sc003_compliant"] = False
        validation_results["summary"] = "No sensitivity data available for validation"
        validation_results["recommendation"] = "Re-run sensitivity analysis with valid parameters"
        return validation_results
    
    # Calculate statistics
    robustness_scores = sensitivity_df['robustness_score'].dropna()
    
    if len(robustness_scores) == 0:
        validation_results["sc003_compliant"] = False
        validation_results["summary"] = "No valid robustness scores in sensitivity data"
        validation_results["recommendation"] = "Check sensitivity analysis implementation"
        return validation_results
    
    validation_results["min_robustness"] = float(robustness_scores.min())
    validation_results["max_robustness"] = float(robustness_scores.max())
    validation_results["mean_robustness"] = float(robustness_scores.mean())
    
    # Validate each sweep
    for idx, row in sensitivity_df.iterrows():
        config = {
            "min_cluster_size": int(row['min_cluster_size']),
            "min_samples": int(row['min_samples']),
            "region_size": int(row['region_size']),
            "mean_correlation": float(row['mean_correlation']),
            "robustness_score": float(row['robustness_score']) if pd.notna(row['robustness_score']) else None
        }
        
        robustness = config['robustness_score']
        
        if robustness is None:
            validation_results["failed_sweeps"] += 1
            validation_results["failed_configs"].append(config)
            validation_results["sc003_compliant"] = False
        elif robustness >= threshold:
            validation_results["successful_sweeps"] += 1
            validation_results["passed_configs"].append(config)
        else:
            validation_results["failed_sweeps"] += 1
            validation_results["failed_configs"].append(config)
            validation_results["sc003_compliant"] = False
    
    # Generate summary
    success_rate = validation_results["successful_sweeps"] / validation_results["total_sweeps"]
    
    if validation_results["sc003_compliant"]:
        validation_results["summary"] = (
            f"All {validation_results['total_sweeps']} parameter configurations passed robustness validation. "
            f"Mean robustness score: {validation_results['mean_robustness']:.3f} "
            f"(threshold: {threshold}). Decoupled region identification is stable across parameter sweeps."
        )
        validation_results["recommendation"] = "No action required. Methodology is robust."
    else:
        failed_count = validation_results["failed_sweeps"]
        validation_results["summary"] = (
            f"{failed_count} of {validation_results['total_sweeps']} parameter configurations failed robustness validation. "
            f"Success rate: {success_rate:.1%}. Mean robustness score: {validation_results['mean_robustness']:.3f}. "
            f"Decoupled region identification shows instability under parameter variation."
        )
        validation_results["recommendation"] = (
            "Review HDBSCAN parameter selection. Consider narrowing parameter range or "
            "re-evaluating the decoupled region threshold. Methodology requires refinement."
        )
    
    return validation_results

def main():
    """Main entry point for robustness validation."""
    parser = argparse.ArgumentParser(description="Validate sensitivity analysis against SC-003 requirements")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/sensitivity_analysis.csv",
        help="Path to sensitivity analysis CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/results/robustness_validation.json",
        help="Path to output validation JSON"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum robustness score threshold for SC-003 compliance"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Loading sensitivity data from: {args.input}")
        sensitivity_df = load_sensitivity_data(args.input)
        
        logger.info(f"Performing SC-003 validation with threshold: {args.threshold}")
        validation_report = validate_against_sc003(sensitivity_df, args.threshold)
        
        # Save validation report
        with open(output_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        logger.info(f"Validation report saved to: {output_path}")
        logger.info(f"SC-003 Compliance: {'PASS' if validation_report['sc003_compliant'] else 'FAIL'}")
        logger.info(f"Summary: {validation_report['summary']}")
        
        # Return exit code based on compliance
        sys.exit(0 if validation_report['sc003_compliant'] else 1)
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
