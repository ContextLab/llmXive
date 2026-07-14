"""
Saliency mapping for GNN node embeddings.

This script computes the gradient of the model's predicted dipole moment
with respect to each node feature (the "saliency") for every molecule in a
dataset. The resulting per‑node importance scores are written to a JSON
file that can be consumed by downstream analysis or visualisation tools.

Usage
-----
python code/attribution/saliency_mapping.py \
    --model-checkpoint data/checkpoints/best_gnn.pt \
    --dataset-root data/processed \
    --output data/processed/saliency_maps.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List

import torch
from tqdm import tqdm

# The MoleculeDataset class is defined in the training module and is part of the
# public API surface of the project.
from training.train_gnn import MoleculeDataset


def compute_saliency(
    model: torch.nn.Module,
    dataset: MoleculeDataset,
    device: torch.device,
) -> Dict[str, List[float]]:
    """
    Compute saliency maps for a whole dataset.

    Parameters
    ----------
    model: torch.nn.Module
        The trained GNN model. It must accept a single ``data`` object
        (as produced by ``MoleculeDataset``) and return a tensor of shape
        ``(1,)`` representing the predicted dipole moment.
    dataset: MoleculeDataset
        Iterable dataset of molecular graphs. Each element must expose at
        least ``x`` (node feature matrix) and an identifier ``mol_id``.
    device: torch.device
        Device on which the computation will be performed.

    Returns
    -------
    dict
        Mapping from molecule identifier to a list of saliency values – one
        per node. The saliency for a node is the L1‑norm of the gradient of
        the output with respect to the node's feature vector.
    """
    model.eval()
    model.to(device)

    saliency_dict: Dict[str, List[float]] = {}

    for data in tqdm(dataset, desc="Computing saliency"):
        # Ensure we have a unique identifier for the molecule.
        # ``MoleculeDataset`` stores the SMILES string in ``data.smiles``;
        # fall back to the index if unavailable.
        mol_id = getattr(data, "smiles", None) or str(len(saliency_dict))

        # Move data to the target device.
        data = data.to(device)

        # Enable gradient tracking on node features.
        data.x.requires_grad = True

        # Forward pass – the model is expected to return a scalar tensor.
        output = model(data)

        # If the model returns a batch of predictions, reduce to a single
        # scalar (we take the mean which is appropriate for a single‑graph
        # batch).
        if output.ndim > 0:
            output = output.mean()

        # Back‑propagate to obtain gradients w.r.t. node features.
        model.zero_grad()
        output.backward()

        # Gradient has same shape as ``data.x``; take L1‑norm per node.
        grad = data.x.grad.detach().abs()
        node_saliency = grad.norm(p=1, dim=1).cpu().tolist()

        saliency_dict[mol_id] = node_saliency

        # Clean up for the next iteration.
        data.x.requires_grad = False
        del data

    return saliency_dict


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate saliency maps for a GNN model."
    )
    parser.add_argument(
        "--model-checkpoint",
        type=pathlib.Path,
        required=True,
        help="Path to the saved GNN model (torch.save).",
    )
    parser.add_argument(
        "--dataset-root",
        type=pathlib.Path,
        required=True,
        help="Root directory of the processed dataset (used by MoleculeDataset).",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("data/processed/saliency_maps.json"),
        help="File to write the saliency maps (JSON).",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Computation device.",
    )
    args = parser.parse_args()

    # Load the model.  We assume the checkpoint contains the full model
    # object; if it only stores a state_dict, users can modify this script
    # to instantiate the model class and load the state dict.
    model = torch.load(args.model_checkpoint, map_location=args.device)

    # Load dataset.
    dataset = MoleculeDataset(root=str(args.dataset_root))

    device = torch.device(args.device)

    saliency_maps = compute_saliency(model, dataset, device)

    # Ensure parent directory exists.
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON output.
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(saliency_maps, f, indent=2)

    print(f"Saliency maps written to {args.output}")


if __name__ == "__main__":
    main()
