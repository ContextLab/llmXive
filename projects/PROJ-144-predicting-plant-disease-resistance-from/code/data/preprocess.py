import os
import sys
import glob
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import from existing project API surface
from utils.constants import DATA_PROCESSED_DIR, DATA_RAW_DIR
from utils.io import log_preprocessing_step, compute_file_hash
from utils.exceptions import DataUnavailableError

# Try to import sklearn-combat, but handle gracefully if not installed
# The task requires ComBat only if study count >= 2
try:
    from skcombat import Combat
    HAS_COMBAT = True
except ImportError:
    HAS_COMBAT = False
    log_preprocessing_step("WARNING", "sklearn-combat not installed. Batch correction will be skipped if multiple studies detected.")

def log_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies log2 transform to all numeric columns.
    Handles zeros and negative values by adding a small offset.
    """
    df_log = df.copy()
    numeric_cols = df_log.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        # Add small offset to handle zeros and negatives
        min_val = df_log[col].min()
        if min_val <= 0:
            offset = abs(min_val) + 1e-8
        else:
            offset = 0
        df_log[col] = np.log2(df_log[col] + offset)
    
    return df_log

def filter_missing_features(df: pd.DataFrame, threshold: float = 0.3) -> pd.DataFrame:
    """
    Filters out features (columns) missing more than `threshold` fraction of values.
    Returns the filtered DataFrame.
    """
    if df.empty:
        return df
    
    # Calculate missing ratio per column
    missing_ratio = df.isna().mean()
    # Keep columns where missing ratio <= threshold
    keep_cols = missing_ratio[missing_ratio <= threshold].index
    
    filtered_df = df[keep_cols]
    
    dropped_cols = missing_ratio[missing_ratio > threshold].index.tolist()
    if dropped_cols:
        log_preprocessing_step("INFO", f"Dropped {len(dropped_cols)} features with >{threshold*100}% missing values: {dropped_cols[:5]}...")
    
    return filtered_df

def align_metabolites_by_inchikey(dfs: List[pd.DataFrame], study_ids: List[str]) -> pd.DataFrame:
    """
    Aligns metabolites across studies by InChIKey.
    Assumes each study's intensity CSV has an 'InChIKey' column or similar identifier.
    Returns a concatenated DataFrame with aligned metabolites (intersection).
    """
    if not dfs:
        raise ValueError("No DataFrames provided for alignment")
    
    # Ensure each DataFrame has InChIKey column
    processed_dfs = []
    valid_study_ids = []
    
    for i, df in enumerate(dfs):
        # Try to find InChIKey column
        inchikey_col = None
        for col_name in ['InChIKey', 'inchikey', 'InChI_Key', 'inchi_key']:
            if col_name in df.columns:
                inchikey_col = col_name
                break
        
        if inchikey_col is None:
            # If no InChIKey found, try to use first column as identifier if it looks like keys
            first_col = df.columns[0]
            if df[first_col].dtype == object and len(df[first_col].unique()) > 0:
                inchikey_col = first_col
                log_preprocessing_step("WARNING", f"Study {study_ids[i]}: Using '{first_col}' as InChIKey column")
            else:
                raise ValueError(f"Study {study_ids[i]}: No InChIKey column found")
        
        # Ensure InChIKey column is string and strip whitespace
        df_processed = df.copy()
        df_processed[inchikey_col] = df_processed[inchikey_col].astype(str).str.strip()
        processed_dfs.append(df_processed)
        valid_study_ids.append(study_ids[i])
    
    # Find intersection of InChIKeys across all studies
    all_inchikeys = [set(df[inchikey_col].unique()) for df in processed_dfs]
    common_inchikeys = set.intersection(*all_inchikeys)
    
    if len(common_inchikeys) < 10:
        log_preprocessing_step("WARNING", f"Alignment intersection is small: {len(common_inchikeys)} metabolites. Proceeding anyway.")
    
    # Log missing metabolites
    missing_log = {}
    for i, df in enumerate(processed_dfs):
        study_id = valid_study_ids[i]
        missing = all_inchikeys[i] - common_inchikeys
        if missing:
            missing_log[study_id] = list(missing)[:10]  # Log first 10 as sample
    
    if missing_log:
        log_path = Path(DATA_PROCESSED_DIR) / "alignment_missing.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            json.dump(missing_log, f, indent=2)
        log_preprocessing_step("INFO", f"Logged missing metabolites to {log_path}")
    
    # Filter each DataFrame to common InChIKeys and concatenate
    aligned_dfs = []
    for i, df in enumerate(processed_dfs):
        study_id = valid_study_ids[i]
        df_filtered = df[df[inchikey_col].isin(common_inchikeys)].copy()
        
        # Set InChIKey as index for easier concatenation
        df_filtered.set_index(inchikey_col, inplace=True)
        
        # Add study identifier column
        df_filtered['study_id'] = study_id
        
        aligned_dfs.append(df_filtered)
    
    # Concatenate all aligned DataFrames
    aligned_df = pd.concat(aligned_dfs, axis=0)
    
    # Reset index to make InChIKey a column again
    aligned_df.reset_index(inplace=True)
    
    log_preprocessing_step("INFO", f"Aligned {len(common_inchikeys)} metabolites across {len(dfs)} studies")
    
    return aligned_df

def apply_combat(df: pd.DataFrame, batch_col: str) -> pd.DataFrame:
    """
    Applies ComBat batch correction if sklearn-combat is available and multiple batches exist.
    Returns the corrected DataFrame.
    """
    if not HAS_COMBAT:
        log_preprocessing_step("WARNING", "sklearn-combat not available. Skipping batch correction.")
        return df
    
    # Check if there are multiple batches
    unique_batches = df[batch_col].unique()
    if len(unique_batches) < 2:
        log_preprocessing_step("WARNING", f"Only one batch detected ({unique_batches[0]}). Skipping ComBat.")
        return df
    
    # Prepare data for ComBat
    # ComBat expects: data (features x samples), batch (1D array), mod (optional model matrix)
    # Our df has InChIKey as first column, then metabolite intensities, then study_id
    
    # Identify numeric columns (metabolite intensities)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove batch_col from numeric_cols if present
    if batch_col in numeric_cols:
        numeric_cols.remove(batch_col)
    
    if not numeric_cols:
        log_preprocessing_step("WARNING", "No numeric columns found for batch correction.")
        return df
    
    # Prepare data matrix (metabolites x samples)
    data_matrix = df[numeric_cols].values.T  # Transpose to (features x samples)
    batch_labels = df[batch_col].values
    
    # Create design matrix (intercept only)
    import numpy as np
    design = np.ones((len(batch_labels), 1))
    
    try:
        combat = Combat()
        corrected_data = combat.fit_transform(data_matrix, batch_labels, design)
        
        # Replace original data with corrected data
        df_corrected = df.copy()
        for i, col in enumerate(numeric_cols):
            df_corrected[col] = corrected_data[i, :]
        
        log_preprocessing_step("INFO", f"Applied ComBat batch correction across {len(unique_batches)} batches")
        return df_corrected
        
    except Exception as e:
        log_preprocessing_step("ERROR", f"ComBat correction failed: {str(e)}")
        return df

def residualize_confounders(df: pd.DataFrame, confounders: List[str]) -> pd.DataFrame:
    """
    Residualizes numeric columns against confounders using linear regression.
    Returns the residualized DataFrame.
    """
    if not confounders:
        return df
    
    # Check if confounders exist in DataFrame
    available_confounders = [c for c in confounders if c in df.columns]
    if not available_confounders:
        log_preprocessing_step("WARNING", f"No confounders found in DataFrame: {confounders}")
        return df
    
    # Identify numeric columns to residualize
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove confounder columns from numeric_cols
    for conf in available_confounders:
        if conf in numeric_cols:
            numeric_cols.remove(conf)
    
    if not numeric_cols:
        return df
    
    # Prepare data
    from sklearn.linear_model import LinearRegression
    
    df_residualized = df.copy()
    
    for col in numeric_cols:
        X = df[available_confounders].values
        y = df[col].values
        
        # Handle missing values
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X_clean = X[mask]
        y_clean = y[mask]
        
        if len(X_clean) < len(available_confounders) + 1:
            continue
        
        model = LinearRegression()
        model.fit(X_clean, y_clean)
        
        # Predict and subtract to get residuals
        predictions = model.predict(X)
        residuals = y - predictions
        
        df_residualized.loc[mask, col] = residuals
        # Keep NaN for rows with missing data
        df_residualized.loc[~mask, col] = np.nan
    
    log_preprocessing_step("INFO", f"Residualized {len(numeric_cols)} features against {len(available_confounders)} confounders")
    return df_residualized

def preprocess_metabolomics(study_ids: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Main preprocessing function that orchestrates the pipeline:
    1. Load raw intensity and phenotype files
    2. Log transform intensities
    3. Filter missing features (>30% missing)
    4. Align metabolites by InChIKey
    5. Apply ComBat batch correction if study count >= 2
    6. Merge with harmonized labels
    7. Save outputs
    
    Returns a dictionary of output file paths.
    """
    log_preprocessing_step("INFO", "Starting metabolomics preprocessing pipeline")
    
    # Determine study IDs if not provided
    if study_ids is None:
        # Load from manifest
        manifest_path = Path(DATA_RAW_DIR) / "study_manifest.json"
        if not manifest_path.exists():
            raise DataUnavailableError(f"Study manifest not found at {manifest_path}. Run T012a first.")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        study_ids = [study['study_id'] for study in manifest]
    
    if not study_ids:
        raise DataUnavailableError("No study IDs provided or found in manifest")
    
    # Load raw intensity files
    intensity_dfs = []
    for study_id in study_ids:
        intensity_file = Path(DATA_RAW_DIR) / f"{study_id}_raw_intensity.csv"
        if not intensity_file.exists():
            raise DataUnavailableError(f"Intensity file not found: {intensity_file}. Run T012b first.")
        
        df = pd.read_csv(intensity_file)
        intensity_dfs.append(df)
        log_preprocessing_step("INFO", f"Loaded intensity data for {study_id}: {df.shape}")
    
    # Load harmonized labels
    labels_file = Path(DATA_PROCESSED_DIR) / "harmonized_labels.csv"
    if not labels_file.exists():
        raise DataUnavailableError(f"Harmonized labels not found: {labels_file}. Run T014b first.")
    
    labels_df = pd.read_csv(labels_file)
    log_preprocessing_step("INFO", f"Loaded harmonized labels: {labels_df.shape}")
    
    # Step 1: Log transform all intensity DataFrames
    log_transformed_dfs = [log_transform(df) for df in intensity_dfs]
    log_preprocessing_step("INFO", "Applied log transformation to all intensity matrices")
    
    # Step 2: Filter missing features (>30% missing)
    filtered_dfs = [filter_missing_features(df, threshold=0.3) for df in log_transformed_dfs]
    log_preprocessing_step("INFO", "Filtered features with >30% missing values")
    
    # Step 3: Align metabolites by InChIKey
    aligned_df = align_metabolites_by_inchikey(filtered_dfs, study_ids)
    
    # Step 4: Apply ComBat batch correction if study count >= 2
    batch_corrected_df = aligned_df.copy()
    batch_correction_applied = False
    
    if len(study_ids) >= 2:
        if HAS_COMBAT:
            # Use study_id as batch column
            batch_corrected_df = apply_combat(aligned_df, 'study_id')
            batch_correction_applied = True
            log_preprocessing_step("INFO", "ComBat batch correction applied")
        else:
            log_preprocessing_step("WARNING", "sklearn-combat not installed. Skipping batch correction despite multiple studies.")
    else:
        log_preprocessing_step("WARNING", f"Only {len(study_ids)} study detected. Skipping batch correction.")
    
    # Step 5: Merge with harmonized labels
    # Assuming labels_df has a 'sample_id' or similar column that matches rows in batch_corrected_df
    # We need to determine the join key
    join_key = None
    for key_candidate in ['sample_id', 'SampleID', 'sample', 'id']:
        if key_candidate in labels_df.columns and key_candidate in batch_corrected_df.columns:
            join_key = key_candidate
            break
    
    if join_key is None:
        # If no common column, try to merge on index
        log_preprocessing_step("WARNING", "No common column found for merging. Attempting index-based merge.")
        merged_df = pd.merge(batch_corrected_df.reset_index(drop=True), 
                             labels_df.reset_index(drop=True), 
                             left_index=True, right_index=True)
    else:
        merged_df = pd.merge(batch_corrected_df, labels_df, on=join_key, how='inner')
    
    if merged_df.empty:
        raise ValueError("Merge with labels resulted in empty DataFrame. Check join keys.")
    
    log_preprocessing_step("INFO", f"Merged with labels: {merged_df.shape}")
    
    # Step 6: Save outputs
    output_dir = Path(DATA_PROCESSED_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save batch corrected matrix
    matrix_file = output_dir / "batch_corrected_matrix.csv"
    # Exclude study_id and join_key from the matrix if they're in the data
      # Keep only numeric columns for the matrix
    matrix_cols = [col for col in merged_df.columns if merged_df[col].dtype in [np.number, 'float64', 'int64']]
    matrix_df = merged_df[matrix_cols]
    matrix_df.to_csv(matrix_file, index=False)
    matrix_hash = compute_file_hash(matrix_file)
    log_preprocessing_step("INFO", f"Saved batch corrected matrix: {matrix_file} (hash: {matrix_hash})")
    
    # Save labels
    labels_output_file = output_dir / "labels.csv"
    # Select label-related columns
    label_cols = [col for col in merged_df.columns if 'label' in col.lower() or 'resistance' in col.lower() or 'phenotype' in col.lower()]
    if not label_cols:
        label_cols = [col for col in merged_df.columns if col in labels_df.columns]
    
    labels_output_df = merged_df[label_cols]
    labels_output_df.to_csv(labels_output_file, index=False)
    labels_hash = compute_file_hash(labels_output_file)
    log_preprocessing_step("INFO", f"Saved harmonized labels: {labels_output_file} (hash: {labels_hash})")
    
    # Save preprocessing log
    log_entry = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "study_count": len(study_ids),
        "studies": study_ids,
        "log_transform_applied": True,
        "missing_filter_threshold": 0.3,
        "features_before_filter": sum(df.shape[1] for df in log_transformed_dfs),
        "features_after_filter": merged_df.shape[1],
        "alignment_metabolites": len(aligned_df['InChIKey'].unique()) if 'InChIKey' in aligned_df.columns else 0,
        "batch_correction_applied": batch_correction_applied,
        "batch_correction_method": "ComBat" if batch_correction_applied else "None",
        "output_files": {
            "matrix": str(matrix_file),
            "labels": str(labels_output_file)
        },
        "checksums": {
            "matrix": matrix_hash,
            "labels": labels_hash
        }
    }
    
    log_file = output_dir / "preprocess_log.json"
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    log_preprocessing_step("INFO", f"Preprocessing complete. Log saved to {log_file}")
    
    return {
        "matrix": str(matrix_file),
        "labels": str(labels_output_file),
        "log": str(log_file)
    }

def main():
    """
    Entry point for command-line execution.
    Usage: python code/data/preprocess.py --study_ids path/to/manifest.json --output path/to/output/
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess metabolomics data")
    parser.add_argument("--study_ids", type=str, help="Path to study manifest JSON")
    parser.add_argument("--output", type=str, default=DATA_PROCESSED_DIR, help="Output directory")
    
    args = parser.parse_args()
    
    try:
        # Load study IDs from manifest if provided
        study_ids = None
        if args.study_ids and os.path.exists(args.study_ids):
            with open(args.study_ids, 'r') as f:
                manifest = json.load(f)
            study_ids = [study['study_id'] for study in manifest]
        
        # Run preprocessing
        output_files = preprocess_metabolomics(study_ids=study_ids)
        
        print("Preprocessing completed successfully!")
        print(f"Output files:")
        for key, path in output_files.items():
            print(f"  {key}: {path}")
        
        sys.exit(0)
        
    except DataUnavailableError as e:
        print(f"Data unavailable: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during preprocessing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()