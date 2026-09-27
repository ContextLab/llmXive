"""
Unit test to verify that the required specs directory structure exists.
This supports T001c verification.
"""
import os
import pytest
from pathlib import Path

def get_project_root():
    """Helper to find the project root."""
    cwd = Path.cwd()
    if (cwd / "projects" / "PROJ-405").exists():
        return cwd / "projects" / "PROJ-405"
    elif (cwd.parent / "projects" / "PROJ-405").exists():
        return cwd.parent / "projects" / "PROJ-405"
    return cwd

def test_specs_root_exists():
    """Verify the main specs directory exists."""
    root = get_project_root()
    specs_dir = root / "specs" / "001-predict-plant-disease-severity"
    assert specs_dir.exists(), f"Specs root directory does not exist: {specs_dir}"
    assert specs_dir.is_dir(), f"Specs root is not a directory: {specs_dir}"

def test_contracts_dir_exists():
    """Verify the contracts subdirectory exists."""
    root = get_project_root()
    contracts_dir = root / "specs" / "001-predict-plant-disease-severity" / "contracts"
    assert contracts_dir.exists(), f"Contracts directory does not exist: {contracts_dir}"
    assert contracts_dir.is_dir(), f"Contracts is not a directory: {contracts_dir}"

def test_design_dir_exists():
    """Verify the design subdirectory exists."""
    root = get_project_root()
    design_dir = root / "specs" / "001-predict-plant-disease-severity" / "design"
    assert design_dir.exists(), f"Design directory does not exist: {design_dir}"
    assert design_dir.is_dir(), f"Design is not a directory: {design_dir}"

def test_data_models_dir_exists():
    """Verify the data-models subdirectory exists."""
    root = get_project_root()
    dm_dir = root / "specs" / "001-predict-plant-disease-severity" / "data-models"
    assert dm_dir.exists(), f"Data-models directory does not exist: {dm_dir}"
    assert dm_dir.is_dir(), f"Data-models is not a directory: {dm_dir}"

def test_research_dir_exists():
    """Verify the research subdirectory exists."""
    root = get_project_root()
    research_dir = root / "specs" / "001-predict-plant-disease-severity" / "research"
    assert research_dir.exists(), f"Research directory does not exist: {research_dir}"
    assert research_dir.is_dir(), f"Research is not a directory: {research_dir}"