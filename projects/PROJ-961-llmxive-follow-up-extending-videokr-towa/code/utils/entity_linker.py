"""
Entity linking module for mapping question entities to graph nodes.
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

import pandas as pd
import numpy as np

from utils.config import get_project_root, get_path, ensure_dir, get_config

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


class EntityLinker:
    """
    Entity linker for mapping question entities to graph nodes.
    """

    def __init__(self, graph: Dict[Any, Set[Any]], threshold: float = 0.5):
        """
        Initialize the entity linker.

        Args:
            graph (Dict[Any, Set[Any]]): Graph adjacency list.
            threshold (float): Confidence threshold for linking.
        """
        self.graph = graph
        self.threshold = threshold
        self.node_names = set(graph.keys())

    def extract_entities(self, text: str) -> List[str]:
        """
        Extract potential entities from text.

        Args:
            text (str): Input text.

        Returns:
            List[str]: List of extracted entities.
        """
        # Simple entity extraction: capitalized words and proper nouns
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(entities))

    def calculate_similarity(self, entity: str, node_name: str) -> float:
        """
        Calculate similarity between an entity and a node name.

        Args:
            entity (str): Extracted entity.
            node_name (str): Graph node name.

        Returns:
            float: Similarity score (0.0 to 1.0).
        """
        entity_lower = entity.lower()
        node_lower = node_name.lower()

        # Exact match
        if entity_lower == node_lower:
            return 1.0

        # Substring match
        if entity_lower in node_lower or node_lower in entity_lower:
            return 0.8

        # Word overlap
        entity_words = set(entity_lower.split())
        node_words = set(node_lower.split())

        if not entity_words or not node_words:
            return 0.0

        overlap = len(entity_words & node_words)

        return overlap / max(len(entity_words), len(node_words))

    def link_entity(self, entity: str) -> Optional[Tuple[str, float]]:
        """
        Link an entity to the best matching graph node.

        Args:
            entity (str): Entity to link.

        Returns:
            Optional[Tuple[str, float]]: Tuple of (node_id, confidence) or None.
        """
        best_match = None
        best_score = 0.0

        for node_name in self.node_names:
            score = self.calculate_similarity(entity, node_name)
            if score > best_score:
                best_score = score
                best_match = node_name

        if best_score >= self.threshold:
            return (best_match, best_score)

        return None

    def link_entities(self, text: str) -> List[Tuple[str, float]]:
        """
        Link all entities in text to graph nodes.

        Args:
            text (str): Input text.

        Returns:
            List[Tuple[str, float]]: List of (node_id, confidence) tuples.
        """
        entities = self.extract_entities(text)
        links = []

        for entity in entities:
            link = self.link_entity(entity)
            if link:
                links.append(link)

        return links


def create_entity_linker(
    graph_path: Union[str, Path],
    threshold: float = 0.5
) -> EntityLinker:
    """
    Create an entity linker from a graph file.

    Args:
        graph_path (Union[str, Path]): Path to the graph file.
        threshold (float): Confidence threshold.

    Returns:
        EntityLinker: Configured entity linker.
    """
    graph = load_graph_from_file(graph_path)
    return EntityLinker(graph, threshold)


def link_dataframe(
    df: pd.DataFrame,
    graph_nodes: Dict[Any, Set[Any]],
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Link entities in a DataFrame to graph nodes.

    This function implements the logic required for task T102:
    - If the DataFrame already contains a ``node_id`` or ``entity_id`` column,
      those identifiers are copied to the output column ``entity_node_id`` and
      a confidence of ``1.0`` is assigned.
    - Otherwise, each row's ``question`` text is examined.  When the optional
      ``sentence_transformers`` package is available, cosine similarity of
      sentence embeddings is used; otherwise a simple fuzzy‑string matching
      approach (implemented in :class:`EntityLinker`) is employed.
    - If the best match's confidence is below ``threshold``, ``entity_node_id``
      is set to ``None`` and confidence to ``0.0``.

    Args:
        df (pd.DataFrame): Input DataFrame. Must contain a ``question`` column.
        graph_nodes (Dict[Any, Set[Any]]): Adjacency list of the knowledge graph.
        threshold (float): Confidence threshold for accepting a match.

    Returns:
        pd.DataFrame: A copy of ``df`` with two additional columns:
            ``entity_node_id`` – the linked node identifier (or ``None``) and
            ``confidence`` – a float in ``[0, 1]``.
    """
    # Work on a copy to avoid side‑effects
    df_out = df.copy()

    # ------------------------------------------------------------------
    # 1. Short‑circuit if IDs are already present
    # ------------------------------------------------------------------
    if 'node_id' in df_out.columns:
        df_out['entity_node_id'] = df_out['node_id']
        df_out['confidence'] = 1.0
        return df_out

    if 'entity_id' in df_out.columns:
        df_out['entity_node_id'] = df_out['entity_id']
        df_out['confidence'] = 1.0
        return df_out

    # ------------------------------------------------------------------
    # 2. Prepare the linker (fuzzy) and optionally the embedding model
    # ------------------------------------------------------------------
    linker = EntityLinker(graph_nodes, threshold)

    use_embeddings = False
    embedding_model = None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        use_embeddings = True
    except Exception:
        use_embeddings = False

    # Helper that returns (node_id, confidence) for a single text entry.
    def _link_text(text: Any) -> Tuple[Optional[str], float]:
        if not isinstance(text, str):
            return None, 0.0

        # ------------------------------------------------------------------
        # Embedding based similarity (if available)
        # ------------------------------------------------------------------
        if use_embeddings and embedding_model is not None:
            query_vec = embedding_model.encode([text])[0]
            best_node = None
            best_score = 0.0
            for node in linker.node_names:
                node_vec = embedding_model.encode([node])[0]
                denom = (np.linalg.norm(query_vec) * np.linalg.norm(node_vec))
                if denom == 0:
                    continue
                sim = np.dot(query_vec, node_vec) / denom
                if sim > best_score:
                    best_score = sim
                    best_node = node
            if best_score >= threshold and best_node is not None:
                return best_node, float(best_score)
            return None, 0.0

        # ------------------------------------------------------------------
        # Fuzzy string matching path – use the whole text as the entity
        # ------------------------------------------------------------------
        link = linker.link_entity(text)
        if link:
            node_id, conf = link
            return node_id, float(conf)
        return None, 0.0

    # ------------------------------------------------------------------
    # 3. Apply linking row‑wise
    # ------------------------------------------------------------------
    entity_ids: List[Optional[str]] = []
    confidences: List[float] = []

    for question in df_out.get('question', []):
        node_id, conf = _link_text(question)
        entity_ids.append(node_id)
        confidences.append(conf)

    df_out['entity_node_id'] = entity_ids
    df_out['confidence'] = confidences

    return df_out


def main() -> None:
    """Main entry point for entity linker module."""
    import argparse

    parser = argparse.ArgumentParser(description="Entity linker utility")
    parser.add_argument(
        "graph_path", type=str, help="Path to the JSON graph file"
    )
    parser.add_argument(
        "data_path", type=str, help="Path to a CSV file containing a 'question' column"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Confidence threshold for linking (default: 0.5)",
    )
    args = parser.parse_args()

    # Load inputs
    graph = load_graph_from_file(args.graph_path)
    df = pd.read_csv(args.data_path)

    # Perform linking
    linked_df = link_dataframe(df, graph, threshold=args.threshold)

    # Print a short summary
    print(linked_df.head())


if __name__ == "__main__":
    main()