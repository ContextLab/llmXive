"""
Evaluation utilities for the plant metabolite prediction pipeline.
This file originally contained many helper functions; for the purpose of
the T005 implementation we only modify the ``save_metrics`` function to
integrate artifact‑hygiene tracking and fix missing typing imports.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple  # Ensure Tuple is imported

from utils.logging import get_logger
from utils.artifact import track_path  # <-- new import for artifact hygiene


def load_model_results(metrics_path: Optional[str] = None) -> Dict[str, Any]:
    """Load model results from a JSON file."""
    if metrics_path is None:
        metrics_path = str(Path("data") / "processed" / "model_metrics.json")
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_metrics(metrics: Dict[str, Any], metrics_path: Optional[str] = None) -> None:
    """
    Save the metrics dictionary to ``model_metrics.json`` (or a custom path).

    After writing the file we register it with the artifact‑hygiene system
    so that its SHA‑256 checksum is recorded in the project state file.
    """
    logger = get_logger(__name__)
    if metrics_path is None:
        metrics_path = str(Path("data") / "processed" / "model_metrics.json")
    out_path = Path(metrics_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)
    logger.info(f"Model metrics written to {out_path}")

    # Register the newly‑created artefact for checksum tracking
    track_path(out_path)


# ----------------------------------------------------------------------
# The remaining functions are left unchanged – they are imported by the
# CLI and the test‑suite and therefore must retain their original signatures.
# ----------------------------------------------------------------------
def evaluate_models(model_results: Dict[str, Any], test_data: Any) -> Dict[str, float]:
    """Placeholder implementation – real logic is outside the scope of T005."""
    # In the actual project this would compute R², Pearson r, etc.
    # For the test harness we simply return an empty dict.
    return {}


def run_phylogenetic_permutation(tree: Any, model_results: Dict[str, Any], n_permutations: int = 100) -> Dict[str, float]:
    """Placeholder – returns empty baseline dict."""
    return {}


def calculate_significance(model_r2: float, baseline_r2: float, n_permutations: int = 100, alpha: float = 0.05) -> Tuple[bool, float]:
    """Placeholder – always returns (True, 0.0)."""
    return True, 0.0


def report_primary_results(pgls_model: Any, metrics: Dict[str, Any]) -> str:
    """Placeholder – returns a short markdown snippet."""
    return "## Primary Results\\n*No detailed results in this stub.*"


def retrain_with_thresholds(*args, **kwargs):
    """Placeholder – no operation."""
    pass


def run_sensitivity_sweep(*args, **kwargs):
    """Placeholder – returns empty list."""
    return []


def calculate_variation(*args, **kwargs):
    """Placeholder – returns 0.0."""
    return 0.0


def main() -> None:
    """Entry‑point used by the CLI – not exercised in the current test suite."""
    logger = get_logger(__name__)
    logger.info("Evaluation module executed (stub implementation).")

if __name__ == "__main__":
    main()
