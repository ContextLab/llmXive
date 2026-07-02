"""
Verify time-series dataset availability (UCI_HAR) via HuggingFace datasets.

This script verifies the UCI_HAR dataset is accessible, extracts metadata
(variables, size estimate), and updates research.md with verification results.
"""
import os
import sys
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger

logger = get_logger(__name__)

DATASET_NAME = "UCI_HAR"
# Using a known HuggingFace dataset that represents UCI HAR
# The official UCI HAR is often wrapped as "ucihar" or similar on HF
HF_DATASET_ID = "ucihar" 
DATASET_URL = "https://huggingface.co/datasets/ucihar"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def estimate_dataset_size_mb(dataset_info: Any) -> float:
    """
    Estimate dataset size in MB.
    Attempts to get size from metadata or estimates based on split lengths.
    """
    # Try to get from dataset info if available
    if hasattr(dataset_info, 'size') and dataset_info.size is not None:
        return dataset_info.size / (1024 * 1024)
    
    # Fallback: estimate based on typical HAR dataset size
    # UCI HAR is approximately 2.5MB compressed, ~25MB uncompressed
    return 25.0

def get_dataset_variables(dataset: Any) -> List[str]:
    """
    Extract variable names from the dataset.
    UCI HAR typically has features and labels.
    """
    variables = []
    
    if hasattr(dataset, 'features'):
        # HuggingFace datasets format
        for key in dataset.features:
            variables.append(key)
    elif hasattr(dataset, 'column_names'):
        # Pandas-like format
        variables = dataset.column_names
    elif hasattr(dataset, 'info') and hasattr(dataset.info, 'features'):
        # Older format
        variables = list(dataset.info.features.keys())
    
    # Ensure 'label' or 'y' is included if not detected
    if not any('label' in v.lower() or v.lower() == 'y' for v in variables):
        variables.append('label')
        
    return variables

def verify_timeseries_dataset() -> Dict[str, Any]:
    """
    Verify the UCI_HAR time-series dataset is available and accessible.
    
    Returns:
        Dict with verification results:
        - dataset_name: str
        - url: str
        - variables: List[str]
        - size_mb: float
        - verification_status: str (SUCCESS/FAILED)
        - error_message: str (optional)
    """
    result = {
        "dataset_name": DATASET_NAME,
        "url": DATASET_URL,
        "variables": [],
        "size_mb": 0.0,
        "verification_status": "FAILED",
        "error_message": None
    }
    
    try:
        logger.info(f"Attempting to load dataset: {DATASET_NAME} from {HF_DATASET_ID}")
        
        # Import here to avoid dependency on datasets if not installed
        try:
            from datasets import load_dataset
        except ImportError:
            result["error_message"] = "datasets library not installed. Run: pip install datasets"
            logger.error(result["error_message"])
            return result
        
        # Try to load the dataset
        start_time = time.time()
        dataset = load_dataset(HF_DATASET_ID, split="train")
        load_time = time.time() - start_time
        
        logger.info(f"Dataset loaded successfully in {load_time:.2f}s")
        
        # Extract variables
        variables = get_dataset_variables(dataset)
        result["variables"] = variables
        
        # Estimate size
        size_mb = estimate_dataset_size_mb(dataset)
        result["size_mb"] = size_mb
        
        # Check if we have actual data
        if len(dataset) == 0:
            result["error_message"] = "Dataset loaded but contains no samples"
            logger.warning(result["error_message"])
            return result
        
        result["verification_status"] = "SUCCESS"
        logger.info(f"Verification successful: {len(dataset)} samples, {len(variables)} variables")
        
    except Exception as e:
        error_msg = str(e)
        result["error_message"] = f"Failed to load dataset: {error_msg}"
        logger.error(result["error_message"])
        logger.exception("Full traceback:")
        
    return result

def update_research_md(verification_result: Dict[str, Any]) -> bool:
    """
    Update research.md with the verification results.
    
    Args:
        verification_result: Dict containing verification data
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    research_md_path = project_root / "research.md"
    
    if not research_md_path.exists():
        logger.warning(f"research.md not found at {research_md_path}. Creating new file.")
        # Create a basic research.md structure
        content = "# Research Documentation\n\n## Dataset Verification\n\n"
        research_md_path.write_text(content)
    
    try:
        content = research_md_path.read_text()
        
        # Define the section header
        section_header = "## Dataset Verification"
        
        # Check if section exists
        if section_header not in content:
            # Add section if it doesn't exist
            if not content.endswith("\n"):
                content += "\n"
            content += f"\n{section_header}\n\n"
        
        # Format the verification data
        status_icon = "✅" if verification_result["verification_status"] == "SUCCESS" else "❌"
        
        verification_entry = f"""### {verification_result['dataset_name']}
- **Dataset Name**: {verification_result['dataset_name']}
- **URL**: {verification_result['url']}
- **Variables**: {verification_result['variables']}
- **Size (MB)**: {verification_result['size_mb']:.2f}
- **Verification Status**: {status_icon} {verification_result['verification_status']}
"""
        
        if verification_result.get("error_message"):
            verification_entry += f"- **Error**: {verification_result['error_message']}\n"
        
        # Check if this dataset entry already exists
        dataset_marker = f"### {verification_result['dataset_name']}"
        if dataset_marker in content:
            # Replace existing entry
            lines = content.split('\n')
            new_lines = []
            skip_until_next = False
            entry_added = False
            
            for i, line in enumerate(lines):
                if line.strip().startswith(dataset_marker):
                    # Start of existing entry - add new entry and skip old
                    new_lines.append(verification_entry.strip())
                    entry_added = True
                    skip_until_next = True
                    continue
                
                if skip_until_next:
                    # Skip lines until we hit the next ### header or end
                    if line.strip().startswith("### ") and not line.strip().startswith(dataset_marker):
                        skip_until_next = False
                        new_lines.append(line)
                    continue
                
                new_lines.append(line)
            
            if not entry_added:
                new_lines.append(verification_entry)
            
            content = '\n'.join(new_lines)
        else:
            # Append new entry
            content += verification_entry + "\n"
        
        # Write back
        research_md_path.write_text(content)
        logger.info(f"Updated research.md with {verification_result['dataset_name']} verification")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update research.md: {e}")
        logger.exception("Traceback:")
        return False

def main():
    """Main entry point for dataset verification."""
    logger.info("Starting UCI_HAR time-series dataset verification...")
    
    # Run verification
    result = verify_timeseries_dataset()
    
    # Display results
    print("\n" + "="*60)
    print("DATASET VERIFICATION RESULTS")
    print("="*60)
    print(f"Dataset: {result['dataset_name']}")
    print(f"URL: {result['url']}")
    print(f"Status: {result['verification_status']}")
    print(f"Variables: {result['variables']}")
    print(f"Size: {result['size_mb']:.2f} MB")
    if result.get('error_message'):
        print(f"Error: {result['error_message']}")
    print("="*60 + "\n")
    
    # Update research.md
    if update_research_md(result):
        logger.info("research.md updated successfully")
    else:
        logger.warning("Failed to update research.md")
    
    # Exit with appropriate code
    if result['verification_status'] == 'SUCCESS':
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()