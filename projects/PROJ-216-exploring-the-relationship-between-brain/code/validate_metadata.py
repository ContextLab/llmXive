import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/metadata_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def load_aggregated_subjects(path: str) -> List[Dict[str, Any]]:
    """
    Load the aggregated subjects JSON file generated during data download/verification.
    
    Args:
        path: Path to the aggregated subjects JSON file.
        
    Returns:
        List of subject dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Aggregated subjects file not found: {path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    return data.get('subjects', [])

def validate_age_gender_metadata(subjects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that subjects with Fluid Intelligence scores have age and gender metadata.
    
    This function checks each subject in the list. If a subject has a Fluid Intelligence
    score, it verifies that 'age' and 'gender' fields are present and non-empty.
    
    Args:
        subjects: List of subject dictionaries containing metadata and scores.
        
    Returns:
        Dictionary containing validation results:
            - 'valid_count': Number of subjects with valid metadata
            - 'invalid_count': Number of subjects with missing/invalid metadata
            - 'missing_age': List of subject IDs missing age
            - 'missing_gender': List of subject IDs missing gender
            - 'missing_fluid_intelligence': List of subject IDs with no Fluid Intelligence score
    """
    result = {
        'valid_count': 0,
        'invalid_count': 0,
        'missing_age': [],
        'missing_gender': [],
        'missing_fluid_intelligence': []
    }
    
    for subject in subjects:
        subject_id = subject.get('subject_id', 'UNKNOWN')
        has_fluid_intelligence = subject.get('has_fluid_intelligence', False)
        
        if not has_fluid_intelligence:
            result['missing_fluid_intelligence'].append(subject_id)
            continue
        
        # Check for age
        age = subject.get('age')
        if age is None or (isinstance(age, str) and age.strip() == ''):
            result['missing_age'].append(subject_id)
            result['invalid_count'] += 1
            continue
        
        # Check for gender
        gender = subject.get('gender')
        if gender is None or (isinstance(gender, str) and gender.strip() == ''):
            result['missing_gender'].append(subject_id)
            result['invalid_count'] += 1
            continue
        
        # If we reach here, both age and gender are present for a subject with FI score
        result['valid_count'] += 1
        
    return result

def write_validation_log(validation_result: Dict[str, Any], output_path: str):
    """
    Write the validation results to a log file and summary JSON.
    
    Args:
        validation_result: Dictionary containing validation results.
        output_path: Path to the output log file.
    """
    log_path = Path(output_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write("=== Age/Gender Metadata Validation Report ===\n\n")
        f.write(f"Total subjects with Fluid Intelligence scores checked: {validation_result['valid_count'] + validation_result['invalid_count']}\n")
        f.write(f"Valid metadata (age + gender present): {validation_result['valid_count']}\n")
        f.write(f"Invalid metadata (missing age or gender): {validation_result['invalid_count']}\n\n")
        
        if validation_result['missing_age']:
            f.write(f"Subjects missing age metadata ({len(validation_result['missing_age'])}):\n")
            for sid in validation_result['missing_age']:
                f.write(f"  - {sid}\n")
            f.write("\n")
        
        if validation_result['missing_gender']:
            f.write(f"Subjects missing gender metadata ({len(validation_result['missing_gender'])}):\n")
            for sid in validation_result['missing_gender']:
                f.write(f"  - {sid}\n")
            f.write("\n")
        
        if validation_result['missing_fluid_intelligence']:
            f.write(f"Subjects without Fluid Intelligence scores ({len(validation_result['missing_fluid_intelligence'])}):\n")
            for sid in validation_result['missing_fluid_intelligence']:
                f.write(f"  - {sid}\n")
            f.write("\n")
        
        # Summary JSON for programmatic access
        summary_path = log_path.parent / "metadata_validation_summary.json"
        with open(summary_path, 'w') as json_f:
            json.dump(validation_result, json_f, indent=2)
        
        logger.info(f"Validation summary written to {summary_path}")

def main():
    """
    Main entry point for the metadata validation script.
    
    This script:
    1. Loads the aggregated subjects JSON from data/processed/aggregated_subjects.json
    2. Validates that subjects with Fluid Intelligence scores have age and gender metadata
    3. Writes the validation log to data/processed/metadata_validation.log
    4. Writes a summary JSON to data/processed/metadata_validation_summary.json
    5. Exits with code 1 if any subjects with Fluid Intelligence scores are missing metadata
    """
    # Define paths
    base_dir = Path(__file__).parent.parent
    aggregated_path = base_dir / "data" / "processed" / "aggregated_subjects.json"
    log_path = base_dir / "data" / "processed" / "metadata_validation.log"
    
    logger.info(f"Loading aggregated subjects from {aggregated_path}")
    
    try:
        subjects = load_aggregated_subjects(str(aggregated_path))
    except FileNotFoundError as e:
        logger.error(f"Failed to load subjects: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in subjects file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(subjects)} subjects")
    
    # Validate metadata
    logger.info("Validating age/gender metadata for subjects with Fluid Intelligence scores...")
    validation_result = validate_age_gender_metadata(subjects)
    
    # Write results
    write_validation_log(validation_result, str(log_path))
    
    # Check for failures
    if validation_result['invalid_count'] > 0:
        logger.error(f"Validation FAILED: {validation_result['invalid_count']} subjects with Fluid Intelligence scores are missing age or gender metadata.")
        if validation_result['missing_age']:
            logger.error(f"Missing age for: {', '.join(validation_result['missing_age'])}")
        if validation_result['missing_gender']:
            logger.error(f"Missing gender for: {', '.join(validation_result['missing_gender'])}")
        sys.exit(1)
    
    logger.info(f"Validation PASSED: All {validation_result['valid_count']} subjects with Fluid Intelligence scores have complete age/gender metadata.")
    sys.exit(0)

if __name__ == "__main__":
    main()
