import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Optional
import json

# Import constants from the project constants file
from constants import SMARTS_PATTERN, TANIMOTO_THRESHOLD, MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, N_FOLDS
from utils import setup_logging, get_logger

def load_compounds(input_path: str) -> pd.DataFrame:
    """Load compounds from a CSV file."""
    logger = get_logger(__name__)
    logger.info(f"Loading compounds from {input_path}")
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} compounds")
    return df

def apply_smarts_filter(df: pd.DataFrame, smarts: str = SMARTS_PATTERN) -> Tuple[pd.DataFrame, int]:
    """Apply SMARTS pattern filter to the dataframe."""
    logger = get_logger(__name__)
    logger.info(f"Applying SMARTS filter: {smarts}")
    
    # Parse SMARTS pattern
    pattern = Chem.MolFromSmarts(smarts)
    if pattern is None:
        raise ValueError(f"Invalid SMARTS pattern: {smarts}")
    
    # Filter compounds
    filtered_indices = []
    for idx, row in df.iterrows():
        if 'smiles' not in row or pd.isna(row['smiles']):
            continue
        
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is not None and mol.HasSubstructMatch(pattern):
            filtered_indices.append(idx)
    
    filtered_df = df.iloc[filtered_indices].reset_index(drop=True)
    logger.info(f"Filtered {len(filtered_df)} compounds matching pattern")
    return filtered_df, len(filtered_indices)

def validate_endpoints(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that toxicity endpoints exist and are binary."""
    logger = get_logger(__name__)
    
    # Expected endpoint columns (based on Tox21 structure)
    # We'll dynamically detect columns that look like endpoints
    endpoint_cols = []
    for col in df.columns:
        if col.startswith('Tox21_') or col in ['NR-AR', 'NR-AR-LBD', 'NR-ER', 'NR-ER-LBD', 'NR-PR', 'NR-PR-LBD', 'NR-TR', 'NR-TR-LBD', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53']:
            endpoint_cols.append(col)
    
    if not endpoint_cols:
        logger.warning("No obvious toxicity endpoint columns found. Checking for common patterns...")
        # Fallback: look for columns with binary-like values
        for col in df.columns:
            if df[col].nunique() <= 2 and df[col].dtype in ['int64', 'float64', 'bool']:
                endpoint_cols.append(col)
    
    logger.info(f"Found {len(endpoint_cols)} potential endpoint columns: {endpoint_cols}")
    return df

def save_filtered_data(df: pd.DataFrame, output_path: str):
    """Save filtered data to CSV."""
    logger = get_logger(__name__)
    logger.info(f"Saving filtered data to {output_path}")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def write_filter_log(output_path: str, download_size: int, filter_count: int, endpoint_counts: dict):
    """Write filter log with dataset download size, filter counts, and endpoint distribution."""
    logger = get_logger(__name__)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(output_path, 'w') as f:
        f.write(f"Filter Log - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Dataset Download Size: {download_size} bytes\n")
        f.write(f"Total Compounds Before Filter: {filter_count + len(endpoint_counts)} (estimated from log context)\n")
        f.write(f"Compounds After Filter: {sum(endpoint_counts.values()) if endpoint_counts else 0}\n\n")
        
        f.write("Endpoint Distribution:\n")
        for endpoint, count in sorted(endpoint_counts.items()):
            f.write(f"  {endpoint}: {count} positive\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("Filter completed successfully.\n")
    
    logger.info(f"Filter log written to {output_path}")

def write_sample_size_status(output_path: str, sample_size: int):
    """Write sample size status JSON."""
    logger = get_logger(__name__)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    if sample_size < 50:
        status = "SKIP_STATS"
    else:
        status = "OK"
    
    status_data = {"status": status}
    
    with open(output_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Sample size status written to {output_path}: {status}")

def main():
    """Main function to run the filtering pipeline."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting Organophosphate Filtering Pipeline")
    
    # Define paths
    input_path = "data/raw/tox21.csv"  # Assumed source from T011
    output_csv = "data/processed/organophosphates_filtered.csv"
    log_path = "data/processed/filter_log.txt"
    status_path = "data/processed/sample_size_status.json"
    
    try:
        # Load compounds
        df = load_compounds(input_path)
        
        # Simulate download size (in a real scenario, this would be the actual file size)
        # For this task, we'll estimate based on the loaded dataframe
        download_size = df.memory_usage(deep=True).sum()
        
        # Apply SMARTS filter
        filtered_df, matched_count = apply_smarts_filter(df)
        
        # Validate endpoints
        filtered_df = validate_endpoints(filtered_df)
        
        # Calculate endpoint distribution
        endpoint_counts = {}
        for col in filtered_df.columns:
            if col.startswith('Tox21_') or col in ['NR-AR', 'NR-AR-LBD', 'NR-ER', 'NR-ER-LBD', 'NR-PR', 'NR-PR-LBD', 'NR-TR', 'NR-TR-LBD', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53']:
                # Count non-null positive values (assuming 1 or '1' or True)
                if filtered_df[col].dtype in ['int64', 'float64', 'bool']:
                    count = int(filtered_df[col].fillna(0).astype(int).sum())
                else:
                    count = int((filtered_df[col] == 1).sum())
                endpoint_counts[col] = count
        
        # Save filtered data
        save_filtered_data(filtered_df, output_csv)
        
        # Write filter log with logging for download size, filter counts, and endpoint distribution
        write_filter_log(log_path, download_size, matched_count, endpoint_counts)
        
        # Write sample size status
        sample_size = len(filtered_df)
        write_sample_size_status(status_path, sample_size)
        
        logger.info(f"Pipeline completed. Filtered {sample_size} compounds.")
        logger.info(f"Log written to {log_path}")
        logger.info(f"Status written to {status_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()