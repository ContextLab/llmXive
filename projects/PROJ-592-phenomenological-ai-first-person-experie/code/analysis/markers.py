"""
Marker analysis module for computing phenomenological marker presence.
"""
from __future__ import annotations
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure we can import from project root
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_marker_dictionaries


class MarkerError(Exception):
    """Custom exception for marker analysis errors."""
    pass


def count_markers_in_text(text: str, markers: List[str]) -> int:
    """Count occurrences of markers in the given text."""
    count = 0
    text_lower = text.lower()
    for marker in markers:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(marker.lower()) + r'\b'
        count += len(re.findall(pattern, text_lower))
    return count


def compute_marker_scores(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute marker scores for a list of reports."""
    markers_dict = get_marker_dictionaries()
    results = []
    
    for report in reports:
        text = report.get("text", "")
        scores = {
            "id": report.get("id", "unknown"),
            "sensory": count_markers_in_text(text, markers_dict.get("sensory", [])),
            "temporal": count_markers_in_text(text, markers_dict.get("temporal", [])),
            "intentional": count_markers_in_text(text, markers_dict.get("intentional", [])),
            "total": 0
        }
        scores["total"] = scores["sensory"] + scores["temporal"] + scores["intentional"]
        results.append(scores)
    
    return results


def run_marker_analysis(input_path: str, output_path: str) -> None:
    """Run marker analysis on generated reports and save results."""
    # Load reports
    reports = []
    input_file = Path(input_path)
    if input_file.exists():
        import json
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                reports = data
            elif isinstance(data, dict) and "reports" in data:
                reports = data["reports"]
    
    if not reports:
        logging.warning(f"No reports found at {input_path}")
        # Create empty output
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return

    scores = compute_marker_scores(reports)
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=2)


def main():
    """Main entry point for marker analysis."""
    import json
    from pathlib import Path

    # Define paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Find all generated report files
    report_files = list(raw_dir.glob("*.json"))
    
    if not report_files:
        logging.warning("No report files found in data/raw/")
        # Create empty marker scores file
        marker_output = processed_dir / "marker_scores.json"
        with open(marker_output, 'w') as f:
            json.dump([], f)
        return

    # Aggregate all reports
    all_reports = []
    for report_file in report_files:
        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_reports.extend(data)
            elif isinstance(data, dict):
                # Handle dict with reports key or single report
                if "reports" in data:
                    all_reports.extend(data["reports"])
                else:
                    all_reports.append(data)

    if not all_reports:
        logging.warning("No valid reports found to analyze.")
        marker_output = processed_dir / "marker_scores.json"
        with open(marker_output, 'w') as f:
            json.dump([], f)
        return

    # Run analysis
    scores = compute_marker_scores(all_reports)
    
    # Save results
    marker_output = processed_dir / "marker_scores.json"
    with open(marker_output, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=2)
    
    logging.info(f"Marker analysis complete. Saved to {marker_output}")
