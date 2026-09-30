"""
Tests for quickstart validator script
"""
import pytest
import tempfile
import os
from pathlib import Path
import yaml
from code.quickstart_validator import (
    ValidationResult,
    check_directory_structure,
    check_config_files,
    check_state_files,
    check_output_artifacts
)

class TestValidationResult:
    """Tests for ValidationResult class."""
    
    def test_initial_state(self):
        """Test that ValidationResult initializes with empty lists."""
        result = ValidationResult()
        assert result.passed == []
        assert result.failed == []
        assert result.warnings == []
        assert result.is_successful()
        
    def test_add_pass(self):
        """Test adding a passed check."""
        result = ValidationResult()
        result.add_pass("test_check")
        assert "test_check" in result.passed
        assert len(result.passed) == 1
        
    def test_add_fail(self):
        """Test adding a failed check."""
        result = ValidationResult()
        result.add_fail("test_check", "reason")
        assert "test_check: reason" in result.failed
        assert not result.is_successful()
        
    def test_add_warning(self):
        """Test adding a warning check."""
        result = ValidationResult()
        result.add_warning("test_check", "reason")
        assert "test_check: reason" in result.warnings
        assert result.is_successful()  # Warnings don't cause failure

class TestDirectoryStructure:
    """Tests for directory structure validation."""
    
    def test_valid_structure(self):
        """Test validation with valid directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create required directories
            for dir_name in ['code', 'data/raw', 'data/processed', 'tests', 'state', 'docs']:
                (root / dir_name).mkdir(parents=True)
                
            result = check_directory_structure(root)
            assert len(result.failed) == 0
            assert len(result.passed) > 0
            
    def test_missing_directory(self):
        """Test validation with missing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Only create some directories
            (root / 'code').mkdir()
            
            result = check_directory_structure(root)
            assert len(result.failed) > 0
            assert any('data/raw' in f for f in result.failed)

class TestConfigFiles:
    """Tests for configuration file validation."""
    
    def test_requirements_exists(self):
        """Test validation when requirements.txt exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            req_file = root / 'requirements.txt'
            req_file.write_text('numpy\nscipy\npandas\n')
            
            result = check_config_files(root)
            assert any('requirements.txt exists' in p for p in result.passed)
            
    def test_requirements_missing(self):
        """Test validation when requirements.txt is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            result = check_config_files(root)
            assert any('requirements.txt exists' in f for f in result.failed)

class TestStateFiles:
    """Tests for state file validation."""
    
    def test_state_file_exists(self):
        """Test validation when state file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_dir = root / 'state' / 'projects'
            state_dir.mkdir(parents=True)
            state_file = state_dir / 'PROJ-204-quantifying-the-impact-of-spatial-correl.yaml'
            state_file.write_text('artifact_hashes: {}\n')
            
            result = check_state_files(root)
            assert any('Project state file exists' in p for p in result.passed)
            
    def test_state_file_missing(self):
        """Test validation when state file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            result = check_state_files(root)
            assert any('Project state file exists' in f for f in result.failed)

class TestOutputArtifacts:
    """Tests for output artifact validation."""
    
    def test_unified_dataset_exists(self):
        """Test validation when unified dataset exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            processed_dir = root / 'data' / 'processed'
            processed_dir.mkdir(parents=True)
            dataset_file = processed_dir / 'unified_dataset.csv'
            dataset_file.write_text('sample_id,PCE,J_sc,V_oc\n1,0.2,10,1.0\n')
            
            result = check_output_artifacts(root)
            assert any('unified_dataset.csv exists' in p for p in result.passed)
            
    def test_unified_dataset_missing(self):
        """Test validation when unified dataset is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            result = check_output_artifacts(root)
            assert any('unified_dataset.csv exists' in w for w in result.warnings)