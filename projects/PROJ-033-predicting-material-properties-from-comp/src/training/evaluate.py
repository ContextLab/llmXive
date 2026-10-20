"""
Evaluation script for the composition‑only GNN and the Random‑Forest baseline.

Computes R², MAE, and RMSE for band gap and hardness on the held‑out test
set, writes the results to a JSON file that conforms to
``contracts/model_metrics.schema.yaml``, and includes a ``delta_vs_rf``
comparison block.
"""
import argparse
import json
import logging
from pathlib import Path

import pandas as pd
import torch
from torch_geometric.loader import DataLoader
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from src.utils.seeds import set_global_seed
from src.graphs.composition import build_composition_graph
from src.models.gnn import CompositionGNN
from src.models.rf_baseline import train_rf, _build_feature_matrix
from src.training.split import stratified_split

log = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate composition‑only models")
    parser.add_argument(
        "--metrics_out",
        type=Path,
        required=True,
        help="Path where the JSON metrics will be written",
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
        default=50,
        help="Maximum epochs for the quick evaluation run",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size (≤ 32)",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early‑stopping patience for the quick run",
    )
    return parser.parse_args()

def _prepare_loader(df_subset, batch_size):
    graphs = []
    for _, row in df_subset.iterrows():
        g = build_composition_graph(
            material_id=row["material_id"],
            formula=row["formula"],
            band_gap=float(row["band_gap"]),
            hardness=float(row["hardness"]),
            cache=False,
        )
        if g is not None:
            graphs.append(g)
    return DataLoader(graphs, batch_size=batch_size, shuffle=False)

def _train_gnn(train_loader, val_loader, device, max_epochs, patience):
    model = CompositionGNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.MSELoss()

    best_val = float("inf")
    epochs_no_improve = 0

    for epoch in range(1, max_epochs + 1):
        model.train()
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            pred_bg, pred_h = model(batch)
            target = batch.y.to(device)
            loss = loss_fn(pred_bg, target[:, 0]) + loss_fn(pred_h, target[:, 1])
            loss.backward()
            optimizer.step()

        # validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                pred_bg, pred_h = model(batch)
                target = batch.y.to(device)
                loss = loss_fn(pred_bg, target[:, 0]) + loss_fn(pred_h, target[:, 1])
                val_losses.append(loss.item())
        val_loss = sum(val_losses) / len(val_losses)

        if val_loss < best_val:
            best_val = val_loss
            epochs_no_improve = 0
            best_state = model.state_dict()
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                break

    model.load_state_dict(best_state)
    return model

def _predict(model, loader, device):
    model.eval()
    preds_bg, preds_h = [], []
    truths_bg, truths_h = [], []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            pred_bg, pred_h = model(batch)
            preds_bg.extend(pred_bg.cpu().numpy())
            preds_h.extend(pred_h.cpu().numpy())
            truths_bg.extend(batch.y[:, 0].cpu().numpy())
            truths_h.extend(batch.y[:, 1].cpu().numpy())
    return (
        np.array(preds_bg),
        np.array(preds_h),
        np.array(truths_bg),
        np.array(truths_h),
    )

def main() -> None:
    args = parse_args()
    set_global_seed(args.seed)

    # Load cleaned data
    data_path = Path("data/processed/materials_processed.csv")
    if not data_path.is_file():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}")

    df = pd.read_csv(data_path)

    # Split
    train_df, val_df, test_df = stratified_split(df, random_state=args.seed)

    # Loaders
    train_loader = _prepare_loader(train_df, args.batch_size)
    val_loader = _prepare_loader(val_df, args.batch_size)
    test_loader = _prepare_loader(test_df, args.batch_size)

    device = torch.device("cpu")

    # Train GNN (quick run)
    gnn_model = _train_gnn(
        train_loader,
        val_loader,
        device,
        max_epochs=args.max_epochs,
        patience=args.patience,
    )

    # Train RF baseline on the full training set
    rf_models = train_rf(train_df)

    # ---------- GNN predictions ----------
    gnn_preds_bg, gnn_preds_h, y_bg, y_h = _predict(gnn_model, test_loader, device)

    def compute_metrics(y_true, y_pred):
        return {
            "r2": r2_score(y_true, y_pred),
            "mae": mean_absolute_error(y_true, y_pred),
            "rmse": mean_squared_error(y_true, y_pred, squared=False),
        }

    gnn_metrics = {
        "band_gap": compute_metrics(y_bg, gnn_preds_bg),
        "hardness": compute_metrics(y_h, gnn_preds_h),
    }

    # ---------- RF predictions ----------
    X_test = _build_feature_matrix(test_df)
    rf_preds_bg = rf_models["band_gap"].predict(X_test)
    rf_preds_h = rf_models["hardness"].predict(X_test)

    rf_metrics = {
        "band_gap": compute_metrics(y_bg, rf_preds_bg),
        "hardness": compute_metrics(y_h, rf_preds_h),
    }

    # ---------- Delta vs RF ----------
    delta_vs_rf = {
        "band_gap": {
            "r2": gnn_metrics["band_gap"]["r2"] - rf_metrics["band_gap"]["r2"],
            "mae": gnn_metrics["band_gap"]["mae"] - rf_metrics["band_gap"]["mae"],
            "rmse": gnn_metrics["band_gap"]["rmse"] - rf_metrics["band_gap"]["rmse"],
        },
        "hardness": {
            "r2": gnn_metrics["hardness"]["r2"] - rf_metrics["hardness"]["r2"],
            "mae": gnn_metrics["hardness"]["mae"] - rf_metrics["hardness"]["mae"],
            "rmse": gnn_metrics["hardness"]["rmse"] - rf_metrics["hardness"]["rmse"],
        },
    }

    # Assemble final JSON
    result = {
        "model": "gnn",
        "targets": gnn_metrics,
        "rf_baseline": rf_metrics,
        "delta_vs_rf": delta_vs_rf,
    }

    # Write out
    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.metrics_out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    log.info("Metrics written to %s", args.metrics_out)

if __name__ == "__main__":
    main()
