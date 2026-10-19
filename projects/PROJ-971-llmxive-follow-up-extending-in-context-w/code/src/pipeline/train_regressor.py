"""
Train a lightweight MLP regressor that predicts the ICWM sampling temperature (τ)
from statistical descriptors of interaction clips.

The script performs the following steps:
  1. Load descriptors (variance, autocorr_lag1, spectral_density) and τ labels.
  2. Split the data into a training set and a validation set (80 % / 20 %).
  3. Standardise the descriptor features using the training‑set statistics.
  4. Run a 5‑fold cross‑validation grid‑search over:
         hidden size ∈ {16, 32, 64}
         L2 regularisation ∈ {1e‑4, 1e‑3, 1e‑2}
     to minimise mean‑squared‑error (MSE) on the held‑out folds.
  5. Retrain the best‑found model on the full training set.
  6. Evaluate the trained model on the validation set and compute a baseline
     MSE (predicting the global mean τ).
  7. Write the trained model checkpoint to ``model/regressor.pt`` and a
     JSON metrics file to ``data/metrics.json`` containing:
         n_train, n_val, train_mse, val_mse, baseline_mse,
         global_mean_tau, meets_sc006, seed
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import StandardScaler

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# MLP definition
# ----------------------------------------------------------------------
class MLP(nn.Module):
    """Simple single‑hidden‑layer MLP for regression."""
    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x):
        return self.net(x)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_data(descriptors_path: Path, labels_path: Path) -> pd.DataFrame:
    """Load descriptors and τ labels and merge on ``clip_id``."""
    log.info(f"Loading descriptors from {descriptors_path}")
    desc = pd.read_csv(descriptors_path)

    log.info(f"Loading labels from {labels_path}")
    labs = pd.read_csv(labels_path)

    # Keep only the τ column (temperature) – the task only cares about τ.
    merged = pd.merge(desc, labs[['clip_id', 'tau']], on='clip_id', how='inner')
    if merged.empty:
        raise RuntimeError("No matching clip_id between descriptors and labels.")
    return merged

def train_one_fold(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    hidden_dim: int,
    l2_reg: float,
    seed: int,
    epochs: int = 200,
    lr: float = 1e-2,
) -> float:
    """Train on a single CV fold and return the validation MSE."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device("cpu")
    model = MLP(input_dim=X_train.shape[1], hidden_dim=hidden_dim).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=l2_reg)

    X_tr = torch.from_numpy(X_train).float().to(device)
    y_tr = torch.from_numpy(y_train).float().unsqueeze(1).to(device)
    X_vl = torch.from_numpy(X_val).float().to(device)
    y_vl = torch.from_numpy(y_val).float().unsqueeze(1).to(device)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        preds = model(X_tr)
        loss = criterion(preds, y_tr)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        val_preds = model(X_vl)
        val_mse = criterion(val_preds, y_vl).item()
    return val_mse

def cross_validate(
    X: np.ndarray,
    y: np.ndarray,
    hidden_sizes: list[int],
    l2_vals: list[float],
    seed: int,
    n_splits: int = 5,
) -> dict:
    """Return the hyper‑parameter combination with the lowest average CV MSE."""
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    results = {}

    for hidden in hidden_sizes:
        for l2 in l2_vals:
            fold_mses = []
            for train_idx, val_idx in cv.split(X):
                X_tr, X_va = X[train_idx], X[val_idx]
                y_tr, y_va = y[train_idx], y[val_idx]
                mse = train_one_fold(
                    X_tr, y_tr, X_va, y_va,
                    hidden_dim=hidden,
                    l2_reg=l2,
                    seed=seed,
                )
                fold_mses.append(mse)
            avg_mse = float(np.mean(fold_mses))
            results[(hidden, l2)] = avg_mse
            log.debug(
                f"CV hidden={hidden}, l2={l2:.0e} → avg MSE={avg_mse:.6f}"
            )

    # Find the best hyper‑parameters (lowest avg MSE)
    best_params = min(results, key=results.get)
    best_mse = results[best_params]
    log.info(
        f"Best CV params: hidden={best_params[0]}, l2={best_params[1]:.0e} "
        f"with avg MSE={best_mse:.6f}"
    )
    return {
        "hidden_dim": best_params[0],
        "l2_reg": best_params[1],
        "cv_mse": best_mse,
    }

def train_final_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    hidden_dim: int,
    l2_reg: float,
    seed: int,
    epochs: int = 300,
    lr: float = 1e-2,
) -> MLP:
    """Train on the full training set using the selected hyper‑parameters."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device("cpu")
    model = MLP(input_dim=X_train.shape[1], hidden_dim=hidden_dim).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=l2_reg)

    X_tr = torch.from_numpy(X_train).float().to(device)
    y_tr = torch.from_numpy(y_train).float().unsqueeze(1).to(device)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        preds = model(X_tr)
        loss = criterion(preds, y_tr)
        loss.backward()
        optimizer.step()
    return model

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Train τ‑only regressor and write metrics."
    )
    parser.add_argument(
        "--descriptors",
        type=str,
        default=str(paths.data("processed", "descriptors.csv")),
        help="Path to the descriptors CSV.",
    )
    parser.add_argument(
        "--labels",
        type=str,
        default=str(paths.data("processed", "labels.csv")),
        help="Path to the τ labels CSV (must contain a 'tau' column).",
    )
    parser.add_argument(
        "--model-out",
        type=str,
        default=str(paths.path("model", "regressor.pt")),
        help="Where to save the trained model checkpoint.",
    )
    parser.add_argument(
        "--metrics-out",
        type=str,
        default=str(paths.data("metrics.json")),
        help="Path for the JSON metrics output.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = _parse_args(argv)

    # ------------------------------------------------------------------
    # Load and prepare data
    # ------------------------------------------------------------------
    df = load_data(Path(args.descriptors), Path(args.labels))
    X = df[["variance", "autocorr_lag1", "spectral_density"]].values.astype(np.float32)
    y = df["tau"].values.astype(np.float32)

    # Train / validation split (80 % / 20 %)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=args.seed, shuffle=True
    )
    n_train, n_val = X_train.shape[0], X_val.shape[0]
    log.info(f"Training set size: {n_train}, validation set size: {n_val}")

    # Standardise features (fit on training data only)
    scaler = StandardScaler()
    X_train_std = scaler.fit_transform(X_train)
    X_val_std = scaler.transform(X_val)

    # ------------------------------------------------------------------
    # Hyper‑parameter search (5‑fold CV)
    # ------------------------------------------------------------------
    hidden_sizes = [16, 32, 64]
    l2_vals = [1e-4, 1e-3, 1e-2]

    cv_result = cross_validate(
        X_train_std,
        y_train,
        hidden_sizes=hidden_sizes,
        l2_vals=l2_vals,
        seed=args.seed,
    )

    # ------------------------------------------------------------------
    # Train final model on the full training set with best hyper‑params
    # ------------------------------------------------------------------
    best_hidden = cv_result["hidden_dim"]
    best_l2 = cv_result["l2_reg"]
    model = train_final_model(
        X_train_std,
        y_train,
        hidden_dim=best_hidden,
        l2_reg=best_l2,
        seed=args.seed,
    )

    # ------------------------------------------------------------------
    # Compute metrics
    # ------------------------------------------------------------------
    device = torch.device("cpu")
    model.eval()
    with torch.no_grad():
        # Train MSE
        train_preds = model(torch.from_numpy(X_train_std).float().to(device)).cpu().numpy().flatten()
        train_mse = float(np.mean((train_preds - y_train) ** 2))

        # Validation MSE
        val_preds = model(torch.from_numpy(X_val_std).float().to(device)).cpu().numpy().flatten()
        val_mse = float(np.mean((val_preds - y_val) ** 2))

    # Baseline: predict global mean τ from the training set
    global_mean_tau = float(y_train.mean())
    baseline_mse = float(np.mean((y_val - global_mean_tau) ** 2))

    meets_sc006 = val_mse < 0.9 * baseline_mse

    metrics = {
        "n_train": int(n_train),
        "n_val": int(n_val),
        "train_mse": train_mse,
        "val_mse": val_mse,
        "baseline_mse": baseline_mse,
        "global_mean_tau": global_mean_tau,
        "meets_sc006": meets_sc006,
        "seed": args.seed,
    }

    # ------------------------------------------------------------------
    # Persist model and metrics
    # ------------------------------------------------------------------
    model_path = Path(args.model_out)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_path)
    log.info(f"Saved model checkpoint to {model_path}")

    metrics_path = Path(args.metrics_out)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    log.info(f"Wrote metrics to {metrics_path}")

    # Print a concise summary for the CLI user
    log.info(
        f"Baseline MSE: {baseline_mse:.6f} | "
        f"Model Val MSE: {val_mse:.6f} | Meets SC‑006: {meets_sc006}"
    )

if __name__ == "__main__":
    main()
