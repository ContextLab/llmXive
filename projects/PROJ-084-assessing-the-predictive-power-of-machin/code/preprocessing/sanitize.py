import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolStandardize
from rdkit.Chem.rdmolops import RemoveHs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = Path("data/raw/uspto_raw.parquet")
CHECKSUM_PATH = Path("data/results/download_checksum.txt")
OUTPUT_PATH = Path("data/processed/sanitized_reactions.parquet")
QUALITY_REPORT_PATH = Path("data/results/data_quality_report.json")


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum() -> bool:
    """
    Verify that the downloaded file's checksum matches the recorded checksum.
    Returns True if valid, raises FileNotFoundError if invalid or missing.
    """
    if not CHECKSUM_PATH.exists():
        raise FileNotFoundError(
            f"Checksum file not found: {CHECKSUM_PATH}. "
            "Run download.py (T019) first."
        )

    with open(CHECKSUM_PATH, "r") as f:
        content = f.read().strip()

    if "FAILED" in content:
        raise FileNotFoundError("Download failed, no data available. Check download logs.")

    # Expected format: "sha256_hash  filename" or just the hash
    # We expect the file to contain the hash of uspto_raw.parquet
    recorded_hash = content.split()[0] if " " in content else content

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")

    actual_hash = calculate_sha256(RAW_DATA_PATH)

    if actual_hash != recorded_hash:
        raise ValueError(
            f"Checksum mismatch! "
            f"Expected: {recorded_hash}, Got: {actual_hash}. "
            f"Data may be corrupted. Please re-run download.py."
        )

    logger.info("Checksum verification passed.")
    return True


def remove_salts_and_standardize(smiles: str) -> Optional[str]:
    """
    Remove salts and standardize a molecule using RDKit.
    Returns the sanitized SMILES string or None if parsing fails.
    """
    if not smiles or not isinstance(smiles, str):
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        # Remove hydrogens
        mol_no_h = RemoveHs(mol)

        # Standardize / Clean (remove salts, normalize)
        cleaner = rdMolStandardize.Cleaner()
        mol_clean = cleaner.clean(mol_no_h)

        if mol_clean is None:
            return None

        # Convert back to canonical SMILES
        canonical_smiles = Chem.MolToSmiles(mol_clean, isomericSmiles=True)
        return canonical_smiles

    except Exception as e:
        logger.debug(f"Failed to sanitize SMILES '{smiles}': {e}")
        return None


def sanitize_reactions(df: pd.DataFrame, batch_size: int = 10000) -> pd.DataFrame:
    """
    Sanitize a DataFrame of reactions.
    Applies salt removal and standardization to the 'smiles' column.
    """
    logger.info(f"Starting sanitization of {len(df)} rows...")
    
    sanitized_smiles = []
    excluded_count = 0
    total = len(df)

    for i in range(0, total, batch_size):
        batch = df.iloc[i : i + batch_size]
        batch_results = []
        
        for idx, row in batch.iterrows():
            original_smiles = row.get('smiles')
            if pd.isna(original_smiles):
                excluded_count += 1
                batch_results.append(None)
                continue
            
            sanitized = remove_salts_and_standardize(str(original_smiles))
            if sanitized is None:
                excluded_count += 1
            batch_results.append(sanitized)
        
        sanitized_smiles.extend(batch_results)
        
        if (i + batch_size) % 50000 == 0 or (i + batch_size) >= total:
            logger.info(f"Processed {min(i + batch_size, total)}/{total} rows. Excluded so far: {excluded_count}")

    df_out = df.copy()
    df_out['smiles'] = sanitized_smiles
    
    # Drop rows where sanitization failed
    df_out = df_out[df_out['smiles'].notna()].reset_index(drop=True)
    final_excluded = total - len(df_out)
    
    logger.info(f"Sanitization complete. Final rows: {len(df_out)}. Total excluded: {final_excluded}")
    return df_out


def parse_yield_batch(df: pd.DataFrame, strategy: str = 'midpoint') -> pd.DataFrame:
    """
    Parse yield column. Handles ranges (e.g., "50-60%") based on strategy.
    This is a placeholder for T015 logic, but included here to ensure
    the pipeline produces a valid numeric yield column if T015 hasn't run yet.
    """
    if 'yield' not in df.columns:
        return df

    def parse_single_yield(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        if val_str.endswith('%'):
            val_str = val_str[:-1]
        
        if '-' in val_str:
            # Range handling
            parts = val_str.split('-')
            if len(parts) == 2:
                try:
                    low = float(parts[0])
                    high = float(parts[1])
                    if strategy == 'midpoint':
                        return (low + high) / 2.0
                    elif strategy == 'exclude':
                        return None
                except ValueError:
                    return None
            return None
        
        try:
            return float(val_str)
        except ValueError:
            return None

    df_out = df.copy()
    df_out['yield'] = df_out['yield'].apply(parse_single_yield)
    df_out = df_out[df_out['yield'].notna()].reset_index(drop=True)
    return df_out


def run_sanitization_pipeline():
    """Main entry point for the sanitization pipeline."""
    logger.info("=== Starting Sanitization Pipeline (T014) ===")
    
    # Step 1: Verify Checksum
    try:
        verify_checksum()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Checksum verification failed: {e}")
        raise

    # Step 2: Load Data
    logger.info(f"Loading raw data from {RAW_DATA_PATH}...")
    try:
        df = pd.read_parquet(RAW_DATA_PATH)
        logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise

    # Step 3: Sanitize (Salts/Standardize)
    df_sanitized = sanitize_reactions(df)

    # Step 4: Parse Yield (Basic implementation, T015 will refine)
    # Note: T015 is listed as a separate task, but T014 needs to produce a valid output.
    # We apply a default 'midpoint' strategy here to ensure the output is numeric.
    df_clean = parse_yield_batch(df_sanitized, strategy='midpoint')

    # Step 5: Ensure Output Directory
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Step 6: Save Output
    logger.info(f"Saving sanitized data to {OUTPUT_PATH}...")
    df_clean.to_parquet(OUTPUT_PATH, index=False)
    
    # Step 7: Generate Quality Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(RAW_DATA_PATH),
        "output_file": str(OUTPUT_PATH),
        "input_rows": len(df),
        "output_rows": len(df_clean),
        "excluded_rows": len(df) - len(df_clean),
        "exclusion_reasons": {
            "invalid_smiles": "Failed to parse or sanitize",
            "missing_smiles": "NaN or empty SMILES",
            "invalid_yield": "Yield parsing failed"
        },
        "yield_parsing_strategy": "midpoint (default for T014)"
    }
    
    QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUALITY_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sanitization pipeline complete. Output: {OUTPUT_PATH}")
    logger.info(f"Quality report saved to {QUALITY_REPORT_PATH}")


def main():
    run_sanitization_pipeline()


if __name__ == "__main__":
    main()