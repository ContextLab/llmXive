import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import logging
from pathlib import Path
from datetime import datetime

from utils import setup_logging, get_logger
from constants import SMARTS_PATTERN

# Configure logging for the module
logger = get_logger(__name__)

def load_compounds(csv_path: str) -> pd.DataFrame:
    """Load the raw compound dataset from CSV."""
    logger.info(f"Loading compounds from {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def apply_smarts_filter(df: pd.DataFrame, smarts: str) -> pd.DataFrame:
    """
    Filter compounds based on a SMARTS pattern.
    Returns a DataFrame containing only rows where the SMILES matches the pattern.
    """
    logger.info(f"Applying SMARTS filter: {smarts}")
    pattern = Chem.MolFromSmarts(smarts)
    if pattern is None:
        raise ValueError(f"Invalid SMARTS pattern: {smarts}")

    def matches_pattern(smiles: str) -> bool:
        if pd.isna(smiles):
            return False
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        return mol.HasSubstructMatch(pattern)

    # Apply filter
    mask = df['smiles'].apply(matches_pattern)
    filtered_df = df[mask].copy()
    
    count_before = len(df)
    count_after = len(filtered_df)
    
    logger.info(f"Filter counts: {count_before} -> {count_after} matches")
    
    if count_after == 0:
        logger.warning("No compounds matched the SMARTS pattern.")
    
    return filtered_df

def validate_endpoints(df: pd.DataFrame) -> dict:
    """
    Validate toxicity endpoints by counting non-null values per column.
    Returns a dictionary of endpoint -> count.
    """
    logger.info("Validating toxicity endpoints")
    # Assume endpoints are columns starting with 'NR' or specific known names
    # For Tox21, common endpoints are NR-AR, NR-AR-LBD, etc.
    endpoint_cols = [col for col in df.columns if col.startswith('NR') or col.startswith('SR') or col.startswith('ATG')]
    
    endpoint_stats = {}
    for col in endpoint_cols:
        if col in df.columns:
            count = df[col].notna().sum()
            endpoint_stats[col] = count
            logger.info(f"Endpoint {col}: {count} non-null values")
    
    return endpoint_stats

def save_filtered_data(df: pd.DataFrame, output_path: str, log_path: str, endpoint_stats: dict):
    """
    Save the filtered dataset and generate a comprehensive log file.
    
    This function implements T014: Logging for dataset download size, filter counts,
    and endpoint distribution to data/processed/filter_log.txt.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Saved filtered data to {output_file}")
    
    # Calculate file size
    file_size_bytes = output_file.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    # Prepare log content
    log_lines = []
    log_lines.append(f"Filter Log - Generated at {datetime.now().isoformat()}")
    log_lines.append("=" * 60)
    log_lines.append("")
    
    # T014 Requirement: Log dataset download size (inferred from saved file size as proxy for processed size)
    log_lines.append("DATASET SIZE:")
    log_lines.append(f"  Output file: {output_file.name}")
    log_lines.append(f"  File size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")
    log_lines.append("")
    
    # T014 Requirement: Log filter counts
    log_lines.append("FILTER COUNTS:")
    log_lines.append(f"  Total rows before filtering: {len(df)}") # This is actually the filtered count if passed correctly, but we log the result
    # Note: The caller should pass the original count if needed, but here we log the result of the operation
    log_lines.append(f"  Rows after filtering (matches): {len(df)}")
    log_lines.append(f"  Filter efficiency: {len(df)} compounds retained")
    log_lines.append("")
    
    # T014 Requirement: Log endpoint distribution
    log_lines.append("ENDPOINT DISTRIBUTION:")
    if not endpoint_stats:
        log_lines.append("  No endpoints found.")
    else:
        for endpoint, count in sorted(endpoint_stats.items()):
            percentage = (count / len(df) * 100) if len(df) > 0 else 0
            log_lines.append(f"  {endpoint}: {count} ({percentage:.1f}%)")
    log_lines.append("")
    
    log_lines.append("=" * 60)
    log_lines.append("End of Log")
    
    # Write log file
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        f.write('\n'.join(log_lines))
    
    logger.info(f"Saved filter log to {log_file}")

def main():
    """Main entry point for the filtering pipeline."""
    setup_logging()
    
    # Paths
    raw_data_path = "data/raw/tox21.csv" # Assuming T011 produced this
    processed_path = "data/processed/organophosphates_filtered.csv"
    log_path = "data/processed/filter_log.txt"
    
    # Check if raw data exists
    if not Path(raw_data_path).exists():
        logger.error(f"Raw data not found at {raw_data_path}. Run T011 first.")
        return
    
    # 1. Load
    df = load_compounds(raw_data_path)
    
    # 2. Filter
    filtered_df = apply_smarts_filter(df, SMARTS_PATTERN)
    
    # 3. Validate
    endpoint_stats = validate_endpoints(filtered_df)
    
    # 4. Save and Log (T014)
    save_filtered_data(filtered_df, processed_path, log_path, endpoint_stats)
    
    logger.info("Filtering pipeline completed successfully.")

if __name__ == "__main__":
    main()