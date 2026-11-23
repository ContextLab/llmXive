"""
Test module for visualize_pathways functionality.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modeling.visualize_pathways import load_json_file, save_json_file, aggregate_pathway_scores, plot_pathway_importance

@pytest.fixture
def sample_pathway_data():
    """Sample pathway data for testing."""
    return {
        "pathway_mappings": [
            {"pathway_name": "Phenylpropanoid biosynthesis", "database_source": "KEGG"},
            {"pathway_name": "Phenylpropanoid biosynthesis", "database_source": "KEGG"},
            {"pathway_name": "Flavonoid biosynthesis", "database_source": "MetaCyc"},
            {"pathway_name": "Phenylpropanoid biosynthesis", "database_source": "MetaCyc"},
            {"pathway_name": "Terpenoid biosynthesis", "database_source": "KEGG"}
        ],
        "narrative_report": "Test report",
        "framing": "associational"
    }

@pytest.fixture
def empty_pathway_data():
    """Empty pathway data for testing."""
    return {
        "pathway_mappings": [],
        "narrative_report": "Test report",
        "framing": "associational"
    }

def test_aggregate_pathway_scores_with_data(sample_pathway_data):
    """Test aggregation with valid pathway data."""
    df = aggregate_pathway_scores(sample_pathway_data)
    
    assert not df.empty
    assert 'pathway_name' in df.columns
    assert 'frequency' in df.columns
    assert 'importance' in df.columns
    
    # Check that Phenylpropanoid biosynthesis appears 3 times
    phenylpropanoid = df[df['pathway_name'] == 'Phenylpropanoid biosynthesis']
    assert len(phenylpropanoid) == 1
    assert phenylpropanoid.iloc[0]['frequency'] == 3

def test_aggregate_pathway_scores_empty(empty_pathway_data):
    """Test aggregation with empty pathway data."""
    df = aggregate_pathway_scores(empty_pathway_data)
    
    assert df.empty
    assert len(df) == 0

def test_plot_pathway_importance_creates_file(sample_pathway_data, tmp_path):
    """Test that plot function creates a file."""
    df = aggregate_pathway_scores(sample_pathway_data)
    output_path = tmp_path / "test_plot.png"
    
    plot_pathway_importance(df, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_pathway_importance_empty_data(empty_pathway_data, tmp_path):
    """Test plot function with empty data creates placeholder."""
    df = aggregate_pathway_scores(empty_pathway_data)
    output_path = tmp_path / "test_plot_empty.png"
    
    plot_pathway_importance(df, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0