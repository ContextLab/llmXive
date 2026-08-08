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
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "valid_subjects.json"
ERROR_LOG = OUTPUT_DIR / "pipeline_errors.log"

def load_behavioral_scores(subject_id: str, base_dir: Path) -> Optional[float]:
    """
    Attempt to load a Fluid Intelligence score for a given subject.
    
    Strategy based on OpenNeuro ds000224 structure:
    1. Check for a 'phenotype' TSV file in the subject folder or root.
    2. Look for columns like 'fluid_intelligence', 'FI', 'fintelligence'.
    3. If no TSV found, check for a generic 'participants.tsv' and filter by subject_id.
    
    Returns the score as a float, or None if not found/invalid.
    """
    # Common locations for phenotype data in OpenNeuro
    possible_paths = [
        base_dir / "phenotype.tsv",
        base_dir / "participants.tsv",
        base_dir / "sub-" + subject_id / "phenotype.tsv",
        base_dir / "sub-" + subject_id / "participants.tsv",
    ]
    
    # Also check for specific fluid intelligence files if they exist (dataset dependent)
    # ds000224 typically has a phenotype.tsv in the root
    
    for p in possible_paths:
        if p.exists():
            try:
                import pandas as pd
                df = pd.read_csv(p, sep='\t')
                
                # Normalize column names for search
                cols_lower = {c.lower(): c for c in df.columns}
                
                # Potential column names for Fluid Intelligence
                target_cols = [
                    'fluid_intelligence', 'fluid_int', 'fi_score', 
                    'intelligence', 'cognitive_score', 'score'
                ]
                
                found_col = None
                for tc in target_cols:
                    if tc in cols_lower:
                        found_col = cols_lower[tc]
                        break
                
                if found_col:
                    # Filter by subject ID
                    sub_col = 'participant_id' if 'participant_id' in cols_lower else 'sub_id' if 'sub_id' in cols_lower else 'subject_id'
                    if sub_col not in cols_lower:
                        # Fallback: assume first column is ID if not found
                        sub_col = df.columns[0]
                    
                    try:
                        row = df[df[cols_lower[sub_col]] == subject_id]
                        if not row.empty:
                            val = row[found_col].iloc[0]
                            if pd.notna(val):
                                return float(val)
                    except (KeyError, ValueError, TypeError):
                        continue
                        
            except Exception as e:
                logger.warning(f"Failed to parse {p}: {e}")
                continue
                
    return None

def scan_subjects_for_scores(subject_ids: List[str], base_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan a list of subject IDs for valid Fluid Intelligence scores.
    """
    valid_subjects = []
    
    logger.info(f"Scanning {len(subject_ids)} subjects for Fluid Intelligence scores in {base_dir}")
    
    for sub_id in subject_ids:
        score = load_behavioral_scores(sub_id, base_dir)
        if score is not None:
            logger.info(f"Found valid Fluid Intelligence score for {sub_id}: {score}")
            valid_subjects.append({
                "id": sub_id,
                "score": score
            })
        else:
            logger.warning(f"No valid Fluid Intelligence score found for {sub_id}. Skipping.")
            
    return valid_subjects

def validate_and_aggregate(subject_ids: List[str], base_dir: Path) -> Dict[str, Any]:
    """
    Main validation logic for T014a.
    1. Scans subjects for scores.
    2. Writes results to data/processed/valid_subjects.json.
    3. Returns the result dict.
    """
    valid_subjects = scan_subjects_for_scores(subject_ids, base_dir)
    count = len(valid_subjects)
    
    result = {
        "subjects": valid_subjects,
        "count": count
    }
    
    # Write output file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Validation complete. Found {count} valid subjects. Output written to {OUTPUT_FILE}")
    
    if count == 0:
        logger.error("CRITICAL: No valid subjects found. Triggering T014c halt logic.")
        # Log to error file
        with open(ERROR_LOG, 'a') as f:
            f.write(f"[CRITICAL] No valid Fluid Intelligence data found. Time: {os.popen('date').read().strip()}\n")
        # Raise to trigger T014c logic in the caller or pipeline
        raise ValueError("No valid Fluid Intelligence data found in specified datasets")
        
    return result

def main():
    """
    Entry point for the validation script.
    Expects subject IDs to be passed or read from a config/download state.
    For this task, we assume the download step (T013a) has populated data/raw 
    and we need to know which subjects were downloaded.
    
    If no specific subject list is provided, we attempt to infer from data/raw.
    """
    # Determine base directory for raw data
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        logger.error("data/raw directory does not exist. Run download task first.")
        sys.exit(1)
    
    # Infer subject IDs from directory structure (e.g., sub-01, sub-02...)
    # Or read from a manifest if T013a created one.
    # For robustness, we scan the raw directory for sub-* folders.
    subject_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    subject_ids = [d.name for d in subject_dirs]
    
    if not subject_ids:
        logger.error("No subject directories found in data/raw.")
        sys.exit(1)
        
    logger.info(f"Detected subjects: {subject_ids}")
    
    try:
        result = validate_and_aggregate(subject_ids, raw_dir)
        print(json.dumps(result))
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
