import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from huggingface_hub import HfApi, model_info
from huggingface_hub.utils import RepositoryNotFoundError, RevisionNotFoundError

from src.utils.logging import get_logger

# Configuration: Models to verify against the <1 GB CPU tractability constraint
# These are representative CPU-tractable foundation models for the required modalities.
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (Small)",
        "hf_id": "google/t5-small",  # Placeholder for a small transformer often used as base for TS; in real impl, swap for specific TS model like 't5-small' or a distilled variant
        "description": "Small transformer backbone suitable for time-series fine-tuning"
    },
    {
        "model_name": "TabPFN (Small)",
        "hf_id": "Pfml-Research/TabPFN-small",
        "description": "Tabular foundation model, known to be lightweight"
    },
    {
        "model_name": "Distilled LLM (Text)",
        "hf_id": "distilbert/distilbert-base-uncased",
        "description": "Distilled BERT for text tasks, <1GB"
    }
]

# Fallback models if the primary ones are not found or too large
FALLBACK_MODELS = [
    {
        "model_name": "TabPFN (Fallback)",
        "hf_id": "Pfml-Research/TabPFN-base",
        "description": "Base TabPFN if small is unavailable"
    },
    {
        "model_name": "DistilBERT (Fallback)",
        "hf_id": "distilbert/distilbert-base-uncased",
        "description": "Standard distilled BERT"
    }
]

logger = get_logger(__name__)

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Fetches the size of a model's files from HuggingFace Hub.
    Returns size in MB. Returns None if the model cannot be found or accessed.
    """
    try:
        api = HfApi()
        # Get model info including siblings (files)
        info = model_info(hf_id)
        
        total_bytes = 0
        if info.siblings:
            for sibling in info.siblings:
                if sibling.size:
                    # Filter for relevant model files (safetensors, bin, pt)
                    if any(sibling.rfilename.endswith(ext) for ext in ['.safetensors', '.bin', '.pt', '.pth']):
                        total_bytes += sibling.size
        
        size_mb = total_bytes / (1024 * 1024)
        return size_mb
    except (RepositoryNotFoundError, RevisionNotFoundError) as e:
        logger.warning(f"Model {hf_id} not found or inaccessible: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching info for {hf_id}: {e}")
        return None

def verify_models() -> List[Dict[str, Any]]:
    """
    Verifies the size of configured models against the <1 GB constraint.
    Returns a list of verification results.
    """
    results = []
    
    for model_config in MODELS_TO_VERIFY:
        hf_id = model_config["hf_id"]
        size_mb = get_model_size_mb(hf_id)
        
        is_cpu_tractable = False
        if size_mb is not None:
            is_cpu_tractable = size_mb < 1024  # 1 GB = 1024 MB
        
        result = {
            "model_name": model_config["model_name"],
            "hf_id": hf_id,
            "size_mb": round(size_mb, 2) if size_mb is not None else None,
            "cpu_tractable": is_cpu_tractable,
            "status": "verified" if size_mb is not None else "failed_to_fetch"
        }
        results.append(result)
        logger.info(f"Verified {model_config['model_name']}: {size_mb} MB, Tractable: {is_cpu_tractable}")
    
    return results

def update_research_md(results: List[Dict[str, Any]], research_md_path: Path) -> None:
    """
    Appends or updates the 'Model Verification' section in research.md.
    """
    section_header = "## Model Verification"
    section_start = -1
    
    if research_md_path.exists():
        content = research_md_path.read_text()
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == section_header:
                section_start = i
                break
        
        # Prepare new content
        new_section_lines = [section_header, "", "Verifying model weights for CPU tractability (< 1 GB):", ""]
        new_section_lines.append("| Model Name | HF ID | Size (MB) | CPU Tractable |")
        new_section_lines.append("| :--- | :--- | :--- | :--- |")
        
        for res in results:
            size_str = f"{res['size_mb']:.2f}" if res['size_mb'] is not None else "N/A"
            tractable_str = "✅" if res['cpu_tractable'] else "❌"
            new_section_lines.append(f"| {res['model_name']} | {res['hf_id']} | {size_str} | {tractable_str} |")
        
        new_section_lines.append("")
        
        if section_start != -1:
            # Replace existing section
            # Find the next header to determine section end
            next_header_idx = -1
            for i in range(section_start + 1, len(lines)):
                if lines[i].startswith("## "):
                    next_header_idx = i
                    break
            
            if next_header_idx == -1:
                next_header_idx = len(lines)
            
            # Reconstruct file
            new_content = lines[:section_start] + new_section_lines + lines[next_header_idx:]
            research_md_path.write_text("\n".join(new_content))
            logger.info(f"Updated {research_md_path} with new Model Verification section.")
        else:
            # Append to end
            with open(research_md_path, "a") as f:
                f.write("\n".join(new_section_lines))
            logger.info(f"Appended Model Verification section to {research_md_path}.")
    else:
        # Create new file with minimal structure
        new_content = [
            "# Research Documentation",
            "",
            "## Dataset Verification",
            "",
            section_header,
            "",
            "Verifying model weights for CPU tractability (< 1 GB):",
            "",
            "| Model Name | HF ID | Size (MB) | CPU Tractable |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for res in results:
            size_str = f"{res['size_mb']:.2f}" if res['size_mb'] is not None else "N/A"
            tractable_str = "✅" if res['cpu_tractable'] else "❌"
            new_content.append(f"| {res['model_name']} | {res['hf_id']} | {size_str} | {tractable_str} |")
        new_content.append("")
        
        research_md_path.write_text("\n".join(new_content))
        logger.info(f"Created new {research_md_path} with Model Verification section.")

def main():
    """
    Main entry point for the model verification task.
    """
    # Determine paths
    project_root = Path(__file__).resolve().parent.parent.parent
    research_md_path = project_root / "research.md"
    output_json_path = project_root / "data" / "model_verification_results.json"
    
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting model verification for T006...")
    
    results = verify_models()
    
    # Save raw results to JSON
    with open(output_json_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved raw results to {output_json_path}")
    
    # Update research.md
    update_research_md(results, research_md_path)
    
    # Check for failures
    failures = [r for r in results if not r['cpu_tractable'] or r['status'] == 'failed_to_fetch']
    if failures:
        logger.warning(f"Verification failed for {len(failures)} models. See report for details.")
    else:
        logger.info("All models verified successfully as CPU tractable.")
    
    return results

if __name__ == "__main__":
    main()
