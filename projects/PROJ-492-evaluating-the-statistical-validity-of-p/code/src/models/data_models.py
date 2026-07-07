"""
Data Models for A/B Test Audit Pipeline.
Defines Pydantic models for ABTestSummary and AuditRecord.
"""

from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field

class ABTestSummary(BaseModel):
    """
    Represents an extracted A/B test summary from a public source.
    """
    url: str
    domain: str
    year: Optional[int] = None
    reported_p_value: Optional[float] = None
    reported_effect_size: Optional[float] = None
    sample_size_a: Optional[float] = None
    sample_size_b: Optional[float] = None
    outcome_type: Optional[str] = None  # 'binary' or 'continuous'
    
    # Fields populated by the reconstructor (T023)
    reconstructed_p_value: Optional[float] = None
    reconstructed_effect_size: Optional[float] = None
    
    # Optional metadata
    notes: Optional[str] = None
    extraction_errors: Optional[List[str]] = None

    class Config:
        populate_by_name = True

class AuditRecord(BaseModel):
    """
    Represents the result of validating an A/B test summary.
    """
    url: str
    domain: str
    year: Optional[int] = None
    
    reported_p_value: Optional[float] = None
    reconstructed_p_value: Optional[float] = None
    reported_effect_size: Optional[float] = None
    reconstructed_effect_size: Optional[float] = None
    
    is_inconsistent: bool
    p_value_difference: Optional[float] = None
    effect_size_difference: Optional[float] = None
    
    data_quality_warning: Optional[List[str]] = None
    issues: Optional[List[str]] = None
    
    timestamp: str

    class Config:
        populate_by_name = True
