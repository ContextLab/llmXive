import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from huggingface_hub import HfApi, hf_hub_download, model_info
except ImportError:
    print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
    sys.exit(1)

from src.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Define models to verify based on task requirements
# Target: TimeSeries-Transformer, TabPFN, Distilled LLM
MODELS_TO_VERIFY = [
    {
        "model_name": "TimeSeries-Transformer (Small)",
        "hf_id": "google/t5-small", # Using T5-small as a proxy for a small transformer backbone often used in time-series or as a base. 
                                   # Note: Specific "TimeSeries-Transformer" might not have a single canonical HF ID <1GB without specific repo.
                                   # We will verify T5-small as a representative small transformer model for the architecture class.
                                   # If a specific time-series model repo exists <1GB, it should be swapped here.
        "target_size_gb": 1.0,
        "description": "Small Transformer backbone (proxy for TimeSeries-Transformer architecture)"
    },
    {
        "model_name": "TabPFN",
        "hf_id": "PriorLabs/TabPFN-v1",
        "target_size_gb": 1.0,
        "description": "Tabular Foundation Model"
    },
    {
        "model_name": "Distilled LLM",
        "hf_id": "distilbert/distilbert-base-uncased",
        "target_size_gb": 1.0,
        "description": "Distilled BERT model for text tasks"
    }
]

def get_model_size_mb(hf_id: str) -> float:
    """
    Fetches the total size of a model repository in MB.
    Uses HuggingFace Hub API to list files and sum their sizes.
    """
    try:
        api = HfApi()
        # Get model info including files if available, or list files
        # Note: model_info might not always return full file list with sizes directly in all versions,
        # so we list files explicitly.
        files = api.list_repo_files(repo_id=hf_id, repo_type="model")
        
        total_bytes = 0
        for file_path in files:
            # We need file size. list_repo_files doesn't give size directly in all contexts.
            # We use model_info with files_metadata=True if supported, or fetch specific file info.
            # A robust way for large repos is to use the API's file info endpoint.
            try:
                # Attempt to get file info for size
                # HuggingFace Hub API via python library often requires specific calls
                # Let's use the direct API approach for file size if possible, or estimate by known patterns.
                # For now, we use model_info which often includes siblings with sizes if available.
                pass 
            except Exception:
                pass

        # Fallback: Use model_info which often returns siblings with size
        try:
            info = model_info(hf_id, files_metadata=True)
            if hasattr(info, 'siblings') and info.siblings:
                for sibling in info.siblings:
                    if hasattr(sibling, 'size') and sibling.size:
                        total_bytes += sibling.size
                    elif hasattr(sibling, 'lfs') and sibling.lfs:
                        total_bytes += sibling.lfs.size
            else:
                # If metadata not available, we might need to fetch individual file headers
                # For this task, we assume model_info with files_metadata=True works.
                # If not, we estimate based on common model sizes or return a flag.
                logger.warning(f"Could not retrieve file sizes for {hf_id} via model_info. Estimating.")
                # Fallback estimation logic if API fails (e.g. network, auth)
                # This is a last resort and should be logged as such.
                # We will not fabricate. We will raise if we can't measure.
                raise RuntimeError("Could not determine model size from API metadata.")
            
            size_mb = total_bytes / (1024 * 1024)
            return size_mb
        except Exception as e:
            logger.error(f"Failed to get model info for {hf_id}: {e}")
            # If we cannot get the size, we cannot verify the constraint.
            # We return -1 to indicate failure to measure, not a fabricated value.
            return -1.0

    except Exception as e:
        logger.error(f"Error fetching model info for {hf_id}: {e}")
        return -1.0

def update_research_md(results: List[Dict[str, Any]], research_md_path: str) -> None:
    """
    Updates research.md with the Model Verification section.
    Creates the section if it doesn't exist, otherwise appends/updates the table.
    """
    path = Path(research_md_path)
    if not path.exists():
        logger.warning(f"research.md not found at {research_md_path}. Creating new file.")
        content = "# Research Documentation\n\n"
    else:
        content = path.read_text()

    section_header = "## Model Verification"
    table_start_marker = "| Model Name | HF ID | Size (MB) | CPU Tractable (<1GB) |"
    
    # Check if section exists
    if section_header not in content:
        content += f"\n\n{section_header}\n\n"
        content += f"Verification of model weights for CPU-tractable inference (Constraint: < 1 GB).\n\n"
    
    # Find the table section
    lines = content.split('\n')
    new_lines = []
    table_found = False
    in_table = False
    table_end_index = -1

    for i, line in enumerate(lines):
        if table_start_marker in line:
            table_found = True
            in_table = True
            # Write header and separator
            new_lines.append(line) # Header
            if i+1 < len(lines) and "|" in lines[i+1] and "---" in lines[i+1]:
                new_lines.append(lines[i+1]) # Separator
                table_end_index = i + 1
            else:
                # Add separator if missing
                new_lines.append("| :--- | :--- | :--- | :--- |")
                table_end_index = i + 1
            continue
        
        if in_table and line.startswith('|'):
            # Skip existing data rows to replace them
            continue
        
        if in_table and not line.startswith('|'):
            # End of table
            in_table = False
            table_end_index = i
            # We will insert new rows before this line
            break
        
        new_lines.append(line)

    # Construct new table rows
    new_rows = []
    for res in results:
        cpu_tractable = "Yes" if res.get('cpu_tractable', False) else "No"
        row = f"| {res['model_name']} | {res['hf_id']} | {res['size_mb']:.2f} | {cpu_tractable} |"
        new_rows.append(row)

    # Reconstruct content
    final_content = '\n'.join(new_lines)
    
    # If table was found, we need to inject rows at table_end_index
    if table_found and table_end_index >= 0:
        # Split at table_end_index
        before = final_content.split('\n', table_end_index)[0] # This logic is tricky with split
        # Better: reconstruct list
        final_lines = new_lines[:table_end_index+1] # Keep header and separator
        final_lines.extend(new_rows)
        final_lines.extend(lines[table_end_index+1:]) # Rest of file
        final_content = '\n'.join(final_lines)
    elif not table_found:
        # Append table at end of section
        final_content += "\n" + table_start_marker + "\n| :--- | :--- | :--- | :--- |\n"
        for row in new_rows:
            final_content += row + "\n"

    path.write_text(final_content)
    logger.info(f"Updated {research_md_path} with model verification results.")

def verify_models() -> List[Dict[str, Any]]:
    """
    Verifies the specified models and returns results.
    """
    results = []
    for model in MODELS_TO_VERIFY:
        logger.info(f"Verifying model: {model['model_name']} ({model['hf_id']})")
        size_mb = get_model_size_mb(model['hf_id'])
        
        if size_mb < 0:
            # Failed to measure
            results.append({
                "model_name": model['model_name'],
                "hf_id": model['hf_id'],
                "size_mb": 0.0, # 0 indicates failure to measure
                "cpu_tractable": False,
                "status": "ERROR",
                "message": "Could not retrieve model size from HuggingFace Hub"
            })
            continue

        cpu_tractable = size_mb < model['target_size_gb'] * 1024 # Convert GB to MB
        
        results.append({
            "model_name": model['model_name'],
            "hf_id": model['hf_id'],
            "size_mb": size_mb,
            "cpu_tractable": cpu_tractable,
            "status": "OK"
        })
        
        status_str = "PASS" if cpu_tractable else "FAIL"
        logger.info(f"  -> Size: {size_mb:.2f} MB, CPU Tractable: {cpu_tractable} [{status_str}]")

    return results

def main():
    """
    Main entry point for the verification script.
    """
    # Determine paths
    project_root = Path(__file__).resolve().parent.parent.parent
    research_md_path = project_root / "research.md"
    
    logger.info(f"Starting model verification. Research MD: {research_md_path}")
    
    results = verify_models()
    
    # Update documentation
    update_research_md(results, str(research_md_path))
    
    # Print summary
    print("\n--- Model Verification Summary ---")
    for r in results:
        print(f"{r['model_name']}: {r['size_mb']:.2f} MB | CPU Tractable: {r['cpu_tractable']}")
    
    # Return exit code based on results
    all_pass = all(r['cpu_tractable'] for r in results if r['status'] == 'OK')
    if not all_pass:
        print("\nWARNING: One or more models exceed the 1GB CPU tractability limit.")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
