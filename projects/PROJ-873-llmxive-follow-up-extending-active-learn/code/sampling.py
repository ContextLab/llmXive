import os
import sys
import json
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from config import get_config
from logging_config import get_comparison_log_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_comparison_logs(log_path: str) -> List[Dict[str, Any]]:
    """Load comparison logs from the JSONL file."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Comparison log file not found: {log_path}")
    
    records = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
    return records

def filter_wasted_calls(records: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """Filter records where cosine_sim > threshold (flagged pairs)."""
    return [r for r in records if r.get('cosine_sim', 0) > threshold]

def load_sample_config(config_path: str) -> Dict[str, Any]:
    """Load sample configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Sample config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def select_simple_random_sample(
    candidates: List[Dict[str, Any]], 
    sample_size: int, 
    seed: int
) -> List[int]:
    """
    Select a simple random sample of indices from the candidate list.
    Returns the list of indices (0-based) corresponding to the selected items.
    """
    if sample_size <= 0:
        return []
    
    if sample_size >= len(candidates):
        # Return all indices if sample size covers everything
        return list(range(len(candidates)))
    
    random.seed(seed)
    # random.sample returns a list of unique random indices
    indices = random.sample(range(len(candidates)), sample_size)
    return sorted(indices)

def run_sampling_pipeline(
    log_path: str = "data/processed/comparison_log.json",
    config_path: str = "data/results/sample_config.json",
    output_path: str = "data/results/consensus_sample.json",
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Main pipeline for T013c:
    1. Load comparison logs.
    2. Filter for flagged pairs (similarity > threshold).
    3. Load sample size config.
    4. Select simple random sample using RANDOM_SEED.
    5. Write sample indices to output file.
    """
    logger.info(f"Loading comparison logs from {log_path}")
    all_records = load_comparison_logs(log_path)
    logger.info(f"Loaded {len(all_records)} total comparison records")

    logger.info(f"Filtering for pairs with similarity > {threshold}")
    flagged_records = filter_wasted_calls(all_records, threshold)
    logger.info(f"Found {len(flagged_records)} flagged pairs (similarity > {threshold})")

    if not flagged_records:
        logger.warning("No flagged pairs found. Writing empty sample.")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return {"sample_size": 0, "status": "empty_input"}

    logger.info(f"Loading sample config from {config_path}")
    config = load_sample_config(config_path)
    sample_size = config.get("sample_size", 0)
    logger.info(f"Requested sample size: {sample_size}")

    if sample_size == 0:
        logger.warning("Sample size is 0. Writing empty sample.")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return {"sample_size": 0, "status": "config_zero"}

    cfg = get_config()
    seed = cfg.RANDOM_SEED
    logger.info(f"Using random seed: {seed}")

    logger.info(f"Selecting simple random sample of {sample_size} from {len(flagged_records)} candidates")
    sample_indices = select_simple_random_sample(flagged_records, sample_size, seed)
    logger.info(f"Selected {len(sample_indices)} indices: {sample_indices}")

    # Write the result
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_indices, f, indent=2)
    
    logger.info(f"Successfully wrote sample indices to {output_path}")
    
    return {
        "sample_size": len(sample_indices),
        "total_flagged": len(flagged_records),
        "seed": seed,
        "output_path": output_path
    }

def main():
    """Entry point for CLI execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Run sampling pipeline for T013c")
    parser.add_argument("--log", default="data/processed/comparison_log.json", help="Path to comparison log")
    parser.add_argument("--config", default="data/results/sample_config.json", help="Path to sample config")
    parser.add_argument("--output", default="data/results/consensus_sample.json", help="Output path for sample indices")
    parser.add_argument("--threshold", type=float, default=0.95, help="Similarity threshold for filtering")
    
    args = parser.parse_args()
    
    result = run_sampling_pipeline(
        log_path=args.log,
        config_path=args.config,
        output_path=args.output,
        threshold=args.threshold
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
