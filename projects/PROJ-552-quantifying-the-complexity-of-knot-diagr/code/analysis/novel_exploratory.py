"""novel_exploratory.py
================================
This module implements the first steps toward the *novel pathways* suggested by the
reviewers: data‑driven exploratory analyses that go beyond the existing composite
metric work.

Two lightweight examples are provided:

1. **Unsupervised clustering** of knot diagrams using a small set of geometric
   features (crossing number, braid index, hyperbolic volume, etc.).  The function
   ``cluster_knot_diagrams`` loads the cleaned dataset (``data/processed/knots_cleaned.csv``),
   runs ``KMeans`` from scikit‑learn, and returns a ``pandas.DataFrame`` with the
   original identifiers plus a new ``cluster`` column.

2. **Persistent homology** of the diagram‑graph representation.  The function
   ``compute_persistent_homology`` is a stub that demonstrates how one could use the
   ``gudhi`` library to extract topological signatures from a graph adjacency
   matrix.  The implementation is deliberately minimal – it validates the input
   and returns an empty list when the optional dependency is unavailable, allowing
   the rest of the pipeline to run unchanged.

Both utilities are deliberately lightweight and have no side‑effects beyond
returning Python objects, making them easy to integrate into notebooks, the
existing ``exploratory.py`` script, or downstream regression analyses.
"""

from __future__ import annotations

import pathlib
from typing import List, Tuple

import pandas as pd

# Optional imports – the core clustering works without them.
try:
    from sklearn.cluster import KMeans
except ImportError:  # pragma: no cover
    KMeans = None  # type: ignore

try:
    import gudhi
except ImportError:  # pragma: no cover
    gudhi = None  # type: ignore

DATA_ROOT = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"


def _load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned knot dataset.

    Returns
    -------
    pandas.DataFrame
        The dataframe with at least the columns required for clustering.
    """
    csv_path = DATA_ROOT / "knots_cleaned.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Cleaned dataset not found at {csv_path}")
    return pd.read_csv(csv_path)


def cluster_knot_diagrams(
    n_clusters: int = 5,
    random_state: int = 42,
    features: Tuple[str, ...] = (
        "crossing_number",
        "braid_index",
        "hyperbolic_volume",
        "determinant",
    ),
) -> pd.DataFrame:
    """Perform K‑means clustering on selected knot features.

    Parameters
    ----------
    n_clusters: int, default 5
        Desired number of clusters.
    random_state: int, default 42
        Seed for reproducibility.
    features: tuple of str, default (crossing_number, braid_index, hyperbolic_volume, determinant)
        Column names in the cleaned CSV to use for clustering.

    Returns
    -------
    pandas.DataFrame
        Original dataframe augmented with a ``cluster`` column.
    """
    if KMeans is None:  # pragma: no cover
        raise ImportError("scikit-learn is required for clustering but is not installed.")

    df = _load_cleaned_data()
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Requested features not present in data: {missing}")

    X = df[list(features)].fillna(0).values
    model = KMeans(n_clusters=n_clusters, random_state=random_state)
    labels = model.fit_predict(X)
    df = df.copy()
    df["cluster"] = labels
    return df


def compute_persistent_homology(adjacency_matrix: List[List[int]]) -> List[Tuple[int, int, float]]:
    """Compute a simple 0‑ and 1‑dimensional persistence diagram.

    This function is illustrative; it expects an undirected adjacency matrix of a
    knot diagram graph.  When ``gudhi`` is unavailable, the function returns an empty
    list so that callers can gracefully skip the topological analysis.

    Parameters
    ----------
    adjacency_matrix: list of list of int
        Square matrix where ``1`` indicates an edge between vertices.

    Returns
    -------
    list of (dimension, birth, death)
        A flat representation of the persistence pairs.
    """
    if gudhi is None:  # pragma: no cover
        # Dependency missing – return an empty result rather than raising.
        return []

    # Build a SimplexTree from the adjacency matrix.
    st = gudhi.SimplexTree()
    n = len(adjacency_matrix)
    for i in range(n):
        st.insert([i])
        for j in range(i + 1, n):
            if adjacency_matrix[i][j]:
                st.insert([i, j])
    st.initialize_filtration()
    diag = st.persistence()
    # Convert to a flat list of (dim, birth, death).
    return [(dim, birth, death) for dim, birth, death in diag]


# Example usage (executed only when run as a script).
if __name__ == "__main__":  # pragma: no cover
    try:
        clustered = cluster_knot_diagrams()
        print(clustered[["knot_id", "cluster"]].head())
    except Exception as exc:  # noqa: BLE001
        print(f"Clustering failed: {exc}")

    # Dummy adjacency matrix for illustration.
    dummy_adj = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    ph = compute_persistent_homology(dummy_adj)
    print("Persistent homology pairs:", ph)

