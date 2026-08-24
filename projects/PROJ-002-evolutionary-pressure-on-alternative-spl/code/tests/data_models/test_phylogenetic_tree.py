import pytest
import tempfile
import os
from pathlib import Path
from code.data_models.phylogenetic_tree import PhylogeneticTree

@pytest.fixture
def temp_tree_file():
    """Creates a temporary Newick file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.nwk', delete=False) as f:
        f.write("((Human:0.1, Chimp:0.1):0.2, Macaque:0.3);")
        return f.name

@pytest.fixture
def temp_tree_dir():
    """Creates a temporary directory for testing directory rejection."""
    return tempfile.mkdtemp()

def test_phylogenetic_tree_creation(temp_tree_file):
    """Test basic creation of PhylogeneticTree."""
    tree = PhylogeneticTree(
        tree_file_path=temp_tree_file,
        source="test_source"
    )
    assert tree.tree_file_path == temp_tree_file
    assert tree.source == "test_source"
    assert tree.topology_hash is not None
    assert len(tree.topology_hash) == 64  # SHA-256 hex length

def test_phylogenetic_tree_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        PhylogeneticTree(
            tree_file_path="/nonexistent/path/tree.nwk",
            source="test"
        )

def test_phylogenetic_tree_hash_verification(temp_tree_file):
    """Test that the hash matches the file content."""
    import hashlib
    with open(temp_tree_file, "rb") as f:
        expected_hash = hashlib.sha256(f.read()).hexdigest()
    
    tree = PhylogeneticTree(
        tree_file_path=temp_tree_file,
        source="test"
    )
    assert tree.topology_hash == expected_hash

def test_phylogenetic_tree_to_dict(temp_tree_file):
    """Test serialization to dictionary."""
    tree = PhylogeneticTree(
        tree_file_path=temp_tree_file,
        source="custom"
    )
    data = tree.to_dict()
    assert data["tree_file_path"] == temp_tree_file
    assert data["source"] == "custom"
    assert "topology_hash" in data

def test_phylogenetic_tree_from_dict(temp_tree_file):
    """Test deserialization from dictionary."""
    data = {
        "tree_file_path": temp_tree_file,
        "source": "custom",
        "topology_hash": "dummy_hash" # Should be recalculated
    }
    tree = PhylogeneticTree.from_dict(data)
    assert tree.tree_file_path == temp_tree_file
    assert tree.source == "custom"
    # Verify hash was recalculated and matches actual file, not dummy
    import hashlib
    with open(temp_tree_file, "rb") as f:
        expected_hash = hashlib.sha256(f.read()).hexdigest()
    assert tree.topology_hash == expected_hash
    assert tree.topology_hash != "dummy_hash"

def test_phylogenetic_tree_directory_not_file(temp_tree_dir):
    """Test that ValueError is raised if path is a directory."""
    with pytest.raises(ValueError):
        PhylogeneticTree(
            tree_file_path=temp_tree_dir,
            source="test"
        )