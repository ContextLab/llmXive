import os
import glob
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import warnings
import sys
from pathlib import Path

# Add project root to path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.constants import DATA_PROCESSED_DIR, DATA_RAW_DIR

# Try to import optional dependencies, fallback gracefully
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LinearRegression
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    warnings.warn("scikit-learn not installed. Covariate residualization and scaling disabled.")

try:
    import pycombat
    HAS_PYCOMBAT = True
except ImportError:
    try:
        import pycombat as pycombat
        HAS_PYCOMBAT = True
    except ImportError:
        HAS_PYCOMBAT = False
        warnings.warn("pycombat not installed. Batch correction (ComBat) disabled. Install via: pip install pycombat")

def _log_message(msg: str):
    """Simple logging helper."""
    print(f"[PREPROCESS] {msg}")

def _load_raw_data() -> List[Dict[str, Any]]:
    """
    Loads harmonized data from data/processed.
    Expects files produced by harmonize_labels.py (e.g., harmonized_study_*.csv).
    Returns a list of dicts: {'study_id': str, 'df': DataFrame, 'path': str}
    """
    pattern = os.path.join(DATA_PROCESSED_DIR, "harmonized_study_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        # Fallback: try to find any csv in processed if harmonized files don't exist yet
        # but strictly, we expect harmonized output.
        _log_message(f"WARNING: No files matching {pattern} found.")
        return []

    data_batches = []
    for f_path in files:
        try:
            df = pd.read_csv(f_path)
            # Extract study ID from filename if possible, otherwise use generic
            study_id = os.path.splitext(os.path.basename(f_path))[0].replace("harmonized_study_", "")
            data_batches.append({
                "study_id": study_id,
                "df": df,
                "path": f_path
            })
            _log_message(f"Loaded study {study_id}: {df.shape}")
        except Exception as e:
            _log_message(f"ERROR loading {f_path}: {e}")
    
    return data_batches

def _log_transform_and_filter(df: pd.DataFrame, threshold: float = 0.30) -> pd.DataFrame:
    """
    1. Log-transforms intensity columns.
    2. Discards features (columns) missing > threshold fraction of values.
    Assumes first column is 'sample_id' or similar, and numeric columns are metabolites.
    """
    _log_message("Applying log-transform and filtering missing values...")
    
    # Identify numeric columns (metabolite intensities)
    # Exclude common ID columns if present
    exclude_cols = ['sample_id', 'subject_id', 'study_id', 'resistance_label', 'resistance_score']
    numeric_cols = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
    
    if not numeric_cols:
        raise ValueError("No numeric metabolite columns found for log-transform.")

    # Log transform (log1p to handle zeros)
    df[numeric_cols] = np.log1p(df[numeric_cols])

    # Calculate missing fraction
    missing_frac = df[numeric_cols].isna().mean()
    cols_to_keep = missing_frac[missing_frac <= threshold].index.tolist()
    
    dropped_count = len(numeric_cols) - len(cols_to_keep)
    _log_message(f"Log-transformed {len(numeric_cols)} features. Dropped {dropped_count} features with >{threshold*100}% missing.")
    
    return df[cols_to_keep + [c for c in df.columns if c not in numeric_cols]]

def _align_metabolites(batches: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aligns metabolites across studies based on column names (InChIKey assumed as column names).
    Performs an outer join on metabolite columns, filling NaNs with 0 or mean? 
    Spec says: "Align metabolites via InChIKey". 
    Strategy: Union of all metabolite columns. 
    """
    _log_message("Aligning metabolites across studies via InChIKey (column names)...")
    
    # Collect all unique metabolite columns (excluding metadata)
    all_met_cols = set()
    exclude_cols = ['sample_id', 'subject_id', 'study_id', 'resistance_label', 'resistance_score']
    
    for batch in batches:
        cols = [c for c in batch['df'].columns if c not in exclude_cols]
        all_met_cols.update(cols)
    
    all_met_cols = sorted(list(all_met_cols))
    _log_message(f"Total unique metabolites across studies: {len(all_met_cols)}")
    
    # Concatenate with reindex to align columns
    # We need to preserve metadata columns too
    meta_cols = ['sample_id', 'study_id', 'resistance_label', 'resistance_score']
    # Filter existing meta cols that actually exist in data
    existing_meta = [c for c in meta_cols if any(c in b['df'].columns for b in batches)]
    
    combined_dfs = []
    for batch in batches:
        df = batch['df']
        # Ensure meta cols exist
        for c in existing_meta:
            if c not in df.columns:
                df[c] = np.nan
        
        # Reindex to ensure all metabolite columns exist (others will be NaN)
        # Only select meta + all_met_cols
        cols_to_select = [c for c in existing_meta if c in df.columns] + all_met_cols
        # Fill missing metabolite cols with NaN initially, then we might impute or leave as NaN
        # But log-transform step usually happens before or after? 
        # Task says: Log-transform -> Discard >30% -> Align -> Residualize -> ComBat
        # If we align now, we introduce NaNs. The 30% filter was per study.
        # We will fill NaNs with 0 later or handle in residualization? 
        # Standard practice: Impute missing with 0 or half-min after alignment, but task doesn't specify.
        # We'll leave as NaN for now, ComBat handles it if configured, or we fill 0.
        # Let's fill with 0 for intensity data if missing entirely in a study (assumed not detected).
        sub_df = df[cols_to_select].copy()
        sub_df[all_met_cols] = sub_df[all_met_cols].fillna(0) 
        combined_dfs.append(sub_df)
    
    result = pd.concat(combined_dfs, ignore_index=True)
    _log_message(f"Combined dataset shape: {result.shape}")
    return result

def _residualize_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs covariate residualization for biological confounders.
    Regresses out confounders (e.g., study_id, batch) from metabolite intensities.
    Uses LinearRegression from sklearn.
    """
    if not HAS_SKLEARN:
        _log_message("Skipping covariate residualization: scikit-learn not available.")
        return df

    _log_message("Performing covariate residualization...")
    
    # Identify confounders
    confounders = ['study_id']
    available_confounders = [c for c in confounders if c in df.columns]
    
    if not available_confounders:
        _log_message("No confounders found to residualize.")
        return df

    # Encode categorical confounders
    df_encoded = df.copy()
    for col in available_confounders:
        if df_encoded[col].dtype == 'object':
            df_encoded[col] = df_encoded[col].astype('category').cat.codes
    
    # Separate features and confounders
    exclude_cols = ['sample_id', 'resistance_label', 'resistance_score'] + available_confounders
    feature_cols = [c for c in df_encoded.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df_encoded[c])]
    
    if not feature_cols:
        return df_encoded

    X_confounders = df_encoded[available_confounders].values
    y_features = df_encoded[feature_cols].values
    
    residuals = np.zeros_like(y_features)
    
    for i, col in enumerate(feature_cols):
        model = LinearRegression()
        model.fit(X_confounders, y_features[:, i])
        # Residual = y - predicted
        residuals[:, i] = y_features[:, i] - model.predict(X_confounders)
    
    # Update dataframe
    df_encoded[feature_cols] = residuals
    _log_message(f"Residualized {len(feature_cols)} metabolites against {available_confounders}.")
    return df_encoded

def _apply_combat(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies ComBat batch-effect correction if >= 2 studies are present.
    Requires 'study_id' as batch column.
    """
    if not HAS_PYCOMBAT:
        _log_message("Skipping ComBat: pycombat not installed.")
        return df

    if 'study_id' not in df.columns:
        _log_message("Skipping ComBat: No 'study_id' column found.")
        return df

    study_counts = df['study_id'].value_counts()
    if len(study_counts) < 2:
        _log_message("Skipping ComBat: Only 1 study present. No batch effect to correct.")
        return df

    _log_message(f"Applying ComBat batch correction across {len(study_counts)} studies...")

    # Prepare data for pycombat
    # pycombat expects: data (genes x samples), batch, mod (optional model matrix)
    # Our df is samples x genes. Need to transpose.
    
    exclude_cols = ['sample_id', 'resistance_label', 'resistance_score']
    feature_cols = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
    
    if not feature_cols:
        return df

    data_matrix = df[feature_cols].values.T  # genes x samples
    batch = df['study_id'].values
    
    # Handle NaNs in data_matrix (ComBat doesn't like them)
    if np.isnan(data_matrix).any():
        # Fill NaNs with 0 or mean? ComBat usually expects complete data.
        # Filling with 0 (assuming missing = not detected)
        data_matrix = np.nan_to_num(data_matrix, nan=0.0)

    try:
        corrected_data = pycombat.Combat(data_matrix, batch)
        # Transpose back to samples x genes
        corrected_data = corrected_data.T
        
        df[feature_cols] = corrected_data
        _log_message("ComBat correction completed successfully.")
    except Exception as e:
        _log_message(f"ERROR in ComBat correction: {e}. Proceeding without correction.")
    
    return df

def preprocess_metabolomics():
    """
    Main entry point for T015.
    1. Load harmonized data.
    2. Log-transform and filter missing > 30%.
    3. Align metabolites.
    4. Residualize covariates.
    5. Apply ComBat.
    6. Save to data/processed/batch_corrected_matrix.csv and labels.csv
    """
    _log_message("Starting preprocessing pipeline (T015)...")
    
    # 1. Load
    batches = _load_raw_data()
    if not batches:
        _log_message("ERROR: No data found to process. Ensure harmonize_labels.py has run.")
        return False

    # 2. Log-transform and filter (per study first? or after merge? 
    # Task says: "Log-transform intensities and discard features missing >30%".
    # Usually done per study before merge to avoid merging sparse data.
    # Let's do per study, then merge.
    processed_batches = []
    for batch in batches:
        df = batch['df']
        # Re-load raw if needed? No, we assume harmonized is the input.
        # But harmonized might not be log transformed yet.
        # We apply log transform and filter here.
        df_clean = _log_transform_and_filter(df, threshold=0.30)
        processed_batches.append({
            "study_id": batch['study_id'],
            "df": df_clean,
            "path": batch['path']
        })

    # 3. Align
    aligned_df = _align_metabolites(processed_batches)
    
    # 4. Residualize
    residualized_df = _residualize_covariates(aligned_df)
    
    # 5. ComBat
    final_df = _apply_combat(residualized_df)
    
    # 6. Save outputs
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # Save matrix
    matrix_path = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    final_df.to_csv(matrix_path, index=False)
    _log_message(f"Saved batch corrected matrix to {matrix_path}")
    
    # Save labels
    label_cols = ['sample_id', 'resistance_label', 'resistance_score']
    available_label_cols = [c for c in label_cols if c in final_df.columns]
    if available_label_cols:
        labels_df = final_df[available_label_cols].copy()
        labels_path = os.path.join(DATA_PROCESSED_DIR, "labels.csv")
        labels_df.to_csv(labels_path, index=False)
        _log_message(f"Saved labels to {labels_path}")
    else:
        _log_message("WARNING: No label columns found to save.")

    _log_message("Preprocessing pipeline completed successfully.")
    return True

if __name__ == "__main__":
    success = preprocess_metabolomics()
    sys.exit(0 if success else 1)
