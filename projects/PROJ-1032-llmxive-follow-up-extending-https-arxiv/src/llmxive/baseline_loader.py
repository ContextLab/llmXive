"""Baseline loading and validation."""
import json
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

def load_baseline_manifest(
    seed: int,
    manifest_dir: Path
) -> Dict[str, Any]:
    """
    Load a baseline manifest for a specific seed.
    
    Args:
        seed: The seed ID.
        manifest_dir: Directory containing manifests.
    
    Returns:
        The manifest dictionary.
    
    Raises:
        DATA_INTEGRITY_ERROR: If manifest is missing or invalid.
    """
    manifest_path = manifest_dir / f"{seed}.json"
    if not manifest_path.exists():
        raise DATA_INTEGRITY_ERROR(f"Baseline manifest not found for seed {seed}.")
    
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DATA_INTEGRITY_ERROR(f"Invalid JSON in manifest for seed {seed}: {e}")
    
    if "mean_reward" not in data or "mean_grad_norm" not in data:
        raise DATA_INTEGRITY_ERROR(f"Manifest for seed {seed} missing required fields.")
    
    return data

def get_baseline_thresholds(
    manifest: Dict[str, Any],
    reward_drop_factor: float = 0.8,
    grad_spike_factor: float = 2.0
) -> Tuple[float, float]:
    """
    Compute divergence thresholds from a manifest.
    
    Args:
        manifest: The baseline manifest.
        reward_drop_factor: Factor below mean to trigger drop.
        grad_spike_factor: Factor above mean to trigger spike.
    
    Returns:
        Tuple of (reward_threshold, grad_threshold).
    """
    reward_threshold = manifest["mean_reward"] * reward_drop_factor
    grad_threshold = manifest["mean_grad_norm"] * grad_spike_factor
    return reward_threshold, grad_threshold

def verify_seed_stability(
    manifest: Dict[str, Any],
    variance_threshold: float = 0.05
) -> bool:
    """
    Verify the stability status in the manifest.
    
    Args:
        manifest: The baseline manifest.
        variance_threshold: Unused in this simplified version.
    
    Returns:
        True if status is STABLE.
    """
    return manifest.get("status") == "STABLE"
