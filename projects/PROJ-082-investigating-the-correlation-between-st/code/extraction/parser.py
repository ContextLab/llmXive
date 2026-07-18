import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from utils.logger import get_logger, log_fallback

logger = get_logger(__name__)

def parse_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse a single study row, extracting r, n, and tract information."""
    try:
        r_val = float(row.get('r', row.get('effect_size', 0)))
        n_val = int(row.get('n', row.get('sample_size', 0)))
        tract = row.get('tract', row.get('tract_name', ''))
        
        if n_val <= 0:
            logger.warning(f"Invalid sample size in row: {row}")
            return None
        
        return {
            'r': r_val,
            'n': n_val,
            'tract': tract,
            'study_id': row.get('study_id', 'unknown')
        }
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse row: {row}, error: {e}")
        return None

def extract_descriptors(text: str, lexicon: Dict[str, List[str]]) -> List[str]:
    """Extract qualitative descriptors based on lexicon."""
    descriptors = []
    text_lower = text.lower()
    
    for category, terms in lexicon.items():
        for term in terms:
            if term.lower() in text_lower:
                descriptors.append(f"{category}: {term}")
    
    return descriptors

def parse_csv_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parse a CSV file containing study data."""
    results = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = parse_row(row)
            if parsed:
                results.append(parsed)
    return results

def parse_json_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parse a JSON file containing study data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return [parse_row(row) for row in data if parse_row(row)]
    elif isinstance(data, dict) and 'studies' in data:
        return [parse_row(row) for row in data['studies'] if parse_row(row)]
    return []

def parse_input(input_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parse input file (CSV or JSON)."""
    path = Path(input_path)
    if path.suffix == '.csv':
        return parse_csv_file(path)
    elif path.suffix == '.json':
        return parse_json_file(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def extract_descriptors_to_json(input_path: Union[str, Path], lexicon_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Extract descriptors from input using a lexicon."""
    with open(lexicon_path, 'r') as f:
        lexicon = json.load(f)
    
    studies = parse_input(input_path)
    for study in studies:
        # Assume there's a 'notes' or 'description' field
        text = study.get('notes', study.get('description', ''))
        study['qualitative_desc'] = extract_descriptors(text, lexicon)
        study['narrative_pool'] = len(study['qualitative_desc']) == 0
    return studies

def main() -> None:
    """Main entry point for parser."""
    import argparse
    parser = argparse.ArgumentParser(description="Study data parser")
    parser.add_argument("--input", type=str, required=True, help="Input file path")
    parser.add_argument("--output", type=str, required=True, help="Output file path")
    parser.add_argument("--lexicon", type=str, help="Lexicon file path for descriptor extraction")
    args = parser.parse_args()
    
    studies = parse_input(args.input)
    
    if args.lexicon:
        studies = extract_descriptors_to_json(args.input, args.lexicon)
    
    with open(args.output, 'w') as f:
        json.dump(studies, f, indent=2)
    
    print(f"Parsed {len(studies)} studies")

if __name__ == "__main__":
    main()