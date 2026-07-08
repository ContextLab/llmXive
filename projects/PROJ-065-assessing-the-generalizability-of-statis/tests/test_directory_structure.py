"""
Tests to verify the directory structure created by T001a, T001b, and T001c.
"""
import os
from pathlib import Path
import pytest

from setup_directories import ensure_directory_structure

def test_base_directories_exist(project_root):
    """Verify that the base code, data, and outputs directories exist."""
    assert (project_root / "code").exists(), "code/ directory missing"
    assert (project_root / "data").exists(), "data/ directory missing"
    assert (project_root / "outputs").exists(), "outputs/ directory missing"

def test_data_subdirectories_exist(project_root):
    """Verify that raw and processed subdirectories exist under data/."""
    data_dir = project_root / "data"
    assert (data_dir / "raw").exists(), "data/raw/ directory missing"
    assert (data_dir / "processed").exists(), "data/processed/ directory missing"

def test_outputs_subdirectories_exist(project_root):
    """Verify that figures and reports subdirectories exist under outputs/."""
    outputs_dir = project_root / "outputs"
    assert (outputs_dir / "figures").exists(), "outputs/figures/ directory missing"
    assert (outputs_dir / "reports").exists(), "outputs/reports/ directory missing"

def test_code_directory_is_writable(project_root):
    """Verify that the code directory is writable (sanity check)."""
    code_dir = project_root / "code"
    assert os.access(code_dir, os.W_OK), "code/ directory is not writable"

def test_data_raw_is_writable(project_root):
    """Verify that the data/raw directory is writable."""
    raw_dir = project_root / "data" / "raw"
    assert os.access(raw_dir, os.W_OK), "data/raw/ directory is not writable"

def test_data_processed_is_writable(project_root):
    """Verify that the data/processed directory is writable."""
    proc_dir = project_root / "data" / "processed"
    assert os.access(proc_dir, os.W_OK), "data/processed/ directory is not writable"

def test_outputs_figures_is_writable(project_root):
    """Verify that the outputs/figures directory is writable."""
    fig_dir = project_root / "outputs" / "figures"
    assert os.access(fig_dir, os.W_OK), "outputs/figures/ directory is not writable"

def test_outputs_reports_is_writable(project_root):
    """Verify that the outputs/reports directory is writable."""
    rep_dir = project_root / "outputs" / "reports"
    assert os.access(rep_dir, os.W_OK), "outputs/reports/ directory is not writable"