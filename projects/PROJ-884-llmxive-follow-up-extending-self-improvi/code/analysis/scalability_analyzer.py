"""
Scalability Analyzer Module.
Implements log-log linear regression to derive complexity class (Big-O).
"""
import json
import csv
import math
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Ensure project root is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scipy import stats
except ImportError:
    print("ERROR: scipy is required for scalability analysis. Install with: pip install scipy")
    sys.exit(1)

@dataclass
class ScalingResult:
    n: int
    time: float
    complexity_class: str
    r_squared: float
    status: str  # 'PASS', 'FAIL', 'INCONCLUSIVE'

def load_scaling_logs(input_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the scaling raw logs from the JSON file.
    Fails loudly if the file does not exist or is invalid.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of experiment records.")
    
    return data

def determine_complexity_class(r_squared: float, slope: float) -> str:
    """
    Maps the regression slope to a complexity class string.
    """
    # Define thresholds for complexity classes based on slope
    # O(1): slope ~ 0
    # O(log n): slope ~ 0 (log-log slope is 0 for constant, but log n is distinct)
    # O(n): slope ~ 1
    # O(n log n): slope ~ 1 (slightly > 1)
    # O(n^2): slope ~ 2
    # O(n^3): slope ~ 3
    
    # We compare the slope to integers
    closest_power = round(slope)
    
    if closest_power == 0:
        if r_squared > 0.85:
            return "O(1)"
        return "O(log n)" # If R2 is low but slope is near 0, often log
    elif closest_power == 1:
        return "O(n)"
    elif closest_power == 2:
        return "O(n^2)"
    elif closest_power == 3:
        return "O(n^3)"
    else:
        return f"O(n^{slope:.2f})"

def perform_log_log_regression(data: List[Dict[str, Any]]) -> List[ScalingResult]:
    """
    Performs log-log linear regression on the data.
    Input: List of records with 'n' and 'avg_wall_clock' (or similar time metric).
    Output: List of ScalingResult objects.
    """
    results = []
    
    # Extract x (n) and y (time)
    # We assume the data is already aggregated by 'n' from T029a
    # T029a output structure: n, avg_wall_clock
    
    x_vals = []
    y_vals = []
    
    for record in data:
        n = record.get('n')
        time_val = record.get('avg_wall_clock')
        
        if n is None or time_val is None:
            logging.warning(f"Skipping record due to missing n or time: {record}")
            continue
        
        if n <= 0 or time_val <= 0:
            logging.warning(f"Skipping record due to non-positive n or time: {record}")
            continue
        
        x_vals.append(math.log(n))
        y_vals.append(math.log(time_val))
    
    if len(x_vals) < 2:
        raise ValueError("Insufficient data points for regression (need at least 2).")
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
    
    r_squared = r_value ** 2
    
    # Determine status based on R^2
    if r_squared >= 0.85:
        status = "PASS"
    else:
        status = "INCONCLUSIVE"
    
    complexity_class = determine_complexity_class(r_squared, slope)
    
    # Create a result for each data point, but the regression is global
    # The task requires outputting a row for each n with the derived class
    for i, record in enumerate(data):
        n = record.get('n')
        time_val = record.get('avg_wall_clock')
        
        if n is None or time_val is None:
            continue
            
        results.append(ScalingResult(
            n=n,
            time=time_val,
            complexity_class=complexity_class,
            r_squared=r_squared,
            status=status
        ))
    
    return results

def save_results_csv(results: List[ScalingResult], output_path: Path):
    """
    Saves the analysis results to a CSV file.
    Columns: n, time, complexity_class, r_squared, status
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['n', 'time', 'complexity_class', 'r_squared', 'status'])
        
        # Write data
        for res in results:
            writer.writerow([
                res.n,
                res.time,
                res.complexity_class,
                f"{res.r_squared:.4f}",
                res.status
            ])

def analyze_scaling(input_path: Path, output_path: Path):
    """
    Main orchestration function for scalability analysis.
    """
    logging.info(f"Loading scaling logs from {input_path}")
    data = load_scaling_logs(input_path)
    
    logging.info(f"Performing log-log regression on {len(data)} data points")
    results = perform_log_log_regression(data)
    
    logging.info(f"Saving results to {output_path}")
    save_results_csv(results, output_path)
    
    # Log summary
    if results:
        last_result = results[-1]
        logging.info(f"Analysis Complete. Complexity Class: {last_result.complexity_class}, R^2: {last_result.r_squared:.4f}, Status: {last_result.status}")
    else:
        logging.warning("No results generated.")

def main():
    """
    Entry point for the module.
    Uses hardcoded paths relative to project root as per T029b spec.
    """
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / "data" / "processed" / "scaling_raw_logs.json"
    output_file = project_root / "data" / "processed" / "scaling_analysis.csv"
    
    try:
        analyze_scaling(input_file, output_file)
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()