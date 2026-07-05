"""
Unit tests for T020: update_state.py functionality.
"""
import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
from code.ingestion import update_state


class TestLoadChecksums:
    """Tests for load_checksums function."""
    
    def test_load_valid_checksums(self, tmp_path):
        """Test loading valid checksums file."""
        checksum_file = tmp_path / "checksums.txt"
        content = """
        # Sample checksums
        abc123def456  data/intermediate/merged.csv
        789xyz012345  data/provenance/dft_queries.jsonl
        """
        checksum_file.write_text(content.strip())
        
        result = update_state.load_checksums(checksum_file)
        
        assert len(result) == 2
        assert result["data/intermediate/merged.csv"] == "abc123def456"
        assert result["data/provenance/dft_queries.jsonl"] == "789xyz012345"
    
    def test_load_empty_file(self, tmp_path):
        """Test loading empty checksums file."""
        checksum_file = tmp_path / "checksums.txt"
        checksum_file.write_text("")
        
        result = update_state.load_checksums(checksum_file)
        
        assert result == {}
    
    def test_load_missing_file(self, tmp_path):
        """Test loading non-existent checksums file."""
        checksum_file = tmp_path / "nonexistent.txt"
        
        result = update_state.load_checksums(checksum_file)
        
        assert result == {}
    
    def test_load_malformed_lines(self, tmp_path):
        """Test handling of malformed checksum lines."""
        checksum_file = tmp_path / "checksums.txt"
        content = """
        valid_hash  valid/path.csv
        malformed_line_without_hash
        another_valid  another/path.json
        """
        checksum_file.write_text(content.strip())
        
        result = update_state.load_checksums(checksum_file)
        
        assert len(result) == 2
        assert "valid/path.csv" in result
        assert "another/path.json" in result


class TestLoadOrCreateState:
    """Tests for load_or_create_state function."""
    
    def test_load_existing_state(self, tmp_path):
        """Test loading existing state file."""
        state_file = tmp_path / "state.yaml"
        existing_state = {
            "project_id": "PROJ-537",
            "status": "in_progress",
            "artifacts": {"old.csv": "hash123"}
        }
        state_file.write_text(yaml.dump(existing_state))
        
        result = update_state.load_or_create_state(state_file)
        
        assert result["project_id"] == "PROJ-537"
        assert result["status"] == "in_progress"
        assert "old.csv" in result["artifacts"]
    
    def test_create_new_state(self, tmp_path):
        """Test creating new state file when none exists."""
        state_file = tmp_path / "nonexistent.yaml"
        
        result = update_state.load_or_create_state(state_file)
        
        assert result["project_id"] == "PROJ-537-predicting-the-yield-strength-of-bcc-ste"
        assert result["status"] == "in_progress"
        assert "artifacts" in result
        assert result["last_updated"] is None


class TestUpdateStateWithChecksums:
    """Tests for update_state_with_checksums function."""
    
    def test_update_with_checksums(self):
        """Test updating state with checksums."""
        state = {
            "project_id": "PROJ-537",
            "artifacts": {"existing.csv": {"hash": "old"}}
        }
        checksums = {
            "new.csv": "hash123",
            "another.json": "hash456"
        }
        
        result = update_state.update_state_with_checksums(state, checksums)
        
        assert "last_updated" in result
        assert "new.csv" in result["artifacts"]
        assert result["artifacts"]["new.csv"]["hash"] == "hash123"
        assert result["artifacts"]["another.json"]["hash"] == "hash456"
    
    def test_create_artifacts_if_missing(self):
        """Test that artifacts section is created if missing."""
        state = {"project_id": "PROJ-537"}
        checksums = {"file.csv": "hash123"}
        
        result = update_state.update_state_with_checksums(state, checksums)
        
        assert "artifacts" in result
        assert "file.csv" in result["artifacts"]


class TestSaveState:
    """Tests for save_state function."""
    
    def test_save_state_creates_directory(self, tmp_path):
        """Test that save_state creates parent directories."""
        state = {"project_id": "PROJ-537"}
        state_file = tmp_path / "nested" / "dir" / "state.yaml"
        
        update_state.save_state(state, state_file)
        
        assert state_file.exists()
    
    def test_save_state_valid_yaml(self, tmp_path):
        """Test that saved state is valid YAML."""
        state = {"project_id": "PROJ-537", "status": "done"}
        state_file = tmp_path / "state.yaml"
        
        update_state.save_state(state, state_file)
        
        with open(state_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded == state


class TestMain:
    """Tests for main function."""
    
    @patch('code.ingestion.update_state.load_checksums')
    @patch('code.ingestion.update_state.load_or_create_state')
    @patch('code.ingestion.update_state.update_state_with_checksums')
    @patch('code.ingestion.update_state.save_state')
    def test_main_success(self, mock_save, mock_update, mock_load_state, mock_load_checksums, tmp_path):
        """Test successful main execution."""
        mock_load_checksums.return_value = {"file.csv": "hash123"}
        mock_load_state.return_value = {"project_id": "PROJ-537"}
        mock_update.return_value = {"project_id": "PROJ-537", "artifacts": {"file.csv": {}}}
        
        with patch('code.ingestion.update_state.CONFIG') as mock_config:
            mock_config.PROVENANCE_DIR = str(tmp_path)
            mock_config.STATE_DIR = str(tmp_path / "state")
            
            result = update_state.main()
        
        assert result == 0
        mock_load_checksums.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('code.ingestion.update_state.load_checksums')
    def test_main_no_checksums(self, mock_load_checksums, tmp_path):
        """Test main when no checksums are found."""
        mock_load_checksums.return_value = {}
        
        with patch('code.ingestion.update_state.CONFIG') as mock_config:
            mock_config.PROVENANCE_DIR = str(tmp_path)
            mock_config.STATE_DIR = str(tmp_path / "state")
            
            result = update_state.main()
        
        assert result == 1