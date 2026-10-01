import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise

def extract_sensitivity_range(sensitivity_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract min, max, and range from sensitivity sweep data.
    
    Args:
        sensitivity_data: List of results from sensitivity sweep with 'fid_score' keys.
        
    Returns:
        Dictionary with 'min', 'max', and 'range' values.
    """
    if not sensitivity_data or not isinstance(sensitivity_data, list):
        logger.warning("Invalid sensitivity data format, returning zeros")
        return {"min": 0.0, "max": 0.0, "range": 0.0}
    
    fid_scores = [item.get('fid_score', 0.0) for item in sensitivity_data if 'fid_score' in item]
    
    if not fid_scores:
        logger.warning("No FID scores found in sensitivity data")
        return {"min": 0.0, "max": 0.0, "range": 0.0}
    
    min_fid = min(fid_scores)
    max_fid = max(fid_scores)
    fid_range = max_fid - min_fid
    
    return {
        "min": min_fid,
        "max": max_fid,
        "range": fid_range
    }

def generate_final_report(
    stats_data: Dict[str, Any],
    sensitivity_data: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """
    Generate the final report combining statistical analysis and sensitivity sweep results.
    
    Args:
        stats_data: Dictionary containing statistical analysis results (mean, std, bootstrap).
        sensitivity_data: Dictionary containing sensitivity sweep results.
        output_path: Path to save the final report JSON file.
        
    Returns:
        The generated final report dictionary.
    """
    logger.info("Generating final report...")
    
    # Extract sensitivity range
    sensitivity_range = extract_sensitivity_range(sensitivity_data.get('results', []))
    
    # Build final report structure
    final_report = {
        "statistical_analysis": {
            "mean": stats_data.get('mean', 0.0),
            "std": stats_data.get('std', 0.0),
            "paired_differences": stats_data.get('paired_differences', []),
            "bootstrap_results": stats_data.get('bootstrap_results', {}),
            "statistical_limitations": stats_data.get('statistical_limitations', 'None')
        },
        "sensitivity_analysis": {
            "threshold_range": sensitivity_data.get('thresholds', []),
            "fid_range": sensitivity_range,
            "robustness_conclusion": sensitivity_data.get('robustness_conclusion', 'Not evaluated'),
            "rationale": sensitivity_data.get('rationale', 'Not provided')
        },
        "summary": {
            "mean_fid_difference": stats_data.get('mean', 0.0),
            "std_fid_difference": stats_data.get('std', 0.0),
            "sensitivity_range": sensitivity_range['range'],
            "conclusion": "Analysis complete"
        }
    }
    
    # Save to file
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final report saved to {output_path}")
    return final_report

def main():
    """Main entry point for generating the final report."""
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    stats_path = project_root / "data" / "results" / "statistical_analysis.json"
    sensitivity_path = project_root / "data" / "results" / "sensitivity_sweep.json"
    output_path = project_root / "data" / "results" / "final_report.json"
    
    try:
        # Load statistical analysis data
        logger.info(f"Loading statistical analysis from {stats_path}")
        stats_data = load_json_file(str(stats_path))
        
        # Load sensitivity sweep data
        logger.info(f"Loading sensitivity sweep from {sensitivity_path}")
        sensitivity_data = load_json_file(str(sensitivity_path))
        
        # Generate final report
        report = generate_final_report(stats_data, sensitivity_data, str(output_path))
        
        logger.info("Final report generation completed successfully")
        print(json.dumps(report, indent=2))
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during final report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
