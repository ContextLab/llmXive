"""
Data models for Sample and Taxon entities.

These models align with the contracts/feature-table.schema.yaml specification
for microbial community analysis in constructed wetlands.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class SampleStage(Enum):
    """Enumeration of wetland establishment stages."""
    EARLY = "early"
    MIDDLE = "middle"
    LATE = "late"
    MATURE = "mature"
    UNKNOWN = "unknown"

@dataclass
class Sample:
    """
    Represents a single biological sample from a constructed wetland.
    
    Attributes:
        sample_id: Unique identifier for the sample (e.g., from SRA or Zenodo).
        dataset_id: The source dataset identifier.
        stage: The wetland establishment stage (early, middle, late, mature).
        read_depth: Total number of reads in the sample after filtering.
        metadata: Additional metadata fields (e.g., nutrient removal rates, location).
        raw_feature_counts: Dictionary mapping taxon IDs to raw read counts.
    """
    sample_id: str
    dataset_id: str
    stage: SampleStage
    read_depth: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_feature_counts: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sample":
        """
        Create a Sample instance from a dictionary.
        
        Args:
            data: Dictionary containing sample data.
                
        Returns:
            Sample instance.
        """
        stage_str = data.get("stage", "unknown").lower()
        try:
            stage = SampleStage(stage_str)
        except ValueError:
            stage = SampleStage.UNKNOWN
        
        return cls(
            sample_id=data["sample_id"],
            dataset_id=data["dataset_id"],
            stage=stage,
            read_depth=data.get("read_depth", 0),
            metadata=data.get("metadata", {}),
            raw_feature_counts=data.get("raw_feature_counts", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Sample instance to a dictionary.
        
        Returns:
            Dictionary representation of the sample.
        """
        return {
            "sample_id": self.sample_id,
            "dataset_id": self.dataset_id,
            "stage": self.stage.value,
            "read_depth": self.read_depth,
            "metadata": self.metadata,
            "raw_feature_counts": self.raw_feature_counts
        }

    def get_nutrient_removal_rate(self, nutrient: str = "N") -> Optional[float]:
        """
        Retrieve the nutrient removal rate for a specific nutrient.
        
        Args:
            nutrient: The nutrient type ('N' for Nitrogen, 'P' for Phosphorus).
                
        Returns:
            The removal rate if available, None otherwise.
        """
        return self.metadata.get(f"{nutrient}_removal_rate")

@dataclass
class Taxon:
    """
    Represents a taxonomic unit (OTU/ASV) in the feature table.
    
    Attributes:
        taxon_id: Unique identifier for the taxon.
        taxonomy: Taxonomic classification string (e.g., "k__Bacteria;p__Proteobacteria;...").
        abundance: Dictionary mapping sample IDs to read counts.
        total_abundance: Total reads across all samples.
    """
    taxon_id: str
    taxonomy: str = ""
    abundance: Dict[str, int] = field(default_factory=dict)
    total_abundance: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Taxon":
        """
        Create a Taxon instance from a dictionary.
        
        Args:
            data: Dictionary containing taxon data.
                
        Returns:
            Taxon instance.
        """
        return cls(
            taxon_id=data["taxon_id"],
            taxonomy=data.get("taxonomy", ""),
            abundance=data.get("abundance", {}),
            total_abundance=data.get("total_abundance", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Taxon instance to a dictionary.
        
        Returns:
            Dictionary representation of the taxon.
        """
        return {
            "taxon_id": self.taxon_id,
            "taxonomy": self.taxonomy,
            "abundance": self.abundance,
            "total_abundance": self.total_abundance
        }

    def get_abundance_in_sample(self, sample_id: str) -> int:
        """
        Get the abundance of this taxon in a specific sample.
        
        Args:
            sample_id: The sample identifier.
                
        Returns:
            The read count, or 0 if not present.
        """
        return self.abundance.get(sample_id, 0)

    def relative_abundance_in_sample(self, sample_id: str, sample_depth: int) -> float:
        """
        Calculate relative abundance in a specific sample.
        
        Args:
            sample_id: The sample identifier.
            sample_depth: Total reads in the sample.
                
        Returns:
            Relative abundance (0.0 to 1.0), or 0.0 if depth is 0.
        """
        if sample_depth == 0:
            return 0.0
        return self.get_abundance_in_sample(sample_id) / sample_depth

@dataclass
class FeatureTable:
    """
    Container for a feature table (Sample x Taxon matrix).
    
    Attributes:
        samples: List of Sample objects.
        taxa: List of Taxon objects.
        metadata: Global metadata for the table.
    """
    samples: List[Sample] = field(default_factory=list)
    taxa: List[Taxon] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert FeatureTable to a dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "samples": [s.to_dict() for s in self.samples],
            "taxa": [t.to_dict() for t in self.taxa],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureTable":
        """
        Create a FeatureTable from a dictionary.
        
        Args:
            data: Dictionary containing feature table data.
                
        Returns:
            FeatureTable instance.
        """
        samples = [Sample.from_dict(s) for s in data.get("samples", [])]
        taxa = [Taxon.from_dict(t) for t in data.get("taxa", [])]
        return cls(
            samples=samples,
            taxa=taxa,
            metadata=data.get("metadata", {})
        )

    def get_sample(self, sample_id: str) -> Optional[Sample]:
        """Retrieve a sample by ID."""
        for s in self.samples:
            if s.sample_id == sample_id:
                return s
        return None

    def get_taxon(self, taxon_id: str) -> Optional[Taxon]:
        """Retrieve a taxon by ID."""
        for t in self.taxa:
            if t.taxon_id == taxon_id:
                return t
        return None
