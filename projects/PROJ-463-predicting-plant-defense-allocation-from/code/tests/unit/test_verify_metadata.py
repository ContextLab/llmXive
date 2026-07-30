"""
Unit tests for metadata verification module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.verify_metadata import (
    fetch_sra_metadata,
    extract_required_metadata,
    verify_metadata_requirements,
    verify_fastq_metadata,
    verify_synthetic_metadata,
    save_verification_report
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_fastq_file(temp_dir):
    """Create a sample FASTQ file for testing."""
    fastq_path = temp_dir / 'SRX123456.fastq.gz'
    # Create an empty file to simulate FASTQ
    fastq_path.touch()
    return fastq_path


@pytest.fixture
def sample_manifest(temp_dir):
    """Create a sample manifest file."""
    manifest_path = temp_dir / 'real_data_manifest.json'
    manifest_data = {
        'SRX123456': {
            'accession_id': 'SRX123456',
            'tissue': 'leaf',
            'treatment': 'herbivore',
            'species': 'Arabidopsis thaliana',
            'replicates': 3
        }
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    return manifest_path


@pytest.fixture
def sample_synthetic_manifest(temp_dir):
    """Create a sample synthetic manifest."""
    manifest_path = temp_dir / 'synthetic_manifest.json'
    manifest_data = {
        'accession_id': 'SYNTH_001',
        'source_type': 'synthetic',
        'organism': 'Arabidopsis thaliana'
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    return manifest_path


def test_extract_required_metadata_basic():
    """Test extraction of basic metadata fields."""
    raw_metadata = {
        'accession': 'SRX123456',
        'study_accession': 'SRP123456',
        'attributes': [
            {'key': 'tissue', 'value': 'leaf'},
            {'key': 'treatment', 'value': 'herbivore'},
            {'key': 'species', 'value': 'Arabidopsis thaliana'}
        ]
    }
    
    extracted = extract_required_metadata(raw_metadata)
    
    assert extracted['accession_id'] == 'SRX123456'
    assert extracted['tissue'] == 'leaf'
    assert extracted['treatment'] == 'herbivore'
    assert extracted['species'] == 'Arabidopsis thaliana'


def test_extract_required_metadata_from_title():
    """Test metadata extraction from title when attributes missing."""
    raw_metadata = {
        'accession': 'SRX123456',
        'title': 'Leaf herbivory response in Arabidopsis',
        'attributes': []
    }
    
    extracted = extract_required_metadata(raw_metadata)
    
    assert extracted['tissue'] == 'leaf'
    assert extracted['treatment'] == 'herbivore'


def test_verify_metadata_requirements_valid():
    """Test verification with valid metadata."""
    metadata = {
        'tissue': 'leaf',
        'treatment': 'herbivore',
        'species': 'Arabidopsis thaliana',
        'replicates': 3
    }
    
    is_valid, reasons = verify_metadata_requirements(metadata)
    
    assert is_valid is True
    assert len(reasons) == 0


def test_verify_metadata_requirements_missing_tissue():
    """Test verification with missing tissue."""
    metadata = {
        'tissue': None,
        'treatment': 'herbivore',
        'species': 'Arabidopsis thaliana',
        'replicates': 3
    }
    
    is_valid, reasons = verify_metadata_requirements(metadata)
    
    assert is_valid is False
    assert 'Missing tissue metadata' in reasons


def test_verify_metadata_requirements_insufficient_replicates():
    """Test verification with insufficient replicates."""
    metadata = {
        'tissue': 'leaf',
        'treatment': 'herbivore',
        'species': 'Arabidopsis thaliana',
        'replicates': 1
    }
    
    is_valid, reasons = verify_metadata_requirements(metadata)
    
    assert is_valid is False
    assert any('Insufficient replicates' in r for r in reasons)


def test_verify_fastq_metadata(sample_fastq_file, sample_manifest, temp_dir):
    """Test FASTQ metadata verification."""
    # Create a mock for fetch_sra_metadata
    with patch('src.data.verify_metadata.fetch_sra_metadata') as mock_fetch:
        mock_fetch.return_value = {
            'accession': 'SRX123456',
            'attributes': [
                {'key': 'tissue', 'value': 'leaf'},
                {'key': 'treatment', 'value': 'herbivore'},
                {'key': 'species', 'value': 'Arabidopsis thaliana'}
            ]
        }
        
        results = verify_fastq_metadata([sample_fastq_file], sample_manifest)
        
        assert len(results) == 1
        assert results[0]['accession_id'] == 'SRX123456'
        assert results[0]['file_exists'] is True
        assert results[0]['metadata_fetched'] is True
        assert results[0]['metadata_valid'] is True
        assert len(results[0]['exclusion_reasons']) == 0


def test_verify_synthetic_metadata(sample_synthetic_manifest):
    """Test synthetic metadata verification."""
    results = verify_synthetic_metadata(sample_synthetic_manifest)
    
    assert len(results) == 1
    assert results[0]['accession_id'] == 'SYNTH_001'
    assert results[0]['file_exists'] is True
    assert results[0]['metadata_valid'] is True
    assert len(results[0]['exclusion_reasons']) == 0
    assert results[0]['metadata']['species'] == 'Arabidopsis thaliana'


def test_save_verification_report(temp_dir):
    """Test saving verification report."""
    results = [
        {
            'accession_id': 'SRX123456',
            'file_path': '/tmp/test.fastq.gz',
            'file_exists': True,
            'metadata_fetched': True,
            'metadata_valid': True,
            'exclusion_reasons': [],
            'metadata': {'tissue': 'leaf'}
        },
        {
            'accession_id': 'SRX789012',
            'file_path': '/tmp/test2.fastq.gz',
            'file_exists': True,
            'metadata_fetched': False,
            'metadata_valid': False,
            'exclusion_reasons': ['Missing tissue metadata'],
            'metadata': {}
        }
    ]
    
    output_path = temp_dir / 'verification_report.json'
    save_verification_report(results, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report['total_studies'] == 2
    assert report['valid_studies'] == 1
    assert report['excluded_studies'] == 1
    assert 'SRX789012' in report['summary']['excluded_accessions']
    assert 'Missing tissue metadata' in report['summary']['by_reason']


def test_verify_fastq_metadata_missing_file(temp_dir):
    """Test verification when FASTQ file is missing."""
    missing_file = temp_dir / 'nonexistent.fastq.gz'
    manifest_path = temp_dir / 'manifest.json'
    manifest_path.touch()
    
    results = verify_fastq_metadata([missing_file], manifest_path)
    
    assert len(results) == 1
    assert results[0]['file_exists'] is False
    assert 'FASTQ file not found' in results[0]['exclusion_reasons']