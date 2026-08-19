"""
Scalability Analysis Logic for llmXive.

Implements log-log linear regression and complexity class mapping
as required by T029e.
"""
import json
import csv
import math
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_INPUT_PATH = "data/processed/scaling_raw_logs.json"
DEFAULT_OUTPUT_PATH = "data/processed/scaling_analysis.csv"
R_SQUARED_THRESHOLD = 0.85

def load_scaling_logs(input_path: str = DEFAULT_INPUT_PATH) -> List[Dict[str, Any]]:
    """
    Load scaling experiment logs from JSON file.
    
    Args:
        input_path: Path to the scaling raw logs JSON file.
        
    Returns:
        List of log entries with puzzle size and timing data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling logs not found at {input_path}")
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    # Handle both list and dict with 'entries' key
    if isinstance(data, dict):
        if 'entries' in data:
            return data['entries']
        else:
            # Try to extract list from any key
            for key, value in data.items():
                if isinstance(value, list):
                    return value
            raise ValueError(f"Unexpected JSON structure in {input_path}")
            
    if isinstance(data, list):
        return data
        
    raise ValueError(f"Expected list or dict with 'entries' key, got {type(data)}")

def perform_log_log_regression(data: List[Dict[str, Any]]) -> Tuple[float, float, float]:
    """
    Perform log-log linear regression on scaling data.
    
    Fits the model: log(time) = a + b * log(n)
    where b is the complexity exponent.
    
    Args:
        data: List of log entries containing 'n' (puzzle size) and 'time' (duration).
        
    Returns:
        Tuple of (slope, intercept, r_squared)
        
    Raises:
        ValueError: If insufficient data points or invalid values.
    """
    # Extract valid data points
    points = []
    for entry in data:
        try:
            n = float(entry.get('n', entry.get('size', 0)))
            time_val = float(entry.get('time', entry.get('duration', 0)))
            
            if n > 0 and time_val > 0:
                points.append((math.log(n), math.log(time_val)))
        except (TypeError, ValueError):
            continue
            
    if len(points) < 2:
        raise ValueError("Insufficient valid data points for regression (need >= 2)")
        
    n_points = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)
    sum_y2 = sum(p[1] ** 2 for p in points)
    
    # Calculate slope (b) and intercept (a)
    denominator = n_points * sum_x2 - sum_x ** 2
    if abs(denominator) < 1e-10:
        raise ValueError("Degenerate data: all x values are identical")
        
    slope = (n_points * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n_points
    
    # Calculate R-squared
    mean_y = sum_y / n_points
    ss_tot = sum((y - mean_y) ** 2 for _, y in points)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in points)
    
    if ss_tot < 1e-10:
        r_squared = 1.0
    else:
        r_squared = 1.0 - (ss_res / ss_tot)
        
    return slope, intercept, r_squared

def determine_complexity_class(slope: float, r_squared: float) -> str:
    """
    Determine the complexity class based on regression slope and R-squared.
    
    Args:
        slope: The exponent from log-log regression.
        r_squared: The R-squared value of the fit.
        
    Returns:
        String representation of complexity class (e.g., 'O(n)', 'O(n^2)', 'UNKNOWN').
    """
    if r_squared < R_SQUARED_THRESHOLD:
        return 'UNKNOWN'
        
    # Round slope to nearest integer for standard complexity classes
    rounded_slope = round(slope)
    
    if abs(slope - rounded_slope) < 0.2:  # Allow some tolerance
        if rounded_slope <= 0:
            return 'O(1)'
        elif rounded_slope == 1:
            return 'O(n)'
        elif rounded_slope == 2:
            return 'O(n^2)'
        elif rounded_slope == 3:
            return 'O(n^3)'
        else:
            return f'O(n^{rounded_slope})'
    else:
        # Non-integer exponent
        return f'O(n^{slope:.2f})'

def save_results_csv(results: List[Dict[str, Any]], output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """
    Save analysis results to CSV file.
    
    Args:
        results: List of result dictionaries with n, time, complexity_class, r_squared.
        output_path: Path for the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        fieldnames = ['n', 'time', 'complexity_class', 'r_squared']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    logger.info(f"Results saved to {output_path}")

def analyze_scaling(
    input_path: str = DEFAULT_INPUT_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH
) -> Dict[str, Any]:
    """
    Main function to perform scalability analysis.
    
    Args:
        input_path: Path to scaling raw logs.
        output_path: Path for output CSV.
        
    Returns:
        Dictionary containing analysis results including slope, intercept, r_squared,
        complexity_class, and the list of individual results.
    """
    logger.info(f"Loading scaling logs from {input_path}")
    data = load_scaling_logs(input_path)
    
    if not data:
        raise ValueError("No data points found in scaling logs")
        
    logger.info(f"Loaded {len(data)} data points")
    
    # Perform regression
    slope, intercept, r_squared = perform_log_log_regression(data)
    logger.info(f"Regression complete: slope={slope:.4f}, intercept={intercept:.4f}, R²={r_squared:.4f}")
    
    # Determine complexity class
    complexity_class = determine_complexity_class(slope, r_squared)
    logger.info(f"Determined complexity class: {complexity_class}")
    
    # Prepare results for each data point
    results = []
    for entry in data:
        try:
            n = float(entry.get('n', entry.get('size', 0)))
            time_val = float(entry.get('time', entry.get('duration', 0)))
            
            if n > 0 and time_val > 0:
                results.append({
                    'n': n,
                    'time': time_val,
                    'complexity_class': complexity_class,
                    'r_squared': round(r_squared, 4)
                })
        except (TypeError, ValueError):
            continue
            
    # Save results
    save_results_csv(results, output_path)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'complexity_class': complexity_class,
        'data_points': len(results),
        'threshold': R_SQUARED_THRESHOLD,
        'results': results
    }

def main():
    """Command-line entry point for scalability analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Perform scalability analysis on experiment logs')
    parser.add_argument(
        '--input', 
        type=str, 
        default=DEFAULT_INPUT_PATH,
        help=f'Input JSON file path (default: {DEFAULT_INPUT_PATH})'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default=DEFAULT_OUTPUT_PATH,
        help=f'Output CSV file path (default: {DEFAULT_OUTPUT_PATH})'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=R_SQUARED_THRESHOLD,
        help=f'R-squared threshold for complexity classification (default: {R_SQUARED_THRESHOLD})'
    )
    
    args = parser.parse_args()
    
    try:
        result = analyze_scaling(args.input, args.output)
        
        print("\n" + "="*50)
        print("SCALABILITY ANALYSIS RESULTS")
        print("="*50)
        print(f"Data points analyzed: {result['data_points']}")
        print(f"Regression slope: {result['slope']:.4f}")
        print(f"Regression intercept: {result['intercept']:.4f}")
        print(f"R-squared: {result['r_squared']:.4f}")
        print(f"Complexity class: {result['complexity_class']}")
        print(f"R-squared threshold: {result['threshold']}")
        print(f"Output file: {args.output}")
        print("="*50)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())