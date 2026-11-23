from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import hashlib

@dataclass(frozen=True)
class PhylogeneticTree:
    """
    Represents a phylogenetic tree used for evolutionary analysis.
    
    Attributes:
        tree_file_path: Path to the Newick tree file (.nwk).
        source: Description of the tree source (e.g., 'UCSC', 'custom', 'Ensembl').
        topology_hash: SHA-256 hash of the tree file contents to ensure topology integrity.
    """
    tree_file_path: str
    source: str
    topology_hash: Optional[str] = None

    def __post_init__(self):
        """
        Validates the tree file exists and computes its hash if not provided.
        Raises FileNotFoundError if the tree file is missing.
        Raises ValueError if the file is a directory.
        """
        path = Path(self.tree_file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Phylogenetic tree file not found: {self.tree_file_path}")
        
        if path.is_dir():
            raise ValueError(f"Phylogenetic tree path must be a file, not a directory: {self.tree_file_path}")
        
        # Compute hash if not explicitly provided (e.g., during reconstruction from dict)
        object.__setattr__(self, 'topology_hash', self._compute_hash(path))

    def _compute_hash(self, path: Path) -> str:
        """Computes SHA-256 hash of the file contents."""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def to_dict(self) -> dict:
        """Converts the instance to a dictionary for serialization."""
        return {
            "tree_file_path": self.tree_file_path,
            "source": self.source,
            "topology_hash": self.topology_hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PhylogeneticTree':
        """Creates an instance from a dictionary."""
        return cls(
            tree_file_path=data["tree_file_path"],
            source=data["source"],
            topology_hash=data.get("topology_hash")
        )
