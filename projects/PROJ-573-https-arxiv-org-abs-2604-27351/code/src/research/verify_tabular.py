"""
Verify tabular dataset availability (selected UCI sets) via HuggingFace datasets.

This script verifies the existence and basic properties of tabular datasets
from the HuggingFace datasets library, specifically selected UCI repository sets.

It generates a verification report and updates research.md with the findings.
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
    print("ERROR: 'datasets' library not found. Please install it: pip install datasets")
    sys.exit(1)

from src.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Define the tabular datasets to verify (selected UCI sets available on HF)
# Using real, publicly available UCI datasets on HuggingFace
TABULAR_DATASETS = [
    {
        "name": "UCI Adult",
        "hf_id": "uciml/adult",
        "description": "Adult Income Prediction dataset from UCI",
        "variables": ["age", "workclass", "fnlwgt", "education", "education-num", 
                     "marital-status", "occupation", "relationship", "race", "sex", 
                     "capital-gain", "capital-loss", "hours-per-week", "native-country", "income"]
    },
    {
        "name": "UCI Heart Disease",
        "hf_id": "chemb16/heart_disease_uci",
        "description": "Heart Disease dataset from UCI",
        "variables": ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", 
                     "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"]
    },
    {
        "name": "UCI Wine Quality Red",
        "hf_id": "uciml/wine-quality-red",
        "description": "Wine Quality Red dataset from UCI",
        "variables": ["fixed acidity", "volatile acidity", "citric acid", "residual sugar",
                     "chlorides", "free sulfur dioxide", "total sulfur dioxide", "density",
                     "pH", "sulphates", "alcohol", "quality"]
    }
]

def estimate_dataset_size_mb(dataset_name: str, hf_id: str) -> float:
    """
    Estimate the size of a dataset in MB by loading a small sample and extrapolating.
    
    Args:
        dataset_name: Name of the dataset
        hf_id: HuggingFace dataset identifier
        
    Returns:
        Estimated size in MB
    """
    logger.info(f"Estimating size for {dataset_name} ({hf_id})...")
    
    try:
        # Load just the first few rows to estimate
        dataset = load_dataset(hf_id, split="train", streaming=True)
        
        # Sample 100 rows to estimate average row size
        sample_count = 100
        sample_size_bytes = 0
        count = 0
        
        for row in dataset:
            # Convert row to string to estimate size
            row_str = str(row)
            sample_size_bytes += len(row_str.encode('utf-8'))
            count += 1
            if count >= sample_count:
                break
        
        if count == 0:
            logger.warning(f"No data found for {dataset_name}")
            return 0.0
        
        avg_row_size = sample_size_bytes / count
        
        # Estimate total size based on known dataset sizes or default assumption
        # For UCI datasets, typical sizes range from 100 to 10000 rows
        # We'll use a conservative estimate based on the dataset description
        estimated_rows = 1000  # Default assumption, would need actual dataset metadata for precision
        
        # Try to get actual size from dataset info if available
        try:
            full_dataset = load_dataset(hf_id, split="train", streaming=False)
            actual_rows = len(full_dataset)
            estimated_rows = actual_rows
        except Exception:
            pass  # Use default if we can't get actual count
        
        estimated_size_bytes = avg_row_size * estimated_rows
        estimated_size_mb = estimated_size_bytes / (1024 * 1024)
        
        logger.info(f"Estimated {dataset_name} size: {estimated_size_mb:.2f} MB ({estimated_rows} rows)")
        return estimated_size_mb
        
    except Exception as e:
        logger.error(f"Error estimating size for {dataset_name}: {e}")
        return 0.0

def compute_dataset_checksum(dataset_name: str, hf_id: str) -> Optional[str]:
    """
    Compute a checksum for the dataset by hashing sample data.
    
    Args:
        dataset_name: Name of the dataset
        hf_id: HuggingFace dataset identifier
        
    Returns:
        Hex string checksum or None if failed
    """
    logger.info(f"Computing checksum for {dataset_name}...")
    
    try:
        dataset = load_dataset(hf_id, split="train", streaming=True)
        
        hasher = hashlib.sha256()
        count = 0
        
        # Hash first 1000 rows for checksum
        for row in dataset:
            row_str = str(row)
            hasher.update(row_str.encode('utf-8'))
            count += 1
            if count >= 1000:
                break
        
        checksum = hasher.hexdigest()
        logger.info(f"Checksum computed for {dataset_name}: {checksum[:16]}...")
        return checksum
        
    except Exception as e:
        logger.error(f"Error computing checksum for {dataset_name}: {e}")
        return None

def verify_dataset(dataset_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a single dataset's availability and properties.
    
    Args:
        dataset_config: Configuration dictionary for the dataset
        
    Returns:
        Verification result dictionary
    """
    name = dataset_config["name"]
    hf_id = dataset_config["hf_id"]
    variables = dataset_config["variables"]
    
    result = {
        "dataset_name": name,
        "url": f"https://huggingface.co/datasets/{hf_id}",
        "variables": variables,
        "size_mb": 0.0,
        "verification_status": "FAILED"
    }
    
    logger.info(f"Verifying dataset: {name} ({hf_id})")
    
    try:
        # Attempt to load the dataset
        start_time = time.time()
        dataset = load_dataset(hf_id, split="train", streaming=True)
        load_time = time.time() - start_time
        
        logger.info(f"Successfully loaded {name} in {load_time:.2f}s")
        
        # Verify we can iterate over the data
        sample_row = next(iter(dataset))
        logger.info(f"Sample row keys: {list(sample_row.keys())}")
        
        # Estimate size
        result["size_mb"] = estimate_dataset_size_mb(name, hf_id)
        
        # Compute checksum
        result["checksum"] = compute_dataset_checksum(name, hf_id)
        
        result["verification_status"] = "VERIFIED"
        logger.info(f"Verification successful for {name}")
        
    except Exception as e:
        logger.error(f"Verification failed for {name}: {e}")
        result["verification_status"] = f"FAILED: {str(e)}"
    
    return result

def generate_verification_table(results: List[Dict[str, Any]]) -> str:
    """
    Generate a markdown table of verification results.
    
    Args:
        results: List of verification result dictionaries
        
    Returns:
        Markdown table string
    """
    table = "| Dataset | URL | Variables | Size (MB) | Status |\n"
    table += "|---------|-----|-----------|-----------|--------|\n"
    
    for r in results:
        variables_str = f"{len(r['variables'])} columns"
        table += f"| {r['dataset_name']} | {r['url']} | {variables_str} | {r['size_mb']:.2f} | {r['verification_status']} |\n"
    
    return table

def update_research_md(results: List[Dict[str, Any]], research_md_path: Path) -> None:
    """
    Update research.md with the verification results.
    
    Args:
        results: List of verification result dictionaries
        research_md_path: Path to research.md file
    """
    if not research_md_path.exists():
        logger.warning(f"research.md not found at {research_md_path}. Creating new file.")
        research_md_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(research_md_path, 'w') as f:
            f.write("# Research Documentation\n\n")
            f.write("## Dataset Verification\n\n")
            f.write("This section documents the verification of dataset availability.\n\n")
    
    with open(research_md_path, 'r') as f:
        content = f.read()
    
    # Find or create the "Dataset Verification" section
    section_header = "## Dataset Verification"
    if section_header not in content:
        # Add section if it doesn't exist
        content += f"\n\n{section_header}\n\n"
        content += "This section documents the verification of dataset availability.\n\n"
    
    # Generate the verification table
    table = generate_verification_table(results)
    
    # Replace existing table or append new one
    if "| Dataset |" in content:
        # Find the start and end of the table
        lines = content.split('\n')
        new_lines = []
        in_table = False
        skip_table = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith("| Dataset |"):
                in_table = True
                skip_table = True
                # Add new table here
                new_lines.append(table)
                continue
            elif in_table and line.strip().startswith("|---"):
                continue
            elif in_table and line.strip().startswith("|"):
                continue
            elif in_table and not line.strip().startswith("|"):
                in_table = False
                skip_table = False
            
            if not skip_table:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
    else:
        # Append table to section
        content += f"\n{table}\n"
    
    with open(research_md_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Updated research.md with verification results")

def main():
    """Main entry point for tabular dataset verification."""
    logger.info("Starting tabular dataset verification...")
    
    # Determine project root and paths
    project_root = Path(__file__).parent.parent.parent.parent
    research_md_path = project_root / "research.md"
    
    results = []
    
    for dataset_config in TABULAR_DATASETS:
        result = verify_dataset(dataset_config)
        results.append(result)
    
    # Generate and save verification table
    table = generate_verification_table(results)
    print("\n" + "="*60)
    print("TABULAR DATASET VERIFICATION RESULTS")
    print("="*60)
    print(table)
    print("="*60)
    
    # Update research.md
    update_research_md(results, research_md_path)
    
    # Check if all verifications passed
    all_passed = all(r["verification_status"] == "VERIFIED" for r in results)
    
    if all_passed:
        logger.info("All tabular datasets verified successfully!")
        return 0
    else:
        failed_count = sum(1 for r in results if r["verification_status"] != "VERIFIED")
        logger.warning(f"{failed_count} dataset(s) failed verification.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
