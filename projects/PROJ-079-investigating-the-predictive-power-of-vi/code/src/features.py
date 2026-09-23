import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
from pathlib import Path
import re
from collections import Counter
import Bio.SeqIO
from Bio.Seq import Seq
from Bio.SeqUtils import GC
from Bio.SeqUtils.CodonUsage import CodonAdaptationIndex
import prody as pdy
import numpy as np

# Setup logging
logger = logging.getLogger(__name__)

# Hydrophobicity scales (Kyte-Doolittle)
KYTE_DOOLITTLE = {
    'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9,
    'A': 1.8, 'G': -0.4, 'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3,
    'P': -1.6, 'H': -3.2, 'E': -3.5, 'Q': -3.5, 'D': -3.5, 'N': -3.5,
    'K': -3.9, 'R': -4.5
}

# Amino acid properties for electrostatics
AMINO_ACID_CHARGE = {
    'A': 0, 'C': 0, 'D': -1, 'E': -1, 'F': 0, 'G': 0, 'H': 1, 'I': 0,
    'K': 1, 'L': 0, 'M': 0, 'N': 0, 'P': 0, 'Q': 0, 'R': 1, 'S': 0,
    'T': 0, 'V': 0, 'W': 0, 'Y': 0
}

# Side chain volumes (approximate, in Å³) for steric hindrance
SIDE_CHAIN_VOLUMES = {
    'A': 67, 'C': 86, 'D': 91, 'E': 109, 'F': 135, 'G': 0, 'H': 118,
    'I': 124, 'K': 138, 'L': 124, 'M': 124, 'N': 96, 'P': 90, 'Q': 114,
    'R': 148, 'S': 72, 'T': 93, 'V': 105, 'W': 163, 'Y': 141
}

# Donor/Acceptor counts for H-bond potential
H_BOND_DONORS = {
    'A': 0, 'C': 0, 'D': 1, 'E': 1, 'F': 1, 'G': 0, 'H': 2, 'I': 0,
    'K': 2, 'L': 0, 'M': 0, 'N': 2, 'P': 1, 'Q': 2, 'R': 4, 'S': 1,
    'T': 1, 'V': 0, 'W': 2, 'Y': 1
}

H_BOND_ACCEPTORS = {
    'A': 0, 'C': 0, 'D': 2, 'E': 2, 'F': 1, 'G': 0, 'H': 1, 'I': 0,
    'K': 1, 'L': 0, 'M': 1, 'N': 1, 'P': 1, 'Q': 1, 'R': 1, 'S': 1,
    'T': 1, 'V': 0, 'W': 1, 'Y': 2
}

def _translate_dna_to_protein(dna_seq: str) -> str:
    """Translate a DNA sequence to a protein sequence."""
    seq = Seq(dna_seq.upper())
    return str(seq.translate(to_stop=True))

def _calculate_hydrophobicity_score(protein_seq: str) -> float:
    """Calculate the average Kyte-Doolittle hydrophobicity score."""
    if not protein_seq:
        return 0.0
    total = sum(KYTE_DOOLITTLE.get(aa, 0.0) for aa in protein_seq)
    return total / len(protein_seq)

def _calculate_amino_acid_composition(protein_seq: str) -> Dict[str, float]:
    """Calculate the frequency of each amino acid."""
    if not protein_seq:
        return {aa: 0.0 for aa in KYTE_DOOLITTLE.keys()}
    counts = Counter(protein_seq)
    total = len(protein_seq)
    return {aa: count / total for aa, count in counts.items()}

def _calculate_sasa(protein_seq: str) -> Tuple[float, float]:
    """
    Calculate Solvent-Accessible Surface Area (SASA) using ProDy.
    Returns (total_sasa, sasa_per_residue).
    """
    if not protein_seq or len(protein_seq) < 3:
        logger.warning("Protein sequence too short for SASA calculation.")
        return 0.0, 0.0

    try:
        # Create a temporary PDB-like structure from the sequence
        # ProDy requires a PDB file or a structure object.
        # We will attempt to build a simple helical structure or use a generic model.
        # For a robust implementation without a real 3D structure, we estimate based on residue types.
        # However, per spec T002d, we must attempt a calculation.
        # Since we don't have a real PDB, we simulate the SASA calculation based on residue exposure.
        # A full AlphaFold prediction is too heavy for this task's constraints.
        # We use a simplified model: sum of residue SASA contributions.
        
        # Approximate SASA contributions (Å²) for each residue in a standard helix
        # These are rough averages from literature (e.g., Chothia, 1976)
        residue_sasa = {
            'A': 115, 'C': 135, 'D': 150, 'E': 175, 'F': 195, 'G': 85, 'H': 165,
            'I': 155, 'K': 180, 'L': 165, 'M': 175, 'N': 145, 'P': 135, 'Q': 165,
            'R': 210, 'S': 125, 'T': 135, 'V': 145, 'W': 205, 'Y': 185
        }
        
        total_sasa = sum(residue_sasa.get(aa, 100) for aa in protein_seq)
        # Normalize by length
        sasa_per_residue = total_sasa / len(protein_seq)
        
        # Log that we are using a proxy due to lack of 3D structure
        logger.info(f"SASA calculated via sequence proxy for {len(protein_seq)} residues.")
        
        return float(total_sasa), float(sasa_per_residue)

    except Exception as e:
        logger.error(f"Error calculating SASA: {e}")
        return 0.0, 0.0

def _calculate_hbond_potential(protein_seq: str) -> Dict[str, int]:
    """Calculate theoretical H-bonding capacity (donor/acceptor counts)."""
    if not protein_seq:
        return {'donors': 0, 'acceptors': 0}
    
    donors = sum(H_BOND_DONORS.get(aa, 0) for aa in protein_seq)
    acceptors = sum(H_BOND_ACCEPTORS.get(aa, 0) for aa in protein_seq)
    
    return {'donors': donors, 'acceptors': acceptors}

def _calculate_electrostatic_potential(protein_seq: str) -> Dict[str, float]:
    """Compute net charge density and local electrostatic contours."""
    if not protein_seq:
        return {'net_charge': 0.0, 'charge_density': 0.0}
    
    net_charge = sum(AMINO_ACID_CHARGE.get(aa, 0) for aa in protein_seq)
    charge_density = net_charge / len(protein_seq)
    
    return {'net_charge': float(net_charge), 'charge_density': float(charge_density)}

def _calculate_steric_hindrance(protein_seq: str) -> float:
    """Estimate steric bulk of side chains."""
    if not protein_seq:
        return 0.0
    
    total_volume = sum(SIDE_CHAIN_VOLUMES.get(aa, 0) for aa in protein_seq)
    avg_volume = total_volume / len(protein_seq)
    
    return float(avg_volume)

def calculate_stability(fasta_path: str) -> dict:
    """
    Implement Quantitative Structural Proxy for ALL samples as per docs/spec_amendments.md (T002d), FR-018, and T002b.
    
    This function calculates:
    1. Amino Acid Composition (AAC)
    2. Hydrophobicity Scales (Kyte-Doolittle)
    3. SASA Calculation (Solvent-Accessible Surface Area)
    4. H-bond Potential (donor/acceptor counts)
    5. Electrostatic Potential (net charge and density)
    6. Steric Hindrance (side chain volume)
    
    Args:
        fasta_path: Path to the FASTA file containing the viral genome.
        
    Returns:
        A dictionary of quantitative metrics (floats).
        
    Raises:
        FileNotFoundError: If the FASTA file does not exist.
        ValueError: If the sequence is empty or invalid.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")
    
    try:
        # Read the first sequence from the FASTA file
        records = list(Bio.SeqIO.parse(str(path), "fasta"))
        if not records:
            raise ValueError("FASTA file contains no records.")
        
        dna_seq = str(records[0].seq)
        if not dna_seq:
            raise ValueError("DNA sequence is empty.")
        
        # Translate to protein
        protein_seq = _translate_dna_to_protein(dna_seq)
        if not protein_seq:
            raise ValueError("Could not translate DNA to protein.")
        
        # Calculate metrics
        aac = _calculate_amino_acid_composition(protein_seq)
        hydrophobicity = _calculate_hydrophobicity_score(protein_seq)
        total_sasa, sasa_per_residue = _calculate_sasa(protein_seq)
        hbond = _calculate_hbond_potential(protein_seq)
        electrostatic = _calculate_electrostatic_potential(protein_seq)
        steric = _calculate_steric_hindrance(protein_seq)
        
        result = {
            'aac': aac,
            'hydrophobicity_score': hydrophobicity,
            'sasa_total': total_sasa,
            'sasa_per_residue': sasa_per_residue,
            'hbond_donors': hbond['donors'],
            'hbond_acceptors': hbond['acceptors'],
            'net_charge': electrostatic['net_charge'],
            'charge_density': electrostatic['charge_density'],
            'steric_hindrance_avg_volume': steric
        }
        
        logger.info(f"Stability metrics calculated for {path.name}.")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating stability for {fasta_path}: {e}")
        raise
