"""
Utility functions for genome coordinate handling and file operations.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GenomicRegion:
    """Represents a genomic region."""
    chrom: str
    start: int
    end: int
    name: Optional[str] = None
    score: Optional[str] = None
    strand: Optional[str] = None

@dataclass
class SNP:
    """Represents a Single Nucleotide Polymorphism."""
    chrom: str
    pos: int
    ref: str
    alt: str
    snp_id: str
    maf: Optional[float] = None

def parse_bed_line(line: str) -> GenomicRegion:
    """Parse a BED format line into a GenomicRegion object."""
    parts = line.strip().split('\t')
    return GenomicRegion(
        chrom=parts[0],
        start=int(parts[1]),
        end=int(parts[2]),
        name=parts[3] if len(parts) > 3 else None,
        score=parts[4] if len(parts) > 4 else None,
        strand=parts[5] if len(parts) > 5 else None
    )

def parse_vcf_line(line: str) -> SNP:
    """Parse a VCF format line into a SNP object."""
    parts = line.strip().split('\t')
    info = dict(item.split('=') if '=' in item else [item, ''] for item in parts[8].split(';'))
    maf = float(info.get('AF', 0))
    
    return SNP(
        chrom=parts[0],
        pos=int(parts[1]),
        ref=parts[3],
        alt=parts[4],
        snp_id=parts[2],
        maf=maf
    )

def calculate_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def load_checksums(checksum_path: str) -> Dict[str, str]:
    """Load checksums from JSON file."""
    import json
    with open(checksum_path, 'r') as f:
        return json.load(f)

def save_checksums(checksums: Dict[str, str], checksum_path: str):
    """Save checksums to JSON file."""
    import json
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksums(file_paths: List[str], checksums: Dict[str, str]) -> bool:
    """Verify checksums for a list of files."""
    all_valid = True
    for path in file_paths:
        if path in checksums:
            calculated = calculate_file_checksum(path)
            if calculated != checksums[path]:
                logger.error(f"Checksum mismatch for {path}")
                all_valid = False
        else:
            logger.warning(f"No checksum found for {path}")
    return all_valid

class FASTAReader:
    """Memory-mapped FASTA file reader."""
    def __init__(self, fasta_path: str):
        self.fasta_path = fasta_path
        self.index_path = fasta_path + '.fai'
        if not os.path.exists(self.index_path):
            self._create_index()
    
    def _create_index(self):
        """Create FASTA index if it doesn't exist."""
        import pyfaidx
        _ = pyfaidx.Fasta(self.fasta_path)
        logger.info(f"Created index for {self.fasta_path}")
    
    def get_sequence(self, chrom: str, start: int, end: int) -> str:
        """Get sequence for a genomic region."""
        import pyfaidx
        fasta = pyfaidx.Fasta(self.fasta_path)
        seq = fasta[chrom][start:end].seq
        return seq.upper()
