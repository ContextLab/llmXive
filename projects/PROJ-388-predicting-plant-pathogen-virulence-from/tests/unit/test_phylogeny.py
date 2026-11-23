"""
Unit tests for phylogeny module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

from src.analysis.phylogeny import (
    find_housekeeping_genes,
    concatenate_genes,
    align_sequences,
    build_tree,
    compute_covariance_matrix,
    run_phylogeny_pipeline,
    PhylogenyResult
)
from Bio import AlignIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

@pytest.fixture
def temp_genome_dir():
    """Create a temporary directory with mock genome files."""
    temp_dir = tempfile.mkdtemp()
    genome_dir = Path(temp_dir)
    
    # Create mock housekeeping genes file
    mock_fasta = genome_dir / "housekeeping_genes.fasta"
    sequences = [
        SeqRecord(Seq("ATCGATCGATCG"), id="isolate_1", description=""),
        SeqRecord(Seq("ATCGATCGATCG"), id="isolate_2", description=""),
        SeqRecord(Seq("ATCGATCGATCG"), id="isolate_3", description=""),
    ]
    AlignIO.write(sequences, str(mock_fasta), "fasta")
    
    yield genome_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def cleanup_temp_dir():
    """Fixture to cleanup temporary directories."""
    dirs = []
    yield dirs
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)

def test_find_housekeeping_genes_success(temp_genome_dir):
    """Test successful extraction of housekeeping genes."""
    output_dir = Path(tempfile.mkdtemp())
    try:
        result = find_housekeeping_genes(temp_genome_dir, output_dir)
        assert len(result) == 1
        assert os.path.exists(result[0])
    finally:
        shutil.rmtree(output_dir)

def test_find_housekeeping_genes_not_found(temp_genome_dir):
    """Test error when housekeeping genes file is missing."""
    empty_dir = Path(tempfile.mkdtemp())
    output_dir = Path(tempfile.mkdtemp())
    try:
        with pytest.raises(FileNotFoundError):
            find_housekeeping_genes(empty_dir, output_dir)
    finally:
        shutil.rmtree(empty_dir)
        shutil.rmtree(output_dir)

def test_concatenate_genes(temp_genome_dir):
    """Test concatenation of multiple gene sequences."""
    output_path = Path(tempfile.mktemp(suffix=".fasta"))
    try:
        gene_files = [str(temp_genome_dir / "housekeeping_genes.fasta")]
        result = concatenate_genes(gene_files, output_path)
        
        assert os.path.exists(result)
        alignment = AlignIO.read(result, "fasta")
        assert len(alignment) == 3
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

def test_concatenate_genes_empty(cleanup_temp_dir):
    """Test concatenation with empty gene files."""
    temp_dir = tempfile.mkdtemp()
    cleanup_temp_dir.append(temp_dir)
    output_path = Path(tempfile.mktemp(suffix=".fasta"))
    
    with pytest.raises(ValueError):
        concatenate_genes([], output_path)

def test_align_sequences(temp_genome_dir):
    """Test sequence alignment."""
    input_fasta = temp_genome_dir / "housekeeping_genes.fasta"
    output_fasta = Path(tempfile.mktemp(suffix=".fasta"))
    try:
        result = align_sequences(input_fasta, output_fasta)
        assert os.path.exists(result)
    finally:
        if os.path.exists(output_fasta):
            os.remove(output_fasta)

def test_build_tree(temp_genome_dir):
    """Test tree construction."""
    input_fasta = temp_genome_dir / "housekeeping_genes.fasta"
    output_newick = Path(tempfile.mktemp(suffix=".newick"))
    try:
        # First align
        aligned_path = Path(tempfile.mktemp(suffix=".fasta"))
        align_sequences(input_fasta, aligned_path)
        
        tree = build_tree(aligned_path, output_newick)
        assert tree is not None
        assert os.path.exists(output_newick)
        
        # Check branch lengths
        for branch in tree.find_clades():
            if branch.length is not None:
                assert branch.length > 0
    finally:
        if os.path.exists(output_newick):
            os.remove(output_newick)
        if os.path.exists(aligned_path):
            os.remove(aligned_path)

def test_compute_covariance_matrix(temp_genome_dir):
    """Test covariance matrix computation."""
    from src.analysis.phylogeny import build_tree
    
    input_fasta = temp_genome_dir / "housekeeping_genes.fasta"
    output_newick = Path(tempfile.mktemp(suffix=".newick"))
    try:
        # Build a tree first
        aligned_path = Path(tempfile.mktemp(suffix=".fasta"))
        align_sequences(input_fasta, aligned_path)
        tree = build_tree(aligned_path, output_newick)
        
        species_labels = ["isolate_1", "isolate_2", "isolate_3"]
        cov_matrix = compute_covariance_matrix(tree, species_labels)
        
        assert cov_matrix.shape == (3, 3)
        assert np.all(cov_matrix >= 0)
        assert np.all(np.diag(cov_matrix) > 0)
    finally:
        if os.path.exists(output_newick):
            os.remove(output_newick)
        if os.path.exists(aligned_path):
            os.remove(aligned_path)

def test_run_phylogeny_pipeline(temp_genome_dir, cleanup_temp_dir):
    """Test full phylogeny pipeline."""
    output_dir = Path(tempfile.mkdtemp())
    cleanup_temp_dir.append(str(output_dir))
    
    try:
        result = run_phylogeny_pipeline(temp_genome_dir, output_dir)
        
        assert isinstance(result, PhylogenyResult)
        assert os.path.exists(result.tree_newick_path)
        assert os.path.exists(result.covariance_matrix_path)
        assert len(result.species_labels) > 0
        assert result.covariance_matrix.shape[0] == len(result.species_labels)
    finally:
        shutil.rmtree(output_dir)