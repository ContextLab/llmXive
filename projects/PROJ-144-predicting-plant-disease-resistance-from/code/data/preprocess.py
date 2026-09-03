import os
import sys
import glob
import json
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import warnings

# Import constants if available in the project
try:
    from utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR
except ImportError:
    # Fallback to hardcoded paths if constants are not yet available
    DATA_RAW_DIR = "data/raw"
    DATA_PROCESSED_DIR = "data/processed"
    RESULTS_DIR = "results"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom Warning class for alignment issues
class DataAlignmentWarning(UserWarning):
    pass

def log_transform(input_file: str, output_file: str) -> pd.DataFrame:
    """
    Apply log1p transformation to metabolite intensity data.
    """
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Identify numeric columns (metabolites)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    logger.info(f"Applying log1p transformation to {len(numeric_cols)} features")
    df[numeric_cols] = df[numeric_cols].apply(lambda x: np.log1p(x))
    
    df.to_csv(output_file, index=False)
    logger.info(f"Saved log-transformed data to {output_file}")
    return df

def filter_missing_features(input_file: str, output_file: str, threshold: float = 0.3) -> pd.DataFrame:
    """
    Filter out features with missing values > threshold.
    """
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Calculate missing percentage per feature (excluding ID columns if any)
    # Assuming first column is sample ID or similar, rest are metabolites
    # Adjust logic if schema differs
    feature_cols = df.columns[1:] if df.columns[0] == 'sample_id' else df.columns
    
    missing_pct = df[feature_cols].isnull().mean()
    keep_cols = missing_pct[missing_pct <= threshold].index.tolist()
    
    logger.info(f"Kept {len(keep_cols)} features after filtering (threshold: {threshold})")
    
    df_filtered = df[keep_cols] if df.columns[0] == 'sample_id' else df[feature_cols]
    df_filtered.to_csv(output_file, index=False)
    logger.info(f"Saved filtered data to {output_file}")
    return df_filtered

def align_metabolites_by_inchikey(input_file: str, output_file: str, log_file: str = None) -> pd.DataFrame:
    """
    Align metabolites across studies by InChIKey.
    If intersection < 10, log a DataAlignmentWarning but DO NOT halt.
    """
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Assume first column is sample/study identifier, rest are metabolites
    # In a real multi-study scenario, this would involve merging multiple files
    # Here we simulate the alignment logic on a single processed file 
    # that represents the merged state, or we process a list of files if glob matches.
    
    # Check if input is a glob pattern or single file
    if '*' in input_file or '?' in input_file:
        files = glob.glob(input_file)
        if not files:
            raise FileNotFoundError(f"No files matching {input_file}")
        
        # Load and merge multiple studies
        dfs = []
        for f in files:
            logger.info(f"Loading study file: {f}")
            dfs.append(pd.read_csv(f))
        
        # Assume first col is ID, rest are features
        # We need to align on the feature columns (InChIKeys)
        # This is a simplified alignment: find intersection of columns
        if len(dfs) > 1:
            # Get feature columns (exclude first column which is likely sample ID)
            feature_sets = [set(df.columns[1:]) for df in dfs]
            intersection = feature_sets[0]
            for fs in feature_sets[1:]:
                intersection = intersection.intersection(fs)
            
            intersection = list(intersection)
            
            # LOGIC FOR T047: Check intersection size
            if len(intersection) < 10:
                msg = f"Alignment reduced to {len(intersection)} metabolites. Minimum recommended: 10."
                logger.warning(msg)
                warnings.warn(msg, DataAlignmentWarning)
                
                # Log to results/alignment_missing.json
                log_path = Path(RESULTS_DIR) / "alignment_missing.json"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                log_entry = {
                    "warning": "Low metabolite overlap detected",
                    "message": msg,
                    "common_metabolite_count": len(intersection),
                    "threshold": 10,
                    "studies_processed": len(files),
                    "timestamp": pd.Timestamp.now().isoformat()
                }
                
                # Append or create log
                if log_path.exists():
                    with open(log_path, 'r') as f:
                        try:
                            existing_logs = json.load(f)
                        except json.JSONDecodeError:
                            existing_logs = []
                else:
                    existing_logs = []
                
                existing_logs.append(log_entry)
                
                with open(log_path, 'w') as f:
                    json.dump(existing_logs, f, indent=2)
                
                logger.info(f"Logged alignment warning to {log_path}")
            
            # Filter all dfs to intersection
            aligned_dfs = []
            for df in dfs:
                # Keep ID column + intersection
                cols_to_keep = [df.columns[0]] + intersection
                aligned_dfs.append(df[cols_to_keep])
            
            # Concatenate
            final_df = pd.concat(aligned_dfs, ignore_index=True)
        else:
            final_df = dfs[0]
    else:
        # Single file case
        final_df = df

    final_df.to_csv(output_file, index=False)
    logger.info(f"Saved aligned data to {output_file}")
    return final_df

def apply_combat(input_file: str, output_file: str, batch_col: str = 'study_id') -> pd.DataFrame:
    """
    Apply ComBat batch correction.
    Requires a batch column. If missing, skip or raise error based on config.
    """
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    if batch_col not in df.columns:
        logger.warning(f"Batch column '{batch_col}' not found. Skipping ComBat.")
        df.to_csv(output_file, index=False)
        return df

    # Placeholder for actual ComBat implementation using pycombat or sva
    # Since we cannot guarantee external dependencies like pycombat are installed,
    # we implement a robust check or a simple fallback if the library is missing.
    try:
        from pycombat import ComBat
        # Extract batch and data
        batches = df[batch_col]
        data = df.drop(columns=[batch_col])
        
        # Run ComBat
        corrected = ComBat(data=data, batch=batches)
        
        # Reconstruct dataframe
        corrected_df = pd.DataFrame(corrected, columns=data.columns)
        corrected_df.insert(0, batch_col, batches.values)
        
        corrected_df.to_csv(output_file, index=False)
        logger.info(f"Applied ComBat and saved to {output_file}")
        return corrected_df
    except ImportError:
        logger.warning("pycombat not installed. Skipping batch correction.")
        # Fallback: just save as is, but log warning
        df.to_csv(output_file, index=False)
        return df

def residualize_confounders(input_file: str, output_file: str, confounder_cols: List[str]) -> pd.DataFrame:
    """
    Residualize data against confounders.
    """
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Simple linear regression residualization
    from sklearn.linear_model import LinearRegression
    
    feature_cols = [c for c in df.columns if c not in confounder_cols]
    X = df[confounder_cols]
    Y = df[feature_cols]
    
    residuals = pd.DataFrame(index=Y.index, columns=Y.columns)
    
    for col in Y.columns:
        model = LinearRegression()
        model.fit(X, Y[col])
        residuals[col] = Y[col] - model.predict(X)
    
    # Merge back with non-feature columns (if any)
    other_cols = [c for c in df.columns if c not in feature_cols and c not in confounder_cols]
    final_df = pd.concat([df[other_cols], residuals], axis=1)
    
    final_df.to_csv(output_file, index=False)
    logger.info(f"Saved residualized data to {output_file}")
    return final_df

def preprocess_metabolomics(
    input_pattern: str = os.path.join(DATA_RAW_DIR, "*_raw_intensity.csv"),
    output_file: str = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv"),
    log_file: str = os.path.join(DATA_PROCESSED_DIR, "preprocess_log.json")
) -> Dict[str, Any]:
    """
    Orchestrates the full preprocessing pipeline:
    1. Log transform
    2. Filter missing values
    3. Align metabolites (T047 logic here)
    4. Apply ComBat
    
    Updates preprocess_log.json with steps taken.
    """
    log_data = {
        "steps": [],
        "status": "success",
        "warnings": []
    }
    
    try:
        # Step 1: Log Transform
        temp1 = os.path.join(DATA_PROCESSED_DIR, "log_transformed_matrix.csv")
        log_transform(input_pattern, temp1)
        log_data["steps"].append({"step": "log_transform", "output": temp1})
        
        # Step 2: Filter Missing
        temp2 = os.path.join(DATA_PROCESSED_DIR, "filtered_matrix.csv")
        filter_missing_features(temp1, temp2)
        log_data["steps"].append({"step": "filter_missing", "output": temp2})
        
        # Step 3: Align Metabolites (T047)
        temp3 = os.path.join(DATA_PROCESSED_DIR, "aligned_matrix.csv")
        try:
            align_metabolites_by_inchikey(temp2, temp3)
            log_data["steps"].append({"step": "align_metabolites", "output": temp3})
        except DataAlignmentWarning as e:
            log_data["warnings"].append(str(e))
            log_data["steps"].append({"step": "align_metabolites", "status": "warning", "output": temp3})
        
        # Step 4: ComBat
        apply_combat(temp3, output_file)
        log_data["steps"].append({"step": "combat", "output": output_file})
        
    except Exception as e:
        log_data["status"] = "failed"
        log_data["error"] = str(e)
        logger.error(f"Preprocessing failed: {e}")
        raise
    
    # Write log
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return log_data

def main():
    """
    CLI entry point.
    Usage: python code/data/preprocess.py [--input INPUT_PATTERN] [--output OUTPUT_FILE]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess metabolomics data")
    parser.add_argument("--input", type=str, default=os.path.join(DATA_RAW_DIR, "*_raw_intensity.csv"),
                        help="Input file pattern (glob)")
    parser.add_argument("--output", type=str, default=os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv"),
                        help="Output file path")
    parser.add_argument("--log", type=str, default=os.path.join(DATA_PROCESSED_DIR, "preprocess_log.json"),
                        help="Log file path")
    
    args = parser.parse_args()
    
    logger.info(f"Starting preprocessing. Input: {args.input}, Output: {args.output}")
    
    try:
        result = preprocess_metabolomics(
            input_pattern=args.input,
            output_file=args.output,
            log_file=args.log
        )
        logger.info(f"Preprocessing complete. Status: {result['status']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()