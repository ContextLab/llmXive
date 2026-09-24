import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MERGED_DATA_PATH = DATA_PROCESSED_DIR / "merged_data.csv"
DESCRIPTIVE_BASELINE_PATH = DATA_PROCESSED_DIR / "descriptive_baseline.csv"
EXCLUSIONS_PATH = DATA_PROCESSED_DIR / "exclusions.json"

def load_merged_data(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the merged dataset containing baseline and post-intervention data.
    
    Args:
        filepath: Path to the merged CSV file. Defaults to data/processed/merged_data.csv.
        
    Returns:
        List of dictionaries representing rows in the merged dataset.
        
    Raises:
        FileNotFoundError: If the merged data file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if filepath is None:
        filepath = MERGED_DATA_PATH
        
    if not filepath.exists():
        raise FileNotFoundError(f"Merged data file not found at {filepath}")
        
    data = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
                
        if not data:
            logger.warning(f"Merged data file {filepath} is empty.")
            
    except Exception as e:
        logger.error(f"Error reading merged data file: {e}")
        raise
        
    return data

def identify_dropouts(merged_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify participants with missing post-intervention data.
    
    Logic: Filter records where 'post_intervention_value' is NULL, empty string, 
    or explicitly 'NaN'.
    
    Args:
        merged_data: List of dictionaries from the merged dataset.
        
    Returns:
        List of dictionaries representing dropped-out participants.
    """
    dropouts = []
    
    for record in merged_data:
        # Check for various representations of missing data
        post_value = record.get('post_intervention_value')
        
        if post_value is None or post_value == '' or str(post_value).lower() in ['nan', 'na', 'null']:
            # Ensure we have a participant ID
            participant_id = record.get('participant_id')
            if participant_id:
                dropouts.append({
                    'participant_id': participant_id,
                    'reason': 'missing_post_data',
                    'baseline_data': {
                        k: v for k, v in record.items() 
                        if 'post' not in k.lower() and k != 'post_intervention_value'
                    }
                })
                
    return dropouts

def extract_baseline_for_descriptive(merged_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract baseline data for all participants for descriptive statistics.
    
    This includes both participants who completed the post-intervention 
    and those who dropped out.
    
    Args:
        merged_data: List of dictionaries from the merged dataset.
        
    Returns:
        List of dictionaries containing baseline data for all participants.
    """
    baseline_records = []
    seen_ids = set()
    
    for record in merged_data:
        participant_id = record.get('participant_id')
        
        if participant_id and participant_id not in seen_ids:
            seen_ids.add(participant_id)
            # Extract baseline-related fields
            baseline_record = {}
            for key, value in record.items():
                if 'post' not in key.lower() and key != 'post_intervention_value':
                    baseline_record[key] = value
            baseline_records.append(baseline_record)
            
    return baseline_records

def generate_exclusions_json(dropouts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate the exclusions JSON structure.
    
    Args:
        dropouts: List of dropout records from identify_dropouts.
        
    Returns:
        Dictionary conforming to the exclusions schema.
    """
    exclusions = {
        "excluded_participants": [],
        "summary": {
            "total_excluded": len(dropouts),
            "reasons": {}
        }
    }
    
    # Group by reason
    reason_counts = {}
    for dropout in dropouts:
        reason = dropout.get('reason', 'unknown')
        if reason not in reason_counts:
            reason_counts[reason] = 0
        reason_counts[reason] += 1
        
        exclusions["excluded_participants"].append({
            "participant_id": dropout['participant_id'],
            "reason": reason
        })
        
    exclusions["summary"]["reasons"] = reason_counts
    
    return exclusions

def write_exclusions_json(exclusions: Dict[str, Any], filepath: Optional[Path] = None) -> Path:
    """
    Write the exclusions data to a JSON file.
    
    Args:
        exclusions: Dictionary containing exclusion data.
        filepath: Path to the output JSON file. Defaults to data/processed/exclusions.json.
        
    Returns:
        Path to the written file.
    """
    if filepath is None:
        filepath = EXCLUSIONS_PATH
        
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(exclusions, f, indent=2)
        
    logger.info(f"Wrote exclusions to {filepath}")
    return filepath

def write_baseline_csv(baseline_data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Write baseline data to a CSV file for descriptive statistics.
    
    Args:
        baseline_data: List of dictionaries containing baseline data.
        filepath: Path to the output CSV file. Defaults to data/processed/descriptive_baseline.csv.
        
    Returns:
        Path to the written file.
    """
    if filepath is None:
        filepath = DESCRIPTIVE_BASELINE_PATH
        
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if not baseline_data:
        logger.warning("No baseline data to write.")
        filepath.touch()
        return filepath
        
    # Determine all unique keys
    fieldnames = set()
    for record in baseline_data:
        fieldnames.update(record.keys())
    fieldnames = sorted(list(fieldnames))
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(baseline_data)
        
    logger.info(f"Wrote baseline data to {filepath}")
    return filepath

def run_dropout_handling(
    merged_data_path: Optional[Path] = None,
    exclusions_path: Optional[Path] = None,
    baseline_path: Optional[Path] = None
) -> Tuple[Dict[str, Any], Path, Path]:
    """
    Execute the full dropout handling pipeline.
    
    This function:
    1. Loads the merged data
    2. Identifies dropouts
    3. Extracts baseline data for descriptive statistics
    4. Generates and writes the exclusions JSON
    5. Writes the descriptive baseline CSV
    
    Args:
        merged_data_path: Path to merged data CSV. Defaults to data/processed/merged_data.csv.
        exclusions_path: Path to output exclusions JSON. Defaults to data/processed/exclusions.json.
        baseline_path: Path to output baseline CSV. Defaults to data/processed/descriptive_baseline.csv.
        
    Returns:
        Tuple of (exclusions_dict, exclusions_path, baseline_path)
        
    Raises:
        FileNotFoundError: If merged data file does not exist.
    """
    logger.info("Starting dropout handling pipeline...")
    
    # Load merged data
    logger.info(f"Loading merged data from {merged_data_path or MERGED_DATA_PATH}")
    merged_data = load_merged_data(merged_data_path)
    
    if not merged_data:
        logger.warning("Merged data is empty. Creating empty outputs.")
        exclusions = generate_exclusions_json([])
        write_exclusions_json(exclusions, exclusions_path)
        write_baseline_csv([], baseline_path)
        return exclusions, exclusions_path or EXCLUSIONS_PATH, baseline_path or DESCRIPTIVE_BASELINE_PATH
    
    # Identify dropouts
    logger.info("Identifying dropouts...")
    dropouts = identify_dropouts(merged_data)
    logger.info(f"Found {len(dropouts)} dropouts.")
    
    # Extract baseline for descriptive statistics
    logger.info("Extracting baseline data for descriptive statistics...")
    baseline_data = extract_baseline_for_descriptive(merged_data)
    logger.info(f"Extracted baseline data for {len(baseline_data)} participants.")
    
    # Generate and write exclusions
    logger.info("Generating exclusions JSON...")
    exclusions = generate_exclusions_json(dropouts)
    exclusions_path = write_exclusions_json(exclusions, exclusions_path)
    
    # Write baseline CSV
    logger.info("Writing descriptive baseline CSV...")
    baseline_path = write_baseline_csv(baseline_data, baseline_path)
    
    logger.info("Dropout handling pipeline completed successfully.")
    return exclusions, exclusions_path, baseline_path

def main():
    """
    Main entry point for the dropout handling script.
    """
    try:
        exclusions, excl_path, base_path = run_dropout_handling()
        
        print(f"\nPipeline completed successfully!")
        print(f"Exclusions written to: {excl_path}")
        print(f"Descriptive baseline written to: {base_path}")
        print(f"Total participants excluded: {exclusions['summary']['total_excluded']}")
        
        if exclusions['summary']['reasons']:
            print("\nExclusion reasons:")
            for reason, count in exclusions['summary']['reasons'].items():
                print(f"  - {reason}: {count}")
                
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during dropout handling: {e}")
        raise

if __name__ == "__main__":
    main()
