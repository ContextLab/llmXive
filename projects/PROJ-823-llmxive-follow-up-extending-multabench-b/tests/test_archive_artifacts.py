"""
Tests for the archive_artifacts pipeline.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from pipelines.archive_artifacts import (
    find_all_artifacts,
    extract_run_id,
    normalize_filename,
    compute_file_hash,
    create_archive_manifest,
    archive_artifacts
)

@pytest.fixture
def temp_artifacts_dir():
    """Create a temporary directory with sample artifact files."""
    temp_dir = tempfile.mkdtemp()
    artifacts_dir = Path(temp_dir) / 'artifacts'
    artifacts_dir.mkdir()
    
    # Create sample files with various naming conventions
    sample_files = [
        'embeddings_run_001.parquet',
        'metrics_conditioned_run_001.json',
        'frozen_baseline_aggregated_run_001.json',
        'correlation_report_run_001.json',
        'embeddings_run_002.parquet',
        'data_integrity_report_run_002.json',
        'metadata_stats_summary.csv',  # No run_id in name
        '.hidden_file.txt',  # Should be ignored
    ]
    
    for filename in sample_files:
        file_path = artifacts_dir / filename
        with open(file_path, 'w') as f:
            f.write(f"Content of {filename}")
    
    yield artifacts_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_find_all_artifacts(temp_artifacts_dir):
    """Test finding all artifact files."""
    artifacts = find_all_artifacts(temp_artifacts_dir)
    
    # Should find all non-hidden files
    assert len(artifacts) == 7  # 7 non-hidden files
    
    # Verify no hidden files are included
    hidden_files = [f for f in artifacts if f.name.startswith('.')]
    assert len(hidden_files) == 0

def test_extract_run_id():
    """Test run_id extraction from various filename patterns."""
    test_cases = [
        ('embeddings_run_001.parquet', 'run_001'),
        ('metrics_conditioned_run_001.json', 'run_001'),
        ('frozen_baseline_aggregated_run_001.json', 'run_001'),
        ('correlation_report_run_001.json', 'run_001'),
        ('data_integrity_report_run_002.json', 'run_002'),
        ('metadata_stats_summary.csv', None),  # No run_id pattern
    ]
    
    for filename, expected_run_id in test_cases:
        filepath = Path(filename)
        run_id = extract_run_id(filepath)
        assert run_id == expected_run_id, f"Failed for {filename}: expected {expected_run_id}, got {run_id}"

def test_extract_run_id_timestamp():
    """Test run_id extraction from timestamp-based filenames."""
    test_cases = [
        ('embeddings_2024-01-15T10-30-00.parquet', '2024-01-15T10-30-00'),
        ('metrics_2024-01-15T10-30-00.json', '2024-01-15T10-30-00'),
    ]
    
    for filename, expected_run_id in test_cases:
        filepath = Path(filename)
        run_id = extract_run_id(filepath)
        assert run_id == expected_run_id, f"Failed for {filename}: expected {expected_run_id}, got {run_id}"

def test_normalize_filename():
    """Test filename normalization with run_id."""
    test_cases = [
        ('embeddings.parquet', 'run_001', 'embeddings_run_001.parquet'),
        ('metrics_run_001.json', 'run_001', 'metrics_run_001.json'),  # Already has run_id
        ('data.csv', None, 'data.csv'),  # No run_id provided
    ]
    
    for original, run_id, expected in test_cases:
        filepath = Path(original)
        normalized = normalize_filename(filepath, run_id)
        assert normalized == expected, f"Failed for {original}: expected {expected}, got {normalized}"

def test_compute_file_hash():
    """Test file hash computation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash1 = compute_file_hash(temp_path)
        hash2 = compute_file_hash(temp_path)
        
        # Same content should produce same hash
        assert hash1 == hash2
        
        # Hash should be a valid hex string
        assert len(hash1) == 64  # SHA256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in hash1)
    finally:
        os.unlink(temp_path)

def test_create_archive_manifest():
    """Test manifest creation."""
    artifacts = [
        {
            'original_path': '/src/file1.parquet',
            'archived_path': '/dst/run_001/file1.parquet',
            'filename': 'file1.parquet',
            'run_id': 'run_001',
            'size_bytes': 1024,
            'hash': 'abc123',
            'created_at': '2024-01-15T10:30:00'
        }
    ]
    
    archive_path = Path('/dst/archive.zip')
    run_ids = ['run_001', 'run_002']
    
    manifest = create_archive_manifest(artifacts, archive_path, run_ids)
    
    assert manifest['total_artifacts'] == 1
    assert manifest['run_ids'] == sorted(run_ids)
    assert 'archive_version' in manifest
    assert 'created_at' in manifest

def test_archive_artifacts(temp_artifacts_dir):
    """Test full archive process."""
    output_dir = Path(tempfile.mkdtemp())
    
    try:
        manifest_path = archive_artifacts(temp_artifacts_dir, output_dir)
        
        # Verify manifest exists
        assert manifest_path.exists()
        
        # Verify manifest content
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert 'artifacts' in manifest
        assert 'total_artifacts' in manifest
        assert manifest['total_artifacts'] > 0
        
        # Verify archived files exist
        for artifact_info in manifest['artifacts']:
            archived_path = Path(artifact_info['archived_path'])
            assert archived_path.exists(), f"Archived file missing: {archived_path}"
        
        # Verify directory structure by run_id
        run_ids = manifest['run_ids']
        for run_id in run_ids:
            run_dir = output_dir / run_id
            assert run_dir.exists(), f"Run directory missing: {run_dir}"
            
    finally:
        shutil.rmtree(output_dir)

def test_archive_artifacts_with_run_id_filter(temp_artifacts_dir):
    """Test archiving with specific run_id filter."""
    output_dir = Path(tempfile.mkdtemp())
    
    try:
        # Only archive run_001
        manifest_path = archive_artifacts(
            temp_artifacts_dir, 
            output_dir,
            include_run_ids=['run_001']
        )
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Should only include run_001 artifacts
        assert 'run_001' in manifest['run_ids']
        assert 'run_002' not in manifest['run_ids']
        
        # Verify all archived artifacts are from run_001
        for artifact_info in manifest['artifacts']:
            assert artifact_info['run_id'] == 'run_001'
            
    finally:
        shutil.rmtree(output_dir)

def test_archive_artifacts_empty_directory():
    """Test archiving when no artifacts exist."""
    temp_dir = tempfile.mkdtemp()
    artifacts_dir = Path(temp_dir) / 'artifacts'
    artifacts_dir.mkdir()
    
    output_dir = Path(tempfile.mkdtemp())
    
    try:
        manifest_path = archive_artifacts(artifacts_dir, output_dir)
        
        # Should create manifest even with no artifacts
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Should indicate error or empty state
        assert manifest.get('total_artifacts', 0) == 0
        
    finally:
        shutil.rmtree(temp_dir)
        shutil.rmtree(output_dir)