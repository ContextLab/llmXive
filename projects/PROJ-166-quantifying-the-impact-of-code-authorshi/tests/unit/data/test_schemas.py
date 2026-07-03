import pytest
import pandas as pd
from code.data.schemas import validate_dataframe, get_schema

def test_validate_target_list_schema():
    """Test validation of target_list schema."""
    df = pd.DataFrame({
        "url": ["https://github.com/test/repo1", "https://github.com/test/repo2"],
        "language": ["Python", "JavaScript"],
        "stars": [100, 200],
        "age": [365, 730]
    })
    assert validate_dataframe(df, "target_list") is True

def test_validate_target_list_missing_column():
    """Test that missing columns raise an error."""
    df = pd.DataFrame({
        "url": ["https://github.com/test/repo1"],
        "language": ["Python"],
        "stars": [100]
        # Missing 'age'
    })
    with pytest.raises(ValueError, match="missing required columns"):
        validate_dataframe(df, "target_list")

def test_validate_repo_metrics_schema():
    """Test validation of repo_metrics schema."""
    df = pd.DataFrame({
        "url": ["https://github.com/test/repo1"],
        "language": ["Python"],
        "unique_authors": [5],
        "kloc": [12.5],
        "cve_count": [2],
        "project_age": [1000],
        "release_count": [10]
    })
    assert validate_dataframe(df, "repo_metrics") is True

def test_get_schema_exists():
    """Test that get_schema returns a valid dict."""
    schema = get_schema("target_list")
    assert isinstance(schema, dict)
    assert "columns" in schema