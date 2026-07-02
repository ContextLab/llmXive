"""
Unit tests for T001: Verify sources.yaml syntax and structure.
"""
import os
import yaml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES_FILE = os.path.join(PROJECT_ROOT, "data", "sources.yaml")

@pytest.fixture
def sources_data():
    if not os.path.exists(SOURCES_FILE):
        pytest.skip("sources.yaml not found")
    with open(SOURCES_FILE, 'r') as f:
        return yaml.safe_load(f)

def test_yaml_syntax(sources_data):
    """Verify the file is valid YAML and loads without error."""
    assert sources_data is not None
    assert "sources" in sources_data
    assert isinstance(sources_data["sources"], list)

def test_required_sources_present(sources_data):
    """Verify both GEO and Metabolomics Workbench sources are defined."""
    source_names = [s["name"] for s in sources_data["sources"]]
    assert "NCBI Gene Expression Omnibus (GEO)" in source_names
    assert "Metabolomics Workbench" in source_names

def test_geo_criteria_structure(sources_data):
    """Verify GEO search criteria has required fields."""
    geo_source = next((s for s in sources_data["sources"] if "GEO" in s["name"]), None)
    assert geo_source is not None
    assert "search_criteria" in geo_source
    assert "keywords" in geo_source["search_criteria"]
    assert "organism" in geo_source["search_criteria"]
    assert len(geo_source["search_criteria"]["keywords"]) > 0

def test_metabolomics_criteria_structure(sources_data):
    """Verify Metabolomics Workbench criteria has required fields."""
    mw_source = next((s for s in sources_data["sources"] if "Metabolomics Workbench" in s["name"]), None)
    assert mw_source is not None
    assert "search_criteria" in mw_source
    assert "keywords" in mw_source["search_criteria"]
    assert len(mw_source["search_criteria"]["keywords"]) > 0

def test_validation_metadata(sources_data):
    """Verify validation metadata is present."""
    assert "validation" in sources_data
    assert sources_data["validation"]["yaml_syntax"] == "verified"
    assert "task_id" in sources_data["validation"]
    assert sources_data["validation"]["task_id"] == "T001"
