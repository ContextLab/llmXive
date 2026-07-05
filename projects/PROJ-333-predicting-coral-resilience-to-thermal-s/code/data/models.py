"""
Base data model definitions for the coral resilience research pipeline.

These classes define the structure for genomic data (VCF/PLINK),
phenotype data, and quality metrics used throughout the pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import pandas as pd


class GenotypeCall(Enum):
    """Enum for genotype calls."""
    HOMO_REF = 0
    HET = 1
    HOMO_ALT = 2
    MISSING = -1


class Sex(Enum):
    """Sex classification."""
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2
    HERMAPHRODITE = 3


@dataclass
class Sample:
    """
    Represents a biological sample (individual coral colony).

    Attributes:
        sample_id: Unique identifier for the sample (FAM ID in PLINK).
        individual_id: Individual identifier (IID in PLINK).
        paternal_id: Paternal parent ID (0 if unknown).
        maternal_id: Maternal parent ID (0 if unknown).
        sex: Sex of the individual.
        phenotype: Phenotype value (1 for case/control, or continuous value).
        metadata: Additional metadata dictionary.
    """
    sample_id: str
    individual_id: str
    paternal_id: str = "0"
    maternal_id: str = "0"
    sex: Sex = Sex.UNKNOWN
    phenotype: float = -9.0  # -9.0 is PLINK's missing phenotype code
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_plink_fam_row(self) -> str:
        """Convert to PLINK .fam file row format."""
        return f"{self.sample_id} {self.individual_id} {self.paternal_id} {self.maternal_id} {self.sex.value} {self.phenotype}"


@dataclass
class Variant:
    """
    Represents a genetic variant (SNP).

    Attributes:
        variant_id: Unique identifier (rsID or custom ID).
        chromosome: Chromosome name (e.g., "1", "X").
        position: 1-based position on the chromosome.
        reference_allele: Reference allele sequence.
        alternate_allele: Alternate allele sequence.
        allele_frequency: Minor allele frequency (optional).
        quality_score: Quality score from VCF.
        filters: List of filter statuses from VCF.
        info: Additional INFO field data from VCF.
    """
    variant_id: str
    chromosome: str
    position: int
    reference_allele: str
    alternate_allele: str
    allele_frequency: Optional[float] = None
    quality_score: float = 0.0
    filters: List[str] = field(default_factory=lambda: ["PASS"])
    info: Dict[str, Any] = field(default_factory=dict)

    def to_plink_bim_row(self) -> str:
        """Convert to PLINK .bim file row format."""
        # PLINK BIM format: chr, variant_id, genetic_pos, bp_pos, allele1, allele2
        # genetic_pos is typically 0 if unknown
        return f"{self.chromosome} {self.variant_id} 0 {self.position} {self.alternate_allele} {self.reference_allele}"


@dataclass
class Genotype:
    """
    Represents a genotype call for a specific sample at a specific variant.

    Attributes:
        variant_id: Reference to the variant.
        sample_id: Reference to the sample.
        call: The genotype call (0, 1, 2, or -1 for missing).
        dosage: Expected number of alternate alleles (0.0 to 2.0).
    """
    variant_id: str
    sample_id: str
    call: GenotypeCall
    dosage: Optional[float] = None

    @property
    def is_missing(self) -> bool:
        """Check if genotype is missing."""
        return self.call == GenotypeCall.MISSING

    @property
    def is_homo_ref(self) -> bool:
        """Check if homozygous reference."""
        return self.call == GenotypeCall.HOMO_REF

    @property
    def is_het(self) -> bool:
        """Check if heterozygous."""
        return self.call == GenotypeCall.HET

    @property
    def is_homo_alt(self) -> bool:
        """Check if homozygous alternate."""
        return self.call == GenotypeCall.HOMO_ALT


@dataclass
class Phenotype:
    """
    Represents phenotype data for analysis.

    Attributes:
        sample_id: Reference to the sample.
        trait_name: Name of the trait (e.g., "survival", "temp_tolerance").
        value: The measured value.
        is_binary: Whether the trait is binary (case/control).
        raw_data: Original raw data dictionary for traceability.
    """
    sample_id: str
    trait_name: str
    value: float
    is_binary: bool = False
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dataframe_row(cls, row: pd.Series, sample_id_col: str, trait_col: str) -> 'Phenotype':
        """Create a Phenotype instance from a pandas DataFrame row."""
        sample_id = str(row[sample_id_col])
        value = float(row[trait_col])
        is_binary = value in [0.0, 1.0, -9.0]
        return cls(
            sample_id=sample_id,
            trait_name=trait_col,
            value=value,
            is_binary=is_binary,
            raw_data=row.to_dict()
        )


@dataclass
class QualityMetrics:
    """
    Stores quality control metrics for a dataset or filter operation.

    Attributes:
        total_samples: Total number of samples.
        retained_samples: Number of samples after filtering.
        total_variants: Total number of variants.
        retained_variants: Number of variants after filtering.
        missingness_rate: Rate of missing data (0.0 to 1.0).
        maf_threshold: Minimum allele frequency threshold used.
        missingness_threshold: Maximum missingness threshold used.
        filtered_variants_reasons: Dictionary mapping variant IDs to filter reasons.
        filtered_samples_reasons: Dictionary mapping sample IDs to filter reasons.
    """
    total_samples: int = 0
    retained_samples: int = 0
    total_variants: int = 0
    retained_variants: int = 0
    missingness_rate: float = 0.0
    maf_threshold: float = 0.05
    missingness_threshold: float = 0.10
    filtered_variants_reasons: Dict[str, str] = field(default_factory=dict)
    filtered_samples_reasons: Dict[str, str] = field(default_factory=dict)

    @property
    def sample_retention_rate(self) -> float:
        """Calculate sample retention rate."""
        if self.total_samples == 0:
            return 0.0
        return self.retained_samples / self.total_samples

    @property
    def variant_retention_rate(self) -> float:
        """Calculate variant retention rate."""
        if self.total_variants == 0:
            return 0.0
        return self.retained_variants / self.total_variants

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary for reporting."""
        return {
            "total_samples": self.total_samples,
            "retained_samples": self.retained_samples,
            "sample_retention_rate": self.sample_retention_rate,
            "total_variants": self.total_variants,
            "retained_variants": self.retained_variants,
            "variant_retention_rate": self.variant_retention_rate,
            "missingness_rate": self.missingness_rate,
            "maf_threshold": self.maf_threshold,
            "missingness_threshold": self.missingness_threshold,
            "num_filtered_variants": len(self.filtered_variants_reasons),
            "num_filtered_samples": len(self.filtered_samples_reasons),
        }


@dataclass
class Dataset:
    """
    Container for a complete genomic dataset (samples, variants, genotypes).

    Attributes:
        name: Dataset name.
        species: Species name (e.g., "Acropora millepora").
        source: Source of the data (e.g., "NCBI PRJNA12345").
        samples: List of Sample objects.
        variants: List of Variant objects.
        genotypes: List of Genotype objects (sparse representation).
        phenotype_data: Optional Phenotype object or list.
        quality_metrics: QualityMetrics object.
    """
    name: str
    species: str
    source: str
    samples: List[Sample] = field(default_factory=list)
    variants: List[Variant] = field(default_factory=list)
    genotypes: List[Genotype] = field(default_factory=list)
    phenotype_data: Optional[Phenotype] = None
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)

    @property
    def sample_count(self) -> int:
        """Get number of samples."""
        return len(self.samples)

    @property
    def variant_count(self) -> int:
        """Get number of variants."""
        return len(self.variants)

    @property
    def genotype_count(self) -> int:
        """Get number of genotype calls."""
        return len(self.genotypes)

    def get_sample_map(self) -> Dict[str, Sample]:
        """Get a dictionary mapping sample_id to Sample object."""
        return {s.sample_id: s for s in self.samples}

    def get_variant_map(self) -> Dict[str, Variant]:
        """Get a dictionary mapping variant_id to Variant object."""
        return {v.variant_id: v for v in self.variants}

    def to_summary(self) -> str:
        """Generate a text summary of the dataset."""
        return (
            f"Dataset: {self.name}\n"
            f"Species: {self.species}\n"
            f"Source: {self.source}\n"
            f"Samples: {self.sample_count}\n"
            f"Variants: {self.variant_count}\n"
            f"Genotypes: {self.genotype_count}\n"
            f"Quality Metrics:\n"
            f"  Missingness Rate: {self.quality_metrics.missingness_rate:.4f}\n"
            f"  MAF Threshold: {self.quality_metrics.maf_threshold}\n"
        )
