import json
import os
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.optimize import curve_fit
from code.config import get_config
from code.logger import get_logger

logger = logging.getLogger(__name__)

def saturation_model(L, PR_inf, xi):
    """Saturation model for finite-size scaling."""
    return PR_inf * (1 - np.exp(-L / xi))

def load_raw_pr_data(input_path: str) -> List[Dict[str, Any]]:
    """Load raw PR data from JSON."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(path, 'r') as f:
        return json.load(f)

def fit_scaling_curve(L_values: List[int], pr_values: List[float]) -> Optional[Dict[str, float]]:
    """Fit the saturation model to PR vs L data."""
    if len(L_values) < 3:
        logger.warning("Insufficient data points for scaling fit.")
        return None
    
    try:
        popt, pcov = curve_fit(
            saturation_model, 
            L_values, 
            pr_values, 
            p0=[max(pr_values), 100], 
            maxfev=5000,
            bounds=([0, 0], [np.inf, np.inf])
        )
        PR_inf, xi = popt
        
        if xi <= 0 or PR_inf <= 0:
            logger.warning(f"Non-physical fit result: xi={xi}, PR_inf={PR_inf}")
            return None
        
        # Calculate R-squared
        pr_pred = saturation_model(np.array(L_values), *popt)
        ss_res = np.sum((np.array(pr_values) - pr_pred) ** 2)
        ss_tot = np.sum((np.array(pr_values) - np.mean(pr_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        if r_squared < 0.95:
            logger.warning(f"Fit R-squared too low: {r_squared}")
            return None
        
        # Estimate uncertainty
        perr = np.sqrt(np.diag(pcov))
        uncertainty = perr[1]
        
        return {
            "xi": float(xi),
            "uncertainty": float(uncertainty),
            "r_squared": float(r_squared)
        }
    except Exception as e:
        logger.warning(f"Scaling fit failed: {e}")
        return None

def run_scaling_analysis(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run scaling analysis for each W."""
    results = []
    warnings_list = []
    
    # Group by W
    grouped = {}
    for item in raw_data:
        w = item["W"]
        if w not in grouped:
            grouped[w] = {}
        if "L" not in grouped[w]:
            grouped[w]["L"] = {}
        
        # Aggregate PR for each L (average over realizations)
        L_val = item["L"]
        if L_val not in grouped[w]["L"]:
            grouped[w]["L"][L_val] = []
        grouped[w]["L"][L_val].append(item["pr"])
    
    for W, L_data in grouped.items():
        logger.info(f"Fitting scaling for W={W}")
        L_values = sorted(L_data["L"].keys())
        avg_pr = [np.mean(L_data["L"][L]) for L in L_values]
        
        fit_result = fit_scaling_curve(L_values, avg_pr)
        
        if fit_result:
            results.append({
                "disorder_width": W,
                "xi": fit_result["xi"],
                "uncertainty": fit_result["uncertainty"],
                "r_squared": fit_result["r_squared"]
            })
        else:
            warnings_list.append(f"Fit failed for W={W}")
    
    # Write warnings if any
    if warnings_list:
        warnings_path = Path("data/metadata/warnings.json")
        warnings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(warnings_path, 'w') as f:
            json.dump(warnings_list, f, indent=2)
    
    return results

def main():
    """Main entry point for finite size scaling."""
    config = get_config()
    input_path = Path("data/processed/pr_raw_multiL.json")
    
    if not input_path.exists():
        logger.error(f"Raw PR data not found: {input_path}")
        return
    
    raw_data = load_raw_pr_data(str(input_path))
    scaling_results = run_scaling_analysis(raw_data)
    
    output_path = Path("data/processed/pr_scaling_raw.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(scaling_results, f, indent=2)
    
    logger.info(f"Scaling results written to {output_path}")

if __name__ == "__main__":
    main()
