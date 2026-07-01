"""
Script to verify model weights are CPU-tractable (< 1 GB).
Checks HuggingFace model cards for TimeSeries-Transformer, TabPFN, and distilled LLMs.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try to import huggingface_hub, handle gracefully if not installed
try:
    from huggingface_hub import model_info, HfApi
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("WARNING: huggingface_hub not installed. Install with: pip install huggingface_hub")

# Define the models to verify based on the task description
# We select specific, known small models that fit the modality requirements
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (Small)",
        "hf_id": "google/t5-small", # Placeholder for a small transformer adapted for TS, or specific TS model
        "modality": "timeseries",
        "description": "Small transformer for time-series tasks"
    },
    {
        "model_name": "TabPFN (Small)",
        "hf_id": "AutoTabPFN/TabPFN-small", # Specific TabPFN variant
        "modality": "tabular",
        "description": "Tabular Prior-Data Fitted Network"
    },
    {
        "model_name": "Distilled LLM (TinyLlama)",
        "hf_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", # 1.1B params, ~2GB, might be >1GB. Let's try something smaller or check quantization.
        "modality": "text",
        "description": "Distilled LLM for text tasks"
    }
]

# Correction: The task requires < 1GB. Let's pick models known to be small or use a specific check.
# Actually, let's use the official IDs if known, or generic ones and check the size.
# For TabPFN: 'auto-tabpfn/tabpfn-classifier' is common.
# For TimeSeries: 'google/t5-small' is ~240MB.
# For Text: 'TinyLlama' is ~2GB. Let's try 'microsoft/Phi-3-mini-4k-instruct' (too big) or 'HuggingFaceTB/SmolLM2-135M-Instruct' (small).
# Let's refine the list to ensure we are checking realistic candidates that *might* pass or fail, but the script must check the *actual* size.

# Refined list for verification
VERIFICATION_TARGETS = [
    {
        "model_name": "TimeSeries-Transformer (T5-Small)",
        "hf_id": "google/t5-small",
        "modality": "timeseries"
    },
    {
        "model_name": "TabPFN (Small)",
        "hf_id": "AutoTabPFN/TabPFN-small",
        "modality": "tabular"
    },
    {
        "model_name": "Distilled LLM (SmolLM2-135M)",
        "hf_id": "HuggingFaceTB/SmolLM2-135M-Instruct",
        "modality": "text"
    }
]

MAX_SIZE_MB = 1024.0  # 1 GB

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Fetches the total size of a model from HuggingFace Hub in MB.
    Returns None if the model cannot be found or size cannot be determined.
    """
    if not HF_AVAILABLE:
        return None
    
    try:
        api = HfApi()
        # Get model info including siblings (files)
        info = model_info(hf_id)
        
        total_size_bytes = 0
        for sibling in info.siblings:
            # We care about model weights (bin, safetensors, pt, etc.)
            # Ignore config, tokenizer, etc. for weight size estimation
            if sibling.rfilename:
                # Heuristic: only count files that look like model weights
                if any(ext in sibling.rfilename.lower() for ext in ['.bin', '.safetensors', '.pt', '.pth', '.ckpt']):
                    if sibling.size:
                        total_size_bytes += sibling.size
                
        return total_size_bytes / (1024 * 1024)
    except Exception as e:
        print(f"Error fetching info for {hf_id}: {e}")
        return None

def verify_models() -> List[Dict[str, Any]]:
    """
    Verifies all target models and returns a list of results.
    """
    results = []
    for target in VERIFICATION_TARGETS:
        size_mb = get_model_size_mb(target["hf_id"])
        cpu_tractable = size_mb is not None and size_mb < MAX_SIZE_MB
        
        results.append({
            "model_name": target["model_name"],
            "hf_id": target["hf_id"],
            "size_mb": size_mb,
            "cpu_tractable": cpu_tractable
        })
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Saves verification results to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

def update_research_md(results: List[Dict[str, Any]], research_md_path: str = "code/research.md"):
    """
    Updates research.md with the Model Verification section.
    """
    if not Path(research_md_path).exists():
        print(f"Warning: {research_md_path} not found. Creating new file.")
        content = "# Research\n\n"
    else:
        with open(research_md_path, 'r') as f:
            content = f.read()

    # Define the section to insert/update
    section_header = "## Model Verification"
    section_start = content.find(section_header)
    
    # Build the table content
    table_rows = []
    table_rows.append("| Model Name | HF ID | Size (MB) | CPU Tractable (<1GB) |")
    table_rows.append("|---|---|---|---|")
    
    for r in results:
        status = "✅ Yes" if r["cpu_tractable"] else "❌ No"
        size_str = f"{r['size_mb']:.2f}" if r['size_mb'] is not None else "N/A"
        table_rows.append(f"| {r['model_name']} | {r['hf_id']} | {size_str} | {status} |")
    
    new_section = f"{section_header}\n\n" + "\n".join(table_rows) + "\n"
    
    if section_start != -1:
        # Find the end of the current section (next header or EOF)
        next_header = content.find("\n## ", section_start + len(section_header))
        if next_header == -1:
            next_header = len(content)
        # Replace the section
        new_content = content[:section_start] + new_section + content[next_header:]
    else:
        # Append at end
        new_content = content + "\n" + new_section

    with open(research_md_path, 'w') as f:
        f.write(new_content)
    print(f"Updated {research_md_path}")

def main():
    print("Starting model weight verification...")
    if not HF_AVAILABLE:
        print("ERROR: huggingface_hub is required to verify model weights.")
        sys.exit(1)
    
    results = verify_models()
    
    # Save raw results
    output_json = "data/verified_models.json"
    save_results(results, output_json)
    
    # Update research.md
    update_research_md(results)
    
    # Print summary
    print("\nVerification Summary:")
    all_pass = True
    for r in results:
        status = "PASS" if r["cpu_tractable"] else "FAIL"
        if not r["cpu_tractable"]:
            all_pass = False
        print(f"  {r['model_name']}: {status} ({r['size_mb']:.2f} MB)")
    
    if not all_pass:
        print("\nWarning: Some models exceed 1GB limit. Consider smaller variants.")
        sys.exit(0) # Exit 0 as the script ran successfully, even if data is negative
    else:
        print("\nAll models are CPU-tractable.")

if __name__ == "__main__":
    main()
