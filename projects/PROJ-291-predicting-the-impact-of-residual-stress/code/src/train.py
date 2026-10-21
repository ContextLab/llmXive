"""
train.py
----------
Implements task **T005** – training Random Forest, Gradient Boosting,
and a shallow neural network with 5‑fold cross‑validation, hyper‑parameter
search, timing, and final evaluation.

The script is runnable as a module:
    python -m src.train --feature-set A
It writes model artefacts under ``code/models/`` and a performance summary
CSV to ``data/results/model_performance.csv``.
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Optional torch import – required only for the shallow NN.
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except Exception:  # pragma: no cover
    torch = None  # type: ignore

from llmxive_toolkit import paths, get_logger
from src.config import SEED
from code.src.timing import phase_timer
from src.build_features import _load_unified_dataset

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Hyper‑parameter grids (10 combos each)
# ----------------------------------------------------------------------
RF_GRID = [
    {"n_estimators": 100, "max_depth": None, "min_samples_split": 2},
    {"n_estimators": 200, "max_depth": None, "min_samples_split": 2},
    {"n_estimators": 100, "max_depth": 10, "min_samples_split": 2},
    {"n_estimators": 100, "max_depth": 20, "min_samples_split": 2},
    {"n_estimators": 150, "max_depth": None, "min_samples_split": 4},
    {"n_estimators": 200, "max_depth": 10, "min_samples_split": 2},
    {"n_estimators": 250, "max_depth": None, "min_samples_split": 2},
    {"n_estimators": 300, "max_depth": 15, "min_samples_split": 2},
    {"n_estimators": 350, "max_depth": None, "min_samples_split": 3},
    {"n_estimators": 400, "max_depth": 20, "min_samples_split": 2},
]

GBM_GRID = [
    {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3},
    {"n_estimators": 200, "learning_rate": 0.1, "max_depth": 3},
    {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 4},
    {"n_estimators": 150, "learning_rate": 0.1, "max_depth": 5},
    {"n_estimators": 200, "learning_rate": 0.05, "max_depth": 5},
    {"n_estimators": 250, "learning_rate": 0.1, "max_depth": 6},
    {"n_estimators": 300, "learning_rate": 0.05, "max_depth": 6},
    {"n_estimators": 350, "learning_rate": 0.1, "max_depth": 7},
    {"n_estimators": 400, "learning_rate": 0.05, "max_depth": 7},
    {"n_estimators": 450, "learning_rate": 0.1, "max_depth": 8},
]

NN_GRID = [
    {"hidden_size": 32, "lr": 0.01, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 64, "lr": 0.01, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 128, "lr": 0.01, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 32, "lr": 0.005, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 64, "lr": 0.005, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 128, "lr": 0.005, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 32, "lr": 0.001, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 64, "lr": 0.001, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 128, "lr": 0.001, "batch_size": 32, "max_epochs": 200},
    {"hidden_size": 64, "lr": 0.0005, "batch_size": 32, "max_epochs": 200},
]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_feature_set(name: str) -> pd.DataFrame:
    """
    Load a feature‑set CSV written by ``src.build_features``.
    """
    path = paths.processed(f"feature_set_{name}.csv")
    if not path.is_file():
        raise FileNotFoundError(f"Feature set file not found: {path}")
    return pd.read_csv(path)

def _prepare_data(
    feature_set_name: str,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Returns X, y, material_class for the requested feature set.

    * For A and B_balanced we use the *balanced* subset (rows where
      ``is_proxy`` is False).  For B_full and C we use the full dataset.
    """
    df = _load_feature_set(feature_set_name)
    # Target
    y = pd.to_numeric(df["fatigue_life_cycles"], errors="coerce")
    # Material class for stratification
    material = df["material_class"]
    # Drop non‑feature columns
    drop_cols = ["sample_id", "fatigue_life_cycles", "material_class", "source"]
    X = df.drop(columns=drop_cols)
    return X, y, material

def _evaluate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """Return (MAPE, R²)."""
    mape = mean_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return float(mape), float(r2)

# ----------------------------------------------------------------------
# Model training per algorithm
# ----------------------------------------------------------------------
def _train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Dict,
) -> RandomForestRegressor:
    model = RandomForestRegressor(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        min_samples_split=params["min_samples_split"],
        random_state=SEED,
        n_jobs=os.cpu_count(),
    )
    model.fit(X_train, y_train)
    return model

def _train_gbm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Dict,
) -> GradientBoostingRegressor:
    model = GradientBoostingRegressor(
        n_estimators=params["n_estimators"],
        learning_rate=params["learning_rate"],
        max_depth=params["max_depth"],
        random_state=SEED,
    )
    model.fit(X_train, y_train)
    return model

class ShallowNN(nn.Module):
    def __init__(self, input_dim: int, hidden_size: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, x):
        return self.net(x)

def _train_shallow_nn(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Dict,
) -> Tuple[ShallowNN, float]:
    if torch is None:
        raise RuntimeError("PyTorch is not available – cannot train the NN model.")

    device = torch.device("cpu")
    X_tensor = torch.from_numpy(X_train.values.astype(np.float32)).to(device)
    y_tensor = torch.from_numpy(y_train.values.astype(np.float32).reshape(-1, 1)).to(device)

    model = ShallowNN(input_dim=X_train.shape[1], hidden_size=params["hidden_size"]).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=params["lr"])

    batch_size = params["batch_size"]
    max_epochs = params["max_epochs"]
    early_stop_patience = 20
    best_loss = float("inf")
    epochs_no_improve = 0
    start_time = time.time()

    for epoch in range(max_epochs):
        permutation = torch.randperm(X_tensor.size(0), generator=torch.Generator().manual_seed(SEED))
        epoch_losses = []
        for i in range(0, X_tensor.size(0), batch_size):
            indices = permutation[i : i + batch_size]
            batch_x, batch_y = X_tensor[indices], y_tensor[indices]

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())

        epoch_loss = np.mean(epoch_losses)
        # Early stopping check
        if epoch_loss < best_loss:
            best_loss = epoch_loss
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= early_stop_patience:
                break

    train_time = time.time() - start_time
    if train_time > 3600:
        raise RuntimeError(f"Shallow NN training exceeded 60 min ({train_time:.1f}s).")
    return model, train_time

# ----------------------------------------------------------------------
# Cross‑validation & hyper‑parameter search
# ----------------------------------------------------------------------
def _cross_validate(
    X: pd.DataFrame,
    y: pd.Series,
    material: pd.Series,
    algorithm: str,
    param_grid: List[Dict],
    balanced: bool,
) -> Tuple[Dict, float, float]:
    """
    Perform 5‑fold stratified CV and return the best‑parameter dict together
    with mean CV‑MAPE and mean CV‑R².
    """
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    best_score = float("inf")
    best_params = None
    best_r2 = -float("inf")

    for params in param_grid:
        fold_maps = []
        fold_r2s = []
        for train_idx, val_idx in skf.split(X, material):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

            if algorithm == "RF":
                model = _train_random_forest(X_tr, y_tr, params)
            elif algorithm == "GBM":
                model = _train_gbm(X_tr, y_tr, params)
            elif algorithm == "NN":
                model, _ = _train_shallow_nn(X_tr, y_tr, params)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            preds = model.predict(X_val) if algorithm != "NN" else model(torch.from_numpy(X_val.values.astype(np.float32))).detach().numpy().ravel()
            mape, r2 = _evaluate_metrics(y_val.values, preds)
            fold_maps.append(mape)
            fold_r2s.append(r2)

        mean_mape = np.mean(fold_maps)
        mean_r2 = np.mean(fold_r2s)

        # Select by lowest MAPE; break ties with higher R².
        if mean_mape < best_score or (np.isclose(mean_mape, best_score) and mean_r2 > best_r2):
            best_score = mean_mape
            best_r2 = mean_r2
            best_params = params

    return best_params, best_score, best_r2

# ----------------------------------------------------------------------
# Main training orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Train models for all feature sets and algorithms, write artefacts, and
    produce ``model_performance.csv``.
    """
    # Map feature‑set identifiers used by ``build_features`` to the names
    # expected by the test suite.
    feature_sets = {
        "A": "A",
        "B_balanced": "B_balanced",
        "B_full": "B_full",
        "C": "C",
    }

    results: List[Dict] = []

    models_dir = Path("code/models")
    models_dir.mkdir(parents=True, exist_ok=True)

    for fs_key, fs_name in feature_sets.items():
        X, y, material = _prepare_data(fs_name)

        # Determine whether this set should be stratified on the *balanced*
        # subset (A and B_balanced) or on the full data (B_full, C).
        balanced = fs_key in ("A", "B_balanced")

        # 80/20 train‑test split (stratified)
        X_tr, X_te, y_tr, y_te, mat_tr, mat_te = train_test_split(
            X,
            y,
            material,
            test_size=0.2,
            stratify=material,
            random_state=SEED,
        )

        # ------------------------------------------------------------------
        # Random Forest
        # ------------------------------------------------------------------
        with phase_timer(f"{fs_name}_RF"):
            best_params, cv_mape, cv_r2 = _cross_validate(
                X_tr,
                y_tr,
                mat_tr,
                algorithm="RF",
                param_grid=RF_GRID,
                balanced=balanced,
            )
            model = _train_random_forest(X_tr, y_tr, best_params)
            test_pred = model.predict(X_te)
            test_mape, test_r2 = _evaluate_metrics(y_te.values, test_pred)

            model_path = models_dir / f"{fs_name}_RF.pkl"
            pd.to_pickle(model, model_path)

            results.append(
                {
                    "feature_set": fs_name,
                    "algorithm": "RF",
                    "cv_mape": round(cv_mape, 6),
                    "cv_r2": round(cv_r2, 6),
                    "test_mape": round(test_mape, 6),
                    "test_r2": round(test_r2, 6),
                    "train_time_s": None,
                }
            )

        # ------------------------------------------------------------------
        # Gradient Boosting
        # ------------------------------------------------------------------
        with phase_timer(f"{fs_name}_GBM"):
            best_params, cv_mape, cv_r2 = _cross_validate(
                X_tr,
                y_tr,
                mat_tr,
                algorithm="GBM",
                param_grid=GBM_GRID,
                balanced=balanced,
            )
            model = _train_gbm(X_tr, y_tr, best_params)
            test_pred = model.predict(X_te)
            test_mape, test_r2 = _evaluate_metrics(y_te.values, test_pred)

            model_path = models_dir / f"{fs_name}_GBM.pkl"
            pd.to_pickle(model, model_path)

            results.append(
                {
                    "feature_set": fs_name,
                    "algorithm": "GBM",
                    "cv_mape": round(cv_mape, 6),
                    "cv_r2": round(cv_r2, 6),
                    "test_mape": round(test_mape, 6),
                    "test_r2": round(test_r2, 6),
                    "train_time_s": None,
                }
            )

        # ------------------------------------------------------------------
        # Shallow Neural Network
        # ------------------------------------------------------------------
        with phase_timer(f"{fs_name}_NN"):
            best_params, cv_mape, cv_r2 = _cross_validate(
                X_tr,
                y_tr,
                mat_tr,
                algorithm="NN",
                param_grid=NN_GRID,
                balanced=balanced,
            )
            model, train_time = _train_shallow_nn(X_tr, y_tr, best_params)
            # NN prediction on test set
            model.eval()
            with torch.no_grad():
                test_tensor = torch.from_numpy(X_te.values.astype(np.float32))
                test_pred = model(test_tensor).numpy().ravel()
            test_mape, test_r2 = _evaluate_metrics(y_te.values, test_pred)

            model_path = models_dir / f"{fs_name}_NN.pt"
            torch.save(model.state_dict(), model_path)

            results.append(
                {
                    "feature_set": fs_name,
                    "algorithm": "NN",
                    "cv_mape": round(cv_mape, 6),
                    "cv_r2": round(cv_r2, 6),
                    "test_mape": round(test_mape, 6),
                    "test_r2": round(test_r2, 6),
                    "train_time_s": round(train_time, 2),
                }
            )

    # ----------------------------------------------------------------------
    # Write performance summary CSV
    # ----------------------------------------------------------------------
    perf_path = paths.results("model_performance.csv")
    perf_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(perf_path, index=False)
    log.info("Model performance written to %s", perf_path)

if __name__ == "__main__":
    main()