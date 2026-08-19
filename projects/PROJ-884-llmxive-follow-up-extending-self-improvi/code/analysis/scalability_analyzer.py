"""
Scalability Analyzer Module.

This module implements the log-log linear regression analysis for
determining the complexity class (Big-O) of the BES algorithm.

Input: data/processed/scaling_raw_logs.json
Output: data/processed/scaling_analysis.csv
"""
import json
import csv
import math
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScalingResult:
    """Represents the result of a scalability analysis for a single data point."""
    n: int
    time: float
    complexity_class: str
    r_squared: float

def load_scaling_logs(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load scaling logs from a JSON file.
    
    Args:
        input_path: Path to the scaling_raw_logs.json file
        
    Returns:
        List of log entries with 'n' and 'time' fields
        
    Raises:
        FileNotFoundError: If the input file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {input_path}, got {type(data)}")
    
    # Validate that each entry has required fields
    for entry in data:
        if 'n' not in entry or 'time' not in entry:
            raise ValueError(f"Entry missing 'n' or 'time' field: {entry}")
    
    logger.info(f"Loaded {len(data)} entries from {input_path}")
    return data


def perform_log_log_regression(n_values: List[int], time_values: List[float]) -> Tuple[float, float]:
    """
    Perform log-log linear regression to determine the slope and R-squared.
    
    The regression fits: log(time) = slope * log(n) + intercept
    
    Args:
        n_values: List of problem sizes (n)
        time_values: List of corresponding execution times
        
    Returns:
        Tuple of (slope, r_squared)
        
    Note:
        If there are fewer than 2 data points, returns (0.0, 0.0)
        If any value is <= 0, that point is skipped (log undefined)
    """
    if len(n_values) < 2:
        logger.warning("Insufficient data points for regression (need at least 2)")
        return 0.0, 0.0
    
    # Filter out non-positive values (log undefined)
    valid_points = [
        (n, t) for n, t in zip(n_values, time_values)
        if n > 0 and t > 0
    ]
    
    if len(valid_points) < 2:
        logger.warning("Not enough valid positive data points for regression")
        return 0.0, 0.0
    
    # Take logs
    log_n = [math.log(n) for n, _ in valid_points]
    log_t = [math.log(t) for _, t in valid_points]
    
    n_points = len(log_n)
    
    # Calculate means
    mean_log_n = sum(log_n) / n_points
    mean_log_t = sum(log_t) / n_points
    
    # Calculate slope and intercept using least squares
    numerator = sum((log_n[i] - mean_log_n) * (log_t[i] - mean_log_t) for i in range(n_points))
    denominator = sum((log_n[i] - mean_log_n) ** 2 for i in range(n_points))
    
    if abs(denominator) < 1e-10:
        logger.warning("Denominator too small in regression, likely constant n values")
        return 0.0, 0.0
    
    slope = numerator / denominator
    intercept = mean_log_t - slope * mean_log_n
    
    # Calculate R-squared
    ss_tot = sum((log_t[i] - mean_log_t) ** 2 for i in range(n_points))
    ss_res = sum((log_t[i] - (slope * log_n[i] + intercept)) ** 2 for i in range(n_points))
    
    if ss_tot < 1e-10:
        r_squared = 1.0 if ss_res < 1e-10 else 0.0
    else:
        r_squared = 1.0 - (ss_res / ss_tot)
    
    return slope, r_squared


def determine_complexity_class(slope: float, r_squared: float) -> str:
    """
    Determine the complexity class based on regression slope and R-squared.
    
    Args:
        slope: The slope from log-log regression
        r_squared: The R-squared value of the regression
        
    Returns:
        Complexity class string: 'O(n)', 'O(n^2)', 'O(n^3)', or 'UNKNOWN'
        
    Note:
        If R-squared < 0.85, returns 'UNKNOWN' regardless of slope
    """
    if r_squared < 0.85:
        return "UNKNOWN"
    
    # Map slope to complexity class
    # O(n): slope ~ 1
    # O(n^2): slope ~ 2
    # O(n^3): slope ~ 3
    # O(log n): slope ~ 0
    # O(n log n): slope ~ 1 but with different characteristics (harder to distinguish with simple regression)
    
    if abs(slope - 1.0) < 0.2:
        return "O(n)"
    elif abs(slope - 2.0) < 0.2:
        return "O(n^2)"
    elif abs(slope - 3.0) < 0.2:
        return "O(n^3)"
    elif abs(slope) < 0.2:
        return "O(log n)"
    elif slope > 0 and slope < 1.5:
        # Could be O(n log n) or similar, but we'll call it O(n) for simplicity
        return "O(n)"
    else:
        # Unknown or non-standard complexity
        return "UNKNOWN"


def save_results_csv(results: List[ScalingResult], output_path: Path) -> None:
    """
    Save scalability analysis results to a CSV file.
    
    Args:
        results: List of ScalingResult objects
        output_path: Path to the output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['n', 'time', 'complexity_class', 'r_squared'])
        
        for result in results:
            writer.writerow([
                result.n,
                f"{result.time:.6f}",
                result.complexity_class,
                f"{result.r_squared:.6f}"
            ])
    
    logger.info(f"Saved {len(results)} results to {output_path}")


def analyze_scaling(input_path: Path, output_path: Path) -> List[ScalingResult]:
    """
    Perform full scalability analysis.
    
    1. Load scaling logs from input JSON
    2. Group data by 'n' and calculate average time for each n
    3. Perform log-log regression
    4. Determine complexity class
    5. Save results to CSV
    
    Args:
        input_path: Path to scaling_raw_logs.json
        output_path: Path to output scaling_analysis.csv
        
    Returns:
        List of ScalingResult objects
    """
    # Load data
    logs = load_scaling_logs(input_path)
    
    if not logs:
        logger.warning("No data found in input file")
        # Create empty output file with headers
        save_results_csv([], output_path)
        return []
    
    # Group by 'n' and calculate average time
    n_to_times: Dict[int, List[float]] = {}
    for entry in logs:
        n = entry['n']
        time = entry['time']
        if n not in n_to_times:
            n_to_times[n] = []
        n_to_times[n].append(time)
    
    # Calculate average time for each n
    n_values = sorted(n_to_times.keys())
    avg_times = [sum(n_to_times[n]) / len(n_to_times[n]) for n in n_values]
    
    logger.info(f"Analyzing {len(n_values)} distinct problem sizes")
    
    # Perform log-log regression on the aggregated data
    slope, r_squared = perform_log_log_regression(n_values, avg_times)
    
    logger.info(f"Regression results: slope={slope:.4f}, R^2={r_squared:.4f}")
    
    # Determine complexity class
    complexity_class = determine_complexity_class(slope, r_squared)
    
    logger.info(f"Determined complexity class: {complexity_class}")
    
    # Create results list (one entry per distinct n, all with same complexity class and r_squared)
    results = [
        ScalingResult(
            n=n,
            time=avg_time,
            complexity_class=complexity_class,
            r_squared=r_squared
        )
        for n, avg_time in zip(n_values, avg_times)
    ]
    
    # Save results
    save_results_csv(results, output_path)
    
    return results


def main():
    """
    Main entry point for scalability analysis.
    
    Reads from: data/processed/scaling_raw_logs.json
    Writes to: data/processed/scaling_analysis.csv
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "scaling_raw_logs.json"
    output_path = project_root / "data" / "processed" / "scaling_analysis.csv"
    
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        results = analyze_scaling(input_path, output_path)
        logger.info(f"Analysis complete. Processed {len(results)} data points.")
        
        # Print summary
        if results:
            unique_classes = set(r.complexity_class for r in results)
            logger.info(f"Complexity classes found: {', '.join(unique_classes)}")
            
            # Show the regression slope and R-squared from the first result (they're all the same)
            first_result = results[0]
            logger.info(f"Overall regression: slope={first_result.r_squared:.4f} (Note: r_squared is stored per row but same for all)")
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Please ensure T029c has been executed to generate scaling_raw_logs.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()