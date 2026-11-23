from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class SampleStage(Enum):
    """Enumeration of wetland establishment stages."""
    EARLY = "early"
    MATURE = "mature"
    TRANSITION = "transition"
    UNKNOWN = "unknown"


@dataclass
class Taxon:
    """
    Represents a taxonomic unit (OTU/ASV) in the feature table.
    
    Attributes:
        id: Unique identifier for the taxon (e.g., OTU ID or ASV sequence hash).
        abundance: The count/abundance of this taxon in a specific sample.
        metadata: Dictionary containing taxonomic classification (Kingdom, Phylum, etc.)
                  and other annotations.
    """
    id: str
    abundance: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.abundance < 0:
            raise ValueError(f"Taxon '{self.id}' abundance cannot be negative.")


@dataclass
class Sample:
    """
    Represents a biological sample with associated metadata.
    
    Attributes:
        id: Unique sample identifier.
        stage: The establishment stage of the wetland (Early, Mature, etc.).
        metadata: Dictionary containing environmental parameters (N/P removal rates,
                  pH, temperature, etc.).
        taxa: List of Taxon objects found in this sample.
    """
    id: str
    stage: SampleStage
    metadata: Dict[str, Any] = field(default_factory=dict)
    taxa: List[Taxon] = field(default_factory=list)

    def add_taxon(self, taxon: Taxon) -> None:
        """Add a taxon to the sample."""
        self.taxa.append(taxon)

    def get_total_reads(self) -> float:
        """Calculate total sequencing depth (sum of abundances)."""
        return sum(t.abundance for t in self.taxa)


@dataclass
class FeatureTable:
    """
    Container for a complete feature table (samples x taxa) and associated metadata.
    
    This class serves as the primary data structure for the analysis pipeline,
    aggregating samples and their taxonomic composition.
    
    Attributes:
        samples: List of Sample objects.
        taxon_ids: List of unique taxon IDs found across all samples.
        metadata: Global metadata about the feature table (source, processing date, etc.).
    """
    samples: List[Sample] = field(default_factory=list)
    taxon_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_sample(self, sample: Sample) -> None:
        """Add a sample to the table and update taxon index."""
        self.samples.append(sample)
        for taxon in sample.taxa:
            if taxon.id not in self.taxon_ids:
                self.taxon_ids.append(taxon.id)

    def get_taxon_abundance_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Returns a nested dictionary: {sample_id: {taxon_id: abundance}}.
        Useful for conversion to pandas DataFrames or numpy arrays.
        """
        matrix = {}
        for sample in self.samples:
            matrix[sample.id] = {}
            for taxon in sample.taxa:
                matrix[sample.id][taxon.id] = taxon.abundance
        return matrix

    def filter_samples_by_stage(self, stage: SampleStage) -> List[Sample]:
        """Return a list of samples matching the specified stage."""
        return [s for s in self.samples if s.stage == stage]

    def filter_samples_by_min_reads(self, min_reads: float) -> List[Sample]:
        """Return a list of samples with total reads >= min_reads."""
        return [s for s in self.samples if s.get_total_reads() >= min_reads]