import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_project_root
from utils.logger import get_logger
from analysis.lmm_model import ASSOCIATION_LABEL

logger = get_logger(__name__)

def load_lmm_results(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load LMM results from a CSV file.
    """
    root = get_project_root()
    if input_path is None:
        input_path = str(root / "output" / "results" / "lmm_summary.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"LMM results file not found at {input_path}")
    
    import pandas as pd
    df = pd.read_csv(input_path)
    results = df.to_dict(orient='records')
    
    # Ensure association label is present
    for res in results:
        if 'association_label' not in res:
            res['association_label'] = ASSOCIATION_LABEL
            
    return results

def run_sensitivity_analysis(results: List[Dict[str, Any]], thresholds: List[float]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by sweeping p-value thresholds.
    Calculates the rate of significant findings at each threshold.
    """
    analysis = []
    
    for threshold in thresholds:
        significant_count = 0
        for res in results:
            p_val = res.get('p_raw', 1.0)
            if p_val < threshold:
                significant_count += 1
        
        rate = significant_count / len(results) if len(results) > 0 else 0.0
        
        analysis.append({
            "threshold": threshold,
            "significant_count": significant_count,
            "total_tests": len(results),
            "rate": rate,
            "association_label": ASSOCIATION_LABEL  # FR-005 Compliance
        })
        
    logger.info(f"Completed sensitivity analysis for {len(thresholds)} thresholds.")
    return {
        "analysis": analysis,
        "association_label": ASSOCIATION_LABEL
    }

def save_results(analysis_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save sensitivity analysis results to JSON.
    """
    root = get_project_root()
    if output_path is None:
        output_path = str(root / "output" / "results" / "sensitivity_analysis.json")
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_result, f, indent=2)
        
    logger.info(f"Saved sensitivity analysis to {output_path}")
    return output_path

def main():
    """
    Main entry point for sensitivity analysis script.
    """
    parser = argparse.ArgumentParser(description="Run Sensitivity Analysis on LMM Results")
    parser.add_argument("--input", type=str, help="Path to input LMM results CSV", default=None)
    parser.add_argument("--output", type=str, help="Path to output JSON", default=None)
    parser.add_argument("--thresholds", type=float, nargs='+', default=[0.01, 0.05, 0.1],
                        help="P-value thresholds to sweep")
    args = parser.parse_args()

    logger.info("Starting Sensitivity Analysis...")
    
    try:
        results = load_lmm_results(args.input)
        analysis = run_sensitivity_analysis(results, args.thresholds)
        save_results(analysis, args.output)
        logger.info("Sensitivity Analysis complete.")
        return 0
    except Exception as e:
        logger.error(f"Sensitivity Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
