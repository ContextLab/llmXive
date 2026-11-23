"""
Unit tests for the base configuration loader in code/__init__.py.
"""
import pytest
import yaml
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import load_metadata, get_metadata_value, PROJECT_ROOT, METADATA_PATH

class TestLoadMetadata:
    def test_metadata_file_exists(self):
        """Verify that metadata.yaml exists in the expected location."""
        assert METADATA_PATH.exists(), f"Metadata file missing at {METADATA_PATH}"

    def test_load_metadata_returns_dict(self):
        """Verify load_metadata returns a dictionary."""
        metadata = load_metadata()
        assert isinstance(metadata, dict)

    def test_metadata_contains_required_sections(self):
        """Verify metadata contains expected top-level keys."""
        metadata = load_metadata()
        required_keys = ['project', 'data', 'models', 'analysis', 'paths']
        for key in required_keys:
            assert key in metadata, f"Missing required key '{key}' in metadata"

    def test_project_name_matches(self):
        """Verify project name in metadata matches expected value."""
        metadata = load_metadata()
        assert metadata['project']['name'] == 'PROJ-076-assessing-the-validity-of-modified-newto'

    def test_mond_a0_value(self):
        """Verify MOND a0 constant is loaded correctly."""
        metadata = load_metadata()
        assert metadata['models']['mond']['a0'] == 1.2e-10

    def test_analysis_thresholds(self):
        """Verify analysis thresholds are loaded correctly."""
        metadata = load_metadata()
        assert metadata['analysis']['inclination_threshold'] == 10.0
        assert metadata['analysis']['min_points'] == 15
        assert metadata['analysis']['alpha'] == 0.05

class TestGetMetadataValue:
    def test_flat_key_access(self):
        """Test accessing a top-level key."""
        value = get_metadata_value('data.source')
        assert value == 'SPARC'

    def test_nested_key_access(self):
        """Test accessing a deeply nested key."""
        value = get_metadata_value('models.mond.interpolating_function')
        assert value == 'simple'

    def test_nonexistent_key_returns_default(self):
        """Test that missing keys return the default value."""
        value = get_metadata_value('nonexistent.key', default='fallback')
        assert value == 'fallback'

    def test_nested_nonexistent_key(self):
        """Test missing nested key returns default."""
        value = get_metadata_value('models.nfw.nonexistent_param', default=0)
        assert value == 0

    def test_chi2_thresholds_list(self):
        """Test retrieving a list from metadata."""
        thresholds = get_metadata_value('analysis.chi2_thresholds')
        assert isinstance(thresholds, list)
        assert 1.0 in thresholds
        assert 1.25 in thresholds
        assert 1.5 in thresholds
        assert 1.75 in thresholds

    def test_path_retrieval(self):
        """Test retrieving file paths from metadata."""
        raw_data_path = get_metadata_value('paths.raw_data')
        assert raw_data_path == 'data/raw/sparc_data.zip'