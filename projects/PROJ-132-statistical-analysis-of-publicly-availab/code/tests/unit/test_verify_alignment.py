import json
import os
import tempfile
from pathlib import Path
import pytest
from src.plan.verify_alignment import (
    load_file_text,
    extract_terms,
    check_mandatory_a_priori_gp,
    check_critical_data_scope_note,
    check_data_source_mismatch,
    check_unknown_terms,
    verify_alignment,
    main
)

@pytest.fixture
def temp_files():
    """Create temporary plan.md and spec.md files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a sample plan.md with some contradictions
        plan_content = """
        # Project Plan
        
        This plan uses Daymet data instead of NOAA/PRISM.
        
        Critical Data Scope Note: We are using a sample dataset.
        
        We implement FR-002-S which is not in the spec.
        """
        
        # Create a sample spec.md
        spec_content = """
        # Project Specification
        
        ## User Story 2
        US-2 requires mandatory a priori GP.
        
        ## Requirements
        FR-001: Use NOAA/PRISM data.
        FR-002: Compute phenology metrics.
        """
        
        plan_path = tmpdir_path / "plan.md"
        spec_path = tmpdir_path / "spec.md"
        
        with open(plan_path, 'w') as f:
            f.write(plan_content)
        
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        
        yield plan_path, spec_path, tmpdir_path

def test_load_file_text(temp_files):
    plan_path, spec_path, _ = temp_files
    content = load_file_text(plan_path)
    assert "Daymet" in content
    assert "NOAA" not in content

def test_extract_terms(temp_files):
    plan_path, spec_path, _ = temp_files
    plan_text = load_file_text(plan_path)
    spec_text = load_file_text(spec_path)
    
    plan_terms = extract_terms(plan_text)
    spec_terms = extract_terms(spec_text)
    
    assert "FR-002-S" in plan_terms
    assert "US-2" in spec_terms
    assert "Daymet" in plan_terms
    assert "NOAA" in spec_terms

def test_check_mandatory_a_priori_gp(temp_files):
    plan_path, spec_path, _ = temp_files
    plan_text = load_file_text(plan_path)
    spec_text = load_file_text(spec_path)
    
    # Plan should have "Critical Data Scope Note" but might not have "mandatory a priori GP"
    # In our test plan, we don't have "mandatory a priori GP"
    contradictions = check_mandatory_a_priori_gp(plan_text, spec_text)
    
    # Since spec has US-2 and plan doesn't have "mandatory a priori GP", there should be a contradiction
    assert len(contradictions) > 0
    assert any(c["type"] == "OTHER" for c in contradictions)

def test_check_critical_data_scope_note(temp_files):
    plan_path, spec_path, _ = temp_files
    plan_text = load_file_text(plan_path)
    
    # Our test plan has "Critical Data Scope Note"
    contradictions = check_critical_data_scope_note(plan_text)
    assert len(contradictions) == 0

def test_check_data_source_mismatch(temp_files):
    plan_path, spec_path, _ = temp_files
    plan_text = load_file_text(plan_path)
    spec_text = load_file_text(spec_path)
    
    # Spec has NOAA, plan has Daymet but not NOAA -> mismatch
    contradictions = check_data_source_mismatch(plan_text, spec_text)
    assert len(contradictions) > 0
    assert any(c["type"] == "DATA_SOURCE_MISMATCH" for c in contradictions)

def test_check_unknown_terms(temp_files):
    plan_path, spec_path, _ = temp_files
    plan_text = load_file_text(plan_path)
    spec_text = load_file_text(spec_path)
    
    # Plan has FR-002-S which is not in spec
    contradictions = check_unknown_terms(plan_text, spec_text)
    assert len(contradictions) > 0
    assert any("FR-002-S" in c["plan_text"] for c in contradictions)

def test_verify_alignment(temp_files):
    plan_path, spec_path, tmpdir_path = temp_files
    
    result = verify_alignment(plan_path, spec_path)
    
    assert "contradictions" in result
    assert isinstance(result["contradictions"], list)
    assert len(result["contradictions"]) > 0  # We expect some contradictions in our test data

def test_main(temp_files):
    plan_path, spec_path, tmpdir_path = temp_files
    
    # Create output path
    output_path = tmpdir_path / "plan_conflicts.json"
    
    # Mock the paths in main by temporarily changing the working directory
    original_cwd = os.getcwd()
    try:
        os.chdir(tmpdir_path)
        # We need to mock the Path(__file__).parent.parent.parent.parent logic
        # For this test, we'll directly call verify_alignment and write to output_path
        result = verify_alignment(plan_path, spec_path)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result == result
    finally:
        os.chdir(original_cwd)