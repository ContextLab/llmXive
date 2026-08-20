"""
Module: code/analysis/compare_slopes.py
Purpose: Compare the computational complexity slopes of Symbolic vs Neural solvers.
Implements the logic for T029g: "Compare solver slopes for complexity class verification."

Constraints:
- Must read from data/processed/scaling_raw_logs.json (Symbolic) and data/processed/neural_baseline_logs.json (Neural).
- Must perform log-log linear regression.
- Must compare slopes to determine if the approach (Symbolic) has a lower complexity class than Neural.
- Must output a JSON report to data/processed/complexity_comparison.json.
- Must fail loudly if input files are missing or data is insufficient for regression.
"""
import json
import math
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RegressionResult:
    slope: float
    intercept: float
    r_squared: float
    n_samples: int
    solver_type: str

@dataclass
class ComplexityComparison:
    symbolic_result: Optional[RegressionResult]
    neural_result: Optional[RegressionResult]
    slope_difference: float
    is_symbolic_more_efficient: bool
    conclusion: str
    status: str  # "PASS", "FAIL", "INCONCLUSIVE"

def load_scaling_logs(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load scaling logs from a JSON file.
    Expects a list of objects with 'n' (problem size) and 'duration' (or 'time').
    """
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"Required input file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        logger.error(f"Expected a list of logs in {filepath}, got {type(data)}")
        raise ValueError(f"Invalid format in {filepath}: expected list")
    
    # Validate minimal schema
    if len(data) > 0:
        required_keys = {'n', 'duration'}
        if not required_keys.issubset(data[0].keys()):
            # Try to normalize keys if 'time' is used instead of 'duration'
            if 'time' in data[0].keys():
                for item in data:
                    item['duration'] = item['time']
            else:
                logger.error(f"Missing required keys in {filepath}. Found keys: {data[0].keys()}")
                raise ValueError(f"Invalid data schema in {filepath}")
    
    return data

def perform_log_log_regression(data: List[Dict[str, Any]], solver_type: str) -> RegressionResult:
    """
    Perform log-log linear regression: log(duration) = slope * log(n) + intercept.
    Returns the slope which represents the computational complexity exponent.
    """
    if len(data) < 3:
        logger.error(f"Not enough data points for regression in {solver_type} logs (n={len(data)})")
        raise ValueError(f"Insufficient data for regression in {solver_type}: need at least 3 points")
    
    # Extract and filter valid points
    points = []
    for item in data:
        n = item.get('n')
        dur = item.get('duration')
        if n is not None and dur is not None and n > 0 and dur > 0:
            points.append((math.log(n), math.log(dur)))
    
    if len(points) < 3:
        logger.error(f"Not enough valid data points after filtering in {solver_type}")
        raise ValueError(f"Insufficient valid data for regression in {solver_type}")
    
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    n = len(x)
    
    # Calculate means
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    # Calculate slope and intercept
    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominator = sum((xi - mean_x) ** 2 for xi in x)
    
    if denominator == 0:
        logger.error(f"Zero denominator in regression for {solver_type}. Data points have constant x.")
        raise ValueError(f"Regression failed for {solver_type}: constant input size")
    
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    
    # Calculate R-squared
    y_pred = [slope * xi + intercept for xi in x]
    ss_res = sum((yi - ypi) ** 2 for yi, ypi in zip(y, y_pred))
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    logger.info(f"Regression for {solver_type}: slope={slope:.4f}, R^2={r_squared:.4f}, n={n}")
    
    return RegressionResult(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        n_samples=n,
        solver_type=solver_type
    )

def determine_complexity_class_from_slope(slope: float, r_squared: float) -> str:
    """
    Map the slope to a complexity class string.
    Thresholds are approximate:
    - slope < 1.0: Sub-linear (unlikely for these puzzles, but possible with heuristics)
    - 1.0 <= slope < 1.5: Linear / Near-linear (O(n), O(n log n))
    - 1.5 <= slope < 2.5: Quadratic (O(n^2))
    - 2.5 <= slope < 4.0: Cubic (O(n^3))
    - slope >= 4.0: Exponential/High-degree (O(n^4) or worse)
    """
    if r_squared < 0.85:
        return "UNKNOWN (Low R^2)"
    
    if slope < 1.0:
        return "Sub-linear (O(n^<1))"
    elif slope < 1.5:
        return "Linear / Near-linear (O(n^1..1.5))"
    elif slope < 2.5:
        return "Quadratic (O(n^2))"
    elif slope < 4.0:
        return "Cubic (O(n^3))"
    else:
        return "High-degree / Exponential (O(n^>=4))"

def compare_slopes(symbolic_result: RegressionResult, neural_result: RegressionResult) -> Tuple[float, bool, str]:
    """
    Compare the slopes of two solvers.
    Returns (difference, is_symbolic_better, conclusion_text).
    """
    diff = neural_result.slope - symbolic_result.slope
    is_better = diff > 0.0 # Positive difference means Neural is slower (higher complexity)
    
    if symbolic_result.r_squared < 0.85 or neural_result.r_squared < 0.85:
        conclusion = "Inconclusive: One or both regressions have low R^2 (< 0.85)."
    elif is_better:
        conclusion = f"Symbolic solver is more efficient. Complexity reduction: {diff:.4f} in exponent."
    elif diff < -0.1: # Neural is significantly better
        conclusion = f"Neural solver is more efficient (unexpected for this hypothesis). Difference: {diff:.4f}."
    else:
        conclusion = "Slopes are statistically similar. No clear complexity advantage."
    
    return diff, is_better, conclusion

def main():
    """
    Main entry point for T029g.
    1. Load symbolic and neural logs.
    2. Perform log-log regression on both.
    3. Compare slopes.
    4. Write results to data/processed/complexity_comparison.json.
    """
    base_dir = Path(__file__).parent.parent.parent
    symbolic_path = base_dir / "data" / "processed" / "scaling_raw_logs.json"
    neural_path = base_dir / "data" / "processed" / "neural_baseline_logs.json"
    output_path = base_dir / "data" / "processed" / "complexity_comparison.json"
    
    logger.info(f"Starting complexity comparison (T029g).")
    logger.info(f"Symbolic logs: {symbolic_path}")
    logger.info(f"Neural logs: {neural_path}")
    
    symbolic_data = None
    neural_data = None
    symbolic_result = None
    neural_result = None
    
    try:
        # Load data
        symbolic_data = load_scaling_logs(symbolic_path)
        neural_data = load_scaling_logs(neural_path)
        
        # Perform regression
        symbolic_result = perform_log_log_regression(symbolic_data, "Symbolic")
        neural_result = perform_log_log_regression(neural_data, "Neural")
        
        # Compare
        diff, is_better, conclusion = compare_slopes(symbolic_result, neural_result)
        
        # Determine complexity classes
        sym_class = determine_complexity_class_from_slope(symbolic_result.slope, symbolic_result.r_squared)
        neu_class = determine_complexity_class_from_slope(neural_result.slope, neural_result.r_squared)
        
        status = "PASS" if is_better and symbolic_result.r_squared >= 0.85 and neural_result.r_squared >= 0.85 else "INCONCLUSIVE"
        
        comparison = ComplexityComparison(
            symbolic_result=symbolic_result,
            neural_result=neural_result,
            slope_difference=diff,
            is_symbolic_more_efficient=is_better,
            conclusion=conclusion,
            status=status
        )
        
        # Prepare output
        output_data = {
            "symbolic_regression": asdict(comparison.symbolic_result),
            "symbolic_complexity_class": sym_class,
            "neural_regression": asdict(comparison.neural_result),
            "neural_complexity_class": neu_class,
            "slope_difference": comparison.slope_difference,
            "is_symbolic_more_efficient": comparison.is_symbolic_more_efficient,
            "conclusion": comparison.conclusion,
            "status": comparison.status
        }
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Comparison complete. Status: {status}. Output written to {output_path}")
        print(f"SUCCESS: {output_path} created.")
        
    except FileNotFoundError as e:
        logger.critical(f"Missing required data file: {e}")
        print(f"FAILED: Missing data file. {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Data validation error: {e}")
        print(f"FAILED: Data validation error. {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during comparison: {e}", exc_info=True)
        print(f"FAILED: Unexpected error. {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()