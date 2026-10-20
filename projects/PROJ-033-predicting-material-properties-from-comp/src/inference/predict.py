"""
Inference entry point – builds a composition graph for a single formula,
loads the latest GNN checkpoint (if any), runs the model and writes a JSON
file with predictions, a timestamp and a simple fold‑disagreement band.
"""
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

import torch

from src.graphs.composition import build_composition_graph
from src.models.gnn import CompositionGNN

log = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict band gap and hardness for a formula")
    parser.add_argument("--formula", type=str, required=True, help="Chemical formula, e.g. Fe2O3")
    parser.add_argument("--out", type=Path, required=True, help="Path to write the JSON prediction")
    return parser.parse_args()

def _load_latest_checkpoint():
    """
    Return the state_dict of the most recent checkpoint under ``outputs/``.
    If none exist, raise FileNotFoundError.
    """
    ckpt_dir = Path("outputs")
    if not ckpt_dir.is_dir():
        raise FileNotFoundError("No outputs directory – cannot locate checkpoint")
    ckpt_files = sorted(ckpt_dir.glob("gnn_checkpoint_*.pt"))
    if not ckpt_files:
        raise FileNotFoundError("No GNN checkpoint files found in outputs/")
    latest = ckpt_files[-1]
    return torch.load(latest, map_location="cpu")

def main() -> None:
    args = parse_args()
    # Build graph
    dummy_row = {
        "material_id": "inference_dummy",
        "formula": args.formula,
        "band_gap": 0.0,
        "hardness": 0.0,
    }
    graph = build_composition_graph(
        material_id=dummy_row["material_id"],
        formula=dummy_row["formula"],
        band_gap=0.0,
        hardness=0.0,
        cache=False,
    )
    if graph is None:
        raise ValueError(f"Could not build graph for formula '{args.formula}'")

    # Load model
    state = _load_latest_checkpoint()
    model = CompositionGNN()
    model.load_state_dict(state)
    model.eval()

    # Inference
    with torch.no_grad():
        pred_bg, pred_h = model(graph)

    # Simple "fold‑disagreement band" – because we have a single checkpoint,
    # we set the interval to zero.
    result = {
        "formula": args.formula,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "band_gap_pred": float(pred_bg.item()),
        "hardness_pred": float(pred_h.item()),
        "band_gap_ci": [float(pred_bg.item()), float(pred_bg.item())],
        "hardness_ci": [float(pred_h.item()), float(pred_h.item())],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    log.info("Prediction written to %s", args.out)

if __name__ == "__main__":
    main()
