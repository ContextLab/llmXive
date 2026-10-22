from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import pandas as pd
from llmxive_toolkit import paths, get_logger

from .trainer import train_model

log = get_logger(__name__)

def generate_and_save(
    dataset_name: str,
    model_name: Literal["CTGAN", "DPGAN", "CopulaGAN"],
    seed: int,
    train_df: pd.DataFrame,
    max_epochs: int = 30,
    early_stopping_delta: float = 0.001,
    early_stopping_patience: int = 3,
) -> Path:
    """Train ``model_name`` on ``train_df`` and persist the synthetic data."""
    try:
        synth_df = train_model(
            model_name=model_name,
            train_df=train_df,
            max_epochs=max_epochs,
            early_stopping_delta=early_stopping_delta,
            early_stopping_patience=early_stopping_patience,
            seed=seed,
        )
        status = "success"
    except RuntimeError as exc:
        log.warning(
            "Non‑convergent training for %s (seed=%s): %s", model_name, seed, exc
        )
        synth_df = pd.DataFrame(columns=train_df.columns)
        status = "failure"

    csv_path = paths.outputs("synthetic", f"{dataset_name}_{model_name}_seed{seed}.csv")
    json_path = csv_path.with_suffix(".json")

    synth_df.to_csv(csv_path, index=False)
    log.info(
        "Synthetic CSV written: %s (status=%s, rows=%d)",
        csv_path,
        status,
        len(synth_df),
    )

    metadata = {
        "dataset": dataset_name,
        "model": model_name,
        "seed": seed,
        "max_epochs": max_epochs,
        "early_stopping_delta": early_stopping_delta,
        "early_stopping_patience": early_stopping_patience,
        "privacy_budget": 1.0 if model_name == "DPGAN" else None,
        "status": status,
        "row_count": len(synth_df),
    }

    json_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    log.info("Side‑car metadata written: %s", json_path)

    return csv_path