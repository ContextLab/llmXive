from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np
import json

@dataclass
class Molecule:
    """
    Represents a single molecular entity with its identifiers and structural data.
    
    Attributes:
        mol_id: Unique identifier for the molecule (e.g., from QM9 dataset).
        smiles: Canonical SMILES string representation.
        formula: Molecular formula (e.g., "C5H12").
        atom_count: Total number of atoms in the molecule.
        heavy_atom_count: Number of non-hydrogen atoms.
        coordinates: Optional 3D coordinates array (N_atoms, 3).
        properties: Dictionary of calculated or experimental properties (e.g., dipole, HOMO, LUMO).
    """
    mol_id: str
    smiles: str
    formula: Optional[str] = None
    atom_count: int = 0
    heavy_atom_count: int = 0
    coordinates: Optional[np.ndarray] = None
    properties: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the molecule instance to a dictionary for serialization."""
        data = {
            "mol_id": self.mol_id,
            "smiles": self.smiles,
            "formula": self.formula,
            "atom_count": self.atom_count,
            "heavy_atom_count": self.heavy_atom_count,
            "properties": self.properties
        }
        if self.coordinates is not None:
            data["coordinates"] = self.coordinates.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Create a Molecule instance from a dictionary."""
        coords = None
        if "coordinates" in data and data["coordinates"] is not None:
            coords = np.array(data["coordinates"])
        return cls(
            mol_id=data["mol_id"],
            smiles=data["smiles"],
            formula=data.get("formula"),
            atom_count=data.get("atom_count", 0),
            heavy_atom_count=data.get("heavy_atom_count", 0),
            coordinates=coords,
            properties=data.get("properties", {})
        )

@dataclass
class FeatureSet:
    """
    Container for molecular features derived from a set of molecules.
    
    Attributes:
        feature_2d: 2D structural features (e.g., Morgan fingerprints). Shape: (n_samples, n_features_2d).
        feature_3d: 3D geometric features (e.g., distance bins, angles). Shape: (n_samples, n_features_3d).
        labels: Target values for the molecules. Shape: (n_samples,) or (n_samples, n_targets).
        molecule_ids: List of molecule identifiers corresponding to the rows in the feature arrays.
        metadata: Additional metadata about the feature extraction process (e.g., radius, nBits).
    """
    feature_2d: Optional[np.ndarray] = None
    feature_3d: Optional[np.ndarray] = None
    labels: Optional[np.ndarray] = None
    molecule_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate consistency of shapes if arrays are provided."""
        if self.feature_2d is not None:
            if len(self.molecule_ids) != self.feature_2d.shape[0]:
                raise ValueError(
                    f"Molecule count mismatch: {len(self.molecule_ids)} IDs vs "
                    f"{self.feature_2d.shape[0]} rows in feature_2d."
                )
        if self.feature_3d is not None:
            if len(self.molecule_ids) != self.feature_3d.shape[0]:
                raise ValueError(
                    f"Molecule count mismatch: {len(self.molecule_ids)} IDs vs "
                    f"{self.feature_3d.shape[0]} rows in feature_3d."
                )
        if self.labels is not None:
            expected_len = len(self.molecule_ids)
            if self.feature_2d is not None:
                expected_len = self.feature_2d.shape[0]
            if self.feature_3d is not None:
                expected_len = self.feature_3d.shape[0]
            
            if self.labels.ndim == 1:
                if len(self.labels) != expected_len:
                    raise ValueError(
                        f"Label count mismatch: {len(self.labels)} labels vs "
                        f"{expected_len} samples."
                    )
            else:
                if self.labels.shape[0] != expected_len:
                    raise ValueError(
                        f"Label row count mismatch: {self.labels.shape[0]} rows vs "
                        f"{expected_len} samples."
                    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the FeatureSet to a dictionary, handling numpy arrays."""
        data = {
            "molecule_ids": self.molecule_ids,
            "metadata": self.metadata
        }
        if self.feature_2d is not None:
            data["feature_2d"] = self.feature_2d.tolist()
        if self.feature_3d is not None:
            data["feature_3d"] = self.feature_3d.tolist()
        if self.labels is not None:
            data["labels"] = self.labels.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureSet":
        """Create a FeatureSet instance from a dictionary."""
        f2d = np.array(data["feature_2d"]) if "feature_2d" in data and data["feature_2d"] else None
        f3d = np.array(data["feature_3d"]) if "feature_3d" in data and data["feature_3d"] else None
        lbls = np.array(data["labels"]) if "labels" in data and data["labels"] else None
        
        return cls(
            feature_2d=f2d,
            feature_3d=f3d,
            labels=lbls,
            molecule_ids=data.get("molecule_ids", []),
            metadata=data.get("metadata", {})
        )
    
    def save_npz(self, path: str) -> None:
        """Save the feature set to an .npz file."""
        if self.feature_2d is None and self.feature_3d is None and self.labels is None:
            raise ValueError("Cannot save empty FeatureSet.")
        
        save_dict = {
            "molecule_ids": np.array(self.molecule_ids, dtype=object),
            "metadata": np.array([json.dumps(self.metadata)], dtype=object)
        }
        if self.feature_2d is not None:
            save_dict["feature_2d"] = self.feature_2d
        if self.feature_3d is not None:
            save_dict["feature_3d"] = self.feature_3d
        if self.labels is not None:
            save_dict["labels"] = self.labels
        
        np.savez(path, **save_dict)
    
    @classmethod
    def load_npz(cls, path: str) -> "FeatureSet":
        """Load a FeatureSet from an .npz file."""
        data = np.load(path, allow_pickle=True)
        
        molecule_ids = data["molecule_ids"].tolist()
        metadata = json.loads(str(data["metadata"][0]))
        
        f2d = data["feature_2d"] if "feature_2d" in data.files else None
        f3d = data["feature_3d"] if "feature_3d" in data.files else None
        lbls = data["labels"] if "labels" in data.files else None
        
        return cls(
            feature_2d=f2d,
            feature_3d=f3d,
            labels=lbls,
            molecule_ids=molecule_ids,
            metadata=metadata
        )

@dataclass
class ModelResult:
    """
    Container for the results of a model training and evaluation process.
    
    Attributes:
        model_type: String identifier of the model (e.g., "RandomForest", "SVR").
        feature_source: Source of features used ("2D", "3D", or "Hybrid").
        best_params: Dictionary of the best hyperparameters found during tuning.
        cv_metrics: Dictionary of cross-validation metrics (e.g., {"mean_mae": 0.5, "std_mae": 0.1}).
        fold_metrics: List of metric dictionaries, one per fold.
        test_metrics: Dictionary of metrics evaluated on the held-out test set.
        model_artifact_path: Path to the saved model pickle file.
        training_time_seconds: Total time spent training the model.
        timestamp: ISO format timestamp of when the result was recorded.
        raw_model: Optional reference to the actual model object (not saved to disk usually).
    """
    model_type: str
    feature_source: str
    best_params: Dict[str, Any] = field(default_factory=dict)
    cv_metrics: Dict[str, float] = field(default_factory=dict)
    fold_metrics: List[Dict[str, float]] = field(default_factory=list)
    test_metrics: Dict[str, float] = field(default_factory=dict)
    model_artifact_path: Optional[str] = None
    training_time_seconds: Optional[float] = None
    timestamp: Optional[str] = None
    raw_model: Any = None  # type: ignore
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary, excluding non-serializable raw model."""
        return {
            "model_type": self.model_type,
            "feature_source": self.feature_source,
            "best_params": self.best_params,
            "cv_metrics": self.cv_metrics,
            "fold_metrics": self.fold_metrics,
            "test_metrics": self.test_metrics,
            "model_artifact_path": self.model_artifact_path,
            "training_time_seconds": self.training_time_seconds,
            "timestamp": self.timestamp
        }
    
    def save_json(self, path: str) -> None:
        """Save the result metrics and metadata to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelResult":
        """Create a ModelResult instance from a dictionary."""
        return cls(
            model_type=data["model_type"],
            feature_source=data["feature_source"],
            best_params=data.get("best_params", {}),
            cv_metrics=data.get("cv_metrics", {}),
            fold_metrics=data.get("fold_metrics", []),
            test_metrics=data.get("test_metrics", {}),
            model_artifact_path=data.get("model_artifact_path"),
            training_time_seconds=data.get("training_time_seconds"),
            timestamp=data.get("timestamp")
        )