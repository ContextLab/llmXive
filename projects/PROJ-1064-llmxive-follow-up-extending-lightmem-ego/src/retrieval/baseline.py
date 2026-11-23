"""
Fixed‑Hierarchy baseline retriever.

The retriever loads a pre‑built FAISS HNSW index (CPU‑only) together
with a mapping from FAISS row indices to ``node_id`` values and the
timestamps of each memory node.  Given a query embedding and a query
timestamp, it determines the appropriate temporal bucket
(current, short‑term, long‑term) based on the age ``t`` (in days)
of each candidate node and returns the top‑k nearest neighbours that
fall within that bucket.

Errors:
  * If the index file cannot be loaded, a ``RuntimeError`` with the
    exact message ``FAISS index load failure: <details>`` is raised.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
import pandas as pd

class FixedHierarchyRetriever:
    """
    Baseline retriever that uses a deterministic FAISS HNSW index and
    routes queries to one of three temporal buckets based on the age
    (in days) of candidate memory nodes.
    """

    def __init__(
        self,
        parquet_path: Path,
        index_path: Path | None = None,
    ) -> None:
        """
        Load the FAISS index, mapping, and timestamps.

        Parameters
        ----------
        parquet_path : Path
            Path to ``memory_nodes.parquet`` (used to obtain timestamps).
        index_path : Path | None
            Path to the FAISS index file.  If ``None``, the default
            location ``data/processed/faiss_hnsw_ego4d.index`` is used.
        """
        parquet_path = Path(parquet_path)
        if not parquet_path.is_file():
            raise RuntimeError(f"Parquet file not found at {parquet_path}")

        # Load timestamps and node IDs
        df = pd.read_parquet(parquet_path, engine="pyarrow")
        self._node_ids = df["node_id"].tolist()
        self._timestamps = [
            datetime.fromisoformat(ts) for ts in df["timestamp"]
        ]

        # Resolve index path
        if index_path is None:
            index_path = (
                Path("data") / "processed" / "faiss_hnsw_ego4d.index"
            )
        index_path = Path(index_path)

        # Load FAISS index
        try:
            self._index = faiss.read_index(str(index_path))
        except Exception as e:
            raise RuntimeError(f"FAISS index load failure: {e}") from e

        # Load mapping (row index → node_id)
        mapping_path = index_path.parent / "faiss_index_mapping.json"
        try:
            with mapping_path.open("r", encoding="utf-8") as f:
                self._row_to_node = json.load(f)
        except Exception as e:
            raise RuntimeError(
                f"FAISS index load failure: unable to read mapping file ({e})"
            ) from e

    @staticmethod
    def _compute_age_days(
        query_ts: datetime, node_ts: datetime
    ) -> float:
        """Return the age ``t`` in days (query time minus node time)."""
        delta = query_ts - node_ts
        return delta.total_seconds() / 86_400.0

    @staticmethod
    def _bucket_for_age(t: float) -> str:
        """Return the bucket name for a given age ``t`` (in days)."""
        if t <= 1.0:
            return "current"
        if t <= 14.0:
            return "short_term"
        return "long_term"

    def retrieve(
        self,
        query_embedding: np.ndarray,
        query_timestamp: datetime,
        k: int = 1,
    ) -> List[Tuple[str, float]]:
        """
        Retrieve the top‑k nearest neighbours that belong to the same
        temporal bucket as the query.

        Parameters
        ----------
        query_embedding : np.ndarray
            1‑D array of shape (768,) dtype float32.
        query_timestamp : datetime
            Timestamp of the query.
        k : int, default 1
            Number of results to return.

        Returns
        -------
        List[Tuple[node_id, score]]
            ``score`` is the FAISS L2 distance (lower is better).
        """
        if query_embedding.ndim != 1 or query_embedding.shape[0] != 768:
            raise ValueError(
                f"Query embedding must be shape (768,), got {query_embedding.shape}"
            )

        # Search the whole index; we will filter by bucket afterwards.
        # Retrieve a modest over‑sample to increase chances of finding
        # enough candidates within the bucket.
        over_k = max(k * 5, 10)
        distances, indices = self._index.search(
            query_embedding.astype(np.float32).reshape(1, -1), over_k
        )
        distances = distances[0]
        indices = indices[0]

        results: List[Tuple[str, float]] = []
        for dist, idx in zip(distances, indices):
            if idx < 0:
                continue  # FAISS may return -1 for empty slots
            node_ts = self._timestamps[idx]
            age = self._compute_age_days(query_timestamp, node_ts)
            bucket = self._bucket_for_age(age)

            # Determine the bucket of the query itself (based on its
            # timestamp relative to the node timestamps).  For the
            # baseline we simply enforce that candidate and query share
            # the same bucket.
            query_age = self._compute_age_days(query_timestamp, query_timestamp)
            query_bucket = self._bucket_for_age(query_age)

            if bucket != query_bucket:
                continue

            node_id = self._row_to_node.get(str(idx), self._node_ids[idx])
            results.append((node_id, float(dist)))
            if len(results) >= k:
                break

        return results
