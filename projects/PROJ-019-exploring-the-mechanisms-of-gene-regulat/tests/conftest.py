"""
Pytest configuration and fixtures for the llmXive gene regulation pipeline.

This file provides shared fixtures and configuration for all tests.
"""
import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test artifacts.
    Automatically cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def sample_bed_content():
    """
    Provide sample BED content for testing.
    """
    return (
        "chr1\t1000\t2000\tpeak1\t0\t+\n"
        "chr1\t3000\t4000\tpeak2\t0\t-\n"
        "chr2\t500\t1500\tpeak3\t0\t+\n"
    )

@pytest.fixture
def sample_enrichment_data():
    """
    Provide sample enrichment data for testing.
    """
    return {
        "GM": [
            {"motif_id": "MA0001", "p_value": 0.0001, "q_value": 0.001},
            {"motif_id": "MA0002", "p_value": 0.001, "q_value": 0.01},
        ],
        "K562": [
            {"motif_id": "MA0001", "p_value": 0.001, "q_value": 0.01},
            {"motif_id": "MA0003", "p_value": 0.0001, "q_value": 0.001},
        ],
    }
