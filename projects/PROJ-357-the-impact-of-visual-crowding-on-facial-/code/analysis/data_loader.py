import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Add project root to path if running as script
if 'code' not in sys.path:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from config import ensure_directories, get_env_config

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'participant_id',
    'stimulus_id',
    'true_label',
    'response_label',
    'timestamp'
]

def load_raw_judgments(file_path: str) -> pd.DataFrame:
    """
    Load a single raw synthetic judgment CSV file.
    
    Args:
        file_path: Path to the CSV file containing raw judgments.
        
    Returns:
        DataFrame with raw judgment data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw judgment file not found: {file_path}")
    
    logger.info(f"Loading raw judgments from {file_path}")
    df = pd.read_csv(file_path)
    
    # Validate required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def load_all_judgments(data_dir: str) -> pd.DataFrame:
    """
    Load and concatenate all raw judgment CSV files from a directory.
    
    Args:
        data_dir: Directory containing raw judgment CSV files.
        
    Returns:
        Combined DataFrame with all judgments.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    csv_files = list(data_path.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {data_dir}")
    
    logger.info(f"Found {len(csv_files)} CSV files in {data_dir}")
    
    dfs = []
    for file in csv_files:
        try:
            df = load_raw_judgments(str(file))
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Failed to load {file}: {e}")
            continue
    
    if not dfs:
        raise ValueError("No valid judgment files could be loaded")
    
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined total of {len(combined_df)} judgments from {len(dfs)} files")
    return combined_df

def validate_judgments(df: pd.DataFrame, manifest_path: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate judgment data against the stimuli manifest if available.
    
    Args:
        df: DataFrame with judgment data.
        manifest_path: Optional path to the stimuli manifest JSON.
        
    Returns:
        Tuple of (validated DataFrame, validation report dict).
    """
    report = {
        'total_rows': len(df),
        'unique_participants': df['participant_id'].nunique(),
        'unique_stimuli': df['stimulus_id'].nunique(),
        'missing_stimuli': [],
        'invalid_labels': [],
        'duplicate_entries': 0
    }
    
    # Check for duplicate entries
    duplicates = df.duplicated(subset=['participant_id', 'stimulus_id'], keep=False)
    report['duplicate_entries'] = duplicates.sum()
    if report['duplicate_entries'] > 0:
        logger.warning(f"Found {report['duplicate_entries']} duplicate participant-stimulus entries")
    
    # Validate against manifest if provided
    if manifest_path and Path(manifest_path).exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        valid_stimuli = {entry['file_path'] for entry in manifest.get('stimuli', [])}
        stimuli_in_judgments = set(df['stimulus_id'].unique())
        
        missing = stimuli_in_judgments - valid_stimuli
        report['missing_stimuli'] = list(missing)
        
        if missing:
            logger.warning(f"Found {len(missing)} stimuli in judgments not in manifest")
        
        # Validate label consistency (optional, depends on manifest structure)
        # For now, we just check that labels are non-empty
        empty_labels = df[df['true_label'].isna() | (df['true_label'] == '')]
        report['invalid_labels'].extend(empty_labels['stimulus_id'].tolist())
        
        if report['invalid_labels']:
            logger.warning(f"Found {len(report['invalid_labels'])} entries with empty labels")
    
    # Final validation
    df['true_label'] = df['true_label'].astype(str).str.strip()
    df['response_label'] = df['response_label'].astype(str).str.strip()
    df['participant_id'] = df['participant_id'].astype(str).str.strip()
    df['stimulus_id'] = df['stimulus_id'].astype(str).str.strip()
    
    # Remove rows with missing critical data
    initial_count = len(df)
    df = df.dropna(subset=['participant_id', 'stimulus_id', 'true_label', 'response_label'])
    removed_count = initial_count - len(df)
    if removed_count > 0:
        logger.warning(f"Removed {removed_count} rows with missing critical data")
    
    report['final_rows'] = len(df)
    report['removed_rows'] = removed_count
    
    return df, report

def main():
    """
    Main entry point for loading and validating raw synthetic judgment data.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = get_env_config()
    data_dir = config.get('RAW_JUDGMENTS_DIR', 'data/raw/judgments')
    manifest_path = config.get('STIMULI_MANIFEST_PATH', 'data/interim/stimuli_manifest.json')
    output_path = config.get('VALIDATED_JUDGMENTS_PATH', 'data/processed/validated_judgments.csv')
    
    ensure_directories([output_path])
    
    try:
        # Load all judgments
        df = load_all_judgments(data_dir)
        
        # Validate
        validated_df, report = validate_judgments(df, manifest_path)
        
        # Save validated data
        validated_df.to_csv(output_path, index=False)
        logger.info(f"Saved validated judgments to {output_path}")
        
        # Print report
        print("\n=== Judgment Validation Report ===")
        print(json.dumps(report, indent=2))
        
        return validated_df, report
        
    except Exception as e:
        logger.error(f"Failed to load and validate judgments: {e}")
        raise

if __name__ == "__main__":
    main()