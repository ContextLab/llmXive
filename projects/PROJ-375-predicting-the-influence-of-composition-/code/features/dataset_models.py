from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from enum import Enum
import re
import math
import logging

logger = logging.getLogger(__name__)

class DataSource(str, Enum):
    """Enum for data sources."""
    MATERIALS_PROJECT = "Materials Project"
    AFLOW = "AFLOW"
    ZENODO = "Zenodo"

class AlloyFamily(str, Enum):
    """Enum for alloy families."""
    ZR = "Zr"
    PD = "Pd"
    FE = "Fe"
    MG = "Mg"
    TI = "Ti"
    OTHER = "Other"

class MetallicGlassEntry(BaseModel):
    """Pydantic model for a single metallic glass entry."""
    model_config = ConfigDict(strict=True, validate_assignment=True)

    composition: str = Field(..., description="Chemical formula (e.g., Zr50Cu40Al10)")
    cte: float = Field(..., ge=0, description="Coefficient of Thermal Expansion (1/K)")
    amorphous_flag: bool = Field(..., description="Is the material amorphous?")
    mean_atomic_radius: float = Field(..., ge=0, description="Weighted mean atomic radius (pm)")
    electronegativity_var: float = Field(..., ge=0, description="Electronegativity variance")
    vec: float = Field(..., ge=0, description="Valence Electron Concentration")
    size_mismatch: float = Field(..., ge=0, le=1, description="Atomic size mismatch parameter")
    source: Optional[DataSource] = Field(None, description="Data source")
    alloy_family: Optional[AlloyFamily] = Field(None, description="Alloy family classification")

    @field_validator('composition')
    @classmethod
    def validate_composition_format(cls, v: str) -> str:
        """Validate that composition follows standard chemical formula notation."""
        if not v:
            raise ValueError("Composition cannot be empty")
        # Basic regex for chemical formulas: Element followed by optional number
        pattern = r"^[A-Z][a-z]?[0-9]+([A-Z][a-z]?[0-9]+)*$"
        if not re.match(pattern, v):
            # Allow simpler cases like "Zr" if no numbers
            simple_pattern = r"^[A-Z][a-z]?([0-9]+)?$"
            if not re.match(simple_pattern, v):
                raise ValueError(f"Invalid composition format: {v}. Expected format like 'Zr50Cu40Al10'")
        return v

    @model_validator(mode='after')
    def check_consistency(self):
        """Perform cross-field validation."""
        if not self.amorphous_flag:
            logger.warning(f"Entry for {self.composition} has amorphous_flag=False. "
                         "This entry might be filtered out in downstream processing.")
        return self

def validate_entry_to_model(row_dict: Dict[str, Any]) -> Optional[MetallicGlassEntry]:
    """
    Validate a dictionary row against the MetallicGlassEntry model.
    
    Args:
        row_dict: Dictionary containing raw data fields.
        
    Returns:
        MetallicGlassEntry if valid, None if invalid (with warning logged).
    """
    try:
        # Ensure required fields exist
        required_fields = ['composition', 'cte', 'amorphous_flag', 
                         'mean_atomic_radius', 'electronegativity_var', 
                         'vec', 'size_mismatch']
        
        for field in required_fields:
            if field not in row_dict:
                raise ValueError(f"Missing required field: {field}")
        
        # Map string source to enum if present
        if 'source' in row_dict and row_dict['source']:
            try:
                row_dict['source'] = DataSource(row_dict['source'])
            except ValueError:
                logger.warning(f"Unknown source '{row_dict['source']}', defaulting to None")
                row_dict['source'] = None
        
        # Map string alloy_family to enum if present
        if 'alloy_family' in row_dict and row_dict['alloy_family']:
            try:
                row_dict['alloy_family'] = AlloyFamily(row_dict['alloy_family'])
            except ValueError:
                logger.warning(f"Unknown alloy family '{row_dict['alloy_family']}', defaulting to Other")
                row_dict['alloy_family'] = AlloyFamily.OTHER

        return MetallicGlassEntry(**row_dict)
        
    except Exception as e:
        logger.warning(f"Failed to validate entry: {e}. Data: {row_dict}")
        return None

def validate_dataframe_schema(df) -> bool:
    """
    Validate that a pandas DataFrame matches the required schema.
    
    Args:
        df: pandas DataFrame to validate.
        
    Returns:
        True if schema matches, False otherwise.
    """
    required_columns = [
        'composition', 'cte', 'amorphous_flag', 
        'mean_atomic_radius', 'electronegativity_var', 
        'vec', 'size_mismatch'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"DataFrame missing required columns: {missing}")
        return False
    
    # Check types
    type_checks = [
        ('composition', 'object'),
        ('cte', 'float64'),
        ('amorphous_flag', 'bool'),
        ('mean_atomic_radius', 'float64'),
        ('electronegativity_var', 'float64'),
        ('vec', 'float64'),
        ('size_mismatch', 'float64')
    ]
    
    for col, expected_type in type_checks:
        if str(df[col].dtype) != expected_type:
            logger.warning(f"Column {col} has type {df[col].dtype}, expected {expected_type}")
            # Try to cast
            try:
                if expected_type == 'bool':
                    df[col] = df[col].astype(bool)
                elif expected_type == 'object':
                    df[col] = df[col].astype(str)
                else:
                    df[col] = df[col].astype(float)
            except Exception as e:
                logger.error(f"Failed to cast column {col} to {expected_type}: {e}")
                return False
                
    return True