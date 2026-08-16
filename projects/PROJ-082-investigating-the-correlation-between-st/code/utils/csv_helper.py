"""
Helper for CSV writing to ensure compatibility with T013 output format.
"""
import csv
from pathlib import Path
from typing import List, Dict

def write_studies_csv(path: Path, studies: List[Dict[str, str]]):
    """Write a list of study dicts to CSV with standard headers."""
    if not studies:
        # Write empty file with headers if no data
        headers = ["author", "year", "tract", "r", "n", "qualitative_desc", "narrative_pool"]
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return

    headers = list(studies[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(studies)