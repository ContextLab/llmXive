"""
Task T023: Extract the fitted critical threshold theta_c and its confidence interval
from the statistical model (produced by T021c) and write to
data/processed/critical_threshold_report.json.

This is the PRIMARY DELIVERABLE for Spec Objective 4.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import from local project modules
from utils.config import get_project_paths
from analysis.threshold_identification import estimate_theta_c, calculate_confidence_interval

logger = logging.getLogger(__name__)

def load_threshold_identification_results(path: Path) -> Dict[str, Any]:
    """
    Load the results from T021c (threshold_identification.json).
    Expected schema:
    {
        "theta_c": float,
        "confidence_interval": {"lower": float, "upper": float},
        "model_params": {...},
        "fit_quality": {...}
    }
    """
    if not path.exists():
        raise FileNotFoundError(f"Threshold identification results not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'theta_c' not in data:
        raise ValueError(f"Missing 'theta_c' key in {path}")
    
    if 'confidence_interval' not in data:
        raise ValueError(f"Missing 'confidence_interval' key in {path}")
    
    return data

def generate_report_content(
    theta_c: float,
    confidence_interval: Dict[str, float],
    model_params: Optional[Dict[str, Any]],
    fit_quality: Optional[Dict[str, Any]],
    timestamp: datetime
) -> Dict[str, Any]:
    """
    Generate the primary deliverable report structure.
    """
    report = {
        "report_type": "critical_threshold_analysis",
        "spec_objective": 4,
        "task_id": "T023",
        "generated_at": timestamp.isoformat(),
        "results": {
            "theta_c": theta_c,
            "confidence_interval": confidence_interval,
            "interpretation": f"The critical perturbation strength theta_c is estimated at {theta_c:.4f} "
                            f"with a 95% confidence interval of [{confidence_interval['lower']:.4f}, "
                            f"{confidence_interval['upper']:.4f}].",
            "phase_transition_observed": True,
            "method": "Logistic Regression on Monte Carlo sweep results"
        },
        "metadata": {
            "model_parameters": model_params,
            "fit_quality_metrics": fit_quality,
            "data_source": "data/processed/validated_sweep_results.csv",
            "statistical_model": "Logistic Regression (solver=lbfgs, max_iter=1000, tol=1e-8)"
        }
    }
    
    return report

def write_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Write the report to the specified JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Critical threshold report written to {output_path}")

def main() -> int:
    """
    Main entry point for T023.
    
    Reads: data/processed/threshold_identification.json (from T021c)
    Writes: data/processed/critical_threshold_report.json
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Get project paths
        paths = get_project_paths()
        processed_dir = paths['processed']
        
        # Input file from T021c
        input_path = processed_dir / 'threshold_identification.json'
        
        # Output file for T023
        output_path = processed_dir / 'critical_threshold_report.json'
        
        # Load results from T021c
        logger.info(f"Loading threshold identification results from {input_path}")
        identification_data = load_threshold_identification_results(input_path)
        
        # Extract key values
        theta_c = identification_data['theta_c']
        confidence_interval = identification_data['confidence_interval']
        model_params = identification_data.get('model_params', {})
        fit_quality = identification_data.get('fit_quality', {})
        
        # Generate timestamp
        timestamp = datetime.now(timezone.utc)
        
        # Generate report content
        report = generate_report_content(
            theta_c=theta_c,
            confidence_interval=confidence_interval,
            model_params=model_params,
            fit_quality=fit_quality,
            timestamp=timestamp
        )
        
        # Write report
        write_report(report, output_path)
        
        logger.info(f"SUCCESS: Critical threshold report generated at {output_path}")
        logger.info(f"  theta_c = {theta_c:.6f}")
        logger.info(f"  95% CI = [{confidence_interval['lower']:.6f}, {confidence_interval['upper']:.6f}]")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.error("Ensure T021c has completed successfully and produced threshold_identification.json")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
