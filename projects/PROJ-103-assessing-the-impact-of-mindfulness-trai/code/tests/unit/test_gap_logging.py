"""
Unit tests for gap logging functionality.

Tests cover gap record creation, logging, loading, grouping, and
documentation generation.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.utils.gap_logging import (
    create_gap_record,
    log_gap,
    load_all_gaps,
    group_gaps_by_type,
    generate_gap_summary,
    generate_methods_documentation,
    log_and_document_gaps,
    GapLoggingError
)


class TestCreateGapRecord:
    """Tests for create_gap_record function."""

    def test_create_basic_gap_record(self):
        """Test creating a basic gap record with required fields."""
        record = create_gap_record(
            dataset_id='ds000001',
            gap_type='missing_post_scan'
        )

        assert record['dataset_id'] == 'ds000001'
        assert record['gap_type'] == 'missing_post_scan'
        assert 'timestamp' in record
        assert record['severity'] == 'medium'
        assert record['details'] == {}

    def test_create_gap_record_with_details(self):
        """Test creating a gap record with additional details."""
        details = {'reason': 'Participant dropout', 'scan_date': '2023-05-15'}
        record = create_gap_record(
            dataset_id='ds000001',
            gap_type='missing_post_scan',
            details=details,
            severity='high'
        )

        assert record['details'] == details
        assert record['severity'] == 'high'

    def test_create_gap_record_all_types(self):
        """Test creating gap records for all gap types."""
        gap_types = [
            'missing_pre_scan',
            'missing_post_scan',
            'missing_metadata',
            'design_mismatch',
            'motion_exceeded',
            'preprocessing_failed',
            'atlas_mismatch',
            'scan_quality_low',
            'intervention_type_unknown'
        ]

        for gap_type in gap_types:
            record = create_gap_record(
                dataset_id='ds000001',
                gap_type=gap_type
            )
            assert record['gap_type'] == gap_type


class TestLogGap:
    """Tests for log_gap function."""

    def test_log_gap_creates_file(self):
        """Test that log_gap creates a JSON file."""
        record = create_gap_record('ds000001', 'missing_post_scan')

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = log_gap(record, Path(tmpdir))

            assert output_path.exists()
            assert output_path.suffix == '.json'

            # Verify file content
            with open(output_path, 'r') as f:
                loaded = json.load(f)

            assert loaded['dataset_id'] == 'ds000001'
            assert loaded['gap_type'] == 'missing_post_scan'

    def test_log_gap_filename_format(self):
        """Test that log_gap creates files with correct naming convention."""
        record = create_gap_record('ds000001', 'motion_exceeded')

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = log_gap(record, Path(tmpdir))

            filename = output_path.name
            assert filename.startswith('gap_ds000001_motion_exceeded_')
            assert filename.endswith('.json')

    def test_log_gap_creates_directory(self):
        """Test that log_gap creates the output directory if it doesn't exist."""
        record = create_gap_record('ds000001', 'missing_post_scan')

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / 'processed' / 'gaps'
            output_path = log_gap(record, nested_dir)

            assert nested_dir.exists()
            assert output_path.exists()


class TestLoadAllGaps:
    """Tests for load_all_gaps function."""

    def test_load_all_gaps_empty_directory(self):
        """Test loading gaps from an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gaps = load_all_gaps(Path(tmpdir))
            assert gaps == []

    def test_load_all_gaps_multiple_files(self):
        """Test loading multiple gap files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample gap files
            for i in range(3):
                record = create_gap_record(f'ds00000{i}', 'missing_post_scan')
                with open(Path(tmpdir) / f'gap_ds00000{i}_missing_post_scan_001.json', 'w') as f:
                    json.dump(record, f)

            gaps = load_all_gaps(Path(tmpdir))
            assert len(gaps) == 3

    def test_load_all_gaps_invalid_json(self):
        """Test handling of invalid JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid file
            record = create_gap_record('ds000001', 'missing_post_scan')
            with open(Path(tmpdir) / 'gap_ds000001_missing_post_scan_001.json', 'w') as f:
                json.dump(record, f)

            # Create an invalid file
            with open(Path(tmpdir) / 'gap_ds000002_missing_post_scan_001.json', 'w') as f:
                f.write('invalid json {{{')

            gaps = load_all_gaps(Path(tmpdir))
            # Should load the valid one, skip the invalid one
            assert len(gaps) == 1


class TestGroupGapsByType:
    """Tests for group_gaps_by_type function."""

    def test_group_gaps_by_type(self):
        """Test grouping gaps by their type."""
        gaps = [
            create_gap_record('ds000001', 'missing_post_scan'),
            create_gap_record('ds000002', 'missing_post_scan'),
            create_gap_record('ds000003', 'motion_exceeded'),
            create_gap_record('ds000004', 'missing_pre_scan'),
        ]

        grouped = group_gaps_by_type(gaps)

        assert len(grouped) == 3
        assert len(grouped['missing_post_scan']) == 2
        assert len(grouped['motion_exceeded']) == 1
        assert len(grouped['missing_pre_scan']) == 1

    def test_group_gaps_empty(self):
        """Test grouping empty list."""
        grouped = group_gaps_by_type([])
        assert grouped == {}


class TestGenerateGapSummary:
    """Tests for generate_gap_summary function."""

    def test_generate_summary(self):
        """Test generating a gap summary."""
        gaps = [
            create_gap_record('ds000001', 'missing_post_scan', severity='high'),
            create_gap_record('ds000002', 'missing_post_scan', severity='medium'),
            create_gap_record('ds000003', 'motion_exceeded', severity='low'),
        ]

        summary = generate_gap_summary(gaps)

        assert summary['total_gaps'] == 3
        assert summary['by_type']['missing_post_scan'] == 2
        assert summary['by_type']['motion_exceeded'] == 1
        assert summary['by_severity']['high'] == 1
        assert summary['by_severity']['medium'] == 1
        assert summary['by_severity']['low'] == 1
        assert len(summary['affected_datasets']) == 3

    def test_generate_summary_empty(self):
        """Test generating summary for empty list."""
        summary = generate_gap_summary([])
        assert summary['total_gaps'] == 0
        assert summary['by_type'] == {}
        assert summary['by_severity'] == {}
        assert summary['affected_datasets'] == []


class TestGenerateMethodsDocumentation:
    """Tests for generate_methods_documentation function."""

    def test_generate_documentation_creates_file(self):
        """Test that documentation file is created."""
        gaps = [
            create_gap_record('ds000001', 'missing_post_scan', severity='high'),
            create_gap_record('ds000002', 'motion_exceeded', severity='medium'),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
          output_path = Path(tmpdir) / 'gaps.md'
          result_path = generate_methods_documentation(gaps, output_path)

          assert result_path.exists()
          assert result_path.suffix == '.md'

    def test_generate_documentation_content(self):
        """Test that documentation contains expected content."""
        gaps = [
            create_gap_record('ds000001', 'missing_post_scan', severity='high'),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gaps.md'
            generate_methods_documentation(gaps, output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            assert '# Dataset Gaps and Missing Data Documentation' in content
            assert '## Overview' in content
            assert '## Gap Summary by Type' in content
            assert '## Detailed Gap Records' in content
            assert 'ds000001' in content
            assert 'missing_post_scan' in content

    def test_generate_documentation_empty_gaps(self):
        """Test documentation generation with no gaps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'gaps.md'
            generate_methods_documentation([], output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            assert '0' in content  # Total gaps should be 0
            assert 'No gaps recorded' in content


class TestLogAndDocumentGaps:
    """Tests for log_and_document_gaps function."""

    def test_log_and_document_gaps(self):
        """Test the combined logging and documentation function."""
        gaps = [
            create_gap_record('ds000001', 'missing_post_scan'),
            create_gap_record('ds000002', 'motion_exceeded'),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'logs'
            docs_path = Path(tmpdir) / 'docs.md'

            result = log_and_document_gaps(gaps, log_dir, docs_path)

            assert len(result['logged_files']) == 2
            assert result['documentation'].exists()

            # Verify all gaps were logged
            for path in result['logged_files']:
                assert path.exists()


class TestGapLoggingIntegration:
    """Integration tests for gap logging workflow."""

    def test_full_workflow(self):
        """Test the complete gap logging workflow."""
        # Create sample gaps
        sample_gaps = [
            create_gap_record(
                dataset_id='ds000001',
                gap_type='missing_post_scan',
                details={'reason': 'Dropout'},
                severity='high'
            ),
            create_gap_record(
                dataset_id='ds000002',
                gap_type='motion_exceeded',
                details={'max_mm': 4.2},
                severity='medium'
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / 'gaps'
            docs_path = Path(tmpdir) / 'gaps.md'

            # Log and document
            result = log_and_document_gaps(sample_gaps, log_dir, docs_path)

            # Verify individual files
            assert len(result['logged_files']) == 2
            for path in result['logged_files']:
                assert path.exists()
                with open(path, 'r') as f:
                    data = json.load(f)
                    assert 'timestamp' in data
                    assert 'dataset_id' in data
                    assert 'gap_type' in data

            # Verify documentation
            assert docs_path.exists()
            with open(docs_path, 'r') as f:
                doc_content = f.read()
                assert 'Dataset Gaps' in doc_content
                assert 'ds000001' in doc_content
                assert 'ds000002' in doc_content