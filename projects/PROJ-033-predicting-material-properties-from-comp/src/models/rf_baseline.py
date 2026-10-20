"""
Random Forest baseline for material property prediction.

This module provides a lightweight wrapper around scikit‑learn's
``RandomForestRegressor`` that builds a composition‑fraction feature matrix
from material formulas and trains a separate regressor for each target
(band gap and hardness).

The implementation is deliberately tolerant of environments where the
heavy ``pymatgen`` dependency is unavailable: it falls back to a tiny
regex‑based parser that extracts element symbols and computes fractional
composition. This ensures that contract‑level unit tests (which import
this module) run without requiring the external package.
"""
import logging
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Optional ``pymatgen`` import – used for robust formula parsing when
# available.  When missing we fall back to a simple regex‑based parser.
# ----------------------------------------------------------------------
try:
    from pymatgen.core import Composition  # type: ignore
except Exception:  # pragma: no cover
    Composition = None  # type: ignore

# ----------------------------------------------------------------------
# Helper: parse a chemical formula into a dict {element: count}
# ----------------------------------------------------------------------
def _parse_formula(formula: str) -> dict:
    """
    Parse ``formula`` into a mapping of element symbols to atom counts.

    If ``pymatgen`` is available we delegate to ``Composition`` which
    handles nested parentheses, hydration, etc.  Otherwise a very simple
    regular‑expression based parser is used – sufficient for the unit‑test
    fixtures (e.g. ``Fe2O3`` or ``SiO2``).

    Parameters
    ----------
    formula : str
        Chemical formula string.

    Returns
    -------
    dict
        Mapping of element symbols to integer counts.
    """
    if Composition is not None:
        try:
            comp = Composition(formula)
            # ``comp.get_el_amt_dict()`` returns a dict of element → amount
            return {el.symbol: int(round(cnt)) for el, cnt in comp.get_el_amt_dict().items()}
        except Exception as e:  # pragma: no cover
            log.warning("pymatgen failed to parse formula %s: %s", formula, e)

    # Fallback: very simple parser – matches element symbols (capital letter
    # possibly followed by a lowercase letter) and optional integer count.
    import re

    tokens = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
    if not tokens:
        raise ValueError(f"Unable to parse formula '{formula}'")
    counts = {}
    for elem, num in tokens:
        cnt = int(num) if num else 1
        counts[elem] = counts.get(elem, 0) + cnt
    return counts

# ----------------------------------------------------------------------
# Feature matrix construction
# ----------------------------------------------------------------------
def _build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a DataFrame where each column corresponds to an element symbol and
    each cell contains the atomic fraction of that element in the material's
    formula.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a ``formula`` column.

    Returns
    -------
    pd.DataFrame
        Index matches ``df``; columns are element symbols.
    """
    if "formula" not in df.columns:
        raise KeyError("DataFrame must contain a 'formula' column")

    # First pass: collect all element symbols present in the dataset
    all_elements = set()
    parsed_formulas = []
    for formula in df["formula"]:
        elem_counts = _parse_formula(formula)
        parsed_formulas.append(elem_counts)
        all_elements.update(elem_counts.keys())

    all_elements = sorted(all_elements)  # deterministic column order
    feature_rows = []
    for elem_counts in parsed_formulas:
        total = sum(elem_counts.values())
        fractions = [elem_counts.get(el, 0) / total for el in all_elements]
        feature_rows.append(fractions)

    feature_df = pd.DataFrame(feature_rows, columns=all_elements, index=df.index)
    return feature_df

# ----------------------------------------------------------------------
# Training routine
# ----------------------------------------------------------------------
def train_rf(df: pd.DataFrame, n_estimators: int = 200, random_state: int = 42) -> dict:
    """
    Train two Random Forest regressors – one for band gap and one for
    hardness – on the composition‑fraction feature matrix.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``formula``, ``band_gap`` and ``hardness`` columns.
    n_estimators : int, optional
        Number of trees in the forest (default 200).
    random_state : int, optional
        Random seed for reproducibility (default 42).

    Returns
    -------
    dict
        ``{'band_gap': model_bg, 'hardness': model_h}``
    """
    required = {"formula", "band_gap", "hardness"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required columns for RF training: {missing}")

    X = _build_feature_matrix(df)
    y_bg = df["band_gap"].values
    y_h = df["hardness"].values

    log.info("Training RandomForestRegressor on %d samples, %d features", X.shape[0], X.shape[1])

    model_bg = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=1,  # CPU‑only, deterministic
    )
    model_h = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=1,
    )
    model_bg.fit(X, y_bg)
    model_h.fit(X, y_h)

    return {"band_gap": model_bg, "hardness": model_h}
