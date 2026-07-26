import os
import sys
import json
import logging
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_project_root, get_output_path, get_data_path

# Configure logger
logger = logging.getLogger(__name__)

def load_norskov_reference_list(path: Optional[str] = None) -> List[str]:
    """Load the Nørskov 2005 descriptors from a local JSON file."""
    if path is None:
        base = get_project_root()
        path = str(base / "code" / "data" / "norskov_2005_descriptors.json")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Nørskov reference file not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("descriptors", [])

def load_metrics(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the metrics JSON file."""
    if path is None:
        base = get_output_path()
        path = str(base / "metrics.json")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_top_descriptors(path: Optional[str] = None) -> List[str]:
    """Load the top descriptors list from the feature importance output."""
    # Assuming this is stored in a specific file or derived from metrics
    # For this implementation, we look for a specific file or infer from metrics if needed.
    # Based on T034/T035, this might be in a specific json or we reconstruct it.
    # Let's assume a file `outputs/top_descriptors.json` exists or we parse from metrics.
    # Given the task flow, T034 produces a ranking. Let's assume it's saved.
    if path is None:
        base = get_output_path()
        path = str(base / "top_descriptors.json")
    
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback: try to extract from metrics if available
    metrics_path = str(get_output_path() / "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            m = json.load(f)
            if "top_descriptors" in m:
                return m["top_descriptors"]
    
    raise FileNotFoundError("Could not load top descriptors from expected location.")

def normalize_descriptor_name(name: str) -> str:
    """Normalize a descriptor name for comparison (lowercase, strip whitespace)."""
    return name.lower().strip().replace(" ", "_").replace("-", "_")

def compare_with_norskov(top_descriptors: List[str], norskov_list: List[str]) -> Dict[str, Any]:
    """Compare top descriptors against Nørskov list."""
    normalized_top = [normalize_descriptor_name(d) for d in top_descriptors]
    normalized_norskov = [normalize_descriptor_name(d) for d in norskov_list]
    
    matches = []
    for t in normalized_top:
        if t in normalized_norskov:
            matches.append(t)
    
    novel = [d for d in normalized_top if d not in normalized_norskov]
    
    return {
        "matches": matches,
        "novel": novel,
        "match_count": len(matches),
        "novel_count": len(novel)
    }

def generate_comparison_table(comparison_result: Dict[str, Any]) -> str:
    """Generate a markdown table for the comparison."""
    lines = [
        "| Category | Descriptors |",
        "|---|---|"
    ]
    
    matches_str = ", ".join(comparison_result["matches"]) if comparison_result["matches"] else "None"
    novel_str = ", ".join(comparison_result["novel"]) if comparison_result["novel"] else "None"
    
    lines.append(f"| Matches | {matches_str} |")
    lines.append(f"| Novel Findings | {novel_str} |")
    
    return "\n".join(lines)

def get_huggingface_commit_hash(dataset_id: str = "oc/oc20", revision: str = "main") -> str:
    """
    Retrieve the commit hash for the HuggingFace dataset.
    This queries the HuggingFace Hub API to get the commit hash for the specified revision.
    """
    url = f"https://huggingface.co/api/datasets/{dataset_id}/revision/{revision}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # The commit hash is usually under 'sha' or 'id' in the revision object
        if 'sha' in data:
            return data['sha']
        elif 'id' in data:
            return data['id']
        else:
            # Fallback or error if structure unexpected
            logger.warning(f"Unexpected API response structure for {dataset_id}: {data.keys()}")
            return "unknown_commit"
    except requests.RequestException as e:
        logger.error(f"Failed to fetch HuggingFace commit hash: {e}")
        return "fetch_failed"

def get_requirements_hash(req_path: Optional[str] = None) -> str:
    """Compute the SHA-256 hash of the requirements.txt file."""
    if req_path is None:
        base = get_project_root()
        req_path = str(base / "requirements.txt")
    
    if not os.path.exists(req_path):
        logger.warning(f"requirements.txt not found at {req_path}")
        return "requirements_file_missing"
    
    hasher = hashlib.sha256()
    with open(req_path, 'rb') as f:
        # Read in chunks to handle large files if necessary
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def generate_final_report(
    metrics: Dict[str, Any],
    comparison_table: str,
    hf_commit: str,
    req_hash: str,
    sc003_status: str,
    sc003_ratio: float
) -> str:
    """Generate the full final report markdown content."""
    report_lines = [
        "# Final Report: Predicting Catalytic Activity",
        "",
        "## Executive Summary",
        f"This report summarizes the model performance, feature importance, and verification of Success Criterion 003 (SC-003).",
        "",
        "## Model Performance Metrics",
        "```json",
        json.dumps(metrics, indent=2),
        "```",
        "",
        "## SC-003 Verification",
        f"- **Status**: {sc003_status}",
        f"- **Reduced/Full R² Ratio**: {sc003_ratio:.4f}",
        "",
        "## Descriptor Comparison",
        comparison_table,
        "",
        "## Reproducibility Metadata",
        "This section documents the exact data and code versions used to ensure reproducibility.",
        "",
        "### Data Lineage",
        f"- **Dataset**: OC20 (HuggingFace)",
        f"- **Commit Hash**: {hf_commit}",
        "",
        "### Code Lineage",
        f"- **Requirements.txt SHA-256**: {req_hash}",
        "",
        "### Environment",
        "- **Python Version**: 3.10",
        "- **Pipeline Version**: 1.0.0",
    ]
    
    return "\n".join(report_lines)

def save_report(content: str, path: Optional[str] = None) -> str:
    """Save the report content to a file."""
    if path is None:
        base = get_output_path()
        path = str(base / "final_report.md")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Final report saved to {path}")
    return path

def run_report_generation() -> str:
    """
    Orchestrates the generation of the final report.
    This function is the entry point for T040 and T049 logic.
    """
    # Load dependencies
    try:
        metrics = load_metrics()
        top_desc = load_top_descriptors()
        norskov = load_norskov_reference_list()
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        # Return a placeholder or re-raise? Task says fail loudly.
        raise e

    # Compare descriptors
    comparison = compare_with_norskov(top_desc, norskov)
    table = generate_comparison_table(comparison)

    # Get lineage info (T049 specific)
    hf_commit = get_huggingface_commit_hash()
    req_hash = get_requirements_hash()

    # Extract SC-003 info if present in metrics or separate file
    sc003_status = metrics.get("sc003_status", "UNKNOWN")
    sc003_ratio = metrics.get("sc003_ratio", 0.0)
    
    # If not in metrics, try loading from sc003_verification.json
    sc003_path = os.path.join(get_output_path(), "sc003_verification.json")
    if os.path.exists(sc003_path):
        with open(sc003_path, 'r') as f:
            sc_data = json.load(f)
            sc003_status = sc_data.get("status", sc003_status)
            sc003_ratio = sc_data.get("ratio", sc003_ratio)

    # Generate report
    report_content = generate_final_report(
        metrics=metrics,
        comparison_table=table,
        hf_commit=hf_commit,
        req_hash=req_hash,
        sc003_status=sc003_status,
        sc003_ratio=sc003_ratio
    )

    # Save report
    output_path = save_report(report_content)
    
    return output_path

def main():
    """Main entry point for the report generation script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        output_file = run_report_generation()
        print(f"Report generated successfully at: {output_file}")
        return 0
    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())