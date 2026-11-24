"""
Extract node embeddings from a trained GNN checkpoint.

For each material graph in the processed dataset we run a forward pass,
capture the node representations *after* the last GCN layer (before the
global pooling) and store them in a NumPy ``.npy`` file.
"""
import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from src.graphs.composition import build_composition_graph
from src.models.gnn import CompositionGNN

log = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract node embeddings from GNN")
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Path where the NumPy array will be saved",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    data_path = Path("data/processed/materials_processed.csv")
    if not data_path.is_file():
        raise FileNotFoundError(f"Processed data not found at {data_path}")

    df = pd.read_csv(data_path)
    graphs = []
    for _, row in df.iterrows():
        g = build_composition_graph(
            material_id=row["material_id"],
            formula=row["formula"],
            band_gap=float(row["band_gap"]),
            hardness=float(row["hardness"]),
            cache=False,
        )
        if g is not None:
            graphs.append(g)

    if not graphs:
        raise RuntimeError("No graphs could be built – nothing to embed")

    loader = DataLoader(graphs, batch_size=32, shuffle=False)

    # Load the latest checkpoint
    ckpt_dir = Path("outputs")
    ckpt_files = sorted(ckpt_dir.glob("gnn_checkpoint_*.pt"))
    if not ckpt_files:
        raise FileNotFoundError("No GNN checkpoint files found")
    state = torch.load(ckpt_files[-1], map_location="cpu")

    model = CompositionGNN()
    model.load_state_dict(state)
    model.eval()

    all_embeddings = []
    with torch.no_grad():
        for batch in loader:
            # forward up to the last conv layer – we replicate the forward
            # logic from ``CompositionGNN`` but stop before pooling.
            x, edge_index, edge_weight = batch.x, batch.edge_index, getattr(batch, "edge_weight", None)

            x = model.conv1(x, edge_index, edge_weight)
            x = model.relu(x)
            x = model.conv2(x, edge_index, edge_weight)
            x = model.relu(x)
            x = model.conv3(x, edge_index, edge_weight)
            x = model.relu(x)  # shape [N, hidden_dim]

            all_embeddings.append(x.cpu().numpy())

    embeddings = np.concatenate(all_embeddings, axis=0)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out, embeddings)
    log.info("Saved %d node embeddings to %s", embeddings.shape[0], args.out)

if __name__ == "__main__":
    main()
