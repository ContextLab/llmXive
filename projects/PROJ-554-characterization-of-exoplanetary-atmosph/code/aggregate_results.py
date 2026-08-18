"""
Aggregate all statistics into a single analysis results JSON file.

This task (T030d) reads the outputs from:
- T030a: correlation_stats.json
- T030b: regression_stats.json
- T030c: mdc_stats.json
- T026: robustness_report.json
- T031: power_analysis.json (if available)
- T035: signal_noise_analysis.csv (if available)

And combines them into data/processed/analysis_results.json.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from config import get_config

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def load_json_file(file_path: Path, required: bool = True) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if not found and not required."""
    if not file_path.exists():
        if required:
            logger.warning(f"Required file not found: {file_path}")
            return None
        logger.info(f"Optional file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {file_path}: {e}")
        return None

def load_csv_file(file_path: Path, required: bool = False) -> Optional[pd.DataFrame]:
    """Load a CSV file, returning None if not found and not required."""
    if not file_path.exists():
        if required:
            logger.warning(f"Required file not found: {file_path}")
            return None
        logger.info(f"Optional file not found: {file_path}")
        return None
    
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to parse CSV from {file_path}: {e}")
        return None

def aggregate_analysis_results(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate all statistics into a single analysis results dictionary.
    
    Args:
        config: Configuration dictionary from get_config()
        
    Returns:
        Dictionary containing all aggregated statistics
    """
    data_processed_dir = Path(config['data_processed_dir'])
    results_dir = Path(config['results_dir'])
    
    # Initialize the aggregated results
    aggregated_results = {
        'metadata': {
            'generated_from': 'T030d_aggregate_results',
            'data_processed_dir': str(data_processed_dir),
            'results_dir': str(results_dir)
        },
        'correlation_analysis': {},
        'regression_analysis': {},
        'mdc_analysis': {},
        'robustness_analysis': {},
        'power_analysis': {},
        'signal_noise_analysis': {},
        'reviewer_compliance': {}
    }
    
    # Load T030a: correlation_stats.json
    correlation_file = data_processed_dir / 'correlation_stats.json'
    correlation_data = load_json_file(correlation_file, required=True)
    if correlation_data:
        aggregated_results['correlation_analysis'] = correlation_data
        # Extract CI for reviewer compliance
        if 'kendall_tau_ci' in correlation_data:
            aggregated_results['reviewer_compliance']['correlation_95_ci'] = correlation_data['kendall_tau_ci']
    
    # Load T030b: regression_stats.json
    regression_file = data_processed_dir / 'regression_stats.json'
    regression_data = load_json_file(regression_file, required=True)
    if regression_data:
        aggregated_results['regression_analysis'] = regression_data
        # Extract coefficients CI for reviewer compliance
        if 'coefficients_ci' in regression_data:
            aggregated_results['reviewer_compliance']['regression_95_ci'] = regression_data['coefficients_ci']
    
    # Load T030c: mdc_stats.json
    mdc_file = data_processed_dir / 'mdc_stats.json'
    mdc_data = load_json_file(mdc_file, required=True)
    if mdc_data:
        aggregated_results['mdc_analysis'] = mdc_data
    
    # Load T026: robustness_report.json
    robustness_file = results_dir / 'robustness_report.json'
    robustness_data = load_json_file(robustness_file, required=False)
    if robustness_data:
        aggregated_results['robustness_analysis'] = robustness_data
    
    # Load T031: power_analysis.json (optional)
    power_file = results_dir / 'power_analysis.json'
    power_data = load_json_file(power_file, required=False)
    if power_data:
        aggregated_results['power_analysis'] = power_data
    
    # Load T035: signal_noise_analysis.csv (optional)
    signal_noise_file = results_dir / 'signal_noise_analysis.csv'
    signal_noise_data = load_csv_file(signal_noise_file, required=False)
    if signal_noise_data is not None:
        # Convert DataFrame to dict for JSON serialization
        aggregated_results['signal_noise_analysis'] = {
            'records': signal_noise_data.to_dict('records'),
            'count': len(signal_noise_data)
        }
        # Check if correlation is valid based on SNR thresholds
        if 'correlation_valid' in signal_noise_data.columns:
            valid_flags = signal_noise_data['correlation_valid'].unique()
            if len(valid_flags) == 1 and valid_flags[0] is True:
                aggregated_results['reviewer_compliance']['correlation_valid_snr'] = True
            else:
                aggregated_results['reviewer_compliance']['correlation_valid_snr'] = False
    
    # Add sample size info if available from T013a
    count_file = data_processed_dir / 'count_report.json'
    count_data = load_json_file(count_file, required=False)
    if count_data:
        aggregated_results['metadata']['sample_size'] = count_data.get('count')
    
    # Add validation status from T013b
    validation_file = data_processed_dir / 'sample_size_report.json'
    validation_data = load_json_file(validation_file, required=False)
    if validation_data:
        aggregated_results['metadata']['sample_validation_status'] = validation_data.get('validation_status')
    
    logger.info(f"Aggregated results from correlation, regression, MDC, robustness, power, and signal-noise analyses.")
    return aggregated_results

def save_aggregated_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save the aggregated results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved aggregated analysis results to {output_path}")

def main():
    """Main entry point for T030d."""
    logger.info("Starting T030d: Aggregate all statistics into analysis_results.json")
    
    config = get_config()
    data_processed_dir = Path(config['data_processed_dir'])
    
    # Ensure required directories exist
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    Path(config['results_dir']).mkdir(parents=True, exist_ok=True)
    
    # Aggregate results
    aggregated_results = aggregate_analysis_results(config)
    
    # Define output path
    output_path = data_processed_dir / 'analysis_results.json'
    
    # Save results
    save_aggregated_results(aggregated_results, output_path)
    
    logger.info(f"T030d completed successfully. Output: {output_path}")
    return output_path

if __name__ == '__main__':
    main()
