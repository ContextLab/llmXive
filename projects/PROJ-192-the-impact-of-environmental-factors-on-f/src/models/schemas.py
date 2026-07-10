"""
Pydantic models for the fungal community structure analysis pipeline.

Defines schemas for:
- ASV Table (sample_id, asv_id, count)
- Environmental Matrix (sample_id, pH, nutrients, etc.)
- Results (R2, p-value, p-value_adj)
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated
import re

class ASVTableRecord(BaseModel):
    """
    Schema for a single row in the ASV (Amplicon Sequence Variant) table.
    Represents the count of a specific ASV in a specific sample.
    """
    sample_id: str = Field(..., description="Unique identifier for the sample")
    asv_id: str = Field(..., description="Unique identifier for the Amplicon Sequence Variant")
    count: int = Field(..., ge=0, description="Read count for this ASV in this sample")

    @field_validator('sample_id', 'asv_id')
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("sample_id and asv_id must be non-empty strings")
        return v

class ASVTable(BaseModel):
    """
    Container for the full ASV table data.
    """
    records: List[ASVTableRecord] = Field(..., description="List of ASV count records")
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert to a list of dictionaries for pandas DataFrame creation."""
        return [r.model_dump() for r in self.records]

class EnvironmentalMatrixRecord(BaseModel):
    """
    Schema for a single row in the Environmental Matrix.
    Contains sample metadata and environmental variables.
    """
    sample_id: str = Field(..., description="Unique identifier for the sample")
    pH: Optional[float] = Field(None, ge=0, le=14, description="Soil pH level")
    nutrients: Optional[float] = Field(None, ge=0, description="Nutrient level (e.g., N, P, K aggregate or specific)")
    temperature: Optional[float] = Field(None, description="Mean annual temperature or soil temperature")
    moisture: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture percentage")
    biome: Optional[str] = Field(None, description="Biome classification (e.g., Forest, Grassland)")
    # Allow arbitrary extra fields for extensibility
    model_config = {"extra": "allow"}

    @field_validator('sample_id')
    @classmethod
    def validate_sample_id(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("sample_id must be non-empty string")
        return v

class EnvironmentalMatrix(BaseModel):
    """
    Container for the full Environmental Matrix data.
    """
    records: List[EnvironmentalMatrixRecord] = Field(..., description="List of environmental records")
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert to a list of dictionaries for pandas DataFrame creation."""
        return [r.model_dump() for r in self.records]

class PERMANOVAResult(BaseModel):
    """
    Schema for a single PERMANOVA test result row.
    """
    term: str = Field(..., description="The environmental variable or factor tested")
    R2: float = Field(..., ge=0, le=1, description="Coefficient of determination (explained variance)")
    p_value: float = Field(..., ge=0, le=1, description="Raw p-value from the permutation test")
    p_value_adj: float = Field(..., ge=0, le=1, description="Benjamini-Hochberg FDR adjusted p-value")
    
    @field_validator('term')
    @classmethod
    def validate_term(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("term must be a non-empty string")
        return v

class RDAVariancePartition(BaseModel):
    """
    Schema for variance partitioning results from db-RDA.
    """
    predictor: str = Field(..., description="Name of the predictor variable or group")
    unique_variance: float = Field(..., ge=0, le=1, description="Variance uniquely explained by this predictor")
    shared_variance: float = Field(..., ge=0, le=1, description="Variance shared with other predictors")
    total_variance: float = Field(..., ge=0, le=1, description="Total variance explained (unique + shared)")

class ResultsSummary(BaseModel):
    """
    Container for the full results summary.
    """
    permanova_results: List[PERMANOVAResult] = Field(default_factory=list, description="PERMANOVA test results")
    variance_partitioning: List[RDAVariancePartition] = Field(default_factory=list, description="Variance partitioning results")

# Type aliases for convenience in other modules
ASVTableSchema = ASVTable
EnvMatrixSchema = EnvironmentalMatrix
ResultsSchema = ResultsSummary