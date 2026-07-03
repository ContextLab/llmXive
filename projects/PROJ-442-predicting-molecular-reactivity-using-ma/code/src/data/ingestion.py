import os
import json
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
import logging
import pandas as pd

from src.utils.logging import setup_logging
from src.utils.state_manager import update_artifact_state
from src.utils.chemistry import load_templates, classify_reaction
from src.data.schemas import ReactionRecord

# Configuration constants
USPTO_URL = "https://zenodo.org/record/3969375/files/uspto-mit-sample.jsonl.gz"
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
STATE_PROJECT_ID = "PROJ-442-predicting-molecular-reactivity-using-ma"
OUTPUT_FILENAME = "filtered_reactions.csv"

logger = setup_logging(__name__)

def ensure_dirs():
    """Create necessary directories for data and state."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories: {RAW_DATA_DIR}, {PROCESSED_DATA_DIR}")

def download_data() -> Path:
    """Download the USPTO-MIT subset from Zenodo."""
    ensure_dirs()
    output_path = RAW_DATA_DIR / "uspto_mit_sample.jsonl.gz"
    
    if output_path.exists():
        logger.info(f"Data file already exists at {output_path}, skipping download.")
        return output_path

    logger.info(f"Downloading data from {USPTO_URL}...")
    try:
        response = requests.get(USPTO_URL, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Download complete: {output_path}")
    except requests.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        raise

    return output_path

def parse_jsonl(file_path: Path) -> Generator[Dict[str, Any], None, None]:
    """Parse the JSONL file (handling .gz if necessary)."""
    import gzip
    
    logger.info(f"Parsing JSONL from {file_path}")
    open_func = gzip.open if file_path.suffix == '.gz' else open
    
    with open_func(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON on line {line_num}: {e}")

def normalize_smiles(smiles: str) -> Optional[str]:
    """Normalize SMILES string using RDKit."""
    from rdkit import Chem
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception as e:
        logger.warning(f"Failed to normalize SMILES '{smiles}': {e}")
        return None

def process_record(record: Dict[str, Any], templates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a single record: normalize SMILES, classify reaction, derive target."""
    # Extract reactants/products
    reactants = record.get('reactants', [])
    products = record.get('products', [])
    
    if not reactants or not products:
        return None

    # Normalize SMILES for reactants
    norm_reactants = []
    for r in reactants:
        norm = normalize_smiles(r)
        if norm:
            norm_reactants.append(norm)
        else:
            return None # Skip record if any reactant is invalid

    # Classify reaction
    reaction_type = classify_reaction(reactants, products, templates)
    if reaction_type is None:
        return None

    # Derive target variable
    # Priority: yield_pct -> success_flag -> None (skip)
    target = None
    if 'yield_pct' in record:
        try:
            target = float(record['yield_pct'])
        except (ValueError, TypeError):
            target = None
    elif 'success_flag' in record:
        target = float(record['success_flag'])
    
    if target is None:
        return None

    return {
        'reactants_smiles': ','.join(norm_reactants),
        'products_smiles': ','.join(products), # Assuming products are already normalized or we skip if not
        'reaction_type': reaction_type,
        'target': target,
        'raw_record': record
    }

def filter_by_class_sample_size(df: pd.DataFrame, min_count: int = 1000) -> pd.DataFrame:
    """Filter out classes with fewer than min_count samples."""
    if df.empty:
        return df

    value_counts = df['reaction_type'].value_counts()
    classes_to_keep = value_counts[value_counts >= min_count].index.tolist()
    
    if len(classes_to_keep) < len(value_counts):
        removed_classes = set(value_counts.index) - set(classes_to_keep)
        logger.warning(f"Removing classes with < {min_count} samples: {removed_classes}")
    
    filtered_df = df[df['reaction_type'].isin(classes_to_keep)]
    logger.info(f"Filtered dataset from {len(df)} to {len(filtered_df)} rows.")
    return filtered_df

def save_to_csv(df: pd.DataFrame, output_path: Path):
    """Save dataframe to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")

def main():
    """Main orchestration function for data ingestion with logging and state updates."""
    logger.info("Starting data ingestion pipeline (T018 integration).")
    
    # 1. Ensure directories
    ensure_dirs()

    # 2. Download data
    data_path = download_data()
    
    # 3. Load templates from config
    # Assuming config.yaml is in src/modeling/config.yaml as per T008/T013c
    config_path = Path("code/src/modeling/config.yaml")
    if not config_path.exists():
        logger.error(f"Config file not found at {config_path}. Cannot proceed without templates.")
        # In a real pipeline, we might exit or use defaults, but here we fail loudly
        return

    templates = load_templates(config_path)
    logger.info(f"Loaded {len(templates)} reaction templates.")

    # 4. Process records
    processed_records = []
    total_rows = 0
    valid_rows = 0

    for record in parse_jsonl(data_path):
        total_rows += 1
        try:
            processed = process_record(record, templates)
            if processed:
                processed_records.append(processed)
                valid_rows += 1
        except Exception as e:
            logger.error(f"Error processing record: {e}")
            continue

    logger.info(f"Processed {total_rows} rows, {valid_rows} valid records.")

    if not processed_records:
        logger.warning("No valid records found to process.")
        return

    # 5. Create DataFrame
    df = pd.DataFrame(processed_records)
    
    # 6. Filter by class sample size
    df_filtered = filter_by_class_sample_size(df, min_count=1000)

    if df_filtered.empty:
        logger.warning("All classes were filtered out due to low sample size.")
        return

    # 7. Save to CSV
    output_path = PROCESSED_DATA_DIR / OUTPUT_FILENAME
    save_to_csv(df_filtered, output_path)

    # 8. Compute checksum
    checksum = hashlib.sha256()
    with open(output_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            checksum.update(chunk)
    checksum_str = checksum.hexdigest()

    # 9. Update State
    logger.info(f"Updating state for artifact: {output_path}")
    try:
        update_artifact_state(
            project_id=STATE_PROJECT_ID,
            artifact_name="filtered_reactions",
            file_path=str(output_path),
            checksum=checksum_str,
            row_count=len(df_filtered),
            columns=list(df_filtered.columns),
            task_id="T018"
        )
        logger.info("State updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update state: {e}")
        # Do not fail the script if state update fails, but log it clearly

    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()