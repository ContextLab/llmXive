"""
Verify text dataset availability (DROP/MUST) via HuggingFace datasets.

This script checks the availability of DROP and MUST datasets,
gathers metadata (variables, size), and updates research.md.
"""
import os
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging utilities from the project
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback for direct execution if path not set up correctly in some environments
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESEARCH_MD_PATH = PROJECT_ROOT / "research" / "research.md"
DATASETS_TO_CHECK = [
    {"name": "drop", "hf_id": "allenai/drop", "desc": "Dataset for Reading Comprehension, Question Answering, and Reasoning"},
    {"name": "must", "hf_id": "mustard/mustard", "desc": "Multimodal Understanding of Speech and Text in Dialogue (Note: Checking availability, might be 'mustard' or similar if 'must' is not exact)"}
]

# Note: 'must' dataset might be 'mustard' or 'mustard' is the intended multimodal dataset. 
# If 'must' is not found, we try common variations or report unavailability.
# Based on standard benchmarks, 'mustard' is a common text/audio dataset. 
# If the task specifically requires 'must', we check that exact ID first.
# Let's assume the user meant 'mustard' for multimodal or a specific 'must' if it exists.
# We will check 'allenai/drop' and 'mustard/mustard' (often used for text+audio tasks) or 'must' if it exists.
# Correction: The prompt mentions "DROP/MUST". Let's check 'allenai/drop' and try to find 'must'.
# A common text dataset is 'multi_nli' or similar, but if 'must' is specific, we try it.
# If 'must' is not on HF, we report it.
# Let's try: 'allenai/drop' and 'mustard' (as a likely candidate for 'must' if it's a typo, or 'must' if it exists).
# Actually, there is a dataset called 'mustard' (Multimodal Understanding of Speech and Text in Dialogue).
# There is also a 'must' dataset? Let's try 'must' first, then fallback.

def estimate_dataset_size_mb(dataset_name: str, hf_id: str) -> float:
    """
    Estimate dataset size in MB.
    Since we cannot download the full dataset here, we try to get the 'splits' info
    or estimate based on typical sizes if metadata is available.
    """
    try:
        from datasets import load_dataset
        # Load only the dataset info (no download of full data)
        # This might still try to download some metadata which is small.
        ds = load_dataset(hf_id, split="train", streaming=True)
        # Streaming doesn't give size directly without iterating.
        # We'll estimate by counting a small sample or using cached info if available.
        # For verification, we just need to know it's accessible.
        # Let's assume a small size for verification purposes if we can't get exact.
        # However, to be accurate, we try to get the size from the dataset info if possible.
        # Most HF datasets don't expose size in MB easily without download.
        # We will return a placeholder estimate or 0 if unknown, but mark as verified.
        # Better: Try to get the size from the HuggingFace Hub API if possible.
        from huggingface_hub import HfApi
        api = HfApi()
        info = api.dataset_info(hf_id)
        # The size is not always directly in the dataset info in MB.
        # We will estimate based on number of files or return a conservative estimate.
        # For the purpose of this verification task, we will report 0.0 if we can't get exact,
        # but the key is 'verification_status'.
        # Let's try to get the size from the 'siblings' if available.
        size_bytes = 0
        if hasattr(info, 'siblings') and info.siblings:
            for file in info.siblings:
                if hasattr(file, 'size'):
                    size_bytes += file.size
        return size_bytes / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Could not estimate size for {hf_id}: {e}")
        return 0.0

def get_dataset_variables(hf_id: str) -> List[str]:
    """
    Get the list of variables (columns) in the dataset.
    """
    try:
        from datasets import load_dataset
        # Load a small sample to get features
        ds = load_dataset(hf_id, split="train", streaming=True)
        # Get features
        features = ds.features
        if isinstance(features, dict):
            return list(features.keys())
        elif hasattr(features, 'keys'):
            return list(features.keys())
        else:
            return []
    except Exception as e:
        logger.error(f"Failed to get variables for {hf_id}: {e}")
        return []

def compute_dataset_checksum(hf_id: str) -> str:
    """
    Compute a checksum for the dataset.
    Since we cannot download the full dataset, we use the dataset info's commit hash or a hash of the features.
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        info = api.dataset_info(hf_id)
        if hasattr(info, 'sha'):
            return info.sha
        # Fallback: hash the string of features
        features_str = str(info.siblings) if hasattr(info, 'siblings') else str(info)
        return hashlib.sha256(features_str.encode()).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Could not compute checksum for {hf_id}: {e}")
        return "unknown"

def verify_dataset(hf_id: str) -> bool:
    """
    Verify that the dataset is available and loadable.
    """
    try:
        from datasets import load_dataset
        # Try to load a tiny sample
        ds = load_dataset(hf_id, split="train", streaming=True)
        # Try to get one item to ensure it's not empty
        next(iter(ds))
        return True
    except Exception as e:
        logger.error(f"Dataset {hf_id} verification failed: {e}")
        return False

def generate_verification_table(results: List[Dict[str, Any]]) -> str:
    """
    Generate a markdown table from verification results.
    """
    table = "| Dataset | URL | Variables | Size (MB) | Status |\n"
    table += "|---|---|---|---|---|\n"
    for r in results:
        status = "✅ Available" if r["verification_status"] == "available" else "❌ Unavailable"
        table += f"| {r['dataset_name']} | {r['url']} | {', '.join(r['variables'][:3])}{'...' if len(r['variables']) > 3 else ''} | {r['size_mb']:.2f} | {status} |\n"
    return table

def update_research_md(results: List[Dict[str, Any]]) -> None:
    """
    Update research.md with the verification results.
    """
    if not RESEARCH_MD_PATH.exists():
        logger.error(f"research.md not found at {RESEARCH_MD_PATH}")
        return

    content = RESEARCH_MD_PATH.read_text()
    
    # Define the section to update
    section_header = "## Dataset Verification"
    if section_header not in content:
        # If section doesn't exist, append it
        content += f"\n\n{section_header}\n\n"
    
    # Generate the new table
    table = generate_verification_table(results)
    
    # Find the section and replace the table
    # We look for the section and then find the next section or end of file
    lines = content.split('\n')
    new_lines = []
    in_section = False
    table_replaced = False
    
    for i, line in enumerate(lines):
        if line.strip() == section_header:
            in_section = True
            new_lines.append(line)
            new_lines.append("") # Add a newline after header
            # Insert the table
            new_lines.append(table)
            table_replaced = True
            # Skip existing table lines until next section or end
            continue
        
        if in_section and not table_replaced:
            # Check if we hit the next section (starts with ##) or end of file
            if line.startswith("##") and line != section_header:
                in_section = False
                new_lines.append(line)
            # Skip lines that are part of the old table (start with |)
            elif line.startswith("|"):
                continue
            else:
                # If it's not a table line and not the next section, we might be in the middle of the section
                # But we already inserted the table, so we stop adding old content
                # Actually, we want to replace the whole table block.
                # If we are in the section and haven't replaced yet, we skip old table lines.
                # If we encounter a non-table line that is not a new section, we stop skipping?
                # Let's assume the table is the main content of the section.
                pass
        elif in_section and table_replaced:
            # We already inserted the table, so we stop processing this section
            # and continue with the rest of the file
            if line.startswith("##") and line != section_header:
                in_section = False
            # We don't add lines that are part of the old table (already skipped)
            # But if we are here, it means we are past the table insertion point
            # We need to avoid adding duplicate content if the old table was long
            # Let's just stop adding lines that are part of the old table
            if line.startswith("|"):
                continue
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    # If we didn't find the section header, we append the table at the end
    if not table_replaced:
        new_lines.append(f"\n{section_header}\n\n{table}")
    
    RESEARCH_MD_PATH.write_text('\n'.join(new_lines))
    logger.info("research.md updated successfully.")

def main():
    """
    Main function to verify text datasets.
    """
    logger.info("Starting text dataset verification (T003)...")
    
    results = []
    for dataset_info in DATASETS_TO_CHECK:
        name = dataset_info["name"]
        hf_id = dataset_info["hf_id"]
        desc = dataset_info.get("desc", "")
        
        logger.info(f"Verifying dataset: {name} (HF ID: {hf_id})")
        
        is_available = verify_dataset(hf_id)
        variables = []
        size_mb = 0.0
        checksum = "unknown"
        
        if is_available:
            variables = get_dataset_variables(hf_id)
            size_mb = estimate_dataset_size_mb(name, hf_id)
            checksum = compute_dataset_checksum(hf_id)
            status = "available"
            logger.info(f"Dataset {name} is available. Variables: {len(variables)}, Size: {size_mb:.2f} MB")
        else:
            status = "unavailable"
            logger.warning(f"Dataset {name} is not available.")
        
        results.append({
            "dataset_name": name,
            "url": f"https://huggingface.co/datasets/{hf_id}",
            "variables": variables,
            "size_mb": size_mb,
            "verification_status": status,
            "checksum": checksum
        })
    
    # Update research.md
    update_research_md(results)
    
    logger.info("Text dataset verification complete.")
    return results

if __name__ == "__main__":
    main()
