from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json
from pathlib import Path


@dataclass
class Subject:
    """
    Represents a single study participant.
    
    Attributes:
        subject_id: Unique identifier for the subject (e.g., 'sub-001').
        group: Group assignment (e.g., 'control', 'mTBI').
        age: Age in years.
        sex: Biological sex (e.g., 'M', 'F').
        time_points: List of time point identifiers (e.g., ['acute', 'chronic']).
        cognitive_scores: Dictionary mapping time points to cognitive scores.
        metadata: Additional arbitrary metadata.
    """
    subject_id: str
    group: str
    age: Optional[float] = None
    sex: Optional[str] = None
    time_points: List[str] = field(default_factory=list)
    cognitive_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_time_point(self, tp: str) -> None:
        """Add a time point if not already present."""
        if tp not in self.time_points:
            self.time_points.append(tp)

    def add_cognitive_score(self, time_point: str, score: float) -> None:
        """Associate a cognitive score with a specific time point."""
        self.cognitive_scores[time_point] = score

    def to_dict(self) -> Dict[str, Any]:
        """Convert the subject to a dictionary for serialization."""
        return {
            "subject_id": self.subject_id,
            "group": self.group,
            "age": self.age,
            "sex": self.sex,
            "time_points": self.time_points,
            "cognitive_scores": self.cognitive_scores,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subject':
        """Create a Subject instance from a dictionary."""
        return cls(
            subject_id=data["subject_id"],
            group=data["group"],
            age=data.get("age"),
            sex=data.get("sex"),
            time_points=data.get("time_points", []),
            cognitive_scores=data.get("cognitive_scores", {}),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a subject at a specific time point.
    
    Attributes:
        subject_id: ID of the subject.
        time_point: The time point (e.g., 'acute', 'chronic').
        matrix_data: The 2D numpy array containing correlation values.
        node_labels: List of labels corresponding to rows/columns (e.g., AAL regions).
        atlas: Name of the atlas used (e.g., 'AAL').
        path: Optional path to the saved file on disk.
    """
    subject_id: str
    time_point: str
    matrix_data: np.ndarray
    node_labels: List[str]
    atlas: str = "AAL"
    path: Optional[Path] = None

    def __post_init__(self):
        """Validate matrix dimensions and consistency."""
        if not isinstance(self.matrix_data, np.ndarray):
            raise TypeError("matrix_data must be a numpy ndarray")
        
        if self.matrix_data.ndim != 2:
            raise ValueError("matrix_data must be 2-dimensional")
        
        if self.matrix_data.shape[0] != self.matrix_data.shape[1]:
            raise ValueError("matrix_data must be square")
        
        if len(self.node_labels) != self.matrix_data.shape[0]:
            raise ValueError("Number of node_labels must match matrix dimensions")

    @property
    def shape(self) -> tuple:
        """Return the shape of the matrix."""
        return self.matrix_data.shape

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes."""
        return self.matrix_data.shape[0]

    def save(self, output_path: Path) -> None:
        """
        Save the connectivity matrix and metadata to a JSON file.
        Note: NumPy arrays are converted to lists for JSON serialization.
        """
        data = {
            "subject_id": self.subject_id,
            "time_point": self.time_point,
            "atlas": self.atlas,
            "node_labels": self.node_labels,
            "matrix_data": self.matrix_data.tolist()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.path = output_path

    @classmethod
    def load(cls, file_path: Path) -> 'ConnectivityMatrix':
        """
        Load a connectivity matrix from a JSON file.
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        matrix_array = np.array(data["matrix_data"])
        
        return cls(
            subject_id=data["subject_id"],
            time_point=data["time_point"],
            matrix_data=matrix_array,
            node_labels=data["node_labels"],
            atlas=data.get("atlas", "AAL"),
            path=file_path
        )

    def get_submatrix(self, indices: List[int]) -> 'ConnectivityMatrix':
        """
        Extract a submatrix based on a list of node indices.
        """
        sub_matrix = self.matrix_data[np.ix_(indices, indices)]
        sub_labels = [self.node_labels[i] for i in indices]
        
        return ConnectivityMatrix(
            subject_id=self.subject_id,
            time_point=self.time_point,
            matrix_data=sub_matrix,
            node_labels=sub_labels,
            atlas=self.atlas
        )


@dataclass
class GraphMetrics:
    """
    Stores computed graph theory metrics for a connectivity matrix.
    
    Attributes:
        subject_id: ID of the subject.
        time_point: The time point.
        global_efficiency: Global efficiency of the network.
        local_efficiency: Local efficiency of the network.
        modularity: Modularity (Q) of the network.
        clustering_coefficient: Average clustering coefficient.
        characteristic_path_length: Average shortest path length.
        metadata: Additional metrics or parameters used (e.g., threshold value).
    """
    subject_id: str
    time_point: str
    global_efficiency: Optional[float] = None
    local_efficiency: Optional[float] = None
    modularity: Optional[float] = None
    clustering_coefficient: Optional[float] = None
    characteristic_path_length: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary."""
        return {
            "subject_id": self.subject_id,
            "time_point": self.time_point,
            "global_efficiency": self.global_efficiency,
            "local_efficiency": self.local_efficiency,
            "modularity": self.modularity,
            "clustering_coefficient": self.clustering_coefficient,
            "characteristic_path_length": self.characteristic_path_length,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphMetrics':
        """Create a GraphMetrics instance from a dictionary."""
        return cls(
            subject_id=data["subject_id"],
            time_point=data["time_point"],
            global_efficiency=data.get("global_efficiency"),
            local_efficiency=data.get("local_efficiency"),
            modularity=data.get("modularity"),
            clustering_coefficient=data.get("clustering_coefficient"),
            characteristic_path_length=data.get("characteristic_path_length"),
            metadata=data.get("metadata", {})
        )

    def save(self, output_path: Path) -> None:
        """Save metrics to a JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> 'GraphMetrics':
        """Load metrics from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def update(self, **kwargs) -> None:
        """Update specific metric fields dynamically."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.metadata[key] = value