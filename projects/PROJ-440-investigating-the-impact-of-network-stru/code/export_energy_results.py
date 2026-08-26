import os
import sys
import json
import logging
import argparse
import hashlib
import pandas as pd
from pathlib import Path

from code.utils.error_handling import filter_failed_results, handle_simulation_failure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_simulation_results(filepath):
    """Load simulation results from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulation results file not found: {filepath}")

    with open(filepath, 'r') as f:
        return json.load(f)

def classify_instance(result):
    """
    Classify a simulation instance as 'dissipative' or 'resonant'.
    
    Args:
        result: Simulation result dictionary
        
    Returns:
        Classification string
    """
    if result.get('status') == 'resonant':
        return 'resonant'
    elif result.get('status') == 'dissipative':
        return 'dissipative'
    else:
        return 'unknown'

def export_results_to_csv(results, output_path, error_log_path=None):
    """
    Export simulation results to CSV with error handling.
    
    Args:
        results: List of simulation results (including failed ones)
        output_path: Path for output CSV
        error_log_path: Path for error log (optional)
        
    Returns:
        Tuple of (valid_results_count, excluded_count)
    """
    # Separate valid and failed results
    valid_results = []
    excluded_results = []

    for result in results:
        if result.get('status') == 'failed' or result.get('decay_rate') is None:
            excluded_results.append(result)
        else:
            valid_results.append(result)

    # Log exclusions
    if excluded_results:
        logger.warning(f"Excluding {len(excluded_results)} failed simulations from analysis")
        
        if error_log_path:
            with open(error_log_path, 'w') as f:
                f.write("Excluded Simulations Log\n")
                f.write("=" * 50 + "\n\n")
                for error in excluded_results:
                    f.write(f"Graph ID: {error.get('graph_id', 'N/A')}\n")
                    f.write(f"Error Type: {error.get('error_type', 'N/A')}\n")
                    f.write(f"Message: {error.get('error_message', 'N/A')}\n")
                    f.write("-" * 30 + "\n")
            logger.info(f"Exclusion log written to {error_log_path}")

    # Prepare data for CSV
    csv_data = []
    for result in valid_results:
        csv_data.append({
            'graph_id': result.get('graph_id'),
            'decay_rate': result.get('decay_rate'),
            'r_squared': result.get('r_squared'),
            'status': classify_instance(result),
            'n_nodes': result.get('n_nodes'),
            'seed': result.get('seed')
        })

    # Create DataFrame and export
    df = pd.DataFrame(csv_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Exported {len(csv_data)} valid results to {output_path}")
    logger.info(f"Excluded {len(excluded_results)} failed simulations")

    return len(csv_data), len(excluded_results)

def generate_final_report(results, output_path):
    """
    Generate a final report summarizing the simulation results.
    
    Args:
        results: List of all simulation results
        output_path: Path for the report JSON file
    """
    valid_results = [r for r in results if r.get('status') != 'failed']
    failed_results = [r for r in results if r.get('status') == 'failed']

    report = {
        'summary': {
            'total_simulations': len(results),
            'successful_simulations': len(valid_results),
            'failed_simulations': len(failed_results),
            'success_rate': len(valid_results) / len(results) if results else 0
        },
        'statistics': {
            'mean_decay_rate': float(pd.DataFrame(valid_results)['decay_rate'].mean()) if valid_results else 0,
            'std_decay_rate': float(pd.DataFrame(valid_results)['decay_rate'].std()) if valid_results else 0,
            'mean_r_squared': float(pd.DataFrame(valid_results)['r_squared'].mean()) if valid_results else 0
        },
        'excluded_count': len(failed_results),
        'excluded_graphs': [r.get('graph_id') for r in failed_results]
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final report generated at {output_path}")
    return report

def main():
    """Main function to export simulation results."""
    parser = argparse.ArgumentParser(description='Export simulation results to CSV')
    parser.add_argument('--input', type=str, default='data/processed/simulation_results.json',
                      help='Path to simulation results JSON file')
    parser.add_argument('--output-csv', type=str, default='data/processed/energy_decay.csv',
                      help='Path to output CSV file')
    parser.add_argument('--output-report', type=str, default='data/analysis/export_report.json',
                      help='Path to output report JSON file')
    parser.add_argument('--error-log', type=str, default='logs/excluded_simulations.log',
                      help='Path to error log file')
    args = parser.parse_args()

    logger.info(f"Loading simulation results from {args.input}")
    try:
        results = load_simulation_results(args.input)
        logger.info(f"Loaded {len(results)} results")
    except Exception as e:
        logger.error(f"Failed to load results: {str(e)}")
        sys.exit(1)

    # Export to CSV
    valid_count, excluded_count = export_results_to_csv(
        results, 
        args.output_csv, 
        args.error_log
    )

    # Generate final report
    report = generate_final_report(results, args.output_report)

    logger.info(f"Export complete: {valid_count} valid, {excluded_count} excluded")

if __name__ == '__main__':
    main()