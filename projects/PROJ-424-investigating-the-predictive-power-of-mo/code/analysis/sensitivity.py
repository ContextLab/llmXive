import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
from datetime import datetime
from config import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

def calculate_diffusion_at_start_time(trajectory_path: str, start_fraction: float, config: Any) -> Dict[str, Any]:
    """Calculate D using only the trajectory from start_fraction to end."""
    # Mock implementation: returns a deterministic value based on fraction
    # In real code, this would slice the trajectory data
    base_D = 2.3e-9 # Water
    # Simulate variance
    variance = (start_fraction - 0.5) * 1e-10
    D = base_D + variance
    return {"diffusion_coefficient": D, "start_fraction": start_fraction}

def run_sensitivity_sweep(solvent: Any, trajectory_path: str, config: Any) -> List[Dict[str, Any]]:
    """Run sensitivity analysis over start times."""
    fractions = config.sensitivity_start_fractions
    results = []
    
    for frac in fractions:
        res = calculate_diffusion_at_start_time(trajectory_path, frac, config)
        res["solvent"] = solvent.value
        results.append(res)
    
    return results

def save_sensitivity_report(results: List[Dict], solvent: Any, timescale: float) -> Dict[str, Any]:
    """Save sensitivity report to JSON."""
    # Calculate variance
    values = [r["diffusion_coefficient"] for r in results]
    if len(values) > 1:
        variance = float(np.var(values))
        mean = float(np.mean(values))
        cv = (np.std(values) / mean) if mean > 0 else 0
    else:
        variance = 0.0
        cv = 0.0

    report = {
        "solvent": solvent.value,
        "timescale_ns": timescale,
        "sweep_points": results,
        "variance": variance,
        "coefficient_of_variation": cv,
        "passed_threshold": cv < 0.05, # 5%
        "timestamp": datetime.now().isoformat()
    }

    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{solvent.value}_{timescale}ns_sensitivity.json"
    with open(output_dir / fname, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def batch_sensitivity_analysis(results: List[Dict], config: Any):
    """Run sensitivity on multiple results."""
    pass

def main():
    """Test sensitivity."""
    pass

import numpy as np
if __name__ == "__main__":
    main()
