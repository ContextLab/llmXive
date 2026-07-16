"""
Data model for connectivity adjacency matrices.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix

from utils.logger import get_logger, ProcessingError

logger = get_logger(__name__)


@dataclass
class AdjacencyMatrix:
    """
    Container for a brain connectivity adjacency matrix and its metadata.

    Attributes:
        matrix: The connectivity matrix (numpy array or scipy sparse).
        node_ids: List of node identifiers (e.g., region names or indices).
        resolution: The parcellation resolution (e.g., 'aal90', 'schaefer200').
        subject_id: Identifier for the subject this matrix belongs to.
        symmetric: Boolean indicating if the matrix is symmetric.
        weighted: Boolean indicating if edge weights are continuous or binary.
        metadata: Additional arbitrary metadata.
    """
    matrix: np.ndarray
    node_ids: List[str]
    resolution: str
    subject_id: str
    symmetric: bool = True
    weighted: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize the matrix after initialization."""
        if not isinstance(self.matrix, (np.ndarray, sp.spmatrix)):
            raise ProcessingError(
                f"AdjacencyMatrix: 'matrix' must be numpy array or sparse matrix, got {type(self.matrix)}"
            )

        if len(self.node_ids) != self.matrix.shape[0]:
            raise ProcessingError(
                f"AdjacencyMatrix: 'node_ids' length ({len(self.node_ids)}) does not match matrix rows ({self.matrix.shape[0]})"
            )

        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ProcessingError(
                f"AdjacencyMatrix: Matrix must be square, got shape {self.matrix.shape}"
            )

        # Convert to dense if sparse for consistent handling, unless explicitly kept sparse
        # Note: For large matrices, keep as sparse. This check is for validation.
        if sp.issparse(self.matrix) and not isinstance(self.matrix, csr_matrix):
            self.matrix = csr_matrix(self.matrix)
            logger.debug(f"Converted matrix to CSR format for efficiency.")

    @property
    def n_nodes(self) -> int:
        """Return the number of nodes (dimensions of the matrix)."""
        return self.matrix.shape[0]

    @property
    def shape(self) -> tuple:
        """Return the shape of the matrix."""
        return self.matrix.shape

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a dictionary for JSON export."""
        # Handle sparse matrices by converting to COO format for serialization
        matrix_data = self.matrix
        if sp.issparse(matrix_data):
            matrix_data = {
                "data": matrix_data.data.tolist(),
                "indices": matrix_data.indices.tolist(),
                "indptr": matrix_data.indptr.tolist(),
                "shape": list(matrix_data.shape),
                "format": "csr"
            }
        else:
            matrix_data = matrix_data.tolist()

        return {
            "subject_id": self.subject_id,
            "resolution": self.resolution,
            "node_ids": self.node_ids,
            "matrix": matrix_data,
            "symmetric": self.symmetric,
            "weighted": self.weighted,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdjacencyMatrix":
        """Deserialize from a dictionary."""
        matrix_data = data["matrix"]
        if isinstance(matrix_data, dict):
            # Reconstruct sparse matrix
            mat = csr_matrix(
                (matrix_data["data"], matrix_data["indices"], matrix_data["indptr"]),
                shape=tuple(matrix_data["shape"])
            )
        else:
            mat = np.array(matrix_data)

        return cls(
            matrix=mat,
            node_ids=data["node_ids"],
            resolution=data["resolution"],
            subject_id=data["subject_id"],
            symmetric=data.get("symmetric", True),
            weighted=data.get("weighted", True),
            metadata=data.get("metadata", {})
        )
