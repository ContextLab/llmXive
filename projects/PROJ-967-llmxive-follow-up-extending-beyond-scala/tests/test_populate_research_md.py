import json
import os
import tempfile
from pathlib import Path
import pytest
import subprocess
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
sys.path.insert(0, 'code')
from populate_research_md import update_research_md, update_config_json, run_verification

class TestUpdateResearchMd:
    def test_updates_existing_entry(self, tmp_path):
        research_md = tmp_path / "research.md"
        initial_content = """# Research Log
        verified_datasets:
          - dataset_id: "z-reward"
            title_token_overlap: 0.0
            checksum: "old"
            verification_date: "2023-01-01"
            source_type: "unknown"
        """
        research_md.write_text(initial_content)
        
        verification_data = {
            "title_token_overlap": 0.85,
            "checksum": "new_checksum_123",
            "source_type": "real"
        }
        
        update_research_md(research_md, verification_data)
        
        content = research_md.read_text()
        assert "0.85" in content
        assert "new_checksum_123" in content
        assert "real" in content
        assert "old" not in content

    def test_appends_new_entry_if_missing(self, tmp_path):
        research_md = tmp_path / "research.md"
        initial_content = """# Research Log
        """
        research_md.write_text(initial_content)
        
        verification_data = {
            "title_token_overlap": 0.90,
            "checksum": "new_checksum_456",
            "source_type": "real"
        }
        
        update_research_md(research_md, verification_data)
        
        content = research_md.read_text()
        assert "verified_datasets:" in content
        assert "0.90" in content
        assert "new_checksum_456" in content

class TestUpdateConfigJson:
    def test_writes_synthetic_flag_when_source_is_synthetic(self, tmp_path):
        project_root = tmp_path
        config_path = project_root / "data/processed" / "config.json"
        lineage_path = project_root / "data/processed" / "lineage_report.json"
        
        # Create lineage report to satisfy SC-004
        lineage_path.parent.mkdir(parents=True, exist_ok=True)
        lineage_path.write_text(json.dumps([]))
        
        verification_data = {
            "source_type": "synthetic"
        }
        
        update_config_json(config_path, verification_data, project_root)
        
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert data.get("IS_SYNTHETIC_RUN") is True

    def test_raises_error_if_synthetic_but_no_lineage(self, tmp_path):
        project_root = tmp_path
        config_path = project_root / "data/processed" / "config.json"
        # Do NOT create lineage_report.json
        
        verification_data = {
            "source_type": "synthetic"
        }
        
        with pytest.raises(RuntimeError, match="SC-004 Violation"):
            update_config_json(config_path, verification_data, project_root)

    def test_does_not_write_flag_when_source_is_real(self, tmp_path):
        project_root = tmp_path
        config_path = project_root / "data/processed" / "config.json"
        
        verification_data = {
            "source_type": "real"
        }
        
        update_config_json(config_path, verification_data, project_root)
        
        assert not config_path.exists()

class TestRunVerification:
    @patch('populate_research_md.subprocess.run')
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"title_token_overlap": 0.7, "checksum": "abc", "source_type": "real"}',
            stderr=""
        )
        
        data = run_verification("Z-Reward", 0.7, "cosine-tfidf")
        
        assert data["title_token_overlap"] == 0.7
        assert data["source_type"] == "real"
        mock_run.assert_called_once()

    @patch('populate_research_md.subprocess.run')
    def test_failure_exit_code(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error occurred"
        )
        
        with pytest.raises(RuntimeError, match="Command failed"):
            run_verification("Z-Reward", 0.7, "cosine-tfidf")

    @patch('populate_research_md.subprocess.run')
    def test_invalid_json(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not json",
            stderr=""
        )
        
        with pytest.raises(RuntimeError, match="Output is not valid JSON"):
            run_verification("Z-Reward", 0.7, "cosine-tfidf")