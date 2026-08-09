import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging to stderr and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('data/processed/validation_errors.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_behavioral_scores(subject_id: str, base_path: Path) -> Optional[float]:
    """
    Attempt to load the Fluid Intelligence score for a specific subject.
    Looks for 'participants.tsv' or 'participants.json' in the subject's functional directory
    or the root of the dataset if subject-specific behavioral data isn't present.
    
    In OpenNeuro ds000224, behavioral data is often in 'participants.tsv'.
    We assume the score is in a column named 'fluid_intelligence' or 'fluid_int'.
    """
    # Strategy: Look in the dataset root for participants.tsv first (common in OpenNeuro)
    # If that fails, look inside the subject folder.
    root_path = base_path.parent.parent if base_path.name.startswith('sub-') else base_path
    
    participants_file = root_path / "participants.tsv"
    
    if not participants_file.exists():
        logger.debug(f"No participants.tsv found for {subject_id} at {participants_file}")
        return None

    try:
        import pandas as pd
        df = pd.read_csv(participants_file, sep='\t')
        
        # Check for column variations
        possible_cols = ['fluid_intelligence', 'fluid_int', 'fluid_intelligence_score', 'score']
        found_col = None
        for col in possible_cols:
            if col in df.columns:
                found_col = col
                break
        
        if not found_col:
            logger.warning(f"Could not find fluid intelligence column in {participants_file}. Columns: {list(df.columns)}")
            return None

        # Filter for the specific subject
        # Subject ID in participants.tsv usually matches the folder name without 'sub-' prefix or with it depending on format.
        # OpenNeuro typically uses 'sub-<label>' in the participant_id column.
        subj_row = df[df['participant_id'] == subject_id]
        
        if subj_row.empty:
            logger.debug(f"Subject {subject_id} not found in participants.tsv")
            return None
        
        score = subj_row[found_col].iloc[0]
        
        # Validate score is numeric and not NaN
        if pd.isna(score):
            return None
        
        try:
            return float(score)
        except (ValueError, TypeError):
            logger.warning(f"Non-numeric fluid intelligence score for {subject_id}: {score}")
            return None

    except Exception as e:
        logger.error(f"Error reading behavioral scores for {subject_id}: {e}")
        return None

def scan_subjects_for_scores(subject_ids: List[str], data_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan a list of subject IDs for valid fluid intelligence scores.
    Returns a list of dicts: {"id": str, "score": float}
    """
    valid_subjects = []
    
    # Determine the base dataset directory (e.g., data/raw/ds000224)
    # We assume subject folders are direct children of data_dir
    
    for sub_id in subject_ids:
        # Check if the subject directory exists to ensure we have data
        sub_dir = data_dir / sub_id
        if not sub_dir.exists():
            logger.warning(f"Subject directory missing for {sub_id}, skipping.")
            continue

        score = load_behavioral_scores(sub_id, data_dir)
        
        if score is not None:
            valid_subjects.append({
                "id": sub_id,
                "score": score
            })
            logger.info(f"Found valid Fluid Intelligence score for {sub_id}: {score}")
        else:
            logger.warning(f"No valid Fluid Intelligence score found for {sub_id}")
    
    return valid_subjects

def validate_and_aggregate(subject_ids: List[str], data_dir: Path) -> Dict[str, Any]:
    """
    Main validation function.
    Scans subjects, aggregates results, and writes to data/processed/valid_subjects.json.
    Returns the result dict.
    """
    output_dir = ensure_directories()
    output_file = output_dir / "valid_subjects.json"
    
    logger.info(f"Starting validation for {len(subject_ids)} subjects in {data_dir}")
    
    valid_subjects = scan_subjects_for_scores(subject_ids, data_dir)
    
    result = {
        "subjects": valid_subjects,
        "count": len(valid_subjects)
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Validation complete. Found {result['count']} valid subjects. Written to {output_file}")
    
    # If count is 0, we trigger the halt logic (T016c) by raising an error or returning a flag.
    # Per T016a description: "If count is 0, trigger T016c."
    # We raise a specific error here so the caller (main) can handle the T016c logic.
    if result['count'] == 0:
        logger.critical("No valid Fluid Intelligence data found in specified datasets.")
        # This error message matches the requirement for T016c
        raise ValueError("No valid Fluid Intelligence data found in specified datasets")
        
    return result

def get_subject_list_from_download_log(download_log_path: Path) -> List[str]:
    """
    Helper to read the list of subjects from the download log or config if available.
    For this implementation, we assume the caller passes the list or we read from a known download artifact.
    If the download process wrote a list of downloaded subjects, we read it here.
    """
    # Fallback: Try to read from a hypothetical download summary if T015 wrote one
    # Since T015 is completed, it might have written a list. 
    # If not, this function expects the list to be passed in the main or derived from directory scan.
    return []

def main():
    """
    Entry point for T016a.
    Reads the list of downloaded subjects (from config or directory scan),
    validates Fluid Intelligence scores, and outputs valid_subjects.json.
    """
    # Determine the dataset directory based on config (T010)
    # Primary: ds000224, Fallback: ds000230
    # We scan data/raw for the dataset directories
    
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        logger.critical("Data raw directory does not exist. Run download tasks first.")
        sys.exit(1)
    
    # Find the dataset directory (ds000224 or ds000230)
    dataset_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith('ds')]
    
    if not dataset_dirs:
        logger.critical("No dataset directories found in data/raw.")
        sys.exit(1)
    
    # Prefer ds000224
    target_dataset = None
    for d in dataset_dirs:
        if d.name == 'ds000224':
            target_dataset = d
            break
    
    if not target_dataset and dataset_dirs:
        target_dataset = dataset_dirs[0] # Fallback to whatever is there
        
    logger.info(f"Using dataset directory: {target_dataset}")
    
    # Extract subject IDs from the directory structure
    # Assuming standard BIDS: data/raw/dsXXXXXX/sub-XXXX/...
    subject_ids = []
    for item in target_dataset.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            subject_ids.append(item.name)
    
    if not subject_ids:
        logger.critical("No subject directories found in the dataset.")
        sys.exit(1)
    
    logger.info(f"Found {len(subject_ids)} subjects to validate.")
    
    try:
        result = validate_and_aggregate(subject_ids, target_dataset)
        print(json.dumps(result, indent=2))
    except ValueError as e:
        # This triggers T016c logic
        logger.error(str(e))
        # Write to validation_errors.log with the specific prefix if not already done by logger
        # The logger already writes to the file, but we ensure the message is there.
        with open("data/processed/validation_errors.log", "a") as log_file:
            log_file.write(f"[VALIDATION_ERROR] {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
