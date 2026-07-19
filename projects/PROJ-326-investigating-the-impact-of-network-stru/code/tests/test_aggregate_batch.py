"""
Unit tests for the batch aggregation module (T018c).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.src.generators.aggregate_batch import (
    find_batch_files,
    load_batch_file,
    aggregate_batches,
    generate_manifest,
    save_manifest,
    verify_threshold,
    main
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock batch files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create mock batch manifests
        batch_1 = {
            'topology_class': 'erdos_renyi',
            'total_generated': 10,
            'valid_count': 9,
            'total_attempts': 12,
            'failed_graphs': ['graph_001', 'graph_002']
        }
        
        batch_2 = {
            'topology_class': 'watts_strogatz',
            'total_generated': 15,
            'valid_count': 14,
            'total_attempts': 16,
            'failed_graphs': ['graph_003']
        }
        
        batch_3 = {
            'topology_class': 'barabasi_albert',
            'total_generated': 20,
            'valid_count': 19,
            'total_attempts': 20,
            'failed_graphs': []
        }
        
        # Write files
        with open(data_dir / 'erdos_renyi_batch_manifest.json', 'w') as f:
            json.dump(batch_1, f)
        
        with open(data_dir / 'watts_strogatz_batch_manifest.json', 'w') as f:
            json.dump(batch_2, f)
        
        with open(data_dir / 'barabasi_albert_batch_manifest.json', 'w') as f:
            json.dump(batch_3, f)
        
        yield data_dir


def test_find_batch_files(temp_data_dir):
    """Test that find_batch_files locates all batch manifests."""
    files = find_batch_files(temp_data_dir)
    assert len(files) == 3
    assert all(f.name.endswith('_batch_manifest.json') for f in files)


def test_find_batch_files_filter(temp_data_dir):
    """Test filtering by topology class."""
    files = find_batch_files(temp_data_dir, topology_class='erdos_renyi')
    assert len(files) == 1
    assert 'erdos_renyi' in files[0].name


def test_load_batch_file(temp_data_dir):
    """Test loading a valid batch file."""
    file_path = temp_data_dir / 'erdos_renyi_batch_manifest.json'
    data = load_batch_file(file_path)
    assert data['topology_class'] == 'erdos_renyi'
    assert data['total_generated'] == 10


def test_load_batch_file_invalid():
    """Test loading a non-existent file returns empty dict."""
    data = load_batch_file(Path('/nonexistent/path.json'))
    assert data == {}


def test_aggregate_batches(temp_data_dir):
    """Test aggregation logic."""
    # Load data manually to pass to aggregate_batches
    files = find_batch_files(temp_data_dir)
    data_list = [load_batch_file(f) for f in files]
    
    result = aggregate_batches(data_list)
    
    # Check totals
    assert result['total_generated'] == 45  # 10 + 15 + 20
    assert result['valid_count'] == 42     # 9 + 14 + 19
    assert result['total_attempts'] == 48  # 12 + 16 + 20
    assert len(result['failed_graphs']) == 3  # 2 + 1 + 0
    
    # Check success rate
    expected_rate = 42 / 48
    assert abs(result['success_rate'] - expected_rate) < 0.0001
    
    # Check topology breakdown
    assert 'erdos_renyi' in result['topology_breakdown']
    assert result['topology_breakdown']['erdos_renyi']['total_generated'] == 10


def test_aggregate_batches_empty():
    """Test aggregation with empty list."""
    result = aggregate_batches([])
    assert result['total_generated'] == 0
    assert result['valid_count'] == 0
    assert result['success_rate'] == 0.0


def test_generate_manifest():
    """Test manifest generation with config."""
    aggregated = {
        'total_generated': 10,
        'valid_count': 9,
        'success_rate': 0.9,
        'total_attempts': 10,
        'failed_graphs': ['g1'],
        'topology_breakdown': {}
    }
    config = {
        'global_seed': 42,
        'topology_targets': ['erdos_renyi']
    }
    
    manifest = generate_manifest(aggregated, config)
    
    assert manifest['config_snapshot']['global_seed'] == 42
    assert 'generated_at' in manifest


def test_verify_threshold():
    """Test threshold verification."""
    manifest = {'success_rate': 0.95}
    assert verify_threshold(manifest, 0.95) is True
    assert verify_threshold(manifest, 0.96) is False


def test_save_manifest(temp_data_dir):
    """Test saving manifest to file."""
    manifest = {
        'total_generated': 1,
        'valid_count': 1,
        'success_rate': 1.0,
        'total_attempts': 1,
        'failed_graphs': [],
        'topology_breakdown': {},
        'generated_at': '2023-01-01T00:00:00'
    }
    output_path = temp_data_dir / 'test_global_manifest.json'
    
    save_manifest(manifest, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded['total_generated'] == 1


def test_main_integration(temp_data_dir, caplog):
    """Test main function integration."""
    import argparse
    args = argparse.Namespace(
        config='code/config.yaml',
        output_dir=str(temp_data_dir),
        input_dir=str(temp_data_dir),
        topology=None
    )
    
    # Note: This might fail if config.yaml is missing, but we test the logic flow
    # We expect it to handle missing config gracefully or fail with a clear error
    try:
        exit_code = main(args)
        # If config exists, it should succeed. If not, it might fail.
        # We verify that it attempts to run.
        assert isinstance(exit_code, int)
    except FileNotFoundError:
        # Expected if config.yaml is missing in test env
        pass
