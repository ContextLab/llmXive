from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class Node:
    """
    Represents a scientific paper or node in the knowledge graph.

    Attributes:
        id (str): Unique identifier for the node (e.g., OpenAlex ID).
        title (str): Title of the scientific paper.
        citation_count (int): Number of citations received by the paper.
        embedding_vector (Optional[List[float]]): Vector embedding of the title.
        primary_cluster (Optional[int]): Cluster ID assigned by Louvain algorithm (topology).
        topic_cluster (Optional[int]): Cluster ID assigned by K-Means algorithm (text).
    """
    id: str
    title: str
    citation_count: int
    embedding_vector: Optional[List[float]] = field(default=None)
    primary_cluster: Optional[int] = field(default=None)
    topic_cluster: Optional[int] = field(default=None)

    def __post_init__(self):
        """
        Validates and normalizes the embedding_vector if provided.
        Converts numpy arrays to lists for JSON/Parquet serialization compatibility.
        """
        if self.embedding_vector is not None:
            if isinstance(self.embedding_vector, np.ndarray):
                self.embedding_vector = self.embedding_vector.tolist()
            elif not isinstance(self.embedding_vector, list):
                raise TypeError(
                    f"embedding_vector must be a list or numpy array, got {type(self.embedding_vector)}"
                )

    def to_dict(self) -> dict:
        """
        Converts the Node instance to a dictionary for serialization.
        """
        return {
            "id": self.id,
            "title": self.title,
            "citation_count": self.citation_count,
            "embedding_vector": self.embedding_vector,
            "primary_cluster": self.primary_cluster,
            "topic_cluster": self.topic_cluster,
        }