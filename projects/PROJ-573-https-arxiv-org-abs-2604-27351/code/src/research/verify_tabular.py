"""
Verify tabular dataset availability (selected UCI sets) via HuggingFace datasets.

This script attempts to load specified tabular datasets from HuggingFace,
extracts metadata (variables, size), and logs the verification status.
It updates research.md with a 'Dataset Verification' section.
"""
import os
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if "code" in os.getcwd():
    sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
else:
    # Handle case where run from project root
    sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "code", "..", "..")))

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library not found. Please install it: pip install datasets")
    sys.exit(1)

from src.utils.logging import get_logger

# Configuration for tabular datasets to verify
# Using UCI-derived datasets available on HuggingFace
TABULAR_DATASETS = [
    {
        "name": "UCI_Credit_Card",
        "hf_id": "UCI_Credit_Card",
        "description": "Credit Card Default dataset"
    },
    {
        "name": "UCI_Adult",
        "hf_id": "UCI_Adult",
        "description": "Adult Income dataset"
    },
    {
        "name": "UCI_Bank_Marketing",
        "hf_id": "UCI_Bank_Marketing",
        "description": "Bank Marketing dataset"
    }
]

logger = get_logger(__name__)

def estimate_dataset_size_mb(dataset_name: str, hf_id: str) -> float:
    """
    Estimate dataset size in MB by loading metadata or a small sample.
    Returns 0.0 if estimation fails.
    """
    try:
        # Attempt to load just the info or a small slice to get size
        # Note: Some datasets might not have 'info' directly accessible without loading
        # We try to load the dataset with trust_remote_code=False and check size
        ds = load_dataset(hf_id, split="train", trust_remote_code=False)
        
        # Estimate size based on number of rows and average row size (heuristic)
        # This is an approximation as we don't have the raw file size without download
        num_rows = len(ds)
        # Heuristic: assume ~1KB per row for tabular data with text fields
        estimated_bytes = num_rows * 1024 
        return estimated_bytes / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Could not estimate size for {hf_id}: {e}")
        return 0.0

def compute_dataset_checksum(dataset_name: str, hf_id: str) -> str:
    """
    Compute a checksum of the dataset structure (schema) to ensure consistency.
    Returns a hex string.
    """
    try:
        ds = load_dataset(hf_id, trust_remote_code=False)
        schema_str = str(ds.features)
        return hashlib.sha256(schema_str.encode('utf-8')).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Could not compute checksum for {hf_id}: {e}")
        return "N/A"

def verify_dataset(hf_id: str, timeout: int = 300) -> Dict[str, Any]:
    """
    Attempt to load a dataset and return verification details.
    """
    result = {
        "dataset_name": hf_id,
        "url": f"https://huggingface.co/datasets/{hf_id}",
        "variables": [],
        "size_mb": 0.0,
        "verification_status": "FAILED",
        "error": None
    }

    start_time = time.time()
    try:
        logger.info(f"Verifying dataset: {hf_id}...")
        
        # Load dataset (try 'train' split)
        ds = load_dataset(hf_id, trust_remote_code=False)
        
        # Extract variables (feature names)
        if isinstance(ds, dict):
            # If it's a dict of splits, pick the first one
            first_split = next(iter(ds.values()))
            result["variables"] = list(first_split.features.keys())
        else:
            result["variables"] = list(ds.features.keys())

        # Estimate size
        result["size_mb"] = estimate_dataset_size_mb(hf_id, hf_id)
        
        # Checksum
        result["checksum"] = compute_dataset_checksum(hf_id, hf_id)

        result["verification_status"] = "VERIFIED"
        elapsed = time.time() - start_time
        logger.info(f"Verified {hf_id} in {elapsed:.2f}s. Size: {result['size_mb']:.2f} MB. Variables: {len(result['variables'])}")

    except Exception as e:
        result["error"] = str(e)
        result["verification_status"] = "FAILED"
        logger.error(f"Failed to verify {hf_id}: {e}")

    return result

def generate_verification_table(results: List[Dict[str, Any]]) -> str:
    """
    Generate a markdown table from verification results.
    """
    lines = ["| Dataset Name | URL | Variables | Size (MB) | Status |", "|---|---|---|---|---|"]
    for r in results:
        url = r.get("url", "N/A")
        vars_str = ", ".join(r.get("variables", []))[:50] + ("..." if len(r.get("variables", [])) > 5 else "")
        size = f"{r.get('size_mb', 0):.2f}"
        status = r.get("verification_status", "UNKNOWN")
        lines.append(f"| {r['dataset_name']} | {url} | {vars_str} | {size} | {status} |")
    return "\n".join(lines)

def update_research_md(results: List[Dict[str, Any]], section_title: str = "Dataset Verification"):
    """
    Update research.md with the verification section.
    """
    research_path = Path("code/research.md")
    if not research_path.exists():
        logger.warning(f"research.md not found at {research_path}. Creating a new one.")
        research_path.parent.mkdir(parents=True, exist_ok=True)
        content = "# Research Documentation\n\n"
    else:
        content = research_path.read_text()

    # Find or create the section
    section_header = f"## {section_title}"
    if section_header in content:
        # Split content, replace section
        parts = content.split(section_header)
        # Keep header, replace rest
        new_section_content = f"{section_header}\n\n{generate_verification_table(results)}\n\n"
        # Reconstruct: everything before the header + new section + everything after the old section
        # This is a simple heuristic; assumes the section ends at the next ## or EOF
        # For robustness, we'll just append if we can't find a clean split, but let's try to replace
        # A safer approach for this task: Append to the end if not found, or overwrite if found
        # Let's overwrite the section content between this header and the next header
        lines = content.split('\n')
        new_lines = []
        in_section = False
        section_replaced = False
        
        for i, line in enumerate(lines):
            if line.strip() == section_header:
                in_section = True
                new_lines.append(line)
                new_lines.append("") # blank line
                new_lines.append(generate_verification_table(results))
                new_lines.append("")
                section_replaced = True
                continue
            
            if in_section and line.startswith("## "):
                in_section = False
            
            if not in_section:
                new_lines.append(line)
        
        if section_replaced:
            content = "\n".join(new_lines)
        else:
            # Fallback: append
            content += f"\n{section_header}\n\n{generate_verification_table(results)}\n\n"
    else:
        content += f"\n{section_header}\n\n{generate_verification_table(results)}\n\n"

    research_path.write_text(content)
    logger.info(f"Updated {research_path} with verification results.")

def main():
    logger.info("Starting Tabular Dataset Verification (T002)...")
    results = []

    for dataset_config in TABULAR_DATASETS:
        result = verify_dataset(dataset_config["hf_id"])
        result["dataset_name"] = dataset_config["name"] # Use friendly name
        results.append(result)

    # Update research.md
    update_research_md(results)

    # Print summary
    print("\n" + "="*50)
    print("TABULAR DATASET VERIFICATION SUMMARY")
    print("="*50)
    print(generate_verification_table(results))
    print("="*50)

    # Check if all succeeded
    all_success = all(r["verification_status"] == "VERIFIED" for r in results)
    if not all_success:
        logger.warning("Some datasets failed verification. Check logs.")
        sys.exit(1)
    else:
        logger.info("All tabular datasets verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()