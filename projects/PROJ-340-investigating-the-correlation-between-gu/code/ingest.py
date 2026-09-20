"""
Data Ingestion and Validation Module.

Handles loading, validating, and preprocessing data for the pipeline.
Implements strict fail-loud behavior for real data fetching.
"""
import os
import sys
import json
import logging
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealDataFetchError(Exception):
    """Raised when real data fetching fails and no valid fallback is configured."""
    pass

def setup_paths():
    """Setup standard directory paths."""
    paths = {
        'raw': Path('data/raw'),
        'processed': Path('data/processed'),
        'results': Path('data/results'),
        'metadata': Path('data/metadata'),
        'config': Path('data/config'),
        'candidates': Path('data/candidates')
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths

def load_schema(schema_path='specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml'):
    """Load dataset schema from YAML file."""
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found: {schema_path}. Using default schema.")
        return {
            'predictors': ['taxon_abundance', 'relative_abundance'],
            'outcomes': ['rem_duration', 'sws_duration', 'total_sleep_time']
        }
    
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_required_variables(config_path='data/config/required_variables.yaml'):
    """Load required variables from configuration."""
    if not os.path.exists(config_path):
        logger.error(f"Required variables config not found: {config_path}")
        return {'required_predictors': [], 'required_outcomes': []}
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return {
        'required_predictors': config.get('required_predictors', []),
        'required_outcomes': config.get('required_outcomes', [])
    }

def validate_variables(df: pd.DataFrame, required: Dict) -> Tuple[bool, Dict]:
    """
    Validate that the DataFrame contains all required variables.
    
    Returns:
        Tuple of (is_valid, metrics_dict)
    """
    columns = set(df.columns)
    missing_predictors = [p for p in required['required_predictors'] if p not in columns]
    missing_outcomes = [o for o in required['required_outcomes'] if o not in columns]
    
    metrics = {
        'total_columns': len(columns),
        'required_predictors': len(required['required_predictors']),
        'found_predictors': len(required['required_predictors']) - len(missing_predictors),
        'missing_predictors': missing_predictors,
        'required_outcomes': len(required['required_outcomes']),
        'found_outcomes': len(required['required_outcomes']) - len(missing_outcomes),
        'missing_outcomes': missing_outcomes,
        'is_valid': len(missing_predictors) == 0 and len(missing_outcomes) == 0
    }
    
    if not metrics['is_valid']:
        error_msg = f"Missing required variables: {missing_predictors + missing_outcomes}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Validation passed: {metrics['found_predictors']}/{metrics['required_predictors']} predictors, "
               f"{metrics['found_outcomes']}/{metrics['required_outcomes']} outcomes")
    return True, metrics

def fetch_real_data(source_config_path='data/config/real_data_sources.yaml'):
    """
    Fetch real data from configured sources.
    
    STRICT FAIL-LOUD BEHAVIOR: Raises RealDataFetchError if no valid source is found.
    """
    if not os.path.exists(source_config_path):
        raise RealDataFetchError(f"No real data source configuration found at {source_config_path}")
    
    import yaml
    with open(source_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    sources = config.get('sources', [])
    if not sources:
        raise RealDataFetchError("No data sources configured in real_data_sources.yaml")
    
    for source in sources:
        url = source.get('url')
        if not url:
            continue
        
        logger.info(f"Attempting to fetch data from: {url}")
        # In a real implementation, this would download the data
        # For now, we check if a local file exists that matches
        local_path = source.get('local_path')
        if local_path and os.path.exists(local_path):
            logger.info(f"Using local cached data: {local_path}")
            return pd.read_csv(local_path)
        
        # If we get here, we'd need to download - but we don't have a real URL in this context
        raise RealDataFetchError(f"Cannot fetch real data from {url} - no local cache and no real API access")
    
    raise RealDataFetchError("No valid data sources could be accessed")

def detect_outliers_iqr(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """
    Detect outliers using the IQR method.
    
    Returns a DataFrame with outlier flags.
    """
    if columns is None:
        # Use numeric columns only
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    outlier_report = []
    
    for col in columns:
        if col not in df.columns:
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        is_outlier = (df[col] < lower_bound) | (df[col] > upper_bound)
        
        for idx in df[is_outlier].index:
            outlier_report.append({
                'subject_id': idx,
                'metric': col,
                'value': df.loc[idx, col],
                'is_outlier': True,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            })
    
    return pd.DataFrame(outlier_report) if outlier_report else pd.DataFrame(columns=['subject_id', 'metric', 'value', 'is_outlier'])

def save_outlier_report(outlier_df: pd.DataFrame, output_path='data/results/outlier_report.json'):
    """Save outlier report to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'outliers': outlier_df.to_dict(orient='records'),
        'exclusion_count': len(outlier_df)
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Outlier report saved to {output_path}")
    return report

def filter_outliers(df: pd.DataFrame, outlier_df: pd.DataFrame) -> pd.DataFrame:
    """Remove outliers from the dataset."""
    if outlier_df.empty:
        logger.info("No outliers to filter")
        return df
    
    # Get unique (subject_id, metric) pairs to exclude
    to_exclude = set(zip(outlier_df['subject_id'], outlier_df['metric']))
    
    # Filter the dataframe
    mask = df.index.map(lambda idx: (idx, None) not in to_exclude)
    filtered_df = df[mask]
    
    logger.info(f"Filtered {len(df) - len(filtered_df)} outlier rows")
    return filtered_df

def save_filtered_data(df: pd.DataFrame, output_path='data/processed/filtered_data.parquet'):
    """Save filtered data to Parquet."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Filtered data saved to {output_path}")
    return output_path

def record_artifact_checksum(file_path: str, state_file: str = 'state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml'):
    """Record checksum of an artifact in the state file."""
    if not os.path.exists(file_path):
        logger.warning(f"Cannot record checksum for non-existent file: {file_path}")
        return None
    
    with open(file_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    import yaml
    state = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes'][file_path] = checksum
    
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"Recorded checksum for {file_path}")
    return checksum

def load_data(input_path: str = None, allow_synthetic: bool = False, pipeline_validation: bool = False) -> pd.DataFrame:
    """
    Main data loading function.
    
    Args:
        input_path: Path to input CSV file
        allow_synthetic: If True, allow synthetic data fallback
        pipeline_validation: If True, enable pipeline validation mode
    
    Returns:
        DataFrame with loaded data
    """
    paths = setup_paths()
    
    # Try to load real data first
    if input_path and os.path.exists(input_path):
        logger.info(f"Loading data from: {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        return df
    
    # Check for real data source configuration
    if os.path.exists('data/config/real_data_sources.yaml'):
        try:
            logger.info("Attempting to fetch real data...")
            df = fetch_real_data()
            return df
        except RealDataFetchError as e:
            if allow_synthetic or pipeline_validation:
                logger.warning(f"Real data fetch failed: {e}. Falling back to synthetic data (validation mode).")
                # Generate synthetic data
                from generate_synthetic_data import main as gen_main
                gen_main()
                input_path = 'data/raw/synthetic_test_data.csv'
                if os.path.exists(input_path):
                    df = pd.read_csv(input_path)
                    return df
            else:
                raise RealDataFetchError(f"Real data fetch failed and synthetic fallback not allowed: {e}")
    
    # No real data source and no input path
    if allow_synthetic or pipeline_validation:
        logger.warning("No real data source found. Generating synthetic data for validation.")
        from generate_synthetic_data import main as gen_main
        gen_main()
        input_path = 'data/raw/synthetic_test_data.csv'
        if os.path.exists(input_path):
            df = pd.read_csv(input_path)
            return df
    
    raise RealDataFetchError("No data source available and synthetic fallback not permitted")

def main():
    """Main entry point for ingestion script."""
    parser = argparse.ArgumentParser(description='Data Ingestion and Validation')
    parser.add_argument('--input', type=str, help='Input CSV file path')
    parser.add_argument('--config', type=str, default='data/config/required_variables.yaml', help='Config file path')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--results-dir', type=str, default='data/results', help='Results directory')
    parser.add_argument('--allow-synthetic-fallback', action='store_true', help='Allow synthetic data fallback')
    parser.add_argument('--pipeline-validation-mode', action='store_true', help='Enable pipeline validation mode')
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_data(
            input_path=args.input,
            allow_synthetic=args.allow_synthetic_fallback,
            pipeline_validation=args.pipeline_validation_mode
        )
        
        # Load required variables
        required = load_required_variables(args.config)
        
        # Validate variables
        is_valid, metrics = validate_variables(df, required)
        
        # Save variable load metrics
        metrics_path = Path(args.results_dir) / 'variable_load_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Saved variable load metrics to {metrics_path}")
        
        # Detect outliers
        outlier_df = detect_outliers_iqr(df)
        save_outlier_report(outlier_df, Path(args.results_dir) / 'outlier_report.json')
        
        # Filter outliers
        filtered_df = filter_outliers(df, outlier_df)
        save_filtered_data(filtered_df, Path(args.output_dir) / 'filtered_data.parquet')
        
        # Record checksum
        record_artifact_checksum(str(Path(args.output_dir) / 'filtered_data.parquet'))
        
        logger.info("Ingestion and validation completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
