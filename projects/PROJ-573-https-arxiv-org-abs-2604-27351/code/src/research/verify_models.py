"""
Verify model weights for TimeSeries-Transformer, TabPFN, and distilled LLM.

This script checks HuggingFace model cards to ensure model weights are < 1 GB
for CPU tractability, as required by FR-002 and SC-002.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Models to verify: (model_name, hf_id, expected_type)
MODELS_TO_VERIFY = [
    ("TimeSeries-Transformer", "google/t5-small", "transformer"),  # Using T5-small as a proxy for time-series transformer capability
    ("TabPFN", "HuggingFaceM4/tabpfn-v2-0.1", "tabular"),
    ("Distilled LLM", "distilbert-base-uncased", "llm"),
]

MAX_SIZE_GB = 1.0
MAX_SIZE_MB = MAX_SIZE_GB * 1024


def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Get the size of a model in MB from HuggingFace.
    
    Args:
        hf_id: HuggingFace model ID
        
    Returns:
        Model size in MB, or None if not available
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        
        # Get model info
        model_info = api.model_info(hf_id)
        
        # Calculate total size of all files
        total_size_bytes = 0
        for sibling in model_info.siblings:
            if sibling.size:
                total_size_bytes += sibling.size
        
        total_size_mb = total_size_bytes / (1024 * 1024)
        return total_size_mb
        
    except Exception as e:
        logger.warning(f"Could not fetch size for {hf_id}: {e}")
        return None


def update_research_md(results: List[Dict[str, Any]], research_md_path: Path) -> None:
    """
    Update research.md with model verification results.
    
    Args:
        results: List of verification results
        research_md_path: Path to research.md
    """
    if not research_md_path.exists():
        logger.error(f"research.md not found at {research_md_path}")
        return

    content = research_md_path.read_text()
    
    # Find or create "Model Verification" section
    section_marker = "## Model Verification"
    if section_marker not in content:
        # Append new section
        content += f"\n\n{section_marker}\n\n"
    else:
        # Replace existing section content
        lines = content.split('\n')
        new_lines = []
        in_section = False
        skip_until_next_header = False
        
        for i, line in enumerate(lines):
            if line.strip() == section_marker:
                in_section = True
                new_lines.append(line)
                continue
            
            if in_section:
                if line.startswith('## ') and line != section_marker:
                    # Start of next section
                    in_section = False
                    skip_until_next_header = False
                
                if skip_until_next_header:
                    continue
                
                # Skip existing content in this section
                if line.strip() == '':
                    new_lines.append(line)
                    continue
                elif line.startswith('## '):
                    # Next section starts
                    new_lines.append(line)
                    in_section = False
                else:
                    # Skip content in current section
                    continue
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    # Add new content
    verification_content = "### Verification Results\n\n"
    verification_content += "| Model Name | HF ID | Size (MB) | CPU Tractable |\n"
    verification_content += "|------------|-------|-----------|---------------|\n"
    
    for result in results:
        cpu_tractable = "Yes" if result['size_mb'] is not None and result['size_mb'] < MAX_SIZE_MB else "No"
        verification_content += f"| {result['model_name']} | {result['hf_id']} | {result['size_mb']:.2f if result['size_mb'] is not None else 'N/A':.2f} | {cpu_tractable} |\n"
    
    verification_content += "\n**Verification Date**: " + str(os.popen('date').read().strip()) + "\n"
    verification_content += f"**Max Size Limit**: {MAX_SIZE_GB} GB\n\n"
    
    content += verification_content
    
    # Write back
    research_md_path.write_text(content)
    logger.info(f"Updated {research_md_path} with model verification results")


def main():
    """Main function to verify model weights and update research.md."""
    logger.info("Starting model weight verification...")
    
    results = []
    research_md_path = project_root / "research.md"
    
    for model_name, hf_id, model_type in MODELS_TO_VERIFY:
        logger.info(f"Verifying {model_name} ({hf_id})...")
        
        size_mb = get_model_size_mb(hf_id)
        cpu_tractable = size_mb is not None and size_mb < MAX_SIZE_MB
        
        result = {
            "model_name": model_name,
            "hf_id": hf_id,
            "size_mb": size_mb,
            "cpu_tractable": cpu_tractable
        }
        results.append(result)
        
        status = "✓" if cpu_tractable else "✗"
        size_str = f"{size_mb:.2f} MB" if size_mb is not None else "N/A"
        logger.info(f"  {status} {model_name}: {size_str} - CPU Tractable: {cpu_tractable}")
    
    # Update research.md
    if results:
        update_research_md(results, research_md_path)
    
    # Save results to JSON for programmatic access
    results_path = project_root / "data" / "model_verification_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model verification complete. Results saved to {results_path}")
    
    # Print summary
    print("\n=== Model Verification Summary ===")
    for result in results:
        status = "PASS" if result['cpu_tractable'] else "FAIL"
        size_str = f"{result['size_mb']:.2f} MB" if result['size_mb'] is not None else "N/A"
        print(f"{result['model_name']}: {status} ({size_str})")
    
    # Return success if all models are CPU tractable
    all_tractable = all(r['cpu_tractable'] for r in results)
    return 0 if all_tractable else 1


if __name__ == "__main__":
    sys.exit(main())
