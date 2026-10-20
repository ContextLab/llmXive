"""
Training script for the composition‑only GNN.

The script respects the runtime guards (FR‑009), uses early stopping
(patience = 10) and runs on CPU only.  It writes a checkpoint after each
epoch to ``outputs/gnn_checkpoint_epoch{epoch}.pt``.
"""
import argparse
import logging
from pathlib import Path

import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from src.utils.seeds import set_global_seed
from src.utils.runtime_guard import RuntimeGuard
from src.graphs.composition import build_composition_graph
from src.models.gnn import CompositionGNN
from src.training.split import stratified_split, generate_cv_folds

log = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train composition‑only GNN")
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to the cleaned CSV produced by the loader",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--max_epochs",
        type=int,
        default=200,
        help="Maximum number of training epochs",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early‑stopping patience",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size (≤ 32)",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)

    # -----------------------------------------------------------------
    # Load data
    # -----------------------------------------------------------------
    df = pd.read_csv(args.data)
    # Perform the 80/10/10 stratified split – we will later use only the
    # training part for the actual model fitting.
    train_df, val_df, _ = stratified_split(df)

    # Build PyG Data objects
    def df_to_data(df_subset):
        data_list = []
        for _, row in df_subset.iterrows():
            graph = build_composition_graph(
                material_id=row["material_id"],
                formula=row["formula"],
                band_gap=float(row["band_gap"]),
                hardness=float(row["hardness"]),
                cache=False,
            )
            if graph is not None:
                data_list.append(graph)
        return data_list

    train_data = df_to_data(train_df)
    val_data = df_to_data(val_df)

    if not train_data:
        log.error("No training graphs were created – aborting.")
        return

    train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=args.batch_size, shuffle=False)

    # -----------------------------------------------------------------
    # Model, optimizer, loss, guard
    # -----------------------------------------------------------------
    device = torch.device("cpu")
    model = CompositionGNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.MSELoss()

    guard = RuntimeGuard()

    best_val_loss = float("inf")
    epochs_no_improve = 0

    for epoch in range(1, args.max_epochs + 1):
        guard.epoch_started()
        model.train()
        epoch_losses = []

        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            pred_bg, pred_h = model(batch)
            target = batch.y.to(device)  # shape [batch, 2]
            loss = loss_fn(pred_bg, target[:, 0]) + loss_fn(pred_h, target[:, 1])
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())

        avg_train_loss = sum(epoch_losses) / len(epoch_losses)

        # Validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                pred_bg, pred_h = model(batch)
                target = batch.y.to(device)
                loss = loss_fn(pred_bg, target[:, 0]) + loss_fn(pred_h, target[:, 1])
                val_losses.append(loss.item())
        avg_val_loss = sum(val_losses) / len(val_losses)

        log.info(
            "Epoch %d – train loss: %.6f – val loss: %.6f",
            epoch,
            avg_train_loss,
            avg_val_loss,
        )

        # Early stopping check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                log.info("Early stopping triggered (no improvement for %d epochs).", args.patience)
                break

        # Save checkpoint for this epoch
        ckpt_path = Path("outputs") / f"gnn_checkpoint_epoch{epoch}.pt"
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), ckpt_path)

        # Runtime guard checks
        try:
            guard.epoch_finished()
        except RuntimeError as e:
            log.error("Runtime guard halted training: %s", e)
            break

    # Final RAM report
    guard.log_peak_ram()
    log.info("Training finished. Best validation loss: %.6f", best_val_loss)

if __name__ == "__main__":
    main()
