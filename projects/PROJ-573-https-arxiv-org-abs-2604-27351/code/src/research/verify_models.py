"""
Verify model weights are CPU-tractable (< 1 GB) for the benchmark.

This script checks the HuggingFace model cards for:
1. TimeSeries-Transformer (using a lightweight variant)
2. TabPFN (Tabular Prior-data Fitted Network)
3. Distilled LLM (using a small distilled model)

It writes the results to research.md under the "Model Verification" section.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Attempt to import huggingface_hub, handle gracefully if missing
try:
    from huggingface_hub import model_info, HfApi
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logging.warning("huggingface_hub not installed. Model sizes will be estimated or marked unknown.")

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define models to verify
# Note: We use specific model IDs known to be small or representative of the class.
# TimeSeries-Transformer: Using a small variant or a standard transformer adapted for TS
# TabPFN: Using the standard small TabPFN model
# Distilled LLM: Using a very small distilled model like distilbert-base-uncased as a proxy for "distilled LLM"
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (Small)",
        "hf_id": "google/t5-small", # Placeholder for a small transformer, real TS models often custom. Using T5-small as a proxy for weight size check.
        "description": "Proxy for TimeSeries-Transformer architecture weight check"
    },
    {
        "model_name": "TabPFN",
        "hf_id": "TabPFN/tabpfn-v2-cifar10", # TabPFN models are often small
        "description": "TabPFN model for tabular data"
    },
    {
        "model_name": "Distilled LLM",
        "hf_id": "distilbert-base-uncased",
        "description": "Distilled BERT model for text"
    }
]

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Fetch the model size in MB from HuggingFace.
    Returns None if unable to fetch.
    """
    if not HF_AVAILABLE:
        logger.warning(f"Cannot fetch size for {hf_id}: huggingface_hub not available.")
        return None
    
    try:
        api = HfApi()
        info = model_info(hf_id)
        
        # Calculate total size of files in the repository
        total_size_bytes = 0
        for sibling in info.siblings:
            if sibling.size:
                total_size_bytes += sibling.size
        
        size_mb = total_size_bytes / (1024 * 1024)
        logger.info(f"Model {hf_id} size: {size_mb:.2f} MB")
        return size_mb
    except Exception as e:
        logger.error(f"Error fetching info for {hf_id}: {e}")
        return None

def verify_models() -> List[Dict[str, Any]]:
    """
    Verify all models in MODELS_TO_VERIFY.
    Returns a list of dictionaries with verification details.
    """
    results = []
    for model in MODELS_TO_VERIFY:
        size_mb = get_model_size_mb(model["hf_id"])
        
        if size_mb is not None:
            cpu_tractable = size_mb < 1024.0 # 1 GB = 1024 MB
        else:
            # If we can't fetch, assume non-tractable to be safe, or mark unknown
            # For this task, we assume if we can't verify, it's not confirmed
            cpu_tractable = False 
            size_mb = -1.0 # Indicator of failure

        results.append({
            "model_name": model["model_name"],
            "hf_id": model["hf_id"],
            "size_mb": round(size_mb, 2) if size_mb >= 0 else None,
            "cpu_tractable": cpu_tractable,
            "status": "verified" if size_mb is not None else "failed_to_fetch"
        })
    
    return results

def update_research_md(results: List[Dict[str, Any]], research_md_path: str) -> bool:
    """
    Update research.md with the "Model Verification" section.
    """
    if not Path(research_md_path).exists():
        logger.error(f"research.md not found at {research_md_path}")
        return False

    try:
        with open(research_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read research.md: {e}")
        return False

    # Define the new section content
    section_header = "## Model Verification"
    table_header = "| model_name | hf_id | size_mb | cpu_tractable |"
    table_sep = "|---|---|---|---|"
    
    table_rows = []
    for res in results:
        size_str = f"{res['size_mb']:.2f}" if res['size_mb'] is not None else "N/A"
        tractable_str = "Yes" if res['cpu_tractable'] else "No"
        table_rows.append(f"| {res['model_name']} | {res['hf_id']} | {size_str} | {tractable_str} |")
    
    new_section = f"{section_header}\n{table_header}\n{table_sep}\n" + "\n".join(table_rows) + "\n"

    # Check if section exists and replace it, or append
    if section_header in content:
        # Find start and end of the section
        start_idx = content.find(section_header)
        # Find next section header (starts with ##) after current one
        next_header_idx = content.find("\n## ", start_idx + len(section_header))
        
        if next_header_idx == -1:
            # No next section, replace till end
            new_content = content[:start_idx] + new_section
        else:
            new_content = content[:start_idx] + new_section + "\n" + content[next_header_idx:]
    else:
        # Append to end
        new_content = content.rstrip() + "\n\n" + new_section

    try:
        with open(research_md_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(f"Successfully updated {research_md_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write research.md: {e}")
        return False

def main():
    """Main entry point."""
    # Determine paths relative to project root
    # Assuming script is at code/src/research/verify_models.py
    # Project root is code/
    project_root = Path(__file__).parent.parent.parent
    research_md_path = project_root / "research.md"
    
    logger.info("Starting model verification...")
    
    if not HF_AVAILABLE:
        logger.warning("huggingface_hub is not installed. Install with `pip install huggingface_hub` for accurate sizes.")
        # We still try to run, but results might be incomplete
    
    results = verify_models()
    
    # Update research.md
    success = update_research_md(results, str(research_md_path))
    
    if success:
        logger.info("Model verification complete. Results written to research.md.")
        # Print summary
        for res in results:
            status = "PASS" if res['cpu_tractable'] else "FAIL (or unknown)"
            print(f"{res['model_name']}: {res['size_mb']} MB - {status}")
    else:
        logger.error("Failed to update research.md.")
        sys.exit(1)

if __name__ == "__main__":
    main()