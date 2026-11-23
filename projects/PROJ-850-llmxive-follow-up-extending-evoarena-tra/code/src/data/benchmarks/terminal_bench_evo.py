import json
import random
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.seeding import set_deterministic_seed
from datasets import load_dataset
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_sample_size_from_research_md() -> int:
    """
    Reads the sample_size from specs/001-evoconflict-filtering/research.md.
    Returns a default of 100 if the file or key is missing.
    """
    research_path = Path("specs/001-evoconflict-filtering/research.md")
    if not research_path.exists():
        logger.warning(f"research.md not found at {research_path}. Defaulting to N=100.")
        return 100

    try:
        with open(research_path, 'r') as f:
            content = f.read()
            # Simple YAML-like parsing for the specific key
            for line in content.splitlines():
                if line.strip().startswith('sample_size:'):
                    val = line.split(':', 1)[1].strip()
                    return int(val)
    except Exception as e:
        logger.error(f"Error reading sample_size from research.md: {e}")
        return 100
    
    logger.warning("sample_size key not found in research.md. Defaulting to N=100.")
    return 100

def load_real_dataset_sample() -> List[Dict[str, Any]]:
    """
    Attempts to download the 'Terminal-Bench-Evo' dataset from HuggingFace.
    If the download fails (dataset not found or network error), it raises an exception
    immediately (FAIL LOUDLY) as per T006 requirements.
    """
    dataset_id = "Terminal-Bench-Evo"
    sample_size = read_sample_size_from_research_md()
    logger.info(f"Attempting to download real dataset: {dataset_id} (Sample N={sample_size})")

    try:
        # Attempt to load the dataset from HuggingFace
        # streaming=True is used to avoid downloading the full dataset if it's large,
        # but we collect exactly 'sample_size' items.
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        collected_tasks = []
        count = 0
        for item in dataset:
            if count >= sample_size:
                break
            collected_tasks.append(item)
            count += 1

        if count == 0:
            raise ValueError("Dataset loaded but contained 0 items.")
        
        logger.info(f"Successfully downloaded {count} items from {dataset_id}.")
        return collected_tasks

    except Exception as e:
        # FAIL LOUDLY: Do not fallback here. Let the caller handle the exception.
        raise RuntimeError(f"CRITICAL: Failed to download real dataset '{dataset_id}'. "
                           f"Real data source unavailable. Exception: {e}")

def generate_synthetic_benchmark_tasks() -> List[Dict[str, Any]]:
    """
    Generates synthetic benchmark tasks as a fallback if real data is unavailable.
    This function is intended to be called by the T006-SYNTH task or the main
    fallback logic if T006 fails.
    """
    set_deterministic_seed()
    sample_size = read_sample_size_from_research_md()
    logger.info(f"Generating synthetic benchmark tasks (N={sample_size})")
    
    tasks = []
    for i in range(sample_size):
        task = {
            "task_id": f"synth_task_{i:04d}",
            "instruction": f"Perform a version update on file config_{i}.json",
            "initial_state": {"file": f"config_{i}.json", "version": 1, "content": f"old_data_{i}"},
            "target_state": {"file": f"config_{i}.json", "version": 2, "content": f"new_data_{i}"},
            "is_contradiction": False, # Synthetic tasks are initially non-contradictory unless modified
            "patch": f"Updated config_{i}.json to version 2"
        }
        tasks.append(task)
    
    return tasks

def main():
    """
    Main entry point for T006: Dataset Verification.
    1. Attempts to load real data.
    2. If successful, writes to data/raw/terminal_bench_evo.jsonl.
    3. If failed, raises an exception (FAIL LOUDLY) so T006-SYNTH can be triggered externally.
    """
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "terminal_bench_evo.jsonl"

    try:
        # Try to get real data
        data = load_real_dataset_sample()
        
        # Write to JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        
        logger.info(f"Real dataset successfully written to {output_file}")
        return 0

    except Exception as e:
        logger.critical(f"Real dataset download failed: {e}")
        logger.critical("T006 FAILED LOUDLY. Please execute T006-SYNTH to generate synthetic data.")
        # Re-raise to ensure the pipeline knows this specific task failed
        raise

if __name__ == "__main__":
    sys.exit(main())
