import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validate_prompt_orderings import (
    load_prompt_manifest,
    extract_ordering_key,
    validate_no_duplicates,
    main
)

@pytest.fixture
def temp_manifest_file():
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        manifest_data = {
            'entries': [
                {
                    'seed': 42,
                    'strategy': 'logical_ascending',
                    'examples': [
                        {'id': 'ex_001'},
                        {'id': 'ex_002'},
                        {'id': 'ex_003'}
                    ]
                },
                {
                    'seed': 123,
                    'strategy': 'logical_ascending',
                    'examples': [
                        {'id': 'ex_004'},
                        {'id': 'ex_005'},
                        {'id': 'ex_006'}
                    ]
                },
                {
                    'seed': 456,
                    'strategy': 'logical_random',
                    'examples': [
                        {'id': 'ex_007'},
                        {'id': 'ex_008'},
                        {'id': 'ex_009'}
                    ]
                }
            ]
        }
        json.dump(manifest_data, f)
        f.flush()
        yield Path(f.name)
        os.unlink(f.name)

@pytest.fixture
def duplicate_manifest_file():
    """Create a temporary manifest file with duplicate orderings."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        manifest_data = {
            'entries': [
                {
                    'seed': 42,
                    'strategy': 'logical_ascending',
                    'examples': [
                        {'id': 'ex_001'},
                        {'id': 'ex_002'},
                        {'id': 'ex_003'}
                    ]
                },
                {
                    'seed': 123,
                    'strategy': 'logical_ascending',
                    'examples': [
                        {'id': 'ex_001'},
                        {'id': 'ex_002'},
                        {'id': 'ex_003'}
                    ]
                },
                {
                    'seed': 456,
                    'strategy': 'logical_random',
                    'examples': [
                        {'id': 'ex_007'},
                        {'id': 'ex_008'},
                        {'id': 'ex_009'}
                    ]
                }
            ]
        }
        json.dump(manifest_data, f)
        f.flush()
        yield Path(f.name)
        os.unlink(f.name)

def test_load_prompt_manifest_success(temp_manifest_file):
    """Test successful loading of a valid manifest file."""
    manifest = load_prompt_manifest(temp_manifest_file)
    
    assert 'entries' in manifest
    assert len(manifest['entries']) == 3
    assert manifest['entries'][0]['seed'] == 42

def test_load_prompt_manifest_not_found():
    """Test loading a non-existent manifest file."""
    with pytest.raises(FileNotFoundError):
        load_prompt_manifest(Path('/nonexistent/path/manifest.json'))

def test_load_prompt_manifest_invalid_json():
    """Test loading a manifest with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json {')
        f.flush()
        temp_path = Path(f.name)
    
    with pytest.raises(json.JSONDecodeError):
        load_prompt_manifest(temp_path)
    
    os.unlink(temp_path)

def test_extract_ordering_key():
    """Test extraction of ordering key from an entry."""
    entry = {
        'seed': 42,
        'strategy': 'logical_ascending',
        'examples': [
            {'id': 'ex_001'},
            {'id': 'ex_002'}
        ]
    }
    
    key = extract_ordering_key(entry)
    
    assert key == 'logical_ascending:("ex_001", "ex_002")' or key == 'logical_ascending:(\'ex_001\', \'ex_002\')'
    # The exact format depends on Python version, but it should contain the strategy and example IDs

def test_validate_no_duplicates_no_duplicates(temp_manifest_file):
    """Test validation when there are no duplicates."""
    manifest = load_prompt_manifest(temp_manifest_file)
    is_valid, duplicates, _ = validate_no_duplicates(manifest)
    
    assert is_valid is True
    assert len(duplicates) == 0

def test_validate_no_duplicates_with_duplicates(duplicate_manifest_file):
    """Test validation when duplicates exist."""
    manifest = load_prompt_manifest(duplicate_manifest_file)
    is_valid, duplicates, duplicate_details = validate_no_duplicates(manifest)
    
    assert is_valid is False
    assert len(duplicates) == 1
    assert 'logical_ascending' in duplicates[0]
    assert '42' in duplicates[0] or '123' in duplicates[0]
    
    assert 'logical_ascending' in duplicate_details
    assert len(duplicate_details['logical_ascending']) == 1

def test_validate_no_duplicates_different_strategies_same_ordering():
    """Test that different strategies can have the same ordering without flagging."""
    manifest = {
        'entries': [
            {
                'seed': 42,
                'strategy': 'logical_ascending',
                'examples': [
                    {'id': 'ex_001'},
                    {'id': 'ex_002'}
                ]
            },
            {
                'seed': 123,
                'strategy': 'logical_random',
                'examples': [
                    {'id': 'ex_001'},
                    {'id': 'ex_002'}
                ]
            }
        ]
    }
    
    is_valid, duplicates, _ = validate_no_duplicates(manifest)
    
    assert is_valid is True
    assert len(duplicates) == 0

def test_main_success(temp_manifest_file):
    """Test main function with valid manifest."""
    output_path = Path(tempfile.mktemp(suffix='.json'))
    
    try:
        with patch('sys.argv', ['validate_prompt_orderings', '--manifest', str(temp_manifest_file), '--output', str(output_path)]):
            main()
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert report['is_valid'] is True
    finally:
        if output_path.exists():
            os.unlink(output_path)

def test_main_duplicate_detection(duplicate_manifest_file):
    """Test main function detects duplicates and exits with error."""
    output_path = Path(tempfile.mktemp(suffix='.json'))
    
    try:
        with patch('sys.argv', ['validate_prompt_orderings', '--manifest', str(duplicate_manifest_file), '--output', str(output_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert report['is_valid'] is False
    finally:
        if output_path.exists():
            os.unlink(output_path)

def test_main_file_not_found():
    """Test main function handles missing manifest file."""
    with patch('sys.argv', ['validate_prompt_orderings', '--manifest', '/nonexistent/path.json']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
