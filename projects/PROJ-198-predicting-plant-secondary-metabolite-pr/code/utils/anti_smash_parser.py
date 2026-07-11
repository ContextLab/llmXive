"""
Utilities for parsing antiSMASH JSON output.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import pandas as pd

logger = logging.getLogger(__name__)

def parse_anti_smash_json(json_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse an antiSMASH JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)

def extract_bgc_summary(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract BGC summary from parsed JSON."""
    # Structure depends on antiSMASH version, this is a generic extractor
    clusters = data.get('clusters', [])
    summary = []
    for c in clusters:
        summary.append({
            'type': c.get('type', 'unknown'),
            'confidence': c.get('confidence', 0.0),
            'start': c.get('start', 0),
            'end': c.get('end', 0)
        })
    return summary

def bgc_summary_to_dataframe(summary: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert BGC summary list to DataFrame."""
    return pd.DataFrame(summary)

def get_bgc_counts_by_type(summary: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count BGCs by type."""
    counts = {}
    for item in summary:
        t = item.get('type', 'unknown')
        counts[t] = counts.get(t, 0) + 1
    return counts

def parse_anti_smash_directory(dir_path: Union[str, Path]) -> Dict[str, pd.DataFrame]:
    """Parse all JSON files in an antiSMASH output directory."""
    results = {}
    dir_path = Path(dir_path)
    for json_file in dir_path.glob("*.json"):
        if "summary" in str(json_file):
            data = parse_anti_smash_json(json_file)
            summary = extract_bgc_summary(data)
            df = bgc_summary_to_dataframe(summary)
            results[json_file.stem] = df
    return results

def main():
    """CLI entry point for parser."""
    pass
