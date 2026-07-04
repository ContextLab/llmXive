from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Dependency(BaseModel):
    """Data model for a single dependency node."""
    package_name: str
    name: str
    version: str
    last_release_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    vulnerability_count: int = 0
    age_in_days: Optional[int] = None
    # Raw data for debugging
    raw_data: Optional[Dict[str, Any]] = None

class Package(BaseModel):
    """Data model for a top-level NPM package."""
    name: str
    version: str
    downloads: int
    dependencies: List[Dependency] = []
    repository_url: Optional[str] = None
    last_commit_date: Optional[datetime] = None

class AnalysisResult(BaseModel):
    """Data model for the result of an analysis run."""
    total_packages: int
    total_dependencies: int
    unmaintained_count: int
    correlation_coefficient: Optional[float] = None
    p_value: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    data_version: Optional[str] = None
