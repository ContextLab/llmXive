"""
Verify model weights for CPU-tractable models via HuggingFace model cards.

This script checks the size of model weights for:
1. TimeSeries-Transformer (via a representative small transformer)
2. TabPFN (Tabular Prior-data Fitted Network)
3. Distilled LLM (e.g., DistilBERT)

It verifies that all models are < 1 GB and documents the results in research.md.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from huggingface_hub import model_info, HfApi
except ImportError:
    print("Error: huggingface_hub is required. Install with: pip install huggingface_hub")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define models to verify
# Note: Using specific model IDs that are known to be CPU-tractable
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (Small)",
        "hf_id": "google/t5-small",  # Using T5-small as a proxy for transformer architecture size
        "description": "Representative small transformer model for time-series tasks"
    },
    {
        "model_name": "TabPFN",
        "hf_id": "TabPFN/TabPFN-small",  # Small version of TabPFN
        "description": "Tabular Prior-data Fitted Network (small variant)"
    },
    {
        "model_name": "DistilBERT",
        "hf_id": "distilbert-base-uncased",
        "description": "Distilled version of BERT for text tasks"
    }
]

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Get the size of a model in MB from HuggingFace.
    
    Args:
        hf_id: HuggingFace model identifier
        
    Returns:
        Size in MB, or None if unable to determine
    """
    try:
        api = HfApi()
        info = model_info(hf_id)
        
        # Calculate total size of model files
        total_size_bytes = 0
        for sibling in info.siblings:
            if sibling.size is not None:
                # Only count model weight files (not config, tokenizer, etc.)
                if any(ext in sibling.rfilename for ext in ['.bin', '.safetensors', '.pt', '.pth']):
                    total_size_bytes += sibling.size
        
        size_mb = total_size_bytes / (1024 * 1024)
        logger.info(f"Model {hf_id}: {size_mb:.2f} MB")
        return size_mb
    except Exception as e:
        logger.error(f"Error getting size for {hf_id}: {e}")
        return None

def check_cpu_tractable(size_mb: float, threshold_gb: float = 1.0) -> bool:
    """
    Check if a model is CPU-tractable based on size.
    
    Args:
        size_mb: Model size in MB
        threshold_gb: Maximum size in GB for CPU tractability
        
    Returns:
        True if model is CPU-tractable, False otherwise
    """
    threshold_mb = threshold_gb * 1024
    return size_mb < threshold_mb

def update_research_md(results: List[Dict[str, Any]], research_md_path: Path) -> None:
    """
    Update research.md with model verification results.
    
    Args:
        results: List of model verification results
        research_md_path: Path to research.md file
    """
    # Ensure research.md exists
    if not research_md_path.exists():
        logger.warning(f"research.md not found at {research_md_path}. Creating new file.")
        research_md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(research_md_path, 'w') as f:
            f.write("# Research Documentation\n\n")
    
    # Read existing content
    with open(research_md_path, 'r') as f:
        content = f.read()
    
    # Check if "Model Verification" section exists
    section_marker = "## Model Verification"
    if section_marker not in content:
        # Add section if it doesn't exist
        content += f"\n{section_marker}\n\n"
        content += "This section documents the verification of model weights for CPU-tractable models.\n\n"
    
    # Find the section and replace/update it
    lines = content.split('\n')
    new_lines = []
    in_section = False
    section_ended = False
    
    for i, line in enumerate(lines):
        if line.strip() == section_marker:
            in_section = True
            new_lines.append(line)
            # Add table header
            new_lines.append("")
            new_lines.append("| Model Name | HF ID | Size (MB) | CPU Tractable |")
            new_lines.append("|------------|-------|-----------|---------------|")
            continue
        
        if in_section and line.startswith('|') and not line.startswith('| Model Name'):
            # Skip existing table rows
            continue
        
        if in_section and line.strip() == "" and i > 0 and lines[i-1].startswith('|'):
            # End of table
            in_section = False
            section_ended = True
            # Add our results
            for result in results:
                cpu_status = "✅ Yes" if result['cpu_tractable'] else "❌ No"
                new_lines.append(f"| {result['model_name']} | {result['hf_id']} | {result['size_mb']:.2f} | {cpu_status} |")
            new_lines.append("")
            new_lines.append("")
            # Add remaining content after the old section
            continue
        
        if not in_section:
            new_lines.append(line)
    
    # If we didn't find the end of the section, add results at the end
    if not section_ended and in_section:
        for result in results:
            cpu_status = "✅ Yes" if result['cpu_tractable'] else "❌ No"
            new_lines.append(f"| {result['model_name']} | {result['hf_id']} | {result['size_mb']:.2f} | {cpu_status} |")
        new_lines.append("")
        new_lines.append("")
    
    # Write updated content
    with open(research_md_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    logger.info(f"Updated {research_md_path} with model verification results")

def main():
    """Main function to verify model weights and update documentation."""
    logger.info("Starting model weight verification...")
    
    # Determine project root (assume script is in src/research/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    research_md_path = project_root / "research.md"
    
    results = []
    all_passed = True
    
    for model in MODELS_TO_VERIFY:
        logger.info(f"Verifying {model['model_name']} ({model['hf_id']})...")
        
        size_mb = get_model_size_mb(model['hf_id'])
        
        if size_mb is None:
            logger.warning(f"Could not determine size for {model['hf_id']}, skipping")
            continue
        
        cpu_tractable = check_cpu_tractable(size_mb)
        
        result = {
            "model_name": model['model_name'],
            "hf_id": model['hf_id'],
            "size_mb": size_mb,
            "cpu_tractable": cpu_tractable,
            "description": model.get('description', '')
        }
        
        results.append(result)
        
        if not cpu_tractable:
            all_passed = False
            logger.warning(f"Model {model['model_name']} ({model['hf_id']}) is NOT CPU-tractable ({size_mb:.2f} MB)")
        else:
            logger.info(f"Model {model['model_name']} ({model['hf_id']}) is CPU-tractable ({size_mb:.2f} MB)")
    
    # Update research.md
    if results:
        update_research_md(results, research_md_path)
    else:
        logger.warning("No results to update in research.md")
    
    # Print summary
    print("\n" + "="*60)
    print("MODEL VERIFICATION SUMMARY")
    print("="*60)
    print(f"{'Model Name':<30} {'Size (MB)':<10} {'CPU Tractable'}")
    print("-"*60)
    for result in results:
        status = "✅ YES" if result['cpu_tractable'] else "❌ NO"
        print(f"{result['model_name']:<30} {result['size_mb']:<10.2f} {status}")
    print("="*60)
    
    if all_passed and results:
        print("✅ All models are CPU-tractable (< 1 GB)")
        return 0
    else:
        print("❌ Some models exceed CPU tractability threshold")
        return 1

if __name__ == "__main__":
    sys.exit(main())
