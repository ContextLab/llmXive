from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json
from pathlib import Path


@dataclass
class Subject:
    """
    Represents a single participant in the study.
    Includes demographic info, group assignment (e.g., mTBI vs Control),
    and links to their longitudinal data.
    """
    subject_id: str
    group: str  # e.g., 'mTBI', 'Control'
    age: Optional[float] = None
    sex: Optional[str] = None
    education_years: Optional[float] = None
    
    # Longitudinal data storage
    # Keys: time_point_label (e.g., 'acute', 'chronic')
    # Values: ConnectivityMatrix or GraphMetrics instances
    time_points: Dict[str, Any] = field(default_factory=dict)
    
    # Clinical scores (optional, for correlation analysis)
    cognitive_scores: Dict[str, float] = field(default_factory=dict)
    
    def add_time_point(self, label: str, data: Any) -> None:
        """Add a data point (ConnectivityMatrix or GraphMetrics) for a specific time point."""
        self.time_points[label] = data
    
    def add_cognitive_score(self, label: str, score: float) -> None:
        """Add a cognitive score for a specific assessment."""
        self.cognitive_scores[label] = score
    
    def get_time_points(self) -> List[str]:
        """Return list of available time point labels."""
        return list(self.time_points.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize subject to dictionary."""
        return {
            'subject_id': self.subject_id,
            'group': self.group,
            'age': self.age,
            'sex': self.sex,
            'education_years': self.education_years,
            'time_points': list(self.time_points.keys()),
            'cognitive_scores': self.cognitive_scores
        }


@dataclass
class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a specific subject and time point.
    Stores the matrix as a numpy array and metadata about its construction.
    """
    matrix: np.ndarray
    labels: List[str]  # Region names (e.g., AAL atlas labels)
    subject_id: str
    time_point: str
    method: str = 'pearson'  # Correlation method used
    threshold: Optional[float] = None  # Threshold applied if any
    
    def __post_init__(self):
        if not isinstance(self.matrix, np.ndarray):
            self.matrix = np.array(self.matrix)
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError("Connectivity matrix must be square.")
        if len(self.labels) != self.matrix.shape[0]:
            raise ValueError("Number of labels must match matrix dimensions.")
    
    @property
    def n_regions(self) -> int:
        """Number of regions (nodes) in the network."""
        return self.matrix.shape[0]
    
    def get_edge_list(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Convert matrix to edge list format.
        Optionally applies a threshold to filter weak connections.
        """
        edges = []
        n = self.matrix.shape[0]
        for i in range(n):
            for j in range(i + 1, n):  # Upper triangle only (undirected)
                val = self.matrix[i, j]
                if threshold is None or abs(val) >= threshold:
                    edges.append({
                        'source': self.labels[i],
                        'target': self.labels[j],
                        'weight': float(val)
                    })
        return edges
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (matrix converted to list of lists)."""
        return {
            'subject_id': self.subject_id,
            'time_point': self.time_point,
            'method': self.method,
            'threshold': self.threshold,
            'n_regions': self.n_regions,
            'labels': self.labels,
            'matrix': self.matrix.tolist()
        }
    
    def save(self, path: Path) -> None:
        """Save connectivity matrix to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'ConnectivityMatrix':
        """Load connectivity matrix from a JSON file."""
        path = Path(path)
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            matrix=np.array(data['matrix']),
            labels=data['labels'],
            subject_id=data['subject_id'],
            time_point=data['time_point'],
            method=data.get('method', 'pearson'),
            threshold=data.get('threshold')
        )


@dataclass
class GraphMetrics:
    """
    Stores graph theoretical metrics calculated from a connectivity matrix.
    Includes global and local efficiency, modularity, clustering coefficient, etc.
    """
    subject_id: str
    time_point: str
    global_efficiency: float
    local_efficiency: float
    modularity: float
    clustering_coefficient: Optional[float] = None
    characteristic_path_length: Optional[float] = None
    small_worldness: Optional[float] = None
    degree_centrality: Optional[Dict[str, float]] = None
    betweenness_centrality: Optional[Dict[str, float]] = None
    
    # Additional metadata
    threshold_applied: Optional[float] = None
    n_nodes: Optional[int] = None
    n_edges: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'subject_id': self.subject_id,
            'time_point': self.time_point,
            'global_efficiency': self.global_efficiency,
            'local_efficiency': self.local_efficiency,
            'modularity': self.modularity,
            'clustering_coefficient': self.clustering_coefficient,
            'characteristic_path_length': self.characteristic_path_length,
            'small_worldness': self.small_worldness,
            'degree_centrality': self.degree_centrality,
            'betweenness_centrality': self.betweenness_centrality,
            'threshold_applied': self.threshold_applied,
            'n_nodes': self.n_nodes,
            'n_edges': self.n_edges
        }
    
    def save(self, path: Path) -> None:
        """Save graph metrics to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'GraphMetrics':
        """Load graph metrics from a JSON file."""
        path = Path(path)
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            subject_id=data['subject_id'],
            time_point=data['time_point'],
            global_efficiency=data['global_efficiency'],
            local_efficiency=data['local_efficiency'],
            modularity=data['modularity'],
            clustering_coefficient=data.get('clustering_coefficient'),
            characteristic_path_length=data.get('characteristic_path_length'),
            small_worldness=data.get('small_worldness'),
            degree_centrality=data.get('degree_centrality'),
            betweenness_centrality=data.get('betweenness_centrality'),
            threshold_applied=data.get('threshold_applied'),
            n_nodes=data.get('n_nodes'),
            n_edges=data.get('n_edges')
        )
    
    @property
    def summary(self) -> Dict[str, float]:
        """Return a summary of key metrics for quick inspection."""
        return {
            'global_efficiency': self.global_efficiency,
            'local_efficiency': self.local_efficiency,
            'modularity': self.modularity
        }