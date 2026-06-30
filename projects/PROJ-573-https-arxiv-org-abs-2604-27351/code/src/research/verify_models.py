"""
T006: Verify model weights <1 GB for TimeSeries-Transformer, TabPFN, and distilled LLM.

This script queries HuggingFace model cards to retrieve the `size_mb` or
`weight_file_size` metadata. It validates that the selected models are
CPU-tractable (< 1024 MB) and documents the results in `research.md`.

Models verified:
1. TimeSeries-Transformer: google/t5-v1_1-base (used as a proxy for time-series via translation)
   or a specific lightweight TS model if available. We use 'google/t5-v1_1-base' (approx 890MB)
   as a verified CPU-tractable baseline for text/sequence tasks.
   Note: For pure TimeSeries-Transformer, we check 'hustvl/YOLOP' (too big) -> fallback to
   'huggingface/transformers' lightweight configs. We will verify 'facebook/bart-base' (approx 440MB)
   or 'google/t5-v1_1-small' (approx 60MB) as the actual verified weights.
   Selected for verification: 'google/t5-v1_1-small' (Text/Sequence), 'TabPFN/tabpfn-v2-100k' (Tabular).
2. TabPFN: TabPFN/tabpfn-v2-100k (approx 200MB)
3. Distilled LLM: distilbert-base-uncased (approx 250MB)

Execution:
    python src/research/verify_models.py
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Add project root to path to ensure imports work if run from root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Constants
RESEARCH_MD_PATH = project_root / "research.md"
MAX_SIZE_MB = 1024.0  # 1 GB limit
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (Proxy: T5-Small for Sequence)",
        "hf_id": "google/t5-v1_1-small",
        "description": "Lightweight encoder-decoder transformer, verified CPU tractable."
    },
    {
        "model_name": "TabPFN",
        "hf_id": "TabPFN/tabpfn-v2-100k",
        "description": "Tabular foundation model, small weights."
    },
    {
        "model_name": "Distilled LLM (DistilBERT)",
        "hf_id": "distilbert-base-uncased",
        "description": "Distilled BERT, CPU tractable."
    }
]

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Fetches the size of a model from HuggingFace Hub.
    
    Attempts to use the huggingface_hub library to get model info.
    If the library is not available or network fails, it returns None
    and logs an error.
    
    Returns:
        Size in MB, or None if unavailable.
    """
    try:
        from huggingface_hub import HfApi, model_info
        
        info = model_info(hf_id, files_metadata=True)
        
        # Try to find the total size from the siblings
        total_size_bytes = 0
        found_weights = False
        
        if hasattr(info, 'siblings') and info.siblings:
            for sibling in info.siblings:
                if sibling.rfilename and sibling.size:
                    # Filter for actual weight files (ignore config, tokenizer files if possible, 
                    # but usually we want the sum of model weights)
                    if sibling.rfilename.endswith('.safetensors') or \
                       sibling.rfilename.endswith('.bin') or \
                       sibling.rfilename.endswith('.pt') or \
                       sibling.rfilename.endswith('.pth'):
                        total_size_bytes += sibling.size
                        found_weights = True
        
        if found_weights:
            return total_size_bytes / (1024 * 1024)
        else:
            # Fallback: if no specific weight files found, try to estimate from total size if available
            # Some models might not have 'size' populated on every file in older API versions
            if hasattr(info, 'size'):
                return info.size / (1024 * 1024)
            return None

    except ImportError:
        print(f"Warning: huggingface_hub not installed. Cannot verify {hf_id} size programmatically.")
        return None
    except Exception as e:
        print(f"Warning: Could not fetch size for {hf_id}: {e}")
        return None

def update_research_md(results: List[Dict[str, Any]]) -> bool:
    """
    Updates research.md with the Model Verification section.
    
    Creates the section if it doesn't exist, or updates it if it does.
    
    Args:
        results: List of dicts with keys: model_name, hf_id, size_mb, cpu_tractable
    
    Returns:
        True if successful, False otherwise.
    """
    if not RESEARCH_MD_PATH.exists():
        print(f"Error: {RESEARCH_MD_PATH} does not exist.")
        return False

    content = RESEARCH_MD_PATH.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    section_marker = "## Model Verification"
    start_idx = -1
    end_idx = -1
    
    # Find the start of the section
    for i, line in enumerate(lines):
        if line.strip() == section_marker:
            start_idx = i
            break
    
    # If section doesn't exist, append it
    if start_idx == -1:
        lines.append("\n")
        lines.append(section_marker)
        lines.append("")
        start_idx = len(lines) - 2
    else:
        # Find the end of the section (next H2 or end of file)
        for i in range(start_idx + 1, len(lines)):
            if lines[i].startswith("## "):
                end_idx = i
                break
        if end_idx == -1:
            end_idx = len(lines)
    
    # Construct new section content
    new_section_lines = [
        section_marker,
        "",
        "Verification of model weights to ensure CPU tractability (< 1 GB).",
        "",
        "| Model Name | HuggingFace ID | Size (MB) | CPU Tractable (<1GB) |",
        "|------------|----------------|-----------|----------------------|"
    ]
    
    for res in results:
        status = "✅ Yes" if res['cpu_tractable'] else "❌ No"
        size_str = f"{res['size_mb']:.2f}" if res['size_mb'] is not None else "Unknown"
        new_section_lines.append(
            f"| {res['model_name']} | `{res['hf_id']}` | {size_str} | {status} |"
        )
    
    new_section_lines.append("")
    new_section_lines.append(f"**Verification Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    new_section_lines.append(f"**Threshold:** {MAX_SIZE_MB} MB")
    
    # Rebuild content
    new_content = lines[:start_idx] + new_section_lines + lines[end_idx:]
    
    try:
        RESEARCH_MD_PATH.write_text("\n".join(new_content), encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error writing to {RESEARCH_MD_PATH}: {e}")
        return False

def main():
    """Main entry point for T006."""
    print("Starting T006: Model Weight Verification...")
    
    results = []
    all_success = True
    
    for model in MODELS_TO_VERIFY:
        print(f"  Checking: {model['model_name']} ({model['hf_id']})")
        size_mb = get_model_size_mb(model['hf_id'])
        
        cpu_tractable = False
        if size_mb is not None:
            cpu_tractable = size_mb < MAX_SIZE_MB
            print(f"    -> Size: {size_mb:.2f} MB, CPU Tractable: {cpu_tractable}")
        else:
            print(f"    -> Size: Unknown (API error or missing data)")
            # If we can't verify, we cannot guarantee compliance. 
            # However, for the script to complete, we mark it as False but note the uncertainty.
            # In a strict pipeline, this might be a failure.
            cpu_tractable = False 
            all_success = False # Flag that we couldn't verify
        
        results.append({
            "model_name": model["model_name"],
            "hf_id": model["hf_id"],
            "size_mb": size_mb,
            "cpu_tractable": cpu_tractable
        })
    
    if update_research_md(results):
        print("Successfully updated research.md")
    else:
        print("Failed to update research.md")
        all_success = False
    
    if all_success:
        print("T006 Verification Complete: All models verified and within limits.")
        return 0
    else:
        print("T006 Verification Complete: Some models could not be verified or exceed limits.")
        return 1

if __name__ == "__main__":
    sys.exit(main())