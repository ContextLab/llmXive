"""
Featurization utilities for the UQ pipeline.
Provides functions to load raw data, cap dataset size, featurize compositions,
perform stratified train/val/test splits, and process datasets into the format
expected by model runners.
"""
import os
import gc
import logging
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold

# Logger
from utils.logger import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def get_memory_usage_gb() -> float:
    """Estimate current memory usage in GB."""
    import psutil

    mem_bytes = psutil.Process().memory_info().rss
    return mem_bytes / (1024 ** 3)


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
def load_raw_data(dataset_name: str) -> pd.DataFrame:
    """
    Load a raw dataset CSV from ``data/raw``.
    The function expects a file named ``<dataset_name>.csv``.
    """
    raw_path = Path(__file__).parents[1] / "data" / "raw" / f"{dataset_name}.csv"
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw dataset not found: {raw_path}")

    logger.info(f"Loading raw dataset: {raw_path}")
    df = pd.read_csv(raw_path)
    return df


# ----------------------------------------------------------------------
# Dataset capping
# ----------------------------------------------------------------------
def cap_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cap the dataframe to ``MAX_SAMPLES`` rows using a fixed random seed.
    ``MAX_SAMPLES`` can be supplied via the ``MAX_SAMPLES`` environment variable.
    """
    max_samples_env = os.getenv("MAX_SAMPLES")
    try:
        max_samples = int(max_samples_env) if max_samples_env else 100
    except ValueError:
        max_samples = 100

    if len(df) <= max_samples:
        return df

    np.random.seed(42)
    selected_idx = np.random.choice(df.index, size=max_samples, replace=False)
    capped = df.loc[selected_idx].reset_index(drop=True)
    logger.info(f"Capped dataset to {max_samples} samples (requested {max_samples_env})")
    return capped


# ----------------------------------------------------------------------
# Composition featurization
# ----------------------------------------------------------------------
def featurize_composition(composition_str: str) -> np.ndarray:
    """
    Convert a composition string to a numeric feature vector.
    Primary attempt uses ``matminer.featurizers.composition.ElementFraction``.
    If that fails (e.g., due to unknown elements), falls back to a simple
    two‑element descriptor based on pymatgen's ``Composition``.
    """
    try:
        from matminer.featurizers.composition import ElementFraction

        ef = ElementFraction()
        # ElementFraction expects a pandas Series; we wrap the string.
        # The ``featurize`` method returns a list/array of fractions for
        # all known elements (118 entries).  We convert to ``np.ndarray``.
        features = ef.featurize(composition_str)
        return np.asarray(features, dtype=float)
    except Exception as e:
        logger.warning(
            f"Matminer ElementFraction failed for composition '{composition_str}': {e}. "
            "Falling back to simple pymatgen descriptor."
        )
        try:
            from pymatgen.core.composition import Composition

            comp = Composition(composition_str)
            num_elements = len(comp.elements)
            total_atoms = comp.num_atoms
            return np.array([float(num_elements), float(total_atoms)], dtype=float)
        except Exception as e2:
            logger.error(
                f"Pymatgen fallback also failed for composition '{composition_str}': {e2}. "
                "Returning zero‑vector."
            )
            # Return a zero‑vector of length 2 (matches fallback size)
            return np.zeros(2, dtype=float)


def featurize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply composition featurization to the entire dataframe.
    The raw datasets are expected to contain a column named ``composition``.
    Non‑numeric columns (other than ``composition``) are dropped.
    The resulting dataframe contains only numeric feature columns.
    """
    if "composition" not in df.columns:
        raise KeyError("Expected a 'composition' column for featurization.")

    # Apply featurization row‑wise
    logger.info("Starting composition featurization...")
    feature_list = []
    for comp in df["composition"]:
        try:
            feats = featurize_composition(comp)
        except Exception as e:
            logger.error(f"Featurization failed for composition '{comp}': {e}")
            feats = np.zeros(2, dtype=float)
        feature_list.append(feats)

    # Determine feature dimensionality from the first row
    feature_dim = len(feature_list[0])
    feature_cols = [f"feat_{i}" for i in range(feature_dim)]

    # Build a DataFrame of features
    features_df = pd.DataFrame(feature_list, columns=feature_cols, index=df.index)

    # Preserve numeric target columns; drop original non‑numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    result_df = pd.concat([numeric_df, features_df], axis=1)

    logger.info(
        f"Featurization complete. Produced {feature_dim} feature columns."
    )
    return result_df


# ----------------------------------------------------------------------
# Stratified split
# ----------------------------------------------------------------------
def stratified_split(
    df: pd.DataFrame,
    target_col: str,
    test_size: float = 0.15,
    val_size: float = 0.15,
    n_bins: int = 10,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split of ``df`` into train / validation / test
    based on the distribution of ``target_col``.
    The target is binned into ``n_bins`` quantiles to create a stratification label.
    """
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in DataFrame.")

    # Create stratification bins
    y = df[target_col]
    bins = pd.qcut(y, q=n_bins, duplicates="drop").cat.codes
    df["__stratify_bin"] = bins

    # First split off test set
    skf = StratifiedKFold(n_splits=int(1 / test_size), shuffle=True, random_state=42)
    test_idx = next(skf.split(df, df["__stratify_bin"]))[1]

    test_df = df.iloc[test_idx].drop(columns="__stratify_bin")
    remaining = df.drop(index=test_idx)

    # Now split validation from the remaining
    val_frac = val_size / (1 - test_size)
    skf_val = StratifiedKFold(
        n_splits=int(1 / val_frac), shuffle=True, random_state=42
    )
    val_idx = next(skf_val.split(remaining, remaining["__stratify_bin"]))[1]

    val_df = remaining.iloc[val_idx].drop(columns="__stratify_bin")
    train_df = remaining.drop(index=val_idx).drop(columns="__stratify_bin")

    logger.info(
        f"Stratified split sizes -> train: {len(train_df)}, val: {len(val_df)}, test: {len(test_df)}"
    )
    return train_df, val_df, test_df


# ----------------------------------------------------------------------
# Dataset processing
# ----------------------------------------------------------------------
def _detect_target_column(df: pd.DataFrame) -> str:
    """
    Heuristic to locate the property/target column in a raw dataset.
    Looks for common substrings; falls back to the last numeric column.
    """
    candidate_keywords = [
        "gap",
        "energy",
        "conductivity",
        "property",
        "value",
        "target",
    ]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        lowered = col.lower()
        if any(kw in lowered for kw in candidate_keywords):
            return col
    # Fallback: last numeric column
    if numeric_cols:
        return numeric_cols[-1]
    raise ValueError("Unable to locate a numeric target column in the dataset.")


def process_dataset(
    dataset_name: Optional[str] = None, cap: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process one or all raw datasets and return a mapping suitable for the
    model runners.

    For each dataset the returned dictionary contains:
        X_train, y_train, X_val, y_val, X_test, y_test
    and the processed CSV files are saved under ``data/processed``.

    If ``dataset_name`` is provided, only that dataset is processed and the
    function returns the split dictionary for that single dataset (rather than
    the full mapping).  This adjustment simplifies downstream callers such as
    ``code/main.py`` which expect a direct dict when a single dataset is
    requested.
    """
    raw_dir = Path(__file__).parents[1] / "data" / "raw"
    processed_dir = Path(__file__).parents[1] / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    dataset_files = (
        [raw_dir / f"{dataset_name}.csv"]
        if dataset_name
        else list(raw_dir.glob("*.csv"))
    )

    all_data: Dict[str, Any] = {}

    for file_path in dataset_files:
        name = file_path.stem
        logger.info(f"Processing dataset: {name}")

        df = pd.read_csv(file_path)

        # Apply cap (environment variable overrides ``cap`` argument)
        df = cap_dataframe(df)

        # Featurize (adds numeric feature columns)
        df = featurize_dataframe(df)

        # Detect target column
        target_col = _detect_target_column(df)

        # Perform stratified split
        train_df, val_df, test_df = stratified_split(df, target_col)

        # Separate features / target
        X_train = train_df.drop(columns=[target_col])
        y_train = train_df[target_col]
        X_val = val_df.drop(columns=[target_col])
        y_val = val_df[target_col]
        X_test = test_df.drop(columns=[target_col])
        y_test = test_df[target_col]

        # Save splits
        for split_name, split_df in zip(
            ["train", "val", "test"], [train_df, val_df, test_df]
        ):
            out_path = processed_dir / f"{name}_{split_name}.csv"
            split_df.to_csv(out_path, index=False)
            logger.debug(f"Wrote {split_name} split to {out_path}")

        # Assemble dict for model runners
        split_dict = {
            "X_train": X_train,
            "y_train": y_train,
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test,
        }

        if dataset_name:
            # Single‑dataset mode: return immediately
            return split_dict

        all_data[name] = split_dict

        # Optional memory clean‑up
        gc.collect()

    logger.info(f"Processed {len(all_data)} dataset(s).")
    return all_data


def main() -> None:
    """
    Entry point for the featurization script.
    Processes all datasets found in ``data/raw``.
    """
    logger.info("Featurization script started.")
    process_dataset()
    logger.info("Featurization completed successfully.")
