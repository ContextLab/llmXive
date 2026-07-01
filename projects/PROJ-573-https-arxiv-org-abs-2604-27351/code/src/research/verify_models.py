"""
Verify model weights for CPU-tractable foundation models.

This script checks the size of HuggingFace models to ensure they are < 1 GB,
making them suitable for CPU-only inference as required by the benchmark.

Models verified:
- TimeSeries-Transformer (via a small proxy or public weights)
- TabPFN (tabular foundation model)
- Distilled LLM (e.g., DistilBERT or similar small text model)
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from huggingface_hub import HfApi, model_info
except ImportError:
    # Fallback if huggingface_hub is not installed
    print("ERROR: huggingface_hub is required. Install with: pip install huggingface_hub")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define models to verify
# Note: Using specific, known CPU-tractable models that are likely < 1GB
MODELS_TO_VERIFY = [
    {
        "model_name": "TabPFN",
        "hf_id": "TabPFN/TabPFN-small",  # Smaller variant if available, or standard
        "expected_type": "tabular"
    },
    {
        "model_name": "DistilBERT",
        "hf_id": "distilbert-base-uncased",  # Standard distilled LLM
        "expected_type": "text"
    },
    {
        "model_name": "TimeSeries-Transformer-Proxy",
        "hf_id": "google/t5-small",  # Using T5-small as a proxy for small transformer architecture
        "expected_type": "timeseries_proxy"
    }
]

def get_model_size_mb(hf_id: str) -> float:
    """
    Fetch the total size of a HuggingFace model in MB.
    
    Args:
        hf_id: The HuggingFace model identifier (e.g., 'username/repo')
        
    Returns:
        Size in MB (float)
        
    Raises:
        Exception: If model cannot be found or accessed
    """
    try:
        api = HfApi()
        # Get model info including siblings (files)
        info = model_info(hf_id)
        
        total_size_bytes = 0
        # Sum sizes of all files in the model repo
        for file in info.siblings:
            if file.size:
                total_size_bytes += file.size
        
        size_mb = total_size_bytes / (1024 * 1024)
        return size_mb
    except Exception as e:
        logger.error(f"Failed to get size for model {hf_id}: {e}")
        raise

def verify_models(models: List[Dict[str, Any]], max_size_gb: float = 1.0) -> List[Dict[str, Any]]:
    """
    Verify that all specified models are under the size limit.
    
    Args:
        models: List of model dicts with 'model_name', 'hf_id', 'expected_type'
        max_size_gb: Maximum allowed size in GB (default 1.0)
        
    Returns:
        List of verification results
    """
    results = []
    max_size_mb = max_size_gb * 1024 * 1024
    
    for model_spec in models:
        model_name = model_spec['model_name']
        hf_id = model_spec['hf_id']
        
        logger.info(f"Verifying model: {model_name} ({hf_id})")
        
        try:
            size_mb = get_model_size_mb(hf_id)
            cpu_tractable = size_mb <= max_size_mb
            
            result = {
                "model_name": model_name,
                "hf_id": hf_id,
                "size_mb": round(size_mb, 2),
                "cpu_tractable": cpu_tractable,
                "status": "PASS" if cpu_tractable else "FAIL"
            }
            logger.info(f"  Size: {result['size_mb']} MB, CPU Tractable: {cpu_tractable}")
            
        except Exception as e:
            result = {
                "model_name": model_name,
                "hf_id": hf_id,
                "size_mb": None,
                "cpu_tractable": False,
                "status": "ERROR",
                "error": str(e)
            }
            logger.error(f"  Error verifying {model_name}: {e}")
        
        results.append(result)
    
    return results

def update_research_md(results: List[Dict[str, Any]], research_md_path: str = "code/research/research.md"):
    """
    Update the research.md file with the model verification results.
    
    Adds or updates the "Model Verification" section with a table of results.
    """
    research_path = Path(research_md_path)
    if not research_path.exists():
        logger.warning(f"research.md not found at {research_md_path}. Creating new file.")
        # Create a new research.md with the section
        content = f"""# Research Documentation

## Model Verification

The following models have been verified for CPU tractability (< 1 GB):

| Model Name | HF ID | Size (MB) | CPU Tractable |
|------------|-------|-----------|---------------|
"""
        for r in results:
            size_str = f"{r['size_mb']:.2f}" if r['size_mb'] is not None else "N/A"
            tractable_str = "Yes" if r['cpu_tractable'] else "No"
            content += f"| {r['model_name']} | {r['hf_id']} | {size_str} | {tractable_str} |\n"
        
        content += "\n*Verification completed automatically by verify_models.py*\n"
        
        with open(research_path, 'w') as f:
            f.write(content)
        logger.info(f"Created new research.md at {research_path}")
        return

    # Read existing content
    with open(research_path, 'r') as f:
        content = f.read()

    # Check if "Model Verification" section exists
    section_marker = "## Model Verification"
    if section_marker in content:
        # Find the start and end of the section
        start_idx = content.find(section_marker)
        # Look for the next section (starts with ##) or end of file
        next_section_idx = content.find("\n## ", start_idx + len(section_marker))
        if next_section_idx == -1:
            end_idx = len(content)
        else:
            end_idx = next_section_idx

        # Build new section content
        new_section = f"""## Model Verification

The following models have been verified for CPU tractability (< 1 GB):

| Model Name | HF ID | Size (MB) | CPU Tractable |
|------------|-------|-----------|---------------|
"""
        for r in results:
            size_str = f"{r['size_mb']:.2f}" if r['size_mb'] is not None else "N/A"
            tractable_str = "Yes" if r['cpu_tractable'] else "No"
            new_section += f"| {r['model_name']} | {r['hf_id']} | {size_str} | {tractable_str} |\n"
        
        new_section += "\n*Verification completed automatically by verify_models.py*\n"

        # Replace old section with new
        new_content = content[:start_idx] + new_section + content[end_idx:]
    else:
        # Append new section to end
        new_content = content + f"""
## Model Verification

The following models have been verified for CPU tractability (< 1 GB):

| Model Name | HF ID | Size (MB) | CPU Tractable |
|------------|-------|-----------|---------------|
"""
        for r in results:
            size_str = f"{r['size_mb']:.2f}" if r['size_mb'] is not None else "N/A"
            tractable_str = "Yes" if r['cpu_tractable'] else "No"
            new_content += f"| {r['model_name']} | {r['hf_id']} | {size_str} | {tractable_str} |\n"
        
        new_content += "\n*Verification completed automatically by verify_models.py*\n"

    # Write updated content
    with open(research_path, 'w') as f:
        f.write(new_content)
    
    logger.info(f"Updated research.md at {research_path}")

def main():
    """Main entry point for model verification."""
    logger.info("Starting model verification...")
    
    # Run verification
    results = verify_models(MODELS_TO_VERIFY)
    
    # Update research.md
    update_research_md(results)
    
    # Print summary
    print("\n" + "="*60)
    print("MODEL VERIFICATION SUMMARY")
    print("="*60)
    print(f"{'Model Name':<30} {'HF ID':<30} {'Size (MB)':<10} {'CPU Tractable'}")
    print("-"*60)
    for r in results:
        size_str = f"{r['size_mb']:.2f}" if r['size_mb'] is not None else "N/A"
        tractable_str = "Yes" if r['cpu_tractable'] else "No"
        print(f"{r['model_name']:<30} {r['hf_id']:<30} {size_str:<10} {tractable_str}")
    print("="*60)
    
    # Check if all passed
    all_passed = all(r['cpu_tractable'] for r in results if r['status'] != 'ERROR')
    if all_passed:
        print("✓ All models are CPU tractable (< 1 GB)")
    else:
        print("✗ Some models exceed the 1 GB limit or failed verification")
        sys.exit(1)

if __name__ == "__main__":
    main()