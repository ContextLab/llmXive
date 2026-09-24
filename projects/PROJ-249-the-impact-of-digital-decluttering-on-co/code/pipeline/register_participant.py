import os
import csv
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from existing API surface
from code.scoring.id_generator import validate_id_format, generate_sequence_ids, get_next_available_id, IDGenerator
from code.config.env_config import get_path

# Pattern for participant IDs: P\d{3}
PARTICIPANT_ID_PATTERN = re.compile(r'^P\d{3}$')

def validate_recruitment_id(recruitment_id: str) -> bool:
    """
    Validate that a recruitment_id is a non-empty string.
    
    Args:
        recruitment_id: The recruitment ID to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If the recruitment_id is invalid
    """
    if not isinstance(recruitment_id, str) or not recruitment_id.strip():
        raise ValueError(f"recruitment_id must be a non-empty string, got: {recruitment_id}")
    return True

def validate_consent_timestamp(timestamp_str: str) -> bool:
    """
    Validate that a consent_timestamp is a valid ISO format timestamp.
    
    Args:
        timestamp_str: The timestamp string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If the timestamp is invalid
    """
    try:
        # Try parsing as ISO format
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid consent_timestamp format: {timestamp_str}. Expected ISO format.") from e

def validate_demographic_hash(hash_value: str) -> bool:
    """
    Validate that a demographic_hash is a non-empty string.
    
    Args:
        hash_value: The hash value to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If the hash is invalid
    """
    if not isinstance(hash_value, str) or not hash_value.strip():
        raise ValueError(f"demographic_hash must be a non-empty string, got: {hash_value}")
    return True

def load_recruitment_csv(input_path: str) -> List[Dict[str, Any]]:
    """
    Load recruitment data from a CSV file.
    
    This function implements the "Fail Loudly" principle: if the file does not exist
    or is malformed, it raises an exception immediately rather than falling back to
    synthetic data.
    
    Args:
        input_path: Path to the recruitment CSV file
        
    Returns:
        List of dictionaries containing recruitment records
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the file is malformed or missing required columns
    """
    path = Path(input_path)
    
    # CRITICAL: Fail loudly if file does not exist - NO fallback to synthetic
    if not path.exists():
        raise FileNotFoundError(
            f"Recruitment file not found: {input_path}. "
            "The pipeline requires real recruitment data. Do not use synthetic fallbacks."
        )
    
    records = []
    required_columns = {'recruitment_id', 'consent_timestamp', 'demographic_hash'}
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            if reader.fieldnames is None:
                raise ValueError(f"CSV file is empty or has no headers: {input_path}")
            
            header_set = set(reader.fieldnames)
            missing = required_columns - header_set
            if missing:
                raise ValueError(
                    f"CSV file missing required columns: {missing}. "
                    f"Found: {header_set}"
                )
            
            for row_num, row in enumerate(reader, start=2):
                # Validate each row - fail loudly on bad data
                try:
                    validate_recruitment_id(row['recruitment_id'])
                    validate_consent_timestamp(row['consent_timestamp'])
                    validate_demographic_hash(row['demographic_hash'])
                    records.append(row)
                except ValueError as e:
                    raise ValueError(f"Error in row {row_num}: {e}") from e
                    
    except csv.Error as e:
        raise ValueError(f"Failed to parse CSV file {input_path}: {e}") from e
    
    if not records:
        raise ValueError(f"CSV file {input_path} contains no data rows")
        
    return records

def register_participant(recruitment_id: str, participant_id: str, status: str = 'registered') -> Dict[str, Any]:
    """
    Create a participant registry record.
    
    Args:
        recruitment_id: The original recruitment ID
        participant_id: The assigned pseudonymous ID (must match P\\d{3} pattern)
        status: Registration status (default: 'registered')
        
    Returns:
        Dictionary representing the registry record
        
    Raises:
        ValueError: If participant_id format is invalid
    """
    if not validate_id_format(participant_id):
        raise ValueError(
            f"Invalid participant_id format: {participant_id}. "
            "Must match pattern P\\d{3} (e.g., P001, P002)."
        )
    
    return {
        'participant_id': participant_id,
        'recruitment_id': recruitment_id,
        'status': status,
        'registration_timestamp': datetime.utcnow().isoformat()
    }

def check_duplicate_recruitment_ids(records: List[Dict[str, Any]]) -> List[str]:
    """
    Check for duplicate recruitment IDs in the input data.
    
    Args:
        records: List of recruitment records
        
    Returns:
        List of duplicate recruitment IDs
    """
    seen = set()
    duplicates = set()
    
    for record in records:
        rid = record['recruitment_id']
        if rid in seen:
            duplicates.add(rid)
        seen.add(rid)
        
    return list(duplicates)

def write_registry_csv(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the participant registry to a CSV file.
    
    Args:
        records: List of registry records
        output_path: Path to the output CSV file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['participant_id', 'recruitment_id', 'status', 'registration_timestamp']
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def run_registration_pipeline(input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the complete participant registration pipeline.
    
    This function:
    1. Loads recruitment data from the input CSV
    2. Validates all records (fail loudly on errors)
    3. Checks for duplicate recruitment IDs
    4. Assigns pseudonymous IDs using the ID generator
    5. Writes the registry to the output CSV
    
    Args:
        input_path: Path to the recruitment CSV
        output_path: Path for the output registry CSV (optional, defaults to data/raw/participant_registry.csv)
        
    Returns:
        Dictionary with pipeline results
        
    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If data validation fails
    """
    if output_path is None:
        output_path = get_path('data/raw/participant_registry.csv')
    
    # Load real data - will raise if file missing or malformed
    print(f"Loading recruitment data from: {input_path}")
    records = load_recruitment_csv(input_path)
    print(f"Loaded {len(records)} recruitment records")
    
    # Check for duplicates
    duplicates = check_duplicate_recruitment_ids(records)
    if duplicates:
        raise ValueError(
            f"Duplicate recruitment IDs found: {duplicates}. "
            "Each recruitment_id must be unique."
        )
    
    # Initialize ID generator
    id_generator = IDGenerator()
    
    # Register each participant
    registry_records = []
    for record in records:
        recruitment_id = record['recruitment_id']
        
        # Generate or load next available ID
        participant_id = id_generator.get_next_available_id()
        
        # Create registry record
        registry_record = register_participant(
            recruitment_id=recruitment_id,
            participant_id=participant_id,
            status='registered'
        )
        registry_records.append(registry_record)
        
        print(f"Registered: {recruitment_id} -> {participant_id}")
    
    # Write output
    write_registry_csv(registry_records, output_path)
    print(f"Registry written to: {output_path}")
    
    return {
        'input_path': input_path,
        'output_path': output_path,
        'total_registered': len(registry_records),
        'status': 'success'
    }

def main():
    """
    Main entry point for the register_participant script.
    
    Usage:
        python code/pipeline/register_participant.py --input <recruitment.csv> --output <registry.csv>
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Register participants from recruitment CSV and assign pseudonymous IDs'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input recruitment CSV file'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Path to output registry CSV file (default: data/raw/participant_registry.csv)'
    )
    
    args = parser.parse_args()
    
    try:
        result = run_registration_pipeline(args.input, args.output)
        print("\n=== Registration Pipeline Complete ===")
        print(f"Total participants registered: {result['total_registered']}")
        print(f"Output file: {result['output_path']}")
        return 0
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}", file=sys.stderr)
        print("The pipeline requires real recruitment data. Please ensure the input file exists.", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"\n[ERROR] Validation failed: {e}", file=sys.stderr)
        print("The input data is invalid. Please check the recruitment file.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
