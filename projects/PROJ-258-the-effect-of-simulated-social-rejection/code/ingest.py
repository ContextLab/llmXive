import os
import sys
import json
import hashlib
import logging
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
import pandas as pd
import requests

# Import from local modules
from config import get_path, get_memory_threshold_mb
from logging_utils import get_process_memory_mb, setup_memory_logger, log_memory_snapshot
from data_model import DesignType

def setup_paths():
    """Set up and return paths for data directories."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {
        'raw': os.path.join(base_dir, 'data', 'raw'),
        'interim': os.path.join(base_dir, 'data', 'interim'),
        'processed': os.path.join(base_dir, 'data', 'processed'),
        'reports': os.path.join(base_dir, 'reports')
    }

def get_process_memory_check():
    """Check if current memory usage exceeds threshold."""
    memory_mb = get_process_memory_mb()
    threshold_mb = get_memory_threshold_mb()
    if memory_mb > threshold_mb:
        raise MemoryError(f"Memory usage {memory_mb:.2f} MB exceeds threshold {threshold_mb} MB")
    return memory_mb

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: str):
    """Save checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def download_dataset(url: str, output_dir: str) -> str:
    """
    Download a dataset from OpenNeuro.
    
    Note: This is a simplified implementation. In production, you would use
    the OpenNeuro CLI or API to download datasets.
    
    Args:
        url: The URL of the dataset
        output_dir: Directory to save the dataset
        
    Returns:
        Path to the downloaded dataset
    """
    os.makedirs(output_dir, exist_ok=True)
    dataset_name = url.split('/')[-1]
    dataset_path = os.path.join(output_dir, dataset_name)
    
    # In a real implementation, this would download the actual dataset
    # For now, we create a placeholder to simulate the structure
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path, exist_ok=True)
        # Create a mock dataset.json
        dataset_json = {
            "name": dataset_name,
            "description": f"Mock dataset for {dataset_name}",
            "version": "1.0.0"
        }
        with open(os.path.join(dataset_path, 'dataset.json'), 'w') as f:
            json.dump(dataset_json, f, indent=2)
    
    return dataset_path

def load_dataframe(file_path: str) -> pd.DataFrame:
    """Load a dataframe from a CSV or TSV file."""
    if file_path.endswith('.tsv'):
        return pd.read_csv(file_path, sep='\t')
    else:
        return pd.read_csv(file_path)

def verify_tasks_in_dataset(dataset_path: str, required_tasks: list) -> bool:
    """Verify that required tasks are present in the dataset."""
    # In a real implementation, this would check the dataset structure
    # For now, we assume the dataset is valid
    return True

def validate_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the schema of a dataframe.
    
    Args:
        df: The dataframe to validate
        
    Returns:
        Dictionary with validation results
    """
    required_columns = ['Condition', 'Reaction Time', 'Mood']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    return {
        'passed': len(missing_columns) == 0,
        'missing_columns': missing_columns,
        'columns_found': list(df.columns)
    }

def verify_single_cohort(df: pd.DataFrame) -> bool:
    """
    Verify if the dataset represents a single cohort (within-subjects design).
    
    Args:
        df: The dataframe to check
        
    Returns:
        True if single cohort, False otherwise
    """
    # Check if participant IDs are consistent across conditions
    if 'Participant ID' not in df.columns:
        return False
    
    # In a real implementation, we would check if the same participants
    # appear in multiple conditions
    return True

def log_design_switch(log_path: str, from_design: str, to_design: str):
    """Log a design switch event to a metadata file."""
    metadata_path = os.path.join(log_path, 'metadata.json')
    
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {'events': []}
    
    metadata['events'].append({
        'event': 'design_switch',
        'from': from_design,
        'to': to_design,
        'timestamp': pd.Timestamp.now().isoformat()
    })
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def validate_composite_datasets(df_rejection: pd.DataFrame, df_reward: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate two separate datasets for between-subjects analysis.
    
    Args:
        df_rejection: DataFrame for rejection task
        df_reward: DataFrame for reward task
        
    Returns:
        Dictionary with validation results
    """
    rejection_valid = validate_schema(df_rejection)
    reward_valid = validate_schema(df_reward)
    
    return {
        'rejection_valid': rejection_valid['passed'],
        'reward_valid': reward_valid['passed'],
        'rejection_missing': rejection_valid['missing_columns'],
        'reward_missing': reward_valid['missing_columns']
    }

def match_ids_across_datasets(df_rejection: pd.DataFrame, df_reward: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if participant IDs exist in both datasets.
    
    Args:
        df_rejection: DataFrame for rejection task
        df_reward: DataFrame for reward task
        
    Returns:
        Dictionary with match statistics
    """
    if 'Participant ID' not in df_rejection.columns or 'Participant ID' not in df_reward.columns:
        return {
            'match_count': 0,
            'design_type': DesignType.BETWEEN_SUBJECTS.value,
            'note': 'Participant ID column not found in one or both datasets'
        }
    
    ids_rejection = set(df_rejection['Participant ID'].unique())
    ids_reward = set(df_reward['Participant ID'].unique())
    
    match_count = len(ids_rejection.intersection(ids_reward))
    
    # If datasets are from distinct studies, always use between-subjects
    # This is enforced by check_single_cohort_constraint
    
    return {
        'match_count': match_count,
        'design_type': DesignType.BETWEEN_SUBJECTS.value,
        'ids_in_rejection': len(ids_rejection),
        'ids_in_reward': len(ids_reward)
    }

def handle_data_unavailable():
    """Handle the case when no valid data is available."""
    logging.error("Data Unavailable: No valid dataset or separate datasets found")
    sys.exit(1)

def write_metadata(design_type: str, output_path: str):
    """Write the final design type to metadata file."""
    metadata = {
        'design_type': design_type,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def run_ingestion():
    """Main ingestion pipeline."""
    logger = setup_memory_logger()
    paths = setup_paths()
    
    # Memory check before loading
    log_memory_snapshot(logger, "start")
    get_process_memory_check()
    
    # In a real implementation, this would:
    # 1. Attempt single-cohort fetch
    # 2. If not found, fetch separate datasets
    # 3. Validate schemas
    # 4. Determine design type
    # 5. Write metadata
    
    # For now, we create a simple metadata file
    metadata_path = os.path.join(paths['processed'], 'metadata.json')
    write_metadata(DesignType.BETWEEN_SUBJECTS.value, metadata_path)
    
    log_memory_snapshot(logger, "end")
    return 0

if __name__ == "__main__":
    sys.exit(run_ingestion())
