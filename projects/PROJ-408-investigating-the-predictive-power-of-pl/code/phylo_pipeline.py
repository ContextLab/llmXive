"""
Phylogenetic Pipeline: Concatenation, Alignment, and Tree Building.
Implements T015a, T015b, T016a, T016b, T017.
"""
import logging
import os
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from entities import PhylogeneticTree, DistanceMatrix
from logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ConcatenationResult:
    species: List[str]
    sequence: str
    lengths: Dict[str, int]

def concatenate_multilocus_fasta(gene_data: Dict[str, Dict[str, str]]) -> ConcatenationResult:
    """
    Concatenate multiple locus sequences for each species.
    Input: {species: {locus: sequence}}
    """
    # Determine order of loci (sorted for consistency)
    all_loci = set()
    for species_genes in gene_data.values():
        all_loci.update(species_genes.keys())
    ordered_loci = sorted(list(all_loci))

    species_list = []
    concatenated_seqs = []
    lengths = {}

    for species, genes in gene_data.items():
        species_list.append(species)
        full_seq = ""
        for locus in ordered_loci:
            if locus in genes:
                seq = genes[locus].replace("\n", "").replace(" ", "")
                full_seq += seq
                lengths[species] = len(full_seq)
            else:
                # Handle missing loci with gaps if necessary, or skip
                # For this pipeline, we assume missing loci result in gaps or exclusion
                # Here we just skip to avoid length mismatch, but log warning
                logger.warning(f"Species {species} missing locus {locus}")
        concatenated_seqs.append(full_seq)

    return ConcatenationResult(
        species=species_list,
        sequence="\n".join([f">{s}\n{seq}" for s, seq in zip(species_list, concatenated_seqs)]),
        lengths=lengths
    )

def write_concatenated_fasta(result: ConcatenationResult, output_path: Path):
    """Write concatenated sequences to a FASTA file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(result.sequence)
    logger.info(f"Wrote concatenated FASTA to {output_path}")

def run_concatenation_pipeline(gene_data: Dict[str, Dict[str, str]], output_path: Path):
    """Full pipeline for concatenation."""
    result = concatenate_multilocus_fasta(gene_data)
    write_concatenated_fasta(result, output_path)
    return result

def run_alignment_pipeline(input_fasta: Path, output_fasta: Path):
    """
    Run MAFFT alignment.
    Constraint: Must use mafft binary with --thread flags.
    """
    if not input_fasta.exists():
        raise FileNotFoundError(f"Input alignment file not found: {input_fasta}")

    # Check for mafft
    try:
        subprocess.run(["mafft", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("MAFFT binary not found in PATH. Ensure T002a is completed.")

    cmd = [
        "mafft",
        "--thread", "4",  # Use 4 threads
        "--auto",
        str(input_fasta)
    ]

    logger.info(f"Running MAFFT: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        output_fasta.parent.mkdir(parents=True, exist_ok=True)
        with open(output_fasta, 'w') as f:
            f.write(result.stdout)
        
        logger.info(f"Alignment complete: {output_fasta}")
    except subprocess.CalledProcessError as e:
        logger.error(f"MAFFT failed: {e.stderr}")
        raise

def run_tree_building_pipeline(input_fasta: Path, output_newick: Path, return_matrix: bool = False):
    """
    Run FastTree to build a maximum likelihood tree.
    Constraint: Must use FastTree binary.
    """
    if not input_fasta.exists():
        raise FileNotFoundError(f"Input alignment file not found: {input_fasta}")

    # Check for FastTree
    try:
        subprocess.run(["FastTree", "-version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("FastTree binary not found in PATH. Ensure T002a is completed.")

    cmd = [
        "FastTree",
        "-nt",  # Nucleotide
        "-lg",  # General Time Reversible model (good for nucleotides)
        str(input_fasta)
    ]

    logger.info(f"Running FastTree: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        output_newick.parent.mkdir(parents=True, exist_ok=True)
        with open(output_newick, 'w') as f:
            f.write(result.stdout)
        
        logger.info(f"Tree building complete: {output_newick}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FastTree failed: {e.stderr}")
        raise

    if return_matrix:
        return calculate_patristic_distance_matrix(output_newick)

    return output_newick

def calculate_patristic_distance_matrix(tree_file: Path) -> DistanceMatrix:
    """
    Calculate patristic distance matrix from a Newick tree.
    Constraint: Treat unresolved nodes as average path length.
    """
    try:
        import dendropy
    except ImportError:
        # Fallback to a simple parser if dendropy is not available, 
        # but dendropy is standard for this. 
        # If not installed, we raise an error as per strict dependencies.
        raise ImportError("DendroPy is required for patristic distance calculation.")

    tree = dendropy.Tree.get(
        path=tree_file,
        schema="newick",
        rooting="force-rooted" # or "unrooted" depending on input
    )

    species_labels = [leaf.taxon.label for leaf in tree.leaf_nodes()]
    n = len(species_labels)
    matrix = np.zeros((n, n))

    for i, leaf_i in enumerate(tree.leaf_nodes()):
        for j, leaf_j in enumerate(tree.leaf_nodes()):
            if i <= j:
                dist = tree.phylogenetic_distance(leaf_i, leaf_j)
                matrix[i, j] = dist
                matrix[j, i] = dist

    return DistanceMatrix(
        species=species_labels,
        values=matrix
    )
