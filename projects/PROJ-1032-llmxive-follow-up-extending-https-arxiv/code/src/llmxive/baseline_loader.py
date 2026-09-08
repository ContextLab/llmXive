import json
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR, ERR_SEED_UNSTABLE

def load_baseline_manifest(seed: int, base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the baseline manifest for a specific seed from the processed directory.
    
    Args:
        seed: The seed ID to load the manifest for.
        base_dir: Optional base directory for the manifests. Defaults to data/processed/baseline_manifests.
    
    Returns:
        A dictionary containing the manifest data.
    
    Raises:
        DATA_INTEGRITY_ERROR: If the manifest file does not exist or is corrupted.
    """
    if base_dir is None:
        base_dir = Path("data/processed/baseline_manifests")
    
    manifest_path = base_dir / f"{seed}.json"
    
    if not manifest_path.exists():
        raise DATA_INTEGRITY_ERROR(f"Baseline manifest not found for seed {seed} at {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise DATA_INTEGRITY_ERROR(f"Corrupted baseline manifest for seed {seed}: {e}")

def verify_seed_stability(manifest: Dict[str, Any], tolerance: float = 0.05) -> Tuple[bool, str]:
    """
    Verify the stability of a seed based on its baseline manifest.
    
    Checks if the variance of the reward is less than `tolerance` (5%) of the mean.
    
    Args:
        manifest: The loaded baseline manifest dictionary.
        tolerance: The maximum allowed ratio of variance to mean (default 0.05).
    
    Returns:
        A tuple (is_stable, message).
        is_stable is True if variance < tolerance * mean, False otherwise.
    
    Raises:
        DATA_INTEGRITY_ERROR: If required fields are missing from the manifest.
    """
    if 'mean_reward' not in manifest:
        raise DATA_INTEGRITY_ERROR("Missing 'mean_reward' in baseline manifest.")
    if 'variance_reward' not in manifest:
        # If variance is not stored, we might need to compute it or treat as unstable if critical.
        # Per spec FR-004, we check variance. If missing, we cannot verify stability.
        # We treat missing variance as a failure to verify stability.
        raise DATA_INTEGRITY_ERROR("Missing 'variance_reward' in baseline manifest. Cannot verify stability.")
    
    mean_reward = manifest['mean_reward']
    variance_reward = manifest['variance_reward']
    
    if mean_reward == 0:
        # Avoid division by zero; if mean is 0, any non-zero variance makes it unstable relative to mean
        # or if variance is 0 it's stable.
        is_stable = (variance_reward == 0)
        msg = "Mean reward is zero." if not is_stable else "Stable (zero mean, zero variance)."
        return is_stable, msg
    
    ratio = variance_reward / abs(mean_reward)
    is_stable = ratio < tolerance
    
    if is_stable:
        return True, f"Seed stable: variance ({variance_reward:.4f}) < {tolerance*100}% of mean ({mean_reward:.4f}). Ratio: {ratio:.4f}"
    else:
        return False, f"Seed UNSTABLE: variance ({variance_reward:.4f}) >= {tolerance*100}% of mean ({mean_reward:.4f}). Ratio: {ratio:.4f}"

def get_baseline_thresholds(seed: int, base_dir: Optional[Path] = None) -> Dict[str, float]:
    """
    Retrieve the baseline thresholds (mean reward, mean gradient norm) for a seed.
    
    This function loads the manifest and verifies stability before returning thresholds.
    If the seed is unstable, it raises ERR_SEED_UNSTABLE.
    
    Args:
        seed: The seed ID.
        base_dir: Optional base directory for manifests.
    
    Returns:
        A dictionary with 'mean_reward' and 'mean_grad_norm'.
    
    Raises:
        ERR_SEED_UNSTABLE: If the seed is found to be unstable.
        DATA_INTEGRITY_ERROR: If the manifest cannot be loaded or is missing fields.
    """
    manifest = load_baseline_manifest(seed, base_dir)
    
    # Verify stability as per FR-004
    is_stable, message = verify_seed_stability(manifest)
    
    if not is_stable:
        raise ERR_SEED_UNSTABLE(f"Seed {seed} is unstable: {message}")
    
    if 'mean_grad_norm' not in manifest:
        raise DATA_INTEGRITY_ERROR("Missing 'mean_grad_norm' in baseline manifest.")
    
    return {
        'mean_reward': manifest['mean_reward'],
        'mean_grad_norm': manifest['mean_grad_norm'],
        'seed_id': seed
    }

def get_valid_seed_for_model(model_id: str, base_dir: Optional[Path] = None, max_attempts: int = 3) -> Optional[int]:
    """
    Find a valid (stable) seed for the given model by iterating through potential seeds.
    
    This function attempts to load and verify stability for seeds in a sequence (e.g., 1, 2, 3...).
    It stops at the first stable seed found or after max_attempts if no stable seed is found in the sequence.
    
    Note: This function assumes seeds are stored as {seed}.json. It tries a range of seeds starting from 1.
    In a real scenario, this might be driven by a list of available seeds or a specific range.
    For this implementation, we try seeds 1 to max_attempts.
    
    Args:
        model_id: The model identifier (not strictly used for file naming here, but kept for API consistency).
        base_dir: Optional base directory for manifests.
        max_attempts: Maximum number of seed attempts to check.
    
    Returns:
        The first stable seed ID found, or None if no stable seed is found within attempts.
    """
    if base_dir is None:
        base_dir = Path("data/processed/baseline_manifests")
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Check if manifest exists for this attempt seed
            manifest_path = base_dir / f"{attempt}.json"
            if not manifest_path.exists():
                continue
            
            manifest = load_baseline_manifest(attempt, base_dir)
            is_stable, _ = verify_seed_stability(manifest)
            
            if is_stable:
                return attempt
        
        except (DATA_INTEGRITY_ERROR, ERR_SEED_UNSTABLE):
            # Continue to next seed if unstable or corrupted
            continue
    
    return None