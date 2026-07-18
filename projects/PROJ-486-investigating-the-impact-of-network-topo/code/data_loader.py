import os
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from config import RANDOM_SEED

def validate_entrainment_csv(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validates the entrainment CSV for required columns and numeric types.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_cols = ['subject_id', 'entrainment_metric']
    
    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}"
    
    # Check subject_id is string or object
    if not df['subject_id'].dtype in ['object', 'string']:
        return False, "subject_id must be string type"
    
    # Check entrainment_metric is numeric
    if not pd.api.types.is_numeric_dtype(df['entrainment_metric']):
        try:
            df['entrainment_metric'] = pd.to_numeric(df['entrainment_metric'], errors='raise')
        except (ValueError, TypeError):
            return False, "entrainment_metric must be numeric"
    
    # Check for NaN values in required columns
    if df['subject_id'].isna().any():
        return False, "subject_id contains NaN values"
    if df['entrainment_metric'].isna().any():
        return False, "entrainment_metric contains NaN values"
    
    return True, "Validation passed"

def validate_topology_columns(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validates the topology metrics CSV for required columns.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_cols = ['subject_id', 'clustering_coefficient', 'path_length']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"Missing required topology columns: {missing_cols}"
    
    # Check numeric types
    for col in ['clustering_coefficient', 'path_length']:
        if not pd.api.types.is_numeric_dtype(df[col]):
            return False, f"{col} must be numeric"
        
    # Check for NaN
    for col in required_cols:
        if df[col].isna().any():
            return False, f"{col} contains NaN values"
    
    return True, "Topology validation passed"

def load_entrainment_csv(filepath: str = "data/raw/entrainment_metrics.csv") -> Dict[str, Any]:
    """
    Attempts to load the entrainment metrics CSV file.
    
    Logic:
    - If file exists: validate columns and numeric types, return loaded data
    - If file missing: return status object with exists=false and reason="missing"
    - Does NOT raise an exception on missing file; allows fallback trigger
    
    Args:
        filepath: Path to the entrainment metrics CSV file
        
    Returns:
        Dictionary with structure:
        - If successful: {"exists": True, "data": DataFrame, "status": "valid"}
        - If missing: {"exists": False, "reason": "missing"}
        - If invalid: {"exists": True, "status": "invalid", "error": error_message}
    """
    if not os.path.exists(filepath):
        return {"exists": False, "reason": "missing"}
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return {"exists": True, "status": "invalid", "error": f"Failed to read CSV: {str(e)}"}
    
    is_valid, error_msg = validate_entrainment_csv(df)
    
    if not is_valid:
        return {"exists": True, "status": "invalid", "error": error_msg}
    
    return {"exists": True, "data": df, "status": "valid"}

def generate_simulated_raw_matrices(n_subjects: int = 50, n_regions: int = 200) -> pd.DataFrame:
    """
    Generates deterministic simulated raw correlation matrices for the Schaefer atlas.
    This satisfies FR-001 given the "Dataset Availability" assumption.
    
    Args:
        n_subjects: Number of subjects to simulate
        n_regions: Number of regions in the parcellation (default 200 for Schaefer)
        
    Returns:
        DataFrame with columns: subject_id, matrix_data (flattened upper triangle)
    """
    np.random.seed(RANDOM_SEED)
    
    records = []
    upper_tri_indices = np.triu_indices(n_regions, k=1)
    n_elements = len(upper_tri_indices[0])
    
    for i in range(n_subjects):
        subject_id = f"sub_{i:03d}"
        
        # Generate a random correlation matrix
        # Create random data with some structure
        X = np.random.randn(n_regions, 50)  # 50 timepoints
        # Add some correlation structure
        X[:, 0] += np.random.randn() * 0.5  # Global signal component
        corr_matrix = np.corrcoef(X)
        
        # Ensure symmetry and diagonal
        corr_matrix = (corr_matrix + corr_matrix.T) / 2
        np.fill_diagonal(corr_matrix, 1.0)
        
        # Extract upper triangle
        upper_tri_values = corr_matrix[upper_tri_indices].tolist()
        
        records.append({
            "subject_id": subject_id,
            "matrix_data": upper_tri_values
        })
    
    return pd.DataFrame(records)

def main():
    """
    Main entry point for data_loader module.
    Demonstrates the load_entrainment_csv function behavior.
    """
    print("Testing load_entrainment_csv...")
    
    # Test with missing file
    result = load_entrainment_csv("data/raw/entrainment_metrics.csv")
    print(f"Missing file test: {result}")
    
    # Create a sample valid file for testing if needed
    if not os.path.exists("data/raw"):
        os.makedirs("data/raw", exist_ok=True)
    
    sample_df = pd.DataFrame({
        'subject_id': ['sub_001', 'sub_002', 'sub_003'],
        'entrainment_metric': [0.75, 0.82, 0.68]
    })
    sample_path = "data/raw/entrainment_metrics.csv"
    sample_df.to_csv(sample_path, index=False)
    
    result = load_entrainment_csv(sample_path)
    print(f"Valid file test: exists={result.get('exists')}, status={result.get('status')}")
    
    if result.get('exists'):
        print(f"Data shape: {result['data'].shape}")
        print(result['data'].head())

if __name__ == "__main__":
    main()