"""
Utility functions for genome coordinate helpers, FASTA I/O, and checksums.
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
    chrom: str
    start: int
    end: int
    name: Optional[str] = None
    score: Optional[int] = None
    strand: Optional[str] = None

@dataclass
class SNP:
    chrom: str
    pos: int
    id: str
    ref: str
    alt: List[str]
    qual: Optional[float] = None
    filter_val: Optional[str] = None
    info: Dict = None

def parse_bed_line(line: str) -> Optional[GenomicRegion]:
    """Parse a BED line into a GenomicRegion."""
    parts = line.strip().split('\t')
    if len(parts) < 3:
        return None
    
    try:
        chrom = parts[0]
        start = int(parts[1])
        end = int(parts[2])
        name = parts[3] if len(parts) > 3 else None
        score = int(parts[4]) if len(parts) > 4 and parts[4] else None
        strand = parts[5] if len(parts) > 5 and parts[5] else None
        
        return GenomicRegion(chrom=chrom, start=start, end=end, name=name, score=score, strand=strand)
    except ValueError:
        return None

def parse_vcf_line(line: str) -> Optional[SNP]:
    """Parse a VCF line into a SNP object."""
    parts = line.strip().split('\t')
    if len(parts) < 8:
        return None
    
    try:
        chrom = parts[0]
        pos = int(parts[1])
        id_val = parts[2]
        ref = parts[3]
        alt = parts[4].split(',')
        qual = float(parts[5]) if parts[5] != '.' else None
        filter_val = parts[6] if parts[6] != '.' else None
        
        info = {}
        if len(parts) > 7:
            for field in parts[7].split(';'):
                if '=' in field:
                    key, val = field.split('=', 1)
                    info[key] = val
                else:
                    info[field] = True
        
        return SNP(chrom=chrom, pos=pos, id=id_val, ref=ref, alt=alt, qual=qual, filter_val=filter_val, info=info)
    except ValueError:
        return None

def calculate_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate the checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def load_checksums(path: str = "data/checksums.json") -> Dict:
    """Load checksums from JSON file."""
    import json
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_checksums(data: Dict, path: str = "data/checksums.json"):
    """Save checksums to JSON file."""
    import json
    import time
    data['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def verify_checksums(files: Dict[str, str], path: str = "data/checksums.json") -> bool:
    """Verify file checksums against stored values."""
    stored = load_checksums(path)
    all_valid = True
    for file_path, expected_hash in files.items():
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            all_valid = False
            continue
        
        actual_hash = calculate_file_checksum(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {file_path}")
            all_valid = False
        else:
            logger.info(f"Checksum verified: {file_path}")
    return all_valid

class FASTAReader:
    """Memory-mapped FASTA reader wrapper."""
    def __init__(self, fasta_path: str):
        try:
            from pyfaidx import Fasta
            self.fasta = Fasta(fasta_path, build_index=True)
        except ImportError:
            raise ImportError("pyfaidx is required for FASTA reading.")
    
    def get_sequence(self, chrom: str, start: int, end: int) -> str:
        """Get sequence from chrom, start, end (1-based, inclusive)."""
        # pyfaidx uses 0-based start, 1-based end?
        # Fasta object: [chrom][start:end] -> start is 0-based, end is exclusive?
        # Let's check: Fasta uses 0-based start, 1-based end for slicing?
        # Actually, pyfaidx uses 1-based coordinates for the Fasta object if initialized with build_index=True?
        # Default is 0-based for slicing.
        # We will assume 0-based start, 1-based end for the slice.
        # Input is 1-based inclusive.
        # So start_0 = start - 1, end_1 = end.
        try:
            seq = self.fasta[chrom][start-1:end].seq
            return seq.upper()
        except KeyError:
            return ""
    
    def close(self):
        self.fasta.close()
