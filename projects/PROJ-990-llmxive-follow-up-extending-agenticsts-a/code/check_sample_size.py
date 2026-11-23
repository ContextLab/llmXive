import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_ablation_labels(path: str) -> List[Dict[str, Any]]:
    """Load ablation labels JSON."""
    p = Path(path)
    if not p.exists():
        return []
    with open(p, 'r') as f:
        return json.load(f)

def log_warning(msg: str):
    logger.warning(msg)

def write_fallback_flag(output_path: str, reason: str):
    """
    Write the fallback flag JSON as required by T008d.
    This ensures the pipeline does not proceed with mock data.
    """
    data = {
        "fallback": True,
        "use_heuristic": True,
        "reason": reason
    }
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Fallback flag written to {output_path}")

def main():
    """
    T008d: Ablation Failure Handling.
    Checks if ablation labels exist. If not, writes the fallback flag.
    """
    ablation_path = "data/processed/ablation_labels_train.json"
    fallback_path = "data/processed/fallback_flag.json"
    
    labels = load_ablation_labels(ablation_path)
    
    if not labels:
        log_warning("Ablation labels missing or empty. Writing fallback flag.")
        write_fallback_flag(fallback_path, "Ablation study failed to produce labels.")
        return True # We handled the failure gracefully
    
    logger.info("Ablation labels present. No fallback needed.")
    return True

if __name__ == "__main__":
    main()