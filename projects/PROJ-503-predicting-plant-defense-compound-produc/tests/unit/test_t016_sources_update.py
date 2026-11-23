"""
Unit tests for T016: update_sources_yaml.py

Tests verify that:
1. The script correctly reads the pairing feasibility report
2. The script validates pairing rate >= 95%
3. The script updates sources.yaml with correct dataset information
4. The script raises E-PAIRING if pairing rate < 95%
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.update_sources_yaml import (
    load_pairing_feasibility_report,
    validate_pairing_rate,
    update_sources_yaml,
    main
)
from code.exceptions import E_PAIRING


class TestT016SourcesUpdate:
    """Test suite for T016 sources update functionality."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for testing."""
        logs_dir = tmp_path / 'logs'
        data_dir = tmp_path / 'data'
        logs_dir.mkdir()
        data_dir.mkdir()
        return {'logs': logs_dir, 'data': data_dir}

    @pytest.fixture
    def mock_pairing_report(self, temp_dirs):
        """Create a mock pairing feasibility report."""
        report = {
            'pairing_rate': 0.98,
            'total_samples': 45,
            'matched_samples': 44,
            'unmatched_samples': 1,
            'status': 'passed'
        }
        report_file = temp_dirs['logs'] / 'pairing_feasibility.json'
        with open(report_file, 'w') as f:
            json.dump(report, f)
        return report_file

    @pytest.fixture
    def mock_pairing_report_failure(self, temp_dirs):
        """Create a mock pairing feasibility report that fails."""
        report = {
            'pairing_rate': 0.85,
            'total_samples': 45,
            'matched_samples': 38,
            'unmatched_samples': 7,
            'status': 'failed'
        }
        report_file = temp_dirs['logs'] / 'pairing_feasibility.json'
        with open(report_file, 'w') as f:
            json.dump(report, f)
        return report_file

    def test_load_pairing_feasibility_report_success(self, mock_pairing_report):
        """Test successful loading of pairing feasibility report."""
        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', mock_pairing_report):
            report = load_pairing_feasibility_report()
            assert report['pairing_rate'] == 0.98
            assert report['total_samples'] == 45
            assert report['status'] == 'passed'

    def test_load_pairing_feasibility_report_not_found(self, temp_dirs):
        """Test error when pairing feasibility report is not found."""
        non_existent_file = temp_dirs['logs'] / 'non_existent.json'
        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', non_existent_file):
            with pytest.raises(E_PAIRING):
                load_pairing_feasibility_report()

    def test_validate_pairing_rate_success(self, mock_pairing_report):
        """Test validation passes when pairing rate >= 95%."""
        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', mock_pairing_report):
            report = load_pairing_feasibility_report()
            result = validate_pairing_rate(report)
            assert result is True

    def test_validate_pairing_rate_failure(self, mock_pairing_report_failure):
        """Test validation fails when pairing rate < 95%."""
        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', mock_pairing_report_failure):
            report = load_pairing_feasibility_report()
            with pytest.raises(E_PAIRING):
                validate_pairing_rate(report)

    def test_update_sources_yaml_creates_file(self, temp_dirs, mock_pairing_report):
        """Test that update_sources_yaml creates the sources.yaml file."""
        sources_file = temp_dirs['data'] / 'sources.yaml'

        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', mock_pairing_report):
            with patch('code.update_sources_yaml.SOURCES_YAML_FILE', sources_file):
                report = load_pairing_feasibility_report()
                validate_pairing_rate(report)
                update_sources_yaml(report)

        assert sources_file.exists()

        # Verify file content
        with open(sources_file, 'r') as f:
            content = yaml.safe_load(f)

        assert 'project' in content
        assert 'datasets' in content
        assert 'validation' in content
        assert 'verification_log' in content

        # Verify project info
        assert content['project']['name'] == 'PROJ-503-predicting-plant-defense-compound-produc'

        # Verify dataset sources
        assert 'expression' in content['datasets']
        assert 'metabolite' in content['datasets']
        assert len(content['datasets']['expression']['sources']) > 0
        assert len(content['datasets']['metabolite']['sources']) > 0

        # Verify verification log
        assert content['verification_log']['task_id'] == 'T016'
        assert content['verification_log']['status'] == 'completed'

    def test_update_sources_yaml_with_existing_file(self, temp_dirs, mock_pairing_report):
        """Test that update_sources_yaml updates existing sources.yaml."""
        sources_file = temp_dirs['data'] / 'sources.yaml'

        # Create initial file
        initial_content = {
            'project': {'name': 'old_project', 'version': '0.0.1'},
            'old_section': {'data': 'should be overwritten'}
        }
        with open(sources_file, 'w') as f:
            yaml.dump(initial_content, f)

        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', mock_pairing_report):
            with patch('code.update_sources_yaml.SOURCES_YAML_FILE', sources_file):
                report = load_pairing_feasibility_report()
                validate_pairing_rate(report)
                update_sources_yaml(report)

        # Verify file was updated
        with open(sources_file, 'r') as f:
            content = yaml.safe_load(f)

        assert content['project']['name'] == 'PROJ-503-predicting-plant-defense-compound-produc'
        assert 'old_section' not in content  # Old data should be replaced
        assert 'verification_log' in content

    def test_main_function_success(self, temp_dirs, mock_pairing_report):
        """Test main function executes successfully."""
        sources_file = temp_dirs['data'] / 'sources.yaml'

        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', mock_pairing_report):
            with patch('code.update_sources_yaml.SOURCES_YAML_FILE', sources_file):
                result = main()
                assert result == 0
                assert sources_file.exists()

    def test_main_function_failure(self, temp_dirs, mock_pairing_report_failure):
        """Test main function raises E-PAIRING on failure."""
        sources_file = temp_dirs['data'] / 'sources.yaml'

        with patch('code.update_sources_yaml.PAIRING_FEASIBILITY_FILE', mock_pairing_report_failure):
            with patch('code.update_sources_yaml.SOURCES_YAML_FILE', sources_file):
                with pytest.raises(E_PAIRING):
                    main()
                # File should not be created on failure
                assert not sources_file.exists()