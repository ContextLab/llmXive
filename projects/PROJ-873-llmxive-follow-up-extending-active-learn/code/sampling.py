import json
import os
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from config import get_config

logger = logging.getLogger(__name__)

def load_comparison_logs(log_path: str) -> List[Dict[str, Any]]:
    """Load comparison logs from file."""
    logs = []
    with open(log_path, "r") as f:
        for line in f:
            logs.append(json.loads(line))
    return logs

def filter_wasted_calls(logs: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """Filter logs for wasted calls (cosine similarity > threshold)."""
    return [log for log in logs if log.get("cosine_sim", 0) > threshold]

def stratify_by_similarity(logs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Stratify logs by similarity ranges."""
    strata = defaultdict(list)
    for log in logs:
        sim = log.get("cosine_sim", 0)
        if sim > 0.95:
            strata["high"].append(log)
        elif sim > 0.80:
            strata["medium"].append(log)
        else:
            strata["low"].append(log)
    return strata

def select_stratified_sample(strata: Dict[str, List[Dict[str, Any]]], sample_size: int) -> List[Dict[str, Any]]:
    """Select a stratified sample from logs."""
    sample = []
    for stratum, logs in strata.items():
        count = min(len(logs), sample_size // len(strata))
        sample.extend(random.sample(logs, count))
    return sample

def load_sample_config(config_path: str) -> Dict[str, Any]:
    """Load sample configuration from file."""
    with open(config_path, "r") as f:
        return json.load(f)

def run_sampling_pipeline():
    """Run the sampling pipeline to generate consensus_sample.json."""
    config = get_config()
    log_path = os.path.join(config.data_dir, "data/processed/comparison_log.json")
    sample_config_path = os.path.join(config.data_dir, "data/results/sample_config.json")
    output_path = os.path.join(config.data_dir, "data/results/consensus_sample.json")

    if not os.path.exists(log_path):
        logger.warning("Comparison log not found. Skipping sampling pipeline.")
        return

    if not os.path.exists(sample_config_path):
        logger.warning("Sample config not found. Skipping sampling pipeline.")
        return

    logs = load_comparison_logs(log_path)
    wasted_calls = filter_wasted_calls(logs)
    strata = stratify_by_similarity(wasted_calls)
    sample_config = load_sample_config(sample_config_path)
    sample_size = sample_config.get("sample_size", 0)

    if sample_size == 0:
        logger.info("Sample size is 0. Skipping sampling.")
        sample_indices = []
    else:
        sample = select_stratified_sample(strata, sample_size)
        sample_indices = [i for i, log in enumerate(logs) if log in sample]

    with open(output_path, "w") as f:
        json.dump(sample_indices, f)

    logger.info(f"Consensus sample saved to {output_path}")

def main():
    run_sampling_pipeline()

if __name__ == "__main__":
    main()