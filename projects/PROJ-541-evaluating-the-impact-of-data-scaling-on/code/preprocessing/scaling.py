"""
Data scaling functions for preprocessing (FR-002).

Implements Standardization (Z-score), Min-Max scaling, and Robust
Scaling (Median/IQR).

Transparency requirements (Constitution VII / task T003):
  * Every scaling call appends a structured JSON entry to
    ``logs/scaling_<method>.log`` (method name, parameters, timestamp).
  * A copy of the PRE-scaled data is written to
    ``data/pre_scaled/<method>/original_<uuid>.csv`` before any
    transformation is applied.

All functions FAIL LOUDLY on invalid input (empty, non-numeric,
non-finite data) — there is no silent fallback.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd

try:  # llmxive_toolkit is provided by the platform runtime
    from llmxive_toolkit import paths as _toolkit_paths

    _PROJECT_ROOT: Path = Path(_toolkit_paths.root)
except Exception:  # pragma: no cover - fallback only outside the runtime
    _PROJECT_ROOT = Path.cwd()

# Module-level directories (monkeypatchable in tests)
PRE_SCALED_DIR: Path = _PROJECT_ROOT / "data" / "pre_scaled"
LOGS_DIR: Path = _PROJECT_ROOT / "logs"

logger = logging.getLogger(__name__)

DataLike = Union[np.ndarray, pd.Series, pd.DataFrame, list]


def _validate_input(data: DataLike) -> None:
    """Validate input data; raise ValueError on any invalid input."""
    if data is None:
        raise ValueError("Input data is None; refusing to scale.")
    if isinstance(data, pd.DataFrame):
        if data.empty:
            raise ValueError("Input DataFrame is empty; refusing to scale.")
        for col in data.columns:
            if not pd.api.types.is_numeric_dtype(data[col]):
                raise ValueError(
                    f"Column '{col}' is non-numeric; refusing to scale."
                )
        if not np.isfinite(data.to_numpy(dtype=float)).all():
            raise ValueError("Input DataFrame contains non-finite values.")
    elif isinstance(data, pd.Series):
        if data.empty:
            raise ValueError("Input Series is empty; refusing to scale.")
        if not pd.api.types.is_numeric_dtype(data):
            raise ValueError("Input Series is non-numeric; refusing to scale.")
        if not np.isfinite(data.to_numpy(dtype=float)).all():
            raise ValueError("Input Series contains non-finite values.")
    else:
        try:
            arr = np.asarray(data, dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Input cannot be converted to numeric: {exc}")
        if arr.size == 0:
            raise ValueError("Input array is empty; refusing to scale.")
        if not np.all(np.isfinite(arr)):
            raise ValueError("Input array contains non-finite values.")


def _persist_original(
    data: DataLike, method: str, parameters: Dict[str, Any]
) -> Path:
    """
    Save a copy of the PRE-scaled data and append a structured log entry.

    Returns the path of the preserved CSV copy.
    """
    PRE_SCALED_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if isinstance(data, pd.DataFrame):
        df = data.copy()
    elif isinstance(data, pd.Series):
        df = data.to_frame(name="value")
    else:
        df = pd.DataFrame({"value": np.asarray(data, dtype=float).ravel()})

    uid = uuid.uuid4().hex
    csv_path = PRE_SCALED_DIR / method / f"original_{uid}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "parameters": parameters,
        "preserved_copy": str(csv_path),
        "rows": int(len(df)),
        "columns": list(df.columns),
    }
    log_path = LOGS_DIR / f"scaling_{method}.log"
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return csv_path


def standardize(
    data: DataLike, persist: bool = True
) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """
    Standardize data to mean=0, std=1 (Z-score).

    Constant (zero-variance) columns are mapped to zeros with a logged
    warning instead of producing NaNs or raising.

    Args:
        data: numeric array / Series / DataFrame
        persist: write pre-scaled copy + structured log entry (default True)

    Returns:
        Standardized data of the same container type
    """
    _validate_input(data)
    if persist:
        _persist_original(data, "standardize", {})

    if isinstance(data, pd.DataFrame):
        mean = data.mean()
        std = data.std()
        zero_std = std == 0
        if zero_std.any():
            logger.warning(
                "Zero standard deviation in columns %s; mapping to zeros.",
                list(data.columns[zero_std]),
            )
            std = std.where(~zero_std, 1.0)
            out = (data - mean) / std
            out.loc[:, zero_std] = 0.0
            return out
        return (data - mean) / std
    if isinstance(data, pd.Series):
        mean = data.mean()
        std = data.std()
        if std == 0:
            logger.warning("Zero standard deviation; mapping to zeros.")
            return pd.Series(0.0, index=data.index, name=data.name)
        return (data - mean) / std

    arr = np.asarray(data, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)
    if std == 0:
        logger.warning("Zero standard deviation; mapping to zeros.")
        return np.zeros_like(arr)
    return (arr - mean) / std


def min_max_scale(
    data: DataLike,
    min_val: float = 0.0,
    max_val: float = 1.0,
    persist: bool = True,
) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """
    Scale data to the range [min_val, max_val].

    Constant (zero-range) data is mapped to ``min_val`` with a logged
    warning instead of producing NaNs.

    Args:
        data: numeric array / Series / DataFrame
        min_val: lower bound of the target range
        max_val: upper bound of the target range
        persist: write pre-scaled copy + structured log entry (default True)

    Returns:
        Scaled data of the same container type
    """
    if not max_val > min_val:
        raise ValueError(
            f"Invalid target range: min_val={min_val} >= max_val={max_val}"
        )
    _validate_input(data)
    if persist:
        _persist_original(
            data, "minmax", {"min_val": min_val, "max_val": max_val}
        )

    if isinstance(data, pd.DataFrame):
        data_min = data.min()
        data_max = data.max()
        zero_range = data_max == data_min
        if zero_range.any():
            logger.warning(
                "Zero range in columns %s; mapping to min_val.",
                list(data.columns[zero_range]),
            )
            span = (data_max - data_min).where(~zero_range, 1.0)
            out = min_val + (data - data_min) * (max_val - min_val) / span
            out.loc[:, zero_range] = min_val
            return out
        return min_val + (data - data_min) * (max_val - min_val) / (
            data_max - data_min
        )
    if isinstance(data, pd.Series):
        data_min = data.min()
        data_max = data.max()
        if data_min == data_max:
            logger.warning("Zero range; mapping to min_val.")
            return pd.Series(min_val, index=data.index, name=data.name)
        return min_val + (data - data_min) * (max_val - min_val) / (
            data_max - data_min
        )

    arr = np.asarray(data, dtype=float)
    data_min = np.min(arr)
    data_max = np.max(arr)
    if data_min == data_max:
        logger.warning("Zero range; mapping to min_val.")
        return np.full_like(arr, min_val)
    return min_val + (arr - data_min) * (max_val - min_val) / (
        data_max - data_min
    )


def robust_scale(
    data: DataLike, persist: bool = True
) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """
    Scale data using median and IQR (robust scaling).

    Constant (zero-IQR) data is mapped to zeros with a logged warning —
    the function NEVER returns NaN and NEVER returns None.

    Args:
        data: numeric array / Series / DataFrame
        persist: write pre-scaled copy + structured log entry (default True)

    Returns:
        Robustly scaled data of the same container type
    """
    _validate_input(data)
    if persist:
        _persist_original(data, "robust", {})

    if isinstance(data, pd.DataFrame):
        median = data.median()
        iqr = data.quantile(0.75) - data.quantile(0.25)
        zero_iqr = iqr == 0
        if zero_iqr.any():
            logger.warning(
                "Zero IQR in columns %s; mapping to zeros.",
                list(data.columns[zero_iqr]),
            )
            iqr = iqr.where(~zero_iqr, 1.0)
            out = (data - median) / iqr
            out.loc[:, zero_iqr] = 0.0
            return out
        return (data - median) / iqr
    if isinstance(data, pd.Series):
        median = data.median()
        iqr = data.quantile(0.75) - data.quantile(0.25)
        if iqr == 0:
            logger.warning("Zero IQR; mapping to zeros.")
            return pd.Series(0.0, index=data.index, name=data.name)
        return (data - median) / iqr

    arr = np.asarray(data, dtype=float)
    median = np.median(arr)
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    if iqr == 0:
        logger.warning("Zero IQR; mapping to zeros.")
        return np.zeros_like(arr)
    return (arr - median) / iqr


# ---------------------------------------------------------------------------
# Backward-compatible aliases (existing API surface)
# ---------------------------------------------------------------------------
def standardize_data(
    data: DataLike,
) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """Alias for :func:`standardize` (legacy API name)."""
    return standardize(data)


def min_max_scale_data(
    data: DataLike,
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> Union[np.ndarray, pd.Series, pd.DataFrame]:
    """Alias kept for symmetry with the legacy naming convention."""
    return min_max_scale(data, min_val=min_val, max_val=max_val)
