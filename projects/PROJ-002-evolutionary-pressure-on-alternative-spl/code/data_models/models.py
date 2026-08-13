"""
Core data models for the evolutionary pressure pipeline.

These classes provide structured data containers with validation, serialization,
and type hints for the main entities in the splicing analysis workflow.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import hashlib
import pandas as pd
import numpy as np

@dataclass
class RNASeqSample:
    """
    Represents a single RNA-seq sample with associated metadata.
    
    Attributes:
        sample_id: Unique identifier for the sample
        species: Species name (e.g., 'Homo_sapiens', 'Pan_troglodytes')
        assembly: Genome assembly version (e.g., 'GRCh38', 'panTro6')
        fastq_path: Path to the FASTQ file
        bam_path: Path to the aligned BAM file (after alignment)
        sra_accession: Original SRA accession number
        replicate_index: Index within the replicate set (1-based)
        total_reads: Total number of reads (populated after QC)
        mapped_reads: Number of mapped reads (populated after alignment)
        mapping_rate: Fraction of reads mapped (populated after alignment)
        created_at: Timestamp of record creation
        metadata: Additional free-form metadata dictionary
    """
    sample_id: str
    species: str
    assembly: str
    fastq_path: Optional[str] = None
    bam_path: Optional[str] = None
    sra_accession: Optional[str] = None
    replicate_index: int = 1
    total_reads: Optional[int] = None
    mapped_reads: Optional[int] = None
    mapping_rate: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sample to dictionary representation."""
        return {
            'sample_id': self.sample_id,
            'species': self.species,
            'assembly': self.assembly,
            'fastq_path': self.fastq_path,
            'bam_path': self.bam_path,
            'sra_accession': self.sra_accession,
            'replicate_index': self.replicate_index,
            'total_reads': self.total_reads,
            'mapped_reads': self.mapped_reads,
            'mapping_rate': self.mapping_rate,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RNASeqSample':
        """Create RNASeqSample from dictionary."""
        # Handle datetime deserialization
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize sample to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RNASeqSample':
        """Deserialize sample from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def validate(self) -> bool:
        """Validate sample data integrity."""
        if not self.sample_id:
            return False
        if not self.species:
            return False
        if not self.assembly:
            return False
        if self.replicate_index < 1:
            return False
        return True
    
    def get_file_hash(self) -> Optional[str]:
        """Calculate SHA-256 hash of the primary data file (BAM if exists, else FASTQ)."""
        file_path = self.bam_path or self.fastq_path
        if not file_path or not Path(file_path).exists():
            return None
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

@dataclass
class SplicingEvent:
    """
    Represents a detected alternative splicing event.
    
    Attributes:
        event_id: Unique identifier for the splicing event
        event_type: Type of splicing event (e.g., 'SE', 'A5SS', 'A3SS', 'RI', 'MXE')
        gene_id: Ensembl or gene identifier
        gene_name: Gene symbol
        chromosome: Chromosome name
        start: Genomic start position (1-based)
        end: Genomic end position
        strand: Strand orientation ('+', '-', or '.')
        psi_values: Dictionary mapping sample_id to PSI value (0.0-1.0)
        delta_psi: Difference in PSI between groups (computed)
        p_value: Statistical p-value for differential splicing
        fdr: False discovery rate adjusted p-value
        is_lineage_specific: Boolean flag for lineage-specific event
        lineage: Lineage name if lineage-specific (e.g., 'human', 'chimp')
        flanking_sequence: Optional flanking sequence data
        phylop_score: Optional phyloP conservation score
        is_accelerated: Boolean flag for accelerated evolution
        placeholder: Boolean flag indicating synthetic/placeholder data
        metadata: Additional metadata dictionary
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
    flanking_sequence: Optional[str] = None
    phylop_score: Optional[float] = None
    is_accelerated: bool = False
    placeholder: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'gene_id': self.gene_id,
            'gene_name': self.gene_name,
            'chromosome': self.chromosome,
            'start': self.start,
            'end': self.end,
            'strand': self.strand,
            'psi_values': self.psi_values,
            'delta_psi': self.delta_psi,
            'p_value': self.p_value,
            'fdr': self.fdr,
            'is_lineage_specific': self.is_lineage_specific,
            'lineage': self.lineage,
            'flanking_sequence': self.flanking_sequence,
            'phylop_score': self.phylop_score,
            'is_accelerated': self.is_accelerated,
            'placeholder': self.placeholder,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplicingEvent':
        """Create SplicingEvent from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SplicingEvent':
        """Deserialize event from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def to_bed(self) -> str:
        """Convert to BED6 format string."""
        # BED is 0-based, start is 1-based in our model
        return f"{self.chromosome}\t{self.start - 1}\t{self.end}\t{self.event_id}\t0\t{self.strand}"
    
    def validate(self) -> bool:
        """Validate splicing event data integrity."""
        if not self.event_id:
            return False
        if not self.event_type:
            return False
        if not self.gene_id:
            return False
        if not self.chromosome:
            return False
        if self.start <= 0 or self.end <= 0:
            return False
        if self.start > self.end:
            return False
        if self.strand not in ['+', '-', '.']:
            return False
        # Validate PSI values are between 0 and 1
        for psi in self.psi_values.values():
            if psi < 0.0 or psi > 1.0:
                return False
        return True
    
    def calculate_delta_psi(self, group1_samples: List[str], group2_samples: List[str]) -> float:
        """
        Calculate delta PSI between two groups of samples.
        
        Args:
            group1_samples: List of sample IDs for group 1
            group2_samples: List of sample IDs for group 2
        
        Returns:
            Mean PSI group 1 minus Mean PSI group 2
        """
        psi_g1 = [self.psi_values.get(s, np.nan) for s in group1_samples]
        psi_g2 = [self.psi_values.get(s, np.nan) for s in group2_samples]
        
        psi_g1_valid = [p for p in psi_g1 if not np.isnan(p)]
        psi_g2_valid = [p for p in psi_g2 if not np.isnan(p)]
        
        if not psi_g1_valid or not psi_g2_valid:
            return np.nan
        
        mean_g1 = np.mean(psi_g1_valid)
        mean_g2 = np.mean(psi_g2_valid)
        
        self.delta_psi = mean_g1 - mean_g2
        return self.delta_psi
    
    def __hash__(self):
        """Make event hashable by event_id."""
        return hash(self.event_id)
    
    def __eq__(self, other):
        """Check equality by event_id."""
        if not isinstance(other, SplicingEvent):
            return False
        return self.event_id == other.event_id

@dataclass
class EnrichmentResult:
    """
    Represents the result of a statistical enrichment test.
    
    Attributes:
        lineage: Lineage tested (e.g., 'human', 'chimp')
        test_type: Type of statistical test performed
        total_events: Total number of events tested
        accelerated_events: Number of accelerated events
        control_events: Number of control events
        odds_ratio: Calculated odds ratio from regression
        p_value: Raw p-value from the test
        fdr: Benjamini-Hochberg adjusted p-value
        regression_coefficient: Coefficient from phylogenetic logistic regression
        confidence_interval: 95% confidence interval tuple (lower, upper)
        permutation_p_value: P-value from permutation test (if performed)
        method_details: Dictionary with detailed method parameters
        timestamp: Timestamp of analysis
    """
    lineage: str
    test_type: str
    total_events: int
    accelerated_events: int
    control_events: int
    odds_ratio: Optional[float] = None
    p_value: Optional[float] = None
    fdr: Optional[float] = None
    regression_coefficient: Optional[float] = None
    confidence_interval: Optional[tuple] = None
    permutation_p_value: Optional[float] = None
    method_details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            'lineage': self.lineage,
            'test_type': self.test_type,
            'total_events': self.total_events,
            'accelerated_events': self.accelerated_events,
            'control_events': self.control_events,
            'odds_ratio': self.odds_ratio,
            'p_value': self.p_value,
            'fdr': self.fdr,
            'regression_coefficient': self.regression_coefficient,
            'confidence_interval': list(self.confidence_interval) if self.confidence_interval else None,
            'permutation_p_value': self.permutation_p_value,
            'method_details': self.method_details,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnrichmentResult':
        """Create EnrichmentResult from dictionary."""
        if 'confidence_interval' in data and data['confidence_interval']:
            data['confidence_interval'] = tuple(data['confidence_interval'])
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EnrichmentResult':
        """Deserialize result from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if result is statistically significant at given alpha."""
        if self.fdr is not None:
            return self.fdr < alpha
        if self.p_value is not None:
            return self.p_value < alpha
        return False
    
    def to_dataframe_row(self) -> Dict[str, Any]:
        """Convert to a flat dictionary suitable for DataFrame row."""
        row = self.to_dict()
        # Flatten confidence interval
        if row['confidence_interval']:
            row['ci_lower'] = row['confidence_interval'][0]
            row['ci_upper'] = row['confidence_interval'][1]
            del row['confidence_interval']
        return row

@dataclass
class PhylogeneticTree:
    """
    Represents a phylogenetic tree for comparative analysis.
    
    Attributes:
        tree_id: Unique identifier for the tree
        newick_string: Newick format string representation
        species: List of species names in the tree
        root_name: Name of the root node
        is_rooted: Whether the tree is rooted
        branch_lengths: Dictionary mapping edge to branch length
        metadata: Additional metadata (source, date, etc.)
    """
    tree_id: str
    newick_string: str
    species: List[str] = field(default_factory=list)
    root_name: Optional[str] = None
    is_rooted: bool = True
    branch_lengths: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to dictionary representation."""
        return {
            'tree_id': self.tree_id,
            'newick_string': self.newick_string,
            'species': self.species,
            'root_name': self.root_name,
            'is_rooted': self.is_rooted,
            'branch_lengths': self.branch_lengths,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhylogeneticTree':
        """Create PhylogeneticTree from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize tree to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PhylogeneticTree':
        """Deserialize tree from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def to_nwk_file(self, path: str) -> None:
        """Write tree to Newick file."""
        with open(path, 'w') as f:
            f.write(self.newick_string + ';')
    
    @classmethod
    def from_nwk_file(cls, path: str, tree_id: str = 'default') -> 'PhylogeneticTree':
        """Load tree from Newick file."""
        with open(path, 'r') as f:
            newick = f.read().strip()
            # Remove trailing semicolon if present
            if newick.endswith(';'):
                newick = newick[:-1]
        
        # Simple parsing to extract species (not full tree parsing)
        # For full parsing, use ape or dendropy
        species = []
        # Extract names between quotes or parentheses
        import re
        names = re.findall(r'["\']([^"\']+)["\']|([a-zA-Z0-9_]+)(?=[,;)\]])', newick)
        for match in names:
            name = match[0] if match[0] else match[1]
            if name and name not in species:
                species.append(name)
        
        return cls(
            tree_id=tree_id,
            newick_string=newick,
            species=species,
            metadata={'source_file': str(path)}
        )
    
    def validate(self) -> bool:
        """Validate tree data integrity."""
        if not self.tree_id:
            return False
        if not self.newick_string:
            return False
        if not self.newick_string.strip():
            return False
        # Basic Newick validation: must have balanced parentheses
        paren_count = 0
        for char in self.newick_string:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            if paren_count < 0:
                return False
        if paren_count != 0:
            return False
        return True
    
    def get_species_count(self) -> int:
        """Return number of species in the tree."""
        return len(self.species)
    
    def __hash__(self):
        """Make tree hashable by tree_id."""
        return hash(self.tree_id)
    
    def __eq__(self, other):
        """Check equality by tree_id and newick string."""
        if not isinstance(other, PhylogeneticTree):
            return False
        return self.tree_id == other.tree_id and self.newick_string == other.newick_string
