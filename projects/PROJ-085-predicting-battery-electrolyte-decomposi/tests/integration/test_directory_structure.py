import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.structure import (
    get_project_root,
    create_directory_structure,
    validate_directory_structure,
    get_data_paths
)
from code.data.checksum import (
    compute_sha256,
    save_checksums,
    register_file
)


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


def test_create_directory_structure(temp_project_root):
    """Test that create_directory_structure creates the required directories."""
    # Mock get_project_root to use our temp directory
    import code.data.structure as structure_module
    original_get_project_root = structure_module.get_project_root
    
    def mock_get_project_root():
        return temp_project_root
    
    structure_module.get_project_root = mock_get_project_root
    
    try:
        create_directory_structure()
        
        # Check that directories were created
        assert (temp_project_root / "data" / "raw").exists()
        assert (temp_project_root / "data" / "processed").exists()
        assert (temp_project_root / "data" / "validation").exists()
        
        # Check that .gitkeep files were created
        assert (temp_project_root / "data" / "raw" / ".gitkeep").exists()
        assert (temp_project_root / "data" / "processed" / ".gitkeep").exists()
        assert (temp_project_root / "data" / "validation" / ".gitkeep").exists()
    finally:
        structure_module.get_project_root = original_get_project_root


def test_validate_directory_structure(temp_project_root):
    """Test directory structure validation."""
    import code.data.structure as structure_module
    original_get_project_root = structure_module.get_project_root
    
    def mock_get_project_root():
        return temp_project_root
    
    structure_module.get_project_root = mock_get_project_root
    
    try:
        # Initially should fail
        assert validate_directory_structure() is False
        
        # Create structure
        create_directory_structure()
        
        # Now should pass
        assert validate_directory_structure() is True
        
        # Remove a directory
        (temp_project_root / "data" / "raw").rmdir()
        
        # Should fail again
        assert validate_directory_structure() is False
    finally:
        structure_module.get_project_root = original_get_project_root


def test_get_data_paths(temp_project_root):
    """Test that get_data_paths returns correct paths."""
    import code.data.structure as structure_module
    original_get_project_root = structure_module.get_project_root
    
    def mock_get_project_root():
        return temp_project_root
    
    structure_module.get_project_root = mock_get_project_root
    
    try:
        create_directory_structure()
        paths = get_data_paths()
        
        assert "raw" in paths
        assert "processed" in paths
        assert "validation" in paths
        
        assert paths["raw"] == temp_project_root / "data" / "raw"
        assert paths["processed"] == temp_project_root / "data" / "processed"
        assert paths["validation"] == temp_project_root / "data" / "validation"
    finally:
        structure_module.get_project_root = original_get_project_root


def test_checksum_integration(temp_project_root):
    """Integration test: create structure, add files, compute and validate checksums."""
    import code.data.structure as structure_module
    original_get_project_root = structure_module.get_project_root
    
    import code.data.checksum as checksum_module
    original_checksum_get_project_root = checksum_module.get_project_root
    
    def mock_get_project_root():
        return temp_project_root
    
    structure_module.get_project_root = mock_get_project_root
    checksum_module.get_project_root = mock_get_project_root
    
    try:
        # Create directory structure
        create_directory_structure()
        
        # Create test files
        raw_file = temp_project_root / "data" / "raw" / "test_data.csv"
        processed_file = temp_project_root / "data" / "processed" / "features.csv"
        
        raw_file.write_text("id,value\n1,100\n2,200")
        processed_file.write_text("feature1,feature2,target\n1.0,2.0,0.5")
        
        # Compute and register checksums
        checksums = {}
        checksums = register_file(raw_file, checksums)
        checksums = register_file(processed_file, checksums)
        
        # Save checksums
        save_checksums(checksums)
        
        # Validate checksums
        validation_results = validate_all_checksums()
        
        assert len(validation_results) == 2
        assert all(validation_results.values()), "All files should pass validation"
        
        # Modify a file and check validation fails
        raw_file.write_text("modified content")
        
        validation_results = validate_all_checksums()
        assert validation_results[str(raw_file)] is False, "Modified file should fail validation"
        assert validation_results[str(processed_file)] is True, "Unmodified file should pass validation"
    finally:
        structure_module.get_project_root = original_get_project_root
        checksum_module.get_project_root = original_checksum_get_project_root
