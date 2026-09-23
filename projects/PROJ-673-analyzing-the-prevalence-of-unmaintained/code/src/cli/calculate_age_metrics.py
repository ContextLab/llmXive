"""
CLI module to calculate age metrics for dependencies.
Implements FR-010: Calculate age_in_days, exclude dependencies with missing release metadata from age calculation,
but include them in vulnerability counts.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.
    Handles various formats and returns None for null/empty strings.
    """
    if not date_str or date_str == "null" or date_str.strip() == "":
        return None
    
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try other common formats
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return None

def calculate_age_in_days(release_date: Optional[datetime], reference_date: Optional[datetime] = None) -> Optional[int]:
    """
    Calculate age in days from release_date to reference_date.
    
    FR-010 Implementation:
    - If release_date is None/null, return None (exclude from age calculation)
    - If reference_date is None, use current UTC time
    
    Args:
        release_date: The release date datetime object (can be None)
        reference_date: The reference date for calculation (optional, defaults to now)
    
    Returns:
        Optional[int]: Age in days, or None if release_date is missing
    """
    # FR-010: Exclude dependencies with missing release metadata from age calculation
    if release_date is None:
        return None
    
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)
    
    # Ensure both dates are timezone-aware
    if release_date.tzinfo is None:
        release_date = release_date.replace(tzinfo=timezone.utc)
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=timezone.utc)
    
    delta = reference_date - release_date
    return delta.days

def load_dependencies_from_json(input_path: str) -> List[Dict[str, Any]]:
    """
    Load dependencies data from a JSON file.
    
    Args:
        input_path: Path to the input JSON file
    
    Returns:
        List of dependency dictionaries
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'dependencies' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'dependencies' in data:
        return data['dependencies']
    else:
        raise ValueError("Invalid JSON format: expected a list or dict with 'dependencies' key")

def process_dependencies(dependencies: List[Dict[str, Any]], reference_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Process dependencies to calculate age_in_days and handle missing release metadata.
    
    FR-010 Implementation:
    - Calculate age_in_days for each dependency
    - If release_date is null, age_in_days is set to null
    - vulnerability_count is always populated (even if release_date is null)
    
    Args:
        dependencies: List of dependency dictionaries
        reference_date: Reference date for age calculation (optional)
    
    Returns:
        Processed list of dependencies with age_in_days calculated
    """
    processed = []
    missing_release_count = 0
    
    for dep in dependencies:
        processed_dep = dep.copy()
        
        # Parse release date
        release_date_str = dep.get('release_date') or dep.get('last_release_date')
        release_date = parse_date(release_date_str)
        
        # FR-010: Calculate age_in_days
        # If release_date is None, age_in_days will be None (excluded from age calculation)
        age_in_days = calculate_age_in_days(release_date, reference_date)
        processed_dep['age_in_days'] = age_in_days
        
        # Track missing release metadata
        if age_in_days is None:
            missing_release_count += 1
        
        # FR-010: Ensure vulnerability_count is populated even if release_date is null
        # The vulnerability count comes from audit data and should be independent of release metadata
        if 'vulnerability_count' not in processed_dep:
            processed_dep['vulnerability_count'] = 0
        
        processed.append(processed_dep)
    
    logger.info(f"Processed {len(processed)} dependencies, {missing_release_count} with missing release metadata")
    return processed

def write_csv(dependencies: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write processed dependencies to a CSV file.
    
    Args:
        dependencies: List of processed dependency dictionaries
        output_path: Path to the output CSV file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        'name', 'version', 'age_in_days', 'vulnerability_count',
        'release_date', 'last_commit_date', 'category'
    ]
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(dependencies)
    
    logger.info(f"Wrote {len(dependencies)} dependencies to {output_path}")

def main():
    """
    Main entry point for the age metrics calculation CLI.
    
    Usage:
        python -m src.cli.calculate_age_metrics --input data/raw/packages_seed.json --output data/processed/dependencies_raw.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate age metrics for dependencies')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file path')
    parser.add_argument('--output', '-o', required=True, help='Output CSV file path')
    parser.add_argument('--reference-date', '-r', help='Reference date for age calculation (ISO format)')
    
    args = parser.parse_args()
    
    try:
        # Load dependencies
        logger.info(f"Loading dependencies from {args.input}")
        dependencies = load_dependencies_from_json(args.input)
        
        # Parse reference date if provided
        reference_date = None
        if args.reference_date:
            reference_date = parse_date(args.reference_date)
            if reference_date is None:
                logger.error(f"Invalid reference date format: {args.reference_date}")
                sys.exit(1)
        
        # Process dependencies (calculate age_in_days)
        logger.info("Calculating age metrics")
        processed = process_dependencies(dependencies, reference_date)
        
        # Write to CSV
        logger.info(f"Writing results to {args.output}")
        write_csv(processed, args.output)
        
        # Verify output
        if not Path(args.output).exists():
            logger.error("Output file was not created!")
            sys.exit(1)
        
        logger.info("Age metrics calculation completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()