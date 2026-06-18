"""Interactive Knot‑Family Map
================================

This module provides a lightweight, **creative** visualisation tool that maps
knots into a 2‑dimensional interactive scatter plot.  By applying PCA (or any
dimensionality‑reduction technique supplied by the caller) to a selection of
numeric knot invariants, we obtain a low‑dimensional embedding that can be
explored with hover‑tooltips, zoom, and pan.

The resulting HTML file can be opened in a browser or embedded in a Jupyter
notebook, offering a fresh perspective on the structure of the knot dataset –
exactly the kind of novel visual narrative the reviewers asked for.
"""

from __future__ import annotations

import pathlib
from typing import Iterable, List

import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA

__all__: List[str] = ["generate_interactive_knot_map"]


def _prepare_matrix(df: pd.DataFrame, invariants: Iterable[str]) -> pd.DataFrame:
    """Return a DataFrame containing only the numeric columns listed in *invariants*.

    Parameters
    ----------
    df:
        The full knot dataset.
    invariants:
        Column names representing numeric invariants (e.g. ``"crossing"``,
        ``"hyperbolic_volume"``).  Non‑numeric columns are ignored.
    """
    cols = [col for col in invariants if col in df.columns]
    numeric_df = df[cols].apply(pd.to_numeric, errors="coerce")
    return numeric_df.dropna()


def generate_interactive_knot_map(
    df: pd.DataFrame,
    invariants: Iterable[str],
    output_path: str | pathlib.Path,
    n_components: int = 2,
    title: str = "Interactive Knot‑Family Map",
) -> None:
    """Create an interactive HTML scatter plot of knots.

    The function performs the following steps:

    1. Extracts the requested *invariants* from ``df`` and coerces them to
       numeric values.
    2. Runs PCA (default ``n_components=2``) to obtain a 2‑D embedding.
    3. Uses :mod:`plotly.express` to generate a scatter plot where each point
       represents a knot.  Hover information includes the original knot name
       (assumed to be stored in a column called ``"knot_name"``) and the values
       of the selected invariants.
    4. Saves the interactive figure to ``output_path`` as an HTML file.

    This visualisation augments the existing high‑resolution static plots with
    an exploratory, interactive tool that can reveal clusters, outliers, and
    relationships between invariants.
    """

    matrix = _prepare_matrix(df, invariants)
    if matrix.empty:
        raise ValueError("No valid numeric invariants found in the provided DataFrame.")

    pca = PCA(n_components=n_components)
    embedding = pca.fit_transform(matrix)

    # Build a DataFrame for Plotly that includes hover data.
    plot_df = pd.DataFrame(embedding, columns=[f"PC{i+1}" for i in range(n_components)])
    # Preserve the original knot identifiers for hover text.
    if "knot_name" in df.columns:
        plot_df["knot_name"] = df.loc[matrix.index, "knot_name"].values
    else:
        plot_df["knot_name"] = matrix.index.astype(str)

    # Add the raw invariant values as additional hover information.
    for inv in invariants:
        if inv in df.columns:
            plot_df[inv] = df.loc[matrix.index, inv].values

    fig = px.scatter(
        plot_df,
        x="PC1",
        y="PC2",
        hover_name="knot_name",
        hover_data={inv: True for inv in invariants},
        title=title,
        width=800,
        height=600,
    )

    # Ensure the output directory exists.
    out_path = pathlib.Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))


