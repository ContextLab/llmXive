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

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the JSON data, or None if file not found
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None

def extract_sensitivity_range(sensitivity_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract min, max, and range of FID degradation from sensitivity sweep data.
    
    Args:
        sensitivity_data: Dictionary containing sensitivity sweep results
        
    Returns:
        Dictionary with min, max, and range of FID degradation
    """
    if not sensitivity_data or 'results' not in sensitivity_data:
        logger.warning("No sensitivity data provided or invalid format")
        return {"min": 0.0, "max": 0.0, "range": 0.0}
    
    fid_scores = [r.get('fid_score', 0.0) for r in sensitivity_data['results']]
    
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
    statistical_data: Optional[Dict[str, Any]],
    sensitivity_data: Optional[Dict[str, Any]],
    output_path: str
) -> bool:
    """
    Generate the final report combining statistical analysis and sensitivity sweep results.
    
    Args:
        statistical_data: Results from statistical analysis (T025/T026)
        sensitivity_data: Results from sensitivity sweep (T027)
        output_path: Path where the final report will be saved
        
    Returns:
        True if report was successfully generated, False otherwise
    """
    logger.info("Generating final report...")
    
    # Extract statistical results
    mean_diff = 0.0
    std_diff = 0.0
    p_value = 0.0
    ci_lower = 0.0
    ci_upper = 0.0
    statistical_limitations = ""
    
    if statistical_data:
        mean_diff = statistical_data.get('mean', 0.0)
        std_diff = statistical_data.get('std', 0.0)
        
        bootstrap_results = statistical_data.get('bootstrap_results', {})
        p_value = bootstrap_results.get('p_value', 0.0)
        ci_lower = bootstrap_results.get('ci_lower', 0.0)
        ci_upper = bootstrap_results.get('ci_upper', 0.0)
        
        statistical_limitations = statistical_data.get('statistical_limitations', "")
    
    # Extract sensitivity range
    sensitivity_range = extract_sensitivity_range(sensitivity_data)
    
    # Build final report
    final_report = {
        "statistical_analysis": {
            "mean_fid_difference": mean_diff,
            "std_fid_difference": std_diff,
            "bootstrap_results": {
                "p_value": p_value,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper
            },
            "statistical_limitations": statistical_limitations
        },
        "sensitivity_analysis": {
            "fid_degradation_range": sensitivity_range
        },
        "summary": {
            "static_vs_dynamic_mean_diff": mean_diff,
            "sensitivity_range": sensitivity_range['range'],
            "conclusion": "Analysis complete"
        }
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save final report
    try:
        with open(output_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        logger.info(f"Final report saved to: {output_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to save final report: {e}")
        return False

def main():
    """Main entry point for final report generation."""
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / "data" / "results"
    
    statistical_file = results_dir / "statistical_analysis.json"
    sensitivity_file = results_dir / "sensitivity_sweep.json"
    output_file = results_dir / "final_report.json"
    
    # Load statistical analysis data
    statistical_data = load_json_file(str(statistical_file))
    if statistical_data is None:
        logger.warning(f"Statistical analysis file not found or invalid: {statistical_file}")
        logger.warning("Proceeding with empty statistical data")
    
    # Load sensitivity sweep data
    sensitivity_data = load_json_file(str(sensitivity_file))
    if sensitivity_data is None:
        logger.warning(f"Sensitivity sweep file not found or invalid: {sensitivity_file}")
        logger.warning("Proceeding with empty sensitivity data")
    
    # Generate final report
    success = generate_final_report(
        statistical_data=statistical_data,
        sensitivity_data=sensitivity_data,
        output_path=str(output_file)
    )
    
    if success:
        logger.info("Final report generation completed successfully")
        return 0
    else:
        logger.error("Final report generation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
