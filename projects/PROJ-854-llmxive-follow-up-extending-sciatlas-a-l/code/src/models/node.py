from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np

@dataclass
class Node:
    id: str
    title: str
    citation_count: int
    embedding_vector: Optional[np.ndarray]
    primary_cluster: Optional[int]
    topic_cluster: Optional[int]
