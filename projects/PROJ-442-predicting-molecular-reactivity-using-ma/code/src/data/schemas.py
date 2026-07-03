from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from rdkit import Chem

class ReactionRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: Optional[str] = None
    reaction_smiles: str
    reactants_smiles: Optional[str] = None
    products_smiles: Optional[str] = None
    yield_pct: Optional[float] = None
    success_flag: Optional[bool] = None
    reaction_type: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class FeatureVector(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    reaction_id: str
    features: Dict[str, float]
    target: Optional[float] = None

class ModelResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model_name: str
    metrics: Dict[str, float]
    predictions_file: Optional[str] = None
    model_path: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
