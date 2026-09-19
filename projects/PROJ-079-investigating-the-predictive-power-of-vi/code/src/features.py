import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
from pathlib import Path
import re
from collections import Counter
from Bio import SeqIO

logger = logging.getLogger(__name__)

def _validate_fasta_path(fasta_path: str) -> Path:
    """Validate that the input path exists and is readable."""
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {fasta_path}")
    return path

def _parse_fasta_sequence(fasta_path: Path) -> str:
    """
    Parse a FASTA file and return the first sequence found.
    Raises ValueError if no sequence is found or if the sequence is too short.
    """
    try:
        records = list(SeqIO.parse(str(fasta_path), "fasta"))
    except Exception as e:
        raise ValueError(f"Failed to parse FASTA file: {e}")

    if not records:
        raise ValueError("No sequences found in FASTA file")

    # Use the first record
    record = records[0]
    sequence = str(record.seq).upper()

    # Filter out non-ACGT characters (e.g., N, R, Y, etc.) but keep the sequence valid
    # We will replace ambiguous bases with 'N' and then handle them
    clean_sequence = re.sub(r'[^ACGT]', '', sequence)

    if not clean_sequence:
        raise ValueError("No valid DNA sequence found after cleaning")

    return clean_sequence

def calculate_kmer_frequencies(fasta_path: str) -> Dict[str, float]:
    """
    Calculate k-mer frequencies for k=3 and k=4 ONLY as authorized by docs/spec_amendments.md.
    
    This function extracts all k-mers of length 3 and 4 from the input FASTA file
    and returns their relative frequencies. The restriction to k=3 and k=4 is mandated
    by Plan.md Methodological Adjustments to ensure CPU feasibility and Debiased Lasso validity.
    
    Args:
        fasta_path (str): Path to the input FASTA file containing viral genome sequence.
    
    Returns:
        Dict[str, float]: Dictionary mapping k-mer strings to their relative frequencies.
                          Keys are in format 'kmer_3:ACG', 'kmer_4:ACGT' etc.
                          Values are floats between 0.0 and 1.0 representing the proportion
                          of that k-mer in the total k-mer count for that k.
    
    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the file cannot be parsed or contains no valid sequence.
    """
    path = _validate_fasta_path(fasta_path)
    sequence = _parse_fasta_sequence(path)
    
    logger.info(f"Calculating k-mer frequencies for sequence of length {len(sequence)}")
    
    result = {}
    
    # Calculate k=3 frequencies
    k3_counts = Counter()
    k3_total = 0
    for i in range(len(sequence) - 2):
        kmer = sequence[i:i+3]
        k3_counts[kmer] += 1
        k3_total += 1
    
    if k3_total > 0:
        for kmer, count in k3_counts.items():
            result[f"k3_{kmer}"] = count / k3_total
    else:
        logger.warning("Sequence too short for k=3 k-mers")
    
    # Calculate k=4 frequencies
    k4_counts = Counter()
    k4_total = 0
    for i in range(len(sequence) - 3):
        kmer = sequence[i:i+4]
        k4_counts[kmer] += 1
        k4_total += 1
    
    if k4_total > 0:
        for kmer, count in k4_counts.items():
            result[f"k4_{kmer}"] = count / k4_total
    else:
        logger.warning("Sequence too short for k=4 k-mers")
    
    logger.info(f"Generated {len(result)} k-mer frequency features (k=3: {len(k3_counts)}, k=4: {len(k4_counts)})")
    
    return result
