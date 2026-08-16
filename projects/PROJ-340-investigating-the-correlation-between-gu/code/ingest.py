import os
import sys
import json
import logging
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ingest')

class RealDataFetchError(Exception):
    """Raised when real data fetch fails."""
    def __init__(self, source_id, message):
        super().__init__(f"RealDataFetchError: Source {source_id} not found. {message}")

def setup_paths(project_root=None):
    """Setup standard paths for the project."""
    if project_root is None:
        project_root = Path(__file__).parent.parent
    return {
        'raw': project_root / 'data' / 'raw',
        'processed': project_root / 'data' / 'processed',
        'results': project_root / 'data' / 'results',
        'metadata': project_root / 'data' / 'metadata',
        'config': project_root / 'data' / 'config',
        'state': project_root / 'state' / 'projects'
    }

def load_schema(schema_path):
    """Load schema from YAML file."""
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_required_variables(config_path='data/config/required_variables.yaml'):
    """Load required variables from config."""
    if not os.path.exists(config_path):
        logger.warning(f"Required variables config not found: {config_path}")
        return {'required_predictors': [], 'required_outcomes': []}

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def validate_variables(df, required_predictors, required_outcomes):
    """
    Validate that required variables are present in the dataframe.
    Returns validation status and metrics.
    """
    missing_predictors = [p for p in required_predictors if p not in df.columns]
    missing_outcomes = [o for o in required_outcomes if o not in df.columns]
    missing_all = missing_predictors + missing_outcomes

    total_required = len(required_predictors) + len(required_outcomes)
    found = total_required - len(missing_all)
    percentage = (found / total_required * 100) if total_required > 0 else 0.0

    status = "PASS" if len(missing_all) == 0 else "FAIL"

    metrics = {
        'status': status,
        'percentage_loaded': percentage,
        'missing_variables': missing_all,
        'total_required': total_required,
        'missing_predictors': missing_predictors,
        'missing_outcomes': missing_outcomes
    }

    return status, metrics

def fetch_real_data(sources_config='data/config/real_data_sources.yaml'):
    """
    Fetch real data from verified sources.
    Raises RealDataFetchError if sources are missing or invalid.
    """
    if not os.path.exists(sources_config):
        raise RealDataFetchError("none", "No real data sources configured")

    with open(sources_config, 'r') as f:
        sources = yaml.safe_load(f)

    if not sources or not sources.get('sources'):
        raise RealDataFetchError("none", "No valid sources found in configuration")

    # In a real implementation, this would download from the specified URLs/IDs
    # For now, we raise an error if no real data file exists
    raise RealDataFetchError("none", "Real data fetch not implemented - no verified source available")

def detect_outliers_iqr(df, columns=None):
    """
    Detect outliers using IQR method.
    Returns dict of column -> list of outlier indices.
    """
    outliers = {}
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns

    for col in columns:
        if col not in df.columns:
            continue
        data = df[col]
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (data < lower_bound) | (data > upper_bound)
        outlier_indices = df.index[outlier_mask].tolist()
        if outlier_indices:
            outliers[col] = outlier_indices

    return outliers

def save_outlier_report(outliers, output_path='data/results/outlier_report.json'):
    """Save outlier report to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Flatten all outlier indices
    all_indices = []
    for col, indices in outliers.items():
        all_indices.extend(indices)
    all_indices = sorted(list(set(all_indices)))

    report = {
        'count': len(all_indices),
        'excluded_indices': all_indices,
        'per_column': outliers
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report

def filter_outliers(df, outliers):
    """Filter outliers from dataframe."""
    all_indices = []
    for col, indices in outliers.items():
        all_indices.extend(indices)
    all_indices = list(set(all_indices))

    filtered_df = df.drop(index=all_indices)
    return filtered_df

def save_filtered_data(df, output_path='data/processed/filtered_data.parquet'):
    """Save filtered data to parquet."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)

def record_artifact_checksum(file_path, state_file):
    """Record checksum of an artifact in state file."""
    import yaml
    if not os.path.exists(file_path):
        return

    with open(file_path, 'rb') as f:
        content = f.read()
    checksum = hashlib.sha256(content).hexdigest()

    state = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}

    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}

    state['artifact_hashes'][str(file_path)] = f"sha256:{checksum}"

    with open(state_file, 'w') as f:
        yaml.dump(state, f)

def load_data(data_path, mode='real'):
    """
    Load data from file, validating variables first.
    """
    df = pd.read_csv(data_path)

    # Load required variables
    required_config = load_required_variables()
    required_predictors = required_config.get('required_predictors', [])
    required_outcomes = required_config.get('required_outcomes', [])

    # Validate
    status, metrics = validate_variables(df, required_predictors, required_outcomes)

    # Always write metrics
    metrics_path = 'data/results/variable_load_metrics.json'
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    if status == "FAIL":
        # Write failure report
        failure_report = {
            'status': 'FAIL',
            'error_code': 'MISSING_VARIABLES',
            'missing_variables': metrics['missing_variables'],
            'timestamp': datetime.now().isoformat(),
            'message': f"Missing required variables: {', '.join(metrics['missing_variables'])}"
        }
        failure_path = 'data/results/validation_failure_report.json'
        with open(failure_path, 'w') as f:
            json.dump(failure_report, f, indent=2)
        logger.error(failure_report['message'])
        sys.exit(1)

    return df

def main():
    """Main entry point for ingestion."""
    parser = argparse.ArgumentParser(description='Data ingestion and validation')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--mode', type=str, default='real', help='Data mode: real or synthetic')
    args = parser.parse_args()

    paths = setup_paths()
    os.makedirs(paths['raw'], exist_ok=True)
    os.makedirs(paths['processed'], exist_ok=True)
    os.makedirs(paths['results'], exist_ok=True)
    os.makedirs(paths['metadata'], exist_ok=True)

    # Load and validate
    df = load_data(args.input, mode=args.mode)

    # Detect and filter outliers
    outliers = detect_outliers_iqr(df)
    save_outlier_report(outliers)

    filtered_df = filter_outliers(df, outliers)
    save_filtered_data(filtered_df)

    # Record checksum
    state_file = paths['state'] / 'PROJ-340-investigating-the-correlation-between-gu.yaml'
    record_artifact_checksum(str(paths['processed'] / 'filtered_data.parquet'), str(state_file))

    logger.info(f"Ingestion complete. Filtered data saved to {paths['processed'] / 'filtered_data.parquet'}")

if __name__ == '__main__':
    import pandas as pd
    from datetime import datetime
    import numpy as np
    main()
