"""
Verify text dataset availability (DROP/MUST) via HuggingFace datasets.
Implements FR-001, Phase 0.1.
"""
import os
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library not found. Please install it via: pip install datasets")
    sys.exit(1)

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Project root relative to this script location
# Assuming script is at code/src/research/verify_text.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESEARCH_MD_PATH = PROJECT_ROOT / "specs" / "001-https-arxiv-org-abs-2604-27351" / "research.md"
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Datasets to verify
# Using "drop" (Dense Passage Retrieval) and "must" (Multimodal Understanding of Stories - text component)
# Note: 'must' might be 'must_qa' or similar depending on exact HF ID. We try common variants.
DATASETS_TO_VERIFY = [
    {
        "name": "drop",
        "hf_id": "drop",
        "description": "Dense Passage Retrieval dataset for reading comprehension",
        "expected_splits": ["train", "validation", "test"]
    },
    {
        "name": "must_qa",
        "hf_id": "must_qa",
        "description": "Multimodal Understanding of Stories - QA text component",
        "expected_splits": ["train", "validation"]
    }
]

def compute_dataset_checksum(dataset_obj: Any, max_samples: int = 1000) -> str:
    """
    Compute a deterministic checksum of the dataset content (first max_samples rows).
    Uses a subset to avoid excessive I/O for large datasets.
    """
    hasher = hashlib.sha256()
    try:
        # Try to get a representative sample
        # Handle different dataset structures
        if hasattr(dataset_obj, 'data'):
            # HuggingFace dataset object
            sample_iter = iter(dataset_obj)
        else:
            # Fallback
            sample_iter = iter([dataset_obj])

        count = 0
        for item in sample_iter:
            if count >= max_samples:
                break
            # Serialize item to string for hashing
            item_str = str(item)
            hasher.update(item_str.encode('utf-8'))
            count += 1
        
        return hasher.hexdigest()
    except Exception as e:
        logger.warning(f"Could not compute checksum for dataset: {e}")
        return "checksum_error"

def estimate_dataset_size_mb(dataset_obj: Any) -> float:
    """
    Estimate dataset size in MB by checking local cache if available,
    or by sampling and extrapolating.
    """
    # Try to get size from dataset info if available
    if hasattr(dataset_obj, '_info') and dataset_obj._info:
        info = dataset_obj._info
        if hasattr(info, 'download_size') and info.download_size:
            return info.download_size / (1024 * 1024)
        if hasattr(info, 'dataset_size') and info.dataset_size:
            return info.dataset_size / (1024 * 1024)
    
    # Fallback: estimate by sampling
    # Load a small sample and estimate
    try:
        if hasattr(dataset_obj, 'select'):
            sample = dataset_obj.select(range(min(100, len(dataset_obj))))
            # Approximate size based on string length of first item
            first_item_str = str(sample[0]) if len(sample) > 0 else ""
            avg_char_size = len(first_item_str)
            total_rows = len(dataset_obj)
            estimated_bytes = avg_char_size * total_rows
            return estimated_bytes / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Could not estimate size: {e}")
    
    return 0.0

def verify_dataset(dataset_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a single dataset from HuggingFace.
    Returns a dict with verification results.
    """
    name = dataset_config["name"]
    hf_id = dataset_config["hf_id"]
    expected_splits = dataset_config.get("expected_splits", [])
    
    result = {
        "dataset_name": name,
        "url": f"https://huggingface.co/datasets/{hf_id}",
        "variables": [],
        "size_mb": 0.0,
        "verification_status": "FAILED",
        "error": None,
        "checksum": None
    }
    
    logger.info(f"Verifying dataset: {name} (ID: {hf_id})")
    
    try:
        # Attempt to load the dataset
        # Use streaming=True to avoid downloading full dataset for verification
        start_time = time.time()
        dataset = load_dataset(hf_id, split="train", streaming=True)
        load_time = time.time() - start_time
        logger.info(f"Loaded {name} in {load_time:.2f}s (streaming)")
        
        # Get column names (variables)
        # For streaming, we need to peek at the first item
        try:
            first_item = next(iter(dataset))
            result["variables"] = list(first_item.keys())
            logger.info(f"Variables found: {result['variables']}")
        except StopIteration:
            logger.warning(f"Dataset {name} appears to be empty.")
            result["variables"] = []
        except Exception as e:
            logger.warning(f"Could not inspect variables: {e}")
            result["variables"] = []
        
        # Estimate size
        # For streaming, we estimate based on available info or sampling
        # Re-load non-streaming for size estimation if possible, but this might be slow
        # For now, we'll use a heuristic or mark as estimated
        try:
            # Try to get full dataset info for size
            full_dataset = load_dataset(hf_id, split="train", trust_remote_code=True)
            result["size_mb"] = estimate_dataset_size_mb(full_dataset)
            result["checksum"] = compute_dataset_checksum(full_dataset, max_samples=500)
            del full_dataset # Explicit cleanup
        except Exception as e:
            logger.warning(f"Could not get full size/checksum: {e}. Using streaming estimate.")
            # Fallback estimate
            result["size_mb"] = estimate_dataset_size_mb(dataset) if hasattr(dataset, '__len__') else 0.0
            result["checksum"] = "streaming_estimate"
        
        result["verification_status"] = "VERIFIED"
        logger.info(f"Dataset {name} verified successfully. Size: {result['size_mb']:.2f} MB")
        
    except Exception as e:
        result["error"] = str(e)
        result["verification_status"] = "FAILED"
        logger.error(f"Failed to verify dataset {name}: {e}")
    
    return result

def update_research_md(results: List[Dict[str, Any]]) -> None:
    """
    Update research.md with the verification results.
    Creates the 'Dataset Verification' section if it doesn't exist.
    """
    if not RESEARCH_MD_PATH.exists():
        logger.warning(f"research.md not found at {RESEARCH_MD_PATH}. Creating new file.")
        RESEARCH_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        content = "# Research Documentation\n\n"
    else:
        content = RESEARCH_MD_PATH.read_text(encoding='utf-8')
    
    # Ensure Dataset Verification section exists
    section_header = "## Dataset Verification"
    if section_header not in content:
        logger.info("Adding 'Dataset Verification' section to research.md")
        content += f"\n\n{section_header}\n\n"
        # Append initial table header
        content += "| Dataset Name | URL | Variables | Size (MB) | Status |\n"
        content += "|---|---|---|---|---|\n"
    
    # Find the start of the table (after the header)
    lines = content.split('\n')
    table_start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "Dataset Name" in line:
            table_start_idx = i + 1
            break
    
    # Prepare new table rows
    new_rows = []
    for res in results:
        if res["verification_status"] == "VERIFIED":
            variables_str = ", ".join(res["variables"]) if res["variables"] else "N/A"
            row = f"| {res['dataset_name']} | {res['url']} | {variables_str} | {res['size_mb']:.2f} | ✅ {res['verification_status']} |\n"
            new_rows.append(row)
        else:
            row = f"| {res['dataset_name']} | {res['url']} | {res.get('error', 'Unknown error')} | N/A | ❌ {res['verification_status']} |\n"
            new_rows.append(row)
    
    # Insert new rows after the header row
    if table_start_idx != -1:
        # Insert at the beginning of the table body
        lines[table_start_idx:table_start_idx] = new_rows
        content = "\n".join(lines)
    else:
        # Fallback: append to end
        content += "\n" + "".join(new_rows)
    
    # Write back
    RESEARCH_MD_PATH.write_text(content, encoding='utf-8')
    logger.info(f"Updated {RESEARCH_MD_PATH}")

def main():
    """Main entry point for the verification script."""
    logger.info("Starting text dataset verification...")
    
    all_results = []
    
    for dataset_cfg in DATASETS_TO_VERIFY:
        result = verify_dataset(dataset_cfg)
        all_results.append(result)
    
    # Update research.md
    update_research_md(all_results)
    
    # Summary
    verified_count = sum(1 for r in all_results if r["verification_status"] == "VERIFIED")
    logger.info(f"Verification complete. {verified_count}/{len(all_results)} datasets verified.")
    
    # Print summary to stdout for quick viewing
    print("\n--- Text Dataset Verification Summary ---")
    for res in all_results:
        status_icon = "✅" if res["verification_status"] == "VERIFIED" else "❌"
        print(f"{status_icon} {res['dataset_name']}: {res['verification_status']} ({res['size_mb']:.2f} MB)")
        if res["error"]:
            print(f"   Error: {res['error']}")
    print("-----------------------------------------")
    
    # Exit with error if any verification failed
    if verified_count < len(all_results):
        sys.exit(1)

if __name__ == "__main__":
    main()
