import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Ensure the code directory is in the path for imports if run as a script
# but rely on the project structure for module imports.
# We assume this script is run from the project root.

def load_extracted_params(filepath: str) -> List[Dict[str, Any]]:
    """Load the extracted parameters from the JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle case where the file contains a list directly or a dict with a key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Common pattern in these pipelines is a key like 'records' or 'data'
        # If not found, try to return the dict itself if it looks like a record
        # But spec implies a list of records.
        for key in ['records', 'data', 'entries']:
            if key in data:
                return data[key]
        # Fallback: if it's a single record wrapped in a dict, wrap it
        return [data]
    else:
        raise ValueError("Unexpected data format in extracted_params.json")

def generate_extraction_stats(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Generate extraction statistics based on the status field in the extracted data.
    
    Calculates:
    - success_rate: fraction of records with status 'success' (or not in failure categories)
    - failure_reasons: counts of 'paywalled', 'unparseable', 'insufficient data'
    
    Args:
        input_path: Path to data/processed/extracted_params.json
        output_path: Path to data/processed/extraction_stats.json
        
    Returns:
        The stats dictionary.
    """
    records = load_extracted_params(input_path)
    
    if not records:
        stats = {
            "success_rate": 0.0,
            "failure_reasons": {
                "paywalled": 0,
                "unparseable": 0,
                "insufficient data": 0
            },
            "total_records": 0
        }
        # Write output even if empty
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        return stats

    failure_counts = {
        "paywalled": 0,
        "unparseable": 0,
        "insufficient data": 0
    }
    
    total = len(records)
    success_count = 0
    
    for record in records:
        status = record.get('status', '').lower()
        
        if status == 'success':
            success_count += 1
        elif status == 'paywalled':
            failure_counts['paywalled'] += 1
        elif status == 'unparseable':
            failure_counts['unparseable'] += 1
        elif status == 'insufficient data':
            failure_counts['insufficient data'] += 1
        else:
            # Treat unknown statuses as failures or log warning?
            # Based on T024, only specific statuses are expected.
            # We'll count unknowns as 'unparseable' for safety or ignore.
            # Let's log a warning but not count in specific buckets unless specified.
            # To be safe, we count it as a failure but not in the specific buckets
            # unless the logic implies only these 3 exist.
            # The task asks for counts of these 3 specifically.
            pass
    
    # Calculate success rate
    # Success is typically when data was extracted (status == 'success')
    # However, sometimes 'abstract' source is still success. 
    # Assuming 'success' status is the target.
    success_rate = success_count / total if total > 0 else 0.0
    
    stats = {
        "success_rate": round(success_rate, 4),
        "failure_reasons": failure_counts,
        "total_records": total,
        "success_count": success_count
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    return stats

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / "data" / "processed" / "extracted_params.json"
    output_file = project_root / "data" / "processed" / "extraction_stats.json"
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info(f"Loading data from {input_file}")
    
    try:
        stats = generate_extraction_stats(str(input_file), str(output_file))
        logger.info(f"Extraction statistics generated successfully: {stats}")
        logger.info(f"Output written to {output_file}")
        
        # Print summary to stdout for immediate verification
        print(f"Total Records: {stats['total_records']}")
        print(f"Success Rate: {stats['success_rate']:.2%}")
        print(f"Failure Reasons: {stats['failure_reasons']}")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()