"""Load and validate baseline manifests."""
import json
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR, ERR_SEED_UNSTABLE

BASELINE_DIR = Path("data/processed/baseline_manifests")

def load_baseline_manifest(model_id: str, seed: int) -> Dict[str, Any]:
    """Load a baseline manifest from disk."""
    manifest_path = BASELINE_DIR / f"{model_id}_{seed}.json"
    
    if not manifest_path.exists():
        raise DATA_INTEGRITY_ERROR(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_seed_stability(manifest: Dict[str, Any], threshold_pct: float = 5.0) -> bool:
    """Verify seed stability from manifest."""
    if manifest.get("status") != "STABLE":
        return False
    
    mean_reward = manifest.get("mean_reward", 0)
    std_reward = (manifest.get("variance_reward", 0)) ** 0.5
    
    if mean_reward == 0:
        return False
    
    cv = (std_reward / abs(mean_reward)) * 100
    return cv < threshold_pct

def get_baseline_thresholds(manifest: Dict[str, Any]) -> Tuple[float, float]:
    """Get reward and gradient thresholds from manifest."""
    if manifest.get("status") != "STABLE":
        raise ERR_SEED_UNSTABLE("Cannot get thresholds from unstable manifest")
    
    return manifest["mean_reward"], manifest["mean_grad_norm"]

def get_valid_seed_for_model(model_id: str, seed_pool: list) -> int:
    """Get a valid seed for the model (placeholder)."""
    return seed_pool[0] if seed_pool else 1
