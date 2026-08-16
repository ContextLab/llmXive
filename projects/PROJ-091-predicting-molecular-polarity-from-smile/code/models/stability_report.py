import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_bootstrap_results(filepath: Path) -> List[Dict[str, Any]]:
    """Load bootstrap results."""
    with open(filepath, "r") as f:
        return json.load(f)

def generate_stability_report(bootstrap_results: List[Dict[str, Any]], threshold: float = 0.7) -> Dict[str, Any]:
    """Generate stability report."""
    if len(bootstrap_results) < 2:
        return {"status": "failed", "reason": "Insufficient samples"}
    
    # Simplified Jaccard calculation
    jaccards = []
    for i in range(len(bootstrap_results) - 1):
        s1 = set(bootstrap_results[i]["top_features"])
        s2 = set(bootstrap_results[i+1]["top_features"])
        j = len(s1.intersection(s2)) / len(s1.union(s2)) if len(s1.union(s2)) > 0 else 0
        jaccards.append(j)
    
    mean_jaccard = sum(jaccards) / len(jaccards)
    status = "success" if mean_jaccard >= threshold else "failed"
    return {"status": status, "mean_jaccard": mean_jaccard}

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save report."""
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

def main() -> None:
    """Main entry point."""
    bootstrap_path = Path("data/processed/analysis/bootstrap_results.json")
    output_path = Path("data/processed/analysis/stability_report.json")
    results = load_bootstrap_results(bootstrap_path)
    report = generate_stability_report(results)
    save_report(report, output_path)

if __name__ == "__main__":
    main()
