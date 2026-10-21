"""
Entity linking module for mapping question entities to graph nodes.
Implements deterministic linking using exact match and Levenshtein distance ≤ 2.
No embedding models are used.
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

import pandas as pd

from utils.config import get_project_root, get_path, ensure_dir

logger = logging.getLogger(__name__)

def load_graph_from_file(graph_path: Union[str, Path]) -> Dict[Any, Set[Any]]:
    """
    Load a graph from a JSON file.

    Args:
        graph_path (Union[str, Path]): Path to the graph file.

    Returns:
        Dict[Any, Set[Any]]: Adjacency list representation of the graph.
    """
    path_obj = Path(graph_path) if isinstance(graph_path, str) else graph_path

    with open(path_obj, 'r') as f:
        data = json.load(f)

    graph: Dict[Any, Set[Any]] = {}
    for node, neighbors in data.items():
        graph[node] = set(neighbors)

    return graph


def _normalize(text: str) -> str:
    """
    Normalise a string: lower‑case, remove punctuation, collapse whitespace.
    """
    # Lower case
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _levenshtein(a: str, b: str) -> int:
    """
    Compute the Levenshtein distance between two strings.
    Simple DP implementation; suitable for short strings.
    """
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    # Initialise matrix
    previous_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current_row = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (ca != cb)
            current_row[j] = min(insertions, deletions, substitutions)
        previous_row = current_row

    return previous_row[-1]


class EntityLinker:
    """
    Deterministic entity linker using exact match and Levenshtein distance ≤ 2.
    """

    def __init__(self, graph: Dict[Any, Set[Any]]):
        """
        Initialise the linker.

        Args:
            graph (Dict[Any, Set[Any]]): Graph adjacency list.
        """
        self.graph = graph
        # Build a mapping from normalised node name to original node identifier
        self.normalised_to_node: Dict[str, str] = {}
        for node in graph.keys():
            norm = _normalize(str(node))
            # In case of collisions, keep the first encountered node
            self.normalised_to_node.setdefault(norm, node)

        # Pre‑compute a list of (original_node, normalised_name) for Levenshtein fallback
        self.node_norm_list: List[Tuple[str, str]] = [
            (node, _normalize(str(node))) for node in graph.keys()
        ]

    def link_entity(self, text: str) -> Tuple[Optional[str], float]:
        """
        Link a single text (treated as an entity) to a graph node.

        Returns:
            Tuple[Optional[str], float]: (node_id or None, confidence flag).
            Confidence is 1.0 for exact match, 0.5 for Levenshtein match,
            0.0 for failure.
        """
        if not isinstance(text, str):
            return None, 0.0

        norm_text = _normalize(text)

        # Exact match (case‑insensitive, punctuation‑insensitive)
        if norm_text in self.normalised_to_node:
            return self.normalised_to_node[norm_text], 1.0

        # Levenshtein fallback (distance ≤ 2)
        best_node: Optional[str] = None
        best_dist = 3  # we only care about distances 0‑2
        for node, norm_node in self.node_norm_list:
            dist = _levenshtein(norm_text, norm_node)
            if dist < best_dist:
                best_dist = dist
                best_node = node
                if dist == 0:
                    break  # shouldn't happen (already caught), but early exit

        if best_node is not None and best_dist <= 2:
            # Confidence 0.5 indicates fuzzy match
            return best_node, 0.5

        return None, 0.0


def create_entity_linker(
    graph_path: Union[str, Path]
) -> EntityLinker:
    """
    Helper to create an EntityLinker from a JSON graph file.

    Args:
        graph_path (Union[str, Path]): Path to the graph file.

    Returns:
        EntityLinker: Configured deterministic entity linker.
    """
    graph = load_graph_from_file(graph_path)
    return EntityLinker(graph)


def link_dataframe(
    df: pd.DataFrame,
    graph_nodes: Dict[Any, Set[Any]],
    threshold: float = 0.5  # retained for API compatibility; not used
) -> pd.DataFrame:
    """
    Link entities in a DataFrame to graph nodes.

    Behaviour:
    1. If a column ``node_id`` or ``entity_id`` exists, copy it to ``entity_node_id``
       and set ``confidence`` to ``1.0``.
    2. Otherwise, treat the whole ``question`` field as the entity string,
       apply deterministic linking (exact match then Levenshtein ≤ 2).
    3. Return a DataFrame with added ``entity_node_id`` and ``confidence`` columns.

    Args:
        df (pd.DataFrame): Input DataFrame containing at least a ``question`` column.
        graph_nodes (Dict[Any, Set[Any]]): Graph adjacency list.
        threshold (float): Kept for backward compatibility; ignored.

    Returns:
        pd.DataFrame: DataFrame with linking results.
    """
    df_out = df.copy()

    # 1. Pre‑existing ID columns
    for id_col in ['node_id', 'entity_id']:
        if id_col in df_out.columns:
            df_out['entity_node_id'] = df_out[id_col]
            df_out['confidence'] = 1.0
            df_out['entity_node_id'] = pd.Series(df_out['entity_node_id'], dtype=object)
            return df_out

    # 2. Deterministic linking
    linker = EntityLinker(graph_nodes)

    entity_ids: List[Optional[str]] = []
    confidences: List[float] = []

    for text in df_out.get('question', []):
        node_id, conf = linker.link_entity(str(text))
        entity_ids.append(node_id)
        confidences.append(conf)

    df_out['entity_node_id'] = pd.Series(entity_ids, dtype=object)
    df_out['confidence'] = confidences
    return df_out


def main() -> None:
    """Command‑line interface for the entity linker."""
    import argparse

    parser = argparse.ArgumentParser(description="Entity linker utility")
    parser.add_argument("graph_path", type=str, help="Path to the JSON graph file")
    parser.add_argument("data_path", type=str, help="Path to a CSV file containing a 'question' column")
    args = parser.parse_args()

    graph = load_graph_from_file(args.graph_path)
    df = pd.read_csv(args.data_path)
    linked_df = link_dataframe(df, graph)
    print(linked_df.head())


if __name__ == "__main__":
    main()
