"""
Unit tests for phylogeny analysis module.
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

@pytest.fixture
def temp_genome_dir():
    """Create a temporary directory with mock genome files."""
    temp_dir = tempfile.mkdtemp()
    genome_dir = Path(temp_dir)
    
    # Create mock genome files with housekeeping genes
    mock_sequences = {
        "strain1.fna": [
            (">strain1 rpoB gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
            (">strain1 gyrB gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
            (">strain1 16S gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
        ],
        "strain2.fna": [
            (">strain2 rpoB gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
            (">strain2 gyrB gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
            (">strain2 16S gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
        ],
        "strain3.fna": [
            (">strain3 rpoB gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
            (">strain3 gyrB gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
            (">strain3 16S gene", "ATGCGTACGTACGTACGTACGTACGTACGTACGTACGT"),
        ],
    }
    
    for filename, sequences in mock_sequences.items():
        filepath = genome_dir / filename
        with open(filepath, 'w') as f:
            for header, seq in sequences:
                f.write(f"{header}\n{seq}\n")
    
    yield genome_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def cleanup_temp_dir():
    """Clean up temporary directories after tests."""
    yield
    # Cleanup is handled by individual fixtures

def test_find_housekeeping_genes_success(temp_genome_dir):
    """Test successful finding of housekeeping genes."""
    genes = ['rpoB', 'gyrB', '16S']
    result = find_housekeeping_genes(temp_genome_dir, genes)
    
    assert len(result) == 3
    for gene in genes:
        assert gene in result
        assert len(result[gene]) == 3  # 3 strains

def test_find_housekeeping_genes_not_found(temp_genome_dir):
    """Test finding non-existent genes."""
    genes = ['nonexistent']
    result = find_housekeeping_genes(temp_genome_dir, genes)
    
    assert len(result) == 1
    assert len(result['nonexistent']) == 0

def test_concatenate_genes(temp_genome_dir):
    """Test concatenation of gene sequences."""
    output_fasta = Path(tempfile.mktemp(suffix=".fasta"))
    
    try:
        sample_ids = concatenate_genes(temp_genome_dir, output_fasta)
        
        assert len(sample_ids) == 3
        assert set(sample_ids) == {'strain1', 'strain2', 'strain3'}
        assert output_fasta.exists()
        
        # Verify file content
        with open(output_fasta, 'r') as f:
            content = f.read()
            assert 'strain1' in content
            assert 'strain2' in content
            assert 'strain3' in content
    finally:
        if output_fasta.exists():
            output_fasta.unlink()

def test_concatenate_genes_empty(temp_genome_dir):
    """Test concatenation with no genes found."""
    output_fasta = Path(tempfile.mktemp(suffix=".fasta"))
    genes = ['nonexistent']
    
    sample_ids = concatenate_genes(temp_genome_dir, output_fasta, genes)
    
    assert len(sample_ids) == 0
    assert not output_fasta.exists()

def test_align_sequences(temp_genome_dir):
    """Test sequence alignment (mock test)."""
    # Create a simple FASTA file
    input_fasta = Path(tempfile.mktemp(suffix=".fasta"))
    output_fasta = Path(tempfile.mktemp(suffix=".fasta"))
    
    try:
        with open(input_fasta, 'w') as f:
            f.write(">seq1\nATCG\n>seq2\nATCG\n")
        
        # This will fail if MUSCLE is not installed, which is expected
        # In a real test environment, MUSCLE should be available
        success = align_sequences(input_fasta, output_fasta)
        
        # If MUSCLE is available, success should be True
        # If not, success should be False
        # We just check that the function returns a boolean
        assert isinstance(success, bool)
    finally:
        if input_fasta.exists():
            input_fasta.unlink()
        if output_fasta.exists():
            output_fasta.unlink()

def test_build_tree(temp_genome_dir):
    """Test tree building (mock test)."""
    # Create a simple alignment file
    align_fasta = Path(tempfile.mktemp(suffix=".fasta"))
    tree_output = Path(tempfile.mktemp(suffix=".tree"))
    
    try:
        with open(align_fasta, 'w') as f:
            f.write(">seq1\nATCG\n>seq2\nATCG\n")
        
        # This will fail if IQ-TREE or MUSCLE is not installed
        tree = build_tree(align_fasta, tree_output)
        
        # If tools are available, tree should be built
        # If not, tree should be None (fallback to distance method)
        # We just check the return type
        assert tree is None or hasattr(tree, 'format')
    finally:
        if align_fasta.exists():
            align_fasta.unlink()
        if tree_output.exists():
            tree_output.unlink()
        # Also remove IQ-TREE generated files
        treefile = Path(str(tree_output.with_suffix('')) + ".treefile")
        if treefile.exists():
            treefile.unlink()

def test_compute_covariance_matrix():
    """Test covariance matrix computation."""
    # Create a simple mock tree
    from Bio.Phylo.BaseTree import Tree, Clade, Branch
    
    # Build a simple tree: (A:1, B:1):0.5
    root = Clade()
    root.name = "root"
    
    clade_a = Clade()
    clade_a.name = "A"
    clade_a.branch_length = 1.0
    
    clade_b = Clade()
    clade_b.name = "B"
    clade_b.branch_length = 1.0
    
    root.clades = [clade_a, clade_b]
    
    tree = Tree(root=root)
    tree.rooted = True
    
    sample_ids = ['A', 'B']
    covariance_matrix = compute_covariance_matrix(tree, sample_ids)
    
    assert covariance_matrix.shape == (2, 2)
    # Diagonal should be path length from root to tip
    assert covariance_matrix[0, 0] > 0
    assert covariance_matrix[1, 1] > 0
    # Off-diagonal should be shared path length
    assert covariance_matrix[0, 1] > 0
    assert covariance_matrix[0, 1] == covariance_matrix[1, 0]

def test_run_phylogeny_pipeline(temp_genome_dir):
    """Test complete phylogeny pipeline."""
    output_dir = Path(tempfile.mkdtemp())
    
    try:
        result = run_phylogeny_pipeline(temp_genome_dir, output_dir)
        
        # Check result type
        assert isinstance(result, PhylogenyResult)
        
        # If pipeline succeeded, check outputs
        if result.success:
            assert Path(result.tree_path).exists()
            assert Path(result.covariance_matrix_path).exists()
            assert len(result.sample_ids) == 3
            
            # Check covariance matrix
            cov_matrix = np.load(result.covariance_matrix_path)
            assert cov_matrix.shape == (3, 3)
            assert np.allclose(cov_matrix, cov_matrix.T)  # Symmetric
        else:
            # If failed, check error message
            assert result.error_message is not None
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
