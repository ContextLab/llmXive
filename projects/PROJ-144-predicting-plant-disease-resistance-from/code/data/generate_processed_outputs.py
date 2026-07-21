import os
import sys
import glob
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.preprocess import preprocess_metabolomics
from code.data.harmonize_labels import harmonize_labels
from code.utils.io import log_preprocessing_step, compute_file_hash
from code.utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR, PROJECT_ROOT

def load_preprocessed_data(raw_dir: Optional[Path] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and preprocess all raw metabolomics data.
    
    Returns:
        tuple: (feature_matrix, metadata)
    """
    if raw_dir is None:
        raw_dir = PROJECT_ROOT / DATA_RAW_DIR
        
    # Find all raw data files (assuming CSV format as per typical pipeline)
    csv_files = glob.glob(str(raw_dir / "*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(
            f"No raw data files found in {raw_dir}. "
            "Please run download.py first to populate data/raw/."
        )
    
    # Load and concatenate all raw data
    all_data = []
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            df['source_file'] = os.path.basename(file_path)
            all_data.append(df)
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No valid data files could be loaded.")
        
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Apply preprocessing pipeline
    feature_matrix, metadata = preprocess_metabolomics(combined_df)
    
    return feature_matrix, metadata

def load_labels(metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and harmonize resistance labels from metadata.
    
    Args:
        metadata: DataFrame containing sample metadata
        
    Returns:
        DataFrame with harmonized labels
    """
    if metadata is None or metadata.empty:
        raise ValueError("Metadata is required to load labels.")
        
    labels_df = harmonize_labels(metadata)
    return labels_df

def apply_batch_correction(feature_matrix: pd.DataFrame, 
                           metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ComBat batch effect correction if multiple batches exist.
    
    Args:
        feature_matrix: Normalized feature matrix
        metadata: Metadata containing batch information
        
    Returns:
        Batch-corrected feature matrix
    """
    # Check if we have batch information
    batch_col = 'batch'
    if batch_col not in metadata.columns:
        # Try to infer batch from source file or study ID
        if 'source_file' in metadata.columns:
            metadata['batch'] = metadata['source_file'].str.replace('.csv', '')
            batch_col = 'batch'
        elif 'study_id' in metadata.columns:
            metadata['batch'] = metadata['study_id']
            batch_col = 'batch'
        else:
            print("Warning: No batch information found. Skipping batch correction.")
            return feature_matrix
    
    # Check if we have multiple batches
    unique_batches = metadata[batch_col].nunique()
    if unique_batches < 2:
        print(f"Only {unique_batches} batch found. Skipping batch correction.")
        return feature_matrix
    
    # Import pycombat if available, otherwise use simple mean-centering
    try:
        from pycombat import PyCombat
        print(f"Applying ComBat correction with {unique_batches} batches...")
        
        # Prepare data for PyCombat
        # PyCombat expects: data (genes x samples), model (batch info), covariates (optional)
        feature_matrix_transposed = feature_matrix.T  # samples x features -> features x samples
        
        combat = PyCombat()
        corrected_data = combat.fit_transform(
            feature_matrix_transposed.values,
            metadata[batch_col].values,
            None  # No covariates for now
        )
        
        # Convert back to DataFrame
        corrected_df = pd.DataFrame(
            corrected_data.T,  # Back to samples x features
            columns=feature_matrix.columns,
            index=feature_matrix.index
        )
        
        print("Batch correction completed successfully.")
        return corrected_df
        
    except ImportError:
        print("Warning: PyCombat not installed. Using simple mean-centering as fallback.")
        # Simple mean-centering per batch
        corrected_data = feature_matrix.copy()
        for batch in metadata[batch_col].unique():
            batch_mask = metadata[batch_col] == batch
            batch_mean = feature_matrix.loc[batch_mask].mean()
            corrected_data.loc[batch_mask] = feature_matrix.loc[batch_mask] - batch_mean + feature_matrix.mean()
        
        print("Simple batch correction completed.")
        return corrected_data

def main():
    """
    Main function to generate processed outputs.
    """
    print("Starting processed data generation...")
    
    # Ensure output directory exists
    output_dir = PROJECT_ROOT / DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and preprocess data
    print("Loading and preprocessing raw data...")
    try:
        feature_matrix, metadata = load_preprocessed_data()
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(feature_matrix)} samples with {len(feature_matrix.columns)} features")
    
    # Load and harmonize labels
    print("Harmonizing labels...")
    try:
        labels_df = load_labels(metadata)
    except Exception as e:
        print(f"Error loading labels: {e}")
        sys.exit(1)
    
    # Apply batch correction
    print("Applying batch correction...")
    try:
        corrected_matrix = apply_batch_correction(feature_matrix, metadata)
    except Exception as e:
        print(f"Error applying batch correction: {e}")
        # Continue without batch correction if it fails
        corrected_matrix = feature_matrix
    
    # Save outputs
    output_matrix_path = output_dir / "batch_corrected_matrix.csv"
    output_labels_path = output_dir / "labels.csv"
    
    print(f"Saving batch corrected matrix to {output_matrix_path}")
    corrected_matrix.to_csv(output_matrix_path, index=False)
    
    print(f"Saving labels to {output_labels_path}")
    labels_df.to_csv(output_labels_path, index=False)
    
    # Log artifacts
    matrix_hash = compute_file_hash(output_matrix_path)
    labels_hash = compute_file_hash(output_labels_path)
    
    log_preprocessing_step(
        step="batch_correction",
        input_files=[str(output_matrix_path), str(output_labels_path)],
        output_files=[str(output_matrix_path), str(output_labels_path)],
        details={
            "num_samples": len(corrected_matrix),
            "num_features": len(corrected_matrix.columns),
            "matrix_hash": matrix_hash,
            "labels_hash": labels_hash
        }
    )
    
    print("Processed data generation completed successfully.")
    print(f"Output files:")
    print(f"  - {output_matrix_path}")
    print(f"  - {output_labels_path}")

if __name__ == "__main__":
    main()