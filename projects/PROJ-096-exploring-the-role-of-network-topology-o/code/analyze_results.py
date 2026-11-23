"""
Analysis module for User Story 3: Quantify Topological Influence via Statistical Correlation.

Implements Spearman correlation and p-value calculation between rewiring probability (p)
and critical coupling strength (Kc).

Dependency: T025 (simulation_results.csv)
Output: data/processed/correlation_results.json
"""
import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import from project utils as per API surface
try:
    from utils.stats_utils import spearman_correlation
except ImportError:
    # Fallback for direct execution or path issues during testing
    # In production, the runner ensures code/ is in sys.path
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.stats_utils import spearman_correlation

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load simulation results from CSV.
    
    Args:
        input_path: Path to simulation_results.csv
        
    Returns:
        List of dictionaries containing simulation results.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    results = []
    required_columns = {'topology_id', 'p', 'kc_binary'}
    
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Verify columns
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header")
        
        missing_cols = required_columns - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        for row in reader:
            try:
                results.append({
                    'topology_id': row['topology_id'],
                    'p': float(row['p']),
                    'kc_binary': float(row['kc_binary']),
                    'kc_linear': float(row['kc_linear']) if row['kc_linear'] else None,
                    'status': row['status']
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row: {row}. Error: {e}")
                continue
    
    if not results:
        raise ValueError("No valid data rows found in simulation results")
    
    return results

def calculate_correlation(input_path: str, output_path: str) -> Dict[str, float]:
    """
    Calculate Spearman correlation and p-value between rewiring probability (p)
    and critical coupling strength (Kc).
    
    This function:
    1. Loads simulation results from CSV
    2. Extracts p values and Kc values
    3. Computes Spearman correlation coefficient and p-value
    4. Writes results to JSON file
    
    Args:
        input_path: Path to simulation_results.csv
        output_path: Path to output correlation_results.json
        
    Returns:
        Dictionary with 'correlation' and 'p_value' keys.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If insufficient data points for correlation.
    """
    # Load data
    logger.info(f"Loading simulation results from {input_path}")
    results = load_simulation_results(input_path)
    
    if len(results) < 3:
        raise ValueError(f"Insufficient data points for correlation: {len(results)}")
    
    # Extract arrays
    p_values = np.array([r['p'] for r in results])
    kc_values = np.array([r['kc_binary'] for r in results])
    
    # Remove any NaN values (should not happen if data is valid, but safety check)
    valid_mask = ~(np.isnan(p_values) | np.isnan(kc_values))
    p_clean = p_values[valid_mask]
    kc_clean = kc_values[valid_mask]
    
    if len(p_clean) < 3:
        raise ValueError(f"Insufficient valid data points after filtering: {len(p_clean)}")
    
    logger.info(f"Computing Spearman correlation with {len(p_clean)} data points")
    
    # Calculate Spearman correlation using project utils
    # The API surface shows spearman_correlation returns (stat, p_value)
    corr_stat, p_val = spearman_correlation(p_clean, kc_clean)
    
    # Prepare results
    correlation_results = {
        'correlation': float(corr_stat),
        'p_value': float(p_val),
        'n_samples': len(p_clean),
        'method': 'spearman',
        'input_file': input_path,
        'output_file': output_path
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write results to JSON
    logger.info(f"Writing correlation results to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(correlation_results, f, indent=2)
    
    logger.info(f"Correlation: {corr_stat:.4f}, p-value: {p_val:.4e}")
    
    return correlation_results

def main():
    """
    Main entry point for correlation analysis.
    """
    # Default paths (can be overridden by command line args)
    input_path = 'data/processed/simulation_results.csv'
    output_path = 'data/processed/correlation_results.json'
    
    # Parse command line arguments
    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    
    try:
        results = calculate_correlation(input_path, output_path)
        logger.info("Analysis completed successfully")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 3

if __name__ == '__main__':
    sys.exit(main())