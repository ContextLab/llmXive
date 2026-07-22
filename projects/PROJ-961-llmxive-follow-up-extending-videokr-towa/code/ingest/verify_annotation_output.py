import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.config import get_project_root, get_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_annotation_output(
    output_path: Path, 
    expected_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Verify the structure and content of the annotation output.
    
    Args:
        output_path: Path to the CSV file.
        expected_columns: Optional list of expected column names.
        
    Returns:
        Dictionary with verification results.
    """
    results = {
        "valid": True,
        "errors": [],
        "record_count": 0,
        "columns": []
    }
    
    if not output_path.exists():
        results["valid"] = False
        results["errors"].append(f"File not found: {output_path}")
        return results
        
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            results["columns"] = reader.fieldnames or []
            records = list(reader)
            results["record_count"] = len(records)
            
            if expected_columns:
                missing = set(expected_columns) - set(results["columns"])
                if missing:
                    results["valid"] = False
                    results["errors"].append(f"Missing columns: {missing}")
                    
            # Check for required fields in records
            if records:
                first_record = records[0]
                if 'chain_length' not in first_record:
                    results["valid"] = False
                    results["errors"].append("Missing 'chain_length' column")
                if 'chain_bin' not in first_record:
                    results["valid"] = False
                    results["errors"].append("Missing 'chain_bin' column")
                    
    except Exception as e:
        results["valid"] = False
        results["errors"].append(f"Error reading file: {str(e)}")
        
    return results

def main() -> None:
    """Main entry point for output verification."""
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    
    expected_columns = ['id', 'question', 'answer', 'chain_length', 'chain_bin', 'correctness']
    
    results = verify_annotation_output(output_path, expected_columns)
    
    if results["valid"]:
        logger.info("Annotation output verified successfully.")
        logger.info(f"Record count: {results['record_count']}")
    else:
        logger.error("Annotation output verification failed.")
        for error in results["errors"]:
            logger.error(f"  - {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()