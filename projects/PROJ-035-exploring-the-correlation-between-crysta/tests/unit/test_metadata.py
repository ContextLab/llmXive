"""
Unit tests for metadata generation module.

Tests for src/utils/metadata.py covering:
- generate_metadata function
- save_metadata and load_metadata functions
- CLI entry point
- Edge cases and error handling
"""

import os
import sys
import json
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.metadata import (
    generate_metadata,
    save_metadata,
    load_metadata,
    main
)
from src.utils.seed_manager import reset_seed


class TestGenerateMetadata:
    """Tests for generate_metadata function."""
    
    def setup_method(self):
        """Reset seed before each test."""
        reset_seed()
    
    def test_generate_metadata_default_values(self):
        """Test metadata generation with default values."""
        metadata = generate_metadata()
        
        assert metadata["project_id"] == "PROJ-035-exploring-the-correlation-between-crysta"
        assert metadata["dataset_name"] == "perovskite_thermal_conductivity"
        assert "generated_at" in metadata
        assert "version" in metadata
        assert "sources" in metadata
        assert "compliance" in metadata
        
        # Check default seed
        assert metadata["seed"] == 42
    
    def test_generate_metadata_custom_date(self):
        """Test metadata generation with custom API query date."""
        custom_date = "2024-01-15"
        metadata = generate_metadata(api_query_date=custom_date)
        
        assert metadata["version"]["api_query_date"] == custom_date
        assert metadata["sources"]["materials_project"]["query_date"] == custom_date
        assert metadata["sources"]["nist_thermal"]["download_date"] == custom_date
    
    def test_generate_metadata_custom_tag(self):
        """Test metadata generation with custom repository tag."""
        custom_tag = "v1.2.0"
        metadata = generate_metadata(repository_tag=custom_tag)
        
        assert metadata["version"]["repository_tag"] == custom_tag
    
    def test_generate_metadata_with_data_sources(self):
        """Test metadata generation with custom data sources."""
        custom_sources = {
            "materials_project": {
                "api_version": "2023.9.1",
                "record_count": 150,
                "filter_criteria": "ABX3_perovskite"
            },
            "nist_thermal": {
                "repository": "NIST-MDR-2023",
                "release_tag": "r2023.10",
                "entry_count": 89,
                "provenance": "peer_reviewed"
            },
            "literature": {
                "citations": ["Smith et al., Advanced Materials, 2021"],
                "total_entries": 12,
                "verification_status": "verified"
            }
        }
        
        metadata = generate_metadata(data_sources=custom_sources)
        
        # Check materials project source
        assert metadata["sources"]["materials_project"]["api_version"] == "2023.9.1"
        assert metadata["sources"]["materials_project"]["record_count"] == 150
        
        # Check NIST source
        assert metadata["sources"]["nist_thermal"]["repository"] == "NIST-MDR-2023"
        assert metadata["sources"]["nist_thermal"]["entry_count"] == 89
        
        # Check literature source
        assert len(metadata["sources"]["literature"]["citations"]) == 1
        assert metadata["sources"]["literature"]["total_entries"] == 12
    
    def test_generate_metadata_seed(self):
        """Test metadata generation with custom seed."""
        metadata = generate_metadata(seed=123)
        assert metadata["seed"] == 123
    
    def test_generate_metadata_compliance(self):
        """Test that compliance flags are set correctly."""
        metadata = generate_metadata()
        
        assert metadata["compliance"]["constitution_vii"] is True
        assert metadata["compliance"]["fr_010_provenance"] is True
        assert metadata["compliance"]["data_lineage"] == "tracked"
    
    def test_generate_metadata_structure_completeness(self):
        """Test that all required fields are present in metadata."""
        metadata = generate_metadata()
        
        required_keys = [
            "project_id", "dataset_name", "generated_at", "version",
            "seed", "sources", "compliance", "checksums", "metadata_version"
        ]
        
        for key in required_keys:
            assert key in metadata, f"Missing required key: {key}"
        
        # Check version sub-keys
        version_keys = ["repository_tag", "api_query_date", "schema_version"]
        for key in version_keys:
            assert key in metadata["version"], f"Missing version key: {key}"
        
        # Check sources structure
        assert "materials_project" in metadata["sources"]
        assert "nist_thermal" in metadata["sources"]
        assert "literature" in metadata["sources"]

class TestSaveAndLoadMetadata:
    """Tests for save_metadata and load_metadata functions."""
    
    def test_save_and_load_metadata(self):
        """Test saving and loading metadata."""
        metadata = generate_metadata()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            save_metadata(metadata, temp_path)
            loaded = load_metadata(temp_path)
            
            assert loaded == metadata
            assert loaded["project_id"] == metadata["project_id"]
        finally:
            os.unlink(temp_path)
    
    def test_save_metadata_creates_directories(self):
        """Test that save_metadata creates parent directories."""
        metadata = generate_metadata()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "subdir", "nested", "metadata.yaml")
            
            save_metadata(metadata, output_path)
            assert os.path.exists(output_path)
    
    def test_load_metadata_file_not_found(self):
        """Test load_metadata raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_metadata("/nonexistent/path/metadata.yaml")
    
    def test_save_metadata_invalid_path(self):
        """Test save_metadata raises IOError for invalid path."""
        metadata = generate_metadata()
        
        with pytest.raises(IOError):
            save_metadata(metadata, "/root/invalid_path/metadata.yaml")

class TestMainFunction:
    """Tests for main CLI entry point."""
    
    def test_main_default_execution(self):
        """Test main function with default arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "metadata.yaml")
            
            sys.argv = ["metadata.py", "--output", output_path]
            result = main()
            
            assert result == 0
            assert os.path.exists(output_path)
            
            # Verify file content
            metadata = load_metadata(output_path)
            assert metadata["project_id"] == "PROJ-035-exploring-the-correlation-between-crysta"
    
    def test_main_with_custom_date(self):
        """Test main function with custom API date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "metadata.yaml")
            custom_date = "2024-01-15"
            
            sys.argv = ["metadata.py", "--output", output_path, "--api-date", custom_date]
            result = main()
            
            assert result == 0
            metadata = load_metadata(output_path)
            assert metadata["version"]["api_query_date"] == custom_date
    
    def test_main_with_custom_tag(self):
        """Test main function with custom repository tag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "metadata.yaml")
            custom_tag = "v2.0.0"
            
            sys.argv = ["metadata.py", "--output", output_path, "--tag", custom_tag]
            result = main()
            
            assert result == 0
            metadata = load_metadata(output_path)
            assert metadata["version"]["repository_tag"] == custom_tag
    
    def test_main_with_data_sources_json(self):
        """Test main function with data sources JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "metadata.yaml")
            
            data_sources = {
                "materials_project": {"record_count": 200},
                "nist_thermal": {"entry_count": 100}
            }
            data_sources_json = json.dumps(data_sources)
            
            sys.argv = ["metadata.py", "--output", output_path, "--data-sources", data_sources_json]
            result = main()
            
            assert result == 0
            metadata = load_metadata(output_path)
            assert metadata["sources"]["materials_project"]["record_count"] == 200
            assert metadata["sources"]["nist_thermal"]["entry_count"] == 100
    
    def test_main_invalid_json(self):
        """Test main function with invalid JSON."""
        sys.argv = ["metadata.py", "--data-sources", "invalid json"]
        
        with patch('src.utils.metadata.setup_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            result = main()
            
            assert result == 1
    
    def test_main_with_seed(self):
        """Test main function with custom seed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "metadata.yaml")
            
            sys.argv = ["metadata.py", "--output", output_path, "--seed", "999"]
            result = main()
            
            assert result == 0
            metadata = load_metadata(output_path)
            assert metadata["seed"] == 999

class TestMetadataCompliance:
    """Tests for Constitution VII and FR-010 compliance."""
    
    def test_constitution_vii_compliance(self):
        """Test that metadata satisfies Constitution VII requirements."""
        metadata = generate_metadata()
        
        # Constitution VII requires version tracking
        assert "version" in metadata
        assert "api_query_date" in metadata["version"]
        assert "repository_tag" in metadata["version"]
        
        # Data lineage must be tracked
        assert metadata["compliance"]["data_lineage"] == "tracked"
    
    def test_fr_010_provenance_tracking(self):
        """Test that metadata satisfies FR-010 provenance requirements."""
        custom_sources = {
            "nist_thermal": {
                "provenance": "peer_reviewed",
                "repository": "NIST-MDR"
            },
            "literature": {
                "verification_status": "verified"
            }
        }
        
        metadata = generate_metadata(data_sources=custom_sources)
        
        # FR-010 requires peer-reviewed provenance
        assert metadata["compliance"]["fr_010_provenance"] is True
        assert metadata["sources"]["nist_thermal"]["provenance"] == "peer_reviewed"
        assert metadata["sources"]["literature"]["verification_status"] == "verified"
    
    def test_checksum_tracking(self):
        """Test that checksums field is present for future tracking."""
        metadata = generate_metadata()
        
        assert "checksums" in metadata
        assert "raw_data" in metadata["checksums"]
        assert "cleaned_data" in metadata["checksums"]
        assert "descriptors" in metadata["checksums"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
