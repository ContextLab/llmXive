"""
Entity Linking Module for VideoKR Knowledge Graph.

This module provides functionality to map question entities (from natural language
questions) to nodes in the knowledge graph using fuzzy string matching and
embedding-based similarity.
"""

import re
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

# Optional dependencies for advanced matching
try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUTHY_AVAILABLE = True
except ImportError:
    FUZZYWUTHY_AVAILABLE = False

try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from utils.config import get_project_root, get_path, ensure_dir, get_config


class EntityLinker:
    """
    Maps entities extracted from questions to nodes in the knowledge graph.

    Supports two matching strategies:
    1. Fuzzy string matching (using fuzzywuzzy)
    2. Embedding-based similarity (using pre-computed node embeddings)

    The linker prioritizes exact matches, then falls back to fuzzy matching,
    and finally to embedding similarity if available.
    """

    def __init__(
        self,
        graph_nodes: Dict[str, Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
        embeddings_path: Optional[Union[str, Path]] = None,
        min_fuzzy_score: int = 80,
        min_embedding_sim: float = 0.6
    ):
        """
        Initialize the Entity Linker.

        Args:
            graph_nodes: Dictionary mapping node IDs to node attributes.
                        Expected format: {node_id: {"name": str, "type": str, ...}}
            config: Optional configuration dictionary.
            embeddings_path: Path to a JSON file containing pre-computed node embeddings.
                            Format: {node_id: [float, float, ...]}
            min_fuzzy_score: Minimum fuzzy matching score (0-100) to consider a match.
            min_embedding_sim: Minimum cosine similarity (0-1) to consider a match.
        """
        self.graph_nodes = graph_nodes
        self.config = config or get_config()
        self.min_fuzzy_score = min_fuzzy_score
        self.min_embedding_sim = min_embedding_sim
        self.embeddings = None
        self.node_names = []
        self.node_id_map = {}  # Maps name -> node_id for exact matching

        # Pre-process node names for matching
        self._preprocess_nodes()

        # Load embeddings if available
        if embeddings_path:
            self._load_embeddings(embeddings_path)

    def _preprocess_nodes(self) -> None:
        """Pre-process node names for efficient matching."""
        self.node_names = []
        self.node_id_map = {}

        for node_id, attrs in self.graph_nodes.items():
            name = attrs.get("name", "")
            if not name:
                continue

            # Create a normalized version for exact matching
            normalized = self._normalize_string(name)
            self.node_id_map[normalized] = node_id
            self.node_names.append(name)

    def _load_embeddings(self, embeddings_path: Union[str, Path]) -> None:
        """Load pre-computed node embeddings from a JSON file."""
        embeddings_path = Path(embeddings_path)
        if not embeddings_path.exists():
            return

        try:
            with open(embeddings_path, 'r', encoding='utf-8') as f:
                self.embeddings = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise RuntimeError(f"Failed to load embeddings from {embeddings_path}: {e}")

    @staticmethod
    def _normalize_string(s: str) -> str:
        """Normalize a string for matching: lowercase, remove punctuation, collapse spaces."""
        s = s.lower()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    @staticmethod
    def _extract_entities(text: str) -> List[str]:
        """
        Extract potential entities from text.

        This is a simple heuristic-based extractor that looks for:
        - Capitalized words (potential proper nouns)
        - Common entity patterns (e.g., "video X", "person Y")

        Args:
            text: The input text (question or statement).

        Returns:
            List of extracted entity candidates.
        """
        # Normalize the text
        text = text.strip()

        # Extract capitalized words/phrases (potential entities)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)

        # Extract common entity patterns
        patterns = [
            r'video\s+(\d+)',
            r'person\s+(\w+)',
            r'actor\s+(\w+)',
            r'director\s+(\w+)',
            r'scene\s+(\w+)',
            r'object\s+(\w+)',
        ]

        entities = set(capitalized)

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update(matches)

        # Also include the full text as a fallback candidate
        if len(entities) == 0:
            entities.add(text)

        return list(entities)

    def _fuzzy_match(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        Perform fuzzy string matching against node names.

        Args:
            query: The query string (entity name).
            top_k: Number of top matches to return.

        Returns:
            List of (node_id, matched_name, score) tuples.
        """
        if not FUZZYWUTHY_AVAILABLE:
            return []

        normalized_query = self._normalize_string(query)

        # Try exact match first
        if normalized_query in self.node_id_map:
            node_id = self.node_id_map[normalized_query]
            name = self.graph_nodes[node_id].get("name", "")
            return [(node_id, name, 100.0)]

        # Fuzzy match
        matches = process.extract(
            query,
            self.node_names,
            scorer=fuzz.ratio,
            limit=top_k
        )

        results = []
        for matched_name, score in matches:
            if score >= self.min_fuzzy_score:
                node_id = None
                # Find the node_id for this name
                for nid, attrs in self.graph_nodes.items():
                    if attrs.get("name") == matched_name:
                        node_id = nid
                        break

                if node_id:
                    results.append((node_id, matched_name, float(score)))

        return results

    def _embedding_match(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        Perform embedding-based similarity matching.

        Args:
            query: The query string (entity name).
            query_embedding: Pre-computed embedding for the query. If None,
                            a simple bag-of-words embedding is used.
            top_k: Number of top matches to return.

        Returns:
            List of (node_id, matched_name, similarity) tuples.
        """
        if not SKLEARN_AVAILABLE or self.embeddings is None:
            return []

        if query_embedding is None:
            # Simple bag-of-words embedding (fallback)
            query_embedding = self._create_simple_embedding(query)

        # Convert query embedding to numpy array
        query_vec = np.array(query_embedding).reshape(1, -1)

        # Get all node embeddings
        node_ids = list(self.embeddings.keys())
        if not node_ids:
            return []

        # Build matrix of node embeddings
        embed_matrix = []
        valid_node_ids = []
        valid_names = []

        for node_id in node_ids:
            if node_id in self.graph_nodes:
                embed_matrix.append(self.embeddings[node_id])
                valid_node_ids.append(node_id)
                valid_names.append(self.graph_nodes[node_id].get("name", ""))

        if not embed_matrix:
            return []

        embed_matrix = np.array(embed_matrix)

        # Compute cosine similarity
        similarities = cosine_similarity(query_vec, embed_matrix)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            sim = float(similarities[idx])
            if sim >= self.min_embedding_sim:
                results.append((valid_node_ids[idx], valid_names[idx], sim))

        return results

    def _create_simple_embedding(self, text: str) -> List[float]:
        """
        Create a simple bag-of-words embedding for the text.

        This is a fallback when no pre-computed embeddings are available.
        Uses a fixed vocabulary based on common entity tokens.

        Args:
            text: Input text.

        Returns:
            List of float values representing the embedding.
        """
        # Simple vocabulary based on common tokens
        vocab = [
            'video', 'scene', 'person', 'actor', 'director', 'object',
            'action', 'event', 'time', 'location', 'character', 'story'
        ]

        text_lower = text.lower()
        embedding = [0.0] * len(vocab)

        for i, token in enumerate(vocab):
            if token in text_lower:
                embedding[i] = 1.0

        return embedding

    def link_entity(
        self,
        entity: str,
        use_fuzzy: bool = True,
        use_embedding: bool = True,
        top_k: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Link a single entity to graph nodes.

        Args:
            entity: The entity string to link.
            use_fuzzy: Whether to use fuzzy matching.
            use_embedding: Whether to use embedding matching.
            top_k: Maximum number of results to return.

        Returns:
            List of dictionaries with keys:
            - node_id: The matched node ID
            - matched_name: The name that was matched
            - score: The matching score (fuzzy or similarity)
            - method: The method used ('exact', 'fuzzy', or 'embedding')
        """
        results = []

        # Try exact match first
        normalized = self._normalize_string(entity)
        if normalized in self.node_id_map:
            node_id = self.node_id_map[normalized]
            name = self.graph_nodes[node_id].get("name", "")
            results.append({
                "node_id": node_id,
                "matched_name": name,
                "score": 1.0,
                "method": "exact"
            })
            return results[:top_k]

        # Try fuzzy matching
        if use_fuzzy:
            fuzzy_results = self._fuzzy_match(entity, top_k=top_k)
            for node_id, matched_name, score in fuzzy_results:
                results.append({
                    "node_id": node_id,
                    "matched_name": matched_name,
                    "score": score / 100.0,  # Normalize to 0-1
                    "method": "fuzzy"
                })

        # Try embedding matching
        if use_embedding and self.embeddings is not None:
            embed_results = self._embedding_match(entity, top_k=top_k)
            for node_id, matched_name, sim in embed_results:
                # Only add if not already found with higher score
                existing = next(
                    (r for r in results if r["node_id"] == node_id),
                    None
                )
                if existing:
                    if sim > existing["score"]:
                        existing["score"] = sim
                        existing["method"] = "embedding"
                else:
                    results.append({
                        "node_id": node_id,
                        "matched_name": matched_name,
                        "score": sim,
                        "method": "embedding"
                    })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]

    def link_question(
        self,
        question: str,
        use_fuzzy: bool = True,
        use_embedding: bool = True,
        min_entities: int = 1
    ) -> Dict[str, Any]:
        """
        Link all entities in a question to graph nodes.

        Args:
            question: The question text.
            use_fuzzy: Whether to use fuzzy matching.
            use_embedding: Whether to use embedding matching.
            min_entities: Minimum number of entities to extract.

        Returns:
            Dictionary with keys:
            - entities: List of extracted entities with their links
            - all_linked: Boolean indicating if all entities were linked
            - link_count: Number of entities successfully linked
        """
        extracted = self._extract_entities(question)

        if len(extracted) < min_entities:
            # If no entities extracted, try to link the whole question
            extracted = [question]

        linked_entities = []
        all_linked = True

        for entity in extracted:
            links = self.link_entity(
                entity,
                use_fuzzy=use_fuzzy,
                use_embedding=use_embedding,
                top_k=1
            )

            if links:
                linked_entities.append({
                    "original": entity,
                    "links": links
                })
            else:
                linked_entities.append({
                    "original": entity,
                    "links": None
                })
                all_linked = False

        return {
            "entities": linked_entities,
            "all_linked": all_linked,
            "link_count": len([e for e in linked_entities if e["links"]])
        }

    def batch_link(
        self,
        questions: List[str],
        use_fuzzy: bool = True,
        use_embedding: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Link entities in multiple questions.

        Args:
            questions: List of question strings.
            use_fuzzy: Whether to use fuzzy matching.
            use_embedding: Whether to use embedding matching.

        Returns:
            List of link results for each question.
        """
        return [
            self.link_question(q, use_fuzzy, use_embedding)
            for q in questions
        ]


def load_graph_from_file(
    graph_path: Union[str, Path],
    format: str = "json"
) -> Dict[str, Dict[str, Any]]:
    """
    Load a knowledge graph from a file.

    Args:
        graph_path: Path to the graph file.
        format: File format ('json' or 'csv').

    Returns:
        Dictionary of nodes: {node_id: {attributes}}
    """
    graph_path = Path(graph_path)

    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    if format == "json":
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list and dict formats
            if isinstance(data, list):
                return {item.get("id", str(i)): item for i, item in enumerate(data)}
            return data
    elif format == "csv":
        import csv
        nodes = {}
        with open(graph_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                node_id = row.get("id", row.get("node_id", str(len(nodes))))
                nodes[node_id] = row
        return nodes
    else:
        raise ValueError(f"Unsupported format: {format}")


def create_entity_linker(
    graph_path: Union[str, Path],
    embeddings_path: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    min_fuzzy_score: int = 80,
    min_embedding_sim: float = 0.6
) -> EntityLinker:
    """
    Factory function to create an EntityLinker instance.

    Args:
        graph_path: Path to the knowledge graph file.
        embeddings_path: Optional path to node embeddings.
        config: Optional configuration dictionary.
        min_fuzzy_score: Minimum fuzzy matching score.
        min_embedding_sim: Minimum embedding similarity.

    Returns:
        Configured EntityLinker instance.
    """
    graph_nodes = load_graph_from_file(graph_path)

    return EntityLinker(
        graph_nodes=graph_nodes,
        config=config,
        embeddings_path=embeddings_path,
        min_fuzzy_score=min_fuzzy_score,
        min_embedding_sim=min_embedding_sim
    )