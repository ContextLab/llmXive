import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

# FR-008 Disclaimer constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str) -> None:
    """Print a formatted header with the FR-008 disclaimer."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"  {FR008_DISCLAIMER}")
    print(f"{'='*60}\n")

def log_disclaimer() -> None:
    """Log the FR-008 disclaimer to stdout."""
    print(f"[DISCLAIMER] {FR008_DISCLAIMER}")

def get_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_and_validate_dataset(file_path: Path) -> Optional[pd.DataFrame]:
    """Load a dataset and perform basic validation."""
    log_disclaimer()
    try:
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix == '.data':
            # Handle UCI .data files (often no header)
            df = pd.read_csv(file_path, header=None)
        else:
            df = pd.read_csv(file_path)
        
        print(f"Loaded dataset with shape: {df.shape}")
        return df
    except Exception as e:
        print(f"Error loading dataset {file_path}: {e}")
        return None

def binarize_column(df: pd.DataFrame, column: str, target_map: Dict[Any, int]) -> pd.DataFrame:
    """Binarize a column based on a mapping."""
    df[column] = df[column].map(target_map)
    return df

def map_categorical_to_binary(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Map categorical values to binary 0/1."""
    # Simple heuristic: if >2 unique values, raise error or handle specifically
    unique_vals = df[column].unique()
    if len(unique_vals) == 2:
        # Map first to 0, second to 1
        mapping = {unique_vals[0]: 0, unique_vals[1]: 1}
        df[column] = df[column].map(mapping)
    elif len(unique_vals) > 2:
        # Attempt to map specific common categories
        # This is a simplified logic; real implementation would be more robust
        print(f"Warning: Column {column} has >2 unique values. Attempting mapping.")
        # Example: if 'Male', 'Female' -> 1, 0
        if 'Male' in unique_vals and 'Female' in unique_vals:
            df[column] = df[column].replace({'Male': 1, 'Female': 0})
        else:
            # Fallback: map first unique to 0, rest to 1? Or error?
            # For now, just return as is and log warning
            print(f"Could not automatically binarize {column}.")
    return df

def stratified_sample(df: pd.DataFrame, target_col: str, max_rows: int = 100000, random_state: int = 42) -> pd.DataFrame:
    """Perform stratified sampling to max_rows."""
    log_disclaimer()
    if len(df) <= max_rows:
        return df
    
    # Ensure target_col exists
    if target_col not in df.columns:
        print(f"Warning: Target column {target_col} not found. Using random sample.")
        return df.sample(n=max_rows, random_state=random_state)
    
    # Check if stratified sample is possible
    counts = df[target_col].value_counts()
    if len(counts) == 0:
        return df.sample(n=max_rows, random_state=random_state)
        
    # Calculate sample size per group
    sample_sizes = (counts / counts.sum()) * max_rows
    sample_sizes = sample_sizes.round().astype(int)
    
    # Ensure we don't exceed max_rows due to rounding
    current_sum = sample_sizes.sum()
    if current_sum > max_rows:
        # Adjust largest group
        max_group = sample_sizes.idxmax()
        sample_sizes[max_group] -= (current_sum - max_rows)
    
    return df.groupby(target_col, group_keys=False).apply(
        lambda x: x.sample(n=min(sample_sizes[x[target_col].iloc[0]], len(x)), random_state=random_state)
    ).reset_index(drop=True)

def preprocess_dataset(df: pd.DataFrame, dataset_name: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Preprocess dataset: extract binary protected attributes and outcomes.
    
    Returns:
        Tuple of (processed_df, list_of_excluded_reasons)
    """
    log_disclaimer()
    excluded = []
    
    # Identify protected attributes and outcomes based on common names
    protected_candidates = ['sex', 'gender', 'race', 'ethnicity', 'protected_attribute']
    outcome_candidates = ['income', 'salary', 'admit', 'default', 'recidivism', 'target']
    
    # Find best match
    protected_col = None
    outcome_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if protected_col is None and any(p in col_lower for p in protected_candidates):
            protected_col = col
        if outcome_col is None and any(o in col_lower for o in outcome_candidates):
            outcome_col = col
            
    if not protected_col:
        excluded.append(f"Missing protected attribute in {dataset_name}")
        print(f"Excluded {dataset_name}: Missing protected attribute")
        return df, excluded
        
    if not outcome_col:
        excluded.append(f"Missing outcome variable in {dataset_name}")
        print(f"Excluded {dataset_name}: Missing outcome variable")
        return df, excluded
        
    # Binarize protected attribute
    df = map_categorical_to_binary(df, protected_col)
    
    # Binarize outcome (simplified)
    # Assume outcome is already numeric or binary, or map high/yes to 1
    if df[outcome_col].dtype == 'object':
        # Map 'Yes'/'Yes'/'High' to 1, others to 0
        df[outcome_col] = df[outcome_col].apply(lambda x: 1 if str(x).lower() in ['yes', 'high', '1', 'true'] else 0)
    elif df[outcome_col].dtype in ['int64', 'float64']:
        # If continuous, might need thresholding, but for this task assume binary or convert
        if df[outcome_col].nunique() > 2:
            # Median split as a simple heuristic for binary outcome
            median_val = df[outcome_col].median()
            df[outcome_col] = (df[outcome_col] > median_val).astype(int)
    
    return df, excluded

def save_processed_dataset(df: pd.DataFrame, output_path: Path, dataset_name: str) -> str:
    """Save processed dataset and return checksum."""
    log_disclaimer()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    checksum = get_file_checksum(output_path)
    print(f"Saved processed data to {output_path}")
    print(f"SHA-256: {checksum}")
    return checksum

def preprocess_dataset_workflow(raw_dir: Path, processed_dir: Path) -> Dict[str, Any]:
    """Run the preprocessing workflow on all raw files."""
    log_header("US1 Preprocessing Pipeline")
    log_disclaimer()
    
    results = {}
    raw_files = list(raw_dir.glob("*"))
    
    for raw_file in raw_files:
        if raw_file.is_file() and raw_file.suffix in ['.csv', '.data', '.zip']:
            # Handle zip files (simplified)
            if raw_file.suffix == '.zip':
                print(f"Skipping zip file {raw_file.name} - extraction not implemented in this snippet")
                continue
                
            print(f"\nProcessing: {raw_file.name}")
            df = load_and_validate_dataset(raw_file)
            if df is None:
                continue
                
            processed_df, exclusions = preprocess_dataset(df, raw_file.stem)
            
            if exclusions:
                # Log exclusions (simplified)
                print(f"Exclusions for {raw_file.name}: {exclusions}")
                continue
                
            output_name = f"{raw_file.stem}_processed.csv"
            output_path = processed_dir / output_name
            checksum = save_processed_dataset(processed_df, output_path, raw_file.stem)
            
            results[raw_file.stem] = {
                "processed_file": str(output_path),
                "checksum": checksum,
                "rows": len(processed_df)
            }
            
    return results

def main():
    """Main entry point for preprocessing."""
    log_header("US1 Preprocessing Pipeline")
    log_disclaimer()
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    if not raw_dir.exists():
        print(f"Error: Raw data directory {raw_dir} does not exist.")
        return
        
    results = preprocess_dataset_workflow(raw_dir, processed_dir)
    
    print(f"\n{'='*60}")
    print(f"Preprocessing Summary")
    print(f"{'='*60}")
    for name, data in results.items():
        print(f"{name}: {data['rows']} rows, checksum: {data['checksum']}")
    print(f"{FR008_DISCLAIMER}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
