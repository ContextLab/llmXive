"""
Base data models for the evolutionary pressure on alternative splicing pipeline.

This module defines the core data structures used throughout the pipeline:
- RNASeqSample: Represents a single RNA-seq sample with metadata.
- SplicingEvent: Represents a detected splicing event (e.g., SE, A5SS, A3SS).
- EnrichmentResult: Stores results from statistical enrichment tests.
- PhylogeneticTree: Wraps Newick tree data and provides tree utilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import hashlib
import uuid

@dataclass
class RNASeqSample:
    """
    Represents a single RNA-seq sample.

    Attributes:
        sample_id: Unique identifier for the sample.
        species: Species name (e.g., 'Homo_sapiens', 'Pan_troglodytes').
        assembly: Genome assembly version (e.g., 'GRCh38', 'panTro6').
        sra_accession: SRA run accession (e.g., 'SRR123456').
        fastq_path: Path to the FASTQ file (local or remote).
        bam_path: Path to the aligned BAM file.
        replicates: List of sample IDs that are biological replicates.
        metadata: Additional arbitrary metadata.
        created_at: Timestamp of record creation.
    """
    sample_id: str
    species: str
    assembly: str
    sra_accession: str
    fastq_path: Optional[str] = None
    bam_path: Optional[str] = None
    replicates: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert sample to a dictionary for serialization."""
        return {
            "sample_id": self.sample_id,
            "species": self.species,
            "assembly": self.assembly,
            "sra_accession": self.sra_accession,
            "fastq_path": self.fastq_path,
            "bam_path": self.bam_path,
            "replicates": self.replicates,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RNASeqSample":
        """Create a sample from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            sample_id=data["sample_id"],
            species=data["species"],
            assembly=data["assembly"],
            sra_accession=data["sra_accession"],
            fastq_path=data.get("fastq_path"),
            bam_path=data.get("bam_path"),
            replicates=data.get("replicates", []),
            metadata=data.get("metadata", {}),
            created_at=created_at or datetime.utcnow(),
        )

    def __hash__(self) -> int:
        return hash(self.sample_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RNASeqSample):
            return NotImplemented
        return self.sample_id == other.sample_id

@dataclass
class SplicingEvent:
    """
    Represents a detected splicing event.

    Attributes:
        event_id: Unique identifier for the event.
        event_type: Type of event (e.g., 'SE', 'A5SS', 'A3SS', 'RI', 'MXE').
        gene_id: Gene identifier.
        gene_name: Gene symbol.
        chromosome: Chromosome name.
        start: Start coordinate (0-based).
        end: End coordinate (0-based).
        strand: Strand ('+' or '-').
        psi_values: Dictionary mapping sample_id to PSI value.
        delta_psi: Difference in PSI between conditions (if calculated).
        p_value: Statistical p-value (if calculated).
        fdr: False discovery rate (if calculated).
        is_lineage_specific: Flag indicating if this is a lineage-specific event.
        lineage: Lineage name if is_lineage_specific is True.
        placeholder: Flag indicating if this result is from synthetic/placeholder data.
        metadata: Additional arbitrary metadata.
    """
    event_id: str
    event_type: str
    gene_id: str
    gene_name: str
    chromosome: str
    start: int
    end: int
    strand: str
    psi_values: Dict[str, float] = field(default_factory=dict)
    delta_psi: Optional[float] = None
    p_value: Optional[float] = None
    fdr: Optional[float] = None
    is_lineage_specific: bool = False
    lineage: Optional[str] = None
    placeholder: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to a dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "gene_id": self.gene_id,
            "gene_name": self.gene_name,
            "chromosome": self.chromosome,
            "start": self.start,
            "end": self.end,
            "strand": self.strand,
            "psi_values": self.psi_values,
            "delta_psi": self.delta_psi,
            "p_value": self.p_value,
            "fdr": self.fdr,
            "is_lineage_specific": self.is_lineage_specific,
            "lineage": self.lineage,
            "placeholder": self.placeholder,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SplicingEvent":
        """Create an event from a dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            gene_id=data["gene_id"],
            gene_name=data["gene_name"],
            chromosome=data["chromosome"],
            start=data["start"],
            end=data["end"],
            strand=data["strand"],
            psi_values=data.get("psi_values", {}),
            delta_psi=data.get("delta_psi"),
            p_value=data.get("p_value"),
            fdr=data.get("fdr"),
            is_lineage_specific=data.get("is_lineage_specific", False),
            lineage=data.get("lineage"),
            placeholder=data.get("placeholder", False),
            metadata=data.get("metadata", {}),
        )

    def __hash__(self) -> int:
        return hash(self.event_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SplicingEvent):
            return NotImplemented
        return self.event_id == other.event_id

@dataclass
class EnrichmentResult:
    """
    Represents the result of an enrichment statistical test.

    Attributes:
        result_id: Unique identifier for the result.
        lineage: Lineage being tested.
        method: Statistical method used (e.g., 'phyloglm', 'permutation').
        predictor: Name of the predictor variable.
        response: Name of the response variable.
        coefficient: Regression coefficient.
        p_value: P-value from the test.
        fdr: FDR-corrected p-value.
        odds_ratio: Odds ratio (if applicable).
        n_events: Number of events in the test.
        n_controls: Number of control regions.
        permutation_p_value: P-value from permutation test (if applicable).
        accelerated_flag_enrichment: Enrichment of accelerated regions (if applicable).
        metadata: Additional arbitrary metadata.
    """
    result_id: str
    lineage: str
    method: str
    predictor: str
    response: str
    coefficient: Optional[float] = None
    p_value: Optional[float] = None
    fdr: Optional[float] = None
    odds_ratio: Optional[float] = None
    n_events: int = 0
    n_controls: int = 0
    permutation_p_value: Optional[float] = None
    accelerated_flag_enrichment: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary for serialization."""
        return {
            "result_id": self.result_id,
            "lineage": self.lineage,
            "method": self.method,
            "predictor": self.predictor,
            "response": self.response,
            "coefficient": self.coefficient,
            "p_value": self.p_value,
            "fdr": self.fdr,
            "odds_ratio": self.odds_ratio,
            "n_events": self.n_events,
            "n_controls": self.n_controls,
            "permutation_p_value": self.permutation_p_value,
            "accelerated_flag_enrichment": self.accelerated_flag_enrichment,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnrichmentResult":
        """Create a result from a dictionary."""
        return cls(
            result_id=data["result_id"],
            lineage=data["lineage"],
            method=data["method"],
            predictor=data["predictor"],
            response=data["response"],
            coefficient=data.get("coefficient"),
            p_value=data.get("p_value"),
            fdr=data.get("fdr"),
            odds_ratio=data.get("odds_ratio"),
            n_events=data.get("n_events", 0),
            n_controls=data.get("n_controls", 0),
            permutation_p_value=data.get("permutation_p_value"),
            accelerated_flag_enrichment=data.get("accelerated_flag_enrichment"),
            metadata=data.get("metadata", {}),
        )

    def __hash__(self) -> int:
        return hash(self.result_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EnrichmentResult):
            return NotImplemented
        return self.result_id == other.result_id

@dataclass
class PhylogeneticTree:
    """
    Wraps a phylogenetic tree in Newick format.

    Attributes:
        tree_id: Unique identifier for the tree.
        newick: Newick string representation of the tree.
        species: List of species/tips in the tree.
        root_name: Name of the root node.
        metadata: Additional arbitrary metadata.
    """
    tree_id: str
    newick: str
    species: List[str] = field(default_factory=list)
    root_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Parse species and root name from Newick if available."""
        if self.newick:
            # Simple extraction of tips (not robust for all Newick formats,
            # but sufficient for standard primate trees with labeled tips)
            # Remove newick punctuation and split
            import re
            clean_newick = re.sub(r'[;:{}()]+', ' ', self.newick)
            tips = clean_newick.split()
            # Filter out empty strings and numbers (branch lengths)
            self.species = [t for t in tips if t and not t.replace('.', '', 1).isdigit()]

            # Heuristic for root: first non-empty token after opening parenthesis
            # This is a simplification; a full parser would be better
            if self.species:
                # For a rooted tree, the last tip before the root is often the outgroup
                # We'll just set root_name to 'root' for now unless explicitly provided
                if not self.root_name:
                    self.root_name = "root"

    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to a dictionary for serialization."""
        return {
            "tree_id": self.tree_id,
            "newick": self.newick,
            "species": self.species,
            "root_name": self.root_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhylogeneticTree":
        """Create a tree from a dictionary."""
        return cls(
            tree_id=data["tree_id"],
            newick=data["newick"],
            species=data.get("species", []),
            root_name=data.get("root_name"),
            metadata=data.get("metadata", {}),
        )

    def save_to_file(self, path: Path) -> None:
        """Save the Newick string to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.newick)

    @classmethod
    def from_file(cls, path: Path, tree_id: Optional[str] = None) -> "PhylogeneticTree":
        """Load a tree from a Newick file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Tree file not found: {path}")

        with open(path, 'r') as f:
            newick = f.read().strip()

        if tree_id is None:
            tree_id = path.stem

        return cls(tree_id=tree_id, newick=newick)

    def __hash__(self) -> int:
        return hash(self.tree_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PhylogeneticTree):
            return NotImplemented
        return self.tree_id == other.tree_id
