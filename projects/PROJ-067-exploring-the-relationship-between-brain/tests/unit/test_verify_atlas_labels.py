"""
Unit tests for code/analysis/verify_atlas_labels.py
"""
import pytest
import pandas as pd
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.verify_atlas_labels import (
    check_hippocampal_label,
    generate_mapping_csv,
    OUTPUT_FILE
)

def test_check_hippocampal_label_with_hippocampus():
    """Test that the function correctly identifies Hippocampal labels."""
    labels = [
        (1, "DMN", "Region1"),
        (2, "Hippocampal", "Hippocampus"),
        (3, "Salience", "Anterior Insula")
    ]
    assert check_hippocampal_label(labels) is True

def test_check_hippocampal_label_with_memory():
    """Test that the function correctly identifies Memory labels."""
    labels = [
        (1, "DMN", "Region1"),
        (2, "Memory", "Hippocampal Formation"),
        (3, "Salience", "Anterior Insula")
    ]
    assert check_hippocampal_label(labels) is True

def test_check_hippocampal_label_without_match():
    """Test that the function returns False when no match is found."""
    labels = [
        (1, "DMN", "Region1"),
        (2, "Salience", "Anterior Insula"),
        (3, "Visual", "V1")
    ]
    assert check_hippocampal_label(labels) is False

def test_generate_mapping_csv():
    """Test the generation of the mapping CSV file."""
    labels = [
        (1, "DMN", "Region1"),
        (2, "Hippocampal", "Hippocampus"),
        (3, "Salience", "Anterior Insula"),
        (4, "Memory", "Parahippocampal")
    ]
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    df = generate_mapping_csv(labels)
    
    # Verify file exists
    assert OUTPUT_FILE.exists(), "Mapping CSV file was not created."
    
    # Verify content
    assert "region_id" in df.columns
    assert "mapped_label" in df.columns
    
    # Check specific mappings
    row_hipp = df[df["source_label"] == "Hippocampus"].iloc[0]
    assert row_hipp["mapped_label"] == "Hippocampal-Memory"
    
    row_mem = df[df["source_label"] == "Parahippocampal"].iloc[0]
    assert row_mem["mapped_label"] == "Hippocampal-Memory"
    
    row_dmn = df[df["source_label"] == "Region1"].iloc[0]
    assert row_dmn["mapped_label"] == "DMN"
    
    # Cleanup
    if OUTPUT_FILE.exists():
        os.remove(OUTPUT_FILE)