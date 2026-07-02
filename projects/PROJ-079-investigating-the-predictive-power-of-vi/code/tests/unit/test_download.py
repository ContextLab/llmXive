"""
Unit tests for the download module stubs.
"""
import pytest
from src.download import fetch_viral_genomes, fetch_geo_data, main
import logging

def test_fetch_viral_genomes_raises_not_implemented():
    """Test that fetch_viral_genomes raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        fetch_viral_genomes(["NC_000001"])

def test_fetch_geo_data_raises_not_implemented():
    """Test that fetch_geo_data raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        fetch_geo_data(["GSE12345"])

def test_main_logs_message(caplog):
    """Test that main() logs the expected initialization message."""
    with caplog.at_level(logging.INFO):
        main()
    assert "Download skeleton initialized" in caplog.text