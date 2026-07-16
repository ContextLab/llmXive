from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np
import json

@dataclass
class Molecule:
    """
    A data class to represent a molecule.
    """
    smiles: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureSet:
    """
    A data class to represent a set of features.
    """
    features_2d: np.ndarray
    features_3d: np.ndarray
    labels: np.ndarray

@dataclass
class ModelResult:
    """
    A data class to represent model results.
    """
    model_name: str
    metrics: Dict[str, float]
    predictions: np.ndarray
    errors: np.ndarray
