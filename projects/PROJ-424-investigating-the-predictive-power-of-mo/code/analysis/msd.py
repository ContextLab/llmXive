import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
import json
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class MSDResult:
    diffusion_coefficient: float
    r_squared: float
    valid: bool
    message: str

def load_trajectory_timeseries(trajectory_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load trajectory and compute MSD.
    MOCK IMPLEMENTATION: Reads the dummy file created by runner.py.
    """
    path = Path(trajectory_path)
    if not path.exists():
        raise FileNotFoundError(f"Trajectory not found: {trajectory_path}")

    # Parse the mock file to generate synthetic but deterministic MSD data
    # In real code, this would use MDAnalysis or GROMACS tools
    times = []
    msds = []
    
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # Skip header lines
    data_started = False
    for line in lines:
        if line.startswith("MOCK"):
            continue
        if line.strip() == "":
            continue
        parts = line.split()
        if len(parts) >= 4:
            try:
                t = float(parts[0]) # Using index as time proxy
                # MSD ~ 6 * D * t. D ~ 2e-9.
                # Scale t to ns, MSD to m2
                t_ns = t * 0.01 # arbitrary scaling for mock
                msd_val = 6 * 2.3e-9 * t_ns # Water D
                times.append(t_ns)
                msds.append(msd_val)
            except ValueError:
                continue

    return np.array(times), np.array(msds)

def perform_linear_regression(times: np.ndarray, msds: np.ndarray) -> Tuple[float, float, float]:
    """Perform linear regression MSD = slope * t + intercept."""
    if len(times) < 2:
        return 0.0, 0.0, 0.0
    
    # Fit line
    coeffs = np.polyfit(times, msds, 1)
    slope = coeffs[0]
    intercept = coeffs[1]
    
    # Calculate R-squared
    y_pred = slope * times + intercept
    ss_res = np.sum((msds - y_pred) ** 2)
    ss_tot = np.sum((msds - np.mean(msds)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return slope, intercept, r_squared

def validate_linearity(r_squared: float, threshold: float) -> bool:
    """Check if R-squared meets the threshold."""
    return r_squared >= threshold

def calculate_diffusion_coefficient(slope: float, scaling_factor: float = 1.0) -> float:
    """Calculate D from slope (MSD = 6Dt in 3D)."""
    # D = slope / 6
    return (slope / 6.0) * scaling_factor

def analyze_msd(solvent: Any, trajectory_path: str, config: Any) -> MSDResult:
    """Main analysis function."""
    try:
        times, msds = load_trajectory_timeseries(trajectory_path)
        if len(times) == 0:
            return MSDResult(0.0, 0.0, False, "No data points in trajectory")

        slope, intercept, r_squared = perform_linear_regression(times, msds)
        
        # Get scaling factor
        scaling = config.scaling_factors.get(solvent.value, 1.0)
        D = calculate_diffusion_coefficient(slope, scaling)
        
        valid = validate_linearity(r_squared, config.r_squared_threshold)
        
        msg = f"R²={r_squared:.4f}, D={D:.2e}"
        if not valid:
            msg += f" (Invalid: R² < {config.r_squared_threshold})"
        
        return MSDResult(D, r_squared, valid, msg)
    except Exception as e:
        logger.error(f"MSD analysis failed: {e}")
        return MSDResult(0.0, 0.0, False, str(e))

def batch_analyze_msd(results: List[Dict], config: Any) -> List[MSDResult]:
    """Analyze multiple results."""
    return [analyze_msd(r["solvent"], r["output_path"], config) for r in results]

def save_analysis_results(results: List[Dict], solvent: Any, timescale: float):
    """Save results to JSON."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{solvent.value}_{timescale}ns_analysis.json"
    with open(output_dir / fname, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Test MSD analysis."""
    # Create mock trajectory
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    with open("data/processed/water_1ns.trr", 'w') as f:
        f.write("MOCK TRAJECTORY: water\n1\n0.1 0.1 0.1\n")
        for i in range(100):
            f.write(f"{i} {i*0.1} {i*0.2} {i*0.3}\n")
    
    from config import ANALYSIS_CONFIG, Solvent
    res = analyze_msd(Solvent.WATER, "data/processed/water_1ns.trr", ANALYSIS_CONFIG)
    print(f"Result: {res}")

if __name__ == "__main__":
    main()
