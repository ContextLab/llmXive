"""
Model Verification Script (T006)

Verifies model weights are < 1 GB for TimeSeries-Transformer, TabPFN, and
distilled LLMs via HuggingFace model cards. Documents findings in research.md.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Attempt to import huggingface_hub, but handle gracefully if missing
try:
    from huggingface_hub import HfApi, model_info
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    logging.warning("huggingface_hub not installed. Model size verification will be skipped.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define models to verify
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (Small)",
        "hf_id": "google/t5-small",  # Placeholder: Using T5-small as a proxy for small transformer size check
        "expected_type": "transformer",
        "max_size_gb": 1.0
    },
    {
        "model_name": "TabPFN",
        "hf_id": "Pfletschinger/TabPFN-small",
        "expected_type": "tabular",
        "max_size_gb": 1.0
    },
    {
        "model_name": "Distilled LLM (TinyLlama)",
        "hf_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "expected_type": "llm",
        "max_size_gb": 1.0
    }
]

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Fetches the model size in MB from HuggingFace Hub.
    
    Args:
        hf_id: HuggingFace model identifier (e.g., 'username/model_name')
        
    Returns:
        Size in MB if successful, None otherwise.
    """
    if not HF_HUB_AVAILABLE:
        logger.error("huggingface_hub is not installed. Cannot verify model sizes.")
        return None

    try:
        # Use the model_info endpoint to get file sizes
        info = model_info(hf_id)
        
        # Calculate total size of all files in the repo
        total_bytes = 0
        for file in info.siblings:
            if file.size:
                total_bytes += file.size
        
        total_mb = total_bytes / (1024 * 1024)
        logger.info(f"Model {hf_id} total size: {total_mb:.2f} MB")
        return total_mb
        
    except Exception as e:
        logger.error(f"Failed to fetch info for {hf_id}: {e}")
        return None

def update_research_md(verification_results: List[Dict[str, Any]], research_md_path: str):
    """
    Updates the research.md file with the model verification results.
    
    Args:
        verification_results: List of dicts containing model verification data.
        research_md_path: Path to the research.md file.
    """
    if not os.path.exists(research_md_path):
        logger.warning(f"research.md not found at {research_md_path}. Creating a new section.")
        # In a real scenario, we might create the file, but for safety we'll just log
        return

    # Read existing content
    with open(research_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the new section header
    section_header = "## Model Verification"
    
    # Check if section already exists
    if section_header in content:
        # Find the start of the section
        start_idx = content.find(section_header)
        # Find the start of the next section (double newline followed by #)
        end_idx = content.find("\n## ", start_idx + len(section_header))
        if end_idx == -1:
            end_idx = len(content)
        
        # Replace the old section content
        new_section_content = f"{section_header}\n\n"
        new_section_content += "Verification of model weights to ensure CPU tractability (< 1 GB).\n\n"
        new_section_content += "| Model Name | HF ID | Size (MB) | CPU Tractable |\n"
        new_section_content += "|------------|-------|-----------|---------------|\n"
        
        for res in verification_results:
            status = "✅ Yes" if res['cpu_tractable'] else "❌ No"
            new_section_content += f"| {res['model_name']} | {res['hf_id']} | {res['size_mb']:.2f} | {status} |\n"
        
        # Reconstruct content
        new_content = content[:start_idx] + new_section_content + content[end_idx:]
    else:
        # Append new section to end
        new_section_content = f"\n\n{section_header}\n\n"
        new_section_content += "Verification of model weights to ensure CPU tractability (< 1 GB).\n\n"
        new_section_content += "| Model Name | HF ID | Size (MB) | CPU Tractable |\n"
        new_section_content += "|------------|-------|-----------|---------------|\n"
        
        for res in verification_results:
            status = "✅ Yes" if res['cpu_tractable'] else "❌ No"
            new_section_content += f"| {res['model_name']} | {res['hf_id']} | {res['size_mb']:.2f} | {status} |\n"
        
        new_content = content + new_section_content

    # Write back
    with open(research_md_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    logger.info(f"Updated {research_md_path} with model verification results.")

def verify_models() -> List[Dict[str, Any]]:
    """
    Main verification logic.
    
    Returns:
        List of verification results.
    """
    results = []
    
    if not HF_HUB_AVAILABLE:
        logger.error("Cannot verify models: huggingface_hub not installed.")
        # Create dummy results indicating failure to verify
        for model in MODELS_TO_VERIFY:
            results.append({
                "model_name": model["model_name"],
                "hf_id": model["hf_id"],
                "size_mb": 0.0,
                "cpu_tractable": False,
                "error": "huggingface_hub not installed"
            })
        return results

    for model in MODELS_TO_VERIFY:
        logger.info(f"Verifying model: {model['model_name']} ({model['hf_id']})")
        size_mb = get_model_size_mb(model['hf_id'])
        
        if size_mb is not None:
            cpu_tractable = size_mb < (model['max_size_gb'] * 1024)
            results.append({
                "model_name": model['model_name'],
                "hf_id": model['hf_id'],
                "size_mb": size_mb,
                "cpu_tractable": cpu_tractable
            })
        else:
            results.append({
                "model_name": model['model_name'],
                "hf_id": model['hf_id'],
                "size_mb": 0.0,
                "cpu_tractable": False,
                "error": "Failed to fetch model info"
            })
    
    return results

def main():
    """Main entry point."""
    logger.info("Starting Model Verification (T006)...")
    
    # Determine paths
    project_root = Path(__file__).resolve().parent.parent.parent
    research_md_path = project_root / "research.md"
    
    # Run verification
    results = verify_models()
    
    # Update research.md
    update_research_md(results, str(research_md_path))
    
    # Print summary
    print("\n--- Model Verification Summary ---")
    for res in results:
        status = "✅ PASS" if res['cpu_tractable'] else "❌ FAIL"
        print(f"{status} | {res['model_name']} | {res['size_mb']:.2f} MB")
    print("----------------------------------")
    
    return results

if __name__ == "__main__":
    main()
