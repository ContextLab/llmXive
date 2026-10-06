import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GenomicRegion:
    chrom: str
    start: int
    end: int
    name: Optional[str] = None
    score: Optional[str] = None
    strand: Optional[str] = None

@dataclass
class SNP:
    snp_id: str
    chrom: str
    pos: int
    ref: str
    alt: str
    maf: float

def parse_bed_line(line: str) -> Optional[GenomicRegion]:
    """Parse a BED line into a GenomicRegion object."""
    parts = line.strip().split('\t')
    if len(parts) < 3:
        return None
    
    try:
        return GenomicRegion(
            chrom=parts[0],
            start=int(parts[1]),
            end=int(parts[2]),
            name=parts[3] if len(parts) > 3 else None,
            score=parts[4] if len(parts) > 4 else None,
            strand=parts[5] if len(parts) > 5 else None
        )
    except (ValueError, IndexError):
        logger.warning(f"Failed to parse BED line: {line}")
        return None

def parse_vcf_line(line: str) -> Optional[SNP]:
    """Parse a VCF line into a SNP object."""
    if line.startswith('#'):
        return None
    
    parts = line.strip().split('\t')
    if len(parts) < 8:
        return None
    
    try:
        snp_id = parts[2] if parts[2] != '.' else f"chr{parts[0]}:{parts[1]}"
        chrom = parts[0]
        pos = int(parts[1])
        ref = parts[3]
        alt = parts[4]
        
        # Parse MAF from INFO field
        maf = 0.0
        for info in parts[7].split(';'):
            if info.startswith('AF='):
                try:
                    maf = float(info.split('=')[1])
                except ValueError:
                    pass
                break
        
        return SNP(
            snp_id=snp_id,
            chrom=chrom,
            pos=pos,
            ref=ref,
            alt=alt,
            maf=maf
        )
    except (ValueError, IndexError):
        logger.warning(f"Failed to parse VCF line: {line}")
        return None

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate the checksum of a file."""
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def load_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    import json
    if not checksum_file.exists():
        return {}
    with open(checksum_file, 'r') as f:
        return json.load(f)

def save_checksums(checksums: Dict[str, str], checksum_file: Path):
    """Save checksums to a JSON file."""
    import json
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksums(checksum_file: Path) -> bool:
    """Verify file checksums against stored values."""
    import json
    if not checksum_file.exists():
        logger.error("Checksum file not found")
        return False
    
    with open(checksum_file, 'r') as f:
        stored_checksums = json.load(f)
    
    all_valid = True
    for file_path, expected_checksum in stored_checksums.items():
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {path}")
            all_valid = False
            continue
        
        actual_checksum = calculate_file_checksum(path)
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch for {path}: expected {expected_checksum}, got {actual_checksum}")
            all_valid = False
        else:
            logger.info(f"Checksum verified for {path}")
    
    return all_valid

class FASTAReader:
    """Memory-mapped FASTA reader."""
    def __init__(self, fasta_path: Path):
        self.fasta_path = fasta_path
        # In a real implementation, we'd use pyfaidx or similar here
        # For now, we provide a basic interface
    
    def get_sequence(self, chrom: str, start: int, end: int) -> Optional[str]:
        """Get sequence for a genomic region."""
        # Placeholder implementation
        # Real implementation would use pyfaidx
        logger.warning("FASTAReader.get_sequence is not fully implemented")
        return None
