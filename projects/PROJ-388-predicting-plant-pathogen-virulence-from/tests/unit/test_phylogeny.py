"""
Unit tests for housekeeping gene extraction and tree construction (T022).

This module tests the logic of src/analysis/phylogeny.py without requiring
the full execution of IQ-TREE or heavy external dependencies during unit testing.
It verifies:
1. Correct identification of housekeeping genes (rpoB, gyrB, 16S).
2. Proper sequence alignment logic (mocked).
3. Tree construction validation logic (mocked/newick parsing).
4. Phylogenetic covariance matrix generation logic.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np

# We will import the functions we intend to test.
# Since src/analysis/phylogeny.py is not yet implemented (T026-T027),
# we define the expected interface here for the test to target,
# and we mock the heavy external calls (prodigal, iqtree).
# The test ensures that once the implementation exists, it follows this contract.

# Mock the external modules that might not be installed in the test environment
# to ensure the test file itself is runnable.
try:
    from src.analysis import phylogeny
except ImportError:
    # If the module doesn't exist yet, we define a minimal stub for testing purposes
    # or skip the specific integration parts, but here we test the logic
    # assuming the module will be created.
    phylogeny = None


# --- Fixtures ---

@pytest.fixture
def temp_genome_dir():
    """Create a temporary directory with mock genome FASTA files."""
    tmpdir = tempfile.mkdtemp()
    genome_path = Path(tmpdir) / "test_genome.fna"
    
    # Mock FASTA content with housekeeping genes
    content = (
        ">gene_001|16S|length=1500\n"
        "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG\n"
        ">gene_002|rpoB|length=3000\n"
        "GGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGGCCCCAAAATTTT\n"
        ">gene_003|gyrB|length=2500\n"
        "TTTTAAAAGGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGG\n"
        ">gene_004|virulence_gene|length=1000\n"
        "ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT\n"
    )
    
    with open(genome_path, "w") as f:
        f.write(content)
    
    yield Path(tmpdir)
    
    # Cleanup
    import shutil
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_prodigal_output():
    """Mock the output of prodigal (gene prediction)."""
    # In a real scenario, this would parse GFF or FASTA output from prodigal.
    # Here we return a dictionary of gene sequences.
    return {
        "16S": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
        "rpoB": "GGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGGCCCCAAAATTTT",
        "gyrB": "TTTTAAAAGGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGGCCCCAAAATTTTGGGG",
        "virulence_gene": "ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT"
    }


# --- Tests ---

@pytest.mark.skipif(phylogeny is None, reason="src.analysis.phylogeny not yet implemented")
def test_extract_housekeeping_genes_success(temp_genome_dir, mock_prodigal_output):
    """
    Test that extract_housekeeping_genes correctly identifies and returns
    rpoB, gyrB, and 16S sequences from a genome file.
    """
    # This test assumes the implementation exists.
    # It verifies the filtering logic.
    expected_genes = {"16S", "rpoB", "gyrB"}
    result = phylogeny.extract_housekeeping_genes(
        genome_path=temp_genome_dir / "test_genome.fna",
        gene_db_path=str(temp_genome_dir / "genes.gff") # Mock path
    )
    
    # The result should be a dictionary of sequences
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_genes
    assert len(result["16S"]) > 0
    assert len(result["rpoB"]) > 0
    assert len(result["gyrB"]) > 0


@pytest.mark.skipif(phylogeny is None, reason="src.analysis.phylogeny not yet implemented")
def test_extract_housekeeping_genes_missing(temp_genome_dir):
    """
    Test behavior when housekeeping genes are missing from the genome.
    """
    # Create a genome with NO housekeeping genes
    empty_path = temp_genome_dir / "empty.fna"
    with open(empty_path, "w") as f:
        f.write(">virulence\nACGT\n")
    
    with pytest.raises(ValueError) as exc_info:
        phylogeny.extract_housekeeping_genes(
            genome_path=empty_path,
            gene_db_path=str(temp_genome_dir / "genes.gff")
        )
    
    assert "Missing housekeeping genes" in str(exc_info.value)


@pytest.mark.skipif(phylogeny is None, reason="src.analysis.phylogeny not yet implemented")
def test_align_sequences(temp_genome_dir, mock_prodigal_output):
    """
    Test that align_sequences performs multiple sequence alignment.
    """
    # Mock the alignment tool (e.g., MUSCLE or MAFFT)
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout=b"aligned.fasta", stderr=b"", returncode=0)
        
        sequences = [
            ("strain1", mock_prodigal_output["16S"]),
            ("strain2", mock_prodigal_output["16S"]),
            ("strain3", mock_prodigal_output["16S"])
        ]
        
        alignment_path = phylogeny.align_sequences(sequences, output_dir=temp_genome_dir)
        
        assert os.path.exists(alignment_path)
        mock_run.assert_called_once() # Verify external tool was called


@pytest.mark.skipif(phylogeny is None, reason="src.analysis.phylogeny not yet implemented")
def test_construct_tree(temp_genome_dir):
    """
    Test that construct_tree runs IQ-TREE and returns a Newick string.
    """
    mock_newick = "(strain1:0.1,strain2:0.2,strain3:0.3);"
    
    with patch('subprocess.run') as mock_run:
        # Mock IQ-TREE output
        mock_run.return_value = MagicMock(stdout=b"", stderr=b"", returncode=0)
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data=mock_newick)):
            tree_str = phylogeny.construct_tree(
                alignment_path=str(temp_genome_dir / "aligned.fasta"),
                output_dir=temp_genome_dir
            )
            
            assert tree_str == mock_newick
            mock_run.assert_called()


@pytest.mark.skipif(phylogeny is None, reason="src.analysis.phylogeny not yet implemented")
def test_validate_tree_structure(temp_genome_dir):
    """
    Test that validate_tree checks for rootedness and branch lengths.
    """
    valid_tree = "((A:0.1,B:0.2):0.3,C:0.4);"
    invalid_tree = "((A,B),C);" # No branch lengths
    
    assert phylogeny.validate_tree(valid_tree) is True
    assert phylogeny.validate_tree(invalid_tree) is False


@pytest.mark.skipif(phylogeny is None, reason="src.analysis.phylogeny not yet implemented")
def test_compute_phylogenetic_covariance(temp_genome_dir):
    """
    Test that compute_phylogenetic_covariance generates a valid matrix.
    """
    mock_newick = "(A:0.1,B:0.2);"
    
    # Mock the tree reading and covariance calculation
    with patch('src.analysis.phylogeny.Dendropy.Tree.get') as mock_tree_get:
        mock_tree = MagicMock()
        mock_tree.get = MagicMock(return_value=mock_newick)
        mock_tree_get.return_value = mock_tree
        
        # Mock the actual covariance calculation to return a simple matrix
        mock_matrix = np.array([[1.0, 0.5], [0.5, 1.0]])
        
        with patch('src.analysis.phylogeny.np.array', return_value=mock_matrix):
            cov_matrix = phylogeny.compute_phylogenetic_covariance(mock_newick)
            
            assert isinstance(cov_matrix, np.ndarray)
            assert cov_matrix.shape == (2, 2)
            assert np.allclose(cov_matrix, mock_matrix)


@pytest.mark.skipif(phylogeny is None, reason="src.analysis.phylogeny not yet implemented")
def test_full_pipeline_integration(temp_genome_dir, mock_prodigal_output):
    """
    Integration test for the full phylogeny pipeline:
    Extract -> Align -> Build Tree -> Validate -> Covariance.
    """
    # This test mocks all external heavy-lifting tools to ensure the
    # orchestration logic in the main function works correctly.
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout=b"", stderr=b"", returncode=0)
        
        with patch('builtins.open', mock_open(read_data="(A:0.1,B:0.2);")):
            with patch('src.analysis.phylogeny.compute_phylogenetic_covariance') as mock_cov:
                mock_cov.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])
                
                result = phylogeny.build_phylogeny(
                    genome_dir=temp_genome_dir,
                    output_dir=temp_genome_dir
                )
                
                assert "tree_path" in result
                assert "covariance_path" in result
                assert os.path.exists(result["tree_path"])
                assert os.path.exists(result["covariance_path"])