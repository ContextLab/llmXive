"""
Base data models and entities for the plant secondary metabolite prediction pipeline.

This module defines the core data structures (Species, BGCFeature, MetaboliteProfile)
used throughout the pipeline for data alignment, feature extraction, and modeling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import json
from pathlib import Path

class BgcType(Enum):
    """Enumeration of known Biosynthetic Gene Cluster (BGC) types from antiSMASH."""
    POLYKETIDE = "polyketide"
    NON_RIBOSOMAL_PEPTIDE = "non-ribosomal peptide"
    TERPENE = "terpene"
    ALKALOID = "alkaloid"
    RIBOSOMALLY_SYNTHESIZED_AND_POST_TRANSLATIONALLY_MODIFIED_PEPTIDE = "ribozymal"
    SACCHARIDE = "saccharide"
    OTHER = "other"

    @classmethod
    def from_str(cls, value: str) -> "BgcType":
        """Convert string representation to BgcType enum."""
        value_lower = value.lower()
        for member in cls:
            if member.value.lower() == value_lower:
                return member
        return cls.OTHER

@dataclass
class Species:
    """
    Represents a plant species in the study.

    Attributes:
        taxon_id: NCBI Taxonomy ID.
        scientific_name: Binomial scientific name (e.g., 'Arabidopsis thaliana').
        common_name: Optional common name.
        genome_assembly_version: Version string of the genome assembly (e.g., 'GCF_000002625.1').
        assembly_level: Assembly level (e.g., 'Chromosome', 'Scaffold', 'Contig').
    """
    taxon_id: int
    scientific_name: str
    common_name: Optional[str] = None
    genome_assembly_version: Optional[str] = None
    assembly_level: Optional[str] = None

    def __hash__(self) -> int:
        return hash(self.taxon_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Species):
            return NotImplemented
        return self.taxon_id == other.taxon_id

    def to_dict(self) -> Dict:
        """Convert Species instance to a dictionary."""
        return {
            "taxon_id": self.taxon_id,
            "scientific_name": self.scientific_name,
            "common_name": self.common_name,
            "genome_assembly_version": self.genome_assembly_version,
            "assembly_level": self.assembly_level
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Species":
        """Create a Species instance from a dictionary."""
        return cls(
            taxon_id=data["taxon_id"],
            scientific_name=data["scientific_name"],
            common_name=data.get("common_name"),
            genome_assembly_version=data.get("genome_assembly_version"),
            assembly_level=data.get("assembly_level")
        )

@dataclass
class BGCFeature:
    """
    Represents a specific Biosynthetic Gene Cluster (BGC) feature detected in a species.

    Attributes:
        species: The Species instance this feature belongs to.
        bgc_id: Unique identifier for the BGC (e.g., from antiSMASH output).
        bgc_type: The type of BGC (e.g., polyketide, terpene).
        start_position: Start position on the genome assembly.
        end_position: End position on the genome assembly.
        confidence_score: Confidence score of the prediction (0.0 to 1.0).
        metadata: Additional metadata from the source (e.g., antiSMASH JSON).
    """
    species: Species
    bgc_id: str
    bgc_type: BgcType
    start_position: int
    end_position: int
    confidence_score: float
    metadata: Dict = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.species.taxon_id, self.bgc_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BGCFeature):
            return NotImplemented
        return (self.species.taxon_id == other.species.taxon_id and
                self.bgc_id == other.bgc_id)

    def to_dict(self) -> Dict:
        """Convert BGCFeature instance to a dictionary."""
        return {
            "species_taxon_id": self.species.taxon_id,
            "bgc_id": self.bgc_id,
            "bgc_type": self.bgc_type.value,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict, species_obj: Optional[Species] = None) -> "BGCFeature":
        """Create a BGCFeature instance from a dictionary."""
        if species_obj is None:
            # If species_obj is not provided, assume the data contains species info
            # This is a simplified reconstruction; in practice, species should be linked externally
            species_data = data.get("species")
            if isinstance(species_data, dict):
                species_obj = Species.from_dict(species_data)
            elif isinstance(species_data, Species):
                species_obj = species_data
            else:
                raise ValueError("Species information is required to construct BGCFeature")

        return cls(
            species=species_obj,
            bgc_id=data["bgc_id"],
            bgc_type=BgcType.from_str(data["bgc_type"]),
            start_position=data["start_position"],
            end_position=data["end_position"],
            confidence_score=data["confidence_score"],
            metadata=data.get("metadata", {})
        )

@dataclass
class MetaboliteProfile:
    """
    Represents the metabolite abundance profile for a species.

    Attributes:
        species: The Species instance this profile belongs to.
        metabolite_id: Unique identifier for the metabolite (e.g., InChIKey).
        compound_name: Common or systematic name of the compound.
        abundance: Measured abundance value (usually log-transformed).
        unit: Unit of measurement (e.g., 'log_intensity', 'ppm').
        detection_confidence: Confidence in detection (e.g., 'confirmed', 'probable').
    """
    species: Species
    metabolite_id: str
    compound_name: str
    abundance: float
    unit: str = "log_intensity"
    detection_confidence: str = "confirmed"

    def __hash__(self) -> int:
        return hash((self.species.taxon_id, self.metabolite_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MetaboliteProfile):
            return NotImplemented
        return (self.species.taxon_id == other.species.taxon_id and
                self.metabolite_id == other.metabolite_id)

    def to_dict(self) -> Dict:
        """Convert MetaboliteProfile instance to a dictionary."""
        return {
            "species_taxon_id": self.species.taxon_id,
            "metabolite_id": self.metabolite_id,
            "compound_name": self.compound_name,
            "abundance": self.abundance,
            "unit": self.unit,
            "detection_confidence": self.detection_confidence
        }

    @classmethod
    def from_dict(cls, data: Dict, species_obj: Optional[Species] = None) -> "MetaboliteProfile":
        """Create a MetaboliteProfile instance from a dictionary."""
        if species_obj is None:
            species_data = data.get("species")
            if isinstance(species_data, dict):
                species_obj = Species.from_dict(species_data)
            elif isinstance(species_data, Species):
                species_obj = species_data
            else:
                raise ValueError("Species information is required to construct MetaboliteProfile")

        return cls(
            species=species_obj,
            metabolite_id=data["metabolite_id"],
            compound_name=data["compound_name"],
            abundance=data["abundance"],
            unit=data.get("unit", "log_intensity"),
            detection_confidence=data.get("detection_confidence", "confirmed")
        )

@dataclass
class AlignedDataset:
    """
    Container for the fully aligned dataset ready for modeling.

    This aggregates Species, BGCFeature counts, and MetaboliteProfile abundances
    into a unified structure per species.

    Attributes:
        species_list: List of Species included in the dataset.
        bgc_counts: Dict mapping species taxon_id to a dict of BGC type counts.
        metabolite_abundances: Dict mapping species taxon_id to a dict of metabolite_id -> abundance.
        metadata: Global metadata about the dataset (e.g., source, date).
    """
    species_list: List[Species]
    bgc_counts: Dict[int, Dict[str, int]] = field(default_factory=dict)
    metabolite_abundances: Dict[int, Dict[str, float]] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def add_species(self, species: Species) -> None:
        """Add a species to the dataset."""
        if species not in self.species_list:
            self.species_list.append(species)
        if species.taxon_id not in self.bgc_counts:
            self.bgc_counts[species.taxon_id] = {}
        if species.taxon_id not in self.metabolite_abundances:
            self.metabolite_abundances[species.taxon_id] = {}

    def add_bgc_count(self, species: Species, bgc_type: str, count: int) -> None:
        """Add or update BGC count for a species."""
        self.add_species(species)
        self.bgc_counts[species.taxon_id][bgc_type] = count

    def add_metabolite_abundance(self, species: Species, metabolite_id: str, abundance: float) -> None:
        """Add or update metabolite abundance for a species."""
        self.add_species(species)
        self.metabolite_abundances[species.taxon_id][metabolite_id] = abundance

    def get_species_ids(self) -> Set[int]:
        """Get the set of all taxon_ids in the dataset."""
        return {s.taxon_id for s in self.species_list}

    def to_dict(self) -> Dict:
        """Convert AlignedDataset to a dictionary for serialization."""
        return {
            "species_list": [s.to_dict() for s in self.species_list],
            "bgc_counts": self.bgc_counts,
            "metabolite_abundances": self.metabolite_abundances,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AlignedDataset":
        """Create an AlignedDataset instance from a dictionary."""
        species_list = [Species.from_dict(s) for s in data.get("species_list", [])]
        return cls(
            species_list=species_list,
            bgc_counts=data.get("bgc_counts", {}),
            metabolite_abundances=data.get("metabolite_abundances", {}),
            metadata=data.get("metadata", {})
        )

    def save_to_json(self, filepath: str) -> None:
        """Save the dataset to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load_from_json(cls, filepath: str) -> "AlignedDataset":
        """Load an AlignedDataset from a JSON file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)