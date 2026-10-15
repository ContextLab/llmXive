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

# Attempt to import sentence_transformers at module level to allow monkeypatching in tests
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

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
        self.node_names = list(graph.keys())

    def extract_entities(self, text: str) -> List[str]:
        """
        Extract potential entities from text.

        Args:
            text (str): Input text.

        Returns:
            List[str]: List of extracted entities.
        """
        # Simple entity extraction: capitalized words and proper nouns
        # Filter out single-character tokens (e.g., "I") which are not useful for linking
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        filtered = [e for e in entities if len(e) > 1]
        return list(set(filtered))

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

    Implements T102 requirements:
    - If 'node_id' or 'entity_id' exists, return them with confidence 1.0.
    - If sentence_transformers is available, use embedding similarity.
    - Otherwise, use fuzzy string matching.
    - Results below threshold are set to None.
    """
    df_out = df.copy()

    # 1. Check for pre-existing IDs
    for id_col in ['node_id', 'entity_id']:
        if id_col in df_out.columns:
            df_out['entity_node_id'] = df_out[id_col]
            df_out['confidence'] = 1.0
            df_out['entity_node_id'] = pd.Series(df_out['entity_node_id'], dtype=object)
            return df_out

    # 2. Determine linking strategy based on availability of sentence_transformers
    # Note: SentenceTransformer is imported at module level to facilitate testing.
    if SentenceTransformer is not None:
        # Embedding path
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            node_names = list(graph_nodes.keys())
            node_embeddings = model.encode(node_names)

            entity_ids = []
            confidences = []

            for text in df_out['question']:
                if not isinstance(text, str):
                    entity_ids.append(None)
                    confidences.append(0.0)
                    continue

                query_embedding = model.encode([text])[0]
                # Cosine similarity: dot product of normalized vectors
                norm_q = np.linalg.norm(query_embedding)
                if norm_q == 0:
                    entity_ids.append(None)
                    confidences.append(0.0)
                    continue

                # Normalize query embedding
                q_norm = query_embedding / norm_q

                best_node = None
                best_score = 0.0

                for idx, node_emb in enumerate(node_embeddings):
                    norm_n = np.linalg.norm(node_emb)
                    if norm_n == 0:
                        continue
                    # Dot product of normalized vectors is cosine similarity
                    sim = np.dot(q_norm, node_emb / norm_n)
                    if sim > best_score:
                        best_score = sim
                        best_node = node_names[idx]

                if best_score >= threshold:
                    entity_ids.append(best_node)
                    confidences.append(float(best_score))
                else:
                    entity_ids.append(None)
                    confidences.append(float(best_score))

            df_out['entity_node_id'] = pd.Series(entity_ids, dtype=object)
            df_out['confidence'] = confidences
            return df_out
        except Exception as e:
            logging.warning(f"Embedding linking failed, falling back to fuzzy: {e}")

    # 3. Fuzzy matching path (Fallback or Default)
    linker = EntityLinker(graph_nodes, threshold)

    entity_ids = []
    confidences = []

    for text in df_out['question']:
        if not isinstance(text, str):
            entity_ids.append(None)
            confidences.append(0.0)
            continue

        # We treat the whole question as the entity for the fuzzy linker
        # since the EntityLinker.link_entity handles similarity.
        res = linker.link_entity(text)
        if res:
            node_id, conf = res
            entity_ids.append(node_id)
            confidences.append(conf)
        else:
            # Calculate best score even if below threshold for the confidence column
            best_score = 0.0
            for node_name in linker.node_names:
                score = linker.calculate_similarity(text, node_name)
                if score > best_score:
                    best_score = score
            entity_ids.append(None)
            confidences.append(best_score)

    df_out['entity_node_id'] = pd.Series(entity_ids, dtype=object)
    df_out['confidence'] = confidences
    return df_out


def main() -> None:
    """Main entry point for entity linker module."""
    import argparse

    parser = argparse.ArgumentParser(description="Entity linker utility")
    parser.add_argument("graph_path", type=str, help="Path to the JSON graph file")
    parser.add_argument("data_path", type=str, help="Path to a CSV file containing a 'question' column")
    parser.add_argument("--threshold", type=float, default=0.5, help="Confidence threshold (default: 0.5)")
    args = parser.parse_args()

    graph = load_graph_from_file(args.graph_path)
    df = pd.read_csv(args.data_path)
    linked_df = link_dataframe(df, graph, threshold=args.threshold)
    print(linked_df.head())


if __name__ == "__main__":
    main()
