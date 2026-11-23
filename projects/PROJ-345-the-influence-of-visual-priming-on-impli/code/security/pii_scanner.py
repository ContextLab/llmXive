import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Define PII patterns using regex
# Note: This is a heuristic scanner. For production, use a dedicated library like presidio-analyzer
# if installed, but the regex fallback is required for robustness.
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_us": re.compile(r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

class PIIResult:
    def __init__(self, leak_type: str, location: str, context: str):
        self.leak_type = leak_type
        self.location = location
        self.context = context

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.leak_type,
            "location": self.location,
            "context": self.context
        }

def scan_text_for_pii(text: str, file_path: str = "unknown") -> List[PIIResult]:
    """
    Scan a string for PII patterns.
    """
    results = []
    for p_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            # Context: snippet around the match
            start = text.find(str(match))
            end = start + len(str(match))
            context = text[max(0, start-20):min(len(text), end+20)]
            results.append(PIIResult(p_type, file_path, context))
    return results

def scan_csv_file(file_path: Path) -> List[PIIResult]:
    """
    Scan a CSV file for PII.
    """
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_idx, row in enumerate(reader):
                for col_idx, cell in enumerate(row):
                    cell_results = scan_text_for_pii(str(cell), f"{file_path}:{row_idx}:{col_idx}")
                    results.extend(cell_results)
    except Exception as e:
        logging.error(f"Error scanning CSV {file_path}: {e}")
    return results

def scan_json_file(file_path: Path) -> List[PIIResult]:
    """
    Scan a JSON file for PII.
    """
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convert to string to scan
            text_data = json.dumps(data)
            results = scan_text_for_pii(text_data, str(file_path))
    except Exception as e:
        logging.error(f"Error scanning JSON {file_path}: {e}")
    return results

def scan_directory_for_pii(directory_path: str) -> Dict[str, Any]:
    """
    Recursively scan a directory for PII in CSV and JSON files.
    Returns a dict with schema {"leaks": [{"type": str, "location": str}]}.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Scanning directory {directory_path} for PII...")
    
    all_leaks = []
    dir_path = Path(directory_path)
    
    if not dir_path.exists():
        logger.warning(f"Directory {directory_path} does not exist.")
        return {"leaks": []}

    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            if file_path.suffix.lower() == '.csv':
                leaks = scan_csv_file(file_path)
                all_leaks.extend(leaks)
            elif file_path.suffix.lower() == '.json':
                leaks = scan_json_file(file_path)
                all_leaks.extend(leaks)
            elif file_path.suffix.lower() == '.txt':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        leaks = scan_text_for_pii(content, str(file_path))
                        all_leaks.extend(leaks)
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")

    # Format output as required: {"leaks": [{"type": ..., "location": ...}]}
    formatted_leaks = [
        {"type": leak.leak_type, "location": leak.location}
        for leak in all_leaks
    ]

    logger.info(f"Scan complete. Found {len(formatted_leaks)} potential leaks.")
    return {"leaks": formatted_leaks}

def generate_security_report(results: Dict[str, Any], output_path: Path):
    """
    Save the security report to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Security report saved to {output_path}")

def run_pii_security_check(data_dir: str, output_file: str) -> Dict[str, Any]:
    """
    Main entry point for running the PII check on a specific directory.
    """
    result = scan_directory_for_pii(data_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_security_report(result, output_path)
    return result

def main():
    """
    CLI entry point for the PII scanner.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Scan for PII in data directories.")
    parser.add_argument('--dir', type=str, required=True, help='Directory to scan')
    parser.add_argument('--output', type=str, default='reports/pii_scan.json', help='Output JSON path')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    run_pii_security_check(args.dir, args.output)

if __name__ == "__main__":
    main()
