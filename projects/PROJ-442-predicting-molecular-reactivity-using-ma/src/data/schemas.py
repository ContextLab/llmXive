from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from rdkit import Chem

class ReactionRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    reactants: str
    products: str
    reaction_type: Optional[str] = None
    target: Optional[float] = None
    raw_record: Optional[Dict[str, Any]] = None

class FeatureVector(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    mol: Any  # RDKit Mol object
    features: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ModelResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    predictions: List[float]
    actuals: List[float]
    metrics: Dict[str, float]
    model_info: Dict[str, Any]