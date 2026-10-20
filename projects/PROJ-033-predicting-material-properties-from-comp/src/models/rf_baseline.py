"""
Random‑Forest baseline for the composition‑only task.

The baseline uses composition‑weighted elemental aggregates as features,
i.e. the fraction of each element in the formula.  Because the number of
possible elements (1‑118) is fixed, we can build a dense feature matrix
with a column for every element; missing elements receive a fraction of 0.
Two independent ``RandomForestRegressor`` models are trained – one for
band‑gap and one for hardness.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from pymatgen.core import Composition

def _build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a DataFrame where each column corresponds to an element symbol
    (e.g. ``Fe``, ``O``) and each cell contains the atomic fraction of that
    element in the material's formula.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a ``formula`` column.

    Returns
    -------
    pd.DataFrame
        Index matches ``df``; columns are element symbols.
    """
    element_set = set()
    # first pass – collect all elements present in the dataset
    compositions = []
    for formula in df["formula"]:
        comp = Composition(formula)
        compositions.append(comp)
        element_set.update(comp.elements)

    # sort for reproducibility
    element_list = sorted([el.symbol for el in element_set])

    # second pass – build rows
    rows = []
    for comp in compositions:
        row = {el: comp.get_atomic_fraction(comp[el]) if el in comp else 0.0 for el in element_list}
        rows.append(row)

    return pd.DataFrame(rows, index=df.index)

def train_rf(df: pd.DataFrame, n_estimators: int = 200, random_state: int = 42):
    """
    Train Random‑Forest regressors for both targets.

    Returns
    -------
    dict
        ``{'band_gap': model_bg, 'hardness': model_h}``
    """
    X = _build_feature_matrix(df)
    y_bg = df["band_gap"].astype(float).values
    y_h = df["hardness"].astype(float).values

    model_bg = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    model_h = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    model_bg.fit(X, y_bg)
    model_h.fit(X, y_h)

    return {"band_gap": model_bg, "hardness": model_h}
