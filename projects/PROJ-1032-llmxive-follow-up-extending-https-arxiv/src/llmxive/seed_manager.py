"""
Seed Manager Module for llmXive.

Handles deterministic seed sequence generation, stability validation of synchronous baselines,
and discard-and-retry logic per FR-004.
"""
import os
import random
import logging
import json
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import numpy as np
import torch

from src.llmxive.baseline_loader import load_baseline_manifest, verify_seed_stability
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR, ERR_SEED_UNSTABLE

logger = logging.getLogger(__name__)

# Pre-defined integer sequence for seed management as per FR-004
DEFAULT_SEED_SEQUENCE = list(range(1, 6))  # [1, 2, 3, 4, 5]

def set_all_seeds(seed: int) -> None:
    """
    Set all random seeds for reproducibility.

    Args:
        seed (int): The seed value to set.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_deterministic_config(seed: int) -> Dict[str, Any]:
    """
    Get a dictionary of deterministic configuration settings for a given seed.

    Args:
        seed (int): The seed value.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    set_all_seeds(seed)
    return {
        "seed": seed,
        "python_hash_seed": os.environ.get('PYTHONHASHSEED'),
        "torch_deterministic": torch.backends.cudnn.deterministic,
        "torch_cudnn_benchmark": torch.backends.cudnn.benchmark,
    }

class SeedManager:
    """
    Manages the seed sequence, validates stability, and handles discard-retry logic.
    """

    def __init__(self, seed_sequence: Optional[List[int]] = None, output_dir: Optional[str] = None):
        """
        Initialize the SeedManager.

        Args:
            seed_sequence (List[int], optional): The sequence of seeds to manage. Defaults to DEFAULT_SEED_SEQUENCE.
            output_dir (str, optional): Directory to write the audit report. Defaults to 'data/processed'.
        """
        self.seed_sequence = seed_sequence or DEFAULT_SEED_SEQUENCE.copy()
        self.output_dir = Path(output_dir or "data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_log: List[Dict[str, Any]] = []
        self.discarded_seeds: List[int] = []
        self.final_sequence: List[int] = []

    def _load_and_verify_baseline(self, seed: int, model_id: str) -> Tuple[bool, Optional[str]]:
        """
        Load the baseline manifest for a seed and verify its stability.

        Args:
            seed (int): The seed to check.
            model_id (str): The model identifier (e.g., 'phi2', 'qwen15').

        Returns:
            Tuple[bool, Optional[str]]: (is_stable, error_reason).
        """
        manifest_path = self.output_dir / "baseline_manifests" / f"{model_id}_{seed}.json"
        
        if not manifest_path.exists():
            return False, f"Manifest not found for seed {seed} and model {model_id}"

        try:
            manifest = load_baseline_manifest(str(manifest_path))
            is_stable = verify_seed_stability(manifest)
            if not is_stable:
                return False, "variance > 5% of mean"
            return True, None
        except (DATA_INTEGRITY_ERROR, ERR_SEED_UNSTABLE, KeyError, json.JSONDecodeError) as e:
            return False, str(e)

    def process_sequence(self, model_ids: List[str]) -> Dict[str, Any]:
        """
        Process the seed sequence for given models, discarding unstable seeds and retrying.

        Args:
            model_ids (List[str]): List of model IDs to validate against.

        Returns:
            Dict[str, Any]: The audit report data.
        """
        logger.info(f"Starting seed audit for sequence: {self.seed_sequence}")
        logger.info(f"Validating against models: {model_ids}")

        valid_seeds = []
        current_index = 0
        max_attempts = len(self.seed_sequence) * 10  # Safety limit to prevent infinite loops in testing

        while len(valid_seeds) < len(self.seed_sequence) and current_index < max_attempts:
            # Determine the next candidate seed
            # We cycle through the original sequence if we need to retry, but we track specific seeds
            candidate_seed_idx = len(valid_seeds) % len(self.seed_sequence)
            candidate_seed = self.seed_sequence[candidate_seed_idx]

            # Check if we already accepted this seed
            if candidate_seed in valid_seeds:
                # Move to next in sequence logic effectively handled by index increment
                current_index += 1
                continue

            # Validate against all required models
            all_models_stable = True
            failure_reason = None

            for model_id in model_ids:
                is_stable, reason = self._load_and_verify_baseline(candidate_seed, model_id)
                if not is_stable:
                    all_models_stable = False
                    failure_reason = reason
                    break

            if all_models_stable:
                logger.info(f"Seed {candidate_seed} verified stable for all models.")
                valid_seeds.append(candidate_seed)
                self.final_sequence.append(candidate_seed)
                current_index += 1
            else:
                logger.warning(f"Seed {candidate_seed} discarded for reason: {failure_reason}")
                self.discarded_seeds.append(candidate_seed)
                self.audit_log.append({
                    "seed": candidate_seed,
                    "status": "discarded",
                    "reason": failure_reason,
                    "timestamp": "N/A" # Placeholder if not needed
                })
                current_index += 1

        if len(valid_seeds) < len(self.seed_sequence):
            logger.error(f"Could not find enough valid seeds. Found {len(valid_seeds)}, needed {len(self.seed_sequence)}.")
            # In a real scenario, we might raise an error here, but we proceed to write the audit

        return self.generate_audit_report()

    def generate_audit_report(self) -> Dict[str, Any]:
        """
        Generate the final audit report dictionary.

        Returns:
            Dict[str, Any]: The audit report.
        """
        report = {
            "discarded_seeds": self.discarded_seeds,
            "reasons": {str(seed): "variance > 5% of mean" for seed in self.discarded_seeds},
            "final_sequence": self.final_sequence,
            "total_seeds_requested": len(self.seed_sequence),
            "total_seeds_validated": len(self.final_sequence),
            "status": "complete" if len(self.final_sequence) == len(self.seed_sequence) else "incomplete"
        }

        audit_path = self.output_dir / "seed_audit.json"
        with open(audit_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Audit report written to {audit_path}")
        return report

def main():
    """
    Main entry point for seed manager execution.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage: Validate seeds 1-5 against phi2 and qwen15
    manager = SeedManager(
        seed_sequence=DEFAULT_SEED_SEQUENCE,
        output_dir="data/processed"
    )
    
    # In a real execution, these model IDs would come from config
    # We assume baseline manifests exist from T019a/T019b
    model_ids = ["phi2", "qwen15"]
    
    report = manager.process_sequence(model_ids)
    print(f"Seed Audit Complete: {report['status']}")
    print(f"Final Sequence: {report['final_sequence']}")
    print(f"Discarded Seeds: {report['discarded_seeds']}")

if __name__ == "__main__":
    main()
