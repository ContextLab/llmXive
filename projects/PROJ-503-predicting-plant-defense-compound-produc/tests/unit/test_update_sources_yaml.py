"""
Unit tests for update_sources_yaml utility.
Verifies that sources.yaml is correctly updated with acquisition metadata.
"""
import json
import pytest
import yaml
from pathlib import Path
from datetime import datetime
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from utils.update_sources_yaml import (
    load_sources_yaml,
    update_expression_source,
    update_metabolite_source,
    save_sources_yaml
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_FILE = PROJECT_ROOT / "data" / "sources.yaml"

@pytest.fixture
def backup_sources():
    """Backup and restore sources.yaml for test isolation."""
    if SOURCES_FILE.exists():
        backup_content = SOURCES_FILE.read_text()
        yield
        SOURCES_FILE.write_text(backup_content)
    else:
        yield

def test_load_sources_yaml_exists():
    """Test that load_sources_yaml successfully reads the file."""
    data = load_sources_yaml()
    assert 'datasets' in data
    assert 'expression' in data['datasets']
    assert 'metabolite' in data['datasets']
    assert 'validation' in data

def test_load_sources_yaml_structure():
    """Test that the loaded YAML has the expected structure."""
    data = load_sources_yaml()
    
    # Check expression sources
    assert 'sources' in data['datasets']['expression']
    sources = data['datasets']['expression']['sources']
    assert isinstance(sources, list)
    assert len(sources) >= 2  # GSE21857 and GSE167633
    
    # Check metabolite sources
    assert 'sources' in data['datasets']['metabolite']
    m_sources = data['datasets']['metabolite']['sources']
    assert isinstance(m_sources, list)
    assert len(m_sources) >= 1  # ST002565

def test_update_expression_source(backup_sources):
    """Test updating an expression source with acquisition metadata."""
    accession = "GSE21857"
    checksum = "abc123def456"
    script_ver = "v1.0.0"
    
    update_expression_source(accession, "2024-01-01T00:00:00Z", checksum, script_ver)
    
    data = load_sources_yaml()
    found = False
    for source in data['datasets']['expression']['sources']:
        if source['accession_id'] == accession:
            assert source['download_date'] == "2024-01-01T00:00:00Z"
            assert source['checksum'] == checksum
            assert source['preprocessing_script_version'] == script_ver
            assert source['download_status'] == 'completed'
            found = True
            break
    
    assert found, f"Source {accession} not found after update"

def test_update_metabolite_source(backup_sources):
    """Test updating a metabolite source with acquisition metadata."""
    accession = "ST002565"
    checksum = "xyz789uvw012"
    script_ver = "v2.0.0"
    
    update_metabolite_source(accession, "2024-02-01T00:00:00Z", checksum, script_ver)
    
    data = load_sources_yaml()
    found = False
    for source in data['datasets']['metabolite']['sources']:
        if source['accession_id'] == accession:
            assert source['download_date'] == "2024-02-01T00:00:00Z"
            assert source['checksum'] == checksum
            assert source['preprocessing_script_version'] == script_ver
            assert source['download_status'] == 'completed'
            found = True
            break
    
    assert found, f"Source {accession} not found after update"

def test_update_nonexistent_expression_source(backup_sources):
    """Test that updating a nonexistent expression source raises ValueError."""
    with pytest.raises(ValueError, match="Expression source.*not found"):
        update_expression_source("GSE99999", "2024-01-01T00:00:00Z", "checksum", "v1")

def test_update_nonexistent_metabolite_source(backup_sources):
    """Test that updating a nonexistent metabolite source raises ValueError."""
    with pytest.raises(ValueError, match="Metabolite source.*not found"):
        update_metabolite_source("ST99999", "2024-01-01T00:00:00Z", "checksum", "v1")

def test_yaml_valid_syntax(backup_sources):
    """Ensure the updated file is valid YAML."""
    update_expression_source("GSE21857", "2024-01-01T00:00:00Z", "checksum", "v1")
    
    # Re-read and parse to ensure validity
    with open(SOURCES_FILE, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data is not None
    assert 'datasets' in data
