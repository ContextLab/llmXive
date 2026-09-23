from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Dependency(BaseModel):
    """
    Represents a single dependency of a package.
    Includes metadata about maintenance status and security.
    """
    name: str = Field(..., description="Name of the dependency")
    version: str = Field(..., description="Version string of the dependency")
    
    # Maintenance metadata (can be null)
    last_release_date: Optional[datetime] = Field(None, description="Date of last release")
    last_commit_date: Optional[datetime] = Field(None, description="Date of last commit")
    
    # Calculated age in days (can be null if dates are missing)
    age_in_days: Optional[float] = Field(None, description="Days since last release")
    
    # Security metadata
    vulnerability_count: int = Field(0, description="Number of known vulnerabilities")
    
    # Source identification
    is_direct: bool = Field(True, description="Whether this is a direct dependency")
    
    @field_validator('age_in_days')
    @classmethod
    def validate_age(cls, v, info):
        # If v is None, it's valid (means data is missing)
        if v is None:
            return v
        if v < 0:
            raise ValueError('age_in_days cannot be negative')
        return v

class Package(BaseModel):
    """
    Represents a top-level NPM package being analyzed.
    Contains its direct and transitive dependencies.
    """
    name: str = Field(..., description="Name of the package")
    version: str = Field(..., description="Version of the package")
    repository_url: Optional[str] = Field(None, description="GitHub repository URL")
    
    # Dependencies list
    dependencies: List[Dependency] = Field(default_factory=list, description="List of dependencies")
    
    # Aggregated metrics
    total_dependency_count: int = Field(0, description="Total number of dependencies")
    unmaintained_count: int = Field(0, description="Count of dependencies with age > threshold")
    
    @field_validator('total_dependency_count')
    @classmethod
    def validate_count(cls, v, info):
        # This will be set manually by the pipeline, but we ensure it's non-negative
        if v < 0:
            raise ValueError('total_dependency_count cannot be negative')
        return v

class AnalysisResult(BaseModel):
    """
    Represents the result of a statistical analysis run.
    """
    analysis_id: str = Field(..., description="Unique identifier for this analysis run")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="When the analysis was run")
    
    # Correlation results
    spearman_correlation: Optional[float] = Field(None, description="Spearman correlation coefficient")
    p_value: Optional[float] = Field(None, description="P-value for the correlation")
    sample_size: Optional[int] = Field(None, description="Number of samples used")
    
    # Stratified results
    stratified_results: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, 
        description="Correlation results per category"
    )
    
    # Data quality metrics
    missing_release_metadata_ratio: float = Field(0.0, description="Ratio of missing release dates")
    total_dependencies_analyzed: int = Field(0, description="Total dependencies processed")
    
    # Power analysis
    statistical_power: Optional[float] = Field(None, description="Calculated statistical power")
    effect_size: Optional[float] = Field(None, description="Effect size used in power analysis")
    
    # File paths to generated artifacts
    output_files: List[str] = Field(default_factory=list, description="Paths to generated output files")