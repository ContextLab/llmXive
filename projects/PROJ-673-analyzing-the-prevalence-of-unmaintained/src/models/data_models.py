"""
Data models for the NPM dependency analysis project.
Defines Pydantic schemas for Package, Dependency, and AnalysisResult.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Union


class Package(BaseModel):
    """Model for an NPM package."""
    name: str = Field(..., description="Package name (e.g., 'lodash')")
    version: str = Field(..., description="Package version")
    description: Optional[str] = Field(None, description="Package description")
    homepage: Optional[str] = Field(None, description="Package homepage URL")
    repository_url: Optional[str] = Field(None, description="Repository URL (GitHub, etc.)")
    license: Optional[str] = Field(None, description="Package license")
    weekly_downloads: Optional[int] = Field(None, description="Weekly download count")
    last_published: Optional[datetime] = Field(None, description="Last publish date")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Package keywords")
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class Dependency(BaseModel):
    """Model for a dependency of a package."""
    name: str = Field(..., description="Dependency package name")
    version: str = Field(..., description="Dependency version")
    is_direct: bool = Field(..., description="Whether this is a direct dependency")
    # Release metadata
    last_release_date: Optional[datetime] = Field(None, description="Last release date from repository")
    last_commit_date: Optional[datetime] = Field(None, description="Last commit date from repository")
    # Age calculation
    age_in_days: Optional[float] = Field(None, description="Days since last release (calculated)")
    # Security metadata
    vulnerability_count: int = Field(0, description="Number of known vulnerabilities")
    # Source tracking
    source_package: Optional[str] = Field(None, description="Name of the package this dependency belongs to")
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class AnalysisResult(BaseModel):
    """Model for analysis results."""
    correlation_coefficient: float = Field(..., description="Spearman correlation coefficient")
    p_value: float = Field(..., description="P-value for the correlation")
    sample_size: int = Field(..., description="Number of samples used")
    significance_level: float = Field(0.05, description="Significance level for hypothesis testing")
    is_significant: bool = Field(..., description="Whether the correlation is statistically significant")
    # Additional analysis metadata
    analysis_date: datetime = Field(default_factory=datetime.now, description="Date of analysis")
    method: str = Field("spearman", description="Statistical method used")
    notes: Optional[str] = Field(None, description="Additional notes about the analysis")
    # Stratified results (optional)
    stratified_results: Optional[List[Dict[str, Any]]] = Field(None, description="Results stratified by category")
    # Sensitivity analysis (optional)
    sensitivity_results: Optional[Dict[str, Any]] = Field(None, description="Results from sensitivity analysis")
