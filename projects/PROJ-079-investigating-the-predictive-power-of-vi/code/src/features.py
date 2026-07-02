import logging
from typing import Dict, Any, Optional
from pathlib import Path
import pybedtools
from src.config import ARTIFACTS_PATH
from Bio.SeqIO import parse
from Bio.Data import IUPACData
import numpy as np

logger = logging.getLogger(__name__)

# Hydrophobicity scales (Kyte-Doolittle)
# Source: Kyte, J. & Doolittle, R.F. (1982)
KYTE_DOOLITTLE = {
    'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9,
    'A': 1.8, 'G': -0.4, 'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3,
    'P': -1.6, 'H': -3.2, 'E': -3.5, 'Q': -3.5, 'D': -3.5, 'N': -3.5,
    'K': -3.9, 'R': -4.5
}

# Standard codon table to map DNA to Amino Acids
CODON_TABLE = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
}

def _translate_dna_to_protein(dna_seq: str) -> str:
    """Translate a DNA sequence to a protein sequence."""
    protein = []
    # Clean sequence
    dna_seq = dna_seq.upper().replace('U', 'T')
    
    # Remove any non-ATGC characters (except N which we skip)
    valid_bases = set('ATGC')
    clean_seq = ''.join([b for b in dna_seq if b in valid_bases])
    
    if len(clean_seq) < 3:
        return ""
    
    for i in range(0, len(clean_seq) - 2, 3):
        codon = clean_seq[i:i+3]
        aa = CODON_TABLE.get(codon, '*')
        if aa == '*':
            break
        protein.append(aa)
    
    return ''.join(protein)

def _calculate_amino_acid_composition(protein: str) -> Dict[str, float]:
    """Calculate the frequency of each amino acid in the protein."""
    if not protein:
        return {aa: 0.0 for aa in KYTE_DOOLITTLE.keys()}
    
    counts = {}
    for aa in KYTE_DOOLITTLE.keys():
        counts[aa] = protein.count(aa)
    
    total = len(protein)
    return {aa: count / total for aa, count in counts.items()}

def _calculate_hydrophobicity_score(protein: str) -> float:
    """Calculate the average hydrophobicity score of the protein."""
    if not protein:
        return 0.0
    
    total_score = 0.0
    valid_count = 0
    
    for aa in protein:
        if aa in KYTE_DOOLITTLE:
            total_score += KYTE_DOOLITTLE[aa]
            valid_count += 1
    
    if valid_count == 0:
        return 0.0
    
    return total_score / valid_count

def calculate_stability(fasta_path: str) -> float:
    """
    Calculate the Uniform Stability Proxy for a viral genome.
    
    This implements the stability metric based on Amino Acid Composition
    and Hydrophobicity Scales (Kyte-Doolittle) as specified in Plan.md.
    ESM-1b is explicitly excluded due to CPU constraints.
    
    Args:
        fasta_path: Path to the FASTA file containing the viral genome.
        
    Returns:
        float: Stability score (higher indicates more hydrophobic/stable).
        
    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the sequence cannot be translated or is empty.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")
    
    try:
        # Parse the first record (assuming one genome per file for this function)
        records = list(parse(str(path), "fasta"))
        if not records:
            raise ValueError("No records found in FASTA file")
        
        record = records[0]
        dna_seq = str(record.seq)
        
        if not dna_seq:
            raise ValueError("Empty sequence in FASTA file")
        
        # Translate DNA to protein
        protein = _translate_dna_to_protein(dna_seq)
        
        if not protein:
            logger.warning(f"No valid protein sequence translated from {fasta_path}")
            return 0.0
        
        # Calculate components
        aa_comp = _calculate_amino_acid_composition(protein)
        hydro_score = _calculate_hydrophobicity_score(protein)
        
        # The Uniform Stability Proxy is defined as the average hydrophobicity
        # weighted by the composition of stable residues (I, V, L, F, C, M, A)
        stable_residues = ['I', 'V', 'L', 'F', 'C', 'M', 'A']
        stable_fraction = sum(aa_comp[aa] for aa in stable_residues)
        
        # Final score: hydrophobicity * stability fraction
        # This captures both the hydrophobic nature and the proportion of stable residues
        stability_score = hydro_score * (1.0 + stable_fraction)
        
        logger.info(f"Calculated stability score for {path.name}: {stability_score:.4f}")
        return float(stability_score)
        
    except Exception as e:
        logger.error(f"Error calculating stability for {fasta_path}: {e}")
        raise

def calculate_repeat_density(fasta_path: str) -> float:
    """
    Calculate the percentage of the genome covered by repeats.
    
    Args:
        fasta_path: Path to the FASTA file.
        
    Returns:
        float: Percentage of genome covered by repeats.
    """
    # Note: This is a stub implementation as per existing file.
    # In a full implementation, this would use pybedtools with a repeat mask track.
    # For now, we return 0.0 to avoid breaking the pipeline if repeat tracks are unavailable.
    # The actual implementation would require a genome reference and repeat mask file.
    logger.warning("calculate_repeat_density is not fully implemented; returning 0.0")
    return 0.0
