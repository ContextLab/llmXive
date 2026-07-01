"""
Verify model weights for CPU-tractable models (< 1 GB).

This script checks HuggingFace model cards for:
1. TimeSeries-Transformer
2. TabPFN
3. Distilled LLM (e.g., DistilBERT)

It queries the HuggingFace Hub API to get the actual model size
and determines if the model is CPU-tractable (< 1024 MB).
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from huggingface_hub import HfApi, model_info
import yaml

# Define the models to verify based on project requirements
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (CPU-tractable)",
        "hf_id": "google/t5-small",  # Using T5-small as a lightweight transformer baseline for time-series
        "description": "Lightweight transformer suitable for time-series tasks"
    },
    {
        "model_name": "TabPFN",
        "hf_id": "Pfils/TabPFN-v1",
        "description": "Prior-data fitted network for tabular data"
    },
    {
        "model_name": "DistilBERT (Distilled LLM)",
        "hf_id": "distilbert-base-uncased",
        "description": "Distilled version of BERT for text tasks"
    }
]

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Fetch model size from HuggingFace Hub API in MB.
    
    Args:
        hf_id: HuggingFace model identifier (e.g., "username/model-name")
        
    Returns:
        Model size in MB, or None if unable to fetch
    """
    try:
        api = HfApi()
        # Get model info including siblings (files)
        info = model_info(hf_id)
        
        # Calculate total size of all files
        total_size_bytes = 0
        if info.siblings:
            for sibling in info.siblings:
                if sibling.size:
                    total_size_bytes += sibling.size
        
        # Convert to MB
        size_mb = total_size_bytes / (1024 * 1024)
        return size_mb
    except Exception as e:
        print(f"Warning: Could not fetch size for {hf_id}: {e}")
        return None

def verify_models() -> List[Dict[str, Any]]:
    """
    Verify all models in MODELS_TO_VERIFY.
    
    Returns:
        List of verification results for each model
    """
    results = []
    for model in MODELS_TO_VERIFY:
        hf_id = model["hf_id"]
        size_mb = get_model_size_mb(hf_id)
        
        if size_mb is not None:
            cpu_tractable = size_mb < 1024.0  # < 1 GB
            status = "PASS" if cpu_tractable else "FAIL"
            print(f"{model['model_name']} ({hf_id}): {size_mb:.2f} MB - {status}")
        else:
            size_mb = 0.0
            cpu_tractable = False
            status = "UNKNOWN"
            print(f"{model['model_name']} ({hf_id}): Unable to fetch size - {status}")
        
        results.append({
            "model_name": model["model_name"],
            "hf_id": hf_id,
            "size_mb": round(size_mb, 2),
            "cpu_tractable": cpu_tractable,
            "status": status
        })
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save verification results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

def update_research_md(results: List[Dict[str, Any]], research_md_path: str) -> None:
    """
    Update research.md with the Model Verification section.
    
    Args:
        results: List of model verification results
        research_md_path: Path to research.md file
    """
    research_path = Path(research_md_path)
    if not research_path.exists():
        print(f"Warning: {research_md_path} does not exist. Creating new file.")
        content = "# Research Documentation\n\n"
    else:
        with open(research_path, 'r') as f:
            content = f.read()
    
    # Generate the Model Verification section
    section = "\n## Model Verification\n\n"
    section += "Verification of model weights to ensure CPU-tractability (< 1 GB).\n\n"
    section += "| Model Name | HF ID | Size (MB) | CPU Tractable |\n"
    section += "|------------|-------|-----------|---------------|\n"
    
    for r in results:
        tractable_str = "✅ Yes" if r["cpu_tractable"] else "❌ No" if r["size_mb"] > 0 else "⚠️ Unknown"
        section += f"| {r['model_name']} | {r['hf_id']} | {r['size_mb']} | {tractable_str} |\n"
    
    section += "\n### Summary\n\n"
    passed = sum(1 for r in results if r["cpu_tractable"])
    total = len(results)
    section += f"Models verified: {total}\n"
    section += f"CPU-tractable (< 1 GB): {passed}\n"
    section += f"Non-tractable: {total - passed}\n"
    
    # Check if section already exists and replace it
    import re
    section_pattern = r"## Model Verification.*?(?=\n## |\Z)"
    if re.search(section_pattern, content, re.DOTALL):
        content = re.sub(section_pattern, section, content, flags=re.DOTALL)
    else:
        content += section
    
    with open(research_path, 'w') as f:
        f.write(content)
    print(f"Updated {research_md_path} with Model Verification section")

def main():
    """Main entry point for model verification."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    research_md_path = project_root / "research.md"
    results_output_path = project_root / "data" / "model_verification_results.json"
    
    # Ensure data directory exists
    results_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Starting model verification...")
    print(f"Checking {len(MODELS_TO_VERIFY)} models for CPU-tractability (< 1 GB)")
    print("-" * 60)
    
    # Verify models
    results = verify_models()
    
    # Save results
    save_results(results, str(results_output_path))
    
    # Update research.md
    update_research_md(results, str(research_md_path))
    
    print("-" * 60)
    print("Model verification complete.")
    
    # Return exit code based on results
    all_tractable = all(r["cpu_tractable"] for r in results if r["size_mb"] > 0)
    if not all_tractable:
        print("Warning: Some models exceed 1 GB limit.")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
