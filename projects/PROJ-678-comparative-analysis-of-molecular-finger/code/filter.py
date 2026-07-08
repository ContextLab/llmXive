import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import logging
from pathlib import Path
from datetime import datetime
import os
import sys

# Ensure sibling modules can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_logger
from constants import SMARTS_PATTERN

logger = get_logger(__name__)

def load_compounds(csv_path: str) -> pd.DataFrame:
    """Load the Tox21 dataset from CSV."""
    logger.info(f"Loading compounds from {csv_path}")
    df = pd.read_csv(csv_path)
    # Ensure SMILES column exists
    if 'SMILES' not in df.columns:
        raise ValueError("Input CSV must contain a 'SMILES' column")
    return df

def apply_smarts_filter(df: pd.DataFrame, smarts: str) -> pd.DataFrame:
    """Filter compounds that match the provided SMARTS pattern."""
    logger.info(f"Applying SMARTS filter: {smarts}")
    pattern = Chem.MolFromSmarts(smarts)
    if pattern is None:
        raise ValueError(f"Invalid SMARTS pattern: {smarts}")

    def matches(mol):
        if mol is None:
            return False
        return mol.HasSubstructMatch(pattern)

    mols = [Chem.MolFromSmiles(smi) for smi in df['SMILES']]
    mask = [matches(mol) for mol in mols]
    filtered_df = df[mask].reset_index(drop=True)
    logger.info(f"Filtered from {len(df)} to {len(filtered_df)} compounds")
    return filtered_df

def validate_endpoints(df: pd.DataFrame) -> dict:
    """Count non-null entries per toxicity endpoint column."""
    # Identify endpoint columns (typically columns starting with 'Nuc' or specific names)
    # In Tox21, endpoints are usually named like 'NR-AR', 'NR-AR-LBD', etc.
    # We'll assume columns other than 'SMILES' and 'id' are endpoints.
    endpoint_cols = [col for col in df.columns if col not in ['SMILES', 'id', 'Compound']]
    counts = {}
    for col in endpoint_cols:
        counts[col] = int(df[col].notna().sum())
    return counts

def save_filtered_data(df: pd.DataFrame, output_path: str, log_path: str) -> None:
    """Save filtered data to CSV and write detailed log."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")

    # Write detailed log
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.write(f"Filter Log - {datetime.now().isoformat()}\n")
        f.write("=" * 50 + "\n\n")
        
        # Dataset download size (simulated as we don't have the raw size here, 
        # but in a real pipeline this would be passed or measured)
        # Since T011 handles download, we log the input file size if it exists
        input_file = Path(output_path).parent / "tox21.csv" # Assumption based on pipeline
        if input_file.exists():
            size_kb = input_file.stat().st_size / 1024
            f.write(f"Dataset Download Size: {size_kb:.2f} KB\n")
        else:
            f.write("Dataset Download Size: N/A (Input file not found at expected path)\n")
        
        f.write(f"Initial Compound Count: {len(df)}\n")
        f.write(f"Filtered Compound Count: {len(df)}\n") # This is the filtered count
        f.write(f"SMARTS Pattern Used: {SMARTS_PATTERN}\n\n")
        
        f.write("Endpoint Distribution:\n")
        endpoint_counts = validate_endpoints(df)
        for endpoint, count in endpoint_counts.items():
            f.write(f"  {endpoint}: {count} non-null values\n")
        
        # Low sample size check
        min_count = min(endpoint_counts.values()) if endpoint_counts else 0
        if min_count < 50:
            f.write(f"\nWARNING: Low Sample Size detected (min count: {min_count}).\n")
            f.write("Statistical tests will be skipped as per validation logic.\n")

def main():
    """Main entry point for the filtering pipeline."""
    # Setup logging
    log_file = Path("data/processed/filter_log.txt")
    log_setup = setup_logging(log_file)
    
    input_csv = "data/raw/tox21.csv" # Assumed input from T011
    output_csv = "data/processed/organophosphates_filtered.csv"
    
    if not Path(input_csv).exists():
        logger.error(f"Input file {input_csv} not found. Run download.py first.")
        sys.exit(1)

    try:
        df = load_compounds(input_csv)
        filtered_df = apply_smarts_filter(df, SMARTS_PATTERN)
        
        if len(filtered_df) == 0:
            logger.warning("No compounds matched the SMARTS pattern.")
        
        save_filtered_data(filtered_df, output_csv, str(log_file))
        logger.info("Filtering and logging completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
