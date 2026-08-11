from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import re

@dataclass
class Sample:
    """
    Represents a single sampling event from a hydrothermal vent site.
    Maps to the 'sample' entity in the data model.
    """
    sample_id: str
    timestamp: datetime
    pH: float
    temperature: float
    location: str
    deployment_event: str
    sensor_id: str
    coordinates: str  # e.g., "lat,lon"
    fastq_path: Optional[str] = None
    pH_sd: float = 0.0  # Heterogeneity metric calculated in window
    pH_heterogeneous: bool = False
    
    def validate(self) -> List[str]:
        errors = []
        if not self.sample_id:
            errors.append("sample_id is required")
        if self.pH < 0 or self.pH > 14:
            errors.append(f"pH {self.pH} out of valid range [0, 14]")
        if not self.coordinates:
            errors.append("coordinates are required")
        return errors

@dataclass
class OTU:
    """
    Represents an Operational Taxonomic Unit (or ASV) count for a sample.
    Maps to the 'otu_table' entity.
    """
    sample_id: str
    otu_id: str
    count: int
    taxonomy: Optional[List[str]] = None  # Kingdom, Phylum, Class, Order, Family, Genus, Species

    def validate(self) -> List[str]:
        errors = []
        if self.count < 0:
            errors.append(f"Count cannot be negative: {self.count}")
        if not self.otu_id:
            errors.append("otu_id is required")
        return errors

@dataclass
class DiversityMetric:
    """
    Represents calculated alpha or beta diversity metrics for a sample.
    Maps to the 'diversity_metric' entity.
    """
    sample_id: str
    metric_name: str  # e.g., 'shannon', 'simpson', 'bray_curtis'
    value: float
    rarefaction_depth: Optional[int] = None
    model_type: Optional[str] = None  # For regression results (e.g., 'LME', 'Spearman')
    estimate: Optional[float] = None
    se: Optional[float] = None
    p_value: Optional[float] = None

    def validate(self) -> List[str]:
        errors = []
        if self.value < 0:
            errors.append(f"Metric value cannot be negative: {self.value}")
        return errors

def validate_sample_schema(data: Dict[str, Any]) -> bool:
    """Validates a dictionary against the Sample schema constraints."""
    required = ['sample_id', 'timestamp', 'pH', 'temperature', 'location', 'deployment_event', 'sensor_id', 'coordinates']
    for key in required:
        if key not in data:
            return False
    return True

def validate_otu_schema(data: Dict[str, Any]) -> bool:
    """Validates a dictionary against the OTU table schema constraints."""
    required = ['sample_id', 'otu_id', 'count']
    for key in required:
        if key not in data:
            return False
    return True

def validate_diversity_metric_schema(data: Dict[str, Any]) -> bool:
    """Validates a dictionary against the Diversity Metric schema constraints."""
    required = ['sample_id', 'metric_name', 'value']
    for key in required:
        if key not in data:
            return False
    return True
