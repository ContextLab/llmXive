"""
Verify text dataset availability (DROP/MUST) via HuggingFace datasets.

This script checks the availability of the DROP and MUST datasets from HuggingFace,
computes basic statistics (size, variables), and updates the research.md file.

FR-001, Phase 0.1
"""

import os
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' package not found. Please install: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESEARCH_MD_PATH = PROJECT_ROOT / "research.md"
DATA_DIR = PROJECT_ROOT / "data"

# Datasets to verify
TEXT_DATASETS = [
    {
        "name": "DROP",
        "hf_id": "ucinl/drop",
        "description": "DROP: A Reading Comprehension Benchmark Requiring Discrete Reasoning Over Paragraphs",
        "url": "https://huggingface.co/datasets/ucinl/drop"
    },
    {
        "name": "MUST",
        "hf_id": "musr/must", 
        "description": "MUST: Multi-Modal Understanding and Reasoning Benchmark",
        "url": "https://huggingface.co/datasets/musr/must"
    }
]

def compute_dataset_checksum(dataset_name: str, split_name: str = "train") -> str:
    """Compute a simple checksum for a dataset split (based on sample count)."""
    try:
        # Load a small sample to get row count
        ds = load_dataset(dataset_name, split=split_name)
        count = len(ds)
        # Create a deterministic hash based on count and name
        data = f"{dataset_name}:{split_name}:{count}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Could not compute checksum for {dataset_name}: {e}")
        return "unavailable"

def estimate_dataset_size_mb(hf_id: str, split_name: str = "train") -> float:
    """
    Estimate dataset size in MB.
    For HuggingFace datasets, we load a small sample and estimate based on memory usage.
    """
    try:
        # Load with streaming to avoid downloading full dataset if large
        ds = load_dataset(hf_id, split=split_name, streaming=True)
        
        # Sample 100 examples to estimate size
        sample_size = 0
        count = 0
        max_samples = 100
        
        for item in ds:
            sample_size += len(str(item).encode('utf-8'))
            count += 1
            if count >= max_samples:
                break
        
        if count == 0:
            return 0.0
        
        avg_size_bytes = sample_size / count
        total_count = len(load_dataset(hf_id, split=split_name))
        estimated_total_bytes = avg_size_bytes * total_count
        estimated_mb = estimated_total_bytes / (1024 * 1024)
        
        return round(estimated_mb, 2)
    except Exception as e:
        logger.warning(f"Could not estimate size for {hf_id}: {e}")
        return 0.0

def get_dataset_variables(hf_id: str, split_name: str = "train") -> List[str]:
    """Get the list of variable names (columns) in the dataset."""
    try:
        ds = load_dataset(hf_id, split=split_name, streaming=True)
        # Get features/columns
        if hasattr(ds, 'features'):
            return list(ds.features.keys())
        else:
            # For streaming datasets, get first example keys
            for item in ds:
                return list(item.keys())
    except Exception as e:
        logger.warning(f"Could not get variables for {hf_id}: {e}")
        return []

def verify_dataset(dataset_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a single dataset's availability and collect metadata.
    
    Returns a dict with:
    - dataset_name
    - url
    - variables (list)
    - size_mb
    - verification_status (available/unavailable/partial)
    - checksum
    """
    name = dataset_config["name"]
    hf_id = dataset_config["hf_id"]
    url = dataset_config["url"]
    
    result = {
        "dataset_name": name,
        "url": url,
        "variables": [],
        "size_mb": 0.0,
        "verification_status": "unavailable",
        "checksum": "unknown"
    }
    
    try:
        logger.info(f"Verifying dataset: {name} ({hf_id})")
        
        # Try to load the dataset
        ds = load_dataset(hf_id, split="train", streaming=True)
        
        # Get variables
        variables = get_dataset_variables(hf_id)
        result["variables"] = variables
        
        # Estimate size
        size_mb = estimate_dataset_size_mb(hf_id)
        result["size_mb"] = size_mb
        
        # Compute checksum
        checksum = compute_dataset_checksum(hf_id)
        result["checksum"] = checksum
        
        if variables and size_mb > 0:
            result["verification_status"] = "available"
        elif variables:
            result["verification_status"] = "partial"
        else:
            result["verification_status"] = "unavailable"
            
        logger.info(f"✓ {name}: {len(variables)} variables, {size_mb} MB, status: {result['verification_status']}")
        
    except Exception as e:
        logger.error(f"✗ {name}: Failed to verify - {e}")
        result["verification_status"] = "unavailable"
    
    return result

def generate_verification_table(results: List[Dict[str, Any]]) -> str:
    """Generate a markdown table for the verification results."""
    if not results:
        return "No datasets verified."
    
    table = "| Dataset | URL | Variables | Size (MB) | Status |\n"
    table += "|---------|-----|-----------|-----------|--------|\n"
    
    for r in results:
        var_str = ", ".join(r["variables"][:5])  # Show first 5
        if len(r["variables"]) > 5:
            var_str += f" (+{len(r['variables'])-5} more)"
        
        table += f"| {r['dataset_name']} | {r['url']} | {var_str} | {r['size_mb']} | {r['verification_status']} |\n"
    
    return table

def update_research_md(results: List[Dict[str, Any]]) -> None:
    """Update research.md with the dataset verification section."""
    if not RESEARCH_MD_PATH.exists():
        logger.warning(f"research.md not found at {RESEARCH_MD_PATH}. Creating new file.")
        research_content = "# Research Documentation\n\n"
    else:
        research_content = RESEARCH_MD_PATH.read_text(encoding='utf-8')
    
    # Define the section to insert/update
    section_title = "## Dataset Verification"
    section_content = f"""
{section_title}

This section documents the verification of text datasets (DROP, MUST) for the benchmark.
Datasets are verified via HuggingFace datasets library.

### Verification Results

{generate_verification_table(results)}

### Details

"""
    
    # Add details for each dataset
    for r in results:
        section_content += f"""
#### {r['dataset_name']}

- **URL**: {r['url']}
- **Variables**: {', '.join(r['variables']) if r['variables'] else 'N/A'}
- **Estimated Size**: {r['size_mb']} MB
- **Status**: {r['verification_status']}
- **Checksum**: {r['checksum']}

"""
    
    # Insert or replace the section
    if section_title in research_content:
        # Find the section and replace it
        start_idx = research_content.find(section_title)
        # Find the next section (starts with ##) after this one
        next_section_idx = research_content.find("\n## ", start_idx + len(section_title))
        if next_section_idx == -1:
            next_section_idx = len(research_content)
        
        # Replace the section
        new_content = (
            research_content[:start_idx] + 
            section_content + 
            research_content[next_section_idx:]
        )
    else:
        # Append to end
        new_content = research_content + "\n" + section_content
    
    # Write back
    RESEARCH_MD_PATH.write_text(new_content, encoding='utf-8')
    logger.info(f"Updated {RESEARCH_MD_PATH} with verification results")

def main():
    """Main entry point for dataset verification."""
    logger.info("Starting text dataset verification...")
    
    results = []
    for dataset_config in TEXT_DATASETS:
        result = verify_dataset(dataset_config)
        results.append(result)
    
    # Generate and save table
    table = generate_verification_table(results)
    logger.info("\n" + table)
    
    # Update research.md
    update_research_md(results)
    
    # Summary
    available_count = sum(1 for r in results if r["verification_status"] == "available")
    logger.info(f"\nVerification complete: {available_count}/{len(results)} datasets available")
    
    return results

if __name__ == "__main__":
    main()