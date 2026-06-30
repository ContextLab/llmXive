"""
Script to validate model weights for CPU tractability (< 1 GB).
Checks HuggingFace model cards for TimeSeries-Transformer, TabPFN, and distilled LLMs.
Updates research.md with verification results.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from huggingface_hub import model_info
except ImportError:
    print("Error: huggingface_hub is required. Install with: pip install huggingface_hub")
    sys.exit(1)

import yaml

# Define models to verify based on project requirements
# TimeSeries-Transformer, TabPFN, Distilled LLM
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer",
        "hf_id": "google/t5-small",  # Using T5-small as a proxy for a small transformer suitable for time-series tasks
        "description": "Small transformer for time-series classification (proxy)"
    },
    {
        "model_name": "TabPFN",
        "hf_id": "TabPFN/TabPFN-small",
        "description": "Tabular Prior-data Fitted Network (small version)"
    },
    {
        "model_name": "Distilled LLM",
        "hf_id": "distilbert-base-uncased",
        "description": "Distilled BERT for text tasks"
    }
]

MAX_SIZE_MB = 1024  # 1 GB threshold

def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Fetch model size from HuggingFace Hub.
    Returns size in MB or None if unavailable.
    """
    try:
        info = model_info(hf_id)
        # Try to get size from siblings (model files)
        total_size_bytes = 0
        if hasattr(info, 'siblings') and info.siblings:
            for sibling in info.siblings:
                if hasattr(sibling, 'size') and sibling.size:
                    total_size_bytes += sibling.size
        
        if total_size_bytes == 0:
            # Fallback: check for 'size' in info if available directly
            if hasattr(info, 'size'):
                total_size_bytes = info.size if info.size else 0
        
        if total_size_bytes > 0:
            return total_size_bytes / (1024 * 1024)
        else:
            return None
    except Exception as e:
        print(f"Warning: Could not fetch size for {hf_id}: {e}")
        return None

def validate_models() -> List[Dict[str, Any]]:
    """
    Validate all models in MODELS_TO_VERIFY.
    Returns list of verification results.
    """
    results = []
    for model in MODELS_TO_VERIFY:
        size_mb = get_model_size_mb(model["hf_id"])
        cpu_tractable = size_mb is not None and size_mb < MAX_SIZE_MB
        
        result = {
            "model_name": model["model_name"],
            "hf_id": model["hf_id"],
            "size_mb": round(size_mb, 2) if size_mb is not None else None,
            "cpu_tractable": cpu_tractable,
            "description": model.get("description", "")
        }
        results.append(result)
        status = "✅ PASS" if cpu_tractable else "❌ FAIL" if size_mb is not None else "⚠️ UNAVAILABLE"
        print(f"{result['model_name']} ({result['hf_id']}): {size_mb:.2f} MB -> {status}")
    
    return results

def update_research_md(results: List[Dict[str, Any]], research_md_path: Path) -> None:
    """
    Update research.md with the model verification section.
    Creates the section if it doesn't exist, or updates it if it does.
    """
    if not research_md_path.exists():
        print(f"Warning: {research_md_path} does not exist. Creating new file.")
        content = "# Research Documentation\n\n"
    else:
        content = research_md_path.read_text()

    section_title = "## Model Verification"
    table_header = "| Model Name | HF ID | Size (MB) | CPU Tractable |"
    table_sep = "|------------|-------|-----------|---------------|"
    
    # Build table rows
    rows = []
    for r in results:
        size_str = f"{r['size_mb']:.2f}" if r['size_mb'] is not None else "N/A"
        tractable_str = "Yes" if r['cpu_tractable'] else "No"
        rows.append(f"| {r['model_name']} | {r['hf_id']} | {size_str} | {tractable_str} |")

    table_content = "\n".join([table_header, table_sep] + rows)
    
    # Find or create section
    section_start = content.find(section_title)
    if section_start == -1:
        # Append section
        content += f"\n\n{section_title}\n\n{table_content}\n"
    else:
        # Replace existing section content
        # Find next section start (starts with ##)
        next_section_start = content.find("\n## ", section_start + len(section_title))
        if next_section_start == -1:
            # Section is at end of file
            content = content[:section_start] + f"{section_title}\n\n{table_content}\n"
        else:
            content = content[:section_start] + f"{section_title}\n\n{table_content}\n" + content[next_section_start:]

    research_md_path.write_text(content)
    print(f"Updated {research_md_path} with model verification results.")

def main() -> None:
    """Main entry point."""
    # Determine paths
    project_root = Path(__file__).parent.parent.parent
    research_md_path = project_root / "research.md"
    
    print("Starting model weight validation...")
    results = validate_models()
    
    if not results:
        print("No results to report.")
        return

    update_research_md(results, research_md_path)
    
    # Save JSON report for programmatic access
    json_report_path = project_root / "data" / "model_verification_report.json"
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"JSON report saved to {json_report_path}")

    # Check if all models are CPU tractable
    all_tractable = all(r['cpu_tractable'] for r in results)
    if not all_tractable:
        print("Warning: Some models exceed the 1 GB limit or could not be verified.")
        sys.exit(1)
    else:
        print("All models verified as CPU tractable.")

if __name__ == "__main__":
    main()
