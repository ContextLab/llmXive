"""
Download and split code dataset from Hugging Face.

Implements T015: Fetch codeparrot/github-code subset (Python/Java) with streaming.
Enforces strict sample size limits from feasibility report.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib

# Import from project modules (must match API surface)
try:
    from config import get_config, ensure_dirs
    from utils.logging import get_logger, NetworkError
    from data.checksum import compute_directory_checksums, save_checksums
except ImportError:
    # Fallback for direct execution (add parent to path)
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_config, ensure_dirs
    from utils.logging import get_logger, NetworkError
    from data.checksum import compute_directory_checksums, save_checksums

# Constants
DATASET_NAME = "codeparrot/github-code"
LANGUAGE_FILTERS = ["python", "java"]
FEASIBILITY_REPORT_PATH = "data/results/feasibility_report.json"

# Configure logging
logger = get_logger(__name__)

def load_feasibility_report() -> Dict[str, Any]:
    """Load the feasibility report to get capped_N."""
    config = get_config()
    report_path = Path(config["project_root"]) / FEASIBILITY_REPORT_PATH
    
    if not report_path.exists():
        raise FileNotFoundError(
            f"Feasibility report not found at {report_path}. "
            "Run T011 (feasibility.py) first."
        )
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    if not report.get("proceed_flag", False):
        raise RuntimeError(
            "Feasibility check failed. proceed_flag is False. "
            "Cannot proceed with download."
        )
    
    capped_n = report.get("capped_N")
    if capped_n is None:
        raise KeyError("capped_N not found in feasibility report.")
    
    return report

def fetch_dataset_subset(capped_n: int, languages: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch dataset subset from Hugging Face with streaming.
    
    Args:
        capped_n: Maximum number of chunks to fetch.
        languages: List of languages to filter (e.g., ["python", "java"]).
        
    Returns:
        List of fetched chunks.
        
    Raises:
        NetworkError: If dataset fetch fails.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' package is required. "
            "Install it via: pip install datasets"
        )

    logger.info(f"Fetching dataset: {DATASET_NAME}")
    logger.info(f"Languages: {languages}, Max chunks: {capped_n}")
    
    # Load dataset with streaming to stay within disk constraints
    # Filter for Python and Java languages
    try:
        dataset = load_dataset(
            DATASET_NAME,
            split="train",
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise NetworkError(f"Failed to fetch dataset: {e}")

    # Filter and limit
    filtered_chunks = []
    count = 0
    
    try:
        for item in dataset:
            if count >= capped_n:
                break
            
            # Check language
            lang = item.get("language", "").lower()
            if lang in languages:
                filtered_chunks.append(item)
                count += 1
                
                if count % 100 == 0:
                    logger.info(f"Fetched {count}/{capped_n} chunks...")
                
    except Exception as e:
        logger.error(f"Error while iterating dataset: {e}")
        raise NetworkError(f"Failed to fetch dataset: {e}")
    
    logger.info(f"Successfully fetched {len(filtered_chunks)} chunks.")
    return filtered_chunks

def write_chunks_to_disk(
    chunks: List[Dict[str, Any]], 
    output_dir: Path, 
  language: str
) -> None:
    """
    Write chunks to disk as individual files.
    
    Args:
        chunks: List of chunk dictionaries.
        output_dir: Output directory path.
        language: Language identifier for naming.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing {len(chunks)} chunks to {output_dir}")
    
    for i, chunk in enumerate(chunks):
        # Create filename
        filename = f"chunk_{i:06d}_{language}.txt"
        filepath = output_dir / filename
        
        # Extract code content
        code_content = chunk.get("code", "")
        if not code_content:
            logger.warning(f"Skipping chunk {i}: no code content")
            continue
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        # Store metadata separately (optional, for later processing)
        # For now, we'll just write the code
        
    logger.info(f"Successfully wrote {len(chunks)} files to {output_dir}")

def main():
    """Main entry point for T015."""
    config = get_config()
    ensure_dirs(config)
    
    # Load feasibility report
    logger.info("Loading feasibility report...")
    try:
        feasibility_report = load_feasibility_report()
    except (FileNotFoundError, RuntimeError, KeyError) as e:
        logger.error(f"Failed to load feasibility report: {e}")
        sys.exit(1)
    
    capped_n = feasibility_report["capped_N"]
    logger.info(f"Proceeding with capped_N = {capped_n}")
    
    # Fetch dataset
    logger.info("Fetching dataset...")
    try:
        chunks = fetch_dataset_subset(capped_n, LANGUAGE_FILTERS)
    except NetworkError as e:
        logger.error(f"Failed to fetch dataset: {e}")
        sys.exit(1)
    
    if len(chunks) == 0:
        logger.error("No chunks fetched. Exiting.")
        sys.exit(1)
    
    # Split by language
    python_chunks = [c for c in chunks if c.get("language", "").lower() == "python"]
    java_chunks = [c for c in chunks if c.get("language", "").lower() == "java"]
    
    logger.info(f"Split: {len(python_chunks)} Python, {len(java_chunks)} Java")
    
    # Write to disk
    base_output = Path(config["project_root"]) / "data" / "processed"
    python_dir = base_output / "train_python"
    java_dir = base_output / "val_java"
    
    write_chunks_to_disk(python_chunks, python_dir, "python")
    write_chunks_to_disk(java_chunks, java_dir, "java")
    
    # Generate checksums
    logger.info("Generating checksums...")
    try:
        checksums = compute_directory_checksums([python_dir, java_dir])
        save_checksums(checksums, Path(config["project_root"]) / "data" / "checksums.json")
    except Exception as e:
        logger.warning(f"Failed to generate checksums: {e}")
    
    logger.info("T015 Download complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
