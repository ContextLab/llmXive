import os
import sys
import json
import pickle
import logging
from pathlib import Path

from config import load_paths

logger = logging.getLogger(__name__)


def save_artifacts(
    models: dict, metrics: dict, output_dir: Path
) -> None:
    """Save model artifacts and metrics."""
    for name, model in models.items():
        path = output_dir / f"model_{name}.pkl"
        with open(path, "wb") as f:
            pickle.dump(model, f)
        logger.info(f"Saved model: {path}")

    metrics_path = output_dir / "model_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics: {metrics_path}")


def main() -> None:
    """Main entry point for saving models."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    # Placeholder: In reality, models would be loaded from training
    models = {}
    metrics = {}

    save_artifacts(models, metrics, paths["data_evaluation"])
    logger.info("Model saving complete")


if __name__ == "__main__":
    main()
