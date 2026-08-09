import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary data directories if they don't exist."""
    dirs = [
        Path("data/raw"),
        Path("data/interim"),
        Path("data/processed"),
        Path("reports")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {[str(d) for d in dirs]}")

def get_subject_list_from_download_log():
    """
    Retrieve subject list from download log if available.
    This is a placeholder for T015 logic to parse download logs.
    """
    # In a real scenario, this would parse data/raw/download_log.json
    # For now, return an empty list or a mock list for testing
    return []

def load_behavioral_scores(subject_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load behavioral scores for a subject.
    
    This function explicitly looks for 'fluid_intelligence' scores.
    Any logic related to 'musical_creativity', 'TTCT', or 'AUT' is
    removed/replaced to comply with the Pivot Logic of T015.
    
    Args:
        subject_dir: Path to the subject's directory.
        
    Returns:
        Dictionary containing score info, or None if not found.
    """
    # Look for common behavioral data files
    possible_files = [
        subject_dir / "behav.json",
        subject_dir / "behav.tsv",
        subject_dir / "participants.tsv",
        subject_dir / "task-rest_bold.json" # Sometimes metadata is here
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            try:
                if file_path.suffix == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                elif file_path.suffix == '.tsv':
                    # Simple TSV parser for testing
                    data = {}
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            headers = lines[0].strip().split('\t')
                            values = lines[1].strip().split('\t')
                            data = dict(zip(headers, values))
                else:
                    continue
                
                # Pivot Logic: Check specifically for Fluid Intelligence
                # Remove any check for 'musical_creativity' or 'TTCT'
                if 'fluid_intelligence' in data:
                    return {
                        "score": float(data['fluid_intelligence']),
                        "source": str(file_path)
                    }
                elif 'Fluid_Intelligence_Score' in data:
                    return {
                        "score": float(data['Fluid_Intelligence_Score']),
                        "source": str(file_path)
                    }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Could not parse {file_path}: {e}")
                continue
                
    return None

def scan_subjects_for_scores(subjects: List[str], base_path: Path = None) -> List[Dict[str, Any]]:
    """
    Scan a list of subjects for valid Fluid Intelligence scores.
    
    Args:
        subjects: List of subject IDs (e.g., ['sub-001', 'sub-002'])
        base_path: Base path to data/raw. Defaults to Path("data/raw")
        
    Returns:
        List of dicts with 'id' and 'score'
    """
    if base_path is None:
        base_path = Path("data/raw")
        
    valid_scores = []
    
    for subj_id in subjects:
        subj_dir = base_path / subj_id
        if not subj_dir.exists():
            logger.debug(f"Subject directory not found: {subj_dir}")
            continue
            
        score_data = load_behavioral_scores(subj_dir)
        if score_data and score_data['score'] is not None:
            valid_scores.append({
                "id": subj_id,
                "score": score_data['score']
            })
            logger.info(f"Found Fluid Intelligence score {score_data['score']} for {subj_id}")
        else:
            logger.debug(f"No valid Fluid Intelligence score found for {subj_id}")
            
    return valid_scores

def validate_and_aggregate():
    """
    Main validation function for T015.
    
    1. Gets the list of subjects (mocked or from download log).
    2. Scans for Fluid Intelligence scores.
    3. Writes results to data/processed/valid_subjects.json.
    4. Returns the results.
    
    This function replaces any previous logic that checked for Musical Creativity.
    """
    ensure_directories()
    
    # In a real run, we would get subjects from the download log or dataset
    # For this implementation, we rely on the test mocking or existing data
    # If no subjects are found, we return an empty list which triggers the halt
    
    # Mocking the subject list for the purpose of this function if not present
    # In a real pipeline, get_subject_list_from_download_log() would provide this
    subjects = get_subject_list_from_download_log()
    
    # If subjects list is empty, we try to scan data/raw directly if it exists
    if not subjects:
        raw_dir = Path("data/raw")
        if raw_dir.exists():
            subjects = [d.name for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    
    valid_scores = scan_subjects_for_scores(subjects)
    
    result = {
        "subjects": valid_scores,
        "count": len(valid_scores)
    }
    
    output_path = Path("data/processed/valid_subjects.json")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Validated {result['count']} subjects with Fluid Intelligence scores.")
    return result

def main():
    """
    Main entry point for validation script.
    """
    ensure_directories()
    result = validate_and_aggregate()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
