"""
Core data models and entities for the solubility prediction pipeline.
Defines Molecule, DatasetSplit, and Dataset dataclasses.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np
import json


@dataclass
class Molecule:
    """
    Represents a single molecule with its graph structure and properties.
    
    Attributes:
        smiles: The SMILES string representation of the molecule.
        logS: The experimental solubility value (logS).
        atom_features: List of feature vectors for each atom.
        bond_features: List of feature vectors for each bond.
        atom_indices: List of atom indices (0 to N-1).
        bond_indices: List of tuples (source_idx, target_idx, bond_type).
        metadata: Optional dictionary for additional molecule information.
    """
    smiles: str
    logS: Optional[float] = None
    atom_features: List[List[float]] = field(default_factory=list)
    bond_features: List[List[float]] = field(default_factory=list)
    atom_indices: List[int] = field(default_factory=list)
    bond_indices: List[tuple] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the molecule to a dictionary for serialization."""
        return {
            "smiles": self.smiles,
            "logS": self.logS,
            "atom_features": self.atom_features,
            "bond_features": self.bond_features,
            "atom_indices": self.atom_indices,
            "bond_indices": self.bond_indices,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Create a Molecule instance from a dictionary."""
        return cls(
            smiles=data["smiles"],
            logS=data.get("logS"),
            atom_features=data.get("atom_features", []),
            bond_features=data.get("bond_features", []),
            atom_indices=data.get("atom_indices", []),
            bond_indices=[tuple(b) if isinstance(b, list) else b for b in data.get("bond_indices", [])],
            metadata=data.get("metadata", {})
        )

    def __post_init__(self):
        """Validate the molecule data after initialization."""
        if not self.smiles:
            raise ValueError("SMILES string cannot be empty")
        if self.atom_indices and not self.atom_features:
            raise ValueError("Atom features must be provided if atom indices exist")
        if self.bond_indices and not self.bond_features:
            raise ValueError("Bond features must be provided if bond indices exist")


@dataclass
class DatasetSplit:
    """
    Represents a split of the dataset (train, validation, or test).
    
    Attributes:
        name: Name of the split (e.g., 'train', 'validation', 'test').
        indices: List of indices corresponding to molecules in this split.
        molecules: List of Molecule objects in this split.
        statistics: Dictionary containing split statistics (count, mean logS, std logS).
    """
    name: str
    indices: List[int] = field(default_factory=list)
    molecules: List[Molecule] = field(default_factory=list)
    statistics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate statistics if molecules are provided."""
        if self.molecules:
            self._calculate_statistics()

    def _calculate_statistics(self):
        """Calculate and store statistics for the split."""
        if not self.molecules:
            self.statistics = {
                "count": 0,
                "mean_logS": None,
                "std_logS": None,
                "min_logS": None,
                "max_logS": None
            }
            return

        logS_values = [m.logS for m in self.molecules if m.logS is not None]
        
        if logS_values:
            self.statistics = {
                "count": len(self.molecules),
                "mean_logS": float(np.mean(logS_values)),
                "std_logS": float(np.std(logS_values)),
                "min_logS": float(np.min(logS_values)),
                "max_logS": float(np.max(logS_values))
            }
        else:
            self.statistics = {
                "count": len(self.molecules),
                "mean_logS": None,
                "std_logS": None,
                "min_logS": None,
                "max_logS": None
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataset split to a dictionary for serialization."""
        return {
            "name": self.name,
            "indices": self.indices,
            "molecules": [m.to_dict() for m in self.molecules],
            "statistics": self.statistics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetSplit":
        """Create a DatasetSplit instance from a dictionary."""
        molecules = [Molecule.from_dict(m) for m in data.get("molecules", [])]
        return cls(
            name=data["name"],
            indices=data.get("indices", []),
            molecules=molecules,
            statistics=data.get("statistics", {})
        )

    def add_molecule(self, molecule: Molecule) -> None:
        """Add a molecule to this split."""
        self.molecules.append(molecule)
        if molecule.smiles not in self.metadata.get("smiles_seen", []):
            self.metadata.setdefault("smiles_seen", []).append(molecule.smiles)
        self._calculate_statistics()

    def get_molecule_by_index(self, idx: int) -> Optional[Molecule]:
        """Get a molecule by its index in the split."""
        if 0 <= idx < len(self.molecules):
            return self.molecules[idx]
        return None


@dataclass
class Dataset:
    """
    Represents the complete dataset with all splits.
    
    Attributes:
        name: Name of the dataset.
        train_split: The training split.
        validation_split: The validation split.
        test_split: The test split.
        full_molecules: List of all molecules in the dataset.
    """
    name: str
    train_split: Optional[DatasetSplit] = None
    validation_split: Optional[DatasetSplit] = None
    test_split: Optional[DatasetSplit] = None
    full_molecules: List[Molecule] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataset to a dictionary for serialization."""
        return {
            "name": self.name,
            "train_split": self.train_split.to_dict() if self.train_split else None,
            "validation_split": self.validation_split.to_dict() if self.validation_split else None,
            "test_split": self.test_split.to_dict() if self.test_split else None,
            "full_molecules": [m.to_dict() for m in self.full_molecules]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dataset":
        """Create a Dataset instance from a dictionary."""
        return cls(
            name=data["name"],
            train_split=DatasetSplit.from_dict(data["train_split"]) if data.get("train_split") else None,
            validation_split=DatasetSplit.from_dict(data["validation_split"]) if data.get("validation_split") else None,
            test_split=DatasetSplit.from_dict(data["test_split"]) if data.get("test_split") else None,
            full_molecules=[Molecule.from_dict(m) for m in data.get("full_molecules", [])]
        )

    def add_molecule_to_split(self, molecule: Molecule, split_name: str) -> None:
        """Add a molecule to the specified split."""
        split = getattr(self, f"{split_name}_split")
        if split:
            split.add_molecule(molecule)
        else:
            raise ValueError(f"Split '{split_name}' does not exist in this dataset")

    def get_split(self, split_name: str) -> Optional[DatasetSplit]:
        """Get a split by name."""
        return getattr(self, f"{split_name}_split", None)

    def get_all_molecules(self) -> List[Molecule]:
        """Get all molecules from all splits."""
        all_molecules = []
        if self.train_split:
            all_molecules.extend(self.train_split.molecules)
        if self.validation_split:
            all_molecules.extend(self.validation_split.molecules)
        if self.test_split:
            all_molecules.extend(self.test_split.molecules)
        return all_molecules

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all splits."""
        stats = {}
        if self.train_split:
            stats["train"] = self.train_split.statistics
        if self.validation_split:
            stats["validation"] = self.validation_split.statistics
        if self.test_split:
            stats["test"] = self.test_split.statistics
        return stats
